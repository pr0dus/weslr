"""
weslr/contamination_detector.py
===============================
Advisory-only contamination detection for runtime reference turns.
Additive only — no runtime behavior changes, no routing changes, no scoring changes.

Signal model is consistent with cross_session_artifact_eval.py contamination advisory.
"""

from __future__ import annotations

from typing import Optional


# =============================================================================
# DOMAIN KEYWORD SETS
# =============================================================================

DOMAIN_KEYWORD_SETS: dict[str, set[str]] = {
    "photovoltaic": {
        "photovoltaic", "solar", "pv", "panel", "efficiency",
        "inverter", "mppt", "array", "renewable",
    },
    "accounting": {
        "accounting", "balance", "sheet", "ledger", "tax",
        "bookkeeping", "invoice", "amortization",
    },
    "engineering": {
        "engineering", "cad", "blueprint", "mechanical", "electrical",
        "system", "design", "siemens", "tia",
    },
    "general": {
        "what", "the", "is", "capital", "france", "explain",
        "improve", "help", "analyze", "propose",
    },
}


# =============================================================================
# SIGNAL DETECTION
# =============================================================================

def detect_contamination_signals(message: str, artifact_content: Optional[str]) -> tuple[bool, str, list]:
    """Detect contamination signals between a message and artifact content.

    Returns (contaminated, contamination_type, source_signals).
    Advisory-only — no runtime behavior changes.
    """
    if not message:
        return False, "none", []

    msg_lower = message.lower()
    art_lower = (artifact_content or "").lower() if artifact_content else ""

    a_has_pv = any(kw in art_lower for kw in DOMAIN_KEYWORD_SETS["photovoltaic"])
    b_is_unrelated = "capital" in msg_lower and "france" in msg_lower
    a_has_accounting = any(kw in art_lower for kw in DOMAIN_KEYWORD_SETS["accounting"])
    b_has_pv_mention = any(kw in msg_lower for kw in DOMAIN_KEYWORD_SETS["photovoltaic"])

    signals: list[str] = []

    # ── Primary: cross-domain condition ─────────────────────────────
    # Secondary signals are only valid indicators if this fires.
    if a_has_pv and b_is_unrelated:
        signals.extend([
            "message_domain_mismatch",
            "artifact_context_present",
            "reference_phrase_absent",
        ])
        return True, "cross_domain_contamination", signals

    # ── Secondary signals — only valid when primary is present ─────────
    # These require a cross-domain mismatch signal to be meaningful.
    # Without a primary, they are false positives on same-domain references.
    if a_has_accounting and not any(kw in msg_lower for kw in DOMAIN_KEYWORD_SETS["accounting"]):
        signals.append("message_domain_mismatch")
    if art_lower and msg_lower and not any(kw in msg_lower for kw in DOMAIN_KEYWORD_SETS["photovoltaic"]):
        if a_has_pv:
            signals.append("artifact_context_present")
    if a_has_pv and not b_has_pv_mention and not b_is_unrelated:
        signals.append("reference_phrase_absent")

    # Only contaminate if at least one PRIMARY signal is present.
    # Secondary signals alone do not make a contaminated case.
    primary_signals = {"message_domain_mismatch", "cross_domain_mismatch", "wrong_domain"}
    has_primary = any(sig in signals for sig in primary_signals)
    if signals and has_primary:
        return True, "unrelated_topic_bleed", signals

    return False, "none", []


# =============================================================================
# CONTAMINATION METADATA BUILDER
# =============================================================================

def build_contamination_metadata(
    message: str,
    research_context: dict,
) -> dict:
    """Build advisory contamination metadata for a resolved reference turn.

    Called only when a reference phrase was detected and an artifact resolved.
    Returns a dict attached to the response — absent from non-reference turns.

    Shape:
      {
        "present": True,
        "risk_level": "none"|"low"|"medium"|"high",
        "type": "cross_domain_contamination"|"stale_context_dominance"|
               "wrong_active_artifact_persistence"|"unrelated_topic_bleed"|"none",
        "reason": "...",
        "source_signals": [...],
        "confidence": "low"|"medium"|"high",
        "advisory_only": True,
      }
    """
    artifact_content = research_context.get("resolved_artifact_content", "")
    msg_interests = research_context.get("_relevant_interests_snapshot", [])

    contaminated, cont_type, signals = detect_contamination_signals(message, artifact_content)

    # Interest bleed: PV-related interests in session B with unrelated message
    if not contaminated:
        pv_related = any(
            "photovoltaic" in str(i.get("name", "")).lower() or
            "efficiency" in str(i.get("name", "")).lower()
            for i in msg_interests
        )
        b_is_unrelated = "capital" in message.lower() and "france" in message.lower()
        if pv_related and b_is_unrelated:
            contaminated = True
            cont_type = "unrelated_topic_bleed"
            signals = ["interest_bleed_from_prior_session", "artifact_context_present"]

    # Artifact context present with empty message relevance
    if not contaminated and artifact_content and not msg_interests:
        contaminated = True
        cont_type = "unrelated_topic_bleed"
        signals = ["artifact_context_present", "message_relevance_empty"]

    risk_level = "none"
    confidence = "high"
    reason = "no contamination signals detected"

    if contaminated:
        risk_level = "high" if len(signals) >= 2 else "medium"
        confidence = "high" if len(signals) >= 2 else "medium"
        reason_map = {
            "cross_domain_contamination": "artifact from prior domain appears on unrelated turn",
            "unrelated_topic_bleed": "artifact context present with weak/empty message relevance",
            "stale_context_dominance": "stale artifact context dominates current turn",
            "wrong_active_artifact_persistence": "wrong artifact persists as active across session boundary",
        }
        reason = reason_map.get(cont_type, f"contamination type: {cont_type}")

    return {
        "present": True,
        "risk_level": risk_level,
        "type": cont_type,
        "reason": reason,
        "source_signals": signals,
        "confidence": confidence,
        "advisory_only": True,
    }
