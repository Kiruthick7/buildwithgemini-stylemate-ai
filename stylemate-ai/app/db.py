"""
Data persistence and mock/Firestore backend for StyleMate AI.
Supports both local in-memory storage (with seed data) and Google Cloud Firestore.
"""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from google.cloud import firestore

USE_FIRESTORE = os.getenv("USE_FIRESTORE", "false").lower() in ("true", "1")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-5c279e7dc881")

_firestore_client = None

def get_firestore_client():
    global _firestore_client
    if not USE_FIRESTORE:
        return None
    if _firestore_client is None:
        try:
            _firestore_client = firestore.Client(project=PROJECT_ID)
        except Exception as e:
            print(f"Firestore connection fallback: {e}")
            _firestore_client = None
    return _firestore_client


# In-memory storage structures for robust local testing and rapid prototyping
_MEMORY_DB = {
    "users": {},
    "style_profiles": {
        "default_user": {
            "user_id": "default_user",
            "is_valid_fashion_portrait": True,
            "approximate_face_shape": "oval",
            "visible_hair_characteristics": "dark brown textured, short to medium length",
            "skin_tone_undertone": {
                "undertone": "neutral-warm",
                "confidence": "moderate",
                "disclaimer": "Visual estimation based on reference lighting; user confirmation advised"
            },
            "suitable_color_families": [
                "navy blue", "olive green", "terracotta", "warm beige", "burgundy", "charcoal grey", "cream"
            ],
            "avoid_colors": ["neon yellow", "bright magenta", "electric lime"],
            "inferred_style_vibes": ["smart casual", "clean minimalist"],
            "outfit_style_suggestions": [
                "Button-down Oxford shirts and structured overshirts complement your frame."
            ],
            "user_reviewed": True,
            "updated_at": datetime.now().isoformat(),
        }
    },
    "wardrobe_items": {
        "w_1": {
            "id": "w_1",
            "userId": "default_user",
            "category": "topwear",
            "sub_category": "oxford button-down shirt",
            "color": "navy blue",
            "color_family": "navy",
            "pattern": "solid",
            "material": "cotton",
            "formality": "smart_casual",
            "seasons": ["all-season", "spring", "autumn"],
            "is_favorite": True,
            "tags": ["versatile", "classic", "date-ready"],
            "image_url": "https://storage.googleapis.com/sample-assets/navy_oxford.jpg"
        },
        "w_2": {
            "id": "w_2",
            "userId": "default_user",
            "category": "topwear",
            "sub_category": "relaxed crewneck t-shirt",
            "color": "cream",
            "color_family": "white/cream",
            "pattern": "solid",
            "material": "heavyweight cotton",
            "formality": "casual",
            "seasons": ["spring", "summer"],
            "is_favorite": False,
            "tags": ["minimalist", "everyday", "breathable"],
            "image_url": "https://storage.googleapis.com/sample-assets/cream_tee.jpg"
        },
        "w_3": {
            "id": "w_3",
            "userId": "default_user",
            "category": "bottomwear",
            "sub_category": "tapered chinos",
            "color": "warm beige",
            "color_family": "beige/tan",
            "pattern": "solid",
            "material": "cotton twill",
            "formality": "smart_casual",
            "seasons": ["all-season"],
            "is_favorite": True,
            "tags": ["tailored", "versatile", "neutral"],
            "image_url": "https://storage.googleapis.com/sample-assets/beige_chinos.jpg"
        },
        "w_4": {
            "id": "w_4",
            "userId": "default_user",
            "category": "bottomwear",
            "sub_category": "slim selvedge jeans",
            "color": "charcoal grey",
            "color_family": "grey/black",
            "pattern": "solid",
            "material": "denim",
            "formality": "casual",
            "seasons": ["all-season", "autumn", "winter"],
            "is_favorite": False,
            "tags": ["rugged", "durable"],
            "image_url": "https://storage.googleapis.com/sample-assets/charcoal_jeans.jpg"
        },
        "w_5": {
            "id": "w_5",
            "userId": "default_user",
            "category": "outerwear",
            "sub_category": "trucker overshirt jacket",
            "color": "olive green",
            "color_family": "olive",
            "pattern": "solid",
            "material": "cotton canvas",
            "formality": "smart_casual",
            "seasons": ["autumn", "spring"],
            "is_favorite": True,
            "tags": ["layering", "earthy"],
            "image_url": "https://storage.googleapis.com/sample-assets/olive_overshirt.jpg"
        },
        "w_6": {
            "id": "w_6",
            "userId": "default_user",
            "category": "footwear",
            "sub_category": "minimal leather sneakers",
            "color": "white",
            "color_family": "white/cream",
            "pattern": "solid",
            "material": "leather",
            "formality": "smart_casual",
            "seasons": ["all-season"],
            "is_favorite": True,
            "tags": ["clean", "versatile"],
            "image_url": "https://storage.googleapis.com/sample-assets/white_sneakers.jpg"
        }
    },
    "outfits": {}
}


