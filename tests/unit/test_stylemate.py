import pytest
import json
from app.tools import (
    get_style_profile,
    update_style_profile,
    analyze_style_profile,
    get_wardrobe,
    add_wardrobe_item,
    remove_wardrobe_item,
    analyze_clothing_item,
    generate_outfit,
    save_outfit
)
from app.agent import root_agent

def test_agent_initialization():
    assert root_agent.name == "stylemate_agent"
    assert len(root_agent.tools) >= 9
    tool_names = [t.__name__ for t in root_agent.tools]
    assert "get_style_profile" in tool_names
    assert "get_wardrobe" in tool_names
    assert "generate_outfit" in tool_names
    assert "save_outfit" in tool_names

def test_style_profile_retrieval_and_update():
    res = json.loads(get_style_profile(user_id="default_user"))
    assert res["status"] == "success"
    profile = res["profile"]
    assert "approximate_face_shape" in profile
    assert "skin_tone_undertone" in profile

    # Update profile
    up_res = json.loads(update_style_profile(
        user_id="default_user",
        undertone="warm",
        suitable_color_families=["olive", "navy"],
        avoid_colors=["neon yellow"]
    ))
    assert up_res["status"] == "success"
    updated = up_res["profile"]
    assert updated["skin_tone_undertone"]["undertone"] == "warm"
    assert "neon yellow" in updated["avoid_colors"]

def test_wardrobe_crud():
    # Initial wardrobe
    w_res = json.loads(get_wardrobe(user_id="default_user"))
    assert w_res["status"] == "success"
    initial_count = w_res["count"]
    assert initial_count > 0

    # Add item
    add_res = json.loads(add_wardrobe_item(
        category="topwear",
        sub_category="flannel shirt",
        color="burgundy",
        formality="casual",
        user_id="default_user"
    ))
    assert add_res["status"] == "success"
    new_item_id = add_res["item"]["id"]

    # Verify added
    w_res_2 = json.loads(get_wardrobe(user_id="default_user"))
    assert w_res_2["count"] == initial_count + 1

    # Remove item
    del_res = json.loads(remove_wardrobe_item(item_id=new_item_id, user_id="default_user"))
    assert del_res["status"] == "success"

def test_outfit_generator_wardrobe_only():
    gen_res = json.loads(generate_outfit(
        occasion="dinner date",
        user_id="default_user",
        excluded_colors=["bright", "neon"]
    ))
    assert gen_res["status"] == "success"
    outfit = gen_res["outfit"]
    assert len(outfit["items"]) >= 2
    assert outfit["source"] == "wardrobe_only"
    assert "rationale" in outfit
    # Check that avoided colors are not present
    for item in outfit["items"]:
        assert "neon" not in item.get("color", "").lower()

def test_save_outfit():
    save_res = json.loads(save_outfit(
        name="Date Night Special",
        items_summary=["Navy Oxford Shirt", "Beige Chinos", "White Sneakers"],
        occasion="dinner date",
        rationale="Classic neutral contrast",
        user_id="default_user",
        collection_tag="Date Night"
    ))
    assert save_res["status"] == "success"
    assert save_res["outfit"]["collection_tag"] == "Date Night"
