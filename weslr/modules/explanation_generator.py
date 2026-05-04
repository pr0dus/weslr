"""
weslr/modules/explanation_generator.py
=========================================
Phase 10 — Template-based natural language explanation generator.
No LLM. All outputs deterministic. Uses f-string templates.

Author: OCC (WESLR governed intelligence) — Phase 10
"""

from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Optional


# ── Template helpers ─────────────────────────────────────────────────────────

def _fmt_confidence(confidence: float) -> str:
    """Format confidence as a readable percentage."""
    return f"{confidence * 100:.0f}%"


def _fmt_evidence_list(evidence: list[dict]) -> str:
    """Format a list of evidence items into a readable sentence."""
    if not evidence:
        return "No evidence recorded."
    if len(evidence) == 1:
        ev = evidence[0]
        key = ev.get("key", "item")
        val = ev.get("value", "")
        return f"One piece of evidence: {key} = {val}."
    # 2+ items
    parts = []
    for ev in evidence[:3]:
        key = ev.get("key", "item")
        val = ev.get("value", "")
        parts.append(f"{key}={val}")
    remaining = len(evidence) - 3
    if remaining > 0:
        parts.append(f"and {remaining} more item(s)")
    return f"Based on {len(evidence)} pieces of evidence: {', '.join(parts)}."


def _fmt_causal_graph(causal_graph: dict) -> str:
    """Format a causal graph into a readable sentence."""
    if not causal_graph:
        return "No causal structure defined."
    edges = list(causal_graph.items())
    if len(edges) == 1:
        (cause, effect), conf = edges[0]
        return f"Causal link: {cause} → {effect} (confidence {conf:.2f})."
    # Multiple edges
    parts = []
    for (cause, effect), conf in edges[:3]:
        parts.append(f"{cause} → {effect} ({conf:.2f})")
    remaining = len(edges) - 3
    if remaining > 0:
        return (
            f"Causal structure with {len(edges)} links: "
            f"{', '.join(parts)}, and {remaining} more."
        )
    return f"Causal structure with {len(edges)} links: {', '.join(parts)}."


def _fmt_suggestions(domain: str) -> str:
    """Template suggestion for next experiment based on domain."""
    suggestions = {
        "discovery": "Design a targeted experiment to test each proposed factor.",
        "causality": "Design a controlled experiment to isolate the proposed causal variable.",
        "simulation": "Run a simulation with updated parameters and compare outputs.",
        "spatial": "Compare predictions against a spatially distinct test case.",
        "temporal": "Compare predictions against a temporally distinct test case.",
        "quantum": "Test the proposed quantum prediction against a classical baseline.",
        "mixed": "Design an experiment that can distinguish between the proposed mechanisms.",
    }
    return suggestions.get(domain, "Design a targeted experiment to test the core claim.")


# ── Hypothesis explanation ───────────────────────────────────────────────────

