from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import Any


@dataclass
class ReasoningTaskProvenance:
    source_eval: str = ""
    dataset_name: str = ""
    subset_name: str = ""
    official_score: bool = False
    internal_eval: bool = True
    sample_only: bool = False
    item_fingerprint: str = ""
    adapter_version: str = ""
    prompt_format_version: str = ""


@dataclass
class ReasoningTaskInput:
    question_text: str = ""
    question_fingerprint: str = ""
    choices: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ParsedReasoningTask:
    task_type: str = ""
    question_intent: str = ""
    premises: list[str] = field(default_factory=list)
    conclusion_candidates: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    relations: list[str] = field(default_factory=list)


@dataclass
class ChoiceRepresentation:
    label: str = ""
    claims: list[str] = field(default_factory=list)
    implied_assumptions: list[str] = field(default_factory=list)
    supports: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)


@dataclass
class ReasoningBlackboard:
    hypotheses: list[str] = field(default_factory=list)
    inferences: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    solver_outputs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SolverPlan:
    candidate_solvers: list[str] = field(default_factory=list)
    selected_solvers: list[str] = field(default_factory=list)
    blocked_solvers: list[str] = field(default_factory=list)


@dataclass
class ArbitrationRecord:
    selected_answer: str = ""
    confidence: str = ""
    uncertainty: str = ""
    conflict_status: str = ""
    why_selected: list[str] = field(default_factory=list)
    why_rejected: list[str] = field(default_factory=list)


@dataclass
class LegibilityRecord:
    human_explanation: str = ""
    reasoning_trace_summary: str = ""
    symbolic_forms_translated: bool = True
    private_authority_used: bool = False


@dataclass
class AntiGamingRecord:
    uses_item_id: bool = False
    uses_answer_key: bool = False
    uses_answer_position_bias: bool = False
    stores_raw_question_by_default: bool = False
    official_score_claimed: bool = False


@dataclass
class FailureRecord:
    failure_mode: str = ""
    missing_skill: str = ""
    target_substrate: str = ""
    enrichment_record_allowed: bool = True


@dataclass
class ReasoningTask:
    schema_version: str
    task_id: str
    task_family: str
    domain: str
    required_skill: str
    provenance: ReasoningTaskProvenance
    input: ReasoningTaskInput
    parsed: ParsedReasoningTask
    choice_representations: list[ChoiceRepresentation]
    blackboard: ReasoningBlackboard
    solver_plan: SolverPlan
    arbitration: ArbitrationRecord
    legibility: LegibilityRecord
    anti_gaming: AntiGamingRecord
    failure: FailureRecord


def create_empty_reasoning_task(
    *,
    task_id: str = "",
    task_family: str = "",
    domain: str = "",
    required_skill: str = "",
    schema_version: str = "1.0",
) -> ReasoningTask:
    return ReasoningTask(
        schema_version=schema_version,
        task_id=task_id,
        task_family=task_family,
        domain=domain,
        required_skill=required_skill,
        provenance=ReasoningTaskProvenance(),
        input=ReasoningTaskInput(),
        parsed=ParsedReasoningTask(),
        choice_representations=[],
        blackboard=ReasoningBlackboard(),
        solver_plan=SolverPlan(),
        arbitration=ArbitrationRecord(),
        legibility=LegibilityRecord(),
        anti_gaming=AntiGamingRecord(),
        failure=FailureRecord(),
    )


def reasoning_task_to_dict(task: ReasoningTask) -> dict[str, Any]:
    return asdict(task)


def reasoning_task_from_dict(data: dict[str, Any]) -> ReasoningTask:
    return ReasoningTask(
        schema_version=data.get("schema_version", ""),
        task_id=data.get("task_id", ""),
        task_family=data.get("task_family", ""),
        domain=data.get("domain", ""),
        required_skill=data.get("required_skill", ""),
        provenance=ReasoningTaskProvenance(**data.get("provenance", {})),
        input=ReasoningTaskInput(**data.get("input", {})),
        parsed=ParsedReasoningTask(**data.get("parsed", {})),
        choice_representations=[
            ChoiceRepresentation(**item) for item in data.get("choice_representations", [])
        ],
        blackboard=ReasoningBlackboard(**data.get("blackboard", {})),
        solver_plan=SolverPlan(**data.get("solver_plan", {})),
        arbitration=ArbitrationRecord(**data.get("arbitration", {})),
        legibility=LegibilityRecord(**data.get("legibility", {})),
        anti_gaming=AntiGamingRecord(**data.get("anti_gaming", {})),
        failure=FailureRecord(**data.get("failure", {})),
    )


def _missing_fields(obj: Any, expected: list[str], prefix: str) -> list[str]:
    missing: list[str] = []
    for name in expected:
        if not hasattr(obj, name):
            missing.append(f"missing {prefix} field: {name}")
    return missing


def validate_reasoning_task(task: ReasoningTask) -> list[str]:
    messages: list[str] = []

    top_level_fields = [
        "schema_version",
        "task_id",
        "task_family",
        "domain",
        "required_skill",
        "provenance",
        "input",
        "parsed",
        "choice_representations",
        "blackboard",
        "solver_plan",
        "arbitration",
        "legibility",
        "anti_gaming",
        "failure",
    ]
    provenance_fields = [
        "source_eval",
        "dataset_name",
        "subset_name",
        "official_score",
        "internal_eval",
        "sample_only",
        "item_fingerprint",
        "adapter_version",
        "prompt_format_version",
    ]

    messages.extend(_missing_fields(task, top_level_fields, "top-level"))

    provenance = getattr(task, "provenance", None)
    if provenance is None:
        messages.append("missing top-level field: provenance")
    else:
        messages.extend(_missing_fields(provenance, provenance_fields, "provenance"))
        if getattr(provenance, "official_score", False):
            messages.append("official_score true is not allowed for ReasoningTask internal schema")

    anti_gaming = getattr(task, "anti_gaming", None)
    if anti_gaming is not None:
        if getattr(anti_gaming, "official_score_claimed", False):
            messages.append("official_score_claimed true is not allowed")
        if getattr(anti_gaming, "uses_answer_key", False):
            messages.append("uses_answer_key true is not allowed")
        if getattr(anti_gaming, "uses_item_id", False):
            messages.append("uses_item_id true is not allowed")
        if getattr(anti_gaming, "stores_raw_question_by_default", False):
            messages.append("stores_raw_question_by_default true is not allowed")

    legibility = getattr(task, "legibility", None)
    if legibility is not None and getattr(legibility, "private_authority_used", False):
        messages.append("private_authority_used true is not allowed")

    return messages


__all__ = [
    "ReasoningTask",
    "ReasoningTaskProvenance",
    "ReasoningTaskInput",
    "ParsedReasoningTask",
    "ChoiceRepresentation",
    "ReasoningBlackboard",
    "SolverPlan",
    "ArbitrationRecord",
    "LegibilityRecord",
    "AntiGamingRecord",
    "FailureRecord",
    "create_empty_reasoning_task",
    "reasoning_task_to_dict",
    "reasoning_task_from_dict",
    "validate_reasoning_task",
]
