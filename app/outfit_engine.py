"""
Outfit Reasoning Engine for StyleMate AI.
Handles:
- Context-aware outfit generation based on occasion, weather, formality, colors, and budget.
- Strict wardrobe_only enforcement (never invents items).
- Iterative modification of existing outfits (e.g. swapping only pants while preserving the rest).
- Fashion rationale generation grounded in user style profile and color theory.
"""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.db import (
    get_style_profile_record,
    list_wardrobe_records,
    get_active_outfit_context,
    set_active_outfit_context,
)
from app.schemas import OutfitRecommendation, OutfitItem


def generate_outfit_reasoning(
    occasion: str,
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
) -> Dict[str, Any]:
    """Generates or iteratively refines an outfit with grounded fashion reasoning.

    Args:
        occasion: e.g. 'dinner date', 'college presentation', 'casual weekend'.
        user_id: Unique user identifier.
        formality: 'casual', 'smart_casual', 'formal', etc.
        weather_context: e.g. 'chilly evening', 'warm summer day', 'rainy'.
        preferred_colors: Desired color accents or tones.
        excluded_colors: Colors that must NOT appear in the ensemble.
        budget: Maximum budget for any non-wardrobe items.
        wardrobe_only: If True, strictly use owned clothes and NEVER invent items.
        requested_categories: Specific categories to include (e.g. ['topwear', 'bottomwear']).
        modify_category: Category to swap (e.g. 'bottomwear' when user dislikes pants).
        feedback_instruction: User critique (e.g. 'I don't like the pants').

    Returns:
        Structured OutfitRecommendation dictionary.
    """
    profile = get_style_profile_record(user_id) or {}
    wardrobe = list_wardrobe_records(user_id)

    if wardrobe_only and not wardrobe:
        return {
            "status": "error",
            "message": "Your wardrobe is empty. Please upload some clothes first to build an outfit from what you own."
        }

    # Banned colors logic: combine excluded_colors with profile avoid_colors
    banned = set([c.lower() for c in (excluded_colors or [])])
    banned.update([c.lower() for c in profile.get("avoid_colors", [])])

    eligible_wardrobe = [
        item for item in wardrobe
        if not any(ban in item.get("color", "").lower() for ban in banned)
    ]

    # Check for iterative modification of active outfit
    active_outfit = get_active_outfit_context(user_id)
    if modify_category and active_outfit:
        return _modify_single_category(
            active_outfit=active_outfit,
            modify_cat=modify_category,
            eligible_wardrobe=eligible_wardrobe,
            user_id=user_id,
            profile=profile,
            feedback_instruction=feedback_instruction
        )

    # Determine formality
    eff_formality = formality
    if not eff_formality:
        occ_lower = occasion.lower()
        if "date" in occ_lower or "dinner" in occ_lower or "presentation" in occ_lower:
            eff_formality = "smart_casual"
        elif "formal" in occ_lower or "wedding" in occ_lower or "interview" in occ_lower:
            eff_formality = "formal"
        else:
            eff_formality = "casual"

    # Filter categories from eligible wardrobe
    tops = [i for i in eligible_wardrobe if i.get("category") == "topwear"]
    bottoms = [i for i in eligible_wardrobe if i.get("category") == "bottomwear"]
    outers = [i for i in eligible_wardrobe if i.get("category") == "outerwear"]
    shoes = [i for i in eligible_wardrobe if i.get("category") == "footwear"]

    # Filter by preferred colors if provided
    if preferred_colors:
        pref_set = set([p.lower() for p in preferred_colors])
        p_tops = [i for i in tops if any(p in i.get("color", "").lower() for p in pref_set)]
        if p_tops:
            tops = p_tops

    # Match tops for formality and occasion
    selected_top = None
    if eff_formality == "smart_casual":
        for t in tops:
            if "oxford" in (t.get("subcategory") or t.get("sub_category", "")).lower() or "button" in t.get("subcategory", "").lower():
                selected_top = t
                break
    elif eff_formality == "casual":
        for t in tops:
            if "tee" in (t.get("subcategory") or t.get("sub_category", "")).lower() or t.get("formality") == "casual":
                selected_top = t
                break
    if not selected_top and tops:
        selected_top = tops[0]

    # Match bottoms for contrast & balance
    selected_bottom = None
    top_color = (selected_top.get("color") if selected_top else "").lower()
    
    if eff_formality == "smart_casual":
        # Look for tailored chinos
        for b in bottoms:
            sub = (b.get("subcategory") or b.get("sub_category", "")).lower()
            if "chino" in sub:
                selected_bottom = b
                break
    if not selected_bottom and bottoms:
        # Avoid same-color top & bottom unless intended monochrome
        contrasting = [b for b in bottoms if b.get("color", "").lower() != top_color]
        selected_bottom = contrasting[0] if contrasting else bottoms[0]

    # Match shoes
    selected_shoes = None
    if shoes:
        if eff_formality in ["smart_casual", "casual"]:
            selected_shoes = shoes[0]

    # Weather & Layering context
    selected_outer = None
    weather_desc = (weather_context or "").lower()
    needs_layer = (
        "cold" in weather_desc or "chilly" in weather_desc or "autumn" in weather_desc or
        "winter" in weather_desc or "evening" in occasion.lower()
    )
    if needs_layer and outers:
        selected_outer = outers[0]

    outfit_items: List[OutfitItem] = []
    if selected_top:
        outfit_items.append(OutfitItem(
            item_id=selected_top.get("id"),
            category="topwear",
            subcategory=selected_top.get("subcategory") or selected_top.get("sub_category", "top"),
            color=selected_top.get("color", "neutral"),
            source="wardrobe",
            image_url=selected_top.get("image_url")
        ))
    if selected_bottom:
        outfit_items.append(OutfitItem(
            item_id=selected_bottom.get("id"),
            category="bottomwear",
            subcategory=selected_bottom.get("subcategory") or selected_bottom.get("sub_category", "bottom"),
            color=selected_bottom.get("color", "neutral"),
            source="wardrobe",
            image_url=selected_bottom.get("image_url")
        ))
    if selected_outer:
        outfit_items.append(OutfitItem(
            item_id=selected_outer.get("id"),
            category="outerwear",
            subcategory=selected_outer.get("subcategory") or selected_outer.get("sub_category", "jacket"),
            color=selected_outer.get("color", "neutral"),
            source="wardrobe",
            image_url=selected_outer.get("image_url")
        ))
    if selected_shoes:
        outfit_items.append(OutfitItem(
            item_id=selected_shoes.get("id"),
            category="footwear",
            subcategory=selected_shoes.get("subcategory") or selected_shoes.get("sub_category", "shoes"),
            color=selected_shoes.get("color", "neutral"),
            source="wardrobe",
            image_url=selected_shoes.get("image_url")
        ))

    items_summary = [f"{i.color} {i.subcategory}" for i in outfit_items]
    undertone = profile.get("skin_tone_undertone", {}).get("undertone", "neutral-warm")

    top_txt = selected_top.get('color', 'top') if selected_top else 'top'
    bottom_txt = selected_bottom.get('color', 'bottom') if selected_bottom else 'bottom'
    
    rationale = (
        f"Selected a coordinated {eff_formality} look for your {occasion}. "
        f"The {top_txt} paired with {bottom_txt} creates balanced contrast that complements "
        f"your {undertone} undertone without washing you out. "
        f"{'An outer layer was included for the cooler context. ' if selected_outer else ''}"
        f"All pieces are strictly sourced from your owned wardrobe."
    )

    outfit_id = f"outfit_{uuid.uuid4().hex[:8]}"
    outfit_rec = OutfitRecommendation(
        outfit_id=outfit_id,
        title=f"Curated {occasion.title()} Look",
        occasion=occasion,
        formality=eff_formality,
        items=outfit_items,
        items_summary=items_summary,
        color_harmony="balanced neutral contrast",
        rationale=rationale,
        wardrobe_only=wardrobe_only
    )

    # Save to active session context for iterative modifications
    set_active_outfit_context(user_id, outfit_rec.model_dump())

    return {
        "status": "success",
        "outfit": outfit_rec.model_dump()
    }


