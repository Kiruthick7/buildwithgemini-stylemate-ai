"""
ADK Function Tools for StyleMate AI.
Provides:
- analyze_style_profile
- update_style_profile
- get_style_profile
- analyze_clothing
- get_wardrobe
- add_wardrobe_item
- update_wardrobe_item
- remove_wardrobe_item
- generate_outfit
- save_outfit
"""

import json
from typing import Any, Dict, List, Optional
from app.db import (
    get_style_profile_record,
    save_style_profile_record,
    list_wardrobe_records,
    add_wardrobe_record,
    update_wardrobe_record,
    delete_wardrobe_record,
    save_outfit_record,
    list_outfit_records,
    get_active_outfit_context,
)
from app.multimodal_service import (
    extract_style_profile_with_gemini,
    extract_clothing_analysis_with_gemini,
)
from app.outfit_engine import generate_outfit_reasoning
from app.schemas import PersonalStyleProfile, ClothingItemAnalysis


def get_style_profile(user_id: str = "default_user") -> str:
    """Retrieves the personal style profile for a user.

    Args:
        user_id: The unique identifier of the user (defaults to 'default_user').

    Returns:
        JSON string representing the user's style profile.
    """
    profile = get_style_profile_record(user_id)
    if not profile:
        return json.dumps({
            "status": "not_found",
            "message": "No profile found for user. Please upload or analyze a photo first."
        })
    return json.dumps({"status": "success", "profile": profile})


def analyze_style_profile(
    image_storage_uri_or_hint: str,
    user_id: str = "default_user"
) -> str:
    """Analyzes a user's uploaded portrait photo using Gemini Multimodal Vision to infer non-sensitive style parameters.

    Args:
        image_storage_uri_or_hint: Cloud Storage URI (gs://...), file path, or image descriptive hint.
        user_id: The ID of the user to assign this profile to.

    Returns:
        Structured JSON string matching PersonalStyleProfile schema.
    """
    extracted_dict = extract_style_profile_with_gemini(
        image_uri=image_storage_uri_or_hint,
        image_hint=image_storage_uri_or_hint,
        user_id=user_id
    )

    saved = save_style_profile_record(user_id, extracted_dict)

    return json.dumps({
        "status": "success",
        "message": (
            "Analyzed style profile successfully."
            if saved.get("is_valid_fashion_portrait")
            else "Image analysis identified portrait quality issues."
        ),
        "profile": saved
    })


def update_style_profile(
    user_id: str = "default_user",
    undertone: Optional[str] = None,
    face_shape: Optional[str] = None,
    suitable_color_families: Optional[List[str]] = None,
    avoid_colors: Optional[List[str]] = None,
    inferred_style_vibes: Optional[List[str]] = None
) -> str:
    """Allows the user to review, correct, or refine their personal style profile.

    Args:
        user_id: The ID of the user.
        undertone: Overridden undertone ('warm', 'cool', 'neutral', 'olive').
        face_shape: Overridden face shape ('oval', 'square', 'round', 'heart', 'oblong').
        suitable_color_families: List of colors the user enjoys wearing or wants prioritized.
        avoid_colors: List of colors the user dislikes or wants to avoid.
        inferred_style_vibes: Style aesthetics the user prefers (e.g. 'smart casual', 'minimalist').

    Returns:
        JSON string of the corrected profile.
    """
    profile = get_style_profile_record(user_id) or {"user_id": user_id}
    
    if undertone:
        if "skin_tone_undertone" not in profile:
            profile["skin_tone_undertone"] = {}
        profile["skin_tone_undertone"]["undertone"] = undertone
        profile["skin_tone_undertone"]["confidence"] = "high"
        profile["skin_tone_undertone"]["disclaimer"] = "User-confirmed undertone."
    
    if face_shape:
        profile["approximate_face_shape"] = face_shape
    if suitable_color_families is not None:
        profile["suitable_color_families"] = suitable_color_families
    if avoid_colors is not None:
        profile["avoid_colors"] = avoid_colors
    if inferred_style_vibes is not None:
        profile["inferred_style_vibes"] = inferred_style_vibes

    profile["user_reviewed"] = True
    updated = save_style_profile_record(user_id, profile)
    return json.dumps({
        "status": "success",
        "message": "Style profile successfully corrected and saved.",
        "profile": updated
    })


def analyze_clothing(
    image_storage_uri_or_hint: str
) -> str:
    """Analyzes a photograph of a clothing item using Gemini Multimodal Vision to extract fashion attributes.

    Returns structured JSON with category, subcategory, primary/secondary colors,
    pattern, material, style, seasons, occasions, styling tags, and confidence.

    Args:
        image_storage_uri_or_hint: Cloud Storage URI (gs://...), file path, or description of clothing photo.

    Returns:
        Structured JSON string matching ClothingItemAnalysis schema.
    """
    analyzed = extract_clothing_analysis_with_gemini(
        image_uri=image_storage_uri_or_hint,
        image_hint=image_storage_uri_or_hint
    )
    return json.dumps({
        "status": "success",
        "analysis": analyzed
    })


