"""Synthetic ARC official-shape mock runner V1.

Offline readiness run that keeps solver-visible inputs separate from hidden
references, emits exactly-two-output candidate packets per test input, and
scores using exact grid equality only.
"""

from __future__ import annotations

from copy import deepcopy
from statistics import pstdev
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_submission_contract import build_arc_agi2_top2_attempt_packet_v1, validate_arc_agi2_top2_attempt_packet_v1
from weslr.arc_primitive_sequence_grid_reconstruction import apply_primitive_sequence_to_grid_v1
from weslr.arc_style_grid_solver_dry_run import run_arc_style_bounded_solver_dry_run_v1
from weslr.arc_synthetic_official_shape_mock_generator import (
    MOCK_BATCH_COUNT_V1,
    MOCK_BATCH_SEEDS_V1,
    build_arc_synthetic_official_shape_mock_bundle_v1,
    summarize_arc_synthetic_official_shape_mock_bundle_v1,
    validate_arc_synthetic_official_shape_mock_bundle_v1,
)
from weslr.arc_synthetic_official_shape_mock_scorer import (
    score_arc_synthetic_official_shape_mock_top2_packet_v1,
    summarize_arc_synthetic_official_shape_mock_scores_v1,
)

SCHEMA_VERSION_V1 = "ArcSyntheticOfficialShapeMockRunnerV1"


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


def _task_input_grid(task_packet: Mapping[str, Any]) -> list[list[Any]]:
    test_input = task_packet.get("test_input", {})
    if isinstance(test_input, Mapping) and isinstance(test_input.get("cell_values"), list):
        return deepcopy(test_input.get("cell_values", []))
    return deepcopy(test_input) if isinstance(test_input, list) else []


def _copy_baseline_grid(task_packet: Mapping[str, Any]) -> list[list[Any]]:
    return deepcopy(_task_input_grid(task_packet))


def _solver_prediction_grid(task_packet: Mapping[str, Any]) -> dict[str, Any]:
    solver_run = run_arc_style_bounded_solver_dry_run_v1([task_packet])
    task_result = solver_run.get("task_results", [{}])[0] if isinstance(solver_run.get("task_results"), list) else {}
    primitive_sequence = task_result.get("selected_primitive_sequence", []) if isinstance(task_result, Mapping) else []
    reconstruction = apply_primitive_sequence_to_grid_v1(_task_input_grid(task_packet), primitive_sequence)
    if reconstruction.get("reconstruction_success"):
        return {
            "grid": reconstruction.get("reconstructed_grid"),
            "reconstruction_success": True,
            "failure_reason": None,
            "selected_primitive_sequence": _safe(primitive_sequence),
            "solver_run": _safe(task_result),
        }
    return {
        "grid": _task_input_grid(task_packet),
        "reconstruction_success": False,
        "failure_reason": reconstruction.get("failure_reason"),
        "selected_primitive_sequence": _safe(primitive_sequence),
        "solver_run": _safe(task_result),
    }


def _build_candidate_packet(
    *,
    task_id: str,
    test_input_index: int,
    candidate_id: str,
    grid: Any,
    role: str,
    confidence_label: str,
    evidence_labels: Sequence[str],
    batch_seed: int,
    family_id: str,
    variant_index: int,
    primitive_sequence: Sequence[Any] | None = None,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "grid": _safe(grid),
        "source_candidate_id": candidate_id,
        "rank": 1,
        "confidence_label": confidence_label,
        "evidence_labels": list(evidence_labels),
        "leakage_flags": {
            "uses_test_output": False,
            "uses_solution_file": False,
            "uses_answer_key": False,
            "uses_hidden_private_data": False,
            "uses_task_id_shortcut": False,
            "uses_notes_shortcut": False,
            "lookup_table_detected": False,
        },
        "metadata": {
            "candidate_role": role,
            "task_id": task_id,
            "test_input_index": test_input_index,
            "batch_seed": batch_seed,
            "family_id": family_id,
            "variant_index": variant_index,
            "synthetic_only": True,
            "source_kind": "synthetic_official_shape_mock",
            "primitive_sequence": _safe(primitive_sequence or []),
        },
    }


def _count_variance(values: Sequence[int]) -> float:
    if not values:
        return 0.0
    return float(pstdev(values)) if len(values) > 1 else 0.0


