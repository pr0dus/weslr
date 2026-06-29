import copy

from weslr.arc_controlled_answer_candidate_generator import (
    ANTILAUNDERING_LAWS,
    CANDIDATE_TREATED_AS_FINAL_ANSWER,
    GENERATOR_GRANTS_DESERVEDNESS,
    GENERATOR_OUTPUTS_FINAL_ANSWER,
    REQUIRES_LEDGER_REVIEW,
    build_controlled_answer_candidate_generator_input_v1,
    generate_controlled_answer_candidates_v1,
)


BASE_TRAIN = [{"input": [[1, 2]], "output": [[2, 1]]}]
KNOWN_BAD_IDS = [
    "v5_replay_v4_rival_grammar_replay_6_01",
    "v5_replay_v4_rival_grammar_replay_6_02",
    "v5_replay_v4_rival_grammar_replay_6_03",
    "v5_replay_v4_rival_grammar_replay_6_04",
    "v5_replay_v4_rival_grammar_replay_6_05",
    "v5_replay_v4_rival_grammar_replay_6_06",
]


def _generate(task_id="task_test", group_id=None, expected_frontier_failure=None, **overrides):
    inp = build_controlled_answer_candidate_generator_input_v1(
        task_id=task_id,
        train_examples=copy.deepcopy(BASE_TRAIN),
        test_input_descriptor={"grid": [[1, 2]]},
        group_id=group_id,
        expected_frontier_failure=expected_frontier_failure,
        **overrides,
    )
    return generate_controlled_answer_candidates_v1(inp)


def _complete_train_forced_result():
    return _generate(
        forced_constraints=["colors preserve order"],
        train_forced_transformations=[
            {
                "train_supported": True,
                "operation_name": "mirror_fill",
                "source_helper": "helper_1",
                "output_shape": {"rows": 1, "cols": 2},
            }
        ],
    )


class TestBoundaryFlags:
    def test_boundary_constants_remain_false_or_true(self):
        assert GENERATOR_GRANTS_DESERVEDNESS is False
        assert GENERATOR_OUTPUTS_FINAL_ANSWER is False
        assert REQUIRES_LEDGER_REVIEW is True
        assert CANDIDATE_TREATED_AS_FINAL_ANSWER is False

    def test_all_anti_laundering_laws_exposed(self):
        assert len(ANTILAUNDERING_LAWS) == 12


class TestTraceGroundingSchema:
    def test_generated_candidate_includes_required_trace_grounding_schema(self):
        result = _complete_train_forced_result()
        candidate = result["candidates"][0]
        required = [
            "requires_ledger_review",
            "candidate_treated_as_final_answer",
            "construction_trace",
            "construction_trace_complete",
            "construction_trace_source_grounded",
            "train_evidence_grounded",
            "forced_uniqueness_trace_present",
            "source_train_ids",
            "synthetic_local_train_ids",
            "train_grounded_transformation_rule",
            "train_grounded_forced_constraints",
            "ambiguity_check",
            "competing_output_rejection_reason",
            "uniquely_forced_reason",
            "unsupported_assumptions",
            "unresolved_rivals",
            "helper_output_as_evidence",
            "rehearsal_repeat_as_evidence",
            "mdl_only_support",
            "rival_context_detected",
            "rival_context_reasons",
        ]
        for field in required:
            assert field in candidate, field
        assert candidate["requires_ledger_review"] is True
        assert candidate["candidate_treated_as_final_answer"] is False

    def test_complete_train_grounded_candidate_has_complete_trace_fields(self):
        result = _complete_train_forced_result()
        candidate = result["candidates"][0]
        assert candidate["construction_trace_complete"] is True
        assert candidate["construction_trace_source_grounded"] is True
        assert candidate["train_evidence_grounded"] is True
        assert candidate["forced_uniqueness_trace_present"] is True
        assert candidate["source_train_ids"] == ["train_1"]
        assert candidate["train_grounded_forced_constraints"] == ["colors preserve order"]
        assert candidate["missing_required_trace_fields"] == []

    def test_incomplete_candidate_does_not_falsely_mark_trace_complete(self):
        result = _generate(
            train_forced_transformations=[{"train_supported": True}],
        )
        candidate = result["candidates"][0]
        assert candidate["construction_trace_complete"] is False
        assert "train_grounded_forced_constraints" in candidate["missing_required_trace_fields"]
        assert candidate["forced_uniqueness_trace_present"] is False


