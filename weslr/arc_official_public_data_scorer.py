"""ARC official-public scorer shape using exact equality only."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_submission_contract import validate_arc_agi2_top2_attempt_packet_v1

SCHEMA_VERSION_V1 = "arc_official_public_data_scorer_v1"


def _safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_safe(item) for item in value]
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, set):
        return [_safe(item) for item in sorted(value, key=repr)]
    return str(value)


def score_arc_official_public_top2_packet_v1(*, top2_packet: Mapping[str, Any], reference_output: Sequence[Any]) -> dict[str, Any]:
    reference_safe = deepcopy(reference_output)
    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": False,
        "task_score": 0,
        "solver_exact": False,
        "baseline_exact": False,
        "malformed_count": 0,
        "error_count": 0,
        "blocked_reason_labels": [],
        "reference_shape": None,
        "metadata_only": True,
    }
    try:
        validation = validate_arc_agi2_top2_attempt_packet_v1(top2_packet)
    except Exception as exc:
        result["malformed_count"] = 1
        result["error_count"] = 1
        result["blocked_reason_labels"] = ["validation_exception"]
        result["reference_shape"] = {
            "height": len(reference_safe) if isinstance(reference_safe, list) else 0,
            "width": len(reference_safe[0]) if isinstance(reference_safe, list) and reference_safe else 0,
        }
        result["validation_error"] = "[redacted]"
        return result

    if not validation["valid"]:
        result["malformed_count"] = 1
        result["error_count"] = 1
        result["blocked_reason_labels"] = list(validation.get("blocked_reason_labels", []))
        result["reference_shape"] = {
            "height": len(reference_safe) if isinstance(reference_safe, list) else 0,
            "width": len(reference_safe[0]) if isinstance(reference_safe, list) and reference_safe else 0,
        }
        return result

    attempts = top2_packet.get("attempts", []) if isinstance(top2_packet.get("attempts"), list) else []
    matches = [attempt.get("grid") == reference_safe for attempt in attempts]
    result["solver_exact"] = bool(matches[0])
    result["baseline_exact"] = bool(matches[1])
    result["task_score"] = 1 if any(matches) else 0
    result["valid"] = True
    result["reference_shape"] = {
        "height": len(reference_safe) if isinstance(reference_safe, list) else 0,
        "width": len(reference_safe[0]) if isinstance(reference_safe, list) and reference_safe else 0,
    }
    json.dumps(_safe(result), ensure_ascii=False, allow_nan=False)
    return result


__all__ = [
    "SCHEMA_VERSION_V1",
    "score_arc_official_public_top2_packet_v1",
]
