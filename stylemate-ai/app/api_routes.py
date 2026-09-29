"""
Custom API boundary routes for StyleMate AI.
Allows the frontend to upload photos, inspect wardrobe, view profiles, and manage saved outfits.
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional, List
import shutil
import os
import json
from datetime import datetime

from app.tools import (
    analyze_style_profile,
    update_style_profile,
    get_style_profile,
    get_wardrobe,
    add_wardrobe_item,
    update_wardrobe_item,
    remove_wardrobe_item,
    analyze_clothing,
    generate_outfit,
    save_outfit
)
from app.storage import upload_user_photo
from app.db import list_outfit_records

router = APIRouter(prefix="/api/stylemate", tags=["StyleMate"])


@router.get("/profile")
def api_get_profile(user_id: str = "default_user"):
    res = json.loads(get_style_profile(user_id=user_id))
    return res


@router.post("/profile/upload")
async def api_upload_profile_photo(
    file: UploadFile = File(...),
    user_id: str = Form("default_user")
):
    try:
        content = await file.read()
        filename = f"{int(datetime.now().timestamp())}_{file.filename}"
        
        gcs_uri = upload_user_photo(file_bytes=content, filename=filename, user_id=user_id, folder="profiles")
        analysis_res = json.loads(analyze_style_profile(image_storage_uri_or_hint=gcs_uri, user_id=user_id))
        
        return {
            "status": "success",
            "storage_uri": gcs_uri,
            "analysis": analysis_res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile")
def api_update_profile(payload: dict):
    user_id = payload.get("user_id", "default_user")
    res = json.loads(update_style_profile(
        user_id=user_id,
        undertone=payload.get("undertone"),
        face_shape=payload.get("face_shape"),
        suitable_color_families=payload.get("suitable_color_families"),
        avoid_colors=payload.get("avoid_colors"),
        inferred_style_vibes=payload.get("inferred_style_vibes")
    ))
    return res


@router.get("/wardrobe")
def api_get_wardrobe(
    user_id: str = "default_user",
    category: Optional[str] = None,
    favorite_only: bool = False
):
    res = json.loads(get_wardrobe(user_id=user_id, category=category, favorite_only=favorite_only))
    return res


@router.post("/wardrobe/upload")
async def api_upload_clothing_photo(
    file: UploadFile = File(...),
    user_id: str = Form("default_user")
):
    try:
        content = await file.read()
        filename = f"clothing_{int(datetime.now().timestamp())}_{file.filename}"
        gcs_uri = upload_user_photo(file_bytes=content, filename=filename, user_id=user_id, folder="wardrobe")

        # Multimodal classification via analyze_clothing
        analyzed_raw = json.loads(analyze_clothing(image_storage_uri_or_hint=filename))
        item_data = analyzed_raw.get("analysis", {})

        added = json.loads(add_wardrobe_item(
            category=item_data.get("category", "topwear"),
            subcategory=item_data.get("subcategory", "clothing item"),
            color=item_data.get("color", "neutral"),
            secondary_colors=item_data.get("secondary_colors", []),
            pattern=item_data.get("pattern", "solid"),
            material=item_data.get("material"),
            style=item_data.get("style", "casual"),
            season=item_data.get("season", ["all-season"]),
            occasions=item_data.get("occasions", []),
            tags=item_data.get("tags", []),
            user_id=user_id,
            image_storage_uri=gcs_uri,
            is_favorite=False
        ))

        return {
            "status": "success",
            "storage_uri": gcs_uri,
            "analysis": item_data,
            "wardrobe_item": added.get("item")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/wardrobe/items/{item_id}")
def api_update_wardrobe_item(item_id: str, payload: dict):
    user_id = payload.get("user_id", "default_user")
    res = json.loads(update_wardrobe_item(
        item_id=item_id,
        user_id=user_id,
        category=payload.get("category"),
        subcategory=payload.get("subcategory"),
        color=payload.get("color"),
        style=payload.get("style"),
        is_favorite=payload.get("is_favorite"),
        tags=payload.get("tags")
    ))
    return res


@router.delete("/wardrobe/items/{item_id}")
def api_delete_wardrobe_item(item_id: str, user_id: str = "default_user"):
    res = json.loads(remove_wardrobe_item(item_id=item_id, user_id=user_id))
    return res


@router.post("/outfits/generate")
def api_generate_outfit(payload: dict):
    occasion = payload.get("occasion", "casual")
    user_id = payload.get("user_id", "default_user")
    excluded_colors = payload.get("excluded_colors")
    preferred_style = payload.get("preferred_style")
    res = json.loads(generate_outfit(
        occasion=occasion,
        user_id=user_id,
        excluded_colors=excluded_colors,
        preferred_style=preferred_style
    ))
    return res


@router.get("/outfits/saved")
def api_get_saved_outfits(user_id: str = "default_user"):
    return {
        "status": "success",
        "outfits": list_outfit_records(user_id)
    }

@router.get("/shopping/search")
def api_search_products(
    query: str,
    user_id: str = "default_user",
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    color: Optional[str] = None,
    pairing_with_wardrobe_item_id: Optional[str] = None
):
    from app.tools import search_products
    res = json.loads(search_products(
        query=query,
        user_id=user_id,
        category=category,
        max_price=max_price,
        color=color,
        pairing_with_wardrobe_item_id=pairing_with_wardrobe_item_id
    ))
    return res

@router.post("/outfits/visualize")
def api_visualize_outfit(payload: dict):
    from app.tools import visualize_outfit
    outfit_id = payload.get("outfit_id")
    items_summary = payload.get("items_summary")
    user_id = payload.get("user_id", "default_user")
    force_failure = payload.get("force_failure", False)
    
    res = json.loads(visualize_outfit(
        outfit_id=outfit_id,
        items_summary=items_summary,
        user_id=user_id,
        force_failure=force_failure
    ))
    return res
