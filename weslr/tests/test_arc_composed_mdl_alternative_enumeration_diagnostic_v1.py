import copy

import pytest

from weslr.arc_composed_mdl_alternative_enumeration_diagnostic import diagnose, diagnose_safe


def test_forbidden_expected_answer_fields_are_rejected():
    candidate = {
        "family": "composed_transform",
        "candidate_mode": "composed_transform_candidate",
        "expected_answer": "forbidden",
    }
    with pytest.raises(ValueError):
        diagnose_safe(candidate)


def test_diagnostic_never_emits_final_answer_fields_and_does_not_mutate_candidate():
    candidate = {
        "family": "composed_transform",
        "candidate_mode": "composed_transform_candidate",
        "components": ["paint", "shift"],
        "component_support": {"paint": True, "shift": True},
        "component_order_forced": True,
        "component_interaction_proven": True,
        "full_ordered_composition_explains_all_train_pairs": True,
        "alternative_orders_viable": False,
        "alternative_orders_rejected_by_train": True,
        "alternative_search_sufficient": True,
    }
    before = copy.deepcopy(candidate)
    result = diagnose(candidate)
    assert candidate == before
    assert "final_answer" not in result
    assert "runtime" not in result


def test_composed_enumerates_alternative_orders_when_components_exist():
    candidate = {
        "family": "composed_transform",
        "candidate_mode": "composed_transform_candidate",
        "components": ["a", "b", "c"],
        "component_support": {"a": True, "b": True, "c": True},
        "component_order_forced": False,
        "component_interaction_proven": True,
        "full_ordered_composition_explains_all_train_pairs": False,
        "alternative_orders_viable": True,
        "alternative_orders_rejected_by_train": False,
        "alternative_search_sufficient": True,
    }
    result = diagnose_safe(candidate)
    assert result["alternatives_enumerated"] is True
    assert any(r["alternative_kind"] == "alternative_component_order" for r in result["alternative_outputs"])
    assert "alternative_identified" in result["classification_labels"]


def test_composed_marks_alternative_not_identified_when_structure_too_thin():
    result = diagnose_safe({
        "family": "composed_transform",
        "candidate_mode": "composed_transform_candidate",
    })
    assert "alternative_not_identified" in result["classification_labels"]
    assert "missing_proof_only" in result["classification_labels"]
    assert "insufficient_alternative_search" in result["classification_labels"]


def test_composed_distinguishes_component_support_only_from_whole_composition_forced():
    result = diagnose_safe({
        "family": "composed_transform",
        "candidate_mode": "composed_transform_candidate",
        "components": ["a", "b"],
        "component_support": {"a": True, "b": True},
        "component_order_forced": False,
        "component_interaction_proven": False,
        "full_ordered_composition_explains_all_train_pairs": False,
        "alternative_search_sufficient": True,
    })
    assert result["whole_claim_support"] is False
    assert "component_support_only" in result["classification_labels"]
    assert "whole_composition_not_train_forced" in result["classification_labels"]


def test_composed_emits_direct_counterexample_found_for_unrejected_viable_alternative():
    result = diagnose_safe({
        "family": "composed_transform",
        "candidate_mode": "composed_transform_candidate",
        "components": ["a", "b"],
        "component_support": {"a": True, "b": True},
        "component_order_forced": False,
        "component_interaction_proven": False,
        "full_ordered_composition_explains_all_train_pairs": False,
        "alternative_orders_viable": True,
        "alternative_orders_rejected_by_train": False,
        "alternative_search_sufficient": True,
    })
    assert "direct_counterexample_found" in result["classification_labels"]
    assert "alternative_order_viable_unrejected" in result["classification_labels"]


def test_composed_emits_missing_proof_only_without_explicit_alternative():
    result = diagnose_safe({
        "family": "composed_transform",
        "candidate_mode": "composed_transform_candidate",
        "components": ["a"],
        "component_support": {"a": True},
        "component_order_forced": False,
        "component_interaction_proven": False,
        "full_ordered_composition_explains_all_train_pairs": False,
        "alternative_search_sufficient": False,
    })
    assert "missing_proof_only" in result["classification_labels"]
    assert "alternative_rejection_missing" in result["classification_labels"]


