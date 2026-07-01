"""Tests for WESLR native ARC language schema."""

import pytest
from weslr.native_arc_language_schema import (
    NativeProgram, PrimitiveContract, AuditArtifactBundle, TypeSignature,
    PromotionStage, make_native_program, make_primitive_contract,
    compute_content_hash, is_valid_type, is_valid_type_signature,
    is_grid_transform, is_promotion_eligible, can_advance_to,
    validate_promotion_eligibility, reject_unvalidated_as_solved,
    BH80_REGRESSION_POLICY, VALID_TYPES,
)


class TestTypeSystem:
    def test_all_valid_types(self):
        for t in VALID_TYPES:
            assert is_valid_type(t)

    def test_invalid_type_rejected(self):
        assert not is_valid_type("Foo")
        assert not is_valid_type("")
        assert not is_valid_type("grid")  # case sensitive

    def test_valid_type_signature(self):
        assert is_valid_type_signature("Grid", "Grid")
        assert is_valid_type_signature("Grid", "Mask")

    def test_invalid_type_signature(self):
        assert not is_valid_type_signature("Grid", "Foo")
        assert not is_valid_type_signature("Bar", "Grid")

    def test_is_grid_transform(self):
        assert is_grid_transform("Grid", "Grid")
        assert not is_grid_transform("Grid", "Mask")
        assert not is_grid_transform("Mask", "Grid")


class TestNativeProgram:
    def test_alien_expression_accepted(self):
        """Alien/non-human-readable expression is accepted if typed and hashable."""
        prog = make_native_program(
            program_id="alien_001",
            internal_expression="λx.⊗(∇x,3)⇒⌬",  # alien symbols
            input_type="Grid",
            output_type="Grid",
        )
        assert prog.program_id == "alien_001"
        assert prog.content_hash  # hashable

    def test_human_summary_optional(self):
        prog = make_native_program(
            program_id="p1",
            internal_expression="binary_op:0xFF1A",
            input_type="Grid",
            output_type="Grid",
            human_summary=None,
        )
        assert prog.human_summary is None  # accepted without summary

    def test_human_summary_provided(self):
        prog = make_native_program(
            program_id="p2",
            internal_expression="binary_op:0xFF1A",
            input_type="Grid",
            output_type="Grid",
            human_summary="Rotate and crop",
        )
        assert prog.human_summary == "Rotate and crop"

    def test_invalid_type_rejected(self):
        with pytest.raises(ValueError, match="Invalid input type"):
            make_native_program("p3", "expr", input_type="Foo", output_type="Grid")

    def test_missing_content_hash_detected(self):
        sig = TypeSignature(input="Grid", output="Grid")
        prog = NativeProgram(
            program_id="p4",
            internal_expression="expr",
            content_hash="",  # empty
            type_signature=sig,
        )
        with pytest.raises(ValueError, match="content_hash is required"):
            prog.validate()

    def test_non_deterministic_rejected(self):
        sig = TypeSignature(input="Grid", output="Grid")
        prog = NativeProgram(
            program_id="p5",
            internal_expression="expr",
            content_hash="abc",
            type_signature=sig,
            deterministic=False,
        )
        with pytest.raises(ValueError, match="Non-deterministic"):
            prog.validate()

    def test_content_hash_computed(self):
        prog = make_native_program("p6", "test_expression", "Grid", "Grid")
        expected = compute_content_hash("test_expression")
        assert prog.content_hash == expected