def explain_hypothesis(
    hypothesis,  # Hypothesis object or dict
    /,
    format: str = "text",
) -> str:
    """Generate a human-readable explanation of a hypothesis.

    Parameters
    ----------
    hypothesis : Hypothesis or dict
        The hypothesis to explain.
    format : str
        'text' (default). Reserved for future formats.

    Returns
    -------
    str — narrative explanation using templates.
    """
    if is_dataclass(hypothesis) and not isinstance(hypothesis, dict):
        h = asdict(hypothesis)
    elif isinstance(hypothesis, dict):
        h = hypothesis
    else:
        return f"[ERROR: unknown hypothesis type {type(hypothesis)}]"

    title = h.get("title", "Untitled")
    description = h.get("description", "No description provided.")
    domain = h.get("domain", "mixed")
    confidence = h.get("confidence", 0.0)
    status = h.get("status", "draft")
    meta = h.get("metadata", {})
    evidence = meta.get("evidence", [])
    causal_graph = meta.get("causal_graph", {})
    effect_size = meta.get("effect_size")

    # Build evidence summary
    num_evidence = len(evidence) if evidence else 0
    if evidence:
        evidence_summary = _fmt_evidence_list(evidence[:5])  # cap at 5 for readability
    else:
        evidence_summary = "No evidence recorded yet."

    # Build causal structure note
    causal_note = ""
    if causal_graph:
        causal_note = " " + _fmt_causal_graph(causal_graph)

    # Effect size note
    effect_note = ""
    if effect_size is not None:
        effect_note = f" Estimated effect size: {effect_size}."

    # Status indicator
    status_note = ""
    if status == "active":
        status_note = " [ACTIVE]"
    elif status == "deprecated":
        status_note = " [DEPRECATED]"

    # Build narrative
    lines = []
    lines.append(f"Hypothesis{status_note}: \"{title}\"")
    lines.append(f"")
    lines.append(f"Claim: {description}")
    lines.append(f"")
    lines.append(f"Confidence: {_fmt_confidence(confidence)} based on {num_evidence} piece(s) of evidence.")
    lines.append(f"Domain: {domain}.{effect_note}")
    lines.append(f"")
    lines.append(f"Evidence: {evidence_summary}")
    lines.append(f"")
    if causal_note:
        lines.append(f"Causal structure:{causal_note}")
        lines.append(f"")

    lines.append(f"Suggested next step: {_fmt_suggestions(domain)}")

    return "\n".join(lines)


def explain_causal_link(
    cause: str,
    effect: str,
    confidence: float,
) -> str:
    """Generate a human-readable explanation of a causal link.

    Parameters
    ----------
    cause : str
        The cause variable/concept.
    effect : str
        The effect variable/concept.
    confidence : float
        Confidence of the causal relationship in [0, 1].

    Returns
    -------
    str — template-based explanation.
    """
    conf_pct = _fmt_confidence(confidence)

    if confidence >= 0.8:
        strength_note = "This is a strongly supported causal relationship."
    elif confidence >= 0.6:
        strength_note = "This causal relationship has moderate support."
    elif confidence >= 0.4:
        strength_note = "This causal relationship has weak support and needs further validation."
    else:
        strength_note = "This is a speculative causal link with little empirical support."

    return (
        f"Causal Link: {cause} → {effect}\n"
        f"Confidence: {conf_pct}\n"
        f"\n"
        f"{strength_note}\n"
        f"\n"
        f"Interpretation: Changes in '{cause}' are predicted to produce "
        f"changes in '{effect}' with estimated reliability of {conf_pct}."
    )


def explain_abduction(
    observation: str,
    explanation: str,
    alternative: Optional[str] = None,
) -> str:
    """Format an abductive reasoning result as a human-readable explanation.

    Parameters
    ----------
    observation : str
        The observed phenomenon.
    explanation : str
        The inferred explanation.
    alternative : str, optional
        An alternative explanation to mention.

    Returns
    -------
    str — template-based explanation.
    """
    lines = []
    lines.append("Abductive Reasoning Result")
    lines.append("=" * 40)
    lines.append(f"Observation: {observation}")
    lines.append(f"Best Explanation: {explanation}")
    lines.append("")

    if alternative:
        lines.append(
            f"An alternative explanation worth considering: {alternative}.\n"
        )

    lines.append(
        "Note: This explanation is inferred from available evidence. "
        "It should be tested with targeted experiments before acceptance."
    )

    return "\n".join(lines)


# ── CLI helper ───────────────────────────────────────────────────────────────

def explain_hypothesis_by_id(
    hypothesis_id: str,
    repo,  # HypothesisRepository
) -> str:
    """Explain a hypothesis by ID, using an injected repository."""
    h = repo.get(hypothesis_id)
    if h is None:
        return f"[ERROR: Hypothesis '{hypothesis_id}' not found in repository.]"
    return explain_hypothesis(h)


def explain_hypothesis_dict(h: dict) -> str:
    """Explain a hypothesis from a plain dict (for imported hypotheses)."""
    return explain_hypothesis(h)