class TestRivalContextRepair:
    def test_train_forced_rival_context_cannot_claim_complete_without_rival_proof(self):
        result = _generate(
            task_id=KNOWN_BAD_IDS[0],
            group_id="v4_rival_grammar_replay_6",
            expected_frontier_failure="rival_grammar_preserved",
            forced_constraints=["constraint_1"],
            train_forced_transformations=[{"train_supported": True, "operation_name": "mirror_fill"}],
        )
        candidate = result["candidates"][0]
        assert candidate["rival_context_detected"] is True
        assert candidate["construction_mode"] == "train_forced_transformation_candidate"
        assert candidate["construction_trace_complete"] is False
        assert candidate["forced_uniqueness_trace_present"] is False
        assert "rival_context_unresolved" in candidate["unresolved_rivals"]
        assert "rival_grammars" in candidate["missing_required_trace_fields"]
        assert "rival_elimination_trace" in candidate["missing_required_trace_fields"]
        assert candidate["competing_output_rejection_reason"] == ""
        assert candidate["uniquely_forced_reason"] == ""

    def test_explicit_rival_grammar_candidate_can_still_be_complete_when_proof_is_present(self):
        result = _generate(
            forced_constraints=["grammar_consistent"],
            explicit_candidate_grammars=[
                {
                    "rules_from_train": True,
                    "grammar_id": "grammar_A",
                    "rival_grammars": ["grammar_B"],
                    "rival_outputs_considered": ["out_B"],
                    "rejected_rival_reasons": ["Rejected grammar_B because it conflicts with train evidence."],
                    "source_helper": "grammar_helper",
                }
            ],
        )
        candidate = result["candidates"][0]
        assert candidate["rival_context_detected"] is True
        assert candidate["construction_trace_complete"] is True
        assert candidate["forced_uniqueness_trace_present"] is True
        assert candidate["surviving_grammar"] == "grammar_A"
        assert candidate["rival_elimination_trace"]
        assert candidate["surviving_grammar_train_evidence"]
        assert candidate["surviving_grammar_uniquely_forces_output"] is True

    def test_known_bad_six_ids_all_detect_rival_context_and_missing_proof(self):
        for task_id in KNOWN_BAD_IDS:
            result = _generate(
                task_id=task_id,
                group_id="v4_rival_grammar_replay_6",
                expected_frontier_failure="rival_grammar_preserved",
                forced_constraints=["constraint_1"],
                train_forced_transformations=[{"train_supported": True, "operation_name": "mirror_fill"}],
            )
            candidate = result["candidates"][0]
            assert candidate["rival_context_detected"] is True
            assert candidate["construction_trace_complete"] is False
            assert candidate["forced_uniqueness_trace_present"] is False


class TestPartialAndSafety:
    def test_partial_candidate_cannot_mark_itself_complete_or_uniquely_forced(self):
        result = _generate()
        candidate = result["candidates"][0]
        assert candidate["construction_mode"] == "partial_candidate_descriptor"
        assert candidate["construction_trace_complete"] is False
        assert candidate["forced_uniqueness_trace_present"] is False

    def test_no_expected_or_scoring_answer_field_appears_in_candidates(self):
        result = _complete_train_forced_result()
        candidate = result["candidates"][0]
        forbidden = {
            "synthetic_expected_answer_for_scoring_only",
            "expected_output",
            "expected_answer",
            "post_ledger_scoring_result",
            "deserved_exact_result",
            "deserved_but_wrong_result",
        }
        assert not (forbidden & set(candidate.keys()))


class TestMetrics:
    def test_required_metrics_exist(self):
        result = _complete_train_forced_result()
        metrics = result["metrics"]
        required = [
            "ledger_review_required_count",
            "construction_trace_complete_count",
            "forced_uniqueness_trace_present_count",
            "rival_elimination_trace_present_count",
            "train_evidence_grounded_count",
            "candidate_trace_missing_required_fields_count",
            "candidate_trace_source_grounded_count",
            "candidate_trace_incomplete_count",
            "rival_context_detected_count",
            "rival_context_missing_proof_count",
            "train_forced_rival_bypass_blocked_count",
        ]
        for key in required:
            assert key in metrics

    def test_rival_context_metrics_increment_from_actual_candidate_state(self):
        complete = _complete_train_forced_result()["metrics"]
        rival = _generate(
            task_id=KNOWN_BAD_IDS[0],
            group_id="v4_rival_grammar_replay_6",
            expected_frontier_failure="rival_grammar_preserved",
            forced_constraints=["constraint_1"],
            train_forced_transformations=[{"train_supported": True, "operation_name": "mirror_fill"}],
        )["metrics"]
        assert complete["rival_context_detected_count"] == 0
        assert rival["rival_context_detected_count"] == 1
        assert rival["rival_context_missing_proof_count"] == 1
        assert rival["train_forced_rival_bypass_blocked_count"] == 1
