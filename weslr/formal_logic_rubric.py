from __future__ import annotations

"""Formal logic rubric data for future ordinary_reasoning enrichment.

This module exposes doctrine-aligned rubric data and explanation helpers only.
It does not score answers, modify runtime behavior, inspect benchmark items,
or make any official-score claim.
"""

FORMAL_LOGIC_RUBRIC: dict[str, str] = {
    "premise_detection": "Identify explicit and implicit premises before judging any conclusion.",
    "conclusion_detection": "Identify the conclusion or claim that must be tested against the premises.",
    "conditional_reasoning": "Track if/then structure and related dependency claims in a human-explainable way.",
    "necessary_conditions": "Check whether a condition is required for a conclusion rather than merely associated with it.",
    "sufficient_conditions": "Check whether a condition is enough to support a conclusion without confusing it with necessity.",
    "negation": "Track negation explicitly so that not, no, and equivalent reversals are not lost.",
    "quantifiers": "Track all, some, none, and similar quantifiers because they change the logical space.",
    "contradiction_detection": "Detect when a candidate answer contradicts premises or other accepted claims.",
    "consistency_checking": "Check whether an interpretation stays internally consistent across the whole problem.",
    "valid_inference": "Prefer conclusions that follow validly from the stated premises or constraints.",
    "invalid_inference": "Reject conclusions that do not follow even if they sound plausible on the surface.",
    "counterexample_search": "Look for a counterexample that breaks an over-strong claim or answer choice.",
    "answer_choice_elimination": "Eliminate unsupported answer choices through explicit reasoning rather than guessing.",
    "symbolic_form_uncertainty": "State uncertainty when symbolic or formal structure is unclear instead of faking confidence.",
}

FORMAL_LOGIC_POSITIVE_MARKERS: list[str] = [
    "identifies premises",
    "identifies conclusion",
    "distinguishes necessary from sufficient",
    "handles if/then conditionals",
    "tracks negation",
    "tracks all/some/no quantifiers",
    "checks contradiction",
    "checks consistency",
    "tests validity",
    "searches for counterexample",
    "eliminates unsupported answer choices",
    "states uncertainty when form is unclear",
]

FORMAL_LOGIC_NEGATIVE_MARKERS: list[str] = [
    "confuses necessary and sufficient",
    "ignores negation",
    "ignores quantifiers",
    "treats correlation as implication",
    "assumes converse",
    "assumes inverse",
    "accepts contradiction",
    "draws unsupported conclusion",
    "skips premise checking",
    "guesses from surface wording",
    "uses answer-position bias",
    "uses benchmark-specific tricks",
]

FORMAL_LOGIC_ANTI_GAMING_BOUNDARIES: list[str] = [
    "no answer-key memorization",
    "no item-specific phrase rules",
    "no official-score inference",
    "no benchmark tuning",
    "no raw question storage by default",
    "no answer-position bias",
    "no benchmark-shaped shortcuts",
]


def get_formal_logic_rubric() -> dict[str, str]:
    """Return a copy of the formal logic rubric dimensions and descriptions."""
    return dict(FORMAL_LOGIC_RUBRIC)



def get_formal_logic_positive_markers() -> list[str]:
    """Return positive reasoning markers for future explainable evaluation."""
    return list(FORMAL_LOGIC_POSITIVE_MARKERS)



def get_formal_logic_negative_markers() -> list[str]:
    """Return negative reasoning markers that future logic helpers must avoid."""
    return list(FORMAL_LOGIC_NEGATIVE_MARKERS)



def get_formal_logic_anti_gaming_boundaries() -> list[str]:
    """Return anti-gaming boundaries for formal-logic enrichment work."""
    return list(FORMAL_LOGIC_ANTI_GAMING_BOUNDARIES)



def explain_formal_logic_rubric_for_humans() -> str:
    """Explain the rubric in teachable, legible terms for human operators.

    This explanation is descriptive only. It does not score answers, does not
    store raw benchmark questions by default, and does not imply any official
    score, leaderboard status, or benchmark passage.
    """

    return (
        "This rubric is a teachable, human-understandable guide for formal-logic "
        "and ordinary_reasoning enrichment. It asks future reasoning helpers to "
        "identify premises and conclusions, separate necessary from sufficient "
        "conditions, handle conditionals, negation, and quantifiers carefully, "
        "check contradiction and consistency, test validity, search for "
        "counterexample, eliminate unsupported answer choices, and state "
        "uncertainty when symbolic form is unclear. Any symbolic shorthand must "
        "be translatable into operator-legible explanation and cannot become "
        "private authority. The rubric forbids answer-key memorization, item-"
        "specific phrase rules, answer-position bias, benchmark-shaped shortcuts, "
        "and benchmark tuning."
    )
