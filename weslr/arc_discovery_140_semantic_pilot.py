"""ARC Synthetic Discovery 140 — Semantic Pilot Runner.

Runs the full 140-task semantic pilot:
- BH80 oracle + native oracle for reference output
- BH80 solver dispatch + native solver for promoted native primitives
- Grid equality comparison for semantic_exact
- Scored vs candidate-probe separation
- Anti-cheat controls 1–18

Does NOT:
- Repair failures
- Promote primitives
- Change BH80
- Change solver/oracle/scorer behavior
- Touch runtime/chat/UI/provider paths
- Touch .weslr
"""

from __future__ import annotations

import json
import os
import sys
from typing import List, Tuple

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from weslr.arc_discovery_140_generator import (
    generate_discovery_140_tasks,
    get_scored_tasks,
    get_candidate_probe_tasks,
    get_scoring_summary,
    get_gate_definitions,
    anti_cheat_readiness,
    SCORED,
    CANDIDATE_PROBE,
)
from weslr.arc_bh80_materializer import materialize_scene
from weslr.arc_bh80_oracle import reference_primitive
from weslr.arc_bh80_semantic_scorer import grids_equal
from weslr.arc_synthetic_3_step_real_dispatch import run_primitive as bh80_solver_run
from weslr.native_arc_oracle import run_native_oracle
from weslr.native_arc_solver import run_native_solver


BH80_PRIMITIVES = {
    "count", "count_objects", "count_or_pattern", "crop", "crop_object",
    "extract", "extract_boundary", "extract_changed_region", "extract_object",
    "fill_region", "isolate_largest", "mirror_object", "normalize_position",
    "pattern_output", "place_back", "recolor", "recolor_boundary",
    "remove_noise", "rotate", "transform",
}


# ---------------------------------------------------------------------------
# Combined oracle: BH80 oracle + native oracle for promoted primitives
# ---------------------------------------------------------------------------

def combined_oracle_pipeline(
    primitive_sequence: List[str],
    input_grid: List[List[int]],
) -> Tuple[bool, List[List[int]], List[dict]]:
    grid = [row[:] for row in input_grid]
    orig_h = len(input_grid)
    orig_w = len(input_grid[0]) if input_grid else 0
    traces = []

    for name in primitive_sequence:
        if name in BH80_PRIMITIVES:
            params = {"original_h": orig_h, "original_w": orig_w}
            supported, grid, trace = reference_primitive(name, grid, params)
        else:
            supported, grid, trace = run_native_oracle(name, grid)
        traces.append(trace)
        if not supported:
            return False, grid, traces

    return True, grid, traces


# ---------------------------------------------------------------------------
# Combined solver: BH80 dispatch + native solver for promoted primitives
# ---------------------------------------------------------------------------

def combined_solver_pipeline(
    input_grid: List[List[int]],
    primitive_sequence: List[str],
) -> Tuple[bool, List[List[int]] | None]:
    grid = [row[:] for row in input_grid]
    orig_h = len(input_grid)
    orig_w = len(input_grid[0]) if input_grid else 0

    for name in primitive_sequence:
        params = {"original_h": orig_h, "original_w": orig_w}
        if name in BH80_PRIMITIVES:
            supported, grid, _ = bh80_solver_run(name, grid, params)
        else:
            supported, grid, _ = run_native_solver(name, grid, params)
        if not supported:
            return False, grid

    return True, grid


# ---------------------------------------------------------------------------
# Score a single task
# ---------------------------------------------------------------------------

def score_single_task(task: dict) -> dict:
    task_id = task["task_id"]
    scene_spec = task["scene_spec"]
    prims = task["primitive_sequence"]
    scoring_layer = task.get("scoring_layer", "scored")

    input_grid = materialize_scene(scene_spec, task_id)
    oracle_supported, oracle_grid, oracle_traces = combined_oracle_pipeline(prims, input_grid)
    solver_supported, solver_grid = combined_solver_pipeline(input_grid, prims)

    if not solver_supported:
        result = "unsupported"
    elif solver_grid is None:
        result = "failed"
    elif oracle_supported and grids_equal(solver_grid, oracle_grid):
        result = "semantic_exact"
    else:
        result = "failed"

    structural_pass = solver_supported
    is_default_ones = input_grid == [[1]]

    return {
        "task_id": task_id,
        "scoring_layer": scoring_layer,
        "result": result,
        "structural_pass": structural_pass,
        "solver_supported": solver_supported,
        "oracle_supported": oracle_supported,
        "grids_equal": grids_equal(solver_grid, oracle_grid) if (solver_supported and oracle_supported and solver_grid is not None) else False,
        "is_default_ones": is_default_ones,
        "solver_grid_dims": (len(solver_grid), len(solver_grid[0]) if solver_grid else 0) if solver_grid else (0, 0),
        "oracle_grid_dims": (len(oracle_grid), len(oracle_grid[0]) if oracle_grid else 0) if oracle_grid else (0, 0),
        "primitive_sequence": prims,
        "oracle_traces": oracle_traces,
    }


