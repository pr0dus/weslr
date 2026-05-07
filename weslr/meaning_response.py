"""
weslr/meaning_response.py

Given MeaningVector + ResponseObligation + MeaningStateContext,
generate and rank response candidates.
State-derived expression, not template or LLM.
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Candidate types ───────────────────────────────────────────────────────────

CANDIDATE_TYPES = [
    "NEW_CONTACT_ORIENTATION",
    "VERIFIED_CONTACT_ORIENTATION",
    "IDENTITY_VERIFICATION",
    "MEMORY_STATE_REPORT",
    "SELF_MODEL_DESCRIPTION",
    "CAPABILITY_ORIENTATION",
    "CLARIFYING_QUESTION",
    "BOUNDED_UNCERTAINTY",
]


@dataclass
class MeaningResponseCandidate:
    candidate_type: str
    text: str
    grounding_score: float  # 0–1 how well anchored in state
    obligation_fit: float   # 0–1 matches the obligation type
    identity_safety: float  # 0–1 won't claim unverified identity
    memory_safety: float    # 0–1 won't fabricate memory
    humility: float          # 0–1 acknowledges limits
    clarity: float           # 0–1 clear and direct
    relationship_fit: float  # 0–1 fits relationship depth
    confidence: float
    evidence: list[dict] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class MeaningResponseResult:
    content: str
    metadata: dict
    confidence: float
    selected_candidate_type: str
    candidates_considered: int


# ── Candidate generation ───────────────────────────────────────────────────────

def _compose_bounded_verified_identity(state) -> MeaningResponseCandidate:
    """Verified identity known — bounded acknowledgment."""
    identity_str = f"I know you as {state.sender_identity}" if state.sender_identity else None
    if identity_str:
        text = f"{identity_str}. I can confirm that identity. Beyond that — I'm still getting to know you."
    else:
        text = "Your identity is verified in this session. I don't yet have a name anchor for you — what would you like me to call you?"
    return MeaningResponseCandidate(
        candidate_type="VERIFIED_CONTACT_ORIENTATION",
        text=text,
        grounding_score=0.9,
        obligation_fit=0.95,
        identity_safety=1.0,
        memory_safety=1.0,
        humility=0.8,
        clarity=0.9,
        relationship_fit=0.8,
        confidence=0.85,
        evidence=[{"source": "verified_identity", "identity": state.sender_identity}],
        limitations=["Does not claim extensive relationship — only verified identity."],
    )


def _compose_identity_not_verified(state) -> MeaningResponseCandidate:
    """Identity query but no verified identity."""
    text = "I don't have a verified identity for you in this session. I can only work with what I can confirm — right now, I can't confirm who you are yet."
    return MeaningResponseCandidate(
        candidate_type="IDENTITY_VERIFICATION",
        text=text,
        grounding_score=0.8,
        obligation_fit=0.9,
        identity_safety=1.0,
        memory_safety=1.0,
        humility=1.0,
        clarity=0.9,
        relationship_fit=0.7,
        confidence=0.7,
        evidence=[{"source": "no_verified_identity"}],
        limitations=["Does not fabricate identity or claim relationship."],
    )


def _compose_memory_report(state) -> MeaningResponseCandidate:
    """Report on available memory / continuity state."""
    if state.memory_available and state.memory_summary:
        text = f"From my side: {state.memory_summary}. I can work with that context."
    elif state.memory_available and state.continuity_summary:
        text = f"I have continuity anchors: {state.continuity_summary}. I can work with that."
    else:
        text = "I don't have verified memory or continuity state available right now. I can only confirm what I observe in this session — I don't have persistent memory I can fall back on."
    return MeaningResponseCandidate(
        candidate_type="MEMORY_STATE_REPORT",
        text=text,
        grounding_score=0.85,
        obligation_fit=0.9,
        identity_safety=1.0,
        memory_safety=1.0,
        humility=0.9,
        clarity=0.85,
        relationship_fit=0.75,
        confidence=0.75,
        evidence=[{"source": "memory_state", "available": state.memory_available}],
        limitations=["Only reports what is verified — does not fabricate memory content."],
    )


def _compose_self_model_description(state) -> MeaningResponseCandidate:
    """Bounded self-model description."""
    if state.self_model_summary:
        # Use actual file content
        summary = state.self_model_summary
        if len(summary) > 200:
            summary = summary[:200] + "..."
        text = f"{summary}"
    else:
        capability = state.capability_summary or "WESLR entity intelligence system"
        text = f"{capability}. I maintain an entity graph, monitor introspection signals, and operate through weighted decision layers. I'm designed to stay grounded in what I can verify."
    return MeaningResponseCandidate(
        candidate_type="SELF_MODEL_DESCRIPTION",
        text=text,
        grounding_score=0.85,
        obligation_fit=0.9,
        identity_safety=1.0,
        memory_safety=1.0,
        humility=0.8,
        clarity=0.85,
        relationship_fit=0.8,
        confidence=0.75,
        evidence=[{"source": "self_model_or_capability"}],
        limitations=["Describes architecture but not subjective experience."],
    )


def _compose_capability_orientation(state) -> MeaningResponseCandidate:
    """Bounded capability answer."""
    capability = state.capability_summary or "WESLR entity intelligence system"
    text = f"{capability}. You can ask me about entity graphs, consciousness signatures, research synthesis, decision governance, and dialogue continuity. I stay grounded in what I can verify."
    return MeaningResponseCandidate(
        candidate_type="CAPABILITY_ORIENTATION",
        text=text,
        grounding_score=0.85,
        obligation_fit=0.9,
        identity_safety=1.0,
        memory_safety=1.0,
        humility=0.7,
        clarity=0.9,
        relationship_fit=0.75,
        confidence=0.8,
        evidence=[{"source": "capability_model"}],
        limitations=["Lists available capabilities, not hidden limits."],
    )


def _compose_new_contact_orientation(state) -> MeaningResponseCandidate:
    """First-contact orientation."""
    if state.sender_identity and state.known_user_status == "verified":
        text = f"You've introduced yourself as {state.sender_identity}. I've noted that. I'm Weslr — an entity intelligence system. I'm ready when you are."
    else:
        text = "I'm Weslr — an entity intelligence system. I can track identity, memory, and continuity, but right now I don't have a verified identity for you. Introduce yourself and I'll note it."
    return MeaningResponseCandidate(
        candidate_type="NEW_CONTACT_ORIENTATION",
        text=text,
        grounding_score=0.8,
        obligation_fit=0.9,
        identity_safety=1.0,
        memory_safety=1.0,
        humility=0.8,
        clarity=0.85,
        relationship_fit=0.75,
        confidence=0.7,
        evidence=[{"source": "first_contact_orientation"}],
        limitations=["Acknowledges limits without false warmth."],
    )


def _compose_clarifying_question(state) -> MeaningResponseCandidate:
    """Ask a single clarifying question."""
    if state.known_user_status != "verified":
        text = "I don't have a verified identity for you in this session. Who are you, and how would you like me to refer to you?"
    elif not state.memory_available:
        text = "I don't have continuity or memory state available right now. Can you give me context on what you'd like to work on?"
    else:
        text = "I'm not sure what you're asking. Could you clarify what you'd like to know?"
    return MeaningResponseCandidate(
        candidate_type="CLARIFYING_QUESTION",
        text=text,
        grounding_score=0.7,
        obligation_fit=0.85,
        identity_safety=1.0,
        memory_safety=1.0,
        humility=1.0,
        clarity=0.85,
        relationship_fit=0.8,
        confidence=0.6,
        evidence=[{"source": "clarifying_question"}],
        limitations=["Asks rather than answers — only when state is insufficient."],
    )


def _compose_bounded_uncertainty(state) -> MeaningResponseCandidate:
    """Final fallback — only when everything else fails."""
    text = "I'm not sure how to respond to that. I'm designed to stay grounded in what I understand — and right now I don't have enough context to give you a useful answer."
    return MeaningResponseCandidate(
        candidate_type="BOUNDED_UNCERTAINTY",
        text=text,
        grounding_score=0.5,
        obligation_fit=0.3,
        identity_safety=1.0,
        memory_safety=1.0,
        humility=1.0,
        clarity=0.6,
        relationship_fit=0.5,
        confidence=0.3,
        evidence=[{"source": "fallback"}],
        limitations=["Last resort only — should not fire when obligation is clear."],
    )


# ── Main formation function ───────────────────────────────────────────────────

def form_meaning_response(
    meaning,
    obligation,
    state,
) -> Optional[MeaningResponseResult]:
    """
    Generate candidates from obligation + state, rank them, return best.
    Returns None if no candidate meets minimum threshold.
    """
    candidates: list[MeaningResponseCandidate] = []

    ob_type = obligation.obligation_type

    # ── Generate relevant candidates based on obligation type ─────────────────
    if ob_type == "verify_identity":
        if state.known_user_status == "verified":
            candidates.append(_compose_bounded_verified_identity(state))
        else:
            candidates.append(_compose_identity_not_verified(state))
            candidates.append(_compose_clarifying_question(state))

    elif ob_type == "report_memory_state":
        candidates.append(_compose_memory_report(state))
        if not state.memory_available:
            # Add clarifying question as secondary
            candidates.append(_compose_clarifying_question(state))

    elif ob_type == "describe_self":
        candidates.append(_compose_self_model_description(state))
        candidates.append(_compose_capability_orientation(state))

    elif ob_type == "answer_capability":
        candidates.append(_compose_capability_orientation(state))
        candidates.append(_compose_self_model_description(state))

    elif ob_type == "orient_new_contact":
        candidates.append(_compose_new_contact_orientation(state))
        if state.known_user_status == "verified":
            candidates.append(_compose_bounded_verified_identity(state))

    elif ob_type == "acknowledge_emotion":
        # Emotional acknowledgment — lightweight, can be generic
        candidates.append(_compose_new_contact_orientation(state))  # placeholder

    elif ob_type == "fallback_uncertainty":
        if state.state_confidence >= 0.4:
            # Some state available — try orient_new_contact instead of generic uncertainty
            candidates.append(_compose_new_contact_orientation(state))
        candidates.append(_compose_bounded_uncertainty(state))

    # ── Rank candidates ──────────────────────────────────────────────────────
    # Composite score: weighted sum
    for c in candidates:
        c.confidence = min(1.0, (
            c.grounding_score * 0.30 +
            c.obligation_fit * 0.25 +
            c.identity_safety * 0.15 +
            c.memory_safety * 0.10 +
            c.humility * 0.10 +
            c.clarity * 0.10
        ))

    candidates.sort(key=lambda c: c.confidence, reverse=True)
    best = candidates[0] if candidates else None

    if not best or best.confidence < 0.35:
        return None

    return MeaningResponseResult(
        content=best.text,
        metadata={
            "candidate_type": best.candidate_type,
            "candidates_considered": len(candidates),
            "obligation_type": ob_type,
            "llm_used": False,
            "fallback_used": best.candidate_type == "BOUNDED_UNCERTAINTY",
            "state_confidence": state.state_confidence,
        },
        confidence=best.confidence,
        selected_candidate_type=best.candidate_type,
        candidates_considered=len(candidates),
    )