def run_arc_synthetic_official_shape_mock_readiness_v1(
    *,
    seeds: Sequence[int] = MOCK_BATCH_SEEDS_V1,
    bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    bundle = build_arc_synthetic_official_shape_mock_bundle_v1(seeds=seeds) if bundle is None else bundle
    bundle_validation = validate_arc_synthetic_official_shape_mock_bundle_v1(bundle)
    summary = summarize_arc_synthetic_official_shape_mock_bundle_v1(bundle)
    batch_results: list[dict[str, Any]] = []
    all_scores: list[dict[str, Any]] = []

    for batch in bundle.get("batches", []) if isinstance(bundle.get("batches"), list) else []:
        batch_index = int(batch.get("batch_index", 0))
        seed = int(batch.get("seed", 0))
        task_results: list[dict[str, Any]] = []
        visible_tasks = batch.get("solver_visible_tasks", []) if isinstance(batch.get("solver_visible_tasks"), list) else []
        references = batch.get("reference_tasks", []) if isinstance(batch.get("reference_tasks"), list) else []
        for task_index, (task_packet, reference) in enumerate(zip(visible_tasks, references)):
            task_id = str(task_packet.get("task_id", ""))
            family_id = str(reference.get("family_id", task_packet.get("trace", {}).get("family_id", "unknown")))
            variant_index = int(reference.get("variant_index", task_packet.get("trace", {}).get("variant_index", 0)))
            solver_prediction = _solver_prediction_grid(task_packet)
            baseline_grid = _copy_baseline_grid(task_packet)
            solver_candidate = _build_candidate_packet(
                task_id=task_id,
                test_input_index=0,
                candidate_id=f"{task_id}:solver:0",
                grid=solver_prediction["grid"],
                role="solver",
                confidence_label="high",
                evidence_labels=("train_fit", "selected_primitive_sequence", "structural_generalization"),
                batch_seed=seed,
                family_id=family_id,
                variant_index=variant_index,
                primitive_sequence=solver_prediction["selected_primitive_sequence"],
            )
            baseline_candidate = _build_candidate_packet(
                task_id=task_id,
                test_input_index=0,
                candidate_id=f"{task_id}:baseline_copy:0",
                grid=baseline_grid,
                role="baseline",
                confidence_label="low",
                evidence_labels=("copy_input",),
                batch_seed=seed,
                family_id=family_id,
                variant_index=variant_index,
            )
            top2_packet = build_arc_agi2_top2_attempt_packet_v1(
                task_id=task_id,
                test_input_index=0,
                candidate_packets=[solver_candidate, baseline_candidate],
                metadata={
                    "schema_version": SCHEMA_VERSION_V1,
                    "batch_index": batch_index,
                    "batch_seed": seed,
                    "family_id": family_id,
                    "variant_index": variant_index,
                    "synthetic_only": True,
                    "official_data_touched": False,
                    "public_data_touched": False,
                    "network_touched": False,
                },
            )
            top2_validation = validate_arc_agi2_top2_attempt_packet_v1(top2_packet)
            scorer_result = score_arc_synthetic_official_shape_mock_top2_packet_v1(
                top2_packet=top2_packet,
                reference_output=reference.get("expected_outputs", [[]])[0] if isinstance(reference.get("expected_outputs"), list) and reference.get("expected_outputs") else [],
            )
            task_result = {
                "task_id": task_id,
                "family_id": family_id,
                "variant_index": variant_index,
                "batch_index": batch_index,
                "batch_seed": seed,
                "task_index": task_index,
                "top2_packet": _safe(top2_packet),
                "top2_validation": _safe(top2_validation),
                "solver_exact": bool(scorer_result.get("solver_exact", False)),
                "baseline_exact": bool(scorer_result.get("baseline_exact", False)),
                "task_score": int(scorer_result.get("task_score", 0)),
                "malformed_count": int(scorer_result.get("malformed_count", 0)),
                "timeout_count": int(scorer_result.get("timeout_count", 0)),
                "error_count": int(scorer_result.get("error_count", 0)),
                "solver_reconstruction_success": bool(solver_prediction["reconstruction_success"]),
                "solver_failure_reason": solver_prediction["failure_reason"],
                "selected_primitive_sequence": _safe(solver_prediction["selected_primitive_sequence"]),
                "reference_shape": _safe(scorer_result.get("reference_shape")),
                "score_audit": {
                    "expected_output_leakage": False,
                    "synthetic_only": True,
                    "official_data_touched": False,
                    "public_data_touched": False,
                    "network_touched": False,
                },
            }
            task_results.append(task_result)
            all_scores.append(task_result)

        batch_summary = summarize_arc_synthetic_official_shape_mock_scores_v1(task_results)
        batch_scores = [int(item["task_score"]) for item in task_results]
        batch_results.append(
            {
                "batch_index": batch_index,
                "seed": seed,
                "task_count": len(task_results),
                "family_ids": list(batch.get("family_ids", [])),
                "task_results": task_results,
                "summary": batch_summary,
                "solver_score": sum(int(item["solver_exact"]) for item in task_results),
                "baseline_score": sum(int(item["baseline_exact"]) for item in task_results),
                "task_score_variance": _count_variance(batch_scores),
                "exact_two_output_compliance": all(item["top2_validation"].get("valid", False) for item in task_results),
                "malformed_count": sum(int(item["malformed_count"]) for item in task_results),
                "timeout_count": sum(int(item["timeout_count"]) for item in task_results),
                "error_count": sum(int(item["error_count"]) for item in task_results),
            }
        )

    overall_summary = summarize_arc_synthetic_official_shape_mock_scores_v1(all_scores)
    batch_scores = [int(batch["summary"]["task_score"]) for batch in batch_results]
    readiness = (
        bundle_validation["valid"]
        and overall_summary["malformed_count"] == 0
        and overall_summary["timeout_count"] == 0
        and overall_summary["error_count"] == 0
        and overall_summary["solver_exact_count"] > overall_summary["baseline_exact_count"]
        and all(batch["exact_two_output_compliance"] for batch in batch_results)
    )
    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "synthetic_only": True,
        "official_data_touched": False,
        "public_data_touched": False,
        "network_touched": False,
        "seeds": [int(seed) for seed in list(seeds)[:MOCK_BATCH_COUNT_V1]],
        "batch_count": len(batch_results),
        "task_count": sum(batch["task_count"] for batch in batch_results),
        "bundle_summary": summary,
        "bundle_validation": bundle_validation,
        "batch_results": batch_results,
        "overall_summary": overall_summary,
        "batch_score_variance": _count_variance(batch_scores),
        "readiness_signal": readiness,
        "readiness_verdict": "mock_ready_for_public_parse_scorer_design" if readiness else "mock_not_ready",
        "audit": {
            "expected_output_leakage": False,
            "synthetic_official_mixing": False,
            "official_data_touched": False,
            "public_data_touched": False,
            "internet_used": False,
            "provider_used": False,
            "retrieval_used": False,
            "tool_calls_used": False,
            "protected_runtime_chat_ui_changed": False,
        },
    }
    return result