# ---------------------------------------------------------------------------
# Anti-cheat controls
# ---------------------------------------------------------------------------

def run_anti_cheat_controls(tasks: list[dict], task_results: list[dict]) -> dict:
    base_controls = anti_cheat_readiness(tasks)

    no_default_ones = all(not r["is_default_ones"] for r in task_results)
    candidate_probe_results = [r for r in task_results if r["scoring_layer"] == CANDIDATE_PROBE]
    probe_counted_as_solved = sum(1 for r in candidate_probe_results if r["result"] == "semantic_exact")
    candidate_probe_non_counting = len(candidate_probe_results) == 10 and probe_counted_as_solved == 0

    scored_results = [r for r in task_results if r["scoring_layer"] == SCORED]
    scored_count = len(scored_results)
    scored_outputs = [r["result"] for r in scored_results]

    base_controls.update({
        "no_default_ones": no_default_ones,
        "candidate_probe_non_counting_proof": candidate_probe_non_counting,
        "candidate_probe_counted_as_solved": probe_counted_as_solved,
        "scored_count": scored_count,
        "scored_semantic_exact_count": sum(1 for r in scored_results if r["result"] == "semantic_exact"),
        "all_controls_pass": all(
            base_controls[k] is True
            for k in [
                "no_default_ones",
                "candidate_probe_separation",
                "unpromoted_blocked",
                "all_three_steps",
                "scene_spec_read_audit",
                "structural_pass_separate",
                "unsupported_sentinel_compatible",
                "duplicate_risk_probe_separation",
                "promoted_native_generalization_coverage",
                "cc_divergence_sentinel",
                "native_chain_order_sensitivity",
            ]
        ) and candidate_probe_non_counting,
        "scored_outputs": scored_outputs,
    })
    return base_controls


# ---------------------------------------------------------------------------
# Main pilot run
# ---------------------------------------------------------------------------

