import pytest
import json
from app.tools import (
    analyze_clothing,
    add_wardrobe_item,
    get_wardrobe,
    update_wardrobe_item,
    remove_wardrobe_item,
    generate_outfit
)
from app.schemas import ClothingItemAnalysis

def test_analyze_clothing_structured():
    # Test shirt analysis
    raw = analyze_clothing(image_storage_uri_or_hint="gs://bucket/wardrobe/u1/navy_oxford_shirt.jpg")
    res = json.loads(raw)
    assert res["status"] == "success"
    analysis = res["analysis"]
    
    item_model = ClothingItemAnalysis(**analysis)
    assert item_model.category == "topwear"
    assert "oxford" in item_model.subcategory
    assert item_model.color == "navy blue"
    assert item_model.style == "smart_casual"
    assert "classic" in item_model.tags
    assert item_model.confidence == "high"

def test_analyze_clothing_unclear():
    # Test unclear image
    raw = analyze_clothing(image_storage_uri_or_hint="blurry_dark_photo.jpg")
    res = json.loads(raw)
    analysis = res["analysis"]
    item_model = ClothingItemAnalysis(**analysis)
    assert item_model.category == "uncertain"
    assert item_model.confidence == "low"

def test_wardrobe_lifecycle():
    user = "test_user_wardrobe"
    
    # 1. Add item
    add_raw = add_wardrobe_item(
        category="outerwear",
        subcategory="bomber jacket",
        color="olive green",
        secondary_colors=["black zip"],
        pattern="solid",
        material="nylon",
        style="casual",
        season=["autumn", "spring"],
        occasions=["weekend", "evening"],
        tags=["lightweight", "sporty"],
        user_id=user,
        is_favorite=False
    )
    add_res = json.loads(add_raw)
    assert add_res["status"] == "success"
    item_id = add_res["item"]["id"]

    # 2. Retrieve wardrobe
    get_raw = get_wardrobe(user_id=user)
    get_res = json.loads(get_raw)
    assert get_res["count"] == 1
    assert get_res["items"][0]["subcategory"] == "bomber jacket"

    # 3. Update / Favorite item
    up_raw = update_wardrobe_item(
        item_id=item_id,
        user_id=user,
        is_favorite=True,
        color="dark olive green"
    )
    up_res = json.loads(up_raw)
    assert up_res["status"] == "success"
    assert up_res["item"]["is_favorite"] is True
    assert up_res["item"]["color"] == "dark olive green"

    # 4. Filter favorites only
    fav_raw = get_wardrobe(user_id=user, favorite_only=True)
    fav_res = json.loads(fav_raw)
    assert fav_res["count"] == 1

    # 5. Delete item
    del_raw = remove_wardrobe_item(item_id=item_id, user_id=user)
    del_res = json.loads(del_raw)
    assert del_res["status"] == "success"

    # Verify empty
    get_raw_after = get_wardrobe(user_id=user)
    assert json.loads(get_raw_after)["count"] == 0

def test_agent_reasoning_over_wardrobe():
    # Tests that generate_outfit synthesizes an outfit from the user's specific clothes
    # and provides a fashion rationale explaining harmony & undertone
    user = "default_user"
    res_raw = generate_outfit(
        occasion="dinner date",
        user_id=user,
        preferred_style="smart casual"
    )
    res = json.loads(res_raw)
    assert res["status"] == "success"
    outfit = res["outfit"]
    assert len(outfit["items"]) >= 2
    assert "navy blue" in outfit["rationale"].lower() or "top" in outfit["rationale"].lower()
    assert "rationale" in outfit
    assert len(outfit["items_summary"]) >= 2
