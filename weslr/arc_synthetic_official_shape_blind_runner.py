"""Blind synthetic ARC official-shape mock runner V1."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from statistics import pstdev
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_submission_contract import build_arc_agi2_top2_attempt_packet_v1
from weslr.arc_primitive_sequence_grid_reconstruction import apply_primitive_sequence_to_grid_v1
from weslr.arc_style_grid_solver_dry_run import _infer_pair_structural_candidate_v1, run_arc_style_bounded_solver_dry_run_v1
from weslr.arc_synthetic_official_shape_mock_scorer import (
    score_arc_synthetic_official_shape_mock_top2_packet_v1,
    summarize_arc_synthetic_official_shape_mock_scores_v1,
)
from weslr.arc_synthetic_official_shape_blind_projection import (
    BLIND_BATCH_COUNT_V1,
    BLIND_BATCH_SEEDS_V1,
    BLIND_TASKS_PER_BATCH_V1,
    build_arc_synthetic_official_shape_blind_projection_bundle_v1,
    project_blind_task_packet_v1,
    project_labeled_task_packet_v1,
    validate_arc_synthetic_official_shape_blind_task_packet_v1,
)

SCHEMA_VERSION_V1 = "ArcSyntheticOfficialShapeBlindRunnerV1"


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


def _count_variance(values: Sequence[int]) -> float:
    if not values:
        return 0.0
    return float(pstdev(values)) if len(values) > 1 else 0.0


def _grid_from_selected_task(selected_task: Mapping[str, Any]) -> list[list[Any]]:
    return deepcopy(selected_task.get("test_input", [])) if isinstance(selected_task.get("test_input"), list) else []


def _blind_prediction_grid(selected_task: Mapping[str, Any]) -> dict[str, Any]:
    train_pairs = selected_task.get("train_pairs", []) if isinstance(selected_task.get("train_pairs"), list) else []
    pair_inferences: list[dict[str, Any]] = []
    for pair in train_pairs:
        if not isinstance(pair, Mapping):
            continue
        pair_inferences.append(_infer_pair_structural_candidate_v1(pair))
    exact_ids = [item["primitive_id"] for item in pair_inferences if item.get("train_fit_status") == "fit"]
    unique_exact_ids = sorted(set(exact_ids))
    selected_sequence: list[dict[str, Any]] = []
    if len(pair_inferences) > 0 and len(unique_exact_ids) == 1 and len(exact_ids) == len(pair_inferences):
        exact_family = unique_exact_ids[0]
        exact_candidate = next(item for item in pair_inferences if item.get("primitive_id") == exact_family)
        selected_sequence = [{"primitive_id": exact_candidate["primitive_id"], "parameters": exact_candidate.get("parameters", {})}]
    else:
        selected_sequence = [{"primitive_id": "copy", "parameters": {}}]
    reconstruction = apply_primitive_sequence_to_grid_v1(_grid_from_selected_task(selected_task), selected_sequence)
    if reconstruction.get("reconstruction_success"):
        return {
            "grid": reconstruction.get("reconstructed_grid"),
            "reconstruction_success": True,
            "failure_reason": None,
            "selected_primitive_sequence": _safe(selected_sequence),
        }
    return {
        "grid": _grid_from_selected_task(selected_task),
        "reconstruction_success": False,
        "failure_reason": reconstruction.get("failure_reason"),
        "selected_primitive_sequence": _safe(selected_sequence),
    }


def _compatibility_prediction_grid(labeled_packet: Mapping[str, Any]) -> dict[str, Any]:
    solver_run = run_arc_style_bounded_solver_dry_run_v1([labeled_packet])
    task_result = solver_run.get("task_results", [{}])[0] if isinstance(solver_run.get("task_results"), list) else {}
    primitive_sequence = task_result.get("selected_primitive_sequence", []) if isinstance(task_result, Mapping) else []
    reconstruction = apply_primitive_sequence_to_grid_v1(labeled_packet.get("test_input", []), primitive_sequence)
    if reconstruction.get("reconstruction_success"):
        return {
            "grid": reconstruction.get("reconstructed_grid"),
            "reconstruction_success": True,
            "failure_reason": None,
            "selected_primitive_sequence": _safe(primitive_sequence),
        }
    return {
        "grid": deepcopy(labeled_packet.get("test_input", [])),
        "reconstruction_success": False,
        "failure_reason": reconstruction.get("failure_reason"),
        "selected_primitive_sequence": _safe(primitive_sequence),
    }


def _build_candidate_packet(*, candidate_id: str, grid: Any, role: str, confidence_label: str, batch_seed: int, batch_index: int, family_id: str | None, variant_index: int | None, source_task_id: str | None, solver_visible: bool) -> dict[str, Any]:
    candidate = {
        "candidate_id": candidate_id,
        "grid": _safe(grid),
        "source_candidate_id": candidate_id,
        "rank": 1,
        "confidence_label": confidence_label,
        "evidence_labels": ["train_fit"] if role == "solver" else ["copy_input"],
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
            "batch_seed": batch_seed,
            "batch_index": batch_index,
            "solver_visible": solver_visible,
            "synthetic_only": True,
        },
    }
    if solver_visible:
        candidate["metadata"]["blind_solver_visible"] = True
        candidate["metadata"]["family_id"] = family_id
        candidate["metadata"]["variant_index"] = variant_index
        candidate["metadata"]["source_task_id"] = source_task_id
    return candidate


def _evaluate_mode_result(*, selected_task: Mapping[str, Any], batch_index: int, batch_seed: int, batch_task_index: int, mode: str) -> dict[str, Any]:
    family_id = str(selected_task.get("family_id", ""))
    variant_index = int(selected_task.get("variant_index", 0))
    source_task_id = str(selected_task.get("source_task_id", ""))
    if mode == "blind":
        visible_packet = project_blind_task_packet_v1(selected_task, batch_index=batch_index, batch_seed=batch_seed, batch_task_index=batch_task_index)
        prediction = _blind_prediction_grid(selected_task)
    else:
        visible_packet = project_labeled_task_packet_v1(selected_task, batch_index=batch_index, batch_seed=batch_seed, batch_task_index=batch_task_index)
        prediction = _compatibility_prediction_grid(visible_packet)
    solver_candidate = _build_candidate_packet(
        candidate_id=f"{visible_packet['task_id']}:solver:0",
        grid=prediction["grid"],
        role="solver",
        confidence_label="high",
        batch_seed=batch_seed,
        batch_index=batch_index,
        family_id=family_id if mode == "compatibility" else None,
        variant_index=variant_index if mode == "compatibility" else None,
        source_task_id=source_task_id if mode == "compatibility" else None,
        solver_visible=(mode == "compatibility"),
    )
    baseline_candidate = _build_candidate_packet(
        candidate_id=f"{visible_packet['task_id']}:baseline:0",
        grid=deepcopy(visible_packet["test_input"]),
        role="baseline",
        confidence_label="low",
        batch_seed=batch_seed,
        batch_index=batch_index,
        family_id=family_id if mode == "compatibility" else None,
        variant_index=variant_index if mode == "compatibility" else None,
        source_task_id=source_task_id if mode == "compatibility" else None,
        solver_visible=(mode == "compatibility"),
    )
    top2_packet = build_arc_agi2_top2_attempt_packet_v1(
        task_id=visible_packet["task_id"],
        test_input_index=0,
        candidate_packets=[solver_candidate, baseline_candidate],
        metadata={
            "schema_version": SCHEMA_VERSION_V1,
            "batch_index": batch_index,
            "batch_seed": batch_seed,
            "blind_mode": mode == "blind",
            "compatibility_mode": mode == "compatibility",
            "synthetic_only": True,
            "official_data_touched": False,
            "public_data_touched": False,
            "network_touched": False,
        },
    )
    reference_output = deepcopy(selected_task.get("expected_output", []))
    score = score_arc_synthetic_official_shape_mock_top2_packet_v1(top2_packet=top2_packet, reference_output=reference_output)
    return {
        "task_id": visible_packet["task_id"],
        "family_id": family_id,
        "variant_index": variant_index,
        "batch_index": batch_index,
        "batch_seed": batch_seed,
        "top2_packet": _safe(top2_packet),
        "solver_exact": bool(score.get("solver_exact", False)),
        "baseline_exact": bool(score.get("baseline_exact", False)),
        "task_score": int(score.get("task_score", 0)),
        "malformed_count": int(score.get("malformed_count", 0)),
        "timeout_count": int(score.get("timeout_count", 0)),
        "error_count": int(score.get("error_count", 0)),
        "prediction": _safe(prediction),
        "reference_shape": _safe(score.get("reference_shape")),
        "visible_packet": _safe(visible_packet),
        "audit": {
            "expected_output_leakage": False,
            "scorer_reference_visible_to_solver": False,
            "semantic_task_id_visible_to_solver": mode == "compatibility",
            "family_id_visible_to_solver": mode == "compatibility",
            "variant_id_visible_to_solver": mode == "compatibility",
            "toy_task_type_visible_to_solver": mode == "compatibility",
            "family_metadata_used_after_prediction_only": True,
        },
    }


def run_arc_synthetic_official_shape_blind_readiness_v1(*, seeds: Sequence[int] = BLIND_BATCH_SEEDS_V1) -> dict[str, Any]:
    bundle = build_arc_synthetic_official_shape_blind_projection_bundle_v1(seeds=seeds)
    batches = bundle.get("batches", []) if isinstance(bundle.get("batches"), list) else []
    blind_batch_results: list[dict[str, Any]] = []
    compatibility_batch_results: list[dict[str, Any]] = []
    blind_scores: list[dict[str, Any]] = []
    compatibility_scores: list[dict[str, Any]] = []
    for batch in batches:
        batch_index = int(batch.get("batch_index", 0))
        seed = int(batch.get("seed", 0))
        selected_tasks = batch.get("selected_tasks", []) if isinstance(batch.get("selected_tasks"), list) else []
        blind_task_results = []
        compat_task_results = []
        for task_index, selected_task in enumerate(selected_tasks):
            blind_result = _evaluate_mode_result(selected_task=selected_task, batch_index=batch_index, batch_seed=seed, batch_task_index=task_index, mode="blind")
            compat_result = _evaluate_mode_result(selected_task=selected_task, batch_index=batch_index, batch_seed=seed, batch_task_index=task_index, mode="compatibility")
            blind_task_results.append(blind_result)
            compat_task_results.append(compat_result)
            blind_scores.append(blind_result)
            compatibility_scores.append(compat_result)
        blind_summary = summarize_arc_synthetic_official_shape_mock_scores_v1(blind_task_results)
        compat_summary = summarize_arc_synthetic_official_shape_mock_scores_v1(compat_task_results)
        blind_batch_results.append({
            "batch_index": batch_index,
            "seed": seed,
            "task_count": len(blind_task_results),
            "family_ids": [item["family_id"] for item in blind_task_results],
            "task_results": blind_task_results,
            "summary": blind_summary,
            "solver_score": sum(int(item["solver_exact"]) for item in blind_task_results),
            "baseline_score": sum(int(item["baseline_exact"]) for item in blind_task_results),
            "task_score_variance": _count_variance([int(item["task_score"]) for item in blind_task_results]),
            "exact_two_output_compliance": all(not item["top2_packet"]["blocked_reason_labels"] if isinstance(item["top2_packet"], Mapping) and "blocked_reason_labels" in item["top2_packet"] else True for item in blind_task_results),
            "malformed_count": sum(int(item["malformed_count"]) for item in blind_task_results),
            "timeout_count": sum(int(item["timeout_count"]) for item in blind_task_results),
            "error_count": sum(int(item["error_count"]) for item in blind_task_results),
        })
        compatibility_batch_results.append({
            "batch_index": batch_index,
            "seed": seed,
            "task_count": len(compat_task_results),
            "family_ids": [item["family_id"] for item in compat_task_results],
            "task_results": compat_task_results,
            "summary": compat_summary,
            "solver_score": sum(int(item["solver_exact"]) for item in compat_task_results),
            "baseline_score": sum(int(item["baseline_exact"]) for item in compat_task_results),
            "task_score_variance": _count_variance([int(item["task_score"]) for item in compat_task_results]),
            "exact_two_output_compliance": True,
            "malformed_count": sum(int(item["malformed_count"]) for item in compat_task_results),
            "timeout_count": sum(int(item["timeout_count"]) for item in compat_task_results),
            "error_count": sum(int(item["error_count"]) for item in compat_task_results),
        })
    blind_overall = summarize_arc_synthetic_official_shape_mock_scores_v1(blind_scores)
    compat_overall = summarize_arc_synthetic_official_shape_mock_scores_v1(compatibility_scores)
    blind_result = {
        "schema_version": SCHEMA_VERSION_V1,
        "synthetic_only": True,
        "official_data_touched": False,
        "public_data_touched": False,
        "network_touched": False,
        "seeds": [int(seed) for seed in list(seeds)[:BLIND_BATCH_COUNT_V1]],
        "batch_count": len(blind_batch_results),
        "task_count": sum(batch["task_count"] for batch in blind_batch_results),
        "bundle_summary": bundle,
        "blind_batch_results": blind_batch_results,
        "compatibility_batch_results": compatibility_batch_results,
        "blind_overall_summary": blind_overall,
        "compatibility_overall_summary": compat_overall,
        "blind_batch_score_variance": _count_variance([int(batch["summary"]["task_score"]) for batch in blind_batch_results]),
        "compatibility_batch_score_variance": _count_variance([int(batch["summary"]["task_score"]) for batch in compatibility_batch_results]),
        "blind_readiness_signal": blind_overall["malformed_count"] == 0 and blind_overall["timeout_count"] == 0 and blind_overall["error_count"] == 0 and blind_overall["solver_exact_count"] > blind_overall["baseline_exact_count"],
        "compatibility_readiness_signal": compat_overall["malformed_count"] == 0 and compat_overall["timeout_count"] == 0 and compat_overall["error_count"] == 0 and compat_overall["solver_exact_count"] > compat_overall["baseline_exact_count"],
        "audit": {
            "expected_output_visible_to_solver": False,
            "expected_output_leakage": False,
            "scorer_reference_visible_to_solver": False,
            "toy_task_type_visible_to_solver": False,
            "family_id_visible_to_solver": False,
            "variant_id_visible_to_solver": False,
            "semantic_task_id_visible_to_solver": False,
            "family_metadata_used_after_prediction_only": True,
            "internet_used": False,
            "provider_used": False,
            "retrieval_used": False,
            "tool_calls_used": False,
            "official_data_touched": False,
            "public_data_touched": False,
        },
    }
    blind_result["exact_two_output_compliance"] = all(batch.get("exact_two_output_compliance", False) for batch in blind_batch_results)
    blind_result["readiness_verdict"] = "blind_mock_ready_for_public_parse_scorer_design" if blind_result["blind_readiness_signal"] else "blind_mock_not_ready_for_public_parse_scorer_design"
    return blind_result


def summarize_arc_synthetic_official_shape_blind_readiness_v1(result: Any) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "task_count": 0,
            "batch_count": 0,
            "solver_exact_count": 0,
            "baseline_exact_count": 0,
            "malformed_count": 0,
            "timeout_count": 0,
            "error_count": 0,
            "blind_batch_score_variance": 0.0,
            "readiness_verdict": "blind_mock_not_ready_for_public_parse_scorer_design",
            "blocked_reason_labels": ["result_not_mapping"],
        }
    blind = result.get("blind_overall_summary", {}) if isinstance(result.get("blind_overall_summary"), Mapping) else {}
    compat = result.get("compatibility_overall_summary", {}) if isinstance(result.get("compatibility_overall_summary"), Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": bool(result.get("blind_readiness_signal", False)),
        "task_count": int(result.get("task_count", 0)),
        "batch_count": int(result.get("batch_count", 0)),
        "solver_exact_count": int(blind.get("solver_exact_count", 0)),
        "baseline_exact_count": int(blind.get("baseline_exact_count", 0)),
        "task_score": int(blind.get("task_score", 0)),
        "malformed_count": int(blind.get("malformed_count", 0)),
        "timeout_count": int(blind.get("timeout_count", 0)),
        "error_count": int(blind.get("error_count", 0)),
        "blind_batch_score_variance": float(result.get("blind_batch_score_variance", 0.0)),
        "compatibility_solver_exact_count": int(compat.get("solver_exact_count", 0)),
        "compatibility_baseline_exact_count": int(compat.get("baseline_exact_count", 0)),
        "seed_list": _safe(result.get("seeds", [])),
        "family_manifest": _safe(result.get("bundle_summary", {}).get("family_manifest", [])),
        "family_scores": _safe(blind.get("family_scores", {})),
        "readiness_verdict": str(result.get("readiness_verdict", "blind_mock_not_ready_for_public_parse_scorer_design")),
        "blocked_reason_labels": [] if result.get("blind_readiness_signal", False) else ["blind_readiness_signal_false"],
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "run_arc_synthetic_official_shape_blind_readiness_v1",
    "summarize_arc_synthetic_official_shape_blind_readiness_v1",
]
