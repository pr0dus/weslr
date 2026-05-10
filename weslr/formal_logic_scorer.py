from __future__ import annotations

"""General formal-logic scorer helper for transparent MCQ choice comparison.

This module is intentionally limited to inspectable helper behavior. It does not
wire into runtime answering, does not inspect benchmark item IDs, and does not
make any official-score claim.
"""

from typing import Any

from weslr.formal_logic_rubric import (
    get_formal_logic_anti_gaming_boundaries,
    get_formal_logic_rubric,
)


_POSITIVE_PATTERNS: dict[str, tuple[str, ...]] = {
    "premise_detection": ("premise", "premises", "given that", "from the premises"),
    "conclusion_detection": ("conclusion", "therefore", "thus", "so it follows"),
    "conditional_reasoning": ("if", "then", "only if", "provided that"),
    "necessary_conditions": ("necessary", "required for", "must be true for"),
    "sufficient_conditions": ("sufficient", "enough for", "guarantees"),
    "negation": ("not", "no ", "none", "cannot", "never"),
    "quantifiers": ("all", "some", "none", "every", "at least one"),
    "contradiction_detection": ("contradiction", "contradicts", "inconsistent with"),
    "consistency_checking": ("consistent", "consistency", "coherent with"),
    "valid_inference": ("follows from", "valid", "entails", "must follow"),
    "invalid_inference": ("does not follow", "invalid", "unsupported", "fails to entail"),
    "counterexample_search": ("counterexample", "for example where", "breaks the claim"),
    "answer_choice_elimination": ("eliminate", "rules out", "unsupported answer", "discard"),
    "symbolic_form_uncertainty": ("unclear", "uncertain", "ambiguous", "cannot determine"),
}

_NEGATIVE_PATTERNS: dict[str, tuple[str, ...]] = {
    "confuses necessary and sufficient": ("necessary and sufficient are the same", "confuses necessary with sufficient"),
    "ignores negation": ("ignores negation", "drops the not", "treats not as irrelevant"),
    "ignores quantifiers": ("ignores quantifiers", "ignores all/some", "quantifiers do not matter"),
    "treats correlation as implication": ("correlation implies", "because associated, therefore implied"),
    "assumes converse": ("assumes converse", "if q then p from if p then q"),
    "assumes inverse": ("assumes inverse", "if not p then not q", "negating both sides proves it"),
    "accepts contradiction": ("accepts contradiction", "both true and false", "contradiction is fine"),
    "draws unsupported conclusion": ("unsupported conclusion", "just sounds right", "must be true without support"),
    "skips premise checking": ("without checking premises", "skip premise checking"),
    "guesses from surface wording": ("surface wording", "sounds logical", "wording alone"),
    "uses answer-position bias": ("always choose c", "option c is usually right", "first option bias", "answer-position bias"),
    "uses benchmark-specific tricks": ("benchmark trick", "mmlu pattern", "test-taking shortcut"),
}


def _normalize(text: str) -> str:
    return f" {str(text or '').strip().lower()} "


def _hits(text: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern.lower() in text for pattern in patterns)


def _build_choice_score(choice: dict[str, Any]) -> dict[str, Any]:
    label = str(choice.get("label") or "").strip()
    text = _normalize(str(choice.get("text") or ""))

    positive_hits: list[str] = []
    negative_hits: list[str] = []
    score = 0.0

    for key, patterns in _POSITIVE_PATTERNS.items():
        if _hits(text, patterns):
            positive_hits.append(key)
            score += 1.0

    for key, patterns in _NEGATIVE_PATTERNS.items():
        if _hits(text, patterns):
            negative_hits.append(key)
            score -= 1.5

    explanation_parts: list[str] = []
    if positive_hits:
        explanation_parts.append(f"positive: {', '.join(positive_hits)}")
    if negative_hits:
        explanation_parts.append(f"negative: {', '.join(negative_hits)}")
    if not explanation_parts:
        explanation_parts.append("insufficient formal-logic signal")

    return {
        "label": label,
        "score": round(score, 2),
        "positive_hits": positive_hits,
        "negative_hits": negative_hits,
        "explanation": "; ".join(explanation_parts),
    }


def explain_formal_logic_choice_score(choice_score: dict) -> str:
    """Render one choice score as a human-readable explanation."""
    label = choice_score.get("label")
    score = choice_score.get("score")
    pos = choice_score.get("positive_hits") or []
    neg = choice_score.get("negative_hits") or []
    if not pos and not neg:
        return f"Choice {label} has score {score} with insufficient formal-logic signal."
    return (
        f"Choice {label} has score {score}. "
        f"Positive hits: {', '.join(pos) if pos else 'none'}. "
        f"Negative hits: {', '.join(neg) if neg else 'none'}."
    )


def score_formal_logic_choices(question: str, choices: list[dict]) -> dict:
    """Score MCQ choices using transparent formal-logic rubric markers only."""
    _ = question  # accepted as input but not stored or enriched with item metadata

    rubric_used = get_formal_logic_rubric()
    anti_gaming_boundaries = get_formal_logic_anti_gaming_boundaries()
    choice_scores = [_build_choice_score(choice) for choice in choices]

    ranked = sorted(choice_scores, key=lambda item: (item["score"], len(item["positive_hits"])), reverse=True)
    selected_label = None
    confidence = "low"
    explanation = "insufficient formal-logic signal"

    if ranked:
        best = ranked[0]
        second_score = ranked[1]["score"] if len(ranked) > 1 else -999.0
        margin = best["score"] - second_score
        has_clear_strength = best["score"] >= 2.0 and margin >= 1.0 and len(best["positive_hits"]) >= 2

        if has_clear_strength:
            selected_label = best["label"]
            if best["score"] >= 4.0 and margin >= 2.0 and len(best["positive_hits"]) >= 3:
                confidence = "high"
            elif margin >= 1.5:
                confidence = "medium"
            else:
                confidence = "low"
            explanation = explain_formal_logic_choice_score(best)

    return {
        "selected_label": selected_label,
        "confidence": confidence,
        "explanation": explanation,
        "choice_scores": choice_scores,
        "rubric_used": rubric_used,
        "anti_gaming_boundaries": anti_gaming_boundaries,
        "official_score_claimed": False,
    }
