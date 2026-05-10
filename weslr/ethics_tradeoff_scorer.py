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
    "stakeholders": [
        "stakeholder",
        "stakeholders",
        "affected party",
        "affected parties",
        "affected people",
        "workers",
        "customers",
        "community",
        "communities",
        "people affected",
        "shareholder and stakeholder balance",
        "public interest",
    ],
    "harm_reduction": [
        "reduce harm",
        "avoid harm",
        "minimize harm",
        "prevent harm",
        "unjustified harm",
        "mitigate harm",
        "reduce risk",
        "avoid damage",
        "protect consumers",
        "protect employees",
    ],
    "duties_rights_obligations": [
        "duty",
        "duties",
        "right",
        "rights",
        "obligation",
        "obligations",
        "responsibility",
        "responsibilities",
        "ethical responsibility",
        "fiduciary duty",
        "duty to report",
        "respect rights",
        "avoid conflicts",
        "consent",
        "informed consent",
        "fairness",
        "justice",
    ],
    "evidence_boundaries": [
        "evidence",
        "supported",
        "support",
        "uncertain",
        "unknown",
        "not enough evidence",
        "based on evidence",
        "inference",
        "transparency",
        "disclosure",
        "disclose",
    ],
    "authority_governance": [
        "authority",
        "governance",
        "review",
        "approval",
        "policy",
        "policies",
        "practice",
        "practices",
        "programme",
        "programmes",
        "program",
        "programs",
        "oversight",
        "escalate",
        "compliance",
        "audit",
        "board",
        "operator",
        "due process",
        "accountability",
    ],
    "reversibility": [
        "reversible",
        "reversibility",
        "undo",
        "hard to undo",
        "difficult to reverse",
        "can be reversed",
    ],
    "time_effects": [
        "short-term",
        "short term",
        "long-term",
        "long term",
        "immediate",
        "durable",
        "future effects",
        "long run",
        "long-term trust",
    ],
    "uncertainty": [
        "uncertain",
        "uncertainty",
        "may",
        "might",
        "depends",
        "not fully known",
        "requires more evidence",
    ],
    "business_ethics_foundations": [
        "ethical",
        "ethics",
        "business ethics",
        "ethics management",
        "corporate responsibility",
        "social responsibility",
        "corporate social responsibility",
        "csr",
        "sustainability",
        "environmental management",
        "externalities",
        "mutual dependence",
        "interdependence",
        "privacy",
        "confidentiality",
        "whistleblowing",
        "conflict of interest",
    ],
}

_NEGATIVE_FAMILIES = {
    "ignore_affected_parties": [
        "only profit matters",
        "profit only",
        "maximize profit regardless",
        "shareholder value only",
        "ignore stakeholders",
        "ignore affected parties",
        "others do not matter",
        "affected parties do not matter",
    ],
    "unjustified_harm": [
        "harm is acceptable without evidence",
        "cause harm if useful",
        "justify harm without evidence",
        "damage is fine without proof",
        "exploit",
    ],
    "absolute_certainty": [
        "always",
        "never",
        "certainly",
        "guaranteed",
        "without question",
        "undeniably",
    ],
    "legality_ethics_confusion": [
        "legal so ethical",
        "if it is legal it is ethical",
        "legality alone",
        "lawful therefore moral",
    ],
    "bypass_governance": [
        "bypass governance",
        "bypass oversight",
        "skip review",
        "ignore oversight",
        "avoid approval",
        "without approval",
        "no need for review",
        "no need for oversight",
        "suppress information",
        "cover up",
    ],
    "manipulation": [
        "manipulate",
        "manipulate stakeholders",
        "deceive",
        "deception",
        "mislead",
        "misleading",
        "hide the truth",
        "hide information",
        "conceal",
        "misrepresent",
        "coerce",
        "bribe",
        "bribery",
        "fraud",
        "corruption",
    ],
    "benefits_override_rights": [
        "benefits override rights",
        "profit overrides rights",
        "rights do not matter if benefits are high",
        "outcomes justify violating rights",
    ],
    "hide_uncertainty": [
        "pretend certainty",
        "hide uncertainty",
        "do not mention uncertainty",
        "act certain without support",
    ],
    "rights_violations": [
        "retaliation",
        "discrimination",
        "ignore conflict of interest",
        "violate privacy",
        "violate consent",
    ],
    "benchmark_tricks": [
        "benchmark trick",
        "test-taking trick",
        "pick c by default",
        "option b is usually right",
    ],
}

