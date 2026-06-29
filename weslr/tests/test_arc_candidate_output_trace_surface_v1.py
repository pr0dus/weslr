import inspect
import json

import pytest

from weslr.arc_candidate_output_trace_surface import (
    ALLOWED_INCOMPARABLE_REASON_CODES,
    CANDIDATE_OUTPUT_SURFACE_KEYS,
    CANDIDATE_TRACE_SURFACE_KEYS,
    COMPOSED_TRACE_SURFACE_KEYS,
    FORBIDDEN_UPSTREAM_SCORING_FIELDS,
    MDL_TRACE_SURFACE_KEYS,
    build_candidate_output_surface,
    build_candidate_trace_surface,
    build_composed_trace_surface,
    build_mdl_trace_surface,
    build_replay_preserved_surface_bundle,
    compare_normalized_grid_int_matrices,
    derive_candidate_output_comparability,
    derive_unscorable_reason,
    detect_forbidden_upstream_scoring_fields,
    normalize_grid_int_matrix,
    preserve_candidate_output_surface_for_replay,
    strip_forbidden_upstream_scoring_fields,
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

    @pytest.mark.parametrize(
        "bad_normalized_output",
        [
            {"not": "a_grid"},
            "abc",
            7,
            [[1, 2], [3]],
            [[1, "2"]],
            [[True, 0]],
            [],
        ],
    )
    def test_malformed_json_safe_normalized_output_cannot_become_comparable(self, bad_normalized_output):
        surface = build_candidate_output_surface(
            present=True,
            output_type="grid_int_matrix",
            normalized_output=bad_normalized_output,
            raw_output_reference=bad_normalized_output,
            output_provenance="candidate_override",
            serialization_status="json_safe",
            comparable_to_expected=False,
            incomparable_reason_code="none",
        )
        checked = derive_candidate_output_comparability(surface, expected_output_available=True)
        assert checked["comparable_to_expected"] is False
        assert checked["incomparable_reason_code"] == "normalization_failed"

    def test_valid_rectangular_nested_integer_list_remains_comparable(self):
        surface = build_candidate_output_surface(
            present=True,
            output_type="grid_int_matrix",
            normalized_output=[[1, 2], [3, 4]],
            raw_output_reference=[[1, 2], [3, 4]],
            output_provenance="candidate_override",
            serialization_status="json_safe",
            comparable_to_expected=False,
            incomparable_reason_code="none",
        )
        checked = derive_candidate_output_comparability(surface, expected_output_available=True)
        assert checked["comparable_to_expected"] is True
        assert checked["incomparable_reason_code"] == "none"

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
        checked = derive_candidate_output_comparability(surface, expected_output_available=False)
        assert checked["comparable_to_expected"] is False
        assert checked["incomparable_reason_code"] == "expected_output_missing"
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


class TestReplayPreservationHelpers:
    def test_replay_preservation_records_only_allowed_surface_metadata(self):
        bundle = build_replay_preserved_surface_bundle(
            candidate_output_surface={
                "present": True,
                "output_type": "grid_int_matrix",
                "normalized_output": [[1]],
                "raw_output_reference": [[1]],
                "output_provenance": "candidate_override",
                "serialization_status": "json_safe",
                "comparable_to_expected": True,
                "incomparable_reason_code": "none",
                "schema_version": "override_me",
                "expected_output": [[9]],
                "extra_field": "drop_me",
            },
            candidate_trace_surface={
                "construction_mode": "mode_a",
                "construction_trace_complete": True,
                "forced_uniqueness_trace_present": False,
                "train_evidence_grounded": True,
                "missing_required_trace_fields": [],
                "unresolved_rivals": [],
                "candidate_trace_provenance": "generated",
                "candidate_output_surface_present": True,
                "candidate_output_surface_type": "grid_int_matrix",
                "scoring_result": "forbidden",
                "extra": "drop_me",
            },
            composed_trace_surface={
                "ordered_component_list": ["a"],
                "component_execution_order": ["a"],
                "component_records": [{"expected_answer": [[1]], "name": "a"}],
                "intermediate_outputs_after_each_component": [[[1]]],
                "component_support_map": {"a": True},
                "component_only_support": False,
                "whole_composition_support": True,
                "interaction_assumptions": [],
                "alternative_order_surfaces": [],
                "alternative_subset_surfaces": [],
                "partial_transform_surfaces": [],
                "full_composition_alternatives": [],
                "sufficient_for_alternative_enumeration": True,
                "unexpected": True,
            },
            mdl_trace_surface={
                "accepted_grammar_id": "g1",
                "accepted_grammar_record": {"rule": "mirror", "expected_output": [[1]]},
                "grammar_output_surface": {"type": "grid_int_matrix"},
                "grammar_train_support_evidence": ["train_rule"],
                "simplicity_primary_evidence": True,
                "negative_evidence_present": False,
                "competing_grammar_records": [{"deserved_exact_result": True}],
                "train_forced_grammar": False,
                "compact_but_not_forced": True,
                "sufficient_for_competing_grammar_diagnosis": True,
                "unexpected": True,
            },
            expected_output_available=False,
        )
        assert set(bundle["candidate_output_surface"].keys()) == CANDIDATE_OUTPUT_SURFACE_KEYS
        assert set(bundle["candidate_trace_surface"].keys()) == CANDIDATE_TRACE_SURFACE_KEYS
        assert set(bundle["composed_trace_surface"].keys()) == COMPOSED_TRACE_SURFACE_KEYS
        assert set(bundle["mdl_trace_surface"].keys()) == MDL_TRACE_SURFACE_KEYS
        assert detect_forbidden_upstream_scoring_fields(bundle) == []
        assert bundle["candidate_output_surface"]["comparable_to_expected"] is False
        assert bundle["candidate_output_surface"]["incomparable_reason_code"] == "expected_output_missing"

    def test_replay_preservation_preserves_valid_grid_without_scoring(self):
        preserved = preserve_candidate_output_surface_for_replay(
            {
                "present": True,
                "output_type": "grid_int_matrix",
                "normalized_output": [[1, 2], [3, 4]],
                "raw_output_reference": [[1, 2], [3, 4]],
                "output_provenance": "generator_emitted_final_output",
                "serialization_status": "json_safe",
                "comparable_to_expected": False,
                "incomparable_reason_code": "none",
            },
            expected_output_available=True,
        )
        assert preserved["comparable_to_expected"] is True
        assert preserved["incomparable_reason_code"] == "none"
        assert "scoring_result" not in preserved

    def test_replay_preservation_blocks_malformed_json_safe_output_from_becoming_comparable(self):
        preserved = preserve_candidate_output_surface_for_replay(
            {
                "present": True,
                "output_type": "grid_int_matrix",
                "normalized_output": [[True, 0]],
                "raw_output_reference": [[True, 0]],
                "output_provenance": "generator_emitted_final_output",
                "serialization_status": "json_safe",
                "comparable_to_expected": True,
                "incomparable_reason_code": "none",
            },
            expected_output_available=True,
        )
        assert preserved["comparable_to_expected"] is False
        assert preserved["incomparable_reason_code"] == "normalization_failed"

    def test_replay_preservation_does_not_copy_expected_answer_values(self):
        bundle = build_replay_preserved_surface_bundle(
            candidate_output_surface={
                "present": True,
                "output_type": "grid_int_matrix",
                "normalized_output": [[1]],
                "raw_output_reference": {"expected_answer": [[999]], "value": [[1]]},
                "output_provenance": "candidate_override",
                "serialization_status": "json_safe",
                "comparable_to_expected": False,
                "incomparable_reason_code": "none",
            },
            expected_output_available=False,
        )
        assert detect_forbidden_upstream_scoring_fields(bundle) == []
        assert bundle["replay_surface_provenance"]["expected_output_loaded_after_ledger_decision"] is False
        assert bundle["replay_surface_provenance"]["expected_output_load_stage"] == "not_loaded_for_replay_preservation"

    def test_replay_preservation_helpers_do_not_mutate_inputs(self):
        candidate_output_surface = {
            "present": True,
            "output_type": "grid_int_matrix",
            "normalized_output": [[1]],
            "raw_output_reference": {"expected_answer": [[999]], "value": [[1]]},
            "output_provenance": "candidate_override",
            "serialization_status": "json_safe",
            "comparable_to_expected": False,
            "incomparable_reason_code": "none",
        }
        original = json.loads(json.dumps(candidate_output_surface))
        _ = preserve_candidate_output_surface_for_replay(candidate_output_surface, expected_output_available=False)
        assert candidate_output_surface == original


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

    def test_helpers_do_not_import_provider_model_tool_or_retrieval_calls(self):
        source = inspect.getsource(__import__("weslr.arc_candidate_output_trace_surface", fromlist=["*"]))
        assert "openai" not in source
        assert "anthropic" not in source
        assert "searx" not in source
        assert "requests." not in source
        assert "subprocess" not in source

    def test_strip_forbidden_scoring_fields_is_recursive_and_non_mutating(self):
        payload = {
            "keep": {"inner": 1, "expected_output": [[1]]},
            "items": [{"scoring_label": "bad"}, {"ok": True}],
        }
        original = json.loads(json.dumps(payload))
        sanitized = strip_forbidden_upstream_scoring_fields(payload)
        assert payload == original
        assert detect_forbidden_upstream_scoring_fields(sanitized) == []

    def test_allowed_reason_codes_cover_ambiguous_and_missing(self):
        assert "ambiguous_output_surface" in ALLOWED_INCOMPARABLE_REASON_CODES
        assert "candidate_output_missing" in ALLOWED_INCOMPARABLE_REASON_CODES
        assert "expected_output_missing" in ALLOWED_INCOMPARABLE_REASON_CODES
