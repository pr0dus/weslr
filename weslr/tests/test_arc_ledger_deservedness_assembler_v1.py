"""Tests for ARC Ledger Deservedness Assembler."""

from weslr.arc_ledger_deservedness_assembler import (
    ANTILAUNDERING_LAWS,
    FINAL_ANSWER_EMITTED,
    HELPER_OUTPUT_AS_EVIDENCE,
    PUBLIC_CLAIM_ALLOWED,
    build_ledger_deservedness_assembler_input_v1,
    evaluate_ledger_deservedness_v1,
    summarize_ledger_deservedness_v1,
)


def _valid_candidate(**overrides):
    candidate = {
        "candidate_id": "c1",
        "requires_ledger_review": True,
        "treated_as_final_answer": False,
        "generation_status": "generated",
        "unsupported_assumptions": [],
        "unresolved_rivals": [],
        "construction_trace": [
            {
                "step_id": 1,
                "source_train_example_ids": ["train_1"],
                "train_grounded_transformation_rule": "mirror the trained object mapping",
                "forced_constraints_tied_to_train_evidence": ["constraint_1"],
            }
        ],
        "construction_trace_complete": True,
        "construction_trace_source_grounded": True,
        "forced_uniqueness_trace_present": True,
        "rival_elimination_trace_present": False,
        "train_evidence_grounded": True,
        "source_train_example_ids": ["train_1"],
        "train_grounded_transformation_rule": "mirror the trained object mapping",
        "forced_constraints_tied_to_train_evidence": ["constraint_1"],
        "ambiguity_check": "clear",
        "competing_outputs_rejected_reason": "train evidence rejects the competing color swap",
        "uniquely_forced_reason": "all surviving train constraints force this exact output family",
        "helper_output_as_evidence": False,
        "rehearsal_repeat_as_evidence": False,
        "mdl_only_support": False,
        "elegance_only_support": False,
        "hidden_test_output_used": False,
        "public_arc_answer_used": False,
        "scoring_answer_used": False,
        "output_affecting_ambiguity": False,
    }
    candidate.update(overrides)
    return candidate


def _evaluate(candidate, **input_overrides):
    inp = build_ledger_deservedness_assembler_input_v1(
        task_id="task_test",
        candidate_descriptors=[candidate],
        **input_overrides,
    )
    return evaluate_ledger_deservedness_v1(inp)


