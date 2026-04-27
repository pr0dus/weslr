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


def build_write_response(
    message: str,
    path: str,
    action_performed: str,
    affected_ids: list[str],
    response_text: str,
    confidence: str = "high",
    suggested_mode: Optional[str] = None,
    write_confirmed: bool = True,
    extra: Optional[dict] = None,
) -> dict:
    """
    Build a write-action response.

    Wraps build_deterministic_response and adds write-specific fields.
    Use for record-creating or record-updating operations.
    Do NOT use for read-only queries.

    Args:
        message: raw operator input
        path: handler path (e.g. "ISS_controlled_proposal_intake")
        action_performed: human-readable action tag (e.g. "proposal_created")
        affected_ids: list of record IDs affected (e.g. ["iss.not_integrated"])
        response_text: human-readable outcome description
        confidence: handler match confidence level
        suggested_mode: optional mode advisory
        write_confirmed: True if write was committed, False if rejected/failed
        extra: optional additional fields merged into result

    Returns:
        dict with deterministic skeleton + action_performed, affected_ids, write_confirmed
    """
    result = build_deterministic_response(
        message=message,
        path=path,
        response_text=response_text,
        confidence=confidence,
        suggested_mode=suggested_mode,
    )
    result["action_performed"] = action_performed
    result["affected_ids"] = affected_ids
    result["write_confirmed"] = write_confirmed
    if extra:
        result.update(extra)
    return result