class TestPrimitiveContract:
    def test_basic_contract(self):
        c = make_primitive_contract("prim_001", "λx.⊗x", "Grid", "Grid")
        assert c.primitive_id == "prim_001"
        assert c.promotion_stage == PromotionStage.GENERATED

    def test_promotion_blocked_before_oracle(self):
        c = make_primitive_contract("prim_002", "expr", "Grid", "Grid")
        c.oracle_execution_status = "not_implemented"
        eligible, reason = validate_promotion_eligibility(c)
        assert not eligible
        assert "Missing stages" in reason or "Oracle" in reason

    def test_promotion_blocked_before_solver(self):
        c = make_primitive_contract("prim_003", "expr", "Grid", "Grid")
        c.completed_stages = {
            PromotionStage.GENERATED, PromotionStage.TYPED,
            PromotionStage.EXECUTABLE, PromotionStage.ORACLE_DEFINED,
        }
        c.oracle_execution_status = "verified"
        eligible, reason = validate_promotion_eligibility(c)
        assert not eligible
        assert "Missing stages" in reason or "Solver" in reason

    def test_promotion_blocked_without_tests(self):
        c = make_primitive_contract("prim_004", "expr", "Grid", "Grid")
        c.completed_stages = {
            PromotionStage.GENERATED, PromotionStage.TYPED,
            PromotionStage.EXECUTABLE, PromotionStage.ORACLE_DEFINED,
            PromotionStage.SOLVER_TARGETED,
        }
        c.oracle_execution_status = "verified"
        c.solver_execution_status = "verified"
        eligible, reason = validate_promotion_eligibility(c)
        assert not eligible
        assert "Missing stages" in reason

    def test_promotion_eligible_with_all_stages(self):
        c = make_primitive_contract("prim_005", "expr", "Grid", "Grid")
        c.completed_stages = set()  # all required stages
        for stage in [PromotionStage.GENERATED, PromotionStage.TYPED,
                      PromotionStage.EXECUTABLE, PromotionStage.ORACLE_DEFINED,
                      PromotionStage.SOLVER_TARGETED, PromotionStage.TESTED,
                      PromotionStage.ANTI_CHEAT_VALIDATED, PromotionStage.REGRESSION_SAFE]:
            c.completed_stages.add(stage)
        c.oracle_execution_status = "verified"
        c.solver_execution_status = "verified"
        c.positive_examples = [{"input": "grid1", "output": "grid1_out"}]
        c.negative_controls = [{"no_op": True, "differs": True}]
        c.anti_cheat_checks = ["no_task_id_access"]
        eligible, reason = validate_promotion_eligibility(c)
        assert eligible, f"Expected eligible but: {reason}"

    def test_promoted_contract_validates(self):
        c = make_primitive_contract("prim_006", "expr", "Grid", "Grid")
        for stage in [PromotionStage.GENERATED, PromotionStage.TYPED,
                      PromotionStage.EXECUTABLE, PromotionStage.ORACLE_DEFINED,
                      PromotionStage.SOLVER_TARGETED, PromotionStage.TESTED,
                      PromotionStage.ANTI_CHEAT_VALIDATED, PromotionStage.REGRESSION_SAFE,
                      PromotionStage.PROMOTED]:
            c.completed_stages.add(stage)
        c.promotion_stage = PromotionStage.PROMOTED
        c.oracle_execution_status = "verified"
        c.solver_execution_status = "verified"
        c.validate()  # should not raise

    def test_promoted_without_stages_rejected(self):
        c = make_primitive_contract("prim_007", "expr", "Grid", "Grid")
        c.promotion_stage = PromotionStage.PROMOTED
        # completed_stages is empty
        with pytest.raises(ValueError, match="marked as promoted but"):
            c.validate()

    def test_promoted_without_oracle_rejected(self):
        c = make_primitive_contract("prim_008", "expr", "Grid", "Grid")
        for stage in REQUIRED_STAGES_BEFORE_PROMOTION_TEST:
            c.completed_stages.add(stage)
        c.promotion_stage = PromotionStage.PROMOTED
        c.oracle_execution_status = "not_implemented"
        with pytest.raises(ValueError, match="verified oracle"):
            c.validate()

    def test_unvalidated_not_counted_as_solved(self):
        c = make_primitive_contract("prim_009", "expr", "Grid", "Grid")
        assert reject_unvalidated_as_solved(c) is True  # rejected

    def test_promoted_counted_as_solved(self):
        c = make_primitive_contract("prim_010", "expr", "Grid", "Grid")
        for stage in [PromotionStage.GENERATED, PromotionStage.TYPED,
                      PromotionStage.EXECUTABLE, PromotionStage.ORACLE_DEFINED,
                      PromotionStage.SOLVER_TARGETED, PromotionStage.TESTED,
                      PromotionStage.ANTI_CHEAT_VALIDATED, PromotionStage.REGRESSION_SAFE,
                      PromotionStage.PROMOTED]:
            c.completed_stages.add(stage)
        c.promotion_stage = PromotionStage.PROMOTED
        c.oracle_execution_status = "verified"
        c.solver_execution_status = "verified"
        assert c.can_be_counted_as_solved() is True
        assert reject_unvalidated_as_solved(c) is False


