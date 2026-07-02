"""Tests for the ARC Synthetic TaskContract schema helpers."""

from __future__ import annotations

import json

import pytest

from weslr.arc_discovery_140_generator import generate_discovery_140_tasks, get_scoring_summary
from weslr.arc_discovery_140_hard_mode_calibration import generate_hard_mode_calibration_tasks, get_hard_mode_summary
from weslr.arc_task_contract_schema import (
    SCHEMA_VERSION_V1,
    classify_task_contract_level,
    detect_task_contract_leakage,
    export_solver_visible_task,
    summarize_task_contract_coverage,
    task_contract_can_be_scored,
    validate_task_contract,
)


@pytest.fixture(scope="module")
def contracts():
    def make(level_id: str, scoring_layer: str, **overrides):
        base = {
            "task_id": f"ARC_{level_id}_{scoring_layer}",
            "task_family": f"family_{level_id}",
            "difficulty_level": level_id,
            "scoring_layer": scoring_layer,
            "latent_rule": f"latent rule for {level_id}",
            "visible_examples": [{"input": [1], "output": [2]}],
            "held_out_test_case": {"input": [3]},
            "expected_output": [4],
            "required_abstraction": "rule matching",
            "required_primitives": ["primitive_a"] if level_id == "T1" else None,
            "primitive_chain": ["primitive_a", "primitive_b"] if level_id == "T2" else None,
            "hardness_dimensions": ["shape", "count"],
            "ambiguity_axes": ["position"] if level_id == "T3" else [],
            "rival_grammars": ["grammar_a", "grammar_b"] if level_id == "T3" else [],
            "separating_examples": [{"input": [5], "output": [6]}] if level_id == "T3" else [],
            "composition_graph": {"nodes": 3, "edges": 2} if level_id == "T4" else None,
            "novelty_marker": "novel_scene_form" if level_id == "T4" else None,
            "nearest_primitive_set": ["primitive_a", "primitive_b"] if level_id == "T5" else [],
            "insufficiency_reason": "boundary fusion needs a new primitive" if level_id == "T5" else "",
            "transfer_anchor": "anchor_a" if level_id == "T6" else "",
            "transfer_variants": ["v1", "v2", "v3"] if level_id == "T6" else [],
            "confidence_state": "unresolved" if level_id == "T7" else "confident",
            "confidence_policy": "exact" if level_id in {"T1", "T2"} else "resolve_or_flag",
            "abstain_policy": "abstain_when_insufficient" if level_id == "T7" else "none",
            "expected_failure_mode": "template lock",
            "oracle_metadata": {
                "internal_task_language": {
                    "latent_rule": f"latent rule for {level_id}",
                    "rival_grammars": ["grammar_a", "grammar_b"] if level_id == "T3" else [],
                    "separating_examples": [{"input": [5], "output": [6]}] if level_id == "T3" else [],
                    "ambiguity_axes": ["position"] if level_id == "T3" else [],
                    "composition_graph": {"nodes": 3, "edges": 2} if level_id == "T4" else None,
                    "novelty_marker": "novel_scene_form" if level_id == "T4" else None,
                    "nearest_existing_primitive_set": ["primitive_a", "primitive_b"] if level_id == "T5" else [],
                    "insufficiency_reason": "boundary fusion needs a new primitive" if level_id == "T5" else "",
                    "transfer_family_anchor": "anchor_a" if level_id == "T6" else "",
                    "surface_variant_axes": ["color", "size", "distractor_density"] if level_id == "T6" else [],
                    "confidence_state": "unresolved" if level_id == "T7" else "confident",
                    "unresolved_abstain_policy": "abstain_when_insufficient" if level_id == "T7" else "",
                }
            },
            "solver_visible_view": {
                "task_id": f"ARC_{level_id}_{scoring_layer}",
                "task_family": f"family_{level_id}",
                "visible_examples": [{"input": [1], "output": [2]}],
                "held_out_test_case": {"input": [3]},
                "required_abstraction": "rule matching",
                "hardness_dimensions": ["shape", "count"],
                "can_be_counted_as_solved": True,
            },
            "can_be_counted_as_solved": True,
        }
        base.update(overrides)
        return base

    return {
        "T1": make("T1", "base", confidence_policy="exact", required_primitives=["primitive_a"], can_be_counted_as_solved=True),
        "T2": make("T2", "hard_mode", confidence_policy="exact", primitive_chain=["primitive_a", "primitive_b"], can_be_counted_as_solved=True),
        "T3": make("T3", "diagnostic", can_be_counted_as_solved=False),
        "T4": make("T4", "hard_mode", can_be_counted_as_solved=True),
        "T5": make("T5", "probe", can_be_counted_as_solved=False),
        "T6": make("T6", "sentinel", can_be_counted_as_solved=False),
        "T7": make("T7", "diagnostic", can_be_counted_as_solved=False),
    }


