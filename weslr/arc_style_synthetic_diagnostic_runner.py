"""WESLR ARC-style synthetic diagnostic runner V1.

Canonical deterministic diagnostic runner for synthetic ARC-style packet
verification. This runner exists to make the synthetic benchmark reproducible
from committed code, not to claim external capability.

Scope boundaries:
- synthetic internal tasks only
- no ARC public/Kaggle/hidden benchmark data
- no provider/model/tool/retrieval/runtime calls
- no candidate_output_surface wiring
- no replay/final-answer behavior
- no benchmark score authority claims
- no `.weslr` operations
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import json
from typing import Any, Mapping, Sequence

from weslr.arc_style_grid_generalization_stress import perturb_arc_style_task_metadata_v1
from weslr.arc_style_grid_schema_helpers import build_arc_style_grid_task_packet_v1
from weslr.arc_style_grid_solver_dry_run import run_arc_style_bounded_solver_dry_run_v1
from weslr.arc_style_synthetic_solver_suite import (
    DEFAULT_DENIED_AUTHORITY_V1,
    FAILURE_CATEGORIES_V1,
    SUPPORTED_SYNTHETIC_FAMILIES_V1,
    _build_packet_result,
    _normalize_leakage_flags,
    _safe_text,
    build_arc_style_synthetic_solver_failure_ledger_v1,
)
from weslr.arc_style_synthetic_task_generators import REQUIRED_FAMILIES_V1, generate_arc_style_synthetic_task_suite_v1

SCHEMA_VERSION_V1 = "ArcStyleSyntheticDiagnosticRunnerV1"
RUNNER_ID_V1 = "arc_style_synthetic_120_diagnostic_runner_v1"
RUNNER_ENTRY_POINT_V1 = "weslr.arc_style_synthetic_diagnostic_runner.run_arc_style_synthetic_120_diagnostic_runner_v1"
CANONICAL_PACKET_COUNT_V1 = 120
OPTIONAL_SHUFFLED_PACKET_COUNT_V1 = 36
CANONICAL_MODE_ORDER_V1 = (
    "full_metadata",
    "toy_task_type_preserved_only",
    "fully_stripped_train_pairs_plus_test_input_only",
)
OPTIONAL_MODE_ORDER_V1 = ("shuffled_renamed",)


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


def to_arc_style_synthetic_diagnostic_runner_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _payload_grid(packet: Mapping[str, Any]) -> list[list[Any]]:
    test_input = packet.get("test_input", {}) if isinstance(packet.get("test_input"), Mapping) else {}
    cell_values = test_input.get("cell_values", []) if isinstance(test_input.get("cell_values"), list) else []
    return [list(row) for row in cell_values]


def _expected_grid(task_family: Mapping[str, Any], test_input_index: int) -> list[list[Any]]:
    validation_metadata = task_family.get("validation_metadata", {}) if isinstance(task_family.get("validation_metadata"), Mapping) else {}
    expected_outputs = validation_metadata.get("expected_outputs", []) if isinstance(validation_metadata.get("expected_outputs"), list) else []
    item = expected_outputs[test_input_index] if test_input_index < len(expected_outputs) and isinstance(expected_outputs[test_input_index], Mapping) else {}
    output_grid = item.get("output_grid", []) if isinstance(item.get("output_grid"), list) else []
    return [list(row) for row in output_grid]


def _input_grid(task_family: Mapping[str, Any], test_input_index: int) -> list[list[Any]]:
    test_inputs = task_family.get("test_inputs", []) if isinstance(task_family.get("test_inputs"), list) else []
    item = test_inputs[test_input_index] if test_input_index < len(test_inputs) and isinstance(test_inputs[test_input_index], Mapping) else {}
    grid = item.get("input_grid", []) if isinstance(item.get("input_grid"), list) else []
    return [list(row) for row in grid]


def _minimal_trace(packet: Mapping[str, Any], *, mode: str, preserve_toy_task_type: bool) -> dict[str, Any]:
    original_trace = packet.get("trace", {}) if isinstance(packet.get("trace"), Mapping) else {}
    trace = {
        "internal_synthetic_only": True,
        "synthetic_diagnostic_runner": True,
        "diagnostic_mode": mode,
    }
    if preserve_toy_task_type:
        toy_task_type = _safe_text(original_trace.get("toy_task_type"))
        if toy_task_type:
            trace["toy_task_type"] = toy_task_type
    return trace


def _rebuild_packet(packet: Mapping[str, Any], *, mode: str, task_id_suffix: str, preserve_toy_task_type: bool) -> dict[str, Any]:
    task_id = f"{_safe_text(packet.get('task_id'))}{task_id_suffix}"
    return build_arc_style_grid_task_packet_v1(
        task_id=task_id,
        task_source=_safe_text(packet.get("task_source")),
        train_pairs=packet.get("train_pairs", []) if isinstance(packet.get("train_pairs"), list) else [],
        test_input=_payload_grid(packet),
        failure_notes=[],
        trace=_minimal_trace(packet, mode=mode, preserve_toy_task_type=preserve_toy_task_type),
    )


def _entry_base(task_family: Mapping[str, Any], *, test_input_index: int) -> dict[str, Any]:
    family_id = _safe_text(task_family.get("family_id"))
    variant_index = int(task_family.get("variant_index", 0))
    task_id = _safe_text(task_family.get("task_id"))
    return {
        "source_task_id": task_id,
        "family_id": family_id,
        "variant_index": variant_index,
        "seed": "n/a",
        "test_input_index": int(test_input_index),
        "expected_grid": _expected_grid(task_family, test_input_index),
        "input_grid": _input_grid(task_family, test_input_index),
    }


def build_arc_style_synthetic_diagnostic_plan_v1() -> dict[str, Any]:
    suite = generate_arc_style_synthetic_task_suite_v1()
    canonical_entries: list[dict[str, Any]] = []
    optional_entries: dict[str, list[dict[str, Any]]] = {name: [] for name in OPTIONAL_MODE_ORDER_V1}

    for task_family in suite.get("tasks", []):
        if not isinstance(task_family, Mapping):
            continue
        packets = task_family.get("generator_metadata", {}).get("arc_style_task_packets", []) if isinstance(task_family.get("generator_metadata"), Mapping) else []
        if not isinstance(packets, list) or not packets:
            continue

        for index, packet in enumerate(packets):
            if not isinstance(packet, Mapping):
                continue
            entry = _entry_base(task_family, test_input_index=index)
            entry.update({
                "diagnostic_mode": "full_metadata",
                "packet": _json_safe(packet),
                "task_id": _safe_text(packet.get("task_id")),
            })
            canonical_entries.append(entry)

        first_packet = packets[0] if isinstance(packets[0], Mapping) else None
        if first_packet is None:
            continue

        preserved_entry = _entry_base(task_family, test_input_index=0)
        preserved_entry.update({
            "diagnostic_mode": "toy_task_type_preserved_only",
            "packet": _rebuild_packet(
                first_packet,
                mode="toy_task_type_preserved_only",
                task_id_suffix="__toy_task_type_preserved_only",
                preserve_toy_task_type=True,
            ),
            "task_id": f"{_safe_text(first_packet.get('task_id'))}__toy_task_type_preserved_only",
        })
        canonical_entries.append(preserved_entry)

        stripped_entry = _entry_base(task_family, test_input_index=0)
        stripped_entry.update({
            "diagnostic_mode": "fully_stripped_train_pairs_plus_test_input_only",
            "packet": _rebuild_packet(
                first_packet,
                mode="fully_stripped_train_pairs_plus_test_input_only",
                task_id_suffix="__fully_stripped",
                preserve_toy_task_type=False,
            ),
            "task_id": f"{_safe_text(first_packet.get('task_id'))}__fully_stripped",
        })
        canonical_entries.append(stripped_entry)

        shuffled_entry = _entry_base(task_family, test_input_index=0)
        shuffled_packet = perturb_arc_style_task_metadata_v1(
            first_packet,
            task_id=f"{_safe_text(first_packet.get('task_id'))}__shuffled",
            notes=[],
            reverse_train_pairs=True,
            reorder_trace_fields=True,
            trace_overrides={
                "diagnostic_mode": "shuffled_renamed",
                "variant_key": f"{_safe_text(first_packet.get('trace', {}).get('variant_key') if isinstance(first_packet.get('trace'), Mapping) else '')}_shuffled",
            },
        )
        shuffled_entry.update({
            "diagnostic_mode": "shuffled_renamed",
            "packet": shuffled_packet,
            "task_id": f"{_safe_text(first_packet.get('task_id'))}__shuffled",
        })
        optional_entries["shuffled_renamed"].append(shuffled_entry)

    if len(canonical_entries) != CANONICAL_PACKET_COUNT_V1:
        raise AssertionError(f"canonical_entries={len(canonical_entries)} expected={CANONICAL_PACKET_COUNT_V1}")
    if len(optional_entries["shuffled_renamed"]) != OPTIONAL_SHUFFLED_PACKET_COUNT_V1:
        raise AssertionError(
            f"optional_entries[shuffled_renamed]={len(optional_entries['shuffled_renamed'])} expected={OPTIONAL_SHUFFLED_PACKET_COUNT_V1}"
        )

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "runner_id": RUNNER_ID_V1,
        "entry_point": RUNNER_ENTRY_POINT_V1,
        "canonical_entries": canonical_entries,
        "optional_entries": optional_entries,
        "required_families": list(REQUIRED_FAMILIES_V1),
    }


def _non_exact_reason(packet_result: Mapping[str, Any], task_result: Mapping[str, Any]) -> str:
    failure_records = packet_result.get("failure_records", []) if isinstance(packet_result.get("failure_records"), list) else []
    if failure_records:
        categories = [_safe_text(item.get("category")) for item in failure_records if _safe_text(item.get("category"))]
        if categories:
            return ",".join(categories)
    failure_notes = task_result.get("failure_notes", []) if isinstance(task_result.get("failure_notes"), list) else []
    if failure_notes:
        return ",".join(_safe_text(item) for item in failure_notes if _safe_text(item))
    return ""


def _mode_summary(entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    packets = [entry.get("packet") for entry in entries if isinstance(entry.get("packet"), Mapping)]
    dry_run = run_arc_style_bounded_solver_dry_run_v1(packets)
    task_results = dry_run.get("task_results", []) if isinstance(dry_run.get("task_results"), list) else []
    failures: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    family_summary: dict[str, dict[str, int]] = defaultdict(lambda: {"exact": 0, "partial": 0, "unsupported": 0, "failed": 0})
    variant_summary: dict[str, dict[str, int]] = defaultdict(lambda: {"exact": 0, "partial": 0, "unsupported": 0, "failed": 0})

    for entry, task_result in zip(entries, task_results):
        packet_result = _build_packet_result(
            task_id=_safe_text(entry.get("task_id")),
            family_id=_safe_text(entry.get("family_id")),
            variant_index=int(entry.get("variant_index", 0)),
            test_input_index=int(entry.get("test_input_index", 0)),
            packet=entry.get("packet", {}),
            task_result=task_result,
            expected_grid=entry.get("expected_grid", []),
            input_grid=entry.get("input_grid", []),
            failures=failures,
        )
        status = _safe_text(packet_result.get("packet_status"))
        family_id = _safe_text(entry.get("family_id"))
        variant_key = f"{family_id}:variant_{int(entry.get('variant_index', 0))}"
        if status not in {"exact", "partial", "unsupported", "failed"}:
            status = "failed"
        family_summary[family_id][status] += 1
        variant_summary[variant_key][status] += 1
        selected_sequence = task_result.get("selected_primitive_sequence", []) if isinstance(task_result.get("selected_primitive_sequence"), list) else []
        inferred_primitive = _safe_text(selected_sequence[0].get("primitive_id")) if selected_sequence and isinstance(selected_sequence[0], Mapping) else ""
        evaluations.append({
            "diagnostic_mode": _safe_text(entry.get("diagnostic_mode")),
            "task_id": _safe_text(entry.get("task_id")),
            "source_task_id": _safe_text(entry.get("source_task_id")),
            "family_id": family_id,
            "variant_index": int(entry.get("variant_index", 0)),
            "seed": _safe_text(entry.get("seed"), "n/a"),
            "test_input_index": int(entry.get("test_input_index", 0)),
            "inferred_primitive": inferred_primitive,
            "selected_candidate_id": _safe_text(task_result.get("selected_candidate_id")),
            "train_fit_status": _safe_text(task_result.get("train_fit_status")),
            "packet_status": status,
            "non_exact_reason": _non_exact_reason(packet_result, task_result),
            "failure_records": _json_safe(packet_result.get("failure_records", [])),
        })

    counts = Counter(item["packet_status"] for item in evaluations)
    count_total = len(evaluations)
    exact = counts.get("exact", 0)
    partial = counts.get("partial", 0)
    unsupported = counts.get("unsupported", 0)
    failed = counts.get("failed", 0)

    return {
        "packet_count": count_total,
        "exact": exact,
        "partial": partial,
        "unsupported": unsupported,
        "failed": failed,
        "exact_pct": (exact / count_total) if count_total else 0.0,
        "family_summary": {key: value for key, value in sorted(family_summary.items())},
        "variant_summary": {key: value for key, value in sorted(variant_summary.items())},
        "evaluations": evaluations,
        "failure_ledger": build_arc_style_synthetic_solver_failure_ledger_v1(failures),
        "dry_run_summary": {
            "selected_exact_match_count": int(dry_run.get("selected_exact_match_count", 0)),
            "selected_partial_match_count": int(dry_run.get("selected_partial_match_count", 0)),
            "selected_unsupported_count": int(dry_run.get("selected_unsupported_count", 0)),
            "trace": _json_safe(dry_run.get("trace", {})),
        },
    }


def run_arc_style_synthetic_120_diagnostic_runner_v1() -> dict[str, Any]:
    plan = build_arc_style_synthetic_diagnostic_plan_v1()
    canonical_entries = plan["canonical_entries"]
    optional_entries = plan["optional_entries"]

    mode_to_entries: dict[str, list[dict[str, Any]]] = {mode: [] for mode in CANONICAL_MODE_ORDER_V1}
    for entry in canonical_entries:
        mode_to_entries[_safe_text(entry.get("diagnostic_mode"))].append(entry)

    canonical_mode_results = {mode: _mode_summary(mode_to_entries[mode]) for mode in CANONICAL_MODE_ORDER_V1}
    optional_mode_results = {mode: _mode_summary(optional_entries[mode]) for mode in OPTIONAL_MODE_ORDER_V1}

    canonical_evaluations: list[dict[str, Any]] = []
    canonical_failures: list[dict[str, Any]] = []
    aggregate_family_summary: dict[str, dict[str, int]] = defaultdict(lambda: {"exact": 0, "partial": 0, "unsupported": 0, "failed": 0})
    for mode in CANONICAL_MODE_ORDER_V1:
        summary = canonical_mode_results[mode]
        canonical_evaluations.extend(summary["evaluations"])
        canonical_failures.extend(summary["failure_ledger"]["entries"])
        for family_id, counts in summary["family_summary"].items():
            for key in ("exact", "partial", "unsupported", "failed"):
                aggregate_family_summary[family_id][key] += int(counts.get(key, 0))

    exact = sum(summary["exact"] for summary in canonical_mode_results.values())
    partial = sum(summary["partial"] for summary in canonical_mode_results.values())
    unsupported = sum(summary["unsupported"] for summary in canonical_mode_results.values())
    failed = sum(summary["failed"] for summary in canonical_mode_results.values())

    dependency = {
        "original_full_metadata_exact": canonical_mode_results["full_metadata"]["exact"],
        "toy_task_type_preserved_only_exact": canonical_mode_results["toy_task_type_preserved_only"]["exact"],
        "fully_stripped_exact": canonical_mode_results["fully_stripped_train_pairs_plus_test_input_only"]["exact"],
        "dependency_still_present": canonical_mode_results["fully_stripped_train_pairs_plus_test_input_only"]["exact"]
        < canonical_mode_results["toy_task_type_preserved_only"]["exact"],
    }

    canonical_trace_flags: dict[str, bool] = {
        "uses_test_output": False,
        "uses_task_id_for_candidate_selection": False,
        "uses_notes_for_candidate_selection": False,
        "lookup_table_detected": False,
    }
    for mode in CANONICAL_MODE_ORDER_V1:
        trace = canonical_mode_results[mode]["dry_run_summary"]["trace"]
        for key in canonical_trace_flags:
            canonical_trace_flags[key] = canonical_trace_flags[key] or bool(trace.get(key, False))

    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "runner_id": RUNNER_ID_V1,
        "entry_point": RUNNER_ENTRY_POINT_V1,
        "deterministic": True,
        "synthetic_internal_result": True,
        "canonical_packet_count": CANONICAL_PACKET_COUNT_V1,
        "canonical_modes": list(CANONICAL_MODE_ORDER_V1),
        "optional_modes": list(OPTIONAL_MODE_ORDER_V1),
        "canonical_exact": exact,
        "canonical_partial": partial,
        "canonical_unsupported": unsupported,
        "canonical_failed": failed,
        "canonical_exact_pct": (exact / CANONICAL_PACKET_COUNT_V1) if CANONICAL_PACKET_COUNT_V1 else 0.0,
        "canonical_family_summary": {key: value for key, value in sorted(aggregate_family_summary.items())},
        "canonical_evaluations": canonical_evaluations,
        "canonical_failure_ledger": build_arc_style_synthetic_solver_failure_ledger_v1(canonical_failures),
        "canonical_mode_results": canonical_mode_results,
        "optional_mode_results": optional_mode_results,
        "required_families": list(REQUIRED_FAMILIES_V1),
        "supported_synthetic_families": list(sorted(SUPPORTED_SYNTHETIC_FAMILIES_V1)),
        "failure_categories": list(FAILURE_CATEGORIES_V1),
        "toy_task_type_dependency": dependency,
        "leakage_flags": _normalize_leakage_flags({}),
        "trace_flags": canonical_trace_flags,
        "denied_authority": list(DEFAULT_DENIED_AUTHORITY_V1),
        "authority_flags": {name: False for name in DEFAULT_DENIED_AUTHORITY_V1},
        "no_score_claim": True,
        "official_score_claim": False,
    }
    return to_arc_style_synthetic_diagnostic_runner_json_safe_v1(result)


def summarize_arc_style_synthetic_120_diagnostic_runner_v1(result: Mapping[str, Any]) -> dict[str, Any]:
    canonical_family_summary = result.get("canonical_family_summary", {}) if isinstance(result, Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "runner_id": _safe_text(result.get("runner_id")) if isinstance(result, Mapping) else "",
        "canonical_packet_count": int(result.get("canonical_packet_count", 0)) if isinstance(result, Mapping) else 0,
        "canonical_exact": int(result.get("canonical_exact", 0)) if isinstance(result, Mapping) else 0,
        "canonical_partial": int(result.get("canonical_partial", 0)) if isinstance(result, Mapping) else 0,
        "canonical_unsupported": int(result.get("canonical_unsupported", 0)) if isinstance(result, Mapping) else 0,
        "canonical_failed": int(result.get("canonical_failed", 0)) if isinstance(result, Mapping) else 0,
        "canonical_exact_pct": float(result.get("canonical_exact_pct", 0.0)) if isinstance(result, Mapping) else 0.0,
        "family_count": len(canonical_family_summary) if isinstance(canonical_family_summary, Mapping) else 0,
        "toy_task_type_dependency": _json_safe(result.get("toy_task_type_dependency", {})) if isinstance(result, Mapping) else {},
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "RUNNER_ID_V1",
    "RUNNER_ENTRY_POINT_V1",
    "CANONICAL_PACKET_COUNT_V1",
    "OPTIONAL_SHUFFLED_PACKET_COUNT_V1",
    "build_arc_style_synthetic_diagnostic_plan_v1",
    "run_arc_style_synthetic_120_diagnostic_runner_v1",
    "summarize_arc_style_synthetic_120_diagnostic_runner_v1",
    "to_arc_style_synthetic_diagnostic_runner_json_safe_v1",
]
