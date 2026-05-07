"""
weslr/weight_observation.py

Structured recording of response quality observations.
Used to build evidence for cognitive weight change proposals.

All observations are append-only. No edits or deletes.
Safe content: response path, obligation type, candidate type, severity, evidence.
Never stores raw private message content unless explicitly marked safe.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
from datetime import datetime, timezone
import json
import os
import uuid

OBS_DEFAULT_PATH = os.path.expanduser("~/.weslr/weight_observations.jsonl")
PROJECT_OBS_PATH = ".weslr_state/weight_observations.jsonl"

# ── Outcome ───────────────────────────────────────────────────────────────────

ObservationOutcome = Literal["success", "partial", "failure", "unknown"]

# ── Issue types ────────────────────────────────────────────────────────────────

IssueType = Literal[
    "meaning_missed",
    "wrong_obligation",
    "weak_response",
    "raw_memory_output",
    "identity_overclaim",
    "identity_underclaim",
    "too_generic",
    "too_verbose",
    "too_cold",
    "too_familiar",
    "good_response",
    "user_positive_signal",
    "user_negative_signal",
    "phrase_not_classified",
    "confidence_too_low",
    "confidence_too_high",
    "other",
]

Severity = Literal["negligible", "minor", "moderate", "significant", "critical"]

Source = Literal["user_feedback", "self_review", "test_failure", "test_regression", "smoke_check", "operator_review"]

# ── Dataclass ───────────────────────────────────────────────────────────────────


@dataclass
class WeightObservation:
    observation_id: str
    timestamp: str          # ISO-8601
    message_hash: Optional[str]   # SHA-256 of message text if safe to record
    response_path: str     # e.g. "meaning-vector:verify_identity:identity_verification"
    obligation_type: str
    candidate_type: Optional[str]
    outcome: ObservationOutcome
    issue_type: IssueType
    severity: Severity
    evidence: list[str]     # human-readable evidence strings
    suggested_area: str     # weight key area, e.g. "meaning.identity_query_weight"
    safe_to_learn: bool     # if False, observation should not support proposals
    source: Source
    notes: Optional[str] = None

    def dict(self) -> dict:
        return asdict(self)

    @classmethod
    def create(
        cls,
        message: str,
        response_path: str,
        obligation_type: str,
        candidate_type: Optional[str],
        outcome: ObservationOutcome,
        issue_type: IssueType,
        severity: Severity,
        evidence: list[str],
        suggested_area: str,
        safe_to_learn: bool = True,
        source: Source = "self_review",
        notes: Optional[str] = None,
    ) -> "WeightObservation":
        """Create a new observation with auto-generated ID, timestamp, hash."""
        import hashlib
        h = hashlib.sha256(message.encode()).hexdigest()[:16]
        return cls(
            observation_id=str(uuid.uuid4())[:8],
            timestamp=_now_iso(),
            message_hash=h,
            response_path=response_path,
            obligation_type=obligation_type,
            candidate_type=candidate_type,
            outcome=outcome,
            issue_type=issue_type,
            severity=severity,
            evidence=evidence,
            suggested_area=suggested_area,
            safe_to_learn=safe_to_learn,
            source=source,
            notes=notes,
        )


# ── Storage ───────────────────────────────────────────────────────────────────

def observations_path(path: Optional[str] = None) -> str:
    if path:
        return path
    if os.path.exists(PROJECT_OBS_PATH):
        return PROJECT_OBS_PATH
    return OBS_DEFAULT_PATH


def append_observation(obs: WeightObservation, path: Optional[str] = None) -> None:
    """Append one observation as JSONL line."""
    p = observations_path(path)
    os.makedirs(os.path.dirname(p) if os.path.dirname(p) else ".", exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(obs.dict()) + "\n")


def load_observations(limit: int = 500, path: Optional[str] = None) -> list[WeightObservation]:
    """Load recent observations (newest last)."""
    p = observations_path(path)
    if not os.path.exists(p):
        return []
    obs_list: list[WeightObservation] = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                obs_list.append(WeightObservation(**d))
            except Exception:
                continue
            if len(obs_list) >= limit:
                break
    return obs_list


def observations_for_area(area: str, limit: int = 200, path: Optional[str] = None) -> list[WeightObservation]:
    """Load observations relevant to a weight key area."""
    return [o for o in load_observations(limit, path) if o.suggested_area == area and o.safe_to_learn]


# ── Helper ───────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
