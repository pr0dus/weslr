from __future__ import annotations

from weslr.public_demo_policy import (
    PUBLIC_DEMO_MODE,
    get_product_mode,
    is_feature_allowed,
    is_public_demo_mode,
    operator_visibility_response,
    public_demo_block_response,
)


def test_default_product_mode_is_public_demo(monkeypatch):
    monkeypatch.delenv("WESLR_PRODUCT_MODE", raising=False)
    assert get_product_mode() == PUBLIC_DEMO_MODE
    assert is_public_demo_mode()


def test_public_demo_blocks_stateful_and_operator_features():
    blocked = [
        "file_upload",
        "file_route",
        "operator_panel",
        "operator_summary",
        "operator_review",
        "deployment_controls",
        "memory_writes",
        "api_key_workflows",
    ]
    for feature in blocked:
        assert is_feature_allowed(feature, PUBLIC_DEMO_MODE) is False


def test_public_demo_allows_unlisted_read_only_features():
    assert is_feature_allowed("continuity_status", PUBLIC_DEMO_MODE) is True
    assert is_feature_allowed("conversation_list", PUBLIC_DEMO_MODE) is True


def test_non_public_mode_allows_features_when_explicitly_configured():
    assert is_feature_allowed("file_upload", "operator_dev") is True
    assert is_feature_allowed("operator_panel", "operator_dev") is True


def test_operator_visibility_is_hidden_in_default_public_demo(monkeypatch):
    monkeypatch.delenv("WESLR_PRODUCT_MODE", raising=False)
    response = operator_visibility_response()
    assert response["visible"] is False
    assert response["can_review"] is False
    assert "Public demo" in response["reason"]


def test_public_demo_block_response_is_safe_and_structured():
    response = public_demo_block_response("file_upload")
    assert response["success"] is False
    assert response["blocked"] is True
    assert response["feature"] == "file_upload"
    assert response["mode"] == PUBLIC_DEMO_MODE
    assert "read-only public demo" in response["error"]
