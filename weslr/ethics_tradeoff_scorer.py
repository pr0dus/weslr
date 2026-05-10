from __future__ import annotations

"""General ethics_tradeoff_reasoning scorer helper.

This module scores provided MCQ choices against the general ethics tradeoff rubric.
It is intentionally inspectable and anti-gaming. It does not wire into runtime
answering, routing, or benchmark flows.
"""

from copy import deepcopy
import re
from typing import Any

from weslr.ethics_tradeoff_rubric import (
    get_anti_gaming_boundaries,
    get_ethics_tradeoff_rubric,
)


_POSITIVE_FAMILIES = {
    "stakeholders": ["stakeholder", "affected party", "affected parties", "affected people", "workers", "customers", "community", "communities", "people affected"],
    "harm_reduction": ["reduce harm", "avoid harm", "minimize harm", "prevent harm", "unjustified harm", "mitigate harm", "reduce risk", "avoid damage"],
    "duties_rights_obligations": ["duty", "duties", "right", "rights", "obligation", "obligations", "responsibility", "responsibilities", "consent", "fairness"],
    "evidence_boundaries": ["evidence", "supported", "support", "uncertain", "unknown", "not enough evidence", "based on evidence", "inference"],
    "authority_governance": ["authority", "governance", "review", "approval", "policy", "oversight", "escalate", "compliance", "board", "operator"],
    "reversibility": ["reversible", "reversibility", "undo", "hard to undo", "difficult to reverse", "can be reversed"],
    "time_effects": ["short-term", "short term", "long-term", "long term", "immediate", "durable", "future effects", "long run"],
    "uncertainty": ["uncertain", "uncertainty", "may", "might", "depends", "not fully known", "requires more evidence"],
}

_NEGATIVE_FAMILIES = {
    "ignore_affected_parties": ["only profit matters", "ignore stakeholders", "ignore affected parties", "others do not matter", "affected parties do not matter"],
    "unjustified_harm": ["harm is acceptable without evidence", "cause harm if useful", "justify harm without evidence", "damage is fine without proof"],
    "absolute_certainty": ["always", "never", "certainly", "guaranteed", "without question", "undeniably"],
    "legality_ethics_confusion": ["legal so ethical", "if it is legal it is ethical", "legality alone", "lawful therefore moral"],
    "bypass_governance": ["bypass governance", "skip review", "ignore oversight", "avoid approval", "without approval", "no need for review", "no need for oversight"],
    "manipulation": ["manipulate stakeholders", "deceive", "mislead", "pressure them", "hide the truth", "coerce"],
    "benefits_override_rights": ["benefits override rights", "profit overrides rights", "rights do not matter if benefits are high", "outcomes justify violating rights"],
    "hide_uncertainty": ["pretend certainty", "hide uncertainty", "do not mention uncertainty", "act certain without support"],
    "benchmark_tricks": ["benchmark trick", "test-taking trick", "pick c by default", "option b is usually right"],
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _count_hits(text: str, patterns: list[str]) -> list[str]:
    hits: list[str] = []
    for pattern in patterns:
        if pattern in text:
            hits.append(pattern)
    return hits


def _confidence_for(best_score: float, second_score: float | None, positive_count: int) -> str:
    margin = best_score - (second_score if second_score is not None else -999)
    if best_score >= 5.0 and margin >= 2.0 and positive_count >= 3:
        return "high"
    if best_score >= 3.0 and margin >= 1.0 and positive_count >= 2:
        return "medium"
    return "low"


def explain_choice_score(choice_score: dict) -> str:
    label = choice_score.get("label")
    score = choice_score.get("score")
    pos = choice_score.get("positive_hits") or []
    neg = choice_score.get("negative_hits") or []
    return (
        f"Choice {label} scored {score:.2f} with positive hits {pos} and negative hits {neg}. "
        "This is a human-readable, rubric-based summary only."
    )


def score_ethics_tradeoff_choices(question: str, choices: list[dict]) -> dict[str, Any]:
    rubric = get_ethics_tradeoff_rubric()
    anti_gaming = get_anti_gaming_boundaries()

    normalized_question = _normalize(question)
    choice_scores: list[dict[str, Any]] = []

    for raw_choice in choices:
        label = str(raw_choice.get("label") or "").strip().upper()
        text = str(raw_choice.get("text") or "")
        normalized_text = _normalize(text)
        combined = f"{normalized_question} {normalized_text}".strip()

        positive_hits: list[str] = []
        negative_hits: list[str] = []
        score = 0.0

        for family, patterns in _POSITIVE_FAMILIES.items():
            hits = _count_hits(combined, patterns)
            if hits:
                positive_hits.extend([f"{family}:{hit}" for hit in hits])
                score += 1.25 * len(hits)

        for family, patterns in _NEGATIVE_FAMILIES.items():
            hits = _count_hits(combined, patterns)
            if hits:
                negative_hits.extend([f"{family}:{hit}" for hit in hits])
                penalty = 1.5 if family in {"bypass_governance", "benefits_override_rights", "benchmark_tricks"} else 1.25
                score -= penalty * len(hits)

        if normalized_text and "?" in text and not positive_hits:
            score -= 0.5
            negative_hits.append("low_signal:question_like_choice")

        choice_score = {
            "label": label,
            "score": round(score, 3),
            "positive_hits": positive_hits,
            "negative_hits": negative_hits,
            "explanation": "",
        }
        choice_score["explanation"] = explain_choice_score(choice_score)
        choice_scores.append(choice_score)

    sorted_scores = sorted(choice_scores, key=lambda item: (item["score"], len(item["positive_hits"]), -len(item["negative_hits"])), reverse=True)
    best = sorted_scores[0] if sorted_scores else None
    second = sorted_scores[1] if len(sorted_scores) > 1 else None

    selected_label = None
    confidence = "low"
    explanation = "insufficient rubric signal"

    if best is not None:
        best_score = float(best["score"])
        second_score = float(second["score"]) if second is not None else None
        margin = best_score - (second_score if second_score is not None else best_score)
        positive_count = len(best.get("positive_hits") or [])
        negative_count = len(best.get("negative_hits") or [])

        clear_winner = best_score > 0 and (
            second is None or margin >= 1.0 or (positive_count >= 2 and negative_count == 0 and best_score >= 2.5)
        )
        low_signal = best_score < 1.0 and positive_count < 2

        if clear_winner and not low_signal:
            selected_label = best.get("label")
            confidence = _confidence_for(best_score, second_score, positive_count)
            explanation = best.get("explanation") or "rubric-based selection"
        else:
            selected_label = None
            confidence = "low"
            explanation = "insufficient rubric signal"

    return {
        "selected_label": selected_label,
        "confidence": confidence,
        "explanation": explanation,
        "choice_scores": deepcopy(choice_scores),
        "rubric_used": rubric,
        "anti_gaming_boundaries": anti_gaming,
        "official_score_claimed": False,
    }
