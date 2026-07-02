"""ARC official-data contamination boundary checker.

Deterministic, metadata-only, and fail-closed.
This module validates proposed ARC evaluation artifacts, runs, and reports
against the official-data contamination boundary before any official-format
adapter, scorer, or local-public run exists.

It does not load official ARC data, run solvers, score outputs, call tools,
call models, call the web, or touch `.weslr` paths.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

SCHEMA_VERSION_V1 = "arc_official_data_contamination_boundary_v1"

DATA_CLASSES_V1 = (
    "synthetic_weslr",
    "public_official_arc",
    "hidden_private_arc",
    "user_provided_example",
    "generated_hard_mode",
    "report_log_metadata",
)

RUN_PHASES_V1 = (
    "phase_0_synthetic_only",
    "phase_1_toy_fixture_adapter",
    "phase_2_public_parse_scorer_validation",
    "phase_3_local_public_run",
    "phase_4_post_run_audit",
    "phase_5_competition_participation_design",
)

_ALLOWED_PUBLIC_OFFICIAL_PHASES_V1 = {
    "phase_2_public_parse_scorer_validation",
    "phase_3_local_public_run",
    "phase_4_post_run_audit",
    "phase_5_competition_participation_design",
}

_FORBIDDEN_LOG_KEYS_V1 = {
    "expected_output",
    "expected_outputs",
    "hidden_answer",
    "hidden_answers",
    "latent_rule",
    "internal_task_language",
    "oracle_metadata",
    "rival_grammars",
    "separating_examples",
    "composition_graph",
    "novelty_marker",
    "nearest_primitive_set",
    "transfer_anchor",
    "insufficiency_reason",
}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return " ".join(str(value).split())


def _nonempty(value: Any) -> bool:
    return bool(_text(value))


def _as_bool(value: Any) -> bool:
    return value is True


def _contains_forbidden_log_key(value: Any, path: str = "") -> list[str]:
    issues: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            nested_path = f"{path}.{key_text}" if path else key_text
            if key_text in _FORBIDDEN_LOG_KEYS_V1:
                issues.append(f"log_leak:{key_text}")
            issues.extend(_contains_forbidden_log_key(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_contains_forbidden_log_key(nested, f"{path}[{index}]"))
    elif isinstance(value, tuple):
        for index, nested in enumerate(value):
            issues.extend(_contains_forbidden_log_key(nested, f"{path}[{index}]"))
    return issues


def classify_data_class(record: Any) -> str:
    data = _as_mapping(record)
    explicit = _text(data.get("data_class"))
    if explicit in DATA_CLASSES_V1:
        return explicit
    if _as_bool(data.get("hidden_private_data_touched")):
        return "hidden_private_arc"
    if _as_bool(data.get("official_data_touched")):
        return "public_official_arc"
    if _text(data.get("source_kind")) == "report_log_metadata":
        return "report_log_metadata"
    if _text(data.get("source_kind")) == "generated_hard_mode":
        return "generated_hard_mode"
    if _text(data.get("source_kind")) == "user_provided_example":
        return "user_provided_example"
    if _text(data.get("source_kind")) == "public_official_arc":
        return "public_official_arc"
    return "synthetic_weslr"


def classify_run_phase(record: Any) -> str:
    data = _as_mapping(record)
    explicit = _text(data.get("run_phase"))
    if explicit in RUN_PHASES_V1:
        return explicit
    if _as_bool(data.get("toy_fixture")):
        return "phase_1_toy_fixture_adapter"
    if _as_bool(data.get("official_run_proof")) and _as_bool(data.get("local_public_run_proof")):
        return "phase_3_local_public_run"
    return "phase_0_synthetic_only"


def validate_official_data_provenance(record: Any) -> dict[str, Any]:
    data = _as_mapping(record)
    provenance = _as_mapping(data.get("dataset_provenance"))
    official_data_touched = _as_bool(data.get("official_data_touched"))
    if not official_data_touched:
        return {
            "official_data_touched": False,
            "provenance_required": False,
            "has_provenance": False,
            "has_version": False,
            "has_checksum": False,
            "valid": True,
        }
    source = _text(provenance.get("source"))
    version = _text(provenance.get("version"))
    checksum = _text(provenance.get("checksum"))
    issues = []
    if not source:
        issues.append("missing_dataset_source")
    if not version:
        issues.append("missing_dataset_version")
    if not checksum:
        issues.append("missing_dataset_checksum")
    if issues:
        raise ValueError(f"Invalid official data provenance: {issues}")
    return {
        "official_data_touched": True,
        "provenance_required": True,
        "has_provenance": True,
        "has_version": True,
        "has_checksum": True,
        "valid": True,
        "dataset_provenance": deepcopy(provenance),
    }


def validate_logging_policy(log_record: Any) -> dict[str, Any]:
    data = _as_mapping(log_record)
    issues = _contains_forbidden_log_key(data)
    if issues:
        raise ValueError(f"Invalid logging policy: {sorted(set(issues))}")
    return {
        "valid": True,
        "has_task_id": _nonempty(data.get("task_id")),
        "has_status": _nonempty(data.get("status")),
        "has_timing": _nonempty(data.get("timing_ms")) or _nonempty(data.get("duration_ms")) or _nonempty(data.get("elapsed_ms")),
        "has_solved_flag": "solved" in data or "solved" in data.get("result", {}),
        "has_score_metadata": _nonempty(data.get("score_metadata")) or _nonempty(data.get("score")),
    }


def validate_result_claim(claim: Any) -> dict[str, Any]:
    data = _as_mapping(claim)
    claim_kind = _text(data.get("claim_kind"))
    evidence_kind = _text(data.get("evidence_kind"))
    official_run_proof = _as_bool(data.get("official_run_proof"))
    local_public_run_proof = _as_bool(data.get("local_public_run_proof"))
    synthetic_score = data.get("synthetic_score")
    official_percentage = data.get("official_percentage")
    official_arc_performance = _as_bool(data.get("official_arc_performance"))
    solver_changed_after_official_run = _as_bool(data.get("solver_changed_after_official_run"))
    iteration_labelled = _as_bool(data.get("iteration_labelled"))

    issues: list[str] = []
    if solver_changed_after_official_run and not iteration_labelled:
        issues.append("solver_changed_after_official_run_unlabelled")
    if claim_kind in {"official_local_percentage", "official_arc_performance"} and not official_run_proof:
        issues.append("missing_official_run_proof")
    if claim_kind == "official_local_percentage" and not local_public_run_proof:
        issues.append("missing_local_public_run_proof")
    if claim_kind == "official_arc_performance" and evidence_kind != "official":
        issues.append("official_performance_requires_official_evidence")
    if official_arc_performance and evidence_kind != "official":
        issues.append("synthetic_or_mixed_claim_presented_as_official_performance")
    if _nonempty(synthetic_score) and official_arc_performance:
        issues.append("synthetic_score_presented_as_official_performance")
    if _nonempty(official_percentage) and not official_run_proof:
        issues.append("official_percentage_without_official_run_proof")
    if claim_kind == "official_local_percentage" and not _nonempty(official_percentage):
        issues.append("missing_official_percentage")
    if evidence_kind == "synthetic" and official_arc_performance:
        issues.append("synthetic_claim_as_official")
    if issues:
        raise ValueError(f"Invalid result claim: {issues}")
    return {
        "valid": True,
        "claim_kind": claim_kind,
        "evidence_kind": evidence_kind,
        "official_run_proof": official_run_proof,
        "local_public_run_proof": local_public_run_proof,
        "official_arc_performance": official_arc_performance,
        "synthetic_score": synthetic_score,
        "official_percentage": official_percentage,
    }


def validate_contamination_boundary_record(record: Any) -> dict[str, Any]:
    data = _as_mapping(record)
    data_class = classify_data_class(data)
    run_phase = classify_run_phase(data)
    official_data_touched = _as_bool(data.get("official_data_touched"))
    hidden_private_data_touched = _as_bool(data.get("hidden_private_data_touched"))
    internet_tool_model_calls_during_solving = _as_bool(data.get("internet_tool_model_calls_during_solving"))
    expected_output_leakage = _as_bool(data.get("expected_output_leakage"))
    internal_task_language_leakage = _as_bool(data.get("internal_task_language_leakage"))
    synthetic_official_score_mixing = _as_bool(data.get("synthetic_official_score_mixing"))

    issues: list[str] = []

    if hidden_private_data_touched or data_class == "hidden_private_arc":
        issues.append("hidden_private_data_rejected")
    if official_data_touched:
        if run_phase not in _ALLOWED_PUBLIC_OFFICIAL_PHASES_V1:
            issues.append("premature_official_data_use")
        validate_official_data_provenance(data)
    if internet_tool_model_calls_during_solving:
        issues.append("internet_tool_model_calls_during_solving")
    if expected_output_leakage:
        issues.append("expected_output_leakage")
    if internal_task_language_leakage:
        issues.append("internal_task_language_leakage")
    if synthetic_official_score_mixing:
        issues.append("synthetic_official_score_mixing")
    if data_class == "synthetic_weslr" and official_data_touched:
        issues.append("synthetic_record_marked_as_official_data")
    if data_class == "report_log_metadata" and expected_output_leakage:
        issues.append("report_log_metadata_contains_answer_leakage")
    if _as_bool(data.get("local_public_percentage_claimed")) and not _as_bool(data.get("official_run_proof")):
        issues.append("local_public_percentage_without_official_run_proof")

    if issues:
        raise ValueError(f"Invalid contamination boundary record: {issues}")

    provenance = validate_official_data_provenance(data)
    summary = summarize_boundary_status(data)
    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "data_class": data_class,
        "run_phase": run_phase,
        "official_data_touched": official_data_touched,
        "hidden_private_data_touched": hidden_private_data_touched,
        "internet_tool_model_calls_during_solving": internet_tool_model_calls_during_solving,
        "expected_output_leakage": expected_output_leakage,
        "internal_task_language_leakage": internal_task_language_leakage,
        "synthetic_official_score_mixing": synthetic_official_score_mixing,
        "official_data_provenance": provenance,
        "summary": summary,
    }


def summarize_boundary_status(record: Any) -> dict[str, Any]:
    data = _as_mapping(record)
    official_run_proof = _as_bool(data.get("official_run_proof"))
    local_public_run_proof = _as_bool(data.get("local_public_run_proof"))
    claimed_percentage = data.get("official_percentage")
    if not official_run_proof:
        claimable_text = "none yet"
        claimable_value = 0
    else:
        claimable_text = _text(claimed_percentage) or "unknown"
        claimable_value = claimed_percentage if claimed_percentage is not None else 0
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "data_class": classify_data_class(data),
        "run_phase": classify_run_phase(data),
        "official_percentage_claimable_text": claimable_text,
        "official_percentage_claimable_value": claimable_value,
        "official_run_proof_present": official_run_proof,
        "local_public_run_proof_present": local_public_run_proof,
        "official_data_touched": _as_bool(data.get("official_data_touched")),
        "hidden_private_data_touched": _as_bool(data.get("hidden_private_data_touched")),
        "synthetic_official_score_mixing": _as_bool(data.get("synthetic_official_score_mixing")),
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "DATA_CLASSES_V1",
    "RUN_PHASES_V1",
    "classify_data_class",
    "classify_run_phase",
    "validate_result_claim",
    "validate_logging_policy",
    "validate_official_data_provenance",
    "validate_contamination_boundary_record",
    "summarize_boundary_status",
]
