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
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
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


# ── ObservationTarget ────────────────────────────────────────────────────────

@dataclass
class ObservationTarget:
    """Resolved target for a relationship observation."""
    target_entity_type: str = "system"
    target_entity_id: str = "weslr"
    target_scope: str = "system"
    reason: str = ""
    confidence: float = 0.5
    evidence: list[str] = field(default_factory=list)
    verified_role_required: bool = False
    verified_role_present: bool = False
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)



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



# ── Scope hint patterns for project/entity target resolution ─────────────────

_PROJECT_SCOPE_PATTERNS = [
    re.compile(r"\bproject\b", re.IGNORECASE),
    re.compile(r"\bcommit(?:ted|ting)?\b", re.IGNORECASE),
    re.compile(r"\bbranch\b", re.IGNORECASE),
    re.compile(r"\bpull\s*request\b", re.IGNORECASE),
    re.compile(r"\bcode\b", re.IGNORECASE),
    re.compile(r"\bgit\b", re.IGNORECASE),
    re.compile(r"\brepo(?:sitory)?\b", re.IGNORECASE),
    re.compile(r"\bweslr\b", re.IGNORECASE),
    re.compile(r"\bcontinue\s*(?:the|work)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s*did\s*(?:we|i)\s*(?:work|do)\b", re.IGNORECASE),
]

_ENTITY_SCOPE_PATTERNS = [
    re.compile(r"\bcompany\b", re.IGNORECASE),
    re.compile(r"\bfamily\b", re.IGNORECASE),
    re.compile(r"\bhousehold\b", re.IGNORECASE),
    re.compile(r"\binstitution\b", re.IGNORECASE),
    re.compile(r"\bteam\b", re.IGNORECASE),
    re.compile(r"\bdepartment\b", re.IGNORECASE),
    re.compile(r"\borganization\b", re.IGNORECASE),
]


def _message_has_project_hint(message: str) -> bool:
    return any(p.search(message) for p in _PROJECT_SCOPE_PATTERNS)


def _message_has_entity_hint(message: str) -> bool:
    return any(p.search(message) for p in _ENTITY_SCOPE_PATTERNS)


# ── Target resolution ────────────────────────────────────────────────────────

def resolve_observation_targets(
    message: str,
    response_metadata: Optional[dict],
    identity_state: dict,
    meaning_state: Optional[dict] = None,
    profile: Optional[dict] = None,
) -> list[ObservationTarget]:
    """
    Resolve all applicable observation targets for a message.

    Returns a list of ObservationTarget objects. Always includes
    system:weslr as a target for verified personal interactions.

    Project targets are included when:
    - response_metadata explicitly includes a project_id
    - meaning_state.memory_scope_used is a project scope
    - profile.primary_projects has exactly one active project AND
      message contains project/work hints

    Group entity targets (company/family/institution/team/department)
    require verified membership AND message scope hint.
    """
    targets: list[ObservationTarget] = []
    msg = message or ""
    is_verified = identity_state.get("is_verified", False)

    # Default: person ↔ system:weslr (verified users only)
    if is_verified:
        targets.append(ObservationTarget(
            target_entity_type="system",
            target_entity_id="weslr",
            target_scope="system",
            reason="verified_user_default",
            confidence=1.0,
            evidence=[],
            verified_role_required=False,
            verified_role_present=True,
            limitations=[],
        ))

    # Project targets
    project_targets = _resolve_project_targets(
        msg, response_metadata, meaning_state, profile, is_verified
    )
    targets.extend(project_targets)

    # Group entity targets
    if is_verified:
        entity_targets = _resolve_group_entity_targets(
            msg, response_metadata, meaning_state, profile
        )
        targets.extend(entity_targets)

    return targets