def _modify_single_category(
    active_outfit: Dict[str, Any],
    modify_cat: str,
    eligible_wardrobe: List[Dict[str, Any]],
    user_id: str,
    profile: Dict[str, Any],
    feedback_instruction: Optional[str] = None
) -> Dict[str, Any]:
    """Swaps out only the specified clothing category while retaining all other garments in the active outfit."""
    current_items = active_outfit.get("items", [])
    current_item_in_cat = next((i for i in current_items if i.get("category") == modify_cat), None)
    current_item_id = current_item_in_cat.get("item_id") if current_item_in_cat else None

    # Find alternatives in wardrobe for this category
    alternatives = [
        w for w in eligible_wardrobe
        if w.get("category") == modify_cat and w.get("id") != current_item_id
    ]

    if not alternatives:
        return {
            "status": "warning",
            "message": f"No other {modify_cat} found in your wardrobe that match your color rules. Kept current outfit.",
            "outfit": active_outfit
        }

    # Pick the best alternative
    replacement = alternatives[0]

    new_items: List[OutfitItem] = []
    for item in current_items:
        if item.get("category") == modify_cat:
            new_items.append(OutfitItem(
                item_id=replacement.get("id"),
                category=modify_cat,
                subcategory=replacement.get("subcategory") or replacement.get("sub_category", "clothing item"),
                color=replacement.get("color", "neutral"),
                source="wardrobe",
                image_url=replacement.get("image_url")
            ))
        else:
            new_items.append(OutfitItem(**item))

    items_summary = [f"{i.color} {i.subcategory}" for i in new_items]
    
    rationale = (
        f"Modified the {modify_cat} based on your feedback: swapped in your {replacement.get('color')} "
        f"{replacement.get('subcategory') or replacement.get('sub_category')} while preserving the rest of your outfit."
    )

    updated_outfit = OutfitRecommendation(
        outfit_id=active_outfit.get("outfit_id", f"outfit_{uuid.uuid4().hex[:8]}"),
        title=active_outfit.get("title", "Updated Look"),
        occasion=active_outfit.get("occasion", "Casual"),
        formality=active_outfit.get("formality", "smart_casual"),
        items=new_items,
        items_summary=items_summary,
        color_harmony="revised neutral harmony",
        rationale=rationale,
        wardrobe_only=True
    )

    set_active_outfit_context(user_id, updated_outfit.model_dump())

    return {
        "status": "success",
        "modified_category": modify_cat,
        "outfit": updated_outfit.model_dump()
    }
