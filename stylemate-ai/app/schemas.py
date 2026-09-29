from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class SkinToneUndertoneEstimate(BaseModel):
    undertone: Literal["warm", "cool", "neutral", "olive", "neutral-warm", "neutral-cool", "uncertain"] = Field(
        description="Estimated skin undertone based strictly on visible clothing contrast and lighting."
    )
    confidence: Literal["high", "moderate", "low", "unreliable"] = Field(
        description="Confidence level of the visual undertone estimation."
    )
    disclaimer: str = Field(
        default="Visual estimation under captured lighting conditions; user confirmation is advised.",
        description="Mandatory disclaimer that visual inference is an approximation."
    )

class PersonalStyleProfile(BaseModel):
    user_id: str = Field(description="Unique identifier for the user.")
    is_valid_fashion_portrait: bool = Field(
        description="True if the photo contains a single clear individual suitable for fashion analysis."
    )
    detection_issues: Optional[List[str]] = Field(
        default=None,
        description="Details on issues such as 'multiple_people_detected', 'low_lighting_or_unclear', 'unsupported_content'."
    )
    approximate_face_shape: Literal["oval", "square", "round", "heart", "oblong", "uncertain"] = Field(
        default="uncertain",
        description="Approximate face shape estimate to suggest collar styles and eyewear."
    )
    visible_hair_characteristics: Optional[str] = Field(
        default=None,
        description="Visible hair color/texture/length if detectable (e.g. 'short dark brown, textured')."
    )
    skin_tone_undertone: SkinToneUndertoneEstimate = Field(
        default_factory=lambda: SkinToneUndertoneEstimate(undertone="uncertain", confidence="unreliable")
    )
    suitable_color_families: List[str] = Field(
        default_factory=list,
        description="Recommended color palettes that complement the user's contrast and undertone."
    )
    avoid_colors: List[str] = Field(
        default_factory=list,
        description="Colors that may clash or wash out the estimated undertone."
    )
    inferred_style_vibes: List[str] = Field(
        default_factory=list,
        description="Fashion styles inferred from visible garments or silhouette (e.g. 'smart casual', 'minimalist')."
    )
    outfit_style_suggestions: List[str] = Field(
        default_factory=list,
        description="Practical clothing cut, collar, and layering advice."
    )
    user_reviewed: bool = Field(
        default=False,
        description="Whether the user has reviewed or manually edited these estimates."
    )
    image_storage_uri: Optional[str] = Field(
        default=None,
        description="Cloud Storage gs:// URI or secure storage reference."
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last update."
    )

class ClothingItemAnalysis(BaseModel):
    category: Literal["topwear", "bottomwear", "outerwear", "footwear", "accessory", "uncertain"] = Field(
        description="Major garment category."
    )
    subcategory: str = Field(
        description="Specific garment type, e.g. oxford shirt, tapered chinos, denim jacket, chelsea boots."
    )
    color: str = Field(
        description="Primary visible color."
    )
    secondary_colors: List[str] = Field(
        default_factory=list,
        description="Secondary accent colors, buttons, stitching, or patterns."
    )
    pattern: Literal["solid", "striped", "checked", "plaid", "floral", "graphic", "textured", "uncertain"] = Field(
        default="solid",
        description="Visual surface pattern."
    )
    material: Optional[str] = Field(
        default=None,
        description="Inferred fabric/material (e.g. cotton twill, linen, denim, wool, leather) only if reasonably identifiable."
    )
    style: Literal["casual", "smart_casual", "formal", "streetwear", "athletic", "rugged"] = Field(
        default="casual",
        description="Dominant aesthetic or style formality."
    )
    season: List[str] = Field(
        default_factory=lambda: ["all-season"],
        description="Appropriate seasons, e.g. ['spring', 'summer'] or ['all-season']."
    )
    occasions: List[str] = Field(
        default_factory=list,
        description="Suitable contexts, e.g. ['work', 'date night', 'weekend', 'casual outing']."
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Styling tags, e.g. ['breathable', 'relaxed-fit', 'collar', 'versatile']."
    )
    confidence: Literal["high", "moderate", "low"] = Field(
        default="moderate",
        description="Confidence of visual classification."
    )
    image_storage_uri: Optional[str] = Field(
        default=None,
        description="Cloud Storage gs:// URI or accessible image path."
    )

class OutfitItem(BaseModel):
    item_id: Optional[str] = Field(default=None, description="Wardrobe item ID if from user closet.")
    category: str = Field(description="Garment category: topwear, bottomwear, outerwear, footwear, accessory.")
    subcategory: str = Field(description="Garment type, e.g. oxford button-down shirt, tapered chinos.")
    color: str = Field(description="Garment color.")
    source: Literal["wardrobe", "catalog"] = Field(default="wardrobe")
    image_url: Optional[str] = None

class OutfitRecommendation(BaseModel):
    outfit_id: str = Field(description="Unique identifier for generated outfit.")
    title: str = Field(description="Descriptive title of the ensemble.")
    occasion: str = Field(description="Target occasion.")
    formality: str = Field(description="Formality level, e.g. casual, smart_casual, formal.")
    items: List[OutfitItem] = Field(description="List of items in the outfit.")
    items_summary: List[str] = Field(description="Human readable summary of garments.")
    color_harmony: str = Field(description="Color harmony classification, e.g. neutral contrast, earth tone.")
    rationale: str = Field(description="Concise fashion explanation of why pieces work and match user profile.")
    wardrobe_only: bool = Field(default=True, description="Whether strictly from owned wardrobe.")
    source: str = Field(default="wardrobe_only", description="Source indicator for backwards compatibility.")

class ProductItem(BaseModel):
    product_id: str = Field(description="Unique product identifier.")
    title: str = Field(description="Garment product name.")
    category: str = Field(description="Category: topwear, bottomwear, outerwear, footwear, accessory.")
    subcategory: str = Field(description="Specific garment subcategory.")
    color: str = Field(description="Primary color.")
    price: float = Field(description="Price in INR.")
    currency: str = Field(default="INR", description="Currency code.")
    brand: str = Field(description="Brand name.")
    rating: float = Field(default=4.5, description="Product rating out of 5.")
    image_url: str = Field(description="Image URL.")
    product_url: str = Field(description="Store link or PDP URL.")
    style: str = Field(default="casual", description="Style formality.")
    material: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    relevance_score: float = Field(default=1.0, description="Score calculated based on query, profile, and occasion.")
    match_rationale: Optional[str] = Field(default=None, description="Why this product matches user style profile and budget.")

class VisualizationResult(BaseModel):
    visualization_id: str = Field(description="Unique ID for visualization run.")
    image_url: Optional[str] = Field(default=None, description="Accessible URL or base64 data URI of visualization.")
    status: Literal["success", "fallback_sketch", "failed", "disabled"] = Field(description="Generation status.")
    ai_generated_label: str = Field(
        default="AI-Generated Approximate Concept Visualization",
        description="Mandatory clear label."
    )
    disclaimer: str = Field(
        default="Simulated conceptual visualization only. Does not represent precise physical fit, exact fabric drape, or true personal appearance.",
        description="Responsible AI disclaimer."
    )
    prompt_used: Optional[str] = Field(default=None, description="Prompt dispatched to generation engine.")
    error_message: Optional[str] = None
