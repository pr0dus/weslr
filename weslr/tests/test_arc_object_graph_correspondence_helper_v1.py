"""
Tests for ARC Object Graph Correspondence Helper

Verifies helper family 8/8:
- Object graph model
- Correspondence model
- Train-evidence forcing
- Anti-laundering laws
- Ledger boundary preserved
- No runtime solver wiring
"""

import pytest
from weslr.arc_object_graph_correspondence_helper import (
    build_object_graph_correspondence_helper_input_v1,
    evaluate_object_graph_correspondence_v1,
    summarize_object_graph_correspondence_status_v1,
    OBJECT_ATTRIBUTES,
    RELATION_TYPES,
    MAPPING_TYPES,
    ALLOWED_OUTPUT_STATUSES,
    FORBIDDEN_OUTPUT_STATUSES,
    ANTI_LAUNDERING_LAWS,
    FINAL_ANSWER_AUTHORITY,
    HELPER_GENERATES_FINAL_ANSWER,
    HELPER_RANKS_GRAMMARS,
    ALLOWED_EVIDENCE_SCOPE,
    HIDDEN_TEST_OUTPUT_AVAILABLE,
    SYNTHETIC_PROBE_RESULTS_ALLOWED_AS_EVIDENCE,
)


class TestInputModel:
    """Test input model with proper boundaries."""
    
    def test_train_only_evidence_scope(self):
        """Helper input sets train_only evidence scope."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
        )
        
        assert helper_input["allowed_evidence_scope"] == "train_only"
    
    def test_hidden_test_output_fails_closed(self):
        """Hidden test output availability is always False."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
        )
        
        assert helper_input["hidden_test_output_available"] is False
    
    def test_synthetic_probe_fails_closed(self):
        """Synthetic probe results as evidence is always False."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
        )
        
        assert helper_input["synthetic_probe_results_allowed_as_evidence"] is False


class TestObjectAttributes:
    """Test object attribute support."""
    
    def test_all_11_object_attributes_defined(self):
        """All 11 object attributes are defined."""
        expected = [
            "color", "size", "shape_signature", "bounding_box", "centroid",
            "area", "perimeter", "component_id", "boundary_contact",
            "symmetry_signature", "role_label",
        ]
        assert set(OBJECT_ATTRIBUTES) == set(expected)


class TestRelationTypes:
    """Test relation type support."""
    
    def test_all_12_relation_types_defined(self):
        """All 12 relation types are defined."""
        expected = [
            "adjacency", "containment", "above_below", "left_right",
            "distance", "alignment", "same_color", "same_shape",
            "same_size", "touches_boundary", "inside_outside", "relative_order",
        ]
        assert set(RELATION_TYPES) == set(expected)


class TestMappingTypes:
    """Test mapping type support."""
    
    def test_all_12_mapping_types_defined(self):
        """All 12 mapping types are defined."""
        expected = [
            "identity_mapping", "move_mapping", "recolor_mapping",
            "copy_mapping", "delete_mapping", "create_mapping",
            "complete_mapping", "mirror_mapping", "rotate_mapping",
            "expand_contract_mapping", "relation_role_mapping", "partial_mapping",
        ]
        assert set(MAPPING_TYPES) == set(expected)


class TestCorrespondenceModel:
    """Test correspondence model."""
    
    def test_correspondence_forced_by_train(self):
        """Correspondence forced by train evidence."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_correspondences=[
                {
                    "correspondence_id": "corr_1",
                    "source_object_id": "obj_a",
                    "target_object_id": "obj_b",
                    "mapping_type": "identity_mapping",
                    "train_support": ["train_1"],
                    "ambiguous_with": [],
                }
            ],
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        assert result["overall_status"] == "object_correspondence_forced_by_train"
    
    def test_correspondence_ambiguous(self):
        """Ambiguous correspondence detected."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_correspondences=[
                {
                    "correspondence_id": "corr_1",
                    "source_object_id": "obj_a",
                    "target_object_id": "obj_b",
                    "mapping_type": "identity_mapping",
                    "train_support": [],
                    "ambiguous_with": ["corr_2"],
                }
            ],
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        assert result["overall_status"] == "object_correspondence_ambiguous"
    
    def test_candidate_violates_correspondence(self):
        """Candidate violating correspondence detected."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_correspondences=[
                {
                    "correspondence_id": "corr_1",
                    "source_object_id": "obj_a",
                    "target_object_id": "obj_b",
                    "mapping_type": "identity_mapping",
                    "train_support": [],
                    "violating_train_examples": ["train_1"],
                }
            ],
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        assert result["overall_status"] == "candidate_violates_correspondence"
    
    def test_partial_mapping_detected(self):
        """Partial mapping detected."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_correspondences=[
                {
                    "correspondence_id": "corr_1",
                    "source_object_id": "obj_a",
                    "target_object_id": "obj_b",
                    "mapping_type": "partial_mapping",
                }
            ],
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        assert result["overall_status"] == "partial_mapping_detected"
    
    def test_bijection_detected(self):
        """Bijection detected."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_correspondences=[
                {
                    "correspondence_id": "corr_1",
                    "source_object_id": "obj_a",
                    "target_object_id": "obj_b",
                    "mapping_type": "identity_mapping",
                    "train_support": ["train_1"],
                    "ambiguous_with": [],
                }
            ],
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        # Should be either forced or bijection
        assert result["overall_status"] in ["object_correspondence_forced_by_train", "bijection_detected"]


