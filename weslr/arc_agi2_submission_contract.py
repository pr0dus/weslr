"""WESLR ARC-AGI-2 submission contract helpers V1.

Synthetic-only schema/helper layer for ARC-AGI-2-style top-2 attempts and
submission structures.

This module does not implement public ARC ingestion, Kaggle notebook wiring,
solver runtime, provider calls, payment calls, ChatResponder wiring, website
runtime wiring, or `.weslr` writes.
"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Mapping, Sequence

from weslr.arc_style_grid_schema_helpers import (
    TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
    build_arc_style_grid_metadata_v1,
)

SCHEMA_VERSION_V1 = "ArcAgi2SubmissionContractV1"
CONTRACT_NAME_V1 = "arc_agi2_submission_contract_v1"
CONTRACT_VERSION_V1 = "v1"

LEAKAGE_FLAG_NAMES_V1 = (
    "uses_test_output",
    "uses_solution_file",
    "uses_answer_key",
    "uses_hidden_private_data",
    "uses_task_id_shortcut",
    "uses_notes_shortcut",
    "lookup_table_detected",
)

REQUIRED_ATTEMPT_FIELDS_V1 = (
    "attempt_id",
    "grid",
    "source_candidate_id",
    "rank",
    "confidence_label",
    "evidence_labels",
    "leakage_flags",
    "metadata",
)

REQUIRED_TOP2_PACKET_FIELDS_V1 = (
    "task_id",
    "test_input_index",
    "attempts",
    "duplicate_attempt_grid",
    "leakage_flags",
    "metadata",
)

REQUIRED_SUBMISSION_TASK_ENTRY_FIELDS_V1 = (
    "task_id",
    "test_input_packets",
    "leakage_flags",
    "metadata",
)

REQUIRED_SUBMISSION_PACKET_FIELDS_V1 = (
    "contract_name",
    "contract_version",
    "synthetic_only",
    "kaggle_ready",
    "requires_official_sample_submission_validation",
    "denied_authority",
    "task_entries",
    "leakage_flags",
    "metadata",
)

DEFAULT_DENIED_AUTHORITY_V1 = (
    "kaggle_ready_claim",
    "competition_submission_authority",
    "answer_key_authority",
)

CONFIDENCE_LABEL_SCORES_V1 = {
    "unknown": 0,
    "low": 10,
    "medium": 20,
    "high": 30,
    "confirmed": 40,
}

VALIDATION_STATUS_SCORES_V1 = {
    "exact_match": 40,
    "fit": 30,
    "partial_fit": 10,
    "unknown": 0,
    "mismatch": -20,
    "unsupported": -30,
    "invalid": -100,
}


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return default if value == "" else str(value)


def _json_safe(value: Any) -> Any:
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    return _safe_text(value)


def to_arc_agi2_submission_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def serialize_arc_agi2_submission_json_safe_v1(value: Any) -> Any:
    safe = to_arc_agi2_submission_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _grid_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        if "cell_values" in value:
            return value.get("cell_values")
        if "grid" in value:
            return value.get("grid")
        if "attempt_grid" in value:
            return value.get("attempt_grid")
        if "output_grid" in value:
            return value.get("output_grid")
        if "predicted_grid" in value:
            return value.get("predicted_grid")
    return value


def _validate_grid_like(value: Any) -> dict[str, Any]:
    payload = _grid_payload(value)
    result = {"valid": False, "reasons": [], "grid_metadata": None}
    if not isinstance(payload, list):
        result["reasons"].append("grid_not_list")
        return result
    if len(payload) == 0:
        result["reasons"].append("empty_grid")
        return result
    for row in payload:
        if not isinstance(row, list):
            result["reasons"].append("row_not_list")
            break
        if len(row) == 0:
            result["reasons"].append("empty_row")
            break

    metadata = build_arc_style_grid_metadata_v1(payload)
    result["grid_metadata"] = metadata
    if metadata["width"] <= 0 or metadata["height"] <= 0:
        result["reasons"].append("empty_grid")
    if metadata["trace"]["rectangular"] is False:
        result["reasons"].append("grid_not_rectangular")
    if metadata["trace"].get("oversized"):
        result["reasons"].append("grid_oversized")
    if metadata["invalid_cells"]:
        result["reasons"].append("invalid_cells_present")
    if any(cell.get("reason") == "invalid_cell_value" for cell in metadata["invalid_cells"]):
        result["reasons"].append("invalid_cell_value")
    if len(metadata["trace"].get("cell_type_names", [])) > 1:
        result["reasons"].append("mixed_cell_types_rejected")
    result["valid"] = not result["reasons"]
    return result


def _normalize_leakage_flags(value: Any) -> dict[str, bool]:
    mapping = value if isinstance(value, Mapping) else {}
    return {name: bool(mapping.get(name, False)) for name in LEAKAGE_FLAG_NAMES_V1}


def _leakage_flags_are_clean(flags: Mapping[str, Any]) -> bool:
    return all(not bool(flags.get(name, False)) for name in LEAKAGE_FLAG_NAMES_V1)


def _validate_leakage_flags(value: Any) -> dict[str, Any]:
    flags = _normalize_leakage_flags(value)
    invalid = [name for name in LEAKAGE_FLAG_NAMES_V1 if bool(flags.get(name, False))]
    return {"valid": not invalid, "flags": flags, "blocked_reason_labels": invalid}


def _confidence_score(label: str) -> int:
    return CONFIDENCE_LABEL_SCORES_V1.get(_safe_text(label, "unknown").lower(), 0)


def _validation_status_score(value: Any) -> int:
    return VALIDATION_STATUS_SCORES_V1.get(_safe_text(value, "unknown").lower(), 0)


def _candidate_grid(candidate: Mapping[str, Any]) -> Any:
    for key in ("grid", "attempt_grid", "predicted_grid", "output_grid", "cell_values"):
        if key in candidate:
            return candidate.get(key)
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    for key in ("grid", "attempt_grid", "predicted_grid", "output_grid", "cell_values"):
        if key in metadata:
            return metadata.get(key)
    return []


def _candidate_id(candidate: Mapping[str, Any], fallback_index: int = 0) -> str:
    for key in ("source_candidate_id", "candidate_id", "attempt_id"):
        candidate_id = _safe_text(candidate.get(key))
        if candidate_id:
            return candidate_id
    return f"candidate_{fallback_index}"


def _candidate_metadata(candidate: Mapping[str, Any]) -> dict[str, Any]:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    trace = candidate.get("trace") if isinstance(candidate.get("trace"), Mapping) else {}
    merged = _json_safe(metadata)
    if isinstance(trace, Mapping):
        for key, value in trace.items():
            merged.setdefault(str(key), _json_safe(value))
    for key in ("validation_status", "train_fit_status", "synthetic_only"):
        if key in candidate and key not in merged:
            merged[key] = _json_safe(candidate.get(key))
    return merged


def _candidate_evidence_labels(candidate: Mapping[str, Any]) -> list[str]:
    labels = candidate.get("evidence_labels")
    if isinstance(labels, list):
        return [_safe_text(label) for label in labels if _safe_text(label)]
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    labels = metadata.get("evidence_labels")
    if isinstance(labels, list):
        return [_safe_text(label) for label in labels if _safe_text(label)]
    trace = candidate.get("trace") if isinstance(candidate.get("trace"), Mapping) else {}
    labels = trace.get("structural_evidence_labels")
    if isinstance(labels, list):
        return [_safe_text(label) for label in labels if _safe_text(label)]
    return []


def _candidate_confidence_label(candidate: Mapping[str, Any]) -> str:
    for key in ("confidence_label", "candidate_confidence"):
        value = _safe_text(candidate.get(key))
        if value:
            return value
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    for key in ("confidence_label", "candidate_confidence"):
        value = _safe_text(metadata.get(key))
        if value:
            return value
    return "unknown"


def _candidate_leakage_flags(candidate: Mapping[str, Any]) -> dict[str, bool]:
    flags = candidate.get("leakage_flags")
    if isinstance(flags, Mapping):
        return _normalize_leakage_flags(flags)
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    flags = metadata.get("leakage_flags")
    if isinstance(flags, Mapping):
        return _normalize_leakage_flags(flags)
    trace = candidate.get("trace") if isinstance(candidate.get("trace"), Mapping) else {}
    flags = trace.get("leakage_flags")
    if isinstance(flags, Mapping):
        return _normalize_leakage_flags(flags)
    return _normalize_leakage_flags({})


def _candidate_validation_status(candidate: Mapping[str, Any], grid_validation: Mapping[str, Any]) -> str:
    for key in ("validation_status", "train_fit_status"):
        value = _safe_text(candidate.get(key))
        if value:
            return value
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    for key in ("validation_status", "train_fit_status"):
        value = _safe_text(metadata.get(key))
        if value:
            return value
    if grid_validation.get("valid"):
        return "unknown"
    return "invalid"


def _candidate_synthetic_only(candidate: Mapping[str, Any]) -> bool:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    trace = candidate.get("trace") if isinstance(candidate.get("trace"), Mapping) else {}
    for container in (candidate, metadata, trace):
        if isinstance(container, Mapping) and bool(container.get("synthetic_only", False)):
            return True
        if isinstance(container, Mapping) and bool(container.get("internal_synthetic_only", False)):
            return True
    return False


def _candidate_score(candidate: Mapping[str, Any]) -> tuple[int, str, str]:
    leakage_flags = _candidate_leakage_flags(candidate)
    if any(leakage_flags.values()):
        return (-100000, _candidate_id(candidate), json.dumps(_json_safe(candidate), sort_keys=True, ensure_ascii=False))

    grid = _candidate_grid(candidate)
    grid_validation = _validate_grid_like(grid)
    validation_status = _candidate_validation_status(candidate, grid_validation)
    confidence_label = _candidate_confidence_label(candidate)
    evidence_labels = _candidate_evidence_labels(candidate)
    metadata = _candidate_metadata(candidate)

    score = 0
    score += _confidence_score(confidence_label)
    score += _validation_status_score(validation_status)
    score += len(evidence_labels) * 3
    score += 5 if _candidate_synthetic_only(candidate) or bool(metadata.get("synthetic_only", False)) else 0
    score += 5 if _leakage_flags_are_clean(leakage_flags) else -100
    if grid_validation.get("valid"):
        score += 5
    else:
        score -= 25
    score_key = json.dumps(_json_safe(grid), sort_keys=True, ensure_ascii=False)
    return (score, _candidate_id(candidate), score_key)


def _attempt_id(task_id: str, test_input_index: int, source_candidate_id: str, rank: int) -> str:
    return f"{_safe_text(task_id)}:{int(test_input_index)}:{_safe_text(source_candidate_id)}:rank{int(rank)}"


def _attempt_grid_signature(grid: Any) -> str:
    return json.dumps(_json_safe(grid), sort_keys=True, ensure_ascii=False)


def _normalize_attempt(
    *,
    task_id: str,
    test_input_index: int,
    candidate: Mapping[str, Any],
    rank: int,
) -> dict[str, Any]:
    grid = _candidate_grid(candidate)
    grid_validation = _validate_grid_like(grid)
    source_candidate_id = _candidate_id(candidate)
    evidence_labels = _candidate_evidence_labels(candidate)
    leakage_flags = _candidate_leakage_flags(candidate)
    metadata = _candidate_metadata(candidate)
    metadata.update(
        {
            "task_id": _safe_text(task_id),
            "test_input_index": int(test_input_index),
            "candidate_score": _candidate_score(candidate)[0],
            "validation_status": _candidate_validation_status(candidate, grid_validation),
            "grid_validation": grid_validation,
            "synthetic_only": _candidate_synthetic_only(candidate),
            "source_kind": _safe_text(candidate.get("source_kind"), "candidate_like"),
        }
    )
    metadata.setdefault("confidence_label", _candidate_confidence_label(candidate))
    metadata.setdefault("evidence_labels", evidence_labels)
    metadata.setdefault("leakage_flags", leakage_flags)
    return build_arc_agi2_attempt_v1(
        attempt_id=_attempt_id(task_id, test_input_index, source_candidate_id, rank),
        grid=grid,
        source_candidate_id=source_candidate_id,
        rank=rank,
        confidence_label=_candidate_confidence_label(candidate),
        evidence_labels=evidence_labels,
        leakage_flags=leakage_flags,
        metadata=metadata,
    )


def build_arc_agi2_attempt_v1(
    *,
    attempt_id: str,
    grid: Sequence[Any],
    source_candidate_id: str,
    rank: int,
    confidence_label: str = "unknown",
    evidence_labels: Sequence[Any] | None = None,
    leakage_flags: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "attempt_id": _safe_text(attempt_id),
        "grid": to_arc_agi2_submission_json_safe_v1(grid),
        "source_candidate_id": _safe_text(source_candidate_id),
        "rank": int(rank),
        "confidence_label": _safe_text(confidence_label, "unknown"),
        "evidence_labels": [_safe_text(label) for label in (evidence_labels or []) if _safe_text(label)],
        "leakage_flags": _normalize_leakage_flags(leakage_flags or {}),
        "metadata": _json_safe(dict(metadata or {})),
    }


def validate_arc_agi2_attempt_v1(attempt: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "attempt_id": None,
        "rank": None,
        "blocked_reason_labels": [],
        "grid_validation": None,
    }
    if not isinstance(attempt, Mapping):
        result["blocked_reason_labels"].append("attempt_not_mapping")
        return result
    missing = [field for field in REQUIRED_ATTEMPT_FIELDS_V1 if field not in attempt]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result

    result["attempt_id"] = _safe_text(attempt.get("attempt_id"))
    result["rank"] = int(attempt.get("rank", 0)) if _safe_text(attempt.get("rank")) else None
    if not result["attempt_id"]:
        result["blocked_reason_labels"].append("empty_attempt_id")
    if result["rank"] not in {1, 2}:
        result["blocked_reason_labels"].append("rank_must_be_1_or_2")

    grid_validation = _validate_grid_like(attempt.get("grid"))
    result["grid_validation"] = grid_validation
    if not grid_validation["valid"]:
        result["blocked_reason_labels"].append("invalid_grid")
        result["blocked_reason_labels"].extend(f"grid:{reason}" for reason in grid_validation["reasons"])

    if not _safe_text(attempt.get("source_candidate_id")):
        result["blocked_reason_labels"].append("empty_source_candidate_id")
    if not _safe_text(attempt.get("confidence_label")):
        result["blocked_reason_labels"].append("empty_confidence_label")
    if not isinstance(attempt.get("evidence_labels"), list):
        result["blocked_reason_labels"].append("evidence_labels_not_list")
    if not isinstance(attempt.get("leakage_flags"), Mapping):
        result["blocked_reason_labels"].append("leakage_flags_not_mapping")
    else:
        leakage = _validate_leakage_flags(attempt.get("leakage_flags"))
        if not leakage["valid"]:
            result["blocked_reason_labels"].append("leakage_flags_not_clean")
            result["blocked_reason_labels"].extend(f"leakage:{label}" for label in leakage["blocked_reason_labels"])
    if not isinstance(attempt.get("metadata"), Mapping):
        result["blocked_reason_labels"].append("metadata_not_mapping")

    result["valid"] = not result["blocked_reason_labels"]
    return result


def rank_arc_agi2_candidate_attempts_top2_v1(
    candidate_packets: Sequence[Mapping[str, Any]],
    *,
    task_id: str,
    test_input_index: int,
    metadata: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(candidate_packets, Sequence) or len(candidate_packets) < 2:
        raise ValueError("rank_arc_agi2_candidate_attempts_top2_v1 requires at least two candidates")

    normalized_candidates = [
        _normalize_attempt(task_id=task_id, test_input_index=test_input_index, candidate=candidate, rank=index + 1)
        for index, candidate in enumerate(candidate_packets)
    ]
    ordered = sorted(
        normalized_candidates,
        key=lambda attempt: (
            -int(attempt.get("metadata", {}).get("candidate_score", 0)),
            _safe_text(attempt.get("source_candidate_id")),
            _attempt_grid_signature(attempt.get("grid")),
            _safe_text(attempt.get("confidence_label")),
            int(attempt.get("rank", 0)),
        ),
    )
    top_two = []
    for rank, attempt in enumerate(ordered[:2], start=1):
        adjusted = _json_safe(attempt)
        adjusted["rank"] = rank
        adjusted["attempt_id"] = _attempt_id(task_id, test_input_index, adjusted["source_candidate_id"], rank)
        adjusted.setdefault("metadata", {})
        adjusted["metadata"] = dict(adjusted["metadata"])
        adjusted["metadata"]["selected_rank"] = rank
        adjusted["metadata"]["task_id"] = _safe_text(task_id)
        adjusted["metadata"]["test_input_index"] = int(test_input_index)
        top_two.append(adjusted)

    if len(top_two) != 2:
        raise ValueError("rank_arc_agi2_candidate_attempts_top2_v1 could not produce two attempts")

    return top_two


def build_arc_agi2_top2_attempt_packet_v1(
    *,
    task_id: str,
    test_input_index: int,
    candidate_packets: Sequence[Mapping[str, Any]],
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    attempts = rank_arc_agi2_candidate_attempts_top2_v1(
        candidate_packets,
        task_id=task_id,
        test_input_index=test_input_index,
        metadata=metadata,
    )
    duplicate_attempt_grid = _attempt_grid_signature(attempts[0]["grid"]) == _attempt_grid_signature(attempts[1]["grid"])
    packet_metadata = _json_safe(dict(metadata or {}))
    packet_metadata.update(
        {
            "task_id": _safe_text(task_id),
            "test_input_index": int(test_input_index),
            "attempt_count": 2,
            "duplicate_attempt_grid": duplicate_attempt_grid,
            "synthetic_only": True,
            "source_kind": "synthetic_only",
        }
    )
    packet_metadata.setdefault("denied_authority", list(DEFAULT_DENIED_AUTHORITY_V1))
    return {
        "task_id": _safe_text(task_id),
        "test_input_index": int(test_input_index),
        "attempts": attempts,
        "duplicate_attempt_grid": duplicate_attempt_grid,
        "leakage_flags": _normalize_leakage_flags({}),
        "metadata": packet_metadata,
    }


def validate_arc_agi2_top2_attempt_packet_v1(packet: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "task_id": None,
        "test_input_index": None,
        "blocked_reason_labels": [],
        "attempt_validation_count": 0,
        "duplicate_attempt_grid": False,
    }
    if not isinstance(packet, Mapping):
        result["blocked_reason_labels"].append("packet_not_mapping")
        return result
    missing = [field for field in REQUIRED_TOP2_PACKET_FIELDS_V1 if field not in packet]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result

    result["task_id"] = _safe_text(packet.get("task_id"))
    try:
        result["test_input_index"] = int(packet.get("test_input_index"))
    except Exception:
        result["test_input_index"] = None
    if not result["task_id"]:
        result["blocked_reason_labels"].append("empty_task_id")
    if result["test_input_index"] is None or result["test_input_index"] < 0:
        result["blocked_reason_labels"].append("invalid_test_input_index")

    attempts = packet.get("attempts")
    if not isinstance(attempts, list):
        result["blocked_reason_labels"].append("attempts_not_list")
        attempts = []
    if len(attempts) != 2:
        result["blocked_reason_labels"].append("attempt_count_must_be_two")

    ranks: list[int] = []
    grid_signatures: list[str] = []
    for attempt in attempts:
        attempt_validation = validate_arc_agi2_attempt_v1(attempt)
        result["attempt_validation_count"] += 1
        if not attempt_validation["valid"]:
            result["blocked_reason_labels"].append(f"attempt_invalid:{attempt_validation.get('attempt_id')}")
            result["blocked_reason_labels"].extend(attempt_validation["blocked_reason_labels"])
        if isinstance(attempt, Mapping):
            try:
                ranks.append(int(attempt.get("rank")))
            except Exception:
                pass
            grid_signatures.append(_attempt_grid_signature(attempt.get("grid")))

    if sorted(ranks) != [1, 2] or len(set(ranks)) != 2:
        result["blocked_reason_labels"].append("rank_collision_or_missing_ranks")

    duplicate_attempt_grid = len(grid_signatures) == 2 and grid_signatures[0] == grid_signatures[1]
    result["duplicate_attempt_grid"] = duplicate_attempt_grid
    if duplicate_attempt_grid and not bool(packet.get("duplicate_attempt_grid", False)):
        result["blocked_reason_labels"].append("duplicate_attempt_grid_not_flagged")
    if not duplicate_attempt_grid and bool(packet.get("duplicate_attempt_grid", False)):
        result["blocked_reason_labels"].append("duplicate_attempt_grid_flag_inconsistent")

    leakage = _validate_leakage_flags(packet.get("leakage_flags"))
    if not leakage["valid"]:
        result["blocked_reason_labels"].append("packet_leakage_flags_not_clean")
        result["blocked_reason_labels"].extend(f"packet_leakage:{label}" for label in leakage["blocked_reason_labels"])

    if not isinstance(packet.get("metadata"), Mapping):
        result["blocked_reason_labels"].append("metadata_not_mapping")

    result["valid"] = not result["blocked_reason_labels"]
    return result


def build_arc_agi2_submission_task_entry_v1(
    *,
    task_id: str,
    test_input_packets: Sequence[Mapping[str, Any]],
    metadata: Mapping[str, Any] | None = None,
    leakage_flags: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    packets = sorted(
        [_json_safe(packet) for packet in test_input_packets],
        key=lambda packet: (int(packet.get("test_input_index", 0)), _safe_text(packet.get("task_id"))),
    )
    entry_metadata = _json_safe(dict(metadata or {}))
    entry_metadata.update(
        {
            "task_id": _safe_text(task_id),
            "test_input_count": len(packets),
            "synthetic_only": True,
        }
    )
    entry_metadata.setdefault("denied_authority", list(DEFAULT_DENIED_AUTHORITY_V1))
    return {
        "task_id": _safe_text(task_id),
        "test_input_packets": packets,
        "leakage_flags": _normalize_leakage_flags(leakage_flags or {}),
        "metadata": entry_metadata,
    }


def validate_arc_agi2_submission_task_entry_v1(entry: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "task_id": None,
        "blocked_reason_labels": [],
        "test_input_packet_validation_count": 0,
    }
    if not isinstance(entry, Mapping):
        result["blocked_reason_labels"].append("entry_not_mapping")
        return result
    missing = [field for field in REQUIRED_SUBMISSION_TASK_ENTRY_FIELDS_V1 if field not in entry]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result

    result["task_id"] = _safe_text(entry.get("task_id"))
    if not result["task_id"]:
        result["blocked_reason_labels"].append("empty_task_id")

    packets = entry.get("test_input_packets")
    if not isinstance(packets, list) or not packets:
        result["blocked_reason_labels"].append("test_input_packets_invalid")
        packets = []

    observed_indices: list[int] = []
    observed_sorted_indices: list[int] = []
    for packet in packets:
        packet_validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
        result["test_input_packet_validation_count"] += 1
        if not packet_validation["valid"]:
            result["blocked_reason_labels"].append(f"top2_packet_invalid:{packet_validation.get('task_id')}:{packet_validation.get('test_input_index')}")
            result["blocked_reason_labels"].extend(packet_validation["blocked_reason_labels"])
        if isinstance(packet, Mapping):
            try:
                observed_indices.append(int(packet.get("test_input_index")))
            except Exception:
                pass
            if _safe_text(packet.get("task_id")) != result["task_id"]:
                result["blocked_reason_labels"].append("task_id_mismatch")

    observed_sorted_indices = sorted(observed_indices)
    if observed_indices != observed_sorted_indices:
        result["blocked_reason_labels"].append("test_input_packets_not_sorted")
    if len(set(observed_indices)) != len(observed_indices):
        result["blocked_reason_labels"].append("duplicate_test_input_index")

    leakage = _validate_leakage_flags(entry.get("leakage_flags"))
    if not leakage["valid"]:
        result["blocked_reason_labels"].append("entry_leakage_flags_not_clean")
        result["blocked_reason_labels"].extend(f"entry_leakage:{label}" for label in leakage["blocked_reason_labels"])

    if not isinstance(entry.get("metadata"), Mapping):
        result["blocked_reason_labels"].append("metadata_not_mapping")

    result["valid"] = not result["blocked_reason_labels"]
    return result


def build_arc_agi2_submission_packet_v1(
    *,
    task_entries: Sequence[Mapping[str, Any]],
    metadata: Mapping[str, Any] | None = None,
    synthetic_only: bool = True,
    kaggle_ready: bool = False,
    requires_official_sample_submission_validation: bool = True,
    denied_authority: Sequence[str] | None = None,
    leakage_flags: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    entries = sorted(
        [_json_safe(entry) for entry in task_entries],
        key=lambda entry: ( _safe_text(entry.get("task_id")), min((int(packet.get("test_input_index", 0)) for packet in entry.get("test_input_packets", []) if isinstance(packet, Mapping)), default=0) ),
    )
    packet_metadata = _json_safe(dict(metadata or {}))
    packet_metadata.update(
        {
            "contract_name": CONTRACT_NAME_V1,
            "contract_version": CONTRACT_VERSION_V1,
            "synthetic_only": bool(synthetic_only),
            "kaggle_ready": bool(kaggle_ready),
            "requires_official_sample_submission_validation": bool(requires_official_sample_submission_validation),
            "denied_authority": list(denied_authority or DEFAULT_DENIED_AUTHORITY_V1),
            "task_entry_count": len(entries),
        }
    )
    return {
        "contract_name": CONTRACT_NAME_V1,
        "contract_version": CONTRACT_VERSION_V1,
        "synthetic_only": bool(synthetic_only),
        "kaggle_ready": bool(kaggle_ready),
        "requires_official_sample_submission_validation": bool(requires_official_sample_submission_validation),
        "denied_authority": list(denied_authority or DEFAULT_DENIED_AUTHORITY_V1),
        "task_entries": entries,
        "leakage_flags": _normalize_leakage_flags(leakage_flags or {}),
        "metadata": packet_metadata,
    }


def validate_arc_agi2_submission_packet_v1(packet: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "contract_name": None,
        "contract_version": None,
        "blocked_reason_labels": [],
        "task_entry_validation_count": 0,
    }
    if not isinstance(packet, Mapping):
        result["blocked_reason_labels"].append("packet_not_mapping")
        return result
    missing = [field for field in REQUIRED_SUBMISSION_PACKET_FIELDS_V1 if field not in packet]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result

    result["contract_name"] = _safe_text(packet.get("contract_name"))
    result["contract_version"] = _safe_text(packet.get("contract_version"))
    if result["contract_name"] != CONTRACT_NAME_V1:
        result["blocked_reason_labels"].append("contract_name_mismatch")
    if result["contract_version"] != CONTRACT_VERSION_V1:
        result["blocked_reason_labels"].append("contract_version_mismatch")

    if packet.get("synthetic_only") is not True:
        result["blocked_reason_labels"].append("synthetic_only_not_true")
    if packet.get("kaggle_ready") is True:
        result["blocked_reason_labels"].append("kaggle_ready_must_be_false_until_official_validation")
    if packet.get("requires_official_sample_submission_validation") is not True:
        result["blocked_reason_labels"].append("official_sample_submission_validation_required")

    denied = packet.get("denied_authority")
    if not isinstance(denied, list) or not denied:
        result["blocked_reason_labels"].append("denied_authority_invalid")

    task_entries = packet.get("task_entries")
    if not isinstance(task_entries, list) or not task_entries:
        result["blocked_reason_labels"].append("task_entries_invalid")
        task_entries = []

    observed_task_ids: list[str] = []
    observed_order: list[tuple[str, int]] = []
    for entry in task_entries:
        entry_validation = validate_arc_agi2_submission_task_entry_v1(entry)
        result["task_entry_validation_count"] += 1
        if not entry_validation["valid"]:
            result["blocked_reason_labels"].append(f"task_entry_invalid:{entry_validation.get('task_id')}")
            result["blocked_reason_labels"].extend(entry_validation["blocked_reason_labels"])
        if isinstance(entry, Mapping):
            task_id = _safe_text(entry.get("task_id"))
            observed_task_ids.append(task_id)
            packets = entry.get("test_input_packets", []) if isinstance(entry.get("test_input_packets"), list) else []
            for packet_item in packets:
                if isinstance(packet_item, Mapping):
                    try:
                        observed_order.append((task_id, int(packet_item.get("test_input_index"))))
                    except Exception:
                        pass

    if observed_task_ids != sorted(observed_task_ids):
        result["blocked_reason_labels"].append("task_entries_not_sorted")
    if len(set(observed_task_ids)) != len(observed_task_ids):
        result["blocked_reason_labels"].append("duplicate_task_id")

    if observed_order != sorted(observed_order):
        result["blocked_reason_labels"].append("test_input_packets_not_sorted")

    leakage = _validate_leakage_flags(packet.get("leakage_flags"))
    if not leakage["valid"]:
        result["blocked_reason_labels"].append("packet_leakage_flags_not_clean")
        result["blocked_reason_labels"].extend(f"packet_leakage:{label}" for label in leakage["blocked_reason_labels"])

    if not isinstance(packet.get("metadata"), Mapping):
        result["blocked_reason_labels"].append("metadata_not_mapping")

    result["valid"] = not result["blocked_reason_labels"]
    return result


def summarize_arc_agi2_submission_packet_v1(packet: Any) -> dict[str, Any]:
    task_entries = packet.get("task_entries", []) if isinstance(packet, Mapping) else []
    task_ids = []
    test_input_indices = []
    attempt_count = 0
    duplicate_attempt_grid_count = 0
    for entry in task_entries if isinstance(task_entries, list) else []:
        if isinstance(entry, Mapping):
            task_ids.append(_safe_text(entry.get("task_id")))
            packets = entry.get("test_input_packets", []) if isinstance(entry.get("test_input_packets"), list) else []
            for packet_item in packets:
                if isinstance(packet_item, Mapping):
                    test_input_indices.append(int(packet_item.get("test_input_index", 0)))
                    attempt_count += len(packet_item.get("attempts", [])) if isinstance(packet_item.get("attempts"), list) else 0
                    if bool(packet_item.get("duplicate_attempt_grid", False)):
                        duplicate_attempt_grid_count += 1
    return {
        "contract_name": _safe_text(packet.get("contract_name")) if isinstance(packet, Mapping) else "",
        "contract_version": _safe_text(packet.get("contract_version")) if isinstance(packet, Mapping) else "",
        "task_count": len(task_ids),
        "test_input_count": len(test_input_indices),
        "attempt_count": attempt_count,
        "duplicate_attempt_grid_count": duplicate_attempt_grid_count,
        "synthetic_only": bool(packet.get("synthetic_only", False)) if isinstance(packet, Mapping) else False,
        "kaggle_ready": bool(packet.get("kaggle_ready", False)) if isinstance(packet, Mapping) else False,
        "requires_official_sample_submission_validation": bool(packet.get("requires_official_sample_submission_validation", False)) if isinstance(packet, Mapping) else False,
    }


def _make_candidate(
    candidate_id: str,
    grid: Sequence[Any],
    *,
    confidence_label: str,
    evidence_labels: Sequence[str],
    validation_status: str,
    synthetic_only: bool = True,
    leakage_flags: Mapping[str, Any] | None = None,
    extra_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
        "validation_status": validation_status,
        "synthetic_only": synthetic_only,
        "evidence_labels": list(evidence_labels),
        "leakage_flags": _normalize_leakage_flags(leakage_flags or {}),
    }
    if extra_metadata:
        metadata.update(_json_safe(dict(extra_metadata)))
    return {
        "candidate_id": candidate_id,
        "grid": _json_safe(grid),
        "confidence_label": confidence_label,
        "evidence_labels": list(evidence_labels),
        "leakage_flags": _normalize_leakage_flags(leakage_flags or {}),
        "metadata": metadata,
        "trace": {"synthetic_only": synthetic_only, "internal_synthetic_only": synthetic_only},
        "validation_status": validation_status,
    }


def build_internal_arc_agi2_synthetic_submission_fixtures_v1() -> dict[str, Any]:
    candidate_a = _make_candidate(
        "cand_a",
        [[1, 1], [1, 1]],
        confidence_label="high",
        evidence_labels=["copy", "synthetic_fixture"],
        validation_status="fit",
    )
    candidate_b = _make_candidate(
        "cand_b",
        [[1, 1], [1, 0]],
        confidence_label="medium",
        evidence_labels=["partial_fit", "synthetic_fixture"],
        validation_status="partial_fit",
    )
    candidate_c = _make_candidate(
        "cand_c",
        [[2, 2], [2, 2]],
        confidence_label="low",
        evidence_labels=["copy", "alternate"],
        validation_status="fit",
    )
    candidate_d = _make_candidate(
        "cand_d",
        [[3, 3, 3], [3, 0, 3], [3, 3, 3]],
        confidence_label="high",
        evidence_labels=["symmetry", "synthetic_fixture"],
        validation_status="fit",
    )
    candidate_e = _make_candidate(
        "cand_e",
        [[4, 4], [4, 4]],
        confidence_label="medium",
        evidence_labels=["copy", "duplicate_grid"],
        validation_status="fit",
    )
    candidate_f = _make_candidate(
        "cand_f",
        [[4, 4], [4, 4]],
        confidence_label="medium",
        evidence_labels=["copy", "duplicate_grid"],
        validation_status="fit",
    )
    invalid_grid_candidate = _make_candidate(
        "cand_invalid_grid",
        [[1, 2], [3]],
        confidence_label="unknown",
        evidence_labels=["invalid_grid"],
        validation_status="invalid",
    )
    leakage_candidate = _make_candidate(
        "cand_leak",
        [[5, 5], [5, 5]],
        confidence_label="high",
        evidence_labels=["leakage"],
        validation_status="fit",
        leakage_flags={"uses_test_output": True},
    )

    single_top2 = build_arc_agi2_top2_attempt_packet_v1(
        task_id="task_single",
        test_input_index=0,
        candidate_packets=[candidate_a, candidate_b],
    )
    double_top2_a = build_arc_agi2_top2_attempt_packet_v1(
        task_id="task_double",
        test_input_index=0,
        candidate_packets=[candidate_a, candidate_b],
    )
    double_top2_b = build_arc_agi2_top2_attempt_packet_v1(
        task_id="task_double",
        test_input_index=1,
        candidate_packets=[candidate_d, candidate_c],
    )
    duplicate_grid_top2 = build_arc_agi2_top2_attempt_packet_v1(
        task_id="task_duplicate",
        test_input_index=0,
        candidate_packets=[candidate_e, candidate_f],
    )

    one_attempt_packet = _json_safe(single_top2)
    one_attempt_packet["attempts"] = one_attempt_packet["attempts"][:1]
    one_attempt_packet["duplicate_attempt_grid"] = False

    three_attempt_packet = _json_safe(single_top2)
    three_attempt_packet["attempts"].append(
        build_arc_agi2_attempt_v1(
            attempt_id="task_single:0:cand_extra:rank3",
            grid=[[9, 9], [9, 9]],
            source_candidate_id="cand_extra",
            rank=3,
            confidence_label="low",
            evidence_labels=["extra"],
            leakage_flags={},
            metadata={"synthetic_only": True},
        )
    )

    rank_collision_packet = _json_safe(single_top2)
    rank_collision_packet["attempts"][1]["rank"] = 1
    rank_collision_packet["attempts"][1]["attempt_id"] = "task_single:0:cand_b:rank1"

    invalid_grid_packet = _json_safe(single_top2)
    invalid_grid_packet["attempts"][0]["grid"] = [[1, 2], [3]]

    leakage_packet = _json_safe(single_top2)
    leakage_packet["attempts"][0]["leakage_flags"]["uses_test_output"] = True

    task_entry_single = build_arc_agi2_submission_task_entry_v1(
        task_id="task_single",
        test_input_packets=[single_top2],
    )
    task_entry_double = build_arc_agi2_submission_task_entry_v1(
        task_id="task_double",
        test_input_packets=[double_top2_b, double_top2_a],
    )
    task_entry_duplicate = build_arc_agi2_submission_task_entry_v1(
        task_id="task_duplicate",
        test_input_packets=[duplicate_grid_top2],
    )

    unsorted_task_entry_z = build_arc_agi2_submission_task_entry_v1(
        task_id="task_z",
        test_input_packets=[build_arc_agi2_top2_attempt_packet_v1(task_id="task_z", test_input_index=1, candidate_packets=[candidate_a, candidate_b])],
    )
    unsorted_task_entry_a = build_arc_agi2_submission_task_entry_v1(
        task_id="task_a",
        test_input_packets=[build_arc_agi2_top2_attempt_packet_v1(task_id="task_a", test_input_index=0, candidate_packets=[candidate_d, candidate_c])],
    )
    sorted_submission_packet = build_arc_agi2_submission_packet_v1(
        task_entries=[unsorted_task_entry_z, unsorted_task_entry_a],
    )

    return {
        "single_task_single_test_input_valid": {
            "top2_packet": single_top2,
            "task_entry": task_entry_single,
            "submission_packet": build_arc_agi2_submission_packet_v1(task_entries=[task_entry_single]),
        },
        "single_task_two_test_inputs_valid": {
            "top2_packets": [double_top2_a, double_top2_b],
            "task_entry": task_entry_double,
            "submission_packet": build_arc_agi2_submission_packet_v1(task_entries=[task_entry_double]),
        },
        "duplicate_attempt_grid_valid": duplicate_grid_top2,
        "invalid_one_attempt_packet": one_attempt_packet,
        "invalid_three_attempt_packet": three_attempt_packet,
        "rank_collision_packet": rank_collision_packet,
        "invalid_grid_packet": invalid_grid_packet,
        "leakage_flag_true_packet": leakage_packet,
        "deterministic_sorting": {
            "unsorted_task_entries": [unsorted_task_entry_z, unsorted_task_entry_a],
            "sorted_submission_packet": sorted_submission_packet,
        },
        "json_safe_serialization": build_arc_agi2_submission_packet_v1(task_entries=[task_entry_single, task_entry_duplicate]),
        "internal_candidates": {
            "fit_pair": [candidate_a, candidate_b],
            "duplicate_grid_pair": [candidate_e, candidate_f],
            "invalid_grid_candidate": invalid_grid_candidate,
            "leakage_candidate": leakage_candidate,
        },
    }


__all__ = [
    "CONTRACT_NAME_V1",
    "CONTRACT_VERSION_V1",
    "DEFAULT_DENIED_AUTHORITY_V1",
    "LEAKAGE_FLAG_NAMES_V1",
    "REQUIRED_ATTEMPT_FIELDS_V1",
    "REQUIRED_SUBMISSION_PACKET_FIELDS_V1",
    "REQUIRED_SUBMISSION_TASK_ENTRY_FIELDS_V1",
    "REQUIRED_TOP2_PACKET_FIELDS_V1",
    "SCHEMA_VERSION_V1",
    "build_arc_agi2_attempt_v1",
    "build_arc_agi2_submission_packet_v1",
    "build_arc_agi2_submission_task_entry_v1",
    "build_arc_agi2_top2_attempt_packet_v1",
    "build_internal_arc_agi2_synthetic_submission_fixtures_v1",
    "rank_arc_agi2_candidate_attempts_top2_v1",
    "serialize_arc_agi2_submission_json_safe_v1",
    "summarize_arc_agi2_submission_packet_v1",
    "to_arc_agi2_submission_json_safe_v1",
    "validate_arc_agi2_attempt_v1",
    "validate_arc_agi2_submission_packet_v1",
    "validate_arc_agi2_submission_task_entry_v1",
    "validate_arc_agi2_top2_attempt_packet_v1",
]
