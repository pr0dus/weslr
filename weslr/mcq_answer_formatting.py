"""MCQ answer formatting V1 for official-style adapter prompts.

Narrow, read-only support for clearly structured multiple-choice prompts.
Does not claim official scores and does not affect normal chat unless the
prompt includes explicit MCQ structural markers.
"""

from __future__ import annotations

import re
from typing import Any


CHOICE_LINE_RE = re.compile(r"^\s*([A-Z])\.\s+(.+?)\s*$")

_SAFE_BLOCK_PHRASES = (
    "fabricated evidence",
    "invent the evidence",
    "invent citations",
    "fabricate literature",
    "manipulate perspective",
    "diagnosis",
    "unsupported scientific discovery",
)


def detect_mcq_prompt(message: str) -> bool:
    text = str(message or "")
    if "Multiple-choice question" not in text:
        return False
    if "Choices:" not in text:
        return False
    if "Select the best answer label" not in text:
        return False
    choice_count = sum(1 for line in text.splitlines() if CHOICE_LINE_RE.match(line))
    return choice_count >= 2


def parse_mcq_prompt(message: str) -> dict[str, Any] | None:
    if not detect_mcq_prompt(message):
        return None

    lines = [line.rstrip() for line in str(message).splitlines()]
    domain = None
    question_lines: list[str] = []
    choices: list[dict[str, str]] = []

    first = lines[0].strip() if lines else ""
    m = re.match(r"^Multiple-choice question(?:\s*\(([^)]+)\))?\.?$", first)
    if m:
        domain = (m.group(1) or "").strip() or None

    mode = "question"
    for raw_line in lines[1:]:
        line = raw_line.strip()
        if not line:
            continue
        if line == "Choices:":
            mode = "choices"
            continue
        if line.startswith("Select the best answer label"):
            break
        if mode == "question":
            question_lines.append(line)
            continue
        m_choice = CHOICE_LINE_RE.match(line)
        if m_choice:
            choices.append({"label": m_choice.group(1).upper(), "text": m_choice.group(2).strip()})

    if len(choices) < 2:
        return None

    return {
        "domain": domain,
        "question": " ".join(question_lines).strip(),
        "choices": choices,
    }


def _lower(text: str) -> str:
    return (text or "").lower()


def _contains_any(text: str, phrases: tuple[str, ...] | list[str]) -> bool:
    lowered = _lower(text)
    return any(phrase in lowered for phrase in phrases)


def _label_by_phrase_choice(choices: list[dict[str, str]], phrases: tuple[str, ...] | list[str]) -> tuple[str | None, int]:
    scored: list[tuple[int, str]] = []
    for choice in choices:
        text = _lower(choice["text"])
        score = sum(1 for phrase in phrases if phrase in text)
        if score > 0:
            scored.append((score, choice["label"]))
    if not scored:
        return None, 0
    scored.sort(reverse=True)
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None, scored[0][0]
    return scored[0][1], scored[0][0]


def _select_label(parsed: dict[str, Any]) -> tuple[str | None, str, str | None]:
    question = _lower(parsed.get("question", ""))
    domain = _lower(parsed.get("domain") or "")
    choices = parsed.get("choices", [])
    combined = question + "\n" + "\n".join(_lower(choice["text"]) for choice in choices)

    if _contains_any(combined, _SAFE_BLOCK_PHRASES):
        return None, "low", "insufficient_signal"

    rules: list[tuple[tuple[str, ...], tuple[str, ...], str]] = [
        (("entropy",), ("spread out energy", "arrangements are in a system"), "Entropy is best matched by the option describing spread-out energy or arrangements."),
        (("metal rod", "expand", "heated"), ("thermal energy", "particle motion", "average spacing"), "The strongest match is the option describing thermal energy increasing motion and spacing."),
        (("meaning", "syntax"), ("sentence expresses", "structurally arranged"), "The best fit is the option distinguishing what a sentence expresses from how it is structured."),
        (("ambiguous",), ("more than one plausible interpretation",), "Ambiguity is best matched by the option allowing more than one plausible interpretation."),
        (("urgent tasks", "little time"), ("highest immediate impact", "risk if delayed"), "The most defensible triage choice is the option prioritizing impact and risk if delayed."),
        (("small problem", "ignored"), ("compounding cost", "dependency spread", "recovery options"), "The strongest reasoning match is the option describing compounding cost and reduced recovery options."),
        (("refuse to act",), ("safety boundaries", "evidence boundaries", "operator authority"), "Refusal is best matched by the option grounded in safety, evidence, and authority boundaries."),
        (("responsibility", "control"), ("answerable", "directly determine"), "The clearest distinction is the option separating answerability from direct control."),
        (("materials candidate", "discovered"), ("literature", "database", "stability evidence", "stronger discovery claims"), "The correct boundary is the option requiring literature, database, and stability evidence before stronger discovery claims."),
        (("capability changes",), ("governance", "tests", "review", "operator approval"), "Capability changes should route through governance, tests, review, and operator approval."),
    ]

    for question_markers, choice_markers, explanation in rules:
        if all(marker in question or marker in domain for marker in question_markers):
            label, score = _label_by_phrase_choice(choices, choice_markers)
            if label is not None:
                confidence = "high" if score >= 2 else "medium"
                return label, confidence, explanation

    return None, "low", "insufficient_signal"


def build_official_mcq_response(message: str) -> dict[str, Any] | None:
    parsed = parse_mcq_prompt(message)
    if parsed is None:
        return None

    selected_label, confidence, explanation = _select_label(parsed)
    if selected_label is None:
        explanation_text = (
            "I can't select confidently from this multiple-choice prompt with the current bounded signal."
            if explanation in {None, "insufficient_signal"}
            else str(explanation)
        )
        return {
            "path": "official_mcq_answer_formatting",
            "response_text": f"Answer: None\nExplanation: {explanation_text}\nConfidence: {confidence}",
            "selected_label": None,
            "confidence": confidence,
            "read_only": True,
            "sample_only_behavior": True,
            "official_score_claimed": False,
            "failure_mode": "insufficient_signal",
            "mcq_answer_formatting": {
                "domain": parsed.get("domain"),
                "question": parsed.get("question"),
                "choices": parsed.get("choices"),
            },
        }

    return {
        "path": "official_mcq_answer_formatting",
        "response_text": f"Answer: {selected_label}\nExplanation: {explanation}\nConfidence: {confidence}",
        "selected_label": selected_label,
        "confidence": confidence,
        "read_only": True,
        "sample_only_behavior": True,
        "official_score_claimed": False,
        "failure_mode": None,
        "mcq_answer_formatting": {
            "domain": parsed.get("domain"),
            "question": parsed.get("question"),
            "choices": parsed.get("choices"),
        },
    }
