from weslr.arc_controlled_answer_candidate_generator import (
    build_controlled_answer_candidate_generator_input_v1,
    generate_controlled_answer_candidates_v1,
)
from weslr.arc_ledger_deservedness_assembler import (
    FINAL_ANSWER_EMITTED,
    HELPER_OUTPUT_AS_EVIDENCE,
    PUBLIC_CLAIM_ALLOWED,
    build_ledger_deservedness_assembler_input_v1,
    evaluate_ledger_deservedness_v1,
)


BASE_TRAIN = [{"input": [[1, 2]], "output": [[2, 1]]}]
KNOWN_BAD_ID = "v5_replay_v4_rival_grammar_replay_6_01"


def _valid_candidate(**overrides):
    candidate = {
        "candidate_id": "cand_1",
        "task_id": "task_test",
        "construction_mode": "train_forced_transformation_candidate",
        "construction_trace": [
            {
                "step_id": 1,
                "source_helper": "helper",
                "source_constraint": "train_forced_transformation",
                "operation": "mirror_fill",
                "train_support": True,
                "assumption_status": "forced",
                "rival_impact": "none",
                "ledger_relevance": "required",
                "evidence_status": "train_explicit",
                "source_train_ids": ["train_1"],
                "train_grounded_transformation_rule": "mirror the train-supported relation",
                "train_grounded_forced_constraints": ["constraint_1"],
                "forced_constraints_tied_to_train_evidence": ["constraint_1"],
                "ambiguity_check": "clear",
                "competing_output_rejection_reason": "train evidence rejects the competing color swap",
                "uniquely_forced_reason": "all surviving train constraints force this exact output family",
            }
        ],
        "requires_ledger_review": True,
        "candidate_treated_as_final_answer": False,
        "treated_as_final_answer": False,
        "construction_trace_complete": True,
        "construction_trace_source_grounded": True,
        "forced_uniqueness_trace_present": True,
        "rival_elimination_trace_present": False,
        "train_evidence_grounded": True,
        "source_train_ids": ["train_1"],
        "source_train_example_ids": ["train_1"],
        "synthetic_local_train_ids": [],
        "train_grounded_transformation_rule": "mirror the train-supported relation",
        "train_grounded_forced_constraints": ["constraint_1"],
        "forced_constraints_tied_to_train_evidence": ["constraint_1"],
        "ambiguity_check": "clear",
        "competing_output_rejection_reason": "train evidence rejects the competing color swap",
        "competing_outputs_rejected_reason": "train evidence rejects the competing color swap",
        "uniquely_forced_reason": "all surviving train constraints force this exact output family",
        "helper_output_as_evidence": False,
        "rehearsal_repeat_as_evidence": False,
        "mdl_only_support": False,
        "unsupported_assumptions": [],
        "unresolved_rivals": [],
        "rival_context_detected": False,
        "rival_context_reasons": [],
        "rival_grammars": [],
        "surviving_grammar": None,
        "rival_elimination_trace": [],
        "surviving_grammar_train_evidence": "",
        "rival_outputs_considered": [],
        "rejected_rival_reasons": [],
        "surviving_grammar_uniquely_forces_output": False,
    }
    candidate.update(overrides)
    return candidate


def _evaluate(candidate, **input_overrides):
    task_id = input_overrides.pop("task_id", "task_test")
    inp = build_ledger_deservedness_assembler_input_v1(
        task_id=task_id,
        candidate_descriptors=[candidate],
        **input_overrides,
    )
    return evaluate_ledger_deservedness_v1(inp)


def _generator_candidate(complete=True, rival=False):
    generator_input = build_controlled_answer_candidate_generator_input_v1(
        task_id=KNOWN_BAD_ID if rival else "task_test",
        group_id="v4_rival_grammar_replay_6" if rival else None,
        expected_frontier_failure="rival_grammar_preserved" if rival else None,
        train_examples=BASE_TRAIN,
        test_input_descriptor={"grid": [[1, 2]]},
        forced_constraints=["constraint_1"] if complete else [],
        train_forced_transformations=[
            {"train_supported": True, "operation_name": "mirror_fill"}
            if complete
            else {"train_supported": True}
        ],
    )
    result = generate_controlled_answer_candidates_v1(generator_input)
    return result["candidates"][0]


