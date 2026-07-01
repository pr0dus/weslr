"""WESLR Native ARC Grid‑World Language Schema.

Implements the schema layer for WESLR's native ARC/grid‑world language:
- native program schema
- type system
- primitive contract schema
- promotion stage model
- audit artifact schema
- validation helpers

This module is schema/validation only. No primitive discovery search.
No solver/oracle changes. No BH80 changes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Type System
# ---------------------------------------------------------------------------

VALID_TYPES: Set[str] = {
    "Grid", "Cell", "Color", "Background", "Object", "ObjectSet",
    "Mask", "Region", "BoundingBox", "Count", "Relation", "Transform",
    "Pattern", "Program", "Trace", "Invariant",
}

GRID_COMPATIBLE_OUTPUT_TYPES: Set[str] = {
    "Grid", "Mask", "Count", "Object", "ObjectSet", "Region", "BoundingBox",
}


def is_valid_type(type_name: str) -> bool:
    return type_name in VALID_TYPES


def is_valid_type_signature(input_type: str, output_type: str) -> bool:
    return is_valid_type(input_type) and is_valid_type(output_type)


def is_grid_transform(input_type: str, output_type: str) -> bool:
    return input_type == "Grid" and output_type == "Grid"


# ---------------------------------------------------------------------------
# Promotion Stages
# ---------------------------------------------------------------------------

class PromotionStage(str, Enum):
    GENERATED = "generated"
    TYPED = "typed"
    EXECUTABLE = "executable"
    ORACLE_DEFINED = "oracle_defined"
    SOLVER_TARGETED = "solver_targeted"
    TESTED = "tested"
    ANTI_CHEAT_VALIDATED = "anti_cheat_validated"
    REGRESSION_SAFE = "regression_safe"
    PROMOTED = "promoted"


STAGE_ORDER: List[PromotionStage] = [
    PromotionStage.GENERATED,
    PromotionStage.TYPED,
    PromotionStage.EXECUTABLE,
    PromotionStage.ORACLE_DEFINED,
    PromotionStage.SOLVER_TARGETED,
    PromotionStage.TESTED,
    PromotionStage.ANTI_CHEAT_VALIDATED,
    PromotionStage.REGRESSION_SAFE,
    PromotionStage.PROMOTED,
]

REQUIRED_STAGES_BEFORE_PROMOTION: Set[PromotionStage] = {
    PromotionStage.GENERATED,
    PromotionStage.TYPED,
    PromotionStage.EXECUTABLE,
    PromotionStage.ORACLE_DEFINED,
    PromotionStage.SOLVER_TARGETED,
    PromotionStage.TESTED,
    PromotionStage.ANTI_CHEAT_VALIDATED,
    PromotionStage.REGRESSION_SAFE,
}


def stage_index(stage: PromotionStage) -> int:
    return STAGE_ORDER.index(stage)


def can_advance_to(from_stage: PromotionStage, to_stage: PromotionStage) -> bool:
    fi = stage_index(from_stage)
    ti = stage_index(to_stage)
    return ti == fi + 1


def is_promotion_eligible(completed_stages: Set[PromotionStage]) -> bool:
    return REQUIRED_STAGES_BEFORE_PROMOTION.issubset(completed_stages)


# ---------------------------------------------------------------------------
# Content Hash
# ---------------------------------------------------------------------------

def compute_content_hash(serialized_expression: str) -> str:
    return hashlib.sha256(serialized_expression.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Native Program Schema
# ---------------------------------------------------------------------------

@dataclass
class TypeSignature:
    input: str
    output: str
    parameters: List[Dict[str, str]] = field(default_factory=list)

    def validate(self) -> None:
        if not is_valid_type(self.input):
            raise ValueError(f"Invalid input type: {self.input}")
        if not is_valid_type(self.output):
            raise ValueError(f"Invalid output type: {self.output}")
        for param in self.parameters:
            if "name" not in param or "type" not in param:
                raise ValueError(f"Parameter missing name or type: {param}")
            if not is_valid_type(param["type"]):
                raise ValueError(f"Invalid parameter type: {param['type']}")

    def is_grid_transform(self) -> bool:
        return is_grid_transform(self.input, self.output)

    def to_dict(self) -> dict:
        return {"input": self.input, "output": self.output, "parameters": self.parameters}


@dataclass
class NativeProgram:
    program_id: str
    internal_expression: str  # alien/non-human-readable is fine
    content_hash: str
    type_signature: TypeSignature
    deterministic: bool = True
    preconditions: List[str] = field(default_factory=list)
    invariants_preserved: List[str] = field(default_factory=list)
    invariants_changed: List[str] = field(default_factory=list)
    human_summary: Optional[str] = None  # optional

    def validate(self) -> None:
        if not self.program_id:
            raise ValueError("program_id is required")
        if not self.internal_expression:
            raise ValueError("internal_expression is required")
        if not self.content_hash:
            raise ValueError("content_hash is required")
        if not self.deterministic:
            raise ValueError("Non-deterministic programs are not allowed")
        self.type_signature.validate()

    def to_dict(self) -> dict:
        return {
            "program_id": self.program_id,
            "internal_expression": self.internal_expression,
            "content_hash": self.content_hash,
            "type_signature": self.type_signature.to_dict(),
            "deterministic": self.deterministic,
            "preconditions": self.preconditions,
            "invariants_preserved": self.invariants_preserved,
            "invariants_changed": self.invariants_changed,
            "human_summary": self.human_summary,
        }


def make_native_program(
    program_id: str,
    internal_expression: str,
    input_type: str,
    output_type: str,
    parameters: Optional[List[Dict[str, str]]] = None,
    preconditions: Optional[List[str]] = None,
    invariants_preserved: Optional[List[str]] = None,
    invariants_changed: Optional[List[str]] = None,
    human_summary: Optional[str] = None,
) -> NativeProgram:
    content_hash = compute_content_hash(internal_expression)
    sig = TypeSignature(input=input_type, output=output_type, parameters=parameters or [])
    prog = NativeProgram(
        program_id=program_id,
        internal_expression=internal_expression,
        content_hash=content_hash,
        type_signature=sig,
        preconditions=preconditions or [],
        invariants_preserved=invariants_preserved or [],
        invariants_changed=invariants_changed or [],
        human_summary=human_summary,
    )
    prog.validate()
    return prog


# ---------------------------------------------------------------------------
# Primitive Contract Schema
# ---------------------------------------------------------------------------

@dataclass
class PrimitiveContract:
    primitive_id: str
    internal_expression: str
    content_hash: str
    type_signature: TypeSignature
    deterministic_semantics: bool
    preconditions: List[str] = field(default_factory=list)
    invariants_preserved: List[str] = field(default_factory=list)
    invariants_changed: List[str] = field(default_factory=list)
    oracle_execution_status: str = "not_implemented"  # not_implemented | implemented | verified
    solver_execution_status: str = "not_implemented"  # not_implemented | implemented | verified
    positive_examples: List[Dict[str, Any]] = field(default_factory=list)
    negative_controls: List[Dict[str, Any]] = field(default_factory=list)
    anti_cheat_checks: List[str] = field(default_factory=list)
    regression_tests: List[str] = field(default_factory=list)
    promotion_stage: PromotionStage = PromotionStage.GENERATED
    completed_stages: Set[PromotionStage] = field(default_factory=set)
    human_summary: Optional[str] = None

    def validate(self) -> None:
        if not self.primitive_id:
            raise ValueError("primitive_id is required")
        if not self.internal_expression:
            raise ValueError("internal_expression is required")
        if not self.content_hash:
            raise ValueError("content_hash is required")
        if not self.deterministic_semantics:
            raise ValueError("Non-deterministic primitives are not allowed")
        self.type_signature.validate()

        # Promotion validation
        if self.promotion_stage == PromotionStage.PROMOTED:
            if not is_promotion_eligible(self.completed_stages):
                raise ValueError(
                    f"Primitive {self.primitive_id} marked as promoted but "
                    f"missing required stages: "
                    f"{REQUIRED_STAGES_BEFORE_PROMOTION - self.completed_stages}"
                )
            if self.oracle_execution_status != "verified":
                raise ValueError(
                    f"Primitive {self.primitive_id} promoted without verified oracle"
                )
            if self.solver_execution_status != "verified":
                raise ValueError(
                    f"Primitive {self.primitive_id} promoted without verified solver"
                )

    def advance_stage(self, to_stage: PromotionStage) -> None:
        if self.completed_stages and not can_advance_to(max(self.completed_stages, key=stage_index), to_stage):
            raise ValueError(
                f"Cannot advance from {max(self.completed_stages, key=stage_index)} to {to_stage}"
            )
        self.completed_stages.add(to_stage)
        self.promotion_stage = to_stage

    def can_be_counted_as_solved(self) -> bool:
        """Unvalidated primitives cannot be counted as solved."""
        return self.promotion_stage == PromotionStage.PROMOTED

    def to_dict(self) -> dict:
        return {
            "primitive_id": self.primitive_id,
            "internal_expression": self.internal_expression,
            "content_hash": self.content_hash,
            "type_signature": self.type_signature.to_dict(),
            "deterministic_semantics": self.deterministic_semantics,
            "preconditions": self.preconditions,
            "invariants_preserved": self.invariants_preserved,
            "invariants_changed": self.invariants_changed,
            "oracle_execution_status": self.oracle_execution_status,
            "solver_execution_status": self.solver_execution_status,
            "positive_examples": self.positive_examples,
            "negative_controls": self.negative_controls,
            "anti_cheat_checks": self.anti_cheat_checks,
            "regression_tests": self.regression_tests,
            "promotion_stage": self.promotion_stage.value,
            "completed_stages": sorted(s.value for s in self.completed_stages),
            "human_summary": self.human_summary,
        }


def make_primitive_contract(
    primitive_id: str,
    internal_expression: str,
    input_type: str = "Grid",
    output_type: str = "Grid",
    parameters: Optional[List[Dict[str, str]]] = None,
    preconditions: Optional[List[str]] = None,
    invariants_preserved: Optional[List[str]] = None,
    invariants_changed: Optional[List[str]] = None,
    human_summary: Optional[str] = None,
) -> PrimitiveContract:
    content_hash = compute_content_hash(internal_expression)
    sig = TypeSignature(input=input_type, output=output_type, parameters=parameters or [])
    contract = PrimitiveContract(
        primitive_id=primitive_id,
        internal_expression=internal_expression,
        content_hash=content_hash,
        type_signature=sig,
        deterministic_semantics=True,
        preconditions=preconditions or [],
        invariants_preserved=invariants_preserved or [],
        invariants_changed=invariants_changed or [],
        human_summary=human_summary,
    )
    contract.validate()
    return contract


# ---------------------------------------------------------------------------
# Audit Artifact Schema
# ---------------------------------------------------------------------------

REQUIRED_AUDIT_ARTIFACTS: Set[str] = {
    "serialized_internal_expression",
    "content_hash",
    "type_signature",
    "deterministic_execution_trace",
    "input_output_examples",
    "oracle_output",
    "solver_output",
    "grid_equality_result",
    "invariant_checks",
    "negative_control_results",
    "regression_impact_summary",
    # "human_summary" is optional, not required
}


@dataclass
class AuditArtifactBundle:
    primitive_id: str
    serialized_internal_expression: str
    content_hash: str
    type_signature: TypeSignature
    deterministic_execution_trace: List[Dict[str, Any]]
    input_output_examples: List[Dict[str, Any]]
    oracle_output: List[Dict[str, Any]]
    solver_output: List[Dict[str, Any]]
    grid_equality_result: List[Dict[str, Any]]
    invariant_checks: List[Dict[str, Any]]
    negative_control_results: List[Dict[str, Any]]
    regression_impact_summary: str
    human_summary: Optional[str] = None

    def validate_completeness(self) -> None:
        required = {
            "serialized_internal_expression": self.serialized_internal_expression,
            "content_hash": self.content_hash,
            "type_signature": self.type_signature,
            "deterministic_execution_trace": self.deterministic_execution_trace,
            "input_output_examples": self.input_output_examples,
            "oracle_output": self.oracle_output,
            "solver_output": self.solver_output,
            "grid_equality_result": self.grid_equality_result,
            "invariant_checks": self.invariant_checks,
            "negative_control_results": self.negative_control_results,
            "regression_impact_summary": self.regression_impact_summary,
        }
        for name, value in required.items():
            if value is None or (isinstance(value, (list, str)) and len(value) == 0):
                raise ValueError(f"Missing required audit artifact: {name}")

    def to_dict(self) -> dict:
        return {
            "primitive_id": self.primitive_id,
            "serialized_internal_expression": self.serialized_internal_expression,
            "content_hash": self.content_hash,
            "type_signature": self.type_signature.to_dict(),
            "deterministic_execution_trace": self.deterministic_execution_trace,
            "input_output_examples": self.input_output_examples,
            "oracle_output": self.oracle_output,
            "solver_output": self.solver_output,
            "grid_equality_result": self.grid_equality_result,
            "invariant_checks": self.invariant_checks,
            "negative_control_results": self.negative_control_results,
            "regression_impact_summary": self.regression_impact_summary,
            "human_summary": self.human_summary,
        }


# ---------------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------------

def validate_schema_completeness(program: NativeProgram) -> None:
    """Validate that a NativeProgram has all required fields."""
    program.validate()


def validate_primitive_contract_completeness(contract: PrimitiveContract) -> None:
    """Validate that a PrimitiveContract has all required fields and valid promotion."""
    contract.validate()


def validate_audit_completeness(bundle: AuditArtifactBundle) -> None:
    """Validate that an AuditArtifactBundle has all mandatory artifacts."""
    bundle.validate_completeness()


def reject_unvalidated_as_solved(contract: PrimitiveContract) -> bool:
    """Return True if the primitive CANNOT be counted as solved (should be rejected)."""
    return not contract.can_be_counted_as_solved()


def validate_promotion_eligibility(contract: PrimitiveContract) -> Tuple[bool, str]:
    """Check if a contract is eligible for promotion. Returns (eligible, reason)."""
    if not is_promotion_eligible(contract.completed_stages):
        missing = REQUIRED_STAGES_BEFORE_PROMOTION - contract.completed_stages
        return False, f"Missing stages: {sorted(s.value for s in missing)}"
    if contract.oracle_execution_status != "verified":
        return False, "Oracle not verified"
    if contract.solver_execution_status != "verified":
        return False, "Solver not verified"
    if not contract.positive_examples:
        return False, "No positive examples"
    if not contract.negative_controls:
        return False, "No negative controls"
    if not contract.anti_cheat_checks:
        return False, "No anti-cheat checks"
    return True, "Eligible for promotion"


# ---------------------------------------------------------------------------
# BH80 Regression Policy Reference (not enforced here, just recorded)
# ---------------------------------------------------------------------------

BH80_REGRESSION_POLICY = {
    "frozen_baseline": 80,
    "clean_gate": 80,
    "preferred_expansion_gate": 75,
    "strong_gate": 72,
    "minimal_gate": 68,
    "critical_threshold": 68,
    "policy": "Any drop below 80/80 requires explanation. Below 72/80 blocks expansion. Below 68/80 is critical.",
}