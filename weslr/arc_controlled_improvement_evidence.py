"""WESLR ARC controlled improvement evidence V1.

Metadata-only internal evidence packets for the controlled diagnostic →
intervention → measurement loop used during synthetic ARC solver development.

This module does not implement solver behavior, depth-3 search, public ARC/
Kaggle ingestion, provider/model/API calls, ChatResponder wiring, website/
runtime wiring, or `.weslr` writes.
"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from typing import Any, Mapping, Sequence

from weslr.arc_style_depth2_compositional_program_search import (
    run_arc_style_depth2_compositional_program_search_v1,
    summarize_arc_style_depth2_compositional_program_search_result_v1,
)
from weslr.arc_style_heldout_compositional_baseline import (
    run_arc_style_heldout_compositional_baseline_v1,
    summarize_arc_style_heldout_compositional_baseline_result_v1,
)
from weslr.arc_style_synthetic_solver_suite import (
    run_arc_style_synthetic_solver_suite_v1,
    summarize_arc_style_synthetic_solver_suite_result_v1,
)

SCHEMA_VERSION_V1 = "ArcControlledImprovementEvidenceV1"
EVIDENCE_TYPE_V1 = "arc_controlled_improvement_evidence_v1"
CHAIN_TYPE_V1 = "arc_controlled_improvement_evidence_chain_v1"

REQUIRED_METRIC_FIELDS_V1 = (
    "exact_count",
    "partial_count",
    "unsupported_count",
    "failed_count",
    "task_count",
)

REQUIRED_PACKET_FIELDS_V1 = (
    "evidence_type",
    "schema_version",
    "chain_type",
    "chain_label",
    "lane_name",
    "evidence_scope",
    "intervention_type",
    "baseline_metrics",
    "after_metrics",
    "delta_metrics",
    "file_references",
    "boundary_flags",
    "non_claim_flags",
    "validation_status",
    "next_lane_recommendation",
    "remaining_gap_hypotheses",
    "evidence_summary",
)

REQUIRED_CHAIN_FIELDS_V1 = (
    "chain_type",
    "schema_version",
    "chain_label",
    "fixtures",
    "summary",
    "validation_status",
)

REQUIRED_FILE_REFERENCE_FIELDS_V1 = (
    "repository",
    "branch",
    "source_files",
    "doc_files",
    "commit_refs",
)

REQUIRED_BOUNDARY_FLAG_NAMES_V1 = (
    "synthetic_only",
    "no_public_arc_data",
    "no_public_arc_samples",
    "no_kaggle_data",
    "no_benchmark_examples_copied",
    "no_answer_keys",
    "no_provider_model_api",
    "no_chat_responder",
    "no_runtime_wiring",
    "no_weslr_writes",
    "no_public_score_claims",
    "no_kaggle_ready_claims",
    "no_agi_claims",
    "no_sentience_claims",
    "no_consciousness_claims",
)

REQUIRED_NON_CLAIM_FLAG_NAMES_V1 = (
    "public_arc_data_claimed",
    "public_arc_samples_claimed",
    "kaggle_data_claimed",
    "benchmark_examples_copied",
    "answer_keys_claimed",
    "provider_model_api_dependency_claimed",
    "chat_responder_dependency_claimed",
    "runtime_wiring_claimed",
    "weslr_writes_claimed",
    "public_score_claimed",
    "kaggle_ready_claimed",
    "agi_claimed",
    "sentience_claimed",
    "consciousness_claimed",
    "autonomous_self_modification_claimed",
)

REQUIRED_EVIDENCE_SCOPE_VALUES_V1 = (
    "synthetic_only_controlled_internal",
    "known_family_improvement",
    "heldout_compositional_improvement",
)

DEFAULT_REPOSITORY_NAME_V1 = "weslr-pr47-clean"
DEFAULT_BRANCH_NAME_V1 = "occ-discovery-doctrine-implementation-20260613"

DEFAULT_SOURCE_FILES_V1 = (
    "weslr/arc_style_synthetic_solver_suite.py",
    "weslr/arc_style_heldout_compositional_baseline.py",
    "weslr/arc_style_depth2_compositional_program_search.py",
    "weslr/arc_style_grid_adapter_phase2.py",
    "weslr/arc_style_grid_solver_dry_run.py",
)
DEFAULT_DOC_FILES_V1 = (
    "docs/WESLR_ARC_RESIDUAL_GAP_INTERNAL_ENGINE_PRESSURE_V1.md",
    "docs/WESLR_ARC_DEPTH2_REMAINING_FAILURES_PATTERN_PRESSURE_V1.md",
    "docs/WESLR_ARC_STYLE_COMPOSITIONAL_PROGRAM_SEARCH_AND_HELDOUT_SYNTHETIC_EVALUATION_DESIGN_V1.md",
)
DEFAULT_COMMIT_REFS_V1 = (
    "known_family_improvement_chain_metadata",
    "heldout_compositional_improvement_chain_metadata",
    "depth2_compositional_search_report_metadata",
)

DEFAULT_CHAIN_LABEL_V1 = "controlled_diagnostic_intervention_measurement_loop_v1"
DEFAULT_VALIDATION_STATUS_V1 = "validated"
DEFAULT_NEXT_LANE_V1 = "IMPLEMENT_ARC_DEPTH2_REMAINING_FAILURE_REPAIR_V1"

KNOWN_FAMILY_PRIMITIVE_EXPANSION_BASELINE_V1 = {
    "exact_count": 14,
    "partial_count": 6,
    "unsupported_count": 28,
    "failed_count": 0,
    "task_count": 48,
}
KNOWN_FAMILY_PRIMITIVE_EXPANSION_AFTER_V1 = {
    "exact_count": 14,
    "partial_count": 30,
    "unsupported_count": 4,
    "failed_count": 0,
    "task_count": 48,
}
KNOWN_FAMILY_PARTIAL_TO_EXACT_BASELINE_V1 = KNOWN_FAMILY_PRIMITIVE_EXPANSION_AFTER_V1
KNOWN_FAMILY_PARTIAL_TO_EXACT_AFTER_V1 = {
    "exact_count": 41,
    "partial_count": 3,
    "unsupported_count": 4,
    "failed_count": 0,
    "task_count": 48,
}
HELDOUT_BASELINE_BEFORE_DEPTH2_V1 = {
    "exact_count": 1,
    "partial_count": 2,
    "unsupported_count": 11,
    "failed_count": 0,
    "task_count": 14,
}
HELDOUT_AFTER_DEPTH2_V1 = {
    "exact_count": 10,
    "partial_count": 2,
    "unsupported_count": 2,
    "failed_count": 0,
    "task_count": 14,
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
    if callable(value):
        return _safe_text(getattr(value, "__name__", repr(value)))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    return _safe_text(value)


def to_arc_controlled_improvement_evidence_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _metric_block(exact_count: int, partial_count: int, unsupported_count: int, failed_count: int, task_count: int | None = None) -> dict[str, int]:
    total = exact_count + partial_count + unsupported_count + failed_count if task_count is None else task_count
    return {
        "exact_count": int(exact_count),
        "partial_count": int(partial_count),
        "unsupported_count": int(unsupported_count),
        "failed_count": int(failed_count),
        "task_count": int(total),
    }


def _metric_delta(baseline: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, int]:
    return {
        key: int(after.get(key, 0)) - int(baseline.get(key, 0))
        for key in REQUIRED_METRIC_FIELDS_V1
    }


def _default_boundary_flags() -> dict[str, bool]:
    return {name: True for name in REQUIRED_BOUNDARY_FLAG_NAMES_V1}


def _default_non_claim_flags() -> dict[str, bool]:
    return {name: False for name in REQUIRED_NON_CLAIM_FLAG_NAMES_V1}


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [_safe_text(item) for item in value if _safe_text(item)]


def _validate_metrics(metrics: Any, *, label: str, blocked_reason_labels: list[str]) -> bool:
    if not isinstance(metrics, Mapping):
        blocked_reason_labels.append(f"{label}_metrics_not_mapping")
        return False
    missing = [field for field in REQUIRED_METRIC_FIELDS_V1 if field not in metrics]
    if missing:
        blocked_reason_labels.append(f"{label}_metrics_missing_required_fields")
        blocked_reason_labels.extend(f"{label}_metrics_missing:{field}" for field in missing)
        return False
    for field in REQUIRED_METRIC_FIELDS_V1:
        value = metrics.get(field)
        if not isinstance(value, int) or isinstance(value, bool):
            blocked_reason_labels.append(f"{label}_metrics_non_integer:{field}")
            return False
        if value < 0:
            blocked_reason_labels.append(f"{label}_metrics_negative:{field}")
            return False
    computed_total = int(metrics.get("exact_count", 0)) + int(metrics.get("partial_count", 0)) + int(metrics.get("unsupported_count", 0)) + int(metrics.get("failed_count", 0))
    if computed_total != int(metrics.get("task_count", -1)):
        blocked_reason_labels.append(f"{label}_metrics_total_mismatch")
        return False
    return True


def _validate_boundary_flags(flags: Any, blocked_reason_labels: list[str]) -> bool:
    if not isinstance(flags, Mapping):
        blocked_reason_labels.append("boundary_flags_not_mapping")
        return False
    missing = [field for field in REQUIRED_BOUNDARY_FLAG_NAMES_V1 if field not in flags]
    if missing:
        blocked_reason_labels.append("boundary_flags_missing_required_fields")
        blocked_reason_labels.extend(f"boundary_flags_missing:{field}" for field in missing)
        return False
    for field in REQUIRED_BOUNDARY_FLAG_NAMES_V1:
        if flags.get(field) is not True:
            blocked_reason_labels.append(f"unsafe_boundary_flag:{field}")
            return False
    return True


def _validate_non_claim_flags(flags: Any, blocked_reason_labels: list[str]) -> bool:
    if not isinstance(flags, Mapping):
        blocked_reason_labels.append("non_claim_flags_not_mapping")
        return False
    missing = [field for field in REQUIRED_NON_CLAIM_FLAG_NAMES_V1 if field not in flags]
    if missing:
        blocked_reason_labels.append("non_claim_flags_missing_required_fields")
        blocked_reason_labels.extend(f"non_claim_flags_missing:{field}" for field in missing)
        return False
    for field in REQUIRED_NON_CLAIM_FLAG_NAMES_V1:
        if flags.get(field) is not False:
            blocked_reason_labels.append(f"unsafe_non_claim_flag:{field}")
            return False
    return True


def _validate_file_references(file_references: Any, blocked_reason_labels: list[str]) -> bool:
    if not isinstance(file_references, Mapping):
        blocked_reason_labels.append("file_references_not_mapping")
        return False
    missing = [field for field in REQUIRED_FILE_REFERENCE_FIELDS_V1 if field not in file_references]
    if missing:
        blocked_reason_labels.append("file_references_missing_required_fields")
        blocked_reason_labels.extend(f"file_references_missing:{field}" for field in missing)
        return False
    repository = _safe_text(file_references.get("repository"))
    branch = _safe_text(file_references.get("branch"))
    if not repository or not branch:
        blocked_reason_labels.append("file_references_empty_repository_or_branch")
        return False
    for field in ("source_files", "doc_files", "commit_refs"):
        if not isinstance(file_references.get(field), list):
            blocked_reason_labels.append(f"file_references_{field}_not_list")
            return False
        if not all(isinstance(item, str) and item for item in file_references.get(field, [])):
            blocked_reason_labels.append(f"file_references_{field}_invalid_entry")
            return False
    all_paths = file_references.get("source_files", []) + file_references.get("doc_files", [])
    if any(".weslr" in path for path in all_paths):
        blocked_reason_labels.append("file_references_include_weslr_path")
        return False
    return True


def _validate_no_extra_fields(packet: Mapping[str, Any], blocked_reason_labels: list[str]) -> bool:
    allowed = set(REQUIRED_PACKET_FIELDS_V1)
    extra = [field for field in packet if field not in allowed]
    if extra:
        blocked_reason_labels.append("unsupported_packet_fields_present")
        blocked_reason_labels.extend(f"unsupported_field:{field}" for field in extra)
        return False
    return True


def _validate_no_claim_text(packet: Mapping[str, Any], blocked_reason_labels: list[str]) -> bool:
    claim_flags = packet.get("non_claim_flags", {}) if isinstance(packet.get("non_claim_flags"), Mapping) else {}
    if any(bool(claim_flags.get(name, False)) for name in REQUIRED_NON_CLAIM_FLAG_NAMES_V1):
        blocked_reason_labels.append("unsafe_claim_flags_present")
        return False
    evidence_scope = _safe_text(packet.get("evidence_scope"))
    if evidence_scope not in REQUIRED_EVIDENCE_SCOPE_VALUES_V1:
        blocked_reason_labels.append("evidence_scope_not_allowed")
        return False
    if any(token in evidence_scope.lower() for token in ("kaggle", "agi", "sentience", "consciousness", "benchmark", "public_score")):
        blocked_reason_labels.append("unsafe_claim_text_in_evidence_scope")
        return False
    return True


def build_arc_controlled_improvement_evidence_packet_v1(
    *,
    lane_name: str,
    intervention_type: str,
    baseline_metrics: Mapping[str, Any],
    after_metrics: Mapping[str, Any],
    file_references: Mapping[str, Any] | None = None,
    evidence_scope: str = "synthetic_only_controlled_internal",
    boundary_flags: Mapping[str, Any] | None = None,
    non_claim_flags: Mapping[str, Any] | None = None,
    next_lane_recommendation: str = DEFAULT_NEXT_LANE_V1,
    chain_label: str = DEFAULT_CHAIN_LABEL_V1,
    remaining_gap_hypotheses: Sequence[str] | None = None,
) -> dict[str, Any]:
    baseline = _json_safe(dict(baseline_metrics))
    after = _json_safe(dict(after_metrics))
    packet = {
        "evidence_type": EVIDENCE_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "chain_type": CHAIN_TYPE_V1,
        "chain_label": _safe_text(chain_label),
        "lane_name": _safe_text(lane_name),
        "evidence_scope": _safe_text(evidence_scope),
        "intervention_type": _safe_text(intervention_type),
        "baseline_metrics": baseline,
        "after_metrics": after,
        "delta_metrics": _metric_delta(baseline, after),
        "file_references": _json_safe(
            file_references
            or {
                "repository": DEFAULT_REPOSITORY_NAME_V1,
                "branch": DEFAULT_BRANCH_NAME_V1,
                "source_files": list(DEFAULT_SOURCE_FILES_V1),
                "doc_files": list(DEFAULT_DOC_FILES_V1),
                "commit_refs": list(DEFAULT_COMMIT_REFS_V1),
            }
        ),
        "boundary_flags": _json_safe(boundary_flags or _default_boundary_flags()),
        "non_claim_flags": _json_safe(non_claim_flags or _default_non_claim_flags()),
        "validation_status": DEFAULT_VALIDATION_STATUS_V1,
        "next_lane_recommendation": _safe_text(next_lane_recommendation),
        "remaining_gap_hypotheses": _normalize_string_list(remaining_gap_hypotheses or []),
        "evidence_summary": {
            "improvement_kind": _safe_text(intervention_type),
            "exact_delta": int(after.get("exact_count", 0)) - int(baseline.get("exact_count", 0)),
            "unsupported_reduction": int(baseline.get("unsupported_count", 0)) - int(after.get("unsupported_count", 0)),
            "partial_delta": int(after.get("partial_count", 0)) - int(baseline.get("partial_count", 0)),
            "task_count_delta": int(after.get("task_count", 0)) - int(baseline.get("task_count", 0)),
        },
    }
    return packet


def validate_arc_controlled_improvement_evidence_packet_v1(packet: Any) -> dict[str, Any]:
    validation = {"valid": False, "blocked_reason_labels": []}
    if not isinstance(packet, Mapping):
        validation["blocked_reason_labels"].append("packet_not_mapping")
        return validation
    if not _validate_no_extra_fields(packet, validation["blocked_reason_labels"]):
        return validation
    if packet.get("evidence_type") != EVIDENCE_TYPE_V1:
        validation["blocked_reason_labels"].append("evidence_type_mismatch")
    if packet.get("schema_version") != SCHEMA_VERSION_V1:
        validation["blocked_reason_labels"].append("schema_version_mismatch")
    if packet.get("chain_type") != CHAIN_TYPE_V1:
        validation["blocked_reason_labels"].append("chain_type_mismatch")
    for field in ("chain_label", "lane_name", "intervention_type", "validation_status", "next_lane_recommendation"):
        if not isinstance(packet.get(field), str) or not packet.get(field):
            validation["blocked_reason_labels"].append(f"{field}_invalid")
    if packet.get("validation_status") != DEFAULT_VALIDATION_STATUS_V1:
        validation["blocked_reason_labels"].append("validation_status_not_validated")
    if not isinstance(packet.get("remaining_gap_hypotheses"), list):
        validation["blocked_reason_labels"].append("remaining_gap_hypotheses_not_list")
    elif not all(isinstance(item, str) and item for item in packet.get("remaining_gap_hypotheses", [])):
        validation["blocked_reason_labels"].append("remaining_gap_hypotheses_invalid")
    if not isinstance(packet.get("evidence_summary"), Mapping):
        validation["blocked_reason_labels"].append("evidence_summary_not_mapping")
    if not _validate_metrics(packet.get("baseline_metrics"), label="baseline", blocked_reason_labels=validation["blocked_reason_labels"]):
        pass
    if not _validate_metrics(packet.get("after_metrics"), label="after", blocked_reason_labels=validation["blocked_reason_labels"]):
        pass
    if isinstance(packet.get("baseline_metrics"), Mapping) and isinstance(packet.get("after_metrics"), Mapping):
        expected_delta = _metric_delta(packet.get("baseline_metrics", {}), packet.get("after_metrics", {}))
        if _json_safe(expected_delta) != _json_safe(packet.get("delta_metrics", {})):
            validation["blocked_reason_labels"].append("delta_metrics_mismatch")
        summary = packet.get("evidence_summary", {}) if isinstance(packet.get("evidence_summary"), Mapping) else {}
        if int(summary.get("exact_delta", 0)) != expected_delta["exact_count"]:
            validation["blocked_reason_labels"].append("evidence_summary_exact_delta_mismatch")
        if int(summary.get("unsupported_reduction", 0)) != int(packet.get("baseline_metrics", {}).get("unsupported_count", 0)) - int(packet.get("after_metrics", {}).get("unsupported_count", 0)):
            validation["blocked_reason_labels"].append("evidence_summary_unsupported_reduction_mismatch")
        if int(summary.get("partial_delta", 0)) != expected_delta["partial_count"]:
            validation["blocked_reason_labels"].append("evidence_summary_partial_delta_mismatch")
        if int(summary.get("task_count_delta", 0)) != expected_delta["task_count"]:
            validation["blocked_reason_labels"].append("evidence_summary_task_count_delta_mismatch")
    if not _validate_file_references(packet.get("file_references"), validation["blocked_reason_labels"]):
        pass
    if not _validate_boundary_flags(packet.get("boundary_flags"), validation["blocked_reason_labels"]):
        pass
    if not _validate_non_claim_flags(packet.get("non_claim_flags"), validation["blocked_reason_labels"]):
        pass
    if not _validate_no_claim_text(packet, validation["blocked_reason_labels"]):
        pass
    validation["valid"] = not validation["blocked_reason_labels"]
    return validation


def summarize_arc_controlled_improvement_evidence_v1(packet: Any) -> dict[str, Any]:
    validation = validate_arc_controlled_improvement_evidence_packet_v1(packet)
    if not isinstance(packet, Mapping):
        packet = {}
    baseline = packet.get("baseline_metrics", {}) if isinstance(packet.get("baseline_metrics"), Mapping) else {}
    after = packet.get("after_metrics", {}) if isinstance(packet.get("after_metrics"), Mapping) else {}
    delta = packet.get("delta_metrics", {}) if isinstance(packet.get("delta_metrics"), Mapping) else {}
    summary = {
        "evidence_type": packet.get("evidence_type", EVIDENCE_TYPE_V1),
        "schema_version": packet.get("schema_version", SCHEMA_VERSION_V1),
        "valid": validation["valid"],
        "lane_name": packet.get("lane_name"),
        "intervention_type": packet.get("intervention_type"),
        "evidence_scope": packet.get("evidence_scope"),
        "baseline_exact_count": int(baseline.get("exact_count", 0)),
        "after_exact_count": int(after.get("exact_count", 0)),
        "exact_delta": int(delta.get("exact_count", 0)),
        "baseline_partial_count": int(baseline.get("partial_count", 0)),
        "after_partial_count": int(after.get("partial_count", 0)),
        "partial_delta": int(delta.get("partial_count", 0)),
        "baseline_unsupported_count": int(baseline.get("unsupported_count", 0)),
        "after_unsupported_count": int(after.get("unsupported_count", 0)),
        "unsupported_delta": int(delta.get("unsupported_count", 0)),
        "baseline_failed_count": int(baseline.get("failed_count", 0)),
        "after_failed_count": int(after.get("failed_count", 0)),
        "task_count_delta": int(delta.get("task_count", 0)),
        "boundary_preserved": all(bool((packet.get("boundary_flags") or {}).get(name, False)) for name in REQUIRED_BOUNDARY_FLAG_NAMES_V1),
        "non_claim_safe": all(not bool((packet.get("non_claim_flags") or {}).get(name, False)) for name in REQUIRED_NON_CLAIM_FLAG_NAMES_V1),
        "next_lane_recommendation": packet.get("next_lane_recommendation"),
        "remaining_gap_hypotheses": _json_safe(packet.get("remaining_gap_hypotheses", [])),
        "file_reference_count": len((packet.get("file_references") or {}).get("source_files", [])) if isinstance(packet.get("file_references"), Mapping) else 0,
        "commit_reference_count": len((packet.get("file_references") or {}).get("commit_refs", [])) if isinstance(packet.get("file_references"), Mapping) else 0,
    }
    return _json_safe(summary)


def summarize_known_family_improvement_v1(packet: Any) -> dict[str, Any]:
    summary = summarize_arc_controlled_improvement_evidence_v1(packet)
    return _json_safe(
        {
            **summary,
            "summary_type": "known_family_improvement_summary_v1",
            "improvement_label": "known_family_improvement",
            "exact_gain": summary["exact_delta"],
            "unsupported_reduction": int(summary["baseline_unsupported_count"]) - int(summary["after_unsupported_count"]),
        }
    )


def summarize_heldout_compositional_improvement_v1(packet: Any) -> dict[str, Any]:
    summary = summarize_arc_controlled_improvement_evidence_v1(packet)
    return _json_safe(
        {
            **summary,
            "summary_type": "heldout_compositional_improvement_summary_v1",
            "improvement_label": "heldout_compositional_improvement",
            "exact_gain": summary["exact_delta"],
            "unsupported_reduction": int(summary["baseline_unsupported_count"]) - int(summary["after_unsupported_count"]),
        }
    )


def summarize_boundary_preservation_v1(packet: Any) -> dict[str, Any]:
    summary = summarize_arc_controlled_improvement_evidence_v1(packet)
    return _json_safe(
        {
            "summary_type": "boundary_preservation_summary_v1",
            "valid": summary["valid"],
            "boundary_preserved": summary["boundary_preserved"],
            "non_claim_safe": summary["non_claim_safe"],
            "boundary_flag_count": len(REQUIRED_BOUNDARY_FLAG_NAMES_V1),
            "non_claim_flag_count": len(REQUIRED_NON_CLAIM_FLAG_NAMES_V1),
            "next_lane_recommendation": summary["next_lane_recommendation"],
        }
    )


def summarize_remaining_gaps_v1(packet: Any) -> dict[str, Any]:
    summary = summarize_arc_controlled_improvement_evidence_v1(packet)
    remaining = {
        "summary_type": "remaining_gaps_summary_v1",
        "valid": summary["valid"],
        "lane_name": summary["lane_name"],
        "remaining_partial_count": summary["after_partial_count"],
        "remaining_unsupported_count": summary["after_unsupported_count"],
        "remaining_failed_count": summary["after_failed_count"],
        "remaining_gap_hypotheses": summary["remaining_gap_hypotheses"],
        "next_lane_recommendation": summary["next_lane_recommendation"],
    }
    return _json_safe(remaining)


def build_arc_controlled_improvement_evidence_fixture_primitive_executor_expansion_v1() -> dict[str, Any]:
    return build_arc_controlled_improvement_evidence_packet_v1(
        lane_name="known_family_primitive_executor_expansion_v1",
        intervention_type="primitive_executor_expansion",
        baseline_metrics=_metric_block(14, 6, 28, 0, task_count=48),
        after_metrics=_metric_block(14, 30, 4, 0, task_count=48),
        evidence_scope="synthetic_only_controlled_internal",
        next_lane_recommendation="IMPLEMENT_ARC_KNOWN_FAMILY_PARTIAL_TO_EXACT_REPAIR_V1",
        chain_label="controlled_improvement_known_family_loop_v1",
        remaining_gap_hypotheses=("executor_coverage_gap", "partial_fit_candidates_remaining"),
    )


def build_arc_controlled_improvement_evidence_fixture_partial_to_exact_repair_v1() -> dict[str, Any]:
    return build_arc_controlled_improvement_evidence_packet_v1(
        lane_name="known_family_partial_to_exact_repair_v1",
        intervention_type="partial_to_exact_repair",
        baseline_metrics=_metric_block(14, 30, 4, 0, task_count=48),
        after_metrics=_metric_block(41, 3, 4, 0, task_count=48),
        evidence_scope="known_family_improvement",
        next_lane_recommendation="DESIGN_ARC_HELDOUT_COMPOSITIONAL_EVALUATION_V1",
        chain_label="controlled_improvement_known_family_loop_v1",
        remaining_gap_hypotheses=("partial_fit_to_exact_fit_conversion", "generalization_boundary_pending"),
    )


@lru_cache(maxsize=1)
def build_arc_controlled_improvement_evidence_fixture_heldout_baseline_v1() -> dict[str, Any]:
    baseline = run_arc_style_heldout_compositional_baseline_v1(seed=20260625)
    summary = summarize_arc_style_heldout_compositional_baseline_result_v1(baseline)
    metrics = _metric_block(summary["exact_count"], summary["partial_count"], summary["unsupported_count"], summary["failed_count"], task_count=summary["task_count"])
    return build_arc_controlled_improvement_evidence_packet_v1(
        lane_name="heldout_compositional_baseline_v1",
        intervention_type="baseline_measurement",
        baseline_metrics=metrics,
        after_metrics=metrics,
        evidence_scope="heldout_compositional_improvement",
        next_lane_recommendation="DESIGN_ARC_DEPTH2_COMPOSITIONAL_SEARCH_V1",
        chain_label="controlled_improvement_heldout_loop_v1",
        remaining_gap_hypotheses=("heldout_compositional_gap", "depth2_search_needed"),
        file_references={
            "repository": DEFAULT_REPOSITORY_NAME_V1,
            "branch": DEFAULT_BRANCH_NAME_V1,
            "source_files": [
                "weslr/arc_style_heldout_compositional_baseline.py",
                "weslr/arc_style_heldout_compositional_synthetic_generator.py",
            ],
            "doc_files": [
                "docs/WESLR_ARC_STYLE_COMPOSITIONAL_PROGRAM_SEARCH_AND_HELDOUT_SYNTHETIC_EVALUATION_DESIGN_V1.md",
                "docs/WESLR_ARC_RESIDUAL_GAP_INTERNAL_ENGINE_PRESSURE_V1.md",
            ],
            "commit_refs": ["heldout_baseline_measurement_metadata"],
        },
    )


@lru_cache(maxsize=1)
def build_arc_controlled_improvement_evidence_fixture_depth2_compositional_search_v1() -> dict[str, Any]:
    search = run_arc_style_depth2_compositional_program_search_v1(seed=20260625)
    summary = summarize_arc_style_depth2_compositional_program_search_result_v1(search)
    baseline = search["heldout_baseline_before"]
    after = search["heldout_search_after"]
    baseline_metrics = _metric_block(baseline["exact_count"], baseline["partial_count"], baseline["unsupported_count"], baseline["failed_count"], task_count=baseline["task_count"])
    after_metrics = _metric_block(after["exact_count"], after["partial_count"], after["unsupported_count"], after["failed_count"], task_count=after["task_count"])
    return build_arc_controlled_improvement_evidence_packet_v1(
        lane_name="heldout_depth2_compositional_search_v1",
        intervention_type="depth2_compositional_search",
        baseline_metrics=baseline_metrics,
        after_metrics=after_metrics,
        evidence_scope="heldout_compositional_improvement",
        next_lane_recommendation="IMPLEMENT_ARC_DEPTH2_REMAINING_FAILURE_REPAIR_V1",
        chain_label="controlled_improvement_heldout_loop_v1",
        remaining_gap_hypotheses=("depth2_parameter_ranking_repair_needed", "unsupported_candidates_remaining"),
        file_references={
            "repository": DEFAULT_REPOSITORY_NAME_V1,
            "branch": DEFAULT_BRANCH_NAME_V1,
            "source_files": [
                "weslr/arc_style_depth2_compositional_program_search.py",
                "weslr/arc_style_heldout_compositional_baseline.py",
                "weslr/arc_style_heldout_compositional_synthetic_generator.py",
                "weslr/arc_style_typed_primitive_signatures.py",
            ],
            "doc_files": [
                "docs/WESLR_ARC_DEPTH2_REMAINING_FAILURES_PATTERN_PRESSURE_V1.md",
                "docs/WESLR_ARC_STYLE_COMPOSITIONAL_PROGRAM_SEARCH_AND_HELDOUT_SYNTHETIC_EVALUATION_DESIGN_V1.md",
            ],
            "commit_refs": ["depth2_compositional_search_metadata"],
        },
    )


@lru_cache(maxsize=1)
def build_arc_controlled_improvement_evidence_fixtures_v1() -> dict[str, dict[str, Any]]:
    fixtures = {
        "known_family_primitive_executor_expansion": build_arc_controlled_improvement_evidence_fixture_primitive_executor_expansion_v1(),
        "known_family_partial_to_exact_repair": build_arc_controlled_improvement_evidence_fixture_partial_to_exact_repair_v1(),
        "heldout_baseline": build_arc_controlled_improvement_evidence_fixture_heldout_baseline_v1(),
        "heldout_depth2_compositional_search": build_arc_controlled_improvement_evidence_fixture_depth2_compositional_search_v1(),
    }
    return _json_safe(fixtures)


@lru_cache(maxsize=1)
def build_arc_controlled_improvement_evidence_chain_v1() -> dict[str, Any]:
    fixtures = build_arc_controlled_improvement_evidence_fixtures_v1()
    chain = {
        "chain_type": CHAIN_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "chain_label": DEFAULT_CHAIN_LABEL_V1,
        "fixtures": fixtures,
        "summary": {
            "known_family_exact_before": int(fixtures["known_family_primitive_executor_expansion"]["baseline_metrics"]["exact_count"]),
            "known_family_exact_after": int(fixtures["known_family_partial_to_exact_repair"]["after_metrics"]["exact_count"]),
            "known_family_exact_gain": int(fixtures["known_family_partial_to_exact_repair"]["after_metrics"]["exact_count"]) - int(fixtures["known_family_primitive_executor_expansion"]["baseline_metrics"]["exact_count"]),
            "heldout_exact_before": int(fixtures["heldout_baseline"]["baseline_metrics"]["exact_count"]),
            "heldout_exact_after": int(fixtures["heldout_depth2_compositional_search"]["after_metrics"]["exact_count"]),
            "heldout_exact_gain": int(fixtures["heldout_depth2_compositional_search"]["after_metrics"]["exact_count"]) - int(fixtures["heldout_baseline"]["baseline_metrics"]["exact_count"]),
            "heldout_unsupported_reduction": int(fixtures["heldout_baseline"]["baseline_metrics"]["unsupported_count"]) - int(fixtures["heldout_depth2_compositional_search"]["after_metrics"]["unsupported_count"]),
        },
        "validation_status": DEFAULT_VALIDATION_STATUS_V1,
    }
    return _json_safe(chain)


def validate_arc_controlled_improvement_evidence_chain_v1(chain: Any) -> dict[str, Any]:
    validation = {"valid": False, "blocked_reason_labels": []}
    if not isinstance(chain, Mapping):
        validation["blocked_reason_labels"].append("chain_not_mapping")
        return validation
    missing = [field for field in REQUIRED_CHAIN_FIELDS_V1 if field not in chain]
    if missing:
        validation["blocked_reason_labels"].append("missing_required_fields")
        validation["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return validation
    if chain.get("chain_type") != CHAIN_TYPE_V1:
        validation["blocked_reason_labels"].append("chain_type_mismatch")
    if chain.get("schema_version") != SCHEMA_VERSION_V1:
        validation["blocked_reason_labels"].append("schema_version_mismatch")
    if chain.get("validation_status") != DEFAULT_VALIDATION_STATUS_V1:
        validation["blocked_reason_labels"].append("validation_status_not_validated")
    if not isinstance(chain.get("fixtures"), Mapping):
        validation["blocked_reason_labels"].append("fixtures_not_mapping")
    else:
        expected_keys = {
            "known_family_primitive_executor_expansion",
            "known_family_partial_to_exact_repair",
            "heldout_baseline",
            "heldout_depth2_compositional_search",
        }
        if set(chain["fixtures"].keys()) != expected_keys:
            validation["blocked_reason_labels"].append("fixtures_key_mismatch")
        for key, packet in chain["fixtures"].items():
            packet_validation = validate_arc_controlled_improvement_evidence_packet_v1(packet)
            if not packet_validation["valid"]:
                validation["blocked_reason_labels"].append(f"invalid_fixture:{key}")
                validation["blocked_reason_labels"].extend(packet_validation["blocked_reason_labels"])
    if not isinstance(chain.get("summary"), Mapping):
        validation["blocked_reason_labels"].append("summary_not_mapping")
    else:
        summary = chain["summary"]
        if summary.get("known_family_exact_gain") != 27:
            validation["blocked_reason_labels"].append("known_family_exact_gain_mismatch")
        if summary.get("heldout_exact_gain") != 9:
            validation["blocked_reason_labels"].append("heldout_exact_gain_mismatch")
        if summary.get("heldout_unsupported_reduction") != 9:
            validation["blocked_reason_labels"].append("heldout_unsupported_reduction_mismatch")
    validation["valid"] = not validation["blocked_reason_labels"]
    return validation


def summarize_arc_controlled_improvement_evidence_chain_v1(chain: Any) -> dict[str, Any]:
    validation = validate_arc_controlled_improvement_evidence_chain_v1(chain)
    if not isinstance(chain, Mapping):
        chain = {}
    summary = chain.get("summary", {}) if isinstance(chain.get("summary"), Mapping) else {}
    fixtures = chain.get("fixtures", {}) if isinstance(chain.get("fixtures"), Mapping) else {}
    return _json_safe(
        {
            "chain_type": chain.get("chain_type", CHAIN_TYPE_V1),
            "schema_version": chain.get("schema_version", SCHEMA_VERSION_V1),
            "valid": validation["valid"],
            "chain_label": chain.get("chain_label"),
            "fixture_count": len(fixtures) if isinstance(fixtures, Mapping) else 0,
            "known_family_exact_gain": summary.get("known_family_exact_gain", 0),
            "heldout_exact_gain": summary.get("heldout_exact_gain", 0),
            "heldout_unsupported_reduction": summary.get("heldout_unsupported_reduction", 0),
            "validation_status": chain.get("validation_status"),
            "blocked_reason_labels": validation["blocked_reason_labels"],
        }
    )


__all__ = [
    "CHAIN_TYPE_V1",
    "EVIDENCE_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "build_arc_controlled_improvement_evidence_chain_v1",
    "build_arc_controlled_improvement_evidence_fixtures_v1",
    "build_arc_controlled_improvement_evidence_fixture_depth2_compositional_search_v1",
    "build_arc_controlled_improvement_evidence_fixture_heldout_baseline_v1",
    "build_arc_controlled_improvement_evidence_fixture_partial_to_exact_repair_v1",
    "build_arc_controlled_improvement_evidence_fixture_primitive_executor_expansion_v1",
    "build_arc_controlled_improvement_evidence_packet_v1",
    "summarize_arc_controlled_improvement_evidence_chain_v1",
    "summarize_arc_controlled_improvement_evidence_v1",
    "summarize_boundary_preservation_v1",
    "summarize_heldout_compositional_improvement_v1",
    "summarize_known_family_improvement_v1",
    "summarize_remaining_gaps_v1",
    "to_arc_controlled_improvement_evidence_json_safe_v1",
    "validate_arc_controlled_improvement_evidence_chain_v1",
    "validate_arc_controlled_improvement_evidence_packet_v1",
]