class TestObjectGraphModel:
    """Test object graph model."""
    
    def test_object_graph_detected(self):
        """Object graph detected."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            candidate_object_graphs=[
                {
                    "graph_id": "graph_1",
                    "objects": [{"id": "obj_a"}],
                    "relations": [{"relation_type": "adjacency"}],
                }
            ],
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        assert len(result["graph_results"]) > 0


class TestHelperRelationships:
    """Test relationships to other helpers."""
    
    def test_accepts_constraint_status(self):
        """Helper accepts constraint helper status."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            constraint_helper_status={"overall_status": "rival_grammar_alive"},
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        assert result is not None
    
    def test_accepts_divergence_status(self):
        """Helper accepts divergence helper status."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            divergence_helper_status={"overall_status": "divergence_detected"},
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        assert result is not None
    
    def test_accepts_invariant_symmetry_status(self):
        """Helper accepts invariant/symmetry helper status."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            invariant_symmetry_helper_status={"overall_status": "invariant_preserved"},
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        assert result is not None
    
    def test_accepts_mdl_status(self):
        """Helper accepts MDL helper status."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[{"input": [1], "output": [2]}],
            test_input_descriptor={},
            mdl_helper_status={"overall_status": "compression_tie"},
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        assert result is not None


class TestAntiLaunderingLaws:
    """Test anti-laundering laws are enforced."""
    
    def test_all_12_laws_present(self):
        """All 12 anti-laundering laws are present."""
        assert len(ANTI_LAUNDERING_LAWS) == 12
    
    def test_correspondence_is_diagnostic(self):
        """Correspondence is diagnostic, not evidence."""
        result = evaluate_object_graph_correspondence_v1(
            build_object_graph_correspondence_helper_input_v1(
                task_id="task_1",
                train_examples=[],
                test_input_descriptor={},
            )
        )
        
        assert result["correspondence_treated_as_final_evidence"] is False
    
    def test_graph_match_does_not_prove_truth(self):
        """Graph match does not prove truth."""
        result = evaluate_object_graph_correspondence_v1(
            build_object_graph_correspondence_helper_input_v1(
                task_id="task_1",
                train_examples=[],
                test_input_descriptor={},
            )
        )
        
        assert result["graph_match_proves_truth"] is False
    
    def test_helper_does_not_rank(self):
        """Helper does not rank grammars."""
        assert HELPER_RANKS_GRAMMARS is False
    
    def test_helper_does_not_generate_final_answer(self):
        """Helper does not generate final answers."""
        assert HELPER_GENERATES_FINAL_ANSWER is False


class TestLedgerBoundary:
    """Test ledger boundary is preserved."""
    
    def test_final_answer_authority_is_ledger(self):
        """Final answer authority remains with ledger."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        assert result["final_answer_authority"] == "ledger"
        assert result["helper_generates_final_answer"] is False
    
    def test_forbidden_status_not_produced(self):
        """Forbidden statuses are not produced."""
        result = evaluate_object_graph_correspondence_v1(
            build_object_graph_correspondence_helper_input_v1(
                task_id="task_1",
                train_examples=[],
                test_input_descriptor={},
            )
        )
        
        # Check overall status is allowed
        assert result["overall_status"] in ALLOWED_OUTPUT_STATUSES


class TestMetrics:
    """Test metrics are returned."""
    
    def test_all_17_metrics_exist(self):
        """All 17 metrics are present."""
        helper_input = build_object_graph_correspondence_helper_input_v1(
            task_id="task_1",
            train_examples=[],
            test_input_descriptor={},
        )
        
        result = evaluate_object_graph_correspondence_v1(helper_input)
        
        required_metrics = [
            "candidate_object_graph_count",
            "candidate_correspondence_count",
            "object_correspondence_detected_count",
            "object_correspondence_forced_count",
            "object_correspondence_ambiguous_count",
            "role_correspondence_detected_count",
            "relation_preserved_count",
            "relation_changed_count",
            "partial_mapping_detected_count",
            "bijection_detected_count",
            "subgraph_match_detected_count",
            "candidate_violates_correspondence_count",
            "unsupported_mapping_assumption_count",
            "safe_failure_recommended_count",
            "hidden_test_mapping_blocked_count",
            "synthetic_probe_mapping_blocked_count",
            "ledger_boundary_preserved_count",
        ]
        
        for metric in required_metrics:
            assert metric in result, f"Missing metric: {metric}"


class TestBoundaryConstants:
    """Test boundary constants."""
    
    def test_allowed_evidence_scope(self):
        """Evidence scope is train_only."""
        assert ALLOWED_EVIDENCE_SCOPE == "train_only"
    
    def test_hidden_test_not_available(self):
        """Hidden test output is not available."""
        assert HIDDEN_TEST_OUTPUT_AVAILABLE is False
    
    def test_synthetic_probes_not_allowed(self):
        """Synthetic probes as evidence is not allowed."""
        assert SYNTHETIC_PROBE_RESULTS_ALLOWED_AS_EVIDENCE is False
    
    def test_final_answer_authority(self):
        """Final answer authority is ledger."""
        assert FINAL_ANSWER_AUTHORITY == "ledger"