class TestTaskContractSchema:
    def test_valid_t1_through_t7_contracts_pass(self, contracts):
        for level_id, contract in contracts.items():
            validated = validate_task_contract(contract)
            assert validated["difficulty_level"] == level_id
            assert classify_task_contract_level(contract) == level_id
            assert validated["solver_visible_view"] == export_solver_visible_task(contract)

    def test_invalid_t3_t4_t5_t6_t7_contracts_fail(self, contracts):
        bad_t3 = dict(contracts["T3"])
        bad_t3["rival_grammars"] = []
        with pytest.raises(ValueError):
            validate_task_contract(bad_t3)

        bad_t4 = dict(contracts["T4"])
        bad_t4["composition_graph"] = None
        with pytest.raises(ValueError):
            validate_task_contract(bad_t4)

        bad_t5 = dict(contracts["T5"])
        bad_t5["insufficiency_reason"] = ""
        with pytest.raises(ValueError):
            validate_task_contract(bad_t5)

        bad_t6 = dict(contracts["T6"])
        bad_t6["transfer_variants"] = ["v1", "v2"]
        with pytest.raises(ValueError):
            validate_task_contract(bad_t6)

        bad_t7 = dict(contracts["T7"])
        bad_t7["abstain_policy"] = ""
        with pytest.raises(ValueError):
            validate_task_contract(bad_t7)

    def test_t5_cannot_be_counted_as_solved(self, contracts):
        bad = dict(contracts["T5"])
        bad["can_be_counted_as_solved"] = True
        with pytest.raises(ValueError):
            validate_task_contract(bad)
        assert task_contract_can_be_scored(bad) is False

    def test_t7_unresolved_abstain_state_is_valid(self, contracts):
        contract = contracts["T7"]
        validated = validate_task_contract(contract)
        assert validated["confidence_state"] == "unresolved"
        assert validated["abstain_policy"] == "abstain_when_insufficient"

    def test_probe_and_sentinel_cannot_count_as_solved(self, contracts):
        probe = dict(contracts["T5"])
        probe["scoring_layer"] = "probe"
        probe["can_be_counted_as_solved"] = True
        with pytest.raises(ValueError):
            validate_task_contract(probe)
        assert task_contract_can_be_scored(probe) is False

        sentinel = dict(contracts["T6"])
        sentinel["scoring_layer"] = "sentinel"
        sentinel["can_be_counted_as_solved"] = True
        with pytest.raises(ValueError):
            validate_task_contract(sentinel)
        assert task_contract_can_be_scored(sentinel) is False

    def test_solver_visible_export_strips_internal_fields(self, contracts):
        contract = dict(contracts["T3"])
        contract["solver_visible_view"] = {
            "task_id": "ARC_T3_diagnostic",
            "task_family": "family_T3",
            "scoring_layer": "diagnostic",
            "visible_examples": [{"input": [1], "output": [2]}],
            "required_abstraction": "rule matching",
            "hardness_dimensions": ["shape", "count"],
            "difficulty_level": "T3",
            "primitive_name": "select",
            "primitive_names": ["select", "recolor"],
            "primitive_chain": ["select", "recolor"],
            "operation_sequence": ["select", "recolor"],
            "latent_rule": "hidden latent rule",
            "rival_grammars": ["grammar_a"],
            "confidence_policy": "resolve_or_flag",
            "abstain_policy": "abstain_when_insufficient",
            "oracle_metadata": {
                "internal_task_language": {
                    "latent_rule": "hidden latent rule",
                    "rival_grammars": ["grammar_a"],
                    "separating_examples": [{"input": [5], "output": [6]}],
                    "composition_graph": {"nodes": 3},
                    "novelty_marker": "novel_scene_form",
                    "nearest_existing_primitive_set": ["primitive_a"],
                    "insufficiency_reason": "needs a new primitive",
                    "transfer_family_anchor": "anchor_a",
                    "surface_variant_axes": ["color", "size", "shape"],
                    "confidence_state": "unresolved",
                    "unresolved_abstain_policy": "abstain_when_insufficient",
                }
            },
            "expected_output": [4],
            "held_out_test_case": {"input": [3]},
            "confidence_state": "unresolved",
            "insufficiency_reason": "needs a new primitive",
            "nearest_primitive_set": ["primitive_a"],
            "transfer_anchor": "anchor_a",
            "separating_examples": [{"input": [5], "output": [6]}],
            "composition_graph": {"nodes": 3},
            "novelty_marker": "novel_scene_form",
            "internal_task_language": {
                "latent_rule": "hidden latent rule",
            },
        }
        visible = export_solver_visible_task(contract)
        assert set(visible) == {
            "task_id",
            "task_family",
            "scoring_layer",
            "visible_examples",
            "required_abstraction",
            "hardness_dimensions",
        }
        exported = json.dumps(visible, sort_keys=True)
        for forbidden in [
            "difficulty_level",
            "primitive_name",
            "primitive_names",
            "primitive_chain",
            "operation_sequence",
            "latent_rule",
            "rival_grammars",
            "confidence_policy",
            "abstain_policy",
            "oracle_metadata",
            "expected_output",
            "internal_task_language",
            "insufficiency_reason",
            "nearest_primitive_set",
            "transfer_anchor",
            "separating_examples",
            "composition_graph",
            "novelty_marker",
            "hidden latent rule",
            "grammar_a",
            "needs a new primitive",
            "anchor_a",
        ]:
            assert forbidden not in exported

    def test_leakage_detector_catches_internal_leaks(self):
        leaked = {
            "solver_visible_view": {
                "difficulty_level": "T3",
                "level_id": "T3",
                "primitive_name": "select",
                "primitive_names": ["select", "recolor"],
                "primitive_chain": ["select", "recolor"],
                "operation_sequence": ["select", "recolor"],
                "latent_rule": "hidden",
                "rival_grammars": ["grammar_a"],
                "confidence_policy": "resolve_or_flag",
                "insufficiency_reason": "needs a new primitive",
                "expected_output": [1, 2, 3],
                "oracle_metadata": {"secret": True},
            }
        }
        issues = detect_task_contract_leakage(leaked)
        assert "leakage:task_level" in issues
        assert "leakage:primitive_name" in issues
        assert "leakage:operation_sequence" in issues
        assert "leakage:latent_rule" in issues
        assert "leakage:rival_grammars" in issues
        assert "leakage:confidence_policy" in issues
        assert "leakage:insufficiency_reason" in issues
        assert "leakage:expected_output" in issues
        assert "leakage:oracle_metadata" in issues

    def test_coverage_summary_reports_counts_and_enumerations(self, contracts):
        summary = summarize_task_contract_coverage(list(contracts.values()))
        assert summary["schema_version"] == SCHEMA_VERSION_V1
        assert summary["counts_by_level"] == {"T1": 1, "T2": 1, "T3": 1, "T4": 1, "T5": 1, "T6": 1, "T7": 1}
        assert summary["counts_by_scoring_layer"] == {"base": 1, "hard_mode": 2, "probe": 1, "sentinel": 1, "diagnostic": 2}
        assert summary["can_be_counted_as_solved_false_total"] == 4
        assert summary["non_counting_task_ids"] == ["ARC_T3_diagnostic", "ARC_T5_probe", "ARC_T6_sentinel", "ARC_T7_diagnostic"]
        assert summary["probe_task_ids"] == ["ARC_T5_probe"]
        assert summary["sentinel_task_ids"] == ["ARC_T6_sentinel"]
        assert summary["t5_primitive_insufficiency_task_ids"] == ["ARC_T5_probe"]
        assert summary["t7_unresolved_task_ids"] == ["ARC_T7_diagnostic"]

    def test_existing_140_base_untouched(self):
        summary = get_scoring_summary(generate_discovery_140_tasks())
        assert summary == {
            "total_tasks": 140,
            "scored_total": 130,
            "candidate_probe_total": 10,
            "bh80_count": 80,
            "previous_scored_base_total": 117,
            "new_scored_expansion_total": 13,
            "old_probe_total": 3,
            "new_probe_total": 7,
            "color_invert_task_count": 16,
            "candidate_probe_counted_as_solved": 0,
        }

    def test_hard_mode_untouched(self):
        summary = get_hard_mode_summary(generate_hard_mode_calibration_tasks())
        assert summary == {
            "total_tasks": 30,
            "hard_mode_total": 30,
            "hard_mode_scored_total": 30,
            "candidate_probe_total": 0,
            "family_counts": {
                "connected_component_ambiguity": 4,
                "diagonal_adjacency_trap": 1,
                "distractor_density": 3,
                "hole_topology_trap": 3,
                "largest_object_trap": 2,
                "leftmost_topmost_trap": 1,
                "object_ambiguity": 1,
                "order_sensitivity": 1,
                "output_dimension_change": 3,
                "primitive_chain_deception": 3,
                "relation_swap_ambiguity": 1,
                "rival_grammar_ambiguity": 3,
                "same_color_multi_object_trap": 2,
                "symmetry_trap": 2,
            },
            "axis_counts": {
                "object_ambiguity": 2,
                "color_ambiguity": 2,
                "connected_component_ambiguity": 7,
                "distractor_density": 3,
                "symmetry_trap": 2,
                "largest_object_trap": 2,
                "leftmost_topmost_trap": 4,
                "same_color_multi_object_trap": 6,
                "diagonal_adjacency_trap": 3,
                "hole_topology_trap": 6,
                "relation_swap_ambiguity": 3,
                "order_sensitivity": 2,
                "primitive_chain_deception": 4,
                "output_dimension_change": 6,
                "unseen_composition": 3,
                "rival_grammar_ambiguity": 6,
            },
            "hard_mode_denominator": 30,
            "hard_mode_counted_as_solved": 0,
        }