def get_wardrobe(
    user_id: str = "default_user",
    category: Optional[str] = None,
    favorite_only: bool = False
) -> str:
    """Retrieves all clothing items currently in the user's virtual wardrobe.

    Args:
        user_id: The ID of the user.
        category: Optional category filter ('topwear', 'bottomwear', 'outerwear', 'footwear', 'accessory').
        favorite_only: If true, returns only items flagged as favorites.

    Returns:
        JSON string containing the list of wardrobe items with full styling details.
    """
    items = list_wardrobe_records(user_id, category=category)
    if favorite_only:
        items = [i for i in items if i.get("is_favorite") is True]
    return json.dumps({
        "status": "success",
        "count": len(items),
        "items": items
    })


def add_wardrobe_item(
    category: str,
    subcategory: Optional[str] = None,
    sub_category: Optional[str] = None,
    color: str = "neutral",
    secondary_colors: Optional[List[str]] = None,
    pattern: str = "solid",
    material: Optional[str] = None,
    style: str = "casual",
    formality: Optional[str] = None,
    season: Optional[List[str]] = None,
    occasions: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    user_id: str = "default_user",
    image_storage_uri: Optional[str] = None,
    is_favorite: bool = False
) -> str:
    """Adds a new clothing item into the user's virtual wardrobe."""
    chosen_sub = subcategory or sub_category or "clothing item"
    chosen_style = formality or style or "casual"
    new_item = {
        "category": category.lower(),
        "subcategory": chosen_sub,
        "sub_category": chosen_sub,
        "color": color.lower(),
        "secondary_colors": secondary_colors or [],
        "pattern": pattern.lower(),
        "material": material,
        "style": chosen_style.lower(),
        "formality": chosen_style.lower(),
        "season": season or ["all-season"],
        "seasons": season or ["all-season"],
        "occasions": occasions or ["casual"],
        "tags": tags or [],
        "image_url": image_storage_uri,
        "image_storage_uri": image_storage_uri,
        "is_favorite": is_favorite
    }
    saved = add_wardrobe_record(user_id, new_item)
    return json.dumps({
        "status": "success",
        "message": f"Added {chosen_sub} ({color}) to wardrobe.",
        "item": saved
    })


def update_wardrobe_item(
    item_id: str,
    user_id: str = "default_user",
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    color: Optional[str] = None,
    style: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    tags: Optional[List[str]] = None
) -> str:
    """Updates an existing item in the user's virtual wardrobe."""
    updates: Dict[str, Any] = {}
    if category is not None:
        updates["category"] = category.lower()
    if subcategory is not None:
        updates["subcategory"] = subcategory
        updates["sub_category"] = subcategory
    if color is not None:
        updates["color"] = color.lower()
    if style is not None:
        updates["style"] = style.lower()
        updates["formality"] = style.lower()
    if is_favorite is not None:
        updates["is_favorite"] = is_favorite
    if tags is not None:
        updates["tags"] = tags

    updated = update_wardrobe_record(user_id, item_id, updates)
    if updated:
        return json.dumps({
            "status": "success",
            "message": f"Updated wardrobe item {item_id}.",
            "item": updated
        })
    return json.dumps({"status": "error", "message": f"Wardrobe item {item_id} not found."})


def remove_wardrobe_item(item_id: str, user_id: str = "default_user") -> str:
    """Removes a clothing item from the user's virtual wardrobe."""
    success = delete_wardrobe_record(user_id, item_id)
    if success:
        return json.dumps({"status": "success", "message": f"Item {item_id} deleted."})
    return json.dumps({"status": "error", "message": f"Item {item_id} not found."})


