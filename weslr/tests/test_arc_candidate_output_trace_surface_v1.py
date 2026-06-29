import inspect
import json

import pytest

from weslr.arc_candidate_output_trace_surface import (
    ALLOWED_INCOMPARABLE_REASON_CODES,
    FORBIDDEN_UPSTREAM_SCORING_FIELDS,
    build_candidate_output_surface,
    build_candidate_trace_surface,
    build_composed_trace_surface,
    build_mdl_trace_surface,
    compare_normalized_grid_int_matrices,
    derive_candidate_output_comparability,
    derive_unscorable_reason,
    detect_forbidden_upstream_scoring_fields,
    normalize_grid_int_matrix,
    validate_json_safe_candidate_output_surface,
)


class TestCandidateOutputSurface:
    def test_candidate_output_surface_defaults_to_missing_unscorable(self):
        surface = build_candidate_output_surface()
        assert surface["present"] is False
        assert surface["output_type"] == "missing"
        assert surface["incomparable_reason_code"] == "candidate_output_missing"

    def test_grid_int_matrix_normalizes_deterministically(self):
        assert normalize_grid_int_matrix([[1, 2], [3, 4]]) == [[1, 2], [3, 4]]

    def test_non_rectangular_grid_is_rejected(self):
        with pytest.raises(ValueError):
            normalize_grid_int_matrix([[1, 2], [3]])

    def test_non_integer_grid_is_rejected(self):
        with pytest.raises(ValueError):
            normalize_grid_int_matrix([[1, "2"]])

    def test_non_json_safe_output_is_rejected(self):
        surface = build_candidate_output_surface(
            present=True,
            output_type="grid_int_matrix",
            normalized_output=[[1]],
            raw_output_reference={"bad": {1, 2}},
            output_provenance="candidate_override",
            serialization_status="json_safe",
            comparable_to_expected=True,
            incomparable_reason_code="none",
        )
        validated = validate_json_safe_candidate_output_surface(surface)
        assert validated["serialization_status"] == "non_json_safe_rejected"
        assert validated["incomparable_reason_code"] == "non_json_safe_output"

    def test_descriptor_only_output_is_not_comparable(self):
        surface = build_candidate_output_surface(
            present=True,
            output_type="descriptor_only",
            normalized_output={"shape": [2, 2]},
            raw_output_reference={"shape": [2, 2]},
            output_provenance="candidate_override",
            serialization_status="json_safe",
            comparable_to_expected=False,
            incomparable_reason_code="output_type_not_comparable",
        )
        checked = derive_candidate_output_comparability(surface, expected_output_available=True)
        assert checked["comparable_to_expected"] is False
        assert checked["incomparable_reason_code"] == "output_type_not_comparable"

    def test_exact_integer_grid_comparison_works_on_normalized_structures(self):
        assert compare_normalized_grid_int_matrices([[1, 2]], [[1, 2]]) is True
        assert compare_normalized_grid_int_matrices([[1, 2]], [[2, 1]]) is False

    def test_missing_candidate_output_gives_candidate_output_missing(self):
        surface = build_candidate_output_surface()
        assert derive_unscorable_reason(surface, expected_output_available=True) == "candidate_output_missing"

    def test_expected_output_missing_gives_expected_output_missing(self):
        surface = build_candidate_output_surface(
            present=True,
            output_type="grid_int_matrix",
            normalized_output=[[1]],
            raw_output_reference=[[1]],
            output_provenance="candidate_override",
            serialization_status="json_safe",
            comparable_to_expected=False,
            incomparable_reason_code="none",
        )
        assert derive_unscorable_reason(surface, expected_output_available=False) == "expected_output_missing"

    def test_ambiguous_output_gives_ambiguous_output_surface(self):
        surface = build_candidate_output_surface(
            present=True,
            output_type="grid_int_matrix",
            normalized_output=None,
            raw_output_reference={"ambiguous": True},
            output_provenance="candidate_override",
            serialization_status="json_safe",
            comparable_to_expected=False,
            incomparable_reason_code="ambiguous_output_surface",
        )
        assert derive_unscorable_reason(surface, expected_output_available=True) == "ambiguous_output_surface"

    def test_helpers_do_not_mutate_inputs(self):
        surface = build_candidate_output_surface(
            present=True,
            output_type="grid_int_matrix",
            normalized_output=[[1]],
            raw_output_reference=[[1]],
            output_provenance="candidate_override",
            serialization_status="json_safe",
            comparable_to_expected=False,
            incomparable_reason_code="none",
        )
        original = json.loads(json.dumps(surface))
        _ = derive_candidate_output_comparability(surface, expected_output_available=True)
        assert surface == original


