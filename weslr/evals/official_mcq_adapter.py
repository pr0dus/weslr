"""Official-style multiple-choice adapter V0.

Local-only evaluation harness for MMLU/GPQA-style multiple-choice tasks.
This module does not download official datasets, claim official scores, or
change WESLR runtime behavior.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from interpretation import interpret_human_turn
from weslr.evals.public_subset_schema_v1 import build_run_provenance, validate_suite_metadata


VALID_BENCHMARK_FAMILY = "mmlu_gpqa_style"
LABEL_RE = re.compile(r"\b(?:answer|choice|selected answer|selected)\s*[:\-]?\s*\(?([A-Z])\)?\b", re.IGNORECASE)
PAREN_LABEL_RE = re.compile(r"\(([A-Z])\)")
SINGLE_LABEL_LINE_RE = re.compile(r"^\s*([A-Z])\s*$")
ADAPTER_VERSION = "official_mcq_adapter_v0"
PROMPT_FORMAT_VERSION = "official_mcq_prompt_v1"


@dataclass
class Choice:
    label: str
    text: str


@dataclass
class MCQItem:
    id: str
    benchmark_family: str
    domain: str
    question: str
    choices: list[Choice]
    answer_label: str
    required_skill: str
    explanation_required: bool


@dataclass
class MCQResult:
    id: str
    domain: str
    benchmark_family: str
    required_skill: str
    question: str
    selected_label: str | None
    answer_label: str
    correct: bool
    confidence: float | None
    uncertainty: str | None
    failure_mode: str | None
    explanation: str
    response_path: str | None
    official_score: bool
    sample_only: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MCQRunSummary:
    suite_id: str
    sample_only: bool
    official_score: bool
    internal_eval: bool
    metadata: dict[str, Any]
    run_provenance: dict[str, Any]
    total: int
    accuracy: float
    answered_count: int
    no_answer_count: int
    average_confidence: float | None
    failure_modes: dict[str, int]
    results: list[MCQResult]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["results"] = [r.to_dict() for r in self.results]
        return data


def _load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate_choice(raw: Any, item_id: str) -> Choice:
    _require(isinstance(raw, dict), f"Choice in {item_id} must be an object.")
    label = str(raw.get("label", "")).strip().upper()
    text = str(raw.get("text", "")).strip()
    _require(bool(label) and len(label) == 1 and label.isalpha(), f"Choice label in {item_id} must be a single letter.")
    _require(bool(text), f"Choice text in {item_id} must be non-empty.")
    return Choice(label=label, text=text)


def _validate_item(raw: Any) -> MCQItem:
    _require(isinstance(raw, dict), "Each suite item must be an object.")
    item_id = str(raw.get("id", "")).strip()
    _require(bool(item_id), "Each suite item must have an id.")
    benchmark_family = str(raw.get("benchmark_family", "")).strip()
    _require(benchmark_family == VALID_BENCHMARK_FAMILY, f"{item_id} benchmark_family must be {VALID_BENCHMARK_FAMILY!r}.")
    domain = str(raw.get("domain", "")).strip()
    question = str(raw.get("question", "")).strip()
    required_skill = str(raw.get("required_skill", "")).strip()
    explanation_required = bool(raw.get("explanation_required", False))
    _require(bool(domain), f"{item_id} domain is required.")
    _require(bool(question), f"{item_id} question is required.")
    _require(bool(required_skill), f"{item_id} required_skill is required.")

    raw_choices = raw.get("choices")
    _require(isinstance(raw_choices, list) and len(raw_choices) >= 2, f"{item_id} choices must be a list with at least 2 entries.")
    choices = [_validate_choice(choice, item_id) for choice in raw_choices]
    labels = [choice.label for choice in choices]
    _require(len(set(labels)) == len(labels), f"{item_id} choice labels must be unique.")

    answer_label = str(raw.get("answer_label", "")).strip().upper()
    _require(answer_label in set(labels), f"{item_id} answer_label must match one of the choice labels.")

    return MCQItem(
        id=item_id,
        benchmark_family=benchmark_family,
        domain=domain,
        question=question,
        choices=choices,
        answer_label=answer_label,
        required_skill=required_skill,
        explanation_required=explanation_required,
    )


def load_suite(path: str | Path) -> dict[str, Any]:
    suite = _load_json(path)
    _require(isinstance(suite, dict), "Suite must be a JSON object.")
    metadata = validate_suite_metadata(suite)

    items = suite.get("items")
    _require(isinstance(items, list) and items, "Suite must contain a non-empty items list.")
    validated = [_validate_item(item) for item in items]

    metadata.setdefault("adapter_version", ADAPTER_VERSION)
    metadata.setdefault("prompt_format_version", PROMPT_FORMAT_VERSION)
    metadata["suite_size"] = len(validated)

    return {
        "suite_id": metadata["suite_id"],
        "sample_only": metadata["sample_only"],
        "official_score": metadata["official_score"],
        "internal_eval": metadata.get("internal_eval", False),
        "metadata": metadata,
        "items": validated,
    }


def build_prompt(item: MCQItem) -> str:
    lines = [
        f"Multiple-choice question ({item.domain}).",
        item.question,
        "Choices:",
    ]
    for choice in item.choices:
        lines.append(f"{choice.label}. {choice.text}")
    lines.append("Select the best answer label and explain briefly.")
    return "\n".join(lines)


def _extract_confidence(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    mapping = {
        "high": 0.85,
        "medium": 0.6,
        "low": 0.35,
    }
    return mapping.get(str(value).strip().lower())


def extract_selected_label(response_text: str, choices: list[Choice]) -> str | None:
    text = str(response_text or "")
    upper_text = text.upper()
    labels = {choice.label for choice in choices}

    m = LABEL_RE.search(text)
    if m:
        candidate = m.group(1).upper()
        if candidate in labels:
            return candidate

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:2]:
        m = SINGLE_LABEL_LINE_RE.match(line.upper())
        if m and m.group(1) in labels:
            return m.group(1)

    paren_hits = [m.group(1) for m in PAREN_LABEL_RE.finditer(upper_text) if m.group(1) in labels]
    if len(set(paren_hits)) == 1:
        return paren_hits[0]

    matching_choices = []
    lowered = text.lower()
    for choice in choices:
        choice_text = choice.text.strip().lower()
        if len(choice_text) >= 10 and choice_text in lowered:
            matching_choices.append(choice.label)
    if len(matching_choices) == 1:
        return matching_choices[0]

    return None


def _uncertainty_label(confidence: float | None, selected_label: str | None) -> str | None:
    if selected_label is None:
        return "high"
    if confidence is None:
        return "unknown"
    if confidence >= 0.75:
        return "low"
    if confidence >= 0.5:
        return "medium"
    return "high"


def _get_repo_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        commit = result.stdout.strip()
        return commit or None
    except Exception:
        return None


def run_item(item: MCQItem, sample_only: bool, official_score: bool) -> MCQResult:
    result = interpret_human_turn(build_prompt(item))
    response_text = str(result.get("response_text") or "") if isinstance(result, dict) else str(result)
    selected_label = extract_selected_label(response_text, item.choices)
    confidence = _extract_confidence(result.get("confidence")) if isinstance(result, dict) else None
    failure_mode = None
    if selected_label is None:
        failure_mode = "no_answer_selection"
    correct = selected_label == item.answer_label if selected_label is not None else False

    return MCQResult(
        id=item.id,
        domain=item.domain,
        benchmark_family=item.benchmark_family,
        required_skill=item.required_skill,
        question=item.question,
        selected_label=selected_label,
        answer_label=item.answer_label,
        correct=correct,
        confidence=confidence,
        uncertainty=_uncertainty_label(confidence, selected_label),
        failure_mode=failure_mode,
        explanation=response_text,
        response_path=result.get("path") if isinstance(result, dict) else None,
        official_score=official_score,
        sample_only=sample_only,
    )


def run_suite(suite_path: str | Path) -> MCQRunSummary:
    suite = load_suite(suite_path)
    results = [run_item(item, suite["sample_only"], suite["official_score"]) for item in suite["items"]]
    total = len(results)
    answered_count = sum(1 for r in results if r.selected_label is not None)
    no_answer_count = sum(1 for r in results if r.selected_label is None)
    correct_count = sum(1 for r in results if r.correct)
    confidence_values = [r.confidence for r in results if r.confidence is not None]
    average_confidence = round(sum(confidence_values) / len(confidence_values), 3) if confidence_values else None

    failure_counter = Counter()
    for result in results:
        if result.failure_mode:
            failure_counter[result.failure_mode] += 1

    metadata = dict(suite.get("metadata", {}))
    metadata.setdefault("suite_id", suite["suite_id"])
    metadata.setdefault("official_score", suite["official_score"])
    metadata.setdefault("sample_only", suite["sample_only"])
    metadata.setdefault("internal_eval", suite.get("internal_eval", False))
    metadata.setdefault("adapter_version", ADAPTER_VERSION)
    metadata.setdefault("prompt_format_version", PROMPT_FORMAT_VERSION)

    repo_commit = _get_repo_commit()
    run_provenance = build_run_provenance(metadata, repo_commit=repo_commit)

    return MCQRunSummary(
        suite_id=suite["suite_id"],
        sample_only=suite["sample_only"],
        official_score=suite["official_score"],
        internal_eval=suite.get("internal_eval", False),
        metadata=metadata,
        run_provenance=run_provenance,
        total=total,
        accuracy=round(correct_count / total, 3) if total else 0.0,
        answered_count=answered_count,
        no_answer_count=no_answer_count,
        average_confidence=average_confidence,
        failure_modes=dict(sorted(failure_counter.items())),
        results=results,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local official-style multiple-choice adapter.")
    parser.add_argument("--suite", required=True, help="Path to a local JSON suite.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args(argv)

    summary = run_suite(args.suite)
    payload = summary.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"suite_id: {summary.suite_id}")
        print(f"sample_only: {summary.sample_only}")
        print(f"official_score: {summary.official_score}")
        print(f"internal_eval: {summary.internal_eval}")
        print(f"total: {summary.total}")
        print(f"accuracy: {summary.accuracy}")
        print(f"answered_count: {summary.answered_count}")
        print(f"no_answer_count: {summary.no_answer_count}")
        print(f"average_confidence: {summary.average_confidence}")
        print(f"failure_modes: {json.dumps(summary.failure_modes, ensure_ascii=False)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
