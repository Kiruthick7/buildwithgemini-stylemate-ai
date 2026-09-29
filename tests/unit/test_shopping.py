import pytest
import json
from app.tools import search_products
from app.shopping_provider import (
    get_shopping_provider,
    set_shopping_provider,
    MockCatalogShoppingProvider,
    BaseShoppingProvider
)
from app.schemas import ProductItem

def test_budget_adherence_under_1500():
    # User query: "I need a black shirt under ₹1500"
    raw_res = search_products(
        query="black shirt",
        category="topwear",
        max_price=1500.0,
        color="black",
        user_id="default_user"
    )
    res = json.loads(raw_res)
    assert res["status"] == "success"
    products = res["products"]
    assert len(products) > 0

    for prod in products:
        # Strict Budget Adherence
        assert prod["price"] <= 1500.0
        # Category matching
        assert prod["category"] == "topwear"
        # Color matching
        assert "black" in prod["color"].lower()
        # Non-empty styling rationale
        assert "match_rationale" in prod
        assert len(prod["match_rationale"]) > 0

def test_date_outfit_under_2000():
    # User query: "I need something for a date under ₹2000"
    raw_res = search_products(
        query="date night shirt",
        max_price=2000.0,
        occasion="dinner date",
        user_id="default_user"
    )
    res = json.loads(raw_res)
    assert res["status"] == "success"
    products = res["products"]
    assert len(products) > 0
    for prod in products:
        assert prod["price"] <= 2000.0

def test_category_matching_and_filtering():
    # Bottomwear query under 2000
    raw_res = search_products(
        query="chinos",
        category="bottomwear",
        max_price=2000.0,
        user_id="default_user"
    )
    res = json.loads(raw_res)
    assert res["status"] == "success"
    products = res["products"]
    for prod in products:
        assert prod["category"] == "bottomwear"
        assert prod["price"] <= 2000.0

def test_pairing_with_wardrobe_item():
    # "Find a shirt that works with my beige pants" (w_3 is beige chinos in default_user wardrobe)
    raw_res = search_products(
        query="shirt",
        category="topwear",
        pairing_with_wardrobe_item_id="w_3",
        max_price=2000.0,
        user_id="default_user"
    )
    res = json.loads(raw_res)
    assert res["status"] == "success"
    products = res["products"]
    assert len(products) > 0
    # Confirms rationale references owned pants
    assert "chinos" in products[0]["match_rationale"].lower() or "beige" in products[0]["match_rationale"].lower()

def test_pluggable_provider_abstraction():
    # Demonstrates replacing the shopping provider
    class CustomTestProvider(BaseShoppingProvider):
        def search(self, query, category=None, max_price=None, color=None, style=None, limit=5):
            return [
                ProductItem(
                    product_id="test_custom_1",
                    title="Custom Verified Sustainable Hemp Shirt",
                    category="topwear",
                    subcategory="hemp shirt",
                    color="natural ecru",
                    price=1199.0,
                    currency="INR",
                    brand="EcoWear",
                    rating=4.9,
                    image_url="https://sample.com/hemp.jpg",
                    product_url="https://sample.com/buy",
                    style="smart_casual",
                    tags=["eco"]
                )
            ]

    original_provider = get_shopping_provider()
    try:
        set_shopping_provider(CustomTestProvider())
        raw_res = search_products(query="hemp shirt", max_price=1500.0)
        res = json.loads(raw_res)
        assert res["status"] == "success"
        assert res["products"][0]["brand"] == "EcoWear"
        assert res["products"][0]["price"] == 1199.0
    finally:
        set_shopping_provider(original_provider)