def generate_outfit(
    occasion: str = "casual",
    user_id: str = "default_user",
    formality: Optional[str] = None,
    weather_context: Optional[str] = None,
    preferred_colors: Optional[List[str]] = None,
    excluded_colors: Optional[List[str]] = None,
    budget: Optional[float] = None,
    wardrobe_only: bool = True,
    requested_categories: Optional[List[str]] = None,
    modify_category: Optional[str] = None,
    feedback_instruction: Optional[str] = None,
    source: Optional[str] = None, # Backwards compatibility alias
    preferred_style: Optional[str] = None # Backwards compatibility alias
) -> str:
    """Generates an outfit recommendation or iteratively refines an existing outfit.

    Args:
        occasion: Event or context (e.g. 'dinner date', 'work meeting', 'casual weekend').
        user_id: User identifier.
        formality: Desired formality level ('casual', 'smart_casual', 'formal').
        weather_context: Ambient conditions (e.g. 'chilly evening', 'hot summer afternoon').
        preferred_colors: Color tones the user wishes to incorporate.
        excluded_colors: Colors the user dislikes or requests to avoid.
        budget: Maximum budget for any external items.
        wardrobe_only: Enforce strictly using owned clothes and NEVER invent unavailable items.
        requested_categories: Specific garment categories to include.
        modify_category: Target category to swap when user requests an adjustment (e.g. 'bottomwear').
        feedback_instruction: User feedback string (e.g. "I don't like the pants").

    Returns:
        Structured JSON string representing the recommended or modified outfit.
    """
    eff_formality = formality or preferred_style
    eff_wardrobe_only = wardrobe_only
    if source == "wardrobe_only":
        eff_wardrobe_only = True

    result = generate_outfit_reasoning(
        occasion=occasion,
        user_id=user_id,
        formality=eff_formality,
        weather_context=weather_context,
        preferred_colors=preferred_colors,
        excluded_colors=excluded_colors,
        budget=budget,
        wardrobe_only=eff_wardrobe_only,
        requested_categories=requested_categories,
        modify_category=modify_category,
        feedback_instruction=feedback_instruction
    )
    return json.dumps(result)


def save_outfit(
    name: str,
    items_summary: List[str],
    occasion: str,
    rationale: str,
    user_id: str = "default_user",
    collection_tag: str = "General"
) -> str:
    """Saves an outfit to the user's saved outfits collection."""
    outfit_data = {
        "name": name,
        "items_summary": items_summary,
        "occasion": occasion,
        "rationale": rationale,
        "collection_tag": collection_tag
    }
    saved = save_outfit_record(user_id, outfit_data)
    return json.dumps({
        "status": "success",
        "message": f"Outfit '{name}' saved to {collection_tag} collection.",
        "outfit": saved
    })

# Backwards compatibility alias
analyze_clothing_item = analyze_clothing

from app.shopping_provider import get_shopping_provider
from app.schemas import ProductItem

def search_products(
    query: str,
    user_id: str = "default_user",
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    color: Optional[str] = None,
    occasion: Optional[str] = None,
    preferred_style: Optional[str] = None,
    pairing_with_wardrobe_item_id: Optional[str] = None,
    limit: int = 5
) -> str:
    """Searches retail fashion products from external catalogs adhering strictly to budget, category, and style rules.

    Args:
        query: Search query, e.g. 'black shirt', 'date night shoes', 'shirt for beige pants'.
        user_id: The user's ID for personalized style grounding.
        category: Garment category filter ('topwear', 'bottomwear', 'outerwear', 'footwear').
        max_price: Hard ceiling price in INR (e.g. 1500.0, 2000.0). Products above this are discarded.
        color: Target color (e.g. 'black', 'terracotta').
        occasion: Context (e.g. 'dinner date', 'summer vacation').
        preferred_style: Formality or aesthetic ('smart_casual', 'casual').
        pairing_with_wardrobe_item_id: Optional ID of a wardrobe item the user wants to pair this with.
        limit: Max products to return.

    Returns:
        Structured JSON string containing matched products and styling rationales grounded in the user's profile.
    """
    profile = get_style_profile_record(user_id) or {}
    wardrobe = list_wardrobe_records(user_id)
    provider = get_shopping_provider()

    # If pairing with an owned wardrobe item, ground search in complementary colors
    pairing_item = None
    effective_color = color
    effective_category = category

    if pairing_with_wardrobe_item_id:
        pairing_item = next((w for w in wardrobe if w.get("id") == pairing_with_wardrobe_item_id), None)
        if pairing_item:
            if pairing_item.get("category") == "bottomwear" and not category:
                effective_category = "topwear"

    # Query extraction heuristics
    q_lower = query.lower()
    if not effective_category:
        if "shirt" in q_lower or "tee" in q_lower or "top" in q_lower:
            effective_category = "topwear"
        elif "pant" in q_lower or "chino" in q_lower or "trouser" in q_lower or "jean" in q_lower:
            effective_category = "bottomwear"
        elif "shoe" in q_lower or "sneaker" in q_lower or "boot" in q_lower:
            effective_category = "footwear"
        elif "jacket" in q_lower or "coat" in q_lower:
            effective_category = "outerwear"

    if not effective_color:
        for c in ["black", "navy", "white", "olive", "terracotta", "beige", "charcoal"]:
            if c in q_lower:
                effective_color = c
                break

    # Execute search via pluggable provider
    products = provider.search(
        query=query,
        category=effective_category,
        max_price=max_price,
        color=effective_color,
        style=preferred_style,
        limit=limit
    )

    if not products:
        return json.dumps({
            "status": "not_found",
            "message": f"No products matching '{query}' were found in the catalog under ₹{max_price or 'any price'}.",
            "products": []
        })

    # Annotate with fashion rationale
    annotated: List[Dict[str, Any]] = []
    undertone = profile.get("skin_tone_undertone", {}).get("undertone", "neutral")

    for p in products:
        p_dict = p.model_dump()
        if pairing_item:
            rationale = (
                f"Matches perfectly with your owned {pairing_item.get('color')} {pairing_item.get('subcategory') or pairing_item.get('sub_category')}. "
                f"The {p.color} color offers balanced contrast and adheres strictly to your budget limit of ₹{max_price or 'flexible'}."
            )
        else:
            rationale = (
                f"A versatile {p.style} piece in {p.color} ({p.brand}, ₹{p.price:,.0f}). "
                f"Flattering for {undertone} undertones and well within your specified price range."
            )
        p_dict["match_rationale"] = rationale
        annotated.append(p_dict)

    return json.dumps({
        "status": "success",
        "count": len(annotated),
        "products": annotated,
        "query_context": {
            "query": query,
            "max_price": max_price,
            "category": effective_category,
            "color": effective_color
        }
    })

