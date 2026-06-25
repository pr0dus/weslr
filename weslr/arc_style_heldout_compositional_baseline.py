"""WESLR ARC-style held-out compositional baseline V1.

Measurement-only baseline for running the current bounded ARC-style solver over
held-out compositional synthetic tasks. This module does not implement program
search, held-out repair, public ARC/Kaggle ingestion, score claims, provider
calls, payment calls, ChatResponder wiring, website/runtime wiring, or
`.weslr` writes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import json
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_top2_attempt_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)
from weslr.arc_style_grid_solver_dry_run import run_arc_style_bounded_solver_dry_run_v1
from weslr.arc_style_heldout_compositional_synthetic_generator import (
    HELDOUT_RECIPE_FAMILIES_V1,
    RECIPE_VARIANTS_PER_FAMILY_V1,
    generate_arc_style_heldout_compositional_suite_v1,
    summarize_arc_style_heldout_compositional_suite_v1,
)
from weslr.arc_style_synthetic_solver_suite import (
    run_arc_style_synthetic_solver_suite_v1,
    summarize_arc_style_synthetic_solver_suite_result_v1,
)

SCHEMA_VERSION_V1 = "ArcStyleHeldoutCompositionalBaselineV1"
BASELINE_TYPE_V1 = "arc_style_heldout_compositional_baseline_v1"
REQUIRED_BASELINE_FIELDS_V1 = (
    "baseline_type",
    "schema_version",
    "heldout_suite_summary",
    "heldout_task_results",
    "task_count",
    "exact_count",
    "partial_count",
    "unsupported_count",
    "failed_count",
    "per_recipe_summary",
    "failure_ledger",
    "top2_packet_count",
    "top2_packet_valid_count",
    "top2_packet_invalid_count",
    "top2_packet_validations",
    "leakage_flags",
    "boundary_flags",
    "solver_visible_expected_outputs_absent",
    "evaluation_outputs_separated",
    "known_family_baseline_summary",
    "no_score_claim",
)
REQUIRED_LEAKAGE_FLAG_NAMES_V1 = (
    "synthetic_only",
    "heldout_compositional",
    "uses_public_arc_data",
    "uses_kaggle_data",
    "uses_solution_file",
    "uses_answer_key",
    "uses_test_output_for_candidate_generation",
    "uses_task_id_shortcut",
    "uses_notes_shortcut",
    "uses_provider_model_api",
)
REQUIRED_BOUNDARY_FLAG_NAMES_V1 = (
    "metadata_only",
    "heldout_compositional",
    "no_public_arc_data",
    "no_kaggle_data",
    "no_solution_file",
    "no_answer_key",
    "no_test_output_access_for_solver",
    "no_task_id_shortcut",
    "no_notes_shortcut",
    "no_provider_model_api",
    "no_chat_responder",
    "no_runtime_wiring",
)


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


def to_arc_style_heldout_compositional_baseline_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _normalize_leakage_flags(value: Any) -> dict[str, bool]:
    mapping = value if isinstance(value, Mapping) else {}
    return {name: bool(mapping.get(name, False)) for name in REQUIRED_LEAKAGE_FLAG_NAMES_V1}


def _normalize_boundary_flags(value: Any) -> dict[str, bool]:
    mapping = value if isinstance(value, Mapping) else {}
    return {name: bool(mapping.get(name, False)) for name in REQUIRED_BOUNDARY_FLAG_NAMES_V1}


def _leakage_flags_are_clean(flags: Mapping[str, Any]) -> bool:
    return bool(flags.get("synthetic_only", False)) and all(
        not bool(flags.get(name, False))
        for name in REQUIRED_LEAKAGE_FLAG_NAMES_V1
        if name != "synthetic_only"
    )


def _boundary_flags_are_clean(flags: Mapping[str, Any]) -> bool:
    return all(bool(flags.get(name, False)) for name in REQUIRED_BOUNDARY_FLAG_NAMES_V1)


def _count_status(task_results: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {"exact": 0, "partial": 0, "unsupported": 0, "failed": 0}
    for task_result in task_results:
        status = _safe_text(task_result.get("train_fit_status"), "failed")
        if status == "fit":
            counts["exact"] += 1
        elif status == "partial_fit":
            counts["partial"] += 1
        elif status == "unsupported":
            counts["unsupported"] += 1
        else:
            counts["failed"] += 1
    return counts


def _build_per_recipe_summary(task_results: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    per_recipe: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "task_count": 0,
        "exact_count": 0,
        "partial_count": 0,
        "unsupported_count": 0,
        "failed_count": 0,
        "train_fit_statuses": [],
        "task_ids": [],
        "top2_packet_valid_count": 0,
        "top2_packet_count": 0,
        "failure_categories": [],
    })
    for task_result in task_results:
        recipe_family_id = _safe_text(task_result.get("recipe_family_id"))
        summary = per_recipe[recipe_family_id]
        summary["task_count"] += 1
        summary["task_ids"].append(_safe_text(task_result.get("task_id")))
        status = _safe_text(task_result.get("train_fit_status"), "failed")
        summary["train_fit_statuses"].append(status)
        if status == "fit":
            summary["exact_count"] += 1
        elif status == "partial_fit":
            summary["partial_count"] += 1
        elif status == "unsupported":
            summary["unsupported_count"] += 1
        else:
            summary["failed_count"] += 1
        top2_validation = task_result.get("top2_packet_validation", {}) if isinstance(task_result.get("top2_packet_validation"), Mapping) else {}
        summary["top2_packet_count"] += 1 if task_result.get("top2_packet") is not None else 0
        summary["top2_packet_valid_count"] += 1 if bool(top2_validation.get("valid", False)) else 0
        for category in task_result.get("failure_notes", []) if isinstance(task_result.get("failure_notes"), list) else []:
            if category not in summary["failure_categories"]:
                summary["failure_categories"].append(_safe_text(category))
    return {key: dict(value) for key, value in sorted(per_recipe.items())}


def run_arc_style_heldout_compositional_baseline_v1(seed: int | None = None) -> dict[str, Any]:
    suite = generate_arc_style_heldout_compositional_suite_v1(seed=seed)
    solver_input_packets = [task["task_packet"] for task in suite["tasks"]]
    solver_result = run_arc_style_bounded_solver_dry_run_v1(solver_input_packets)

    heldout_task_results: list[dict[str, Any]] = []
    top2_packet_validations: list[dict[str, Any]] = []
    top2_packet_count = 0
    top2_packet_valid_count = 0
    top2_packet_invalid_count = 0
    for task, task_result in zip(suite["tasks"], solver_result.get("task_results", [])):
        candidate_packets = task_result.get("candidate_packets", []) if isinstance(task_result.get("candidate_packets"), list) else []
        top2_packet = None
        top2_validation = {
            "valid": False,
            "task_id": _safe_text(task_result.get("task_id")),
            "blocked_reason_labels": ["not_enough_candidates"] if len(candidate_packets) < 2 else [],
        }
        if len(candidate_packets) >= 2:
            task_input_grid = task["task_packet"]["test_input"]["cell_values"]
            candidate_packets_for_top2 = []
            for candidate_packet in candidate_packets[:2]:
                candidate_packet_out = _json_safe(candidate_packet)
                candidate_packet_out["grid"] = _json_safe(task_input_grid)
                candidate_packets_for_top2.append(candidate_packet_out)
            top2_packet = build_arc_agi2_top2_attempt_packet_v1(
                task_id=_safe_text(task_result.get("task_id")),
                test_input_index=0,
                candidate_packets=candidate_packets_for_top2,
                metadata={
                    "baseline_type": BASELINE_TYPE_V1,
                    "heldout_compositional": True,
                    "recipe_family_id": task.get("recipe_family_id"),
                    "recipe_id": task.get("recipe_id"),
                },
            )
            top2_validation = validate_arc_agi2_top2_attempt_packet_v1(top2_packet)
            top2_packet_count += 1
            if top2_validation.get("valid"):
                top2_packet_valid_count += 1
            else:
                top2_packet_invalid_count += 1
        else:
            top2_packet_invalid_count += 1
        top2_packet_validations.append({
            "task_id": _safe_text(task_result.get("task_id")),
            "top2_packet": top2_packet,
            "top2_packet_validation": top2_validation,
        })
        heldout_task_results.append({
            "task_id": _safe_text(task_result.get("task_id")),
            "recipe_id": _safe_text(task.get("recipe_id")),
            "recipe_family_id": _safe_text(task.get("recipe_family_id")),
            "variant_index": int(task.get("variant_index", 0)),
            "train_fit_status": _safe_text(task_result.get("train_fit_status"), "failed"),
            "candidate_count": int(task_result.get("candidate_count", 0)),
            "exact_count": int(task_result.get("exact_match_count", 0)),
            "partial_count": int(task_result.get("partial_match_count", 0)),
            "unsupported_count": int(task_result.get("unsupported_count", 0)),
            "failed_count": 0 if _safe_text(task_result.get("train_fit_status"), "failed") in {"fit", "partial_fit", "unsupported"} else 1,
            "failure_notes": list(task_result.get("failure_notes", [])) if isinstance(task_result.get("failure_notes"), list) else [],
            "task_packet": _json_safe(task.get("task_packet")),
            "evaluation_metadata": _json_safe(task.get("evaluation_metadata", {})),
            "provenance_metadata": _json_safe(task.get("provenance_metadata", {})),
            "leakage_flags": _json_safe(task.get("leakage_flags", {})),
            "boundary_flags": _json_safe(task.get("boundary_flags", {})),
            "top2_packet": top2_packet,
            "top2_packet_validation": top2_validation,
            "solver_visible_expected_outputs_absent": True,
            "evaluation_outputs_separated": True,
        })

    status_counts = _count_status(heldout_task_results)
    known_family_result = run_arc_style_synthetic_solver_suite_v1()
    known_family_summary = summarize_arc_style_synthetic_solver_suite_result_v1(known_family_result)
    result = {
        "baseline_type": BASELINE_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "heldout_suite_summary": summarize_arc_style_heldout_compositional_suite_v1(suite),
        "heldout_task_results": heldout_task_results,
        "task_count": len(heldout_task_results),
        "exact_count": status_counts["exact"],
        "partial_count": status_counts["partial"],
        "unsupported_count": status_counts["unsupported"],
        "failed_count": status_counts["failed"],
        "per_recipe_summary": _build_per_recipe_summary(heldout_task_results),
        "failure_ledger": _json_safe(solver_result.get("failure_ledger", {})),
        "top2_packet_count": top2_packet_count,
        "top2_packet_valid_count": top2_packet_valid_count,
        "top2_packet_invalid_count": top2_packet_invalid_count,
        "top2_packet_validations": top2_packet_validations,
        "leakage_flags": {
            "synthetic_only": True,
            "heldout_compositional": False,
            "uses_public_arc_data": False,
            "uses_kaggle_data": False,
            "uses_solution_file": False,
            "uses_answer_key": False,
            "uses_test_output_for_candidate_generation": False,
            "uses_task_id_shortcut": False,
            "uses_notes_shortcut": False,
            "uses_provider_model_api": False,
        },
        "boundary_flags": {
            "metadata_only": True,
            "heldout_compositional": True,
            "no_public_arc_data": True,
            "no_kaggle_data": True,
            "no_solution_file": True,
            "no_answer_key": True,
            "no_test_output_access_for_solver": True,
            "no_task_id_shortcut": True,
            "no_notes_shortcut": True,
            "no_provider_model_api": True,
            "no_chat_responder": True,
            "no_runtime_wiring": True,
        },
        "solver_visible_expected_outputs_absent": True,
        "evaluation_outputs_separated": True,
        "known_family_baseline_summary": known_family_summary,
        "solver_result": _json_safe(solver_result),
        "heldout_suite": _json_safe(suite),
        "no_score_claim": True,
    }
    return result


def validate_arc_style_heldout_compositional_baseline_result_v1(result: Any) -> dict[str, Any]:
    validation = {"valid": False, "blocked_reason_labels": []}
    if not isinstance(result, Mapping):
        validation["blocked_reason_labels"].append("result_not_mapping")
        return validation
    missing = [field for field in REQUIRED_BASELINE_FIELDS_V1 if field not in result]
    if missing:
        validation["blocked_reason_labels"].append("missing_required_fields")
        validation["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return validation
    if result.get("baseline_type") != BASELINE_TYPE_V1:
        validation["blocked_reason_labels"].append("baseline_type_mismatch")
    if result.get("no_score_claim") is not True:
        validation["blocked_reason_labels"].append("no_score_claim_not_true")
    if not isinstance(result.get("heldout_task_results"), list) or len(result.get("heldout_task_results", [])) != 14:
        validation["blocked_reason_labels"].append("heldout_task_count_invalid")
    if result.get("task_count") != 14:
        validation["blocked_reason_labels"].append("task_count_mismatch")
    if result.get("exact_count", 0) + result.get("partial_count", 0) + result.get("unsupported_count", 0) + result.get("failed_count", 0) != result.get("task_count", 0):
        validation["blocked_reason_labels"].append("count_total_mismatch")
    if result.get("solver_visible_expected_outputs_absent") is not True:
        validation["blocked_reason_labels"].append("solver_visible_expected_outputs_not_absent")
    if result.get("evaluation_outputs_separated") is not True:
        validation["blocked_reason_labels"].append("evaluation_outputs_not_separated")
    if not _leakage_flags_are_clean(_normalize_leakage_flags(result.get("leakage_flags"))):
        validation["blocked_reason_labels"].append("leakage_flags_not_clean")
    if not _boundary_flags_are_clean(_normalize_boundary_flags(result.get("boundary_flags"))):
        validation["blocked_reason_labels"].append("boundary_flags_not_clean")
    if not isinstance(result.get("failure_ledger"), Mapping):
        validation["blocked_reason_labels"].append("failure_ledger_not_mapping")
    if not isinstance(result.get("per_recipe_summary"), Mapping) or set(result.get("per_recipe_summary", {}).keys()) != set(HELDOUT_RECIPE_FAMILIES_V1):
        validation["blocked_reason_labels"].append("per_recipe_summary_incomplete")
    if result.get("top2_packet_count", 0) < 1:
        validation["blocked_reason_labels"].append("top2_packet_count_invalid")
    if result.get("top2_packet_valid_count", 0) > result.get("top2_packet_count", 0):
        validation["blocked_reason_labels"].append("top2_packet_valid_count_invalid")
    validation["valid"] = not validation["blocked_reason_labels"]
    return validation


def summarize_arc_style_heldout_compositional_baseline_result_v1(result: Any) -> dict[str, Any]:
    validation = validate_arc_style_heldout_compositional_baseline_result_v1(result)
    if not isinstance(result, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "baseline_type": BASELINE_TYPE_V1,
            "valid": False,
            "task_count": 0,
            "exact_count": 0,
            "partial_count": 0,
            "unsupported_count": 0,
            "failed_count": 0,
            "top2_packet_count": 0,
            "top2_packet_valid_count": 0,
            "top2_packet_invalid_count": 0,
            "recipe_count": 0,
            "blocked_reason_labels": validation["blocked_reason_labels"],
        }
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "baseline_type": _safe_text(result.get("baseline_type")),
        "valid": validation["valid"],
        "task_count": int(result.get("task_count", 0)),
        "exact_count": int(result.get("exact_count", 0)),
        "partial_count": int(result.get("partial_count", 0)),
        "unsupported_count": int(result.get("unsupported_count", 0)),
        "failed_count": int(result.get("failed_count", 0)),
        "top2_packet_count": int(result.get("top2_packet_count", 0)),
        "top2_packet_valid_count": int(result.get("top2_packet_valid_count", 0)),
        "top2_packet_invalid_count": int(result.get("top2_packet_invalid_count", 0)),
        "recipe_count": len(result.get("per_recipe_summary", {})) if isinstance(result.get("per_recipe_summary"), Mapping) else 0,
        "recipe_families": list(result.get("per_recipe_summary", {}).keys()) if isinstance(result.get("per_recipe_summary"), Mapping) else [],
        "failure_categories": list(result.get("failure_ledger", {}).get("category_counts", {}).keys()) if isinstance(result.get("failure_ledger"), Mapping) else [],
        "solver_visible_expected_outputs_absent": bool(result.get("solver_visible_expected_outputs_absent", False)),
        "evaluation_outputs_separated": bool(result.get("evaluation_outputs_separated", False)),
        "known_family_exact_count": int(result.get("known_family_baseline_summary", {}).get("synthetic_exact_count", 0)) if isinstance(result.get("known_family_baseline_summary"), Mapping) else 0,
        "known_family_partial_count": int(result.get("known_family_baseline_summary", {}).get("synthetic_partial_count", 0)) if isinstance(result.get("known_family_baseline_summary"), Mapping) else 0,
        "known_family_unsupported_count": int(result.get("known_family_baseline_summary", {}).get("synthetic_unsupported_count", 0)) if isinstance(result.get("known_family_baseline_summary"), Mapping) else 0,
        "known_family_failed_count": int(result.get("known_family_baseline_summary", {}).get("synthetic_failed_count", 0)) if isinstance(result.get("known_family_baseline_summary"), Mapping) else 0,
        "blocked_reason_labels": validation["blocked_reason_labels"],
    }


__all__ = [
    "BASELINE_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "run_arc_style_heldout_compositional_baseline_v1",
    "summarize_arc_style_heldout_compositional_baseline_result_v1",
    "to_arc_style_heldout_compositional_baseline_json_safe_v1",
    "validate_arc_style_heldout_compositional_baseline_result_v1",
]
