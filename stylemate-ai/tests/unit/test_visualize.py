import pytest
import json
import os
from app.tools import visualize_outfit, generate_outfit
from app.schemas import VisualizationResult

def test_visualize_outfit_success():
    # 1. Generate an outfit first
    generate_outfit(occasion="dinner date", user_id="default_user")

    # 2. Call visualize_outfit
    raw = visualize_outfit(user_id="default_user")
    res = json.loads(raw)
    assert res["status"] == "success"
    viz = res["visualization"]
    
    # Verify strict schema conformance
    model = VisualizationResult(**viz)
    assert model.status == "success"
    assert "AI-Generated" in model.ai_generated_label
    assert "Does not represent precise physical fit" in model.disclaimer
    assert model.image_url is not None
    assert "Editorial" in model.prompt_used or "lookbook" in model.prompt_used.lower()

def test_visualize_graceful_failure_handling():
    # Simulates image generation failure
    raw = visualize_outfit(user_id="default_user", force_failure=True)
    res = json.loads(raw)
    assert res["status"] == "failed"
    viz = res["visualization"]
    assert viz["status"] == "failed"
    assert "temporarily unavailable" in viz["error_message"]
    # Crucially: Core functionality is unaffected
    outfit_res = json.loads(generate_outfit(occasion="casual weekend", user_id="default_user"))
    assert outfit_res["status"] == "success"

def test_visualize_feature_flag_disable(monkeypatch):
    # Disable feature flag via env
    import app.visualization_service as vs
    monkeypatch.setattr(vs, "ENABLE_VIRTUAL_TRYON", False)

    raw = visualize_outfit(user_id="default_user")
    res = json.loads(raw)
    assert res["status"] == "disabled"
    assert res["visualization"]["status"] == "disabled"
    assert "disabled by administrator" in res["visualization"]["error_message"]