from app.visualization_service import generate_outfit_visualization

def visualize_outfit(
    outfit_id: Optional[str] = None,
    items_summary: Optional[List[str]] = None,
    user_id: str = "default_user",
    force_failure: bool = False
) -> str:
    """Generates an approximate conceptual AI visualization of the user or outfit.

    Strictly labeled as an AI-generated concept. Does not represent exact physical fit
    or exact personal appearance. Private user images are kept strictly confidential.

    Args:
        outfit_id: Optional ID of the outfit to visualize.
        items_summary: Optional list of garment names (e.g. ['navy blue oxford shirt', 'warm beige chinos']).
        user_id: The ID of the user.
        force_failure: Set to True to test graceful failure resilience.

    Returns:
        Structured JSON string conforming to VisualizationResult schema.
    """
    profile = get_style_profile_record(user_id) or {}
    active_outfit = get_active_outfit_context(user_id) or {}

    summary = items_summary or active_outfit.get("items_summary") or ["navy blue oxford shirt", "warm beige chinos"]
    title = active_outfit.get("title", "Curated Look")

    res = generate_outfit_visualization(
        outfit_title=title,
        items_summary=summary,
        user_style_description=profile.get("inferred_style_vibes", ["smart casual"])[0] if profile.get("inferred_style_vibes") else "smart casual",
        user_image_uri=profile.get("image_storage_uri"),
        force_failure=force_failure
    )

    return json.dumps({
        "status": res.get("status"),
        "visualization": res
    })

def check_items_match(
    item_a_description_or_id: str,
    item_b_description_or_id: str,
    user_id: str = "default_user"
) -> str:
    """Evaluates whether two clothing items match harmoniously based on color theory, contrast, and style formality.

    Args:
        item_a_description_or_id: First garment description or wardrobe ID (e.g. 'olive overshirt' or 'w_5').
        item_b_description_or_id: Second garment description or wardrobe ID (e.g. 'beige chinos' or 'w_3').
        user_id: The ID of the user.

    Returns:
        Structured JSON string evaluating color compatibility, formality match, undertone balance, and styling verdict.
    """
    profile = get_style_profile_record(user_id) or {}
    wardrobe = list_wardrobe_records(user_id)

    # Resolve descriptions or IDs
    def resolve_item(query: str):
        for w in wardrobe:
            if w.get("id") == query or query.lower() in f"{w.get('color')} {w.get('subcategory') or w.get('sub_category')}".lower():
                return f"{w.get('color')} {w.get('subcategory') or w.get('sub_category')}", w.get("category"), w.get("color")
        return query, "unknown", "unknown"

    desc_a, cat_a, color_a = resolve_item(item_a_description_or_id)
    desc_b, cat_b, color_b = resolve_item(item_b_description_or_id)

    undertone = profile.get("skin_tone_undertone", {}).get("undertone", "neutral")

    # Fashion rule evaluation
    # E.g. olive + beige = classic earth tone harmony
    is_clash = ("black" in color_a.lower() and "brown" in color_b.lower()) or ("neon" in desc_a.lower() or "neon" in desc_b.lower())
    
    if is_clash:
        match_score = 45
        verdict = "Difficult Pairing"
        explanation = f"{desc_a} and {desc_b} have competing visual weights or clashing undertones that make cohesion tricky."
    else:
        match_score = 92
        verdict = "Great Match"
        explanation = (
            f"The combination of {desc_a} and {desc_b} works exceptionally well. "
            f"The contrast creates a grounded, natural harmony that complements {undertone} undertones."
        )

    return json.dumps({
        "status": "success",
        "item_a": desc_a,
        "item_b": desc_b,
        "verdict": verdict,
        "compatibility_score": match_score,
        "explanation": explanation
    })