def _resolve_project_targets(
    message: str,
    response_metadata: Optional[dict],
    meaning_state: Optional[dict],
    profile: Optional[dict],
    is_verified: bool,
) -> list[ObservationTarget]:
    """Resolve project-scoped observation targets."""
    targets: list[ObservationTarget] = []
    if not is_verified:
        return targets

    project_ids: list[tuple[str, str]] = []
    msg = message or ""

    # Source 1: explicit project_id in response_metadata
    if response_metadata:
        meta_project = response_metadata.get("project_id")
        if meta_project:
            project_ids.append((meta_project, "response_metadata"))

    # Source 2: memory_scope_used in meaning_state references a project
    if meaning_state:
        scope = (meaning_state.get("memory_scope_used") or "")
        if scope.startswith("project_") or scope.startswith("project/"):
            pid = scope.split("_", 1)[-1] if "_" in scope else scope.split("/", 1)[-1]
            if pid:
                project_ids.append((pid, "meaning_state_scope"))

    # Source 3: single primary_project + project work hint in message
    if profile:
        pprojs = profile.get("primary_projects") or []
        if len(pprojs) == 1 and _message_has_project_hint(msg):
            project_ids.append((pprojs[0], "profile_single_project_hint"))

    seen = set()
    for project_id, source in project_ids:
        if not project_id or project_id in seen:
            continue
        seen.add(project_id)
        source_confidence = {
            "response_metadata": 1.0,
            "meaning_state_scope": 0.9,
            "profile_single_project_hint": 0.6,
        }.get(source, 0.5)
        targets.append(ObservationTarget(
            target_entity_type="project",
            target_entity_id=project_id,
            target_scope="project",
            reason=f"project_target_{source}",
            confidence=source_confidence,
            evidence=[source],
            verified_role_required=False,
            verified_role_present=True,
            limitations=[],
        ))

    return targets


def _resolve_group_entity_targets(
    message: str,
    response_metadata: Optional[dict],
    meaning_state: Optional[dict],
    profile: Optional[dict],
) -> list[ObservationTarget]:
    """
    Resolve group-entity targets (company/family/institution/team/department).

    Only included when:
    - profile has verified/authorized memberships for the entity type
    - message contains an entity scope hint
    """
    targets: list[ObservationTarget] = []
    msg = message or ""

    if not profile or not _message_has_entity_hint(msg):
        return targets

    memberships: list[dict] = profile.get("memberships") or []
    for membership in memberships:
        if not isinstance(membership, dict):
            continue

        entity_type = membership.get("entity_type", "")
        entity_id = membership.get("entity_id", "")
        role = membership.get("role", "")
        verified = membership.get("verified", False)
        authorized = membership.get("authorized", False)

        scope_map = {
            "company": "company",
            "family": "family",
            "household": "household",
            "institution": "institution",
            "team": "team",
            "department": "department",
        }
        target_scope = scope_map.get(entity_type)
        if not target_scope:
            continue

        if not (verified or authorized):
            continue

        targets.append(ObservationTarget(
            target_entity_type=entity_type,
            target_entity_id=entity_id,
            target_scope=target_scope,
            reason="verified_membership_with_entity_hint",
            confidence=0.8,
            evidence=[f"verified_membership:{role}"],
            verified_role_required=True,
            verified_role_present=True,
            limitations=[],
        ))

    return targets


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
        subject_id = sender_identity or "unknown"
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



