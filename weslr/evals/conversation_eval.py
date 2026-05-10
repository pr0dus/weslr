"""Conversation Evaluation Suite V1.

File-based deterministic conversation scoring for WESLR.

Purpose:
- protect a lower-bound non-degradation floor
- save suite results for regression comparison
- provide a future gate for cognitive auto-refinement

This module does not call external providers, mutate memory, execute tools, or
change WESLR behavior. It scores supplied responses against saved suite rules.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Iterable
import json
import time


Responder = Callable[[str, list[dict[str, str]]], str]


@dataclass
class TurnScore:
    turn_index: int
    user: str
    response: str
    score: float
    passed: bool
    missing_required: list[str]
    forbidden_present: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SuiteResult:
    suite_id: str
    suite_name: str
    minimum_score: float
    score: float
    passed: bool
    turn_scores: list[TurnScore]
    created_at: float

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["turn_scores"] = [t.to_dict() for t in self.turn_scores]
        return data


def load_suite(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _lower(text: str) -> str:
    return (text or "").lower()


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def score_turn(response: str, turn: dict[str, Any], suite_defaults: dict[str, Any] | None = None, turn_index: int = 0) -> TurnScore:
    """Score one response deterministically against required/forbidden snippets."""

    defaults = suite_defaults or {}
    required = _as_list(defaults.get("must_include")) + _as_list(turn.get("must_include"))
    forbidden = _as_list(defaults.get("must_not_include")) + _as_list(turn.get("must_not_include"))
    response_l = _lower(response)

    missing_required = [item for item in required if _lower(item) not in response_l]
    forbidden_present = [item for item in forbidden if _lower(item) in response_l]

    total_checks = len(required) + len(forbidden)
    if total_checks == 0:
        score = 1.0 if response.strip() else 0.0
    else:
        passed_checks = (len(required) - len(missing_required)) + (len(forbidden) - len(forbidden_present))
        score = max(0.0, min(1.0, passed_checks / total_checks))

    min_turn_score = float(turn.get("minimum_score", defaults.get("minimum_turn_score", 1.0)))
    passed = score >= min_turn_score and not forbidden_present

    notes: list[str] = []
    if missing_required:
        notes.append("missing required snippets")
    if forbidden_present:
        notes.append("forbidden snippets present")
    if not response.strip():
        notes.append("empty response")

    return TurnScore(
        turn_index=turn_index,
        user=str(turn.get("user", "")),
        response=response,
        score=score,
        passed=passed,
        missing_required=missing_required,
        forbidden_present=forbidden_present,
        notes=notes,
    )


def evaluate_suite(suite: dict[str, Any], responder: Responder) -> SuiteResult:
    """Run a suite against a responder.

    The responder receives `(user_message, history)` and returns text.
    History contains previous user/assistant turns as dicts.
    """

    suite_id = str(suite.get("id") or suite.get("suite") or "unknown_suite")
    suite_name = str(suite.get("name") or suite_id)
    minimum_score = float(suite.get("minimum_score", 0.85))
    defaults = {
        "must_include": suite.get("must_include", []),
        "must_not_include": suite.get("must_not_include", []),
        "minimum_turn_score": suite.get("minimum_turn_score", 1.0),
    }

    history: list[dict[str, str]] = []
    turn_scores: list[TurnScore] = []

    for idx, turn in enumerate(suite.get("turns", [])):
        user_msg = str(turn.get("user", ""))
        response = responder(user_msg, history)
        score = score_turn(response, turn, defaults, idx)
        turn_scores.append(score)
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": response})

    overall = sum(t.score for t in turn_scores) / len(turn_scores) if turn_scores else 0.0
    passed = overall >= minimum_score and all(t.passed for t in turn_scores)

    return SuiteResult(
        suite_id=suite_id,
        suite_name=suite_name,
        minimum_score=minimum_score,
        score=overall,
        passed=passed,
        turn_scores=turn_scores,
        created_at=time.time(),
    )


def evaluate_suite_file(path: str | Path, responder: Responder) -> SuiteResult:
    return evaluate_suite(load_suite(path), responder)


def save_result(result: SuiteResult, output_dir: str | Path) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{result.suite_id}.result.json"
    with open(target, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
    return target


def compare_to_baseline(result: SuiteResult, baseline_path: str | Path) -> tuple[bool, list[str]]:
    """Return whether result is non-degraded against a saved baseline."""

    path = Path(baseline_path)
    if not path.exists():
        return True, ["baseline not found; comparison skipped"]

    with open(path, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    baseline_score = float(baseline.get("score", 0.0))
    reasons: list[str] = []

    if result.score < baseline_score:
        reasons.append(f"score degraded: {result.score:.3f} < baseline {baseline_score:.3f}")

    if baseline.get("passed") is True and result.passed is False:
        reasons.append("baseline passed but current result failed")

    return len(reasons) == 0, reasons


def deterministic_public_demo_responder(message: str, _history: list[dict[str, str]]) -> str:
    """Default local responder for public-demo suites."""

    from weslr.public_demo_chat import public_demo_chat

    return str(public_demo_chat(message).get("reply", ""))


def interpretation_responder(message: str, _history: list[dict[str, str]]) -> str:
    """Route evaluation turns through WESLR interpretation without side effects."""

    from interpretation import interpret_human_turn

    result = interpret_human_turn(message)
    if isinstance(result, dict):
        response_text = result.get("response_text")
        if isinstance(response_text, str) and response_text:
            return response_text
        message_value = result.get("message")
        if isinstance(message_value, str) and message_value:
            return message_value
    return str(result)


def iter_suite_files(root: str | Path) -> Iterable[Path]:
    """Return all suite JSON files under root, including nested suite groups."""

    path = Path(root)
    if not path.exists():
        return []
    return sorted(path.rglob("*.json"))