# Required stages set for test fixtures
REQUIRED_STAGES_BEFORE_PROMOTION_TEST = {
    PromotionStage.GENERATED, PromotionStage.TYPED,
    PromotionStage.EXECUTABLE, PromotionStage.ORACLE_DEFINED,
    PromotionStage.SOLVER_TARGETED, PromotionStage.TESTED,
    PromotionStage.ANTI_CHEAT_VALIDATED, PromotionStage.REGRESSION_SAFE,
}


class TestPromotionStageModel:
    def test_stage_order(self):
        assert PromotionStage.GENERATED == STAGE_ORDER_TEST[0]
        assert PromotionStage.PROMOTED == STAGE_ORDER_TEST[-1]

    def test_can_advance_sequentially(self):
        assert can_advance_to(PromotionStage.GENERATED, PromotionStage.TYPED)
        assert can_advance_to(PromotionStage.TYPED, PromotionStage.EXECUTABLE)

    def test_cannot_skip_stages(self):
        assert not can_advance_to(PromotionStage.GENERATED, PromotionStage.EXECUTABLE)
        assert not can_advance_to(PromotionStage.GENERATED, PromotionStage.PROMOTED)

    def test_is_promotion_eligible_empty(self):
        assert not is_promotion_eligible(set())

    def test_is_promotion_eligible_all(self):
        assert is_promotion_eligible(REQUIRED_STAGES_BEFORE_PROMOTION_TEST)


STAGE_ORDER_TEST = [
    PromotionStage.GENERATED, PromotionStage.TYPED,
    PromotionStage.EXECUTABLE, PromotionStage.ORACLE_DEFINED,
    PromotionStage.SOLVER_TARGETED, PromotionStage.TESTED,
    PromotionStage.ANTI_CHEAT_VALIDATED, PromotionStage.REGRESSION_SAFE,
    PromotionStage.PROMOTED,
]


class TestAuditArtifacts:
    def test_complete_audit_bundle(self):
        sig = TypeSignature(input="Grid", output="Grid")
        bundle = AuditArtifactBundle(
            primitive_id="prim_aud",
            serialized_internal_expression="λx.x",
            content_hash="abc123",
            type_signature=sig,
            deterministic_execution_trace=[{"step": 1, "grid": [[1]]}],
            input_output_examples=[{"input": [[1]], "output": [[2]]}],
            oracle_output=[{"output": [[2]]}],
            solver_output=[{"output": [[2]]}],
            grid_equality_result=[{"equal": True}],
            invariant_checks=[{"name": "dims", "preserved": True}],
            negative_control_results=[{"type": "noop", "differs": True}],
            regression_impact_summary="BH80: 80/80 (no change)",
        )
        bundle.validate_completeness()  # should not raise

    def test_missing_audit_artifact_rejected(self):
        sig = TypeSignature(input="Grid", output="Grid")
        bundle = AuditArtifactBundle(
            primitive_id="prim_aud2",
            serialized_internal_expression="",
            content_hash="abc",
            type_signature=sig,
            deterministic_execution_trace=[],
            input_output_examples=[],
            oracle_output=[],
            solver_output=[],
            grid_equality_result=[],
            invariant_checks=[],
            negative_control_results=[],
            regression_impact_summary="",
        )
        with pytest.raises(ValueError, match="Missing required audit artifact"):
            bundle.validate_completeness()

    def test_human_summary_optional_in_audit(self):
        sig = TypeSignature(input="Grid", output="Grid")
        bundle = AuditArtifactBundle(
            primitive_id="prim_aud3",
            serialized_internal_expression="expr",
            content_hash="abc",
            type_signature=sig,
            deterministic_execution_trace=[{"step": 1}],
            input_output_examples=[{"in": [[1]]}],
            oracle_output=[{"out": [[2]]}],
            solver_output=[{"out": [[2]]}],
            grid_equality_result=[{"eq": True}],
            invariant_checks=[{"ok": True}],
            negative_control_results=[{"diff": True}],
            regression_impact_summary="OK",
            human_summary=None,
        )
        bundle.validate_completeness()  # should not raise even without human_summary


class TestBH80RegressionPolicy:
    def test_policy_exists(self):
        assert BH80_REGRESSION_POLICY["frozen_baseline"] == 80
        assert BH80_REGRESSION_POLICY["strong_gate"] == 72
        assert BH80_REGRESSION_POLICY["minimal_gate"] == 68