class TestAssemblerRepair:
    def test_task_level_forced_constraints_alone_cannot_make_candidate_deserved(self):
        candidate = _valid_candidate(
            forced_uniqueness_trace_present=False,
            uniquely_forced_reason="",
            competing_output_rejection_reason="",
            competing_outputs_rejected_reason="",
        )
        result = _evaluate(candidate, forced_constraints=["constraint_1"], train_evidence_support={"support": True})
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["safe_failure_from_insufficient_evidence_count"] == 1

    def test_generator_produced_complete_candidate_can_pass_assembler(self):
        candidate = _generator_candidate(complete=True)
        result = _evaluate(candidate, forced_constraints=["constraint_1"], train_evidence_support={"support": True})
        assert result["decision"] == "candidate_deserved"
        assert result["metrics"]["candidate_deserved_count"] == 1

    def test_generator_produced_incomplete_candidate_safe_fails(self):
        candidate = _generator_candidate(complete=False)
        result = _evaluate(candidate)
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["safe_failure_from_incomplete_trace_count"] == 1

    def test_rival_context_train_forced_candidate_missing_proof_safe_fails(self):
        candidate = _generator_candidate(complete=True, rival=True)
        result = _evaluate(
            candidate,
            group_id="v4_rival_grammar_replay_6",
            expected_frontier_failure="rival_grammar_preserved",
        )
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["safe_failure_from_unresolved_rival_count"] == 1
        assert result["metrics"]["rival_context_detected_count"] == 1
        assert result["metrics"]["rival_context_missing_proof_count"] == 1
        assert result["metrics"]["rival_context_safe_failure_count"] == 1
        assert result["metrics"]["train_forced_rival_bypass_blocked_count"] == 1

    def test_task_level_rival_context_catches_candidate_even_without_candidate_flag(self):
        candidate = _valid_candidate(
            task_id=KNOWN_BAD_ID,
            rival_context_detected=False,
            rival_context_reasons=[],
        )
        result = _evaluate(
            candidate,
            task_id=KNOWN_BAD_ID,
            group_id="v4_rival_grammar_replay_6",
            expected_frontier_failure="rival_grammar_preserved",
        )
        assert result["decision"] == "safe_failure_required"
        assert result["metrics"]["safe_failure_from_unresolved_rival_count"] == 1

    def test_rival_grammar_candidate_with_full_proof_can_be_deserved(self):
        candidate = _valid_candidate(
            construction_mode="explicit_grammar_candidate",
            rival_context_detected=True,
            rival_context_reasons=["rival_grammars_present"],
            rival_grammars=["g2"],
            surviving_grammar="g1",
            rival_elimination_trace=[{"rival_grammar": "g2", "reason": "contradicted by train evidence"}],
            rival_elimination_trace_present=True,
            surviving_grammar_train_evidence="Train examples support surviving grammar g1.",
            rival_outputs_considered=["alt_output"],
            rejected_rival_reasons=["Rejected g2 because it conflicts with train evidence."],
            surviving_grammar_uniquely_forces_output=True,
        )
        result = _evaluate(candidate)
        assert result["decision"] == "candidate_deserved"

    def test_scoring_answer_in_assembler_input_fails_closed(self):
        inp = build_ledger_deservedness_assembler_input_v1(
            task_id="task_test",
            candidate_descriptors=[_valid_candidate()],
        )
        inp["synthetic_expected_answer_for_scoring_only"] = [[1]]
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
        required = [
            "ledger_review_required_count",
            "construction_trace_complete_count",
            "forced_uniqueness_trace_present_count",
            "rival_elimination_trace_present_count",
            "train_evidence_grounded_count",
            "safe_failure_from_insufficient_evidence_count",
            "safe_failure_from_incomplete_trace_count",
            "safe_failure_from_unresolved_rival_count",
            "rival_context_detected_count",
            "rival_context_missing_proof_count",
            "rival_context_safe_failure_count",
            "train_forced_rival_bypass_blocked_count",
        ]
        for key in required:
            assert key in result["metrics"]

    def test_anti_laundering_boundary_constants_remain_false(self):
        assert HELPER_OUTPUT_AS_EVIDENCE is False
        assert "train_evidence_grounded" in _valid_candidate()
