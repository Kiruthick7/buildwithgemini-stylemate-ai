import pytest
import json
from app.tools import (
    analyze_style_profile,
    update_style_profile,
    get_style_profile
)
from app.schemas import PersonalStyleProfile

def test_valid_image_profile():
    # Simulate a valid solo portrait
    result_raw = analyze_style_profile(
        image_storage_uri_or_hint="gs://bucket/profiles/user_1/selfie_daylight.jpg",
        user_id="test_user_valid"
    )
    result = json.loads(result_raw)
    assert result["status"] == "success"
    profile = result["profile"]
    
    # Verify schema conformance
    pydantic_obj = PersonalStyleProfile(**profile)
    assert pydantic_obj.is_valid_fashion_portrait is True
    assert pydantic_obj.approximate_face_shape == "oval"
    assert pydantic_obj.skin_tone_undertone.undertone == "neutral-warm"
    assert pydantic_obj.skin_tone_undertone.confidence in ["moderate", "high"]
    assert "navy blue" in pydantic_obj.suitable_color_families
    assert len(pydantic_obj.avoid_colors) > 0
    assert "visual estimation" in pydantic_obj.skin_tone_undertone.disclaimer.lower()

def test_unclear_image():
    # Simulate low-lighting / blurry portrait
    result_raw = analyze_style_profile(
        image_storage_uri_or_hint="unclear_dark_blurry_photo.jpg",
        user_id="test_user_unclear"
    )
    result = json.loads(result_raw)
    profile = result["profile"]
    pydantic_obj = PersonalStyleProfile(**profile)
    
    # Must explicitly express uncertainty
    assert "low_lighting_or_unclear" in pydantic_obj.detection_issues
    assert pydantic_obj.skin_tone_undertone.confidence == "low"
    assert pydantic_obj.skin_tone_undertone.undertone == "uncertain"
    assert "daylight" in pydantic_obj.outfit_style_suggestions[0].lower()

def test_multiple_people_in_image():
    # Simulate photo with multiple people / group
    result_raw = analyze_style_profile(
        image_storage_uri_or_hint="group_photo_multiple_friends.jpg",
        user_id="test_user_group"
    )
    result = json.loads(result_raw)
    profile = result["profile"]
    pydantic_obj = PersonalStyleProfile(**profile)
    
    # Must refuse solo profiling and flag issue
    assert pydantic_obj.is_valid_fashion_portrait is False
    assert "multiple_people_detected" in pydantic_obj.detection_issues
    assert pydantic_obj.skin_tone_undertone.confidence == "unreliable"

def test_unsupported_image():
    # Simulate landscape / pet / scenery photo
    result_raw = analyze_style_profile(
        image_storage_uri_or_hint="scenery_landscape_cat.jpg",
        user_id="test_user_unsupported"
    )
    result = json.loads(result_raw)
    profile = result["profile"]
    pydantic_obj = PersonalStyleProfile(**profile)
    
    # Flag unsupported content
    assert pydantic_obj.is_valid_fashion_portrait is False
    assert "unsupported_content" in pydantic_obj.detection_issues
    assert pydantic_obj.skin_tone_undertone.undertone == "uncertain"

def test_user_correcting_ai_result():
    # Initial analysis
    analyze_style_profile(
        image_storage_uri_or_hint="gs://bucket/profiles/user_correct/selfie.jpg",
        user_id="test_user_correct"
    )

    # User corrects undertone and adds favorite color
    update_raw = update_style_profile(
        user_id="test_user_correct",
        undertone="cool",
        face_shape="square",
        suitable_color_families=["emerald green", "cobalt blue", "crisp white"],
        avoid_colors=["mustard yellow", "warm orange"]
    )
    update_res = json.loads(update_raw)
    assert update_res["status"] == "success"
    profile = update_res["profile"]
    
    # Confirm user corrections override AI estimates
    assert profile["skin_tone_undertone"]["undertone"] == "cool"
    assert profile["skin_tone_undertone"]["confidence"] == "high"
    assert profile["approximate_face_shape"] == "square"
    assert "emerald green" in profile["suitable_color_families"]
    assert profile["user_reviewed"] is True

    # Check agent can retrieve the corrected profile
    agent_retrieved = json.loads(get_style_profile(user_id="test_user_correct"))
    assert agent_retrieved["profile"]["skin_tone_undertone"]["undertone"] == "cool"
