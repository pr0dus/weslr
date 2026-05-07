"""
WESLR Relationship Depth Model

Bounded relationship depth learned from verified interaction history.
Relationship depth is NOT identity verification.
Relationship depth is NOT memory access permission.
Relationship depth is NOT emotional attachment.

Relationship depth is an evidence-based signal of shared interaction history,
scoped to the relevant person/entity/project relationship.

WESLR may adapt tone and initiative from relationship depth.
WESLR must NOT use relationship depth to bypass verification, privacy, or access control.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_WESLR_HOME = "/data/data/com.termux/files/home/.weslr"
RELATIONSHIPS_DIR = "relationships"
OBSERVATIONS_FILE = "relationship_observations.jsonl"
RELATIONSHIPS_VERSION = 1

# Relationship stages
class RelationshipStage(str, Enum):
    UNKNOWN = "unknown"
    FIRST_CONTACT = "first_contact"
    EARLY = "early"
    DEVELOPING = "developing"
    ESTABLISHED = "established"
    DEEP = "deep"


# Interaction signals
class InteractionSignal(str, Enum):
    # Positive / depth-building
    VERIFIED_SESSION_INTERACTION = "verified_session_interaction"
    SHARED_WORK_COMPLETED = "shared_work_completed"
    USER_PREFERENCE_SAVED = "user_preference_saved"
    SUCCESSFUL_FOLLOWUP = "successful_followup"
    CORRECTION_RESOLVED = "correction_resolved"
    MEMORY_CONFIRMED = "memory_confirmed"
    USER_POSITIVE_FEEDBACK = "user_positive_feedback"
    REPEATED_RETURN = "repeated_return"
    CORRECTION_ACKNOWLEDGED = "correction_acknowledged"
    IDENTITY_VERIFIED_THIS_SESSION = "identity_verified_this_session"

    # Neutral
    SIMPLE_QUESTION = "simple_question"
    ONE_OFF_TASK = "one_off_task"
    SYSTEM_STATUS = "system_status"
    UNKNOWN_SIGNAL = "unknown_signal"

    # Negative / restraint-building
    USER_NEGATIVE_FEEDBACK = "user_negative_feedback"
    USER_CORRECTION = "user_correction"
    USER_IGNORED_PROACTIVE = "user_ignored_proactive"
    USER_REQUESTED_QUIET = "user_requested_quiet"
    USER_REJECTED_MEMORY_CLAIM = "user_rejected_memory_claim"
    IDENTITY_UNCERTAIN = "identity_uncertain"
    PRIVACY_BOUNDARY = "privacy_boundary"
    FALSE_MEMORY_CLAIM = "false_memory_claim"


# Score weights per signal
SIGNAL_WEIGHTS: dict[str, float] = {
    InteractionSignal.VERIFIED_SESSION_INTERACTION.value: 0.02,
    InteractionSignal.SHARED_WORK_COMPLETED.value: 0.05,
    InteractionSignal.USER_PREFERENCE_SAVED.value: 0.03,
    InteractionSignal.SUCCESSFUL_FOLLOWUP.value: 0.03,
    InteractionSignal.CORRECTION_RESOLVED.value: 0.02,
    InteractionSignal.CORRECTION_ACKNOWLEDGED.value: 0.01,
    InteractionSignal.MEMORY_CONFIRMED.value: 0.04,
    InteractionSignal.USER_POSITIVE_FEEDBACK.value: 0.03,
    InteractionSignal.REPEATED_RETURN.value: 0.04,
    InteractionSignal.IDENTITY_VERIFIED_THIS_SESSION.value: 0.01,

    InteractionSignal.SIMPLE_QUESTION.value: 0.005,
    InteractionSignal.ONE_OFF_TASK.value: 0.005,
    InteractionSignal.SYSTEM_STATUS.value: 0.002,
    InteractionSignal.UNKNOWN_SIGNAL.value: 0.0,

    InteractionSignal.USER_NEGATIVE_FEEDBACK.value: -0.03,
    InteractionSignal.USER_CORRECTION.value: -0.02,
    InteractionSignal.USER_IGNORED_PROACTIVE.value: -0.02,
    InteractionSignal.USER_REQUESTED_QUIET.value: 0.0,  # restraint, not depth loss
    InteractionSignal.USER_REJECTED_MEMORY_CLAIM.value: -0.10,
    InteractionSignal.IDENTITY_UNCERTAIN.value: -0.05,
    InteractionSignal.PRIVACY_BOUNDARY.value: -0.01,
    InteractionSignal.FALSE_MEMORY_CLAIM.value: -0.10,
}

# Stage thresholds
STAGE_THRESHOLDS: list[tuple[float, float, RelationshipStage]] = [
    (0.00, 0.05, RelationshipStage.UNKNOWN),
    (0.05, 0.15, RelationshipStage.FIRST_CONTACT),
    (0.15, 0.30, RelationshipStage.EARLY),
    (0.30, 0.55, RelationshipStage.DEVELOPING),
    (0.55, 0.80, RelationshipStage.ESTABLISHED),
    (0.80, 1.00, RelationshipStage.DEEP),
]

# Identity caps: max relationship_depth by known_user_status
IDENTITY_DEPTH_CAPS: dict[str, float] = {
    "unknown": 0.05,
    "claimed": 0.10,
    "onboarded_unverified": 0.20,
    "profile_only": 0.20,
    "channel_verified": 1.00,
    "device_verified": 1.00,
    "test_verified": 1.00,
}

# Decay settings
INACTIVITY_DECAY_DAYS = 60
DECAY_RATE_PER_DAY = 0.005  # ~0.3 per month of inactivity


# ── Paths ──────────────────────────────────────────────────────────────────

def relationships_base(base_path: Optional[str] = None) -> str:
    if base_path:
        return base_path
    return os.path.join(DEFAULT_WESLR_HOME, RELATIONSHIPS_DIR)


def observations_path(base_path: Optional[str] = None) -> str:
    return os.path.join(relationships_base(base_path), OBSERVATIONS_FILE)


# ── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class RelationshipObservation:
    """One observation of an interaction event affecting relationship depth."""
    observation_id: str = ""
    timestamp: str = ""
    subject_entity_type: str = ""   # person, company, project, etc.
    subject_entity_id: str = ""
    target_entity_type: str = ""    # system, project, person, etc.
    target_entity_id: str = ""
    channel_id: str = ""
    interaction_signal: str = ""
    weight: float = 0.0
    confidence: float = 1.0
    verified: bool = False
    source: str = "explicit"
    metadata: dict = field(default_factory=dict)
    limitations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "RelationshipObservation":
        known = {
            k: v for k, v in d.items()
            if k in (
                "observation_id", "timestamp", "subject_entity_type",
                "subject_entity_id", "target_entity_type", "target_entity_id",
                "channel_id", "interaction_signal", "weight", "confidence",
                "verified", "source", "metadata", "limitations",
            )
        }
        return RelationshipObservation(**known)


@dataclass
class RelationshipState:
    """
    Current computed relationship state for a subject↔target entity pair.
    relationship_depth is NOT identity verification.
    """
    subject_entity_type: str = ""
    subject_entity_id: str = ""
    target_entity_type: str = ""
    target_entity_id: str = ""
    relationship_depth: float = 0.0
    relationship_stage: str = RelationshipStage.UNKNOWN.value
    confidence: float = 0.0
    verified_interaction_count: int = 0
    memory_count: int = 0
    session_count: int = 0
    positive_signal_count: int = 0
    negative_signal_count: int = 0
    neutral_signal_count: int = 0
    last_interaction_at: Optional[str] = None
    first_interaction_at: Optional[str] = None
    evidence: list = field(default_factory=list)
    limitations: list = field(default_factory=list)
    state_version: int = RELATIONSHIPS_VERSION

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "RelationshipState":
        known = {
            k: v for k, v in d.items()
            if k in (
                "subject_entity_type", "subject_entity_id", "target_entity_type",
                "target_entity_id", "relationship_depth", "relationship_stage",
                "confidence", "verified_interaction_count", "memory_count",
                "session_count", "positive_signal_count", "negative_signal_count",
                "neutral_signal_count", "last_interaction_at", "first_interaction_at",
                "evidence", "limitations", "state_version",
            )
        }
        return RelationshipState(**known)


# ── Observation CRUD ─────────────────────────────────────────────────────────

def create_relationship_observation(
    subject_entity_type: str,
    subject_entity_id: str,
    interaction_signal: str,
    target_entity_type: str = "system",
    target_entity_id: str = "weslr",
    channel_id: str = "",
    weight: Optional[float] = None,
    confidence: float = 1.0,
    verified: bool = False,
    source: str = "explicit",
    metadata: Optional[dict] = None,
    limitations: Optional[list] = None,
) -> RelationshipObservation:
    """Create a new relationship observation with generated ID and timestamp."""
    now = datetime.now(timezone.utc).isoformat()
    signal_weight = weight if weight is not None else SIGNAL_WEIGHTS.get(interaction_signal, 0.0)
    return RelationshipObservation(
        observation_id=uuid.uuid4().hex[:16],
        timestamp=now,
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        channel_id=channel_id,
        interaction_signal=interaction_signal,
        weight=signal_weight,
        confidence=confidence,
        verified=verified,
        source=source,
        metadata=metadata or {},
        limitations=limitations or [],
    )


def append_relationship_observation(
    observation: RelationshipObservation,
    base_path: Optional[str] = None,
) -> None:
    """Append an observation to the relationship observations file."""
    path = observations_path(base_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(observation.to_dict()) + "\n")


def load_relationship_observations(
    subject_entity_type: str,
    subject_entity_id: str,
    target_entity_type: Optional[str] = None,
    target_entity_id: Optional[str] = None,
    base_path: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 200,
) -> list[RelationshipObservation]:
    """
    Load relationship observations for a subject entity.
    Optionally filter by target entity.
    """
    path = observations_path(base_path)
    if not os.path.isfile(path):
        return []

    results: list[RelationshipObservation] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                obs = RelationshipObservation.from_dict(d)
                if obs.subject_entity_type != subject_entity_type:
                    continue
                if obs.subject_entity_id != subject_entity_id:
                    continue
                if target_entity_type and obs.target_entity_type != target_entity_type:
                    continue
                if target_entity_id and obs.target_entity_id != target_entity_id:
                    continue
                if since and obs.timestamp < since:
                    continue
                results.append(obs)
            except Exception:
                continue

    results.sort(key=lambda o: o.timestamp, reverse=True)
    return results[:limit]


# ── State computation ───────────────────────────────────────────────────────

def compute_relationship_state(
    observations: list[RelationshipObservation],
    identity_status: str = "unknown",
    inactivity_days: int = 0,
) -> RelationshipState:
    """
    Compute relationship state from a list of observations.

    identity_status is used to cap the final relationship_depth.
    inactivity_days is used to apply decay if relationship is inactive.
    """
    if not observations:
        return RelationshipState(
            subject_entity_type=observations[0].subject_entity_type if observations else "",
            subject_entity_id=observations[0].subject_entity_id if observations else "",
            target_entity_type=observations[0].target_entity_type if observations else "system",
            target_entity_id=observations[0].target_entity_id if observations else "weslr",
            relationship_stage=RelationshipStage.UNKNOWN.value,
        )

    first_obs = observations[-1]
    last_obs = observations[0]

    # Aggregate signals
    positive_count = sum(
        1 for o in observations
        if o.weight > 0 and o.interaction_signal not in (
            InteractionSignal.SIMPLE_QUESTION.value,
            InteractionSignal.ONE_OFF_TASK.value,
            InteractionSignal.SYSTEM_STATUS.value,
        )
    )
    negative_count = sum(1 for o in observations if o.weight < 0)
    neutral_count = sum(1 for o in observations if o.weight == 0)
    verified_count = sum(1 for o in observations if o.verified)

    # Sum weights from verified observations only for conservative depth
    verified_weight = sum(o.weight for o in observations if o.verified and o.weight > 0)
    unverified_weight = sum(o.weight for o in observations if not o.verified and o.weight > 0)

    # Start with verified weight, add unverified at 50% confidence
    raw_depth = verified_weight + (unverified_weight * 0.5)

    # Apply identity cap
    cap = IDENTITY_DEPTH_CAPS.get(identity_status, 0.05)
    depth = min(raw_depth, cap)

    # Apply inactivity decay
    if inactivity_days > INACTIVITY_DECAY_DAYS:
        decay = (inactivity_days - INACTIVITY_DECAY_DAYS) * DECAY_RATE_PER_DAY
        depth = max(0.0, depth - decay)

    # Confidence: based on observation count and verification rate
    obs_count = len(observations)
    if obs_count == 0:
        conf = 0.0
    elif obs_count < 3:
        conf = 0.2
    elif obs_count < 10:
        conf = 0.5
    else:
        conf = 0.8
    # Reduce confidence if many unverified observations
    if verified_count == 0 and obs_count > 5:
        conf = min(conf, 0.3)

    # Classify stage
    stage = classify_relationship_stage(depth, conf)

    return RelationshipState(
        subject_entity_type=first_obs.subject_entity_type,
        subject_entity_id=first_obs.subject_entity_id,
        target_entity_type=first_obs.target_entity_type,
        target_entity_id=first_obs.target_entity_id,
        relationship_depth=round(depth, 4),
        relationship_stage=stage.value,
        confidence=round(conf, 4),
        verified_interaction_count=verified_count,
        memory_count=sum(1 for o in observations if o.interaction_signal == InteractionSignal.MEMORY_CONFIRMED.value),
        session_count=len(set(o.channel_id for o in observations if o.channel_id)),
        positive_signal_count=positive_count,
        negative_signal_count=negative_count,
        neutral_signal_count=neutral_count,
        last_interaction_at=last_obs.timestamp,
        first_interaction_at=first_obs.timestamp,
        evidence=[o.interaction_signal for o in observations[:20]],
        limitations=[
            "relationship_depth is NOT identity verification",
            "relationship_depth does NOT grant memory access",
            "relationship_depth does NOT imply emotional attachment",
            "relationship depth is capped by identity status",
        ],
    )


def classify_relationship_stage(depth: float, confidence: float) -> RelationshipStage:
    """Classify relationship stage from depth score and confidence."""
    if confidence < 0.2:
        return RelationshipStage.UNKNOWN
    for low, high, stage in STAGE_THRESHOLDS:
        if low <= depth < high:
            return stage
    if depth >= 0.80:
        return RelationshipStage.DEEP
    return RelationshipStage.UNKNOWN


def decay_relationship_depth_if_inactive(
    state: RelationshipState,
    last_interaction_at: Optional[str] = None,
    now: Optional[str] = None,
) -> RelationshipState:
    """
    Apply decay if the relationship has been inactive.
    Returns updated state (does not mutate original).
    """
    if not last_interaction_at:
        last_interaction_at = state.last_interaction_at
    if not last_interaction_at:
        return state

    from datetime import datetime as dt, timezone as tz
    if now:
        current = dt.fromisoformat(now)
    else:
        current = dt.now(tz.utc)

    last = dt.fromisoformat(last_interaction_at)
    inactive_days = (current - last).days

    if inactive_days > INACTIVITY_DECAY_DAYS:
        decay = (inactive_days - INACTIVITY_DECAY_DAYS) * DECAY_RATE_PER_DAY
        new_depth = max(0.0, state.relationship_depth - decay)
        new_stage = classify_relationship_stage(new_depth, state.confidence)
        return RelationshipState(
            **{**asdict(state),
               "relationship_depth": round(new_depth, 4),
               "relationship_stage": new_stage.value,
               "limitations": state.limitations + [f"decayed {decay:.3f} after {inactive_days} inactive days"]}
        )

    return state


# ── High-level API ─────────────────────────────────────────────────────────

def record_interaction_outcome(
    subject_entity_type: str,
    subject_entity_id: str,
    signal: str,
    verified: bool = False,
    weight: Optional[float] = None,
    target_entity_type: str = "system",
    target_entity_id: str = "weslr",
    channel_id: str = "",
    source: str = "explicit",
    base_path: Optional[str] = None,
) -> RelationshipObservation:
    """
    Record an interaction outcome and append to observation log.
    Returns the created observation.
    """
    obs = create_relationship_observation(
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        interaction_signal=signal,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        channel_id=channel_id,
        weight=weight,
        verified=verified,
        source=source,
    )
    append_relationship_observation(obs, base_path=base_path)
    return obs


def get_relationship_depth_for_identity(
    identity_status: str,
    subject_entity_type: str,
    subject_entity_id: str,
    base_path: Optional[str] = None,
) -> RelationshipState:
    """
    Get relationship state for a given identity and subject entity.
    Loads all relevant observations and computes state.
    """
    observations = load_relationship_observations(
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        base_path=base_path,
    )
    return compute_relationship_state(observations, identity_status=identity_status)


# ── Summarize ────────────────────────────────────────────────────────────────

def summarize_relationship_state(state: RelationshipState) -> str:
    """
    Produce a bounded human-readable summary of relationship state.
    Does NOT claim personhood verification or emotional attachment.
    """
    parts = [
        f"depth={state.relationship_stage} ({state.relationship_depth:.2f})",
        f"conf={state.confidence:.2f}",
    ]
    if state.positive_signal_count > 0:
        parts.append(f"positive={state.positive_signal_count}")
    if state.negative_signal_count > 0:
        parts.append(f"negative={state.negative_signal_count}")
    if state.verified_interaction_count > 0:
        parts.append(f"verified={state.verified_interaction_count}")
    if state.last_interaction_at:
        parts.append(f"last={state.last_interaction_at[:10]}")
    return " ".join(parts)


def get_relationship_tone(depth: float, stage: str) -> dict[str, Any]:
    """
    Return tone/expression parameters derived from relationship depth.
    Used ONLY for expression, not for truth or access.
    """
    tone: dict[str, Any] = {
        "verbosity": "medium",
        "warmth": "neutral",
        "proactive": False,
        "explanatory": True,
        "greeting_style": "standard",
        "initiative_level": "normal",
    }

    if stage == RelationshipStage.UNKNOWN.value or depth < 0.05:
        tone["warmth"] = "reserved"
        tone["verbosity"] = "brief"
        tone["greeting_style"] = "cautious"
        tone["explanatory"] = True
    elif stage == RelationshipStage.FIRST_CONTACT.value:
        tone["warmth"] = "warm"
        tone["verbosity"] = "medium"
        tone["greeting_style"] = "introductory"
        tone["explanatory"] = True
    elif stage == RelationshipStage.EARLY.value:
        tone["warmth"] = "warm"
        tone["verbosity"] = "medium"
        tone["greeting_style"] = "friendly"
        tone["explanatory"] = True
    elif stage == RelationshipStage.DEVELOPING.value:
        tone["warmth"] = "warm"
        tone["verbosity"] = "medium"
        tone["greeting_style"] = "familiar"
        tone["explanatory"] = True
        tone["proactive"] = True
    elif stage == RelationshipStage.ESTABLISHED.value:
        tone["warmth"] = "familiar"
        tone["verbosity"] = "concise"
        tone["greeting_style"] = "established"
        tone["explanatory"] = False
        tone["proactive"] = True
        tone["initiative_level"] = "elevated"
    elif stage == RelationshipStage.DEEP.value:
        tone["warmth"] = "familiar"
        tone["verbosity"] = "concise"
        tone["greeting_style"] = "established"
        tone["explanatory"] = False
        tone["proactive"] = True
        tone["initiative_level"] = "high"

    return tone


def relationship_state_path(
    subject_entity_type: str,
    subject_entity_id: str,
    target_entity_type: str = "system",
    target_entity_id: str = "weslr",
    base_path: Optional[str] = None,
) -> str:
    """Return path to a cached relationship state file (optional)."""
    base = relationships_base(base_path)
    return os.path.join(
        base,
        f"{subject_entity_type}_{subject_entity_id}_{target_entity_type}_{target_entity_id}_state.json",
    )


def save_relationship_state(
    state: RelationshipState,
    base_path: Optional[str] = None,
) -> None:
    """Save relationship state to a state file."""
    path = relationship_state_path(
        state.subject_entity_type,
        state.subject_entity_id,
        state.target_entity_type,
        state.target_entity_id,
        base_path=base_path,
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state.to_dict(), f, indent=2)


def load_relationship_state(
    subject_entity_type: str,
    subject_entity_id: str,
    target_entity_type: str = "system",
    target_entity_id: str = "weslr",
    base_path: Optional[str] = None,
) -> Optional[RelationshipState]:
    """Load cached relationship state if it exists."""
    path = relationship_state_path(
        subject_entity_type, subject_entity_id,
        target_entity_type, target_entity_id,
        base_path=base_path,
    )
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return RelationshipState.from_dict(json.load(f))
    except Exception:
        return None
