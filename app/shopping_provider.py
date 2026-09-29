"""
Shopping Catalog Provider Abstraction for StyleMate AI.
Enables pluggable e-commerce backends (Google Shopping, Vertex Search, mock retail catalogs).
Strictly adheres to real catalog availability, budgets, and style profile criteria.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas import ProductItem

# Curated catalog of realistic, budget-friendly men's fashion essentials
MOCK_PRODUCT_CATALOG: List[Dict[str, Any]] = [
    {
        "product_id": "p_top_1",
        "title": "Classic Oxford Cotton Button-Down Shirt",
        "category": "topwear",
        "subcategory": "oxford button-down shirt",
        "color": "black",
        "price": 1299.0,
        "currency": "INR",
        "brand": "CottonCraft",
        "rating": 4.6,
        "image_url": "https://storage.googleapis.com/sample-assets/black_oxford.jpg",
        "product_url": "https://shop.stylemate.ai/products/black-oxford-shirt",
        "style": "smart_casual",
        "material": "100% cotton",
        "tags": ["collar", "breathable", "minimalist", "date-ready"]
    },
    {
        "product_id": "p_top_2",
        "title": "Heavyweight Regular Fit Crewneck Tee",
        "category": "topwear",
        "subcategory": "crewneck t-shirt",
        "color": "black",
        "price": 799.0,
        "currency": "INR",
        "brand": "UrbanBasics",
        "rating": 4.4,
        "image_url": "https://storage.googleapis.com/sample-assets/black_tee.jpg",
        "product_url": "https://shop.stylemate.ai/products/black-crewneck-tee",
        "style": "casual",
        "material": "cotton",
        "tags": ["everyday", "minimal", "streetwear"]
    },
    {
        "product_id": "p_top_3",
        "title": "Breathable French Linen Shirt",
        "category": "topwear",
        "subcategory": "linen shirt",
        "color": "olive green",
        "price": 1899.0,
        "currency": "INR",
        "brand": "BreezeStudio",
        "rating": 4.7,
        "image_url": "https://storage.googleapis.com/sample-assets/olive_linen_shirt.jpg",
        "product_url": "https://shop.stylemate.ai/products/olive-linen-shirt",
        "style": "smart_casual",
        "material": "pure linen",
        "tags": ["summer", "vacation", "date-ready", "earthy"]
    },
    {
        "product_id": "p_top_4",
        "title": "Tailored Slim Dress Shirt",
        "category": "topwear",
        "subcategory": "formal dress shirt",
        "color": "navy blue",
        "price": 1499.0,
        "currency": "INR",
        "brand": "Sartorial",
        "rating": 4.8,
        "image_url": "https://storage.googleapis.com/sample-assets/navy_dress_shirt.jpg",
        "product_url": "https://shop.stylemate.ai/products/navy-dress-shirt",
        "style": "formal",
        "material": "micro twill",
        "tags": ["formal", "date-ready", "office"]
    },
    {
        "product_id": "p_top_5",
        "title": "Relaxed Camp Collar Cuban Shirt",
        "category": "topwear",
        "subcategory": "camp collar shirt",
        "color": "terracotta",
        "price": 1199.0,
        "currency": "INR",
        "brand": "NomadWear",
        "rating": 4.5,
        "image_url": "https://storage.googleapis.com/sample-assets/terracotta_cuban_shirt.jpg",
        "product_url": "https://shop.stylemate.ai/products/terracotta-cuban-shirt",
        "style": "casual",
        "material": "viscose rayon blend",
        "tags": ["date-ready", "warm undertone", "relaxed"]
    },
    {
        "product_id": "p_top_6",
        "title": "Premium Structured Denim Overshirt",
        "category": "topwear",
        "subcategory": "denim overshirt",
        "color": "dark indigo",
        "price": 2499.0,
        "currency": "INR",
        "brand": "DenimCraft",
        "rating": 4.7,
        "image_url": "https://storage.googleapis.com/sample-assets/denim_overshirt.jpg",
        "product_url": "https://shop.stylemate.ai/products/indigo-denim-overshirt",
        "style": "smart_casual",
        "material": "cotton denim",
        "tags": ["rugged", "layering", "durable"]
    },
    {
        "product_id": "p_bot_1",
        "title": "Slim Tapered Stretch Chinos",
        "category": "bottomwear",
        "subcategory": "tapered chinos",
        "color": "warm beige",
        "price": 1599.0,
        "currency": "INR",
        "brand": "CottonCraft",
        "rating": 4.6,
        "image_url": "https://storage.googleapis.com/sample-assets/beige_chinos_shop.jpg",
        "product_url": "https://shop.stylemate.ai/products/slim-chinos-beige",
        "style": "smart_casual",
        "material": "stretch cotton twill",
        "tags": ["versatile", "office", "date-ready"]
    },
    {
        "product_id": "p_bot_2",
        "title": "Relaxed Straight-Leg Pleated Trousers",
        "category": "bottomwear",
        "subcategory": "pleated trousers",
        "color": "charcoal grey",
        "price": 1999.0,
        "currency": "INR",
        "brand": "TailorLane",
        "rating": 4.7,
        "image_url": "https://storage.googleapis.com/sample-assets/charcoal_trousers.jpg",
        "product_url": "https://shop.stylemate.ai/products/pleated-trousers-charcoal",
        "style": "smart_casual",
        "material": "poly-viscose blend",
        "tags": ["drape", "modern fit", "sophisticated"]
    },
    {
        "product_id": "p_foot_1",
        "title": "Low-Top Minimalist Court Leather Sneakers",
        "category": "footwear",
        "subcategory": "minimal leather sneakers",
        "color": "white",
        "price": 1999.0,
        "currency": "INR",
        "brand": "StepMinimal",
        "rating": 4.8,
        "image_url": "https://storage.googleapis.com/sample-assets/white_court_sneakers.jpg",
        "product_url": "https://shop.stylemate.ai/products/white-court-sneakers",
        "style": "smart_casual",
        "material": "synthetic leather",
        "tags": ["versatile", "clean", "date-ready"]
    }
]


class BaseShoppingProvider(ABC):
    """Abstract base class for e-commerce search providers."""

    @abstractmethod
    def search(
        self,
        query: str,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        color: Optional[str] = None,
        style: Optional[str] = None,
        limit: int = 5
    ) -> List[ProductItem]:
        """Searches products adhering to availability, price, and category boundaries."""
        pass


class MockCatalogShoppingProvider(BaseShoppingProvider):
    """Production-grade mock provider implementing realistic catalog filtering, ranking, and budget adherence."""

    def __init__(self, catalog: Optional[List[Dict[str, Any]]] = None):
        self._catalog = catalog or MOCK_PRODUCT_CATALOG

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        color: Optional[str] = None,
        style: Optional[str] = None,
        limit: int = 5
    ) -> List[ProductItem]:
        query_words = set(query.lower().split()) if query else set()
        results: List[ProductItem] = []

        for item in self._catalog:
            # 1. Budget Adherence: Strictly discard if price exceeds max_price
            if max_price is not None and item["price"] > max_price:
                continue

            # 2. Category matching
            if category:
                cat_lower = category.lower()
                if item["category"].lower() != cat_lower:
                    # check subcategory match e.g. "shirt" -> topwear
                    if cat_lower in ["shirt", "t-shirt", "top"] and item["category"] != "topwear":
                        continue
                    elif cat_lower in ["pant", "pants", "chinos", "jeans", "bottom"] and item["category"] != "bottomwear":
                        continue
                    elif cat_lower not in ["shirt", "t-shirt", "top", "pant", "pants", "chinos", "jeans", "bottom"]:
                        if item["category"].lower() != cat_lower:
                            continue

            # 3. Color matching
            if color:
                color_lower = color.lower()
                if color_lower not in item["color"].lower() and item["color"].lower() not in color_lower:
                    continue

            # 4. Relevance ranking
            relevance = 1.0
            item_text = f"{item['title']} {item['subcategory']} {item['color']} {item['style']} {' '.join(item.get('tags', []))}".lower()

            for w in query_words:
                if w in item_text:
                    relevance += 1.5

            if style and style.lower() in item["style"].lower():
                relevance += 1.0

            results.append(ProductItem(
                product_id=item["product_id"],
                title=item["title"],
                category=item["category"],
                subcategory=item["subcategory"],
                color=item["color"],
                price=item["price"],
                currency=item["currency"],
                brand=item["brand"],
                rating=item["rating"],
                image_url=item["image_url"],
                product_url=item["product_url"],
                style=item["style"],
                material=item.get("material"),
                tags=item.get("tags", []),
                relevance_score=relevance
            ))

        # Sort by relevance desc, then price asc
        results.sort(key=lambda p: (-p.relevance_score, p.price))
        return results[:limit]


# Global provider instance behind the abstraction boundary
_current_shopping_provider: BaseShoppingProvider = MockCatalogShoppingProvider()

def get_shopping_provider() -> BaseShoppingProvider:
    return _current_shopping_provider

def set_shopping_provider(provider: BaseShoppingProvider) -> None:
    global _current_shopping_provider
    _current_shopping_provider = provider
