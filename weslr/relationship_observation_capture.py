"""
WESLR Relationship Observation Capture

Safe, structured relationship observations from verified interaction events.
Does NOT store raw message content. Does NOT use LLM. Does NOT break response flow.

Capture is post-response only: observation failure never prevents answer delivery.
All writes are append-only. Observations are scoped to entity pairs.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from typing import Optional

from weslr.relationship_depth import (
    RelationshipObservation,
    RelationshipStage,
    append_relationship_observation,
    create_relationship_observation,
    record_interaction_outcome,
    get_relationship_tone,
    load_relationship_observations,
    compute_relationship_state,
    IDENTITY_DEPTH_CAPS,
)


# ── Safe message fingerprint ────────────────────────────────────────────────

def safe_message_fingerprint(message: str, max_len: int = 120) -> str:
    """
    Return a short SHA-like hash of the message content.
    Does NOT store the message text.
    """
    if not message:
        return "empty"
    normalized = " ".join(message.lower().split())[:max_len]
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


# ── Signal classifiers ───────────────────────────────────────────────────────

# Correction patterns (do NOT implement as response handlers)
_CORRECTION_PATTERNS = [
    re.compile(r"\bno[,.]?\s*i\s*meant", re.IGNORECASE),
    re.compile(r"\bthat'?s?\s*not\s*(what\s*i\s*asked|right|what\s*i\s*said)", re.IGNORECASE),
    re.compile(r"\bno+(?:,|\s)*you?(?:'re|\s+(?:mis)?understand)", re.IGNORECASE),
    re.compile(r"\bI\s*said\s*(?:it\s*was|she|he|they|them|this|that)", re.IGNORECASE),
    re.compile(r"\bwait[,.]\s*(?:no|stop)", re.IGNORECASE),
    re.compile(r"\bactually[,.]\s", re.IGNORECASE),
    re.compile(r"\bno\s+(?:this|that|it|wrong)", re.IGNORECASE),
    re.compile(r"^(?:n|noo+|nah)\s", re.IGNORECASE),
    re.compile(r"\bnoo+[,.]\s", re.IGNORECASE),  # "Nooo, you"
]

# Positive feedback patterns
_POSITIVE_PATTERNS = [
    re.compile(r"\b(good|great|perfect|yes|yeah|yep|exactly|that'?s?\s*it|correct|nailed\s*it)\b", re.IGNORECASE),
    re.compile(r"\b(awesome|thanks?|thank\s*you|impressive)\b", re.IGNORECASE),
    re.compile(r"\b(you'?re?\s*(?:right|the\s*best|helpful|amazing))\b", re.IGNORECASE),
    re.compile(r"\b(I\s*like\s*(?:this|that|it|your|how))\b", re.IGNORECASE),
    re.compile(r"^(?:y|yes|yeah|yep)\s*$", re.IGNORECASE),
    re.compile(r"\bcool\b", re.IGNORECASE),
    re.compile(r"\bworks?\s*(?:for\s*me|perfect|great)\b", re.IGNORECASE),
]

# Negative feedback patterns
_NEGATIVE_PATTERNS = [
    re.compile(r"\b(wrong|bad|terrible|awful|hate\s*(?:this|it|that))\b", re.IGNORECASE),
    re.compile(r"\b(I\s*(?:dislike|don'?t\s*like|don'?t\s*want))\b", re.IGNORECASE),
    re.compile(r"\bthis\s*(?:doesn'?t\s*work|isn'?t\s*(?:right|normal|correct))\b", re.IGNORECASE),
    re.compile(r"\b(you)?\s*deviated?\s*(?:from\s*(?:what\s*i\s*asked|the\s*request))?\b", re.IGNORECASE),
    re.compile(r"\b(stop|quit|don'?t\s*do\s*that)\b", re.IGNORECASE),
    re.compile(r"\bno+(?:\s+(?:way|thanks?))\b", re.IGNORECASE),
    re.compile(r"^(?:nah|nope|na)\s*$", re.IGNORECASE),
    re.compile(r"\b(I\s*don'?t\s*(?:think\s*so|agree|want\s*this))\b", re.IGNORECASE),
    re.compile(r"\bnot\s+(?:right|correct)\b", re.IGNORECASE),
]

# Quiet/distance patterns
_QUIET_PATTERNS = [
    re.compile(r"\b(stop|talk(ing|ed)?\s*(?:so\s*much|all\s*the\s*time)|quiet|shut\s*up|less\s*(?:please|talk))\b", re.IGNORECASE),
    re.compile(r"\b(don'?t\s*be\s*(?:so\s*|proactive|annoying|forward))\b", re.IGNORECASE),
    re.compile(r"\b(you)?\s*(?:don'?t?\s*need\s*to\s*be\s*so\s*(?:chatty|talkative|active))\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:need\s*to\s*be\s*proactive|proactive\s*(?:stuff|things?|help))\b", re.IGNORECASE),
]

# Memory confirmation/rejection patterns
_MEMORY_CONFIRM_PATTERNS = [
    re.compile(r"\b(yes|confirmed?|correct|that'?s?\s*right|exactly|confirmed?\s+it)\b", re.IGNORECASE),
    re.compile(r"\b(you\s*remembered?\s*(?:it\s*correctly|this|that))\b", re.IGNORECASE),
    re.compile(r"\b(I\s*didn'?t\s*say\s*that\s*but)\b", re.IGNORECASE),  # partial correction
]

_MEMORY_REJECT_PATTERNS = [
    re.compile(r"\b(I\s*never\s*said|you\s*(?:mis)?remember|I\s*didn'?t\s*(?:say|tell|ask))\b", re.IGNORECASE),
    re.compile(r"\bthat'?s?\s*not\s*what\s*I\s*(?:said|told|asked)\b", re.IGNORECASE),
    re.compile(r"\b(you\s*got\s*(?:it\s*wrong|this\s*wrong|memory\s*wrong))\b", re.IGNORECASE),
    re.compile(r"\b(I\s*didn'?t\s*(?:have|mention|want)\s*(?:that|it))\b", re.IGNORECASE),
]


def classify_interaction_signal(message: str) -> list[str]:
    """
    Classify the interaction type(s) from message text.
    Returns list of signal names (from InteractionSignal enum).
    Does NOT implement response logic; only classification for observation capture.
    """
    if not message:
        return []

    msg_lower = message.lower()
    signals: list[str] = []

    for pat in _CORRECTION_PATTERNS:
        if pat.search(message):
            signals.append("correction_received")
            break

    for pat in _POSITIVE_PATTERNS:
        if pat.search(message):
            signals.append("user_positive_feedback")
            break

    for pat in _NEGATIVE_PATTERNS:
        if pat.search(message):
            signals.append("user_negative_feedback")
            break

    for pat in _QUIET_PATTERNS:
        if pat.search(message):
            signals.append("user_requested_quiet")
            break

    for pat in _MEMORY_CONFIRM_PATTERNS:
        if pat.search(message):
            signals.append("memory_confirmed")
            break

    for pat in _MEMORY_REJECT_PATTERNS:
        if pat.search(message):
            signals.append("user_rejected_memory_claim")
            break

    return signals


# ── Identity gating ──────────────────────────────────────────────────────────

_VERIFIED_STATUSES = {"channel_verified", "device_verified", "test_verified"}


def get_relationship_identity_status(identity_meta: Optional[dict]) -> tuple[str, bool]:
    """
    Extract (identity_status, is_verified) from identity_meta dict.
    Returns ('unknown', False) if meta is None or missing.
    """
    if not identity_meta:
        return "unknown", False
    status = identity_meta.get("known_user_status", "unknown")
    return status, status in _VERIFIED_STATUSES


# ── Observation builder ───────────────────────────────────────────────────────

def build_relationship_observation(
    signal: str,
    sender_identity: Optional[str],
    identity_status: str,
    is_verified: bool,
    target_entity_type: str = "system",
    target_entity_id: str = "weslr",
    channel_id: str = "",
    response_path: str = "",
    source: str = "live_interaction",
    base_path: Optional[str] = None,
) -> Optional[RelationshipObservation]:
    """
    Build a RelationshipObservation from a classified signal.
    Returns None if the signal should not be recorded for this identity status.
    """
    # Gate: unverified users do NOT build personal relationship depth
    if identity_status == "unknown" and signal not in ("user_requested_quiet",):
        return None

    # Gate: profile_only / onboarded_unverified cannot build verified personal depth
    if identity_status in ("profile_only", "onboarded_unverified"):
        if signal in ("verified_session_interaction", "shared_work_completed"):
            return None

    # Subject entity type
    if is_verified and sender_identity:
        subject_type = "person"
        subject_id = sender_identity
    elif identity_status in ("profile_only", "onboarded_unverified"):
        subject_type = "person"
        subject_id = identity_meta.get("sender_identity", identity_meta.get("user_id", "unknown")) if identity_meta else "unknown"
        # Only record system-scoped observations for unverified
        if signal not in ("user_requested_quiet",):
            return None
    else:
        return None

    obs = create_relationship_observation(
        subject_entity_type=subject_type,
        subject_entity_id=subject_id,
        interaction_signal=signal,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        channel_id=channel_id,
        verified=is_verified,
        source=source,
        metadata={
            "response_path": response_path,
            "identity_status_at_capture": identity_status,
        },
    )
    return obs


# ── Correction state machine ─────────────────────────────────────────────────

# In-memory correction tracking (not persistent across restarts)
_correction_pending: dict[str, str] = {}  # channel_id → observation_id


def track_pending_correction(channel_id: str, observation_id: str) -> None:
    """Remember that a correction was just recorded for this channel."""
    _correction_pending[channel_id] = observation_id


def pop_pending_correction(channel_id: str) -> Optional[str]:
    """Pop and return the pending correction observation_id if one exists."""
    return _correction_pending.pop(channel_id, None)


def record_correction_resolved(
    channel_id: str,
    sender_identity: Optional[str],
    identity_status: str,
    is_verified: bool,
    base_path: Optional[str] = None,
) -> Optional[RelationshipObservation]:
    """
    If a correction was pending for this channel and user gives positive feedback,
    record correction_resolved.
    """
    correction_obs_id = pop_pending_correction(channel_id)
    if not correction_obs_id:
        return None

    if not is_verified:
        return None

    obs = create_relationship_observation(
        subject_entity_type="person",
        subject_entity_id=sender_identity or "unknown",
        interaction_signal="correction_resolved",
        target_entity_type="system",
        target_entity_id="weslr",
        channel_id=channel_id,
        verified=True,
        source="live_interaction",
        metadata={"corrected_observation_id": correction_obs_id},
    )
    append_relationship_observation(obs, base_path=base_path)
    return obs


# ── Safe append wrapper ─────────────────────────────────────────────────────

def safe_record_observation(
    observation: RelationshipObservation,
    base_path: Optional[str] = None,
) -> bool:
    """
    Append a relationship observation safely.
    Returns True on success, False on any error.
    Observation failure never crashes or blocks.
    """
    try:
        append_relationship_observation(observation, base_path=base_path)
        return True
    except Exception:
        return False


# ── High-level capture ───────────────────────────────────────────────────────

def capture_relationship_observations(
    message: str,
    response_path: str,
    identity_meta: Optional[dict],
    channel_id: str = "",
    base_path: Optional[str] = None,
) -> list[str]:
    """
    Main entry point. Called after a chat response is produced.
    Returns list of recorded observation IDs.
    Does not store raw message text.
    Does not raise.
    """
    recorded_ids: list[str] = []

    try:
        # Determine identity state
        identity_status, is_verified = get_relationship_identity_status(identity_meta)
        sender_identity = (identity_meta or {}).get("sender_identity") or (identity_meta or {}).get("user_id")

        # Check for pending correction → positive feedback resolution
        if is_verified and sender_identity:
            signals_to_check = classify_interaction_signal(message)
            if "user_positive_feedback" in signals_to_check:
                resolved_obs = record_correction_resolved(
                    channel_id=channel_id,
                    sender_identity=sender_identity,
                    identity_status=identity_status,
                    is_verified=is_verified,
                    base_path=base_path,
                )
                if resolved_obs:
                    recorded_ids.append(resolved_obs.observation_id)
                    # Positive feedback was consumed for correction resolution
                    # Remove it from further processing to avoid double-counting
                    signals_to_check = [s for s in signals_to_check if s != "user_positive_feedback"]

            # Classify other signals
            for signal in signals_to_check:
                obs = build_relationship_observation(
                    signal=signal,
                    sender_identity=sender_identity,
                    identity_status=identity_status,
                    is_verified=is_verified,
                    target_entity_type="system",
                    target_entity_id="weslr",
                    channel_id=channel_id,
                    response_path=response_path,
                )
                if obs:
                    success = safe_record_observation(obs, base_path=base_path)
                    if success:
                        recorded_ids.append(obs.observation_id)
                        if signal == "correction_received":
                            track_pending_correction(channel_id, obs.observation_id)

        # Record simple verified session interaction (once per response path hit)
        if is_verified and sender_identity and response_path:
            simple_obs = create_relationship_observation(
                subject_entity_type="person",
                subject_entity_id=sender_identity,
                interaction_signal="verified_session_interaction",
                target_entity_type="system",
                target_entity_id="weslr",
                channel_id=channel_id,
                verified=True,
                source="live_interaction",
                metadata={"response_path": response_path},
            )
            success = safe_record_observation(simple_obs, base_path=base_path)
            if success:
                recorded_ids.append(simple_obs.observation_id)

    except Exception:
        pass  # Never break response flow

    return recorded_ids


# ── Meaning-state integration helpers ───────────────────────────────────────

def get_relationship_tone_for_context(
    identity_status: str,
    sender_identity: Optional[str],
    base_path: Optional[str] = None,
) -> dict:
    """
    Return the relationship tone dict for use in response shaping.
    Loads current relationship state and returns tone parameters.
    """
    if not sender_identity or identity_status == "unknown":
        return {
            "verbosity": "brief",
            "warmth": "reserved",
            "explanatory": True,
            "greeting_style": "cautious",
            "proactive": False,
            "initiative_level": "normal",
        }

    observations = load_relationship_observations(
        subject_entity_type="person",
        subject_entity_id=sender_identity,
        base_path=base_path,
    )
    cap = IDENTITY_DEPTH_CAPS.get(identity_status, 0.05)
    state = compute_relationship_state(observations, identity_status=identity_status)
    depth = min(state.relationship_depth, cap)
    stage = state.relationship_stage or RelationshipStage.UNKNOWN.value
    return get_relationship_tone(depth, stage)