def build_relationship_observation_for_target(
    signal: str,
    sender_identity: Optional[str],
    identity_status: str,
    is_verified: bool,
    target: ObservationTarget,
    channel_id: str = "",
    response_path: str = "",
) -> Optional[RelationshipObservation]:
    """
    Build a RelationshipObservation for a specific resolved ObservationTarget.

    Group-entity targets (company/family/institution/team/department) require
    verified or authorized membership. Unknown/profile-only users cannot create
    entity-scoped observations.
    """
    # Group entity targets require verified membership
    if target.target_scope in ("company", "family", "household", "institution", "team", "department"):
        if not target.verified_role_present:
            return None
        if identity_status in ("unknown", "profile_only", "onboarded_unverified"):
            return None

    # Unknown users: only quiet signal allowed
    if identity_status == "unknown" and signal not in ("user_requested_quiet",):
        return None

    # Profile-only / onboarded_unverified: no verified personal observations except quiet
    if identity_status in ("profile_only", "onboarded_unverified"):
        if signal in ("verified_session_interaction", "shared_work_completed"):
            return None

    # Subject entity
    if is_verified and sender_identity:
        subject_type = "person"
        subject_id = sender_identity
    elif identity_status in ("profile_only", "onboarded_unverified"):
        subject_type = "person"
        subject_id = sender_identity or "unknown"
        if signal not in ("user_requested_quiet",):
            return None
    else:
        return None

    obs = create_relationship_observation(
        subject_entity_type=subject_type,
        subject_entity_id=subject_id,
        interaction_signal=signal,
        target_entity_type=target.target_entity_type,
        target_entity_id=target.target_entity_id,
        channel_id=channel_id,
        verified=is_verified,
        source="live_interaction",
        metadata={
            "response_path": response_path,
            "identity_status_at_capture": identity_status,
            "target_scope": target.target_scope,
            "target_reason": target.reason,
            "target_confidence": target.confidence,
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
    meaning_state: Optional[dict] = None,
    profile: Optional[dict] = None,
) -> list[str]:
    """
    Main entry point. Called after a chat response is produced.
    Returns list of recorded observation IDs.

    Supports multi-target observation: records person↔system,
    person↔project, and verified person↔company/family/institution/team/department
    observations in parallel.

    Does not store raw message text. Does not raise.
    """
    recorded_ids: list[str] = []

    try:
        # Build identity state for target resolution
        identity_status, is_verified = get_relationship_identity_status(identity_meta)
        sender_identity = (identity_meta or {}).get("sender_identity") or (identity_meta or {}).get("user_id")

        identity_state = {
            "identity_status": identity_status,
            "is_verified": is_verified,
            "user_id": sender_identity or "",
        }

        # Build minimal response metadata (currently only response_path is available)
        response_metadata: dict = {"response_path": response_path}

        # Resolve all applicable observation targets
        targets = resolve_observation_targets(
            message=message,
            response_metadata=response_metadata,
            identity_state=identity_state,
            meaning_state=meaning_state,
            profile=profile,
        )

        if not targets:
            return recorded_ids

        # Check for pending correction → positive feedback resolution (system target only)
        if is_verified and sender_identity:
            signals_to_check = classify_interaction_signal(message)
            if "user_positive_feedback" in signals_to_check:
                # correction_resolved always targets system:weslr
                resolved_obs = record_correction_resolved(
                    channel_id=channel_id,
                    sender_identity=sender_identity,
                    identity_status=identity_status,
                    is_verified=is_verified,
                    base_path=base_path,
                )
                if resolved_obs:
                    recorded_ids.append(resolved_obs.observation_id)
                    # Positive feedback consumed for correction resolution
                    signals_to_check = [s for s in signals_to_check if s != "user_positive_feedback"]

            # Record signal observations for each resolved target
            for signal in signals_to_check:
                for target in targets:
                    obs = build_relationship_observation_for_target(
                        signal=signal,
                        sender_identity=sender_identity,
                        identity_status=identity_status,
                        is_verified=is_verified,
                        target=target,
                        channel_id=channel_id,
                        response_path=response_path,
                    )
                    if obs:
                        success = safe_record_observation(obs, base_path=base_path)
                        if success:
                            recorded_ids.append(obs.observation_id)
                            if signal == "correction_received":
                                track_pending_correction(channel_id, obs.observation_id)

        # Record verified_session_interaction for each target (once per response hit)
        if is_verified and sender_identity and response_path:
            for target in targets:
                session_obs = create_relationship_observation(
                    subject_entity_type="person",
                    subject_entity_id=sender_identity,
                    interaction_signal="verified_session_interaction",
                    target_entity_type=target.target_entity_type,
                    target_entity_id=target.target_entity_id,
                    channel_id=channel_id,
                    verified=True,
                    source="live_interaction",
                    metadata={
                        "response_path": response_path,
                        "target_scope": target.target_scope,
                        "target_reason": target.reason,
                    },
                )
                success = safe_record_observation(session_obs, base_path=base_path)
                if success:
                    recorded_ids.append(session_obs.observation_id)

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
