"""
Agent Evaluation Suite for StyleMate AI.
Evaluates:
- Tool selection accuracy
- Tool arguments correctness
- Wardrobe & style profile grounding
- Budget ceiling adherence
- Negative constraint (banned color) enforcement
- Context retention across iterative outfit adjustments
- Hallucination resistance on limited/empty wardrobe
- Ambiguity and uncertainty handling
- Responsible AI & privacy guardrails
"""

import os
import json
import pytest
from typing import Dict, Any, List

from app.tools import (
    generate_outfit,
    get_wardrobe,
    get_style_profile,
    search_products,
    check_items_match,
    analyze_clothing,
    analyze_style_profile
)
from app.schemas import OutfitRecommendation, ProductItem, ClothingItemAnalysis


@pytest.fixture(scope="module")
def eval_dataset():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "eval_dataset.json")
    with open(fixture_path, "r") as f:
        return json.load(f)


# Scenario 1: Outfit using existing wardrobe
def test_scenario_01_existing_wardrobe():
    res_raw = generate_outfit(occasion="casual outing", user_id="default_user", wardrobe_only=True)
    res = json.loads(res_raw)
    assert res["status"] == "success"
    outfit = res["outfit"]
    
    # Assert wardrobe grounding
    assert outfit["wardrobe_only"] is True
    assert len(outfit["items"]) >= 2
    for item in outfit["items"]:
        assert item["source"] == "wardrobe"
        assert item["item_id"] is not None


# Scenario 2: Date outfit
def test_scenario_02_date_outfit():
    res_raw = generate_outfit(occasion="dinner date", user_id="default_user", formality="smart_casual")
    res = json.loads(res_raw)
    assert res["status"] == "success"
    outfit = res["outfit"]
    assert outfit["formality"] == "smart_casual"
    assert "date" in outfit["occasion"].lower()
    assert "rationale" in outfit


# Scenario 3: Office outfit
def test_scenario_03_office_outfit():
    res_raw = generate_outfit(occasion="office presentation", user_id="default_user", formality="smart_casual")
    res = json.loads(res_raw)
    assert res["status"] == "success"
    outfit = res["outfit"]
    assert outfit["formality"] == "smart_casual"


# Scenario 4: Casual weekend outfit
def test_scenario_04_casual_weekend():
    res_raw = generate_outfit(occasion="casual weekend", user_id="default_user", formality="casual")
    res = json.loads(res_raw)
    assert res["status"] == "success"
    outfit = res["outfit"]
    assert outfit["formality"] == "casual"


# Scenario 5: User has limited wardrobe (hallucination resistance)
def test_scenario_05_limited_wardrobe():
    res_raw = generate_outfit(occasion="party", user_id="empty_closet_eval_user", wardrobe_only=True)
    res = json.loads(res_raw)
    # MUST refuse and NEVER invent unavailable wardrobe items
    assert res["status"] == "error"
    assert "empty" in res["message"].lower()


# Scenario 6: User explicitly excludes a color
def test_scenario_06_color_exclusion():
    res_raw = generate_outfit(
        occasion="dinner date",
        user_id="default_user",
        excluded_colors=["navy", "navy blue"]
    )
    res = json.loads(res_raw)
    assert res["status"] == "success"
    outfit = res["outfit"]
    for item in outfit["items"]:
        assert "navy" not in item["color"].lower()


# Scenario 7: User requests a specific budget (budget adherence)
def test_scenario_07_budget_request():
    max_b = 1500.0
    res_raw = search_products(query="black shirt", category="topwear", max_price=max_b, color="black")
    res = json.loads(res_raw)
    assert res["status"] == "success"
    products = res["products"]
    assert len(products) > 0
    for p in products:
        assert p["price"] <= max_b
        assert p["category"] == "topwear"
        assert "black" in p["color"].lower()


# Scenario 8: User asks to replace only one outfit component
def test_scenario_08_replace_component():
    # Initial generation
    init_res = json.loads(generate_outfit(occasion="dinner date", user_id="default_user"))
    initial_top = next(i for i in init_res["outfit"]["items"] if i["category"] == "topwear")
    initial_bottom = next(i for i in init_res["outfit"]["items"] if i["category"] == "bottomwear")

    # Modify bottomwear only
    mod_res = json.loads(generate_outfit(user_id="default_user", modify_category="bottomwear"))
    assert mod_res["status"] == "success"
    mod_outfit = mod_res["outfit"]
    
    mod_top = next(i for i in mod_outfit["items"] if i["category"] == "topwear")
    mod_bottom = next(i for i in mod_outfit["items"] if i["category"] == "bottomwear")

    # Top preserved, bottom swapped
    assert mod_top["item_id"] == initial_top["item_id"]
    assert mod_bottom["item_id"] != initial_bottom["item_id"]


# Scenario 9: User asks whether two items match
def test_scenario_09_items_match():
    res_raw = check_items_match("olive overshirt", "beige chinos", user_id="default_user")
    res = json.loads(res_raw)
    assert res["status"] == "success"
    assert res["verdict"] in ["Great Match", "Good Match"]
    assert res["compatibility_score"] >= 70
    assert "explanation" in res


# Scenario 10: User asks for shopping recommendations
def test_scenario_10_shopping_recommendations():
    res_raw = search_products(query="date shirt", max_price=2000.0, user_id="default_user")
    res = json.loads(res_raw)
    assert res["status"] == "success"
    assert len(res["products"]) > 0
    for p in res["products"]:
        assert p["price"] <= 2000.0


# Scenario 11: User asks to use only wardrobe items
def test_scenario_11_only_wardrobe_items():
    res_raw = generate_outfit(occasion="coffee", user_id="default_user", wardrobe_only=True)
    res = json.loads(res_raw)
    assert res["status"] == "success"
    assert res["outfit"]["wardrobe_only"] is True
    for item in res["outfit"]["items"]:
        assert item["source"] == "wardrobe"


# Scenario 12: User uploads an ambiguous clothing image
def test_scenario_12_ambiguous_image():
    res_raw = analyze_clothing("blurry_unclear_dark_photo.jpg")
    res = json.loads(res_raw)
    assert res["status"] == "success"
    analysis = res["analysis"]
    assert analysis["confidence"] == "low"
    assert analysis["category"] == "uncertain"


# Scenario 13: User provides insufficient information
def test_scenario_13_insufficient_information():
    # User calls get_style_profile to check baseline context
    prof_raw = get_style_profile("default_user")
    prof = json.loads(prof_raw)
    assert prof["status"] == "success"
    # When generating without occasion, defaults to casual and provides coherent styling
    res_raw = generate_outfit(user_id="default_user")
    res = json.loads(res_raw)
    assert res["status"] == "success"
    assert res["outfit"]["formality"] == "casual"