def test_composed_emits_laundering_type():
    result = diagnose_safe({
        "family": "composed_transform",
        "candidate_mode": "composed_transform_candidate",
        "components": ["a", "b"],
        "component_support": {"a": True, "b": True},
        "full_composition_forced": True,
        "component_order_forced": False,
        "component_interaction_proven": False,
        "full_ordered_composition_explains_all_train_pairs": False,
    })
    assert result["laundering_risk_detected"] is True
    assert result["laundering_type"] == "component_forcedness_laundered_as_composition_forcedness"


def test_mdl_distinguishes_rules_from_train_from_train_forced_uniqueness():
    result = diagnose_safe({
        "family": "explicit_grammar",
        "candidate_mode": "explicit_grammar_candidate",
        "accepted_grammar": "rule_from_train",
        "grammar_explains_all_train_pairs": True,
        "grammar_complexity": "simple",
        "simplicity_primary_evidence": False,
        "negative_evidence_present": True,
        "competing_grammar_search_sufficient": True,
        "competing_grammar_records": [
            {
                "grammar_id": "alt_same_train",
                "grammar_kind": "same_train_different_test_output",
                "fits_train_pairs": True,
                "produces_distinct_output_descriptor": True,
                "explicit_train_rejection_found": True,
            }
        ],
    })
    assert result["whole_claim_support"] is True
    assert "alternative_rejection_proven" in result["classification_labels"]


def test_mdl_emits_simplicity_as_primary_evidence_when_compactness_dominates():
    result = diagnose_safe({
        "family": "explicit_grammar",
        "candidate_mode": "explicit_grammar_candidate",
        "grammar_complexity": "simple",
        "train_pairs_explained": True,
        "competing_grammar_search_sufficient": False,
    })
    assert "simplicity_as_primary_evidence" in result["classification_labels"]


def test_mdl_enumerates_competing_grammar_categories_without_expected_answer_leakage():
    result = diagnose_safe({
        "family": "mdl_trap",
        "candidate_mode": "explicit_grammar_candidate",
        "grammar_complexity": "simple",
        "train_pairs_explained": True,
        "competing_grammars": [
            {"grammar_id": "g1", "grammar_kind": "simpler_grammar", "fits_train_pairs": True},
            {"grammar_id": "g2", "grammar_kind": "more_complex_grammar", "fits_train_pairs": True},
        ],
    })
    kinds = {g["alternative_kind"] for g in result["competing_grammar_outputs"]}
    assert "simpler_grammar" in kinds
    assert "more_complex_grammar" in kinds


def test_mdl_distinguishes_unrejected_rival_output_from_absence_of_rival_enumeration():
    result = diagnose_safe({
        "family": "explicit_grammar",
        "candidate_mode": "explicit_grammar_candidate",
        "grammar_complexity": "simple",
        "train_pairs_explained": True,
        "negative_evidence_present": False,
        "competing_grammar_records": [
            {
                "grammar_id": "rival",
                "grammar_kind": "same_train_different_test_output",
                "fits_train_pairs": True,
                "produces_distinct_output_descriptor": True,
                "explicit_train_rejection_found": False,
            }
        ],
    })
    assert "direct_counterexample_found" in result["classification_labels"]
    assert "competing_output_identified" in result["classification_labels"]


def test_mdl_emits_missing_proof_only_when_no_explicit_grammar_rival_identified():
    result = diagnose_safe({
        "family": "explicit_grammar",
        "candidate_mode": "explicit_grammar_candidate",
        "grammar_complexity": "simple",
        "train_pairs_explained": True,
        "competing_grammar_search_sufficient": False,
    })
    assert "competing_grammar_unenumerated" in result["classification_labels"]
    assert "missing_proof_only" in result["classification_labels"]


def test_mdl_emits_simplicity_laundered_as_train_forcing():
    result = diagnose_safe({
        "family": "explicit_grammar",
        "candidate_mode": "explicit_grammar_candidate",
        "grammar_complexity": "simple",
        "train_pairs_explained": True,
        "grammar_forced_by_train_claimed": True,
        "competing_grammar_search_sufficient": False,
        "negative_evidence_present": False,
    })
    assert result["laundering_risk_detected"] is True
    assert result["laundering_type"] == "simplicity_laundered_as_train_forcing"


def test_unsupported_future_family_fails_closed_without_false_precision():
    result = diagnose_safe({
        "family": "object_correspondence",
        "candidate_mode": "object_graph_candidate",
    })
    assert result["safe_failure_required"] is True
    assert result["classification_labels"] == ["insufficient_alternative_search"]
    assert result["recommended_repair_family"] == "object_correspondence_laundered_as_whole_grid_mapping"
