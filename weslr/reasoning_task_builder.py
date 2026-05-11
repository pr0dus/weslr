from __future__ import annotations

import hashlib
from dataclasses import asdict, is_dataclass
from typing import Any

from weslr.reasoning_task import (
    AntiGamingRecord,
    ChoiceRepresentation,
    FailureRecord,
    ParsedReasoningTask,
    ReasoningTask,
    ReasoningTaskInput,
    ReasoningTaskProvenance,
    create_empty_reasoning_task,
    validate_reasoning_task,
)
from weslr.solver_registry import create_empty_solver_registry, list_candidate_solvers


REQUIRED_ITEM_FIELDS = [
    "id",
    "benchmark_family",
    "domain",
    "question",
    "choices",
    "required_skill",
    "explanation_required",
]


def fingerprint_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _to_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return {
            key: val
            for key, val in vars(value).items()
            if not key.startswith("_") and not callable(val)
        }
    result: dict[str, Any] = {}
    for name in REQUIRED_ITEM_FIELDS:
        if hasattr(value, name):
            result[name] = getattr(value, name)
    return result


def normalize_mcq_item(item: Any) -> dict[str, Any]:
    data = _to_mapping(item)
    missing = [field for field in REQUIRED_ITEM_FIELDS if field not in data]
    if missing:
        raise ValueError(f"mcq item missing required fields: {', '.join(missing)}")
    return data


def normalize_suite_metadata(metadata: Any) -> dict[str, Any]:
    return _to_mapping(metadata)


def _normalize_choice(choice: Any) -> dict[str, Any]:
    data = _to_mapping(choice)
    if isinstance(choice, str):
        return {"label": choice, "text": choice}
    if "label" not in data:
        if "id" in data:
            data["label"] = data["id"]
        elif "key" in data:
            data["label"] = data["key"]
    if "text" not in data:
        if "content" in data:
            data["text"] = data["content"]
        elif "value" in data:
            data["text"] = data["value"]
    return data


def build_reasoning_task_from_mcq_item(
    item: Any,
    suite_metadata: Any = None,
    *,
    store_raw_question: bool = False,
) -> ReasoningTask:
    normalized_item = normalize_mcq_item(item)
    metadata = normalize_suite_metadata(suite_metadata)

    question_text = str(normalized_item.get("question", ""))
    question_fingerprint = fingerprint_text(question_text)
    stable_identity = "|".join(
        [
            str(normalized_item.get("id", "")),
            str(normalized_item.get("benchmark_family", "")),
            str(normalized_item.get("domain", "")),
            question_text,
        ]
    )
    item_fingerprint = fingerprint_text(stable_identity)

    task = create_empty_reasoning_task(
        task_id=str(normalized_item.get("id", "")),
        task_family=str(normalized_item.get("benchmark_family", "")),
        domain=str(normalized_item.get("domain", "")),
        required_skill=str(normalized_item.get("required_skill", "")),
    )

    task.provenance = ReasoningTaskProvenance(
        source_eval="official_mcq_adapter_v0",
        dataset_name=str(metadata.get("dataset_name", "")),
        subset_name=str(metadata.get("subset_name", "")),
        official_score=False,
        internal_eval=bool(metadata.get("internal_eval", True)),
        sample_only=bool(metadata.get("sample_only", False)),
        item_fingerprint=item_fingerprint,
        adapter_version=str(metadata.get("adapter_version", "official_mcq_adapter_v0")),
        prompt_format_version=str(metadata.get("prompt_format_version", "official_mcq_prompt_v1")),
    )

    input_choices: list[dict[str, Any]] = []
    choice_representations: list[ChoiceRepresentation] = []
    for raw_choice in normalized_item.get("choices", []):
        choice = _normalize_choice(raw_choice)
        label = str(choice.get("label", ""))
        text = str(choice.get("text", ""))
        input_choice = {"label": label}
        if store_raw_question:
            input_choice["text"] = text
        else:
            input_choice["text_fingerprint"] = fingerprint_text(text)
        input_choices.append(input_choice)
        choice_representations.append(
            ChoiceRepresentation(
                label=label,
                claims=[] if not store_raw_question else [],
                implied_assumptions=[],
                supports=[],
                violations=[],
                uncertainties=[],
            )
        )

    task.input = ReasoningTaskInput(
        question_text=question_text if store_raw_question else "",
        question_fingerprint=question_fingerprint,
        choices=input_choices,
    )
    task.parsed = ParsedReasoningTask(
        task_type="multiple_choice_reasoning",
        question_intent="select_best_answer",
        premises=[],
        conclusion_candidates=[],
        constraints=[],
        assumptions=[],
        entities=[],
        relations=[],
    )
    task.choice_representations = choice_representations

    registry = create_empty_solver_registry()
    candidates = list_candidate_solvers(
        registry,
        task_type="multiple_choice_reasoning",
        domain=task.domain,
        required_skill=task.required_skill,
    )
    task.solver_plan.candidate_solvers = [solver.solver_id for solver in candidates]
    task.solver_plan.selected_solvers = []
    task.solver_plan.blocked_solvers = []

    task.anti_gaming = AntiGamingRecord(
        uses_item_id=False,
        uses_answer_key=False,
        uses_answer_position_bias=False,
        stores_raw_question_by_default=False,
        official_score_claimed=False,
    )
    task.failure = FailureRecord(
        failure_mode="",
        missing_skill="",
        target_substrate="",
        enrichment_record_allowed=True,
    )

    return task


def validate_built_reasoning_task(task: ReasoningTask) -> list[str]:
    return validate_reasoning_task(task)


__all__ = [
    "build_reasoning_task_from_mcq_item",
    "fingerprint_text",
    "normalize_mcq_item",
    "normalize_suite_metadata",
    "validate_built_reasoning_task",
]