def run_140_semantic_pilot() -> dict:
    tasks = generate_discovery_140_tasks()
    assert len(tasks) == 140, f"Expected 140 tasks, got {len(tasks)}"

    summary = get_scoring_summary(tasks)

    task_results = [score_single_task(task) for task in tasks]

    scored_results = [r for r in task_results if r["scoring_layer"] == SCORED]
    probe_results = [r for r in task_results if r["scoring_layer"] == CANDIDATE_PROBE]

    assert len(scored_results) == summary["scored_total"], f"Expected {summary['scored_total']} scored, got {len(scored_results)}"
    assert len(probe_results) == summary["candidate_probe_total"], f"Expected {summary['candidate_probe_total']} probes, got {len(probe_results)}"

    scored_exact = sum(1 for r in scored_results if r["result"] == "semantic_exact")
    scored_failed = sum(1 for r in scored_results if r["result"] == "failed")
    scored_unsupported = sum(1 for r in scored_results if r["result"] == "unsupported")
    scored_structural_pass = sum(1 for r in scored_results if r["structural_pass"])

    bh80_results = [r for r in scored_results if r["task_id"].startswith("BH80_")]
    bh80_exact = sum(1 for r in bh80_results if r["result"] == "semantic_exact")

    previous_117_results = [r for r in scored_results if not r["task_id"].startswith("T140_")]
    previous_117_exact = sum(1 for r in previous_117_results if r["result"] == "semantic_exact")

    new_13_results = [r for r in scored_results if r["task_id"].startswith("T140_") and 121 <= int(r["task_id"].split("_")[1]) <= 133]
    new_13_exact = sum(1 for r in new_13_results if r["result"] == "semantic_exact")

    probe_executed = len(probe_results)
    probe_oracle_solver_agree = sum(1 for r in probe_results if r["oracle_supported"] and r["solver_supported"] and r["grids_equal"])
    probe_counted_as_solved = sum(1 for r in probe_results if r["result"] == "semantic_exact")

    anti_cheat = run_anti_cheat_controls(tasks, task_results)
    anti_cheat["candidate_probe_non_counting_proof"] = probe_counted_as_solved == 0 and probe_executed == 10
    anti_cheat["candidate_probe_counted_as_solved"] = probe_counted_as_solved
    anti_cheat["all_controls_pass"] = all(
        anti_cheat[k] is True
        for k in [
            "no_default_ones",
            "candidate_probe_separation",
            "unpromoted_blocked",
            "all_three_steps",
            "scene_spec_read_audit",
            "structural_pass_separate",
            "unsupported_sentinel_compatible",
            "duplicate_risk_probe_separation",
            "promoted_native_generalization_coverage",
            "cc_divergence_sentinel",
            "native_chain_order_sensitivity",
            "candidate_probe_non_counting_proof",
        ]
    )

    gates = get_gate_definitions()
    semantic_exact_rate = (scored_exact / summary["scored_total"] * 100) if summary["scored_total"] else 0
    bh80_exact_rate = (bh80_exact / 80 * 100) if 80 else 0

    return {
        "summary": summary,
        "scored_aggregate": {
            "scored_total": summary["scored_total"],
            "scored_exact": scored_exact,
            "failed": scored_failed,
            "unsupported": scored_unsupported,
            "structural_pass": scored_structural_pass,
            "semantic_exact_rate": round(semantic_exact_rate, 2),
        },
        "bh80_subset": {
            "total": 80,
            "semantic_exact": bh80_exact,
            "semantic_exact_rate": round(bh80_exact_rate, 2),
        },
        "previous_117_scored_base": {
            "total": 117,
            "semantic_exact": previous_117_exact,
        },
        "new_13_scored_expansion": {
            "total": 13,
            "semantic_exact": new_13_exact,
        },
        "candidate_probe_diagnostics": {
            "candidate_probe_total": len(probe_results),
            "candidate_probe_executed": probe_executed,
            "candidate_probe_oracle_solver_agree": probe_oracle_solver_agree,
            "candidate_probe_counted_as_solved": probe_counted_as_solved,
        },
        "anti_cheat": anti_cheat,
        "gates": gates,
        "gate_results": {
            "scored_clean": scored_exact == 130,
            "scored_preferred": scored_exact >= 122,
            "scored_strong": scored_exact >= 117,
            "scored_minimal": scored_exact >= 111,
            "bh80_clean": bh80_exact == 80,
            "previous_117_scored_base_clean": previous_117_exact == 117,
            "new_13_scored_expansion_clean": new_13_exact == 13,
            "candidate_probe_counted_as_solved_zero": probe_counted_as_solved == 0,
            "future_all_140_clean": scored_exact == 140,
        },
        "task_results": task_results,
    }


if __name__ == "__main__":
    results = run_140_semantic_pilot()

    sa = results["scored_aggregate"]
    bh = results["bh80_subset"]
    prev = results["previous_117_scored_base"]
    new13 = results["new_13_scored_expansion"]
    cpd = results["candidate_probe_diagnostics"]
    ac = results["anti_cheat"]
    gr = results["gate_results"]

    print("Running ARC Synthetic Discovery 140 Semantic Pilot...")
    print()
    print("=" * 60)
    print(f"SCORED AGGREGATE ({sa['scored_total']} tasks)")
    print("=" * 60)
    print(f"  scored_exact:       {sa['scored_exact']}/{sa['scored_total']}")
    print(f"  failed:             {sa['failed']}/{sa['scored_total']}")
    print(f"  unsupported:        {sa['unsupported']}/{sa['scored_total']}")
    print(f"  structural_pass:    {sa['structural_pass']}/{sa['scored_total']}")
    print(f"  semantic_exact_rate: {sa['semantic_exact_rate']}%")
    print()
    print("SUBSET RESULTS")
    print(f"  BH80 subset:             {bh['semantic_exact']}/80 ({bh['semantic_exact_rate']}%)")
    print(f"  previous 117 base:       {prev['semantic_exact']}/117")
    print(f"  new 13 expansion:        {new13['semantic_exact']}/13")
    print()
    print("CANDIDATE PROBE DIAGNOSTICS")
    print(f"  total:                   {cpd['candidate_probe_total']}")
    print(f"  executed:                {cpd['candidate_probe_executed']}")
    print(f"  oracle_solver_agree:     {cpd['candidate_probe_oracle_solver_agree']}")
    print(f"  counted_as_solved:       {cpd['candidate_probe_counted_as_solved']}")
    print()
    print("ANTI-CHEAT CONTROLS")
    for key, value in ac.items():
        if key == "scored_outputs":
            continue
        print(f"  {key}: {value}")
    print()
    print("GATE RESULTS")
    for key, value in gr.items():
        print(f"  {key}: {value}")
    print()
    print("PILOT RUN COMPLETE")