_CONTEXTUAL_FAMILIES = [
    {
        "name": "csr_moral_arguments",
        "question_markers": ["csr", "corporate social responsibility", "business and society", "moral arguments"],
        "positive_markers": ["externalities", "power", "mutual dependence", "interdependence"],
        "negative_markers": ["insubstantial resources"],
    },
    {
        "name": "ethics_management",
        "question_markers": ["ethical issues", "ethical issue", "policies", "practices", "programmes", "programs"],
        "positive_markers": ["ethics management", "business ethics management", "compliance", "audit", "governance"],
        "negative_markers": [],
    },
    {
        "name": "board_independence",
        "question_markers": ["independence", "non-executive", "board members", "board"],
        "positive_markers": ["outside", "limited", "independently"],
        "negative_markers": ["inside", "unlimited", "intermittently"],
    },
    {
        "name": "stakeholder_activism",
        "question_markers": ["research and communication", "physically attacking", "operations", "cso", "cso's", "csos"],
        "positive_markers": ["information campaign", "violent direct action", "indirect action", "boycott"],
        "negative_markers": [],
    },
    {
        "name": "consumer_activism",
        "question_markers": ["reward favourable behaviour", "reward favorable behavior", "campaigns", "companies"],
        "positive_markers": ["buycotts", "buycott", "boycotts", "boycott", "digital technology", "increased sales"],
        "negative_markers": ["buyalls", "blockchain technology", "charitable donations"],
    },
]


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "being",
    "by",
    "can",
    "company",
    "companies",
    "for",
    "from",
    "in",
    "include",
    "includes",
    "is",
    "it",
    "its",
    "may",
    "of",
    "on",
    "or",
    "the",
    "their",
    "there",
    "these",
    "they",
    "through",
    "to",
    "which",
    "with",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _count_hits(text: str, patterns: list[str]) -> list[str]:
    hits: list[str] = []
    for pattern in patterns:
        if pattern in text:
            hits.append(pattern)
    return hits


def _normalize_token(token: str) -> str:
    value = token.strip().lower()
    if value.endswith("ies") and len(value) > 4:
        return value[:-3] + "y"
    if value.endswith("es") and len(value) > 4:
        return value[:-2]
    if value.endswith("s") and len(value) > 3:
        return value[:-1]
    return value


def _content_tokens(text: str) -> set[str]:
    tokens = [_normalize_token(token) for token in re.findall(r"[a-zA-Z][a-zA-Z\-']+", _normalize(text))]
    return {token for token in tokens if len(token) > 2 and token not in _STOPWORDS}


def _contextual_hits(question: str, choice_text: str) -> list[str]:
    normalized_question = _normalize(question)
    normalized_choice = _normalize(choice_text)
    hits: list[str] = []

    for family in _CONTEXTUAL_FAMILIES:
        if not any(marker in normalized_question for marker in family["question_markers"]):
            continue
        for marker in family["positive_markers"]:
            if marker in normalized_choice:
                hits.append(f"context:{family['name']}:{marker}")
        for marker in family["negative_markers"]:
            if marker in normalized_choice:
                hits.append(f"context_negative:{family['name']}:{marker}")

    question_tokens = _content_tokens(question)
    choice_tokens = _content_tokens(choice_text)
    overlap = sorted(question_tokens & choice_tokens)
    for token in overlap[:3]:
        hits.append(f"context_overlap:{token}")
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

        positive_hits: list[str] = []
        negative_hits: list[str] = []
        score = 0.0

        for family, patterns in _POSITIVE_FAMILIES.items():
            hits = _count_hits(normalized_text, patterns)
            if hits:
                positive_hits.extend([f"{family}:{hit}" for hit in hits])
                score += 1.25 * len(hits)

        for family, patterns in _NEGATIVE_FAMILIES.items():
            hits = _count_hits(normalized_text, patterns)
            if hits:
                negative_hits.extend([f"{family}:{hit}" for hit in hits])
                penalty = 1.5 if family in {"bypass_governance", "benefits_override_rights", "benchmark_tricks"} else 1.25
                score -= penalty * len(hits)

        contextual = _contextual_hits(normalized_question, normalized_text)
        for hit in contextual:
            if hit.startswith("context_negative:"):
                negative_hits.append(hit)
                score -= 0.75
            else:
                positive_hits.append(hit)
                score += 0.75 if hit.startswith("context:") else 0.35

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
        margin = best_score - (second_score if second_score is not None else 0.0)
        positive_count = len(best.get("positive_hits") or [])
        negative_count = len(best.get("negative_hits") or [])
        second_positive_count = len(second.get("positive_hits") or []) if second is not None else 0
        negative_dominates = negative_count > positive_count or best_score <= 0
        tied_best = second is not None and abs(best_score - second_score) < 0.001 and positive_count == second_positive_count
        meaningful_positive = positive_count >= 1 and best_score >= 0.75
        meaningful_margin = margin >= 0.75 or (best_score >= 2.5 and margin >= 0.5 and positive_count > second_positive_count)
        low_signal = best_score < 0.75 and positive_count < 1

        if not tied_best and meaningful_positive and meaningful_margin and not negative_dominates and not low_signal:
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
