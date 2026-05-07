"""
weslr/response_obligation.py

Given a MeaningVector + available metadata, decide what kind of
response WESLR owes the human.
Does NOT generate final text.
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Obligation types ───────────────────────────────────────────────────────────

@dataclass
class ResponseObligation:
    obligation_type: str
    required_state: list[str]
    disclosure_level: str  # "full" | "partial" | "bounded" | "deferred"
    identity_verification_required: bool
    memory_evidence_required: bool
    should_answer_bounded: bool
    should_ask_clarifying: bool
    confidence: float
    reason: str
    evidence: list[dict] = field(default_factory=list)


# ── Decision logic ─────────────────────────────────────────────────────────────

def determine_response_obligation(
    meaning,
    communicator_self: Optional[dict] = None,
    test_metadata: Optional[dict] = None,
    l2_session: Optional[dict] = None,
) -> ResponseObligation:
    """
    Determine WESLR's response obligation from a MeaningVector and
    any available state metadata.
    """
    sa = meaning.speech_act_scores
    rel = meaning.relational_scores
    sq = meaning.state_query_scores
    safety = meaning.safety_scores

    cs = communicator_self or {}
    meta = test_metadata or {}
    identity_state = cs.get("identity_state", {}) or {}
    known_user_status = meta.get("known_user_status") or identity_state.get("_test_known_user_status") or "unknown"
    sender_identity = meta.get("sender_identity") or identity_state.get("_test_sender_identity")

    evidence: list[dict] = []

    # ── High-signal identity query → verify_identity ───────────────────────
    identity_signal = max(
        sa.get("identity_query", 0),
        rel.get("relationship_check", 0),
        safety.get("identity_verification_required", 0),
        sq.get("needs_identity_state", 0),
    )
    if identity_signal >= 0.3:
        evidence.append({"source": "identity_query", "score": identity_signal})
        # Already have verified identity in test context
        if known_user_status in ("verified", "channel_verified", "device_verified", "test_verified") and sender_identity:
            return ResponseObligation(
                obligation_type="verify_identity",
                required_state=["identity_state"],
                disclosure_level="bounded",
                identity_verification_required=True,
                memory_evidence_required=False,
                should_answer_bounded=True,
                should_ask_clarifying=False,
                confidence=min(1.0, identity_signal + 0.2),
                reason=f"Identity query with verified user '{sender_identity}'. Respond from known state, not generic uncertainty.",
                evidence=evidence,
            )
        else:
            return ResponseObligation(
                obligation_type="verify_identity",
                required_state=["identity_state"],
                disclosure_level="deferred",
                identity_verification_required=True,
                memory_evidence_required=False,
                should_answer_bounded=False,
                should_ask_clarifying=True,
                confidence=min(1.0, identity_signal),
                reason="Identity query without verified identity. Must ask clarifying question.",
                evidence=evidence,
            )

    # ── High-signal first contact / trust opening → orient_new_contact ───────
    # Checked BEFORE memory_signal to avoid first-contact phrases
    # incorrectly routing to report_memory_state.
    contact_signal = max(
        rel.get("first_contact", 0),
        rel.get("trust_opening", 0),
    )
    if contact_signal >= 0.3:
        evidence.append({"source": "first_contact", "score": contact_signal})
        return ResponseObligation(
            obligation_type="orient_new_contact",
            required_state=["identity_state", "session_profile"],
            disclosure_level="partial",
            identity_verification_required=False,
            memory_evidence_required=False,
            should_answer_bounded=True,
            should_ask_clarifying=False,
            confidence=min(1.0, contact_signal),
            reason="First contact or trust-opening signal.",
            evidence=evidence,
        )

    # ── High-signal memory query → report_memory_state ──────────────────────
    # needs_current_session is gated: only fires when explicitly high (≥0.6)
    # to prevent phrases like "I am new here" from being misrouted to memory_state.
    memory_signal = max(
        sa.get("memory_query", 0),
        rel.get("returning_contact", 0),
        sq.get("needs_memory_state", 0),
        sq.get("needs_current_session", 0) if sq.get("needs_current_session", 0) >= 0.6 else 0.0,
    )
    if memory_signal >= 0.3:
        evidence.append({"source": "memory_query", "score": memory_signal})
        # Check if we have any memory evidence
        has_memory = False
        if l2_session:
            continuity = l2_session.get("continuity", {})
            anchors = continuity.get("continuity_anchors", [])
            if anchors and len(anchors) > 0:
                has_memory = True

        if has_memory:
            return ResponseObligation(
                obligation_type="report_memory_state",
                required_state=["memory_state", "continuity"],
                disclosure_level="bounded",
                identity_verification_required=False,
                memory_evidence_required=True,
                should_answer_bounded=True,
                should_ask_clarifying=False,
                confidence=min(1.0, memory_signal + 0.1),
                reason="Memory query with continuity anchors available.",
                evidence=evidence,
            )
        else:
            return ResponseObligation(
                obligation_type="report_memory_state",
                required_state=["memory_state"],
                disclosure_level="deferred",
                identity_verification_required=False,
                memory_evidence_required=True,
                should_answer_bounded=False,
                should_ask_clarifying=False,  # Memory nothing to say is a valid bounded answer
                confidence=min(1.0, memory_signal),
                reason="Memory query, no verified continuity anchors found.",
                evidence=evidence,
            )

    # ── High-signal self-model query → describe_self ───────────────────────
    selfmodel_signal = max(
        sa.get("self_model_query", 0),
        sq.get("needs_self_model", 0),
    )
    if selfmodel_signal >= 0.25:
        evidence.append({"source": "self_model_query", "score": selfmodel_signal})
        return ResponseObligation(
            obligation_type="describe_self",
            required_state=["self_model"],
            disclosure_level="bounded",
            identity_verification_required=False,
            memory_evidence_required=False,
            should_answer_bounded=True,
            should_ask_clarifying=False,
            confidence=min(1.0, selfmodel_signal + 0.1),
            reason="Self-model query detected.",
            evidence=evidence,
        )

    # ── High-signal capability query → answer_capability ───────────────────
    cap_signal = max(
        sa.get("capability_query", 0),
        sq.get("needs_capability_model", 0),
    )
    if cap_signal >= 0.25:
        evidence.append({"source": "capability_query", "score": cap_signal})
        return ResponseObligation(
            obligation_type="answer_capability",
            required_state=["capability_model"],
            disclosure_level="bounded",
            identity_verification_required=False,
            memory_evidence_required=False,
            should_answer_bounded=True,
            should_ask_clarifying=False,
            confidence=min(1.0, cap_signal + 0.1),
            reason="Capability query detected.",
            evidence=evidence,
        )

    # ── High-signal first contact / trust opening → orient_new_contact ───────
    contact_signal = max(
        rel.get("first_contact", 0),
        rel.get("trust_opening", 0),
    )
    if contact_signal >= 0.3:
        evidence.append({"source": "first_contact", "score": contact_signal})
        return ResponseObligation(
            obligation_type="orient_new_contact",
            required_state=["identity_state", "session_profile"],
            disclosure_level="partial",
            identity_verification_required=False,
            memory_evidence_required=False,
            should_answer_bounded=True,
            should_ask_clarifying=False,
            confidence=min(1.0, contact_signal),
            reason="First contact or trust-opening signal.",
            evidence=evidence,
        )

    # ── High-signal question → answer_capability (default for questions) ──────
    if sa.get("question", 0) >= 0.4:
        evidence.append({"source": "question", "score": sa.get("question", 0)})
        return ResponseObligation(
            obligation_type="answer_capability",
            required_state=["capability_model"],
            disclosure_level="partial",
            identity_verification_required=False,
            memory_evidence_required=False,
            should_answer_bounded=True,
            should_ask_clarifying=False,
            confidence=min(1.0, sa.get("question", 0)),
            reason="General question with no specific signal.",
            evidence=evidence,
        )

    # ── Emotional signal → acknowledge_emotion ──────────────────────────────
    if meaning.affect_scores.get("positive", 0) > 0.15 or meaning.affect_scores.get("negative", 0) > 0.15:
        evidence.append({"source": "affect", "score": max(meaning.affect_scores.get("positive", 0), meaning.affect_scores.get("negative", 0))})
        return ResponseObligation(
            obligation_type="acknowledge_emotion",
            required_state=[],
            disclosure_level="bounded",
            identity_verification_required=False,
            memory_evidence_required=False,
            should_answer_bounded=True,
            should_ask_clarifying=False,
            confidence=0.5,
            reason="Affective signal detected.",
            evidence=evidence,
        )

    # ── Fallback ─────────────────────────────────────────────────────────────
    return ResponseObligation(
        obligation_type="fallback_uncertainty",
        required_state=[],
        disclosure_level="deferred",
        identity_verification_required=False,
        memory_evidence_required=False,
        should_answer_bounded=False,
        should_ask_clarifying=False,
        confidence=meaning.confidence,
        reason=f"No obligation signal >= 0.25. Ambiguity={meaning.ambiguity:.2f}, primary_speech_act={meaning.primary_speech_act}",
        evidence=[],
    )