class TestAssemblerRepair:
    def test_task_level_forced_constraints_alone_cannot_make_candidate_deserved(self):
        result = _evaluate(
            _valid_candidate(
                construction_trace_complete=False,
                construction_trace=[],
                construction_trace_source_grounded=False,
                forced_uniqueness_trace_present=False,
                train_evidence_grounded=False,
            ),
            forced_constraints=["constraint_1"],
            train_evidence_support={"support": True},
        )
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["candidate_deserved_count"] == 0

    def test_candidate_missing_construction_trace_cannot_be_deserved(self):
        result = _evaluate(_valid_candidate(construction_trace=[]))
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["safe_failure_from_incomplete_trace_count"] == 1

    def test_candidate_with_incomplete_construction_trace_cannot_be_deserved(self):
        result = _evaluate(_valid_candidate(construction_trace_complete=False))
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["safe_failure_from_incomplete_trace_count"] == 1

    def test_candidate_missing_requires_ledger_review_cannot_be_deserved(self):
        candidate = _valid_candidate()
        del candidate["requires_ledger_review"]
        result = _evaluate(candidate)
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["ledger_review_required_count"] == 0

    def test_candidate_requires_ledger_review_false_cannot_be_deserved(self):
        result = _evaluate(_valid_candidate(requires_ledger_review=False))
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["ledger_review_required_count"] == 0

    def test_candidate_without_source_grounded_train_evidence_cannot_be_deserved(self):
        result = _evaluate(_valid_candidate(train_evidence_grounded=False))
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["safe_failure_from_insufficient_evidence_count"] == 1

    def test_rival_grammar_candidate_missing_surviving_grammar_cannot_be_deserved(self):
        result = _evaluate(
            _valid_candidate(
                rival_grammar_case=True,
                rival_grammars=["g_a", "g_b"],
                surviving_grammar=None,
                rival_elimination_trace_present=True,
            )
        )
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["safe_failure_from_unresolved_rival_count"] == 1

    def test_rival_grammar_candidate_missing_elimination_trace_cannot_be_deserved(self):
        result = _evaluate(
            _valid_candidate(
                rival_grammar_case=True,
                rival_grammars=["g_a", "g_b"],
                surviving_grammar="g_a",
                rival_elimination_trace_present=False,
            )
        )
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["safe_failure_from_unresolved_rival_count"] == 1

    def test_rival_grammar_candidate_without_uniqueness_proof_cannot_be_deserved(self):
        result = _evaluate(
            _valid_candidate(
                rival_grammar_case=True,
                rival_grammars=["g_a", "g_b"],
                surviving_grammar="g_a",
                surviving_grammar_train_evidence="train example 1 rejects g_b",
                rival_elimination_trace_present=True,
                forced_uniqueness_trace_present=False,
            )
        )
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["candidate_deserved_count"] == 0

    def test_valid_rival_grammar_candidate_with_complete_trace_can_be_deserved(self):
        result = _evaluate(
            _valid_candidate(
                rival_grammar_case=True,
                rival_grammars=["g_a", "g_b"],
                surviving_grammar="g_a",
                surviving_grammar_train_evidence="train example 1 rejects g_b and preserves g_a",
                rival_elimination_trace_present=True,
            )
        )
        assert result["decision"] == "candidate_deserved"
        assert result["metrics"]["candidate_deserved_count"] == 1

    def test_insufficient_evidence_routes_to_safe_failure(self):
        result = _evaluate(_valid_candidate(forced_uniqueness_trace_present=False))
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["safe_failure_from_insufficient_evidence_count"] == 1

    def test_output_affecting_ambiguity_routes_to_safe_failure(self):
        result = _evaluate(_valid_candidate(output_affecting_ambiguity=True))
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["safe_failure_required_count"] == 1

    def test_helper_output_as_evidence_fails_closed(self):
        result = _evaluate(_valid_candidate(helper_output_as_evidence=True))
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["helper_output_as_evidence_blocked_count"] == 1

    def test_expected_or_scoring_answer_in_assembler_input_fails_closed(self):
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[_valid_candidate(synthetic_expected_answer_for_scoring_only=[[1]])],
        )
        result = evaluate_ledger_deservedness_v1(inp)
        assert result["decision"] == "safe_failure_required"

    def test_final_answer_emitted_remains_false(self):
        result = _evaluate(_valid_candidate())
        assert result["final_answer_emitted"] is False
        assert FINAL_ANSWER_EMITTED is False

    def test_public_claim_allowed_remains_false(self):
        result = _evaluate(_valid_candidate())
        assert result["public_claim_allowed"] is False
        assert PUBLIC_CLAIM_ALLOWED is False


class TestSummaryAndMetrics:
    def test_required_metrics_exist(self):
        result = _evaluate(_valid_candidate())
        metrics = result["metrics"]
        required = [
            "ledger_review_required_count",
            "construction_trace_complete_count",
            "forced_uniqueness_trace_present_count",
            "rival_elimination_trace_present_count",
            "train_evidence_grounded_count",
            "safe_failure_from_insufficient_evidence_count",
            "safe_failure_from_incomplete_trace_count",
            "safe_failure_from_unresolved_rival_count",
        ]
        for key in required:
            assert key in metrics

    def test_anti_laundering_boundary_constants_remain_false(self):
        assert HELPER_OUTPUT_AS_EVIDENCE is False
        assert "train_evidence_is_the_only_source_of_deservedness" in ANTILAUNDERING_LAWS

    def test_summary_is_produced(self):
        result = _evaluate(_valid_candidate())
        summary = summarize_ledger_deservedness_v1(result)
        assert "Ledger Deservedness Assembler Summary" in summary["summary"]
