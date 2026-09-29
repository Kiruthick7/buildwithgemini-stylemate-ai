import pytest
import json
from app.tools import (
    generate_outfit,
    get_wardrobe,
    get_style_profile,
    add_wardrobe_item
)
from app.schemas import OutfitRecommendation

def test_full_context_reasoning():
    # 1. User asks: "Give me something for a dinner date"
    raw_res = generate_outfit(
        occasion="dinner date",
        user_id="default_user",
        formality="smart_casual",
        weather_context="chilly evening",
        wardrobe_only=True
    )
    res = json.loads(raw_res)
    assert res["status"] == "success"
    outfit = res["outfit"]
    
    # Verify OutfitRecommendation structure
    model = OutfitRecommendation(**outfit)
    assert model.occasion == "dinner date"
    assert model.formality == "smart_casual"
    assert model.wardrobe_only is True

    # Grounded items from default_user's wardrobe
    categories = [i.category for i in model.items]
    assert "topwear" in categories
    assert "bottomwear" in categories
    assert "outerwear" in categories  # Selected because of chilly evening context
    assert "footwear" in categories

    # Verify fashion rationale
    assert "chilly" in model.rationale.lower() or "cooler" in model.rationale.lower()
    assert "undertone" in model.rationale.lower()

def test_iterative_outfit_modification():
    # Step 1: Initial outfit generation for dinner date
    initial_raw = generate_outfit(
        occasion="dinner date",
        user_id="default_user",
        formality="smart_casual",
        wardrobe_only=True
    )
    initial_outfit = json.loads(initial_raw)["outfit"]
    initial_top = next(i for i in initial_outfit["items"] if i["category"] == "topwear")
    initial_bottom = next(i for i in initial_outfit["items"] if i["category"] == "bottomwear")

    # Step 2: User says "I don't like the pants" -> modify_category="bottomwear"
    modified_raw = generate_outfit(
        user_id="default_user",
        modify_category="bottomwear",
        feedback_instruction="I don't like the pants"
    )
    mod_res = json.loads(modified_raw)
    assert mod_res["status"] == "success"
    mod_outfit = mod_res["outfit"]

    mod_top = next(i for i in mod_outfit["items"] if i["category"] == "topwear")
    mod_bottom = next(i for i in mod_outfit["items"] if i["category"] == "bottomwear")

    # The top MUST remain identical (preserving the rest of the outfit)
    assert mod_top["item_id"] == initial_top["item_id"]
    assert mod_top["color"] == initial_top["color"]

    # The pants MUST be different from the initial pants
    assert mod_bottom["item_id"] != initial_bottom["item_id"]
    assert "modified the bottomwear" in mod_outfit["rationale"].lower()

def test_strict_wardrobe_only_enforcement():
    user = "empty_closet_user"
    # When wardrobe_only is True and user has no clothes, it MUST refuse and NEVER invent items
    res_raw = generate_outfit(
        occasion="party",
        user_id=user,
        wardrobe_only=True
    )
    res = json.loads(res_raw)
    assert res["status"] == "error"
    assert "empty" in res["message"].lower()

def test_banned_color_respect():
    # User dislikes navy blue for this outfit
    res_raw = generate_outfit(
        occasion="casual Friday",
        user_id="default_user",
        excluded_colors=["navy blue", "navy"],
        wardrobe_only=True
    )
    res = json.loads(res_raw)
    assert res["status"] == "success"
    outfit = res["outfit"]
    
    # Ensure NO navy blue garments were picked
    for item in outfit["items"]:
        assert "navy" not in item["color"].lower()