def summarize_arc_synthetic_official_shape_mock_readiness_v1(result: Any) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "task_count": 0,
            "batch_count": 0,
            "solver_exact_count": 0,
            "baseline_exact_count": 0,
            "task_score": 0,
            "malformed_count": 0,
            "timeout_count": 0,
            "error_count": 0,
            "batch_score_variance": 0.0,
            "readiness_verdict": "mock_not_ready",
            "blocked_reason_labels": ["result_not_mapping"],
        }
    overall = result.get("overall_summary", {}) if isinstance(result.get("overall_summary"), Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": bool(result.get("readiness_signal", False)),
        "task_count": int(result.get("task_count", 0)),
        "batch_count": int(result.get("batch_count", 0)),
        "solver_exact_count": int(overall.get("solver_exact_count", 0)),
        "baseline_exact_count": int(overall.get("baseline_exact_count", 0)),
        "task_score": int(overall.get("task_score", 0)),
        "malformed_count": int(overall.get("malformed_count", 0)),
        "timeout_count": int(overall.get("timeout_count", 0)),
        "error_count": int(overall.get("error_count", 0)),
        "batch_score_variance": float(result.get("batch_score_variance", 0.0)),
        "seed_list": _safe(result.get("seeds", [])),
        "family_manifest": _safe(result.get("bundle_summary", {}).get("family_manifest", [])),
        "family_scores": _safe(overall.get("family_scores", {})),
        "readiness_verdict": str(result.get("readiness_verdict", "mock_not_ready")),
        "blocked_reason_labels": [] if result.get("readiness_signal", False) else ["readiness_signal_false"],
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "run_arc_synthetic_official_shape_mock_readiness_v1",
    "summarize_arc_synthetic_official_shape_mock_readiness_v1",
]
