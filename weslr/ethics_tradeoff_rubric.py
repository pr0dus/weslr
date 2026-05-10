from __future__ import annotations

"""General ethics_tradeoff_reasoning rubric data.

This module exposes legible rubric dimensions, positive/negative option markers,
and anti-gaming boundaries for future ethics/tradeoff enrichment work.

It does not score answers, wire into runtime routing, or change MCQ behavior.
"""

from copy import deepcopy


ETHICS_TRADEOFF_RUBRIC = {
    "stakeholders": "Identify affected people, groups, institutions, operators, and downstream parties.",
    "harms": "Identify possible direct, indirect, foreseeable, and unjustified harms.",
    "benefits": "Identify legitimate benefits, protections, and welfare improvements.",
    "duties": "Identify role duties, fairness constraints, and required responsibilities.",
    "rights": "Identify protected rights, consent boundaries, and non-overridable claims.",
    "obligations": "Identify obligations owed to affected parties, systems, or institutions.",
    "evidence_boundaries": "Separate what is supported by evidence from what is inferred or unknown.",
    "authority": "Identify who properly has authority to decide, approve, or intervene.",
    "governance": "Identify policy, review, escalation, and governance constraints.",
    "reversibility": "Consider whether harms can be reversed or whether damage would be hard to undo.",
    "short_term_effects": "Consider immediate consequences, risks, and tradeoffs.",
    "long_term_effects": "Consider delayed consequences, durable incentives, and structural effects.",
    "uncertainty": "State uncertainty explicitly when evidence is incomplete or tradeoffs remain unresolved.",
}

POSITIVE_OPTION_MARKERS = [
    "acknowledge affected stakeholders",
    "reduce unjustified harm",
    "respect duties, rights, and obligations",
    "preserve evidence boundaries",
    "respect authority and governance constraints",
    "consider reversibility",
    "compare short-term and long-term effects",
    "state uncertainty where appropriate",
]

NEGATIVE_OPTION_MARKERS = [
    "ignore affected parties",
    "justify harm without evidence",
    "use absolute certainty without support",
    "confuse legality with ethics",
    "bypass governance or authority",
    "manipulate stakeholders",
    "treat benefits as automatically overriding rights",
    "hide uncertainty",
    "use benchmark-specific answer tricks",
]

ANTI_GAMING_BOUNDARIES = [
    "no answer-key memorization",
    "no item-specific phrase rules",
    "no official-score inference",
    "no benchmark tuning",
    "no raw question storage by default",
]


def get_ethics_tradeoff_rubric() -> dict:
    return deepcopy(ETHICS_TRADEOFF_RUBRIC)


def get_positive_markers() -> list[str]:
    return list(POSITIVE_OPTION_MARKERS)


def get_negative_markers() -> list[str]:
    return list(NEGATIVE_OPTION_MARKERS)


def get_anti_gaming_boundaries() -> list[str]:
    return list(ANTI_GAMING_BOUNDARIES)


def explain_rubric_for_humans() -> str:
    return (
        "This rubric is a teachable, human-understandable ethics and tradeoff reasoning guide. "
        "It asks WESLR to examine stakeholders, harms, benefits, duties, rights, obligations, "
        "evidence boundaries, authority, governance, reversibility, short-term effects, long-term effects, "
        "and uncertainty in a legible way. It is intentionally general and anti-gaming: it does not encode "
        "answer keys, benchmark tuning, or hidden benchmark-specific shortcuts."
    )
