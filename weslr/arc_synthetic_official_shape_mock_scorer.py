"""Synthetic ARC official-shape mock scorer V1.

Exact-match-only scoring for hidden references against ARC-AGI-2-style top-2
attempt packets. No official/public ARC data is touched.
"""

from __future__ import annotations

from collections import defaultdict
import json
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_submission_contract import validate_arc_agi2_top2_attempt_packet_v1

SCHEMA_VERSION_V1 = "ArcSyntheticOfficialShapeMockScorerV1"


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


def _candidate_role(attempt: Mapping[str, Any]) -> str:
    metadata = attempt.get("metadata", {}) if isinstance(attempt.get("metadata"), Mapping) else {}
    role = metadata.get("candidate_role") if isinstance(metadata, Mapping) else None
    if isinstance(role, str) and role:
        return role
    source = str(attempt.get("source_candidate_id", ""))
    if "baseline" in source:
        return "baseline"
    if "solver" in source:
        return "solver"
    return "unknown"


def score_arc_synthetic_official_shape_mock_top2_packet_v1(
    *,
    top2_packet: Mapping[str, Any],
    reference_output: Sequence[Any],
) -> dict[str, Any]:
    validation = validate_arc_agi2_top2_attempt_packet_v1(top2_packet)
    reference_safe = _safe(reference_output)
    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": False,
        "task_score": 0,
        "solver_exact": False,
        "baseline_exact": False,
        "malformed_count": 0,
        "timeout_count": 0,
        "error_count": 0,
        "blocked_reason_labels": [],
        "attempt_roles": [],
        "reference_shape": None,
    }
    if not validation["valid"]:
        result["blocked_reason_labels"] = list(validation["blocked_reason_labels"])
        result["malformed_count"] = 1
        result["error_count"] = 1
        result["reference_shape"] = {
            "height": len(reference_safe) if isinstance(reference_safe, list) else 0,
            "width": len(reference_safe[0]) if isinstance(reference_safe, list) and reference_safe else 0,
        }
        return result

    attempts = top2_packet.get("attempts", []) if isinstance(top2_packet.get("attempts"), list) else []
    if len(attempts) != 2:
        result["malformed_count"] = 1
        result["error_count"] = 1
        result["blocked_reason_labels"] = ["attempt_count_must_be_two"]
        return result

    matches = [attempt.get("grid") == reference_safe for attempt in attempts]
    roles = [_candidate_role(attempt) for attempt in attempts]
    result["attempt_roles"] = roles
    role_to_match = {role: bool(match) for role, match in zip(roles, matches)}
    result["solver_exact"] = role_to_match.get("solver", matches[0])
    result["baseline_exact"] = role_to_match.get("baseline", matches[1])
    result["task_score"] = 1 if any(matches) else 0
    result["valid"] = True
    result["reference_shape"] = {
        "height": len(reference_safe) if isinstance(reference_safe, list) else 0,
        "width": len(reference_safe[0]) if isinstance(reference_safe, list) and reference_safe else 0,
    }
    json.dumps(_safe(result), ensure_ascii=False, allow_nan=False)
    return result


def summarize_arc_synthetic_official_shape_mock_scores_v1(scores: Any) -> dict[str, Any]:
    if not isinstance(scores, list):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "task_count": 0,
            "task_score": 0,
            "solver_exact_count": 0,
            "baseline_exact_count": 0,
            "malformed_count": 0,
            "timeout_count": 0,
            "error_count": 0,
            "family_scores": {},
            "blocked_reason_labels": ["scores_not_list"],
        }
    family_scores: dict[str, dict[str, int]] = defaultdict(lambda: {"task_score": 0, "count": 0, "solver_exact": 0, "baseline_exact": 0})
    task_score = solver_exact_count = baseline_exact_count = malformed_count = timeout_count = error_count = 0
    for item in scores:
        if not isinstance(item, Mapping):
            malformed_count += 1
            error_count += 1
            continue
        family_id = str(item.get("family_id", "unknown"))
        family_scores[family_id]["count"] += 1
        family_scores[family_id]["task_score"] += int(item.get("task_score", 0))
        family_scores[family_id]["solver_exact"] += int(bool(item.get("solver_exact", False)))
        family_scores[family_id]["baseline_exact"] += int(bool(item.get("baseline_exact", False)))
        task_score += int(item.get("task_score", 0))
        solver_exact_count += int(bool(item.get("solver_exact", False)))
        baseline_exact_count += int(bool(item.get("baseline_exact", False)))
        malformed_count += int(item.get("malformed_count", 0))
        timeout_count += int(item.get("timeout_count", 0))
        error_count += int(item.get("error_count", 0))
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": malformed_count == 0 and error_count == 0,
        "task_count": len(scores),
        "task_score": task_score,
        "solver_exact_count": solver_exact_count,
        "baseline_exact_count": baseline_exact_count,
        "malformed_count": malformed_count,
        "timeout_count": timeout_count,
        "error_count": error_count,
        "family_scores": {family_id: dict(value) for family_id, value in sorted(family_scores.items())},
        "blocked_reason_labels": [] if malformed_count == 0 and error_count == 0 else ["malformed_or_error_present"],
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "score_arc_synthetic_official_shape_mock_top2_packet_v1",
    "summarize_arc_synthetic_official_shape_mock_scores_v1",
]
