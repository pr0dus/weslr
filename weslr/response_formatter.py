"""WESLR response formatter — standardizes deterministic response skeletons."""

from typing import Optional


def build_deterministic_response(
    message: str,
    path: str,
    response_text: str,
    payload: Optional[dict] = None,
    confidence: str = "high",
    suggested_mode: Optional[str] = None,
) -> dict:
    """
    Build a canonical deterministic response skeleton.

    Args:
        message: raw operator input
        path: deterministic handler path (e.g. "ISS_probe_registry_query")
        response_text: human-readable primary output
        payload: optional structured payload (probe_registry, probe_plan, etc.)
        confidence: handler match confidence level
        suggested_mode: optional mode advisory

    Returns:
        dict with all canonical fields plus payload if provided.

    All deterministic responses use this skeleton.
    Payload fields are merged on top — no payload fields are overwritten.
    """
    result = {
        "message": message,
        "response_text": response_text,
        "path": path,
        "_weslr_deterministic": True,
        "confidence": confidence,
    }
    if suggested_mode is not None:
        result["suggested_mode"] = suggested_mode
    if payload:
        result.update(payload)
    return result