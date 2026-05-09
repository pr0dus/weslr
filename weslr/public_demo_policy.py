"""Public demo backend policy helpers.

These helpers mirror the frontend `public_demo_readonly` contract from
`docs/WESLR_PRODUCT_MODE_MATRIX_V1.md`.

Frontend flags are UX only. Backend routes must still enforce the public-demo
boundary before exposing file upload, operator review, deployment controls, or
other state-changing capabilities.
"""

from __future__ import annotations

import os
from typing import Any, Dict

PUBLIC_DEMO_MODE = "public_demo_readonly"

BLOCKED_PUBLIC_DEMO_FEATURES = {
    "file_upload",
    "file_route",
    "operator_panel",
    "operator_summary",
    "operator_review",
    "deployment_controls",
    "memory_writes",
    "api_key_workflows",
}


def get_product_mode() -> str:
    """Return the active product mode.

    Defaults to public_demo_readonly for the standalone test deployment because
    public exposure should fail closed unless an operator explicitly configures
    a more capable mode.
    """

    return os.environ.get("WESLR_PRODUCT_MODE", PUBLIC_DEMO_MODE).strip() or PUBLIC_DEMO_MODE


def is_public_demo_mode(mode: str | None = None) -> bool:
    return (mode or get_product_mode()) == PUBLIC_DEMO_MODE


def is_feature_allowed(feature: str, mode: str | None = None) -> bool:
    """Return whether a backend feature is allowed in the given product mode."""

    active_mode = mode or get_product_mode()
    if active_mode == PUBLIC_DEMO_MODE and feature in BLOCKED_PUBLIC_DEMO_FEATURES:
        return False
    return True


def public_demo_block_response(feature: str) -> Dict[str, Any]:
    """Return a safe, user-facing block response for disabled public features."""

    return {
        "success": False,
        "blocked": True,
        "feature": feature,
        "mode": PUBLIC_DEMO_MODE,
        "error": "This action is not available in the read-only public demo.",
        "reason": "public_demo_readonly disables file upload, memory writes, operator controls, deployment controls, and API-key workflows.",
    }


def operator_visibility_response() -> Dict[str, Any]:
    """Return the operator visibility gate for the active product mode."""

    if not is_feature_allowed("operator_panel"):
        return {
            "visible": False,
            "reason": "Public demo mode — operator panel disabled",
            "can_review": False,
        }

    return {
        "visible": True,
        "reason": "Operator panel enabled by configured product mode",
        "can_review": True,
    }