class TestTraceSurfaces:
    def test_core_trace_surface_serializes_json_safe(self):
        surface = build_candidate_trace_surface(
            construction_mode="composed_transform_candidate",
            construction_trace_complete=True,
            forced_uniqueness_trace_present=False,
            train_evidence_grounded=True,
            missing_required_trace_fields=["field_a"],
            unresolved_rivals=["r1"],
            candidate_trace_provenance="generated_from_candidate_generation_inputs",
            candidate_output_surface_present=False,
            candidate_output_surface_type="missing",
        )
        json.dumps(surface)
        assert surface["construction_mode"] == "composed_transform_candidate"

    def test_composed_trace_surface_serializes_json_safe(self):
        surface = build_composed_trace_surface(
            ordered_component_list=["a", "b"],
            component_execution_order=["a", "b"],
            component_records=[{"name": "a"}],
            intermediate_outputs_after_each_component=[[[1]]],
            component_support_map={"a": True, "b": False},
            component_only_support=True,
            whole_composition_support=False,
            interaction_assumptions=["ordered"],
            sufficient_for_alternative_enumeration=False,
        )
        json.dumps(surface)
        assert surface["component_only_support"] is True
        assert surface["whole_composition_support"] is False

    def test_mdl_trace_surface_serializes_json_safe(self):
        surface = build_mdl_trace_surface(
            accepted_grammar_id="g1",
            accepted_grammar_record={"rule": "mirror"},
            grammar_output_surface={"type": "grid_int_matrix"},
            grammar_train_support_evidence=["train_rule"],
            simplicity_primary_evidence=True,
            negative_evidence_present=False,
            train_forced_grammar=False,
            compact_but_not_forced=True,
        )
        json.dumps(surface)
        assert surface["simplicity_primary_evidence"] is True
        assert surface["train_forced_grammar"] is False

    def test_composed_trace_helper_records_component_only_vs_whole_support_separately(self):
        surface = build_composed_trace_surface(
            component_only_support=True,
            whole_composition_support=False,
        )
        assert surface["component_only_support"] is True
        assert surface["whole_composition_support"] is False

    def test_mdl_trace_helper_records_simplicity_primary_vs_train_forced_separately(self):
        surface = build_mdl_trace_surface(
            simplicity_primary_evidence=True,
            train_forced_grammar=False,
        )
        assert surface["simplicity_primary_evidence"] is True
        assert surface["train_forced_grammar"] is False


class TestBoundaryLeakageHelpers:
    def test_forbidden_scoring_fields_are_detected_in_upstream_payloads(self):
        payload = {
            "candidate": {
                "expected_answer": [[1]],
                "nested": {"scoring_label": "wrong"},
            }
        }
        found = detect_forbidden_upstream_scoring_fields(payload)
        assert found == ["expected_answer", "scoring_label"]

    def test_forbidden_field_inventory_contains_required_keys(self):
        for key in (
            "synthetic_expected_answer_for_scoring_only",
            "expected_output",
            "expected_answer",
            "post_ledger_scoring_status",
            "post_ledger_scoring_result",
            "deserved_exact_result",
            "deserved_but_wrong_result",
            "scoring_result",
            "scoring_label",
        ):
            assert key in FORBIDDEN_UPSTREAM_SCORING_FIELDS

    def test_helpers_do_not_use_rng_hash_or_random(self):
        source = inspect.getsource(__import__("weslr.arc_candidate_output_trace_surface", fromlist=["*"]))
        assert "random.seed" not in source
        assert "random.random" not in source
        assert "hash(" not in source

    def test_helpers_do_not_import_or_call_replay_runtime_wiring(self):
        source = inspect.getsource(__import__("weslr.arc_candidate_output_trace_surface", fromlist=["*"]))
        assert "arc_generative_bridge_v5_replay" not in source
        assert "ChatResponder" not in source

    def test_allowed_reason_codes_cover_ambiguous_and_missing(self):
        assert "ambiguous_output_surface" in ALLOWED_INCOMPARABLE_REASON_CODES
        assert "candidate_output_missing" in ALLOWED_INCOMPARABLE_REASON_CODES
        assert "expected_output_missing" in ALLOWED_INCOMPARABLE_REASON_CODES