def get_style_profile_record(user_id: str) -> Optional[Dict[str, Any]]:
    client = get_firestore_client()
    if client:
        doc = client.collection("style_profiles").document(user_id).get()
        if doc.exists:
            return doc.to_dict()
    return _MEMORY_DB["style_profiles"].get(user_id)


def save_style_profile_record(user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    profile_data["user_id"] = user_id
    profile_data["updated_at"] = datetime.now().isoformat()
    
    client = get_firestore_client()
    if client:
        client.collection("style_profiles").document(user_id).set(profile_data, merge=True)
    
    existing = _MEMORY_DB["style_profiles"].get(user_id, {})
    existing.update(profile_data)
    _MEMORY_DB["style_profiles"][user_id] = existing
    return existing


def list_wardrobe_records(user_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    client = get_firestore_client()
    if client:
        query = client.collection("wardrobe_items").where("userId", "==", user_id)
        if category:
            query = query.where("category", "==", category.lower())
        return [doc.to_dict() for doc in query.stream()]
        
    items = [
        item for item in _MEMORY_DB["wardrobe_items"].values()
        if item.get("userId") == user_id
    ]
    if category:
        items = [i for i in items if i.get("category", "").lower() == category.lower()]
    return items


def add_wardrobe_record(user_id: str, item_dict: Dict[str, Any]) -> Dict[str, Any]:
    item_id = item_dict.get("id") or f"w_{len(_MEMORY_DB['wardrobe_items']) + 1}_{int(datetime.now().timestamp())}"
    item_dict["id"] = item_id
    item_dict["userId"] = user_id
    item_dict["created_at"] = datetime.now().isoformat()
    
    client = get_firestore_client()
    if client:
        client.collection("wardrobe_items").document(item_id).set(item_dict)

    _MEMORY_DB["wardrobe_items"][item_id] = item_dict
    return item_dict


def delete_wardrobe_record(user_id: str, item_id: str) -> bool:
    client = get_firestore_client()
    if client:
        doc_ref = client.collection("wardrobe_items").document(item_id)
        doc = doc_ref.get()
        if doc.exists and doc.to_dict().get("userId") == user_id:
            doc_ref.delete()
            return True

    if item_id in _MEMORY_DB["wardrobe_items"]:
        if _MEMORY_DB["wardrobe_items"][item_id].get("userId") == user_id:
            del _MEMORY_DB["wardrobe_items"][item_id]
            return True
    return False


def save_outfit_record(user_id: str, outfit_dict: Dict[str, Any]) -> Dict[str, Any]:
    outfit_id = outfit_dict.get("id") or f"outfit_{len(_MEMORY_DB['outfits']) + 1}_{int(datetime.now().timestamp())}"
    outfit_dict["id"] = outfit_id
    outfit_dict["userId"] = user_id
    outfit_dict["created_at"] = datetime.now().isoformat()
    
    client = get_firestore_client()
    if client:
        client.collection("outfits").document(outfit_id).set(outfit_dict)

    _MEMORY_DB["outfits"][outfit_id] = outfit_dict
    return outfit_dict


def list_outfit_records(user_id: str) -> List[Dict[str, Any]]:
    client = get_firestore_client()
    if client:
        return [
            doc.to_dict()
            for doc in client.collection("outfits").where("userId", "==", user_id).stream()
        ]
    return [
        o for o in _MEMORY_DB["outfits"].values()
        if o.get("userId") == user_id
    ]

def update_wardrobe_record(user_id: str, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    client = get_firestore_client()
    if client:
        doc_ref = client.collection("wardrobe_items").document(item_id)
        doc = doc_ref.get()
        if doc.exists and doc.to_dict().get("userId") == user_id:
            updates["updated_at"] = datetime.now().isoformat()
            doc_ref.update(updates)
            updated_data = doc_ref.get().to_dict()
            _MEMORY_DB["wardrobe_items"][item_id] = updated_data
            return updated_data

    if item_id in _MEMORY_DB["wardrobe_items"]:
        item = _MEMORY_DB["wardrobe_items"][item_id]
        if item.get("userId") == user_id:
            item.update(updates)
            item["updated_at"] = datetime.now().isoformat()
            return item
    return None

_ACTIVE_OUTFIT_CONTEXT = {}

def set_active_outfit_context(user_id: str, outfit_data: Dict[str, Any]) -> None:
    _ACTIVE_OUTFIT_CONTEXT[user_id] = outfit_data

def get_active_outfit_context(user_id: str) -> Optional[Dict[str, Any]]:
    return _ACTIVE_OUTFIT_CONTEXT.get(user_id)
