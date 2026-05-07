"""weslr/channel_identity.py — Channel Identity Evidence Model

Bounded identity evidence for the meaning-vector response path.
Separates three concerns:

- Profile:       what WESLR has been told about a user
- Verification:   why WESLR believes this session/channel is that user
- Memory:        what WESLR can verify from stored information / shared work

Rules:
- Text self-claims ("I am Arthur") are ONLY claims, not verification.
- No hidden permanent identity writes.
- Profile and channel binding are separate.
- All fields are optional — the model degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json as _json
from typing import Any, Dict, List, Optional, Union


class IdentityStatus(str, Enum):
    """Identity confidence level for a given session/channel."""

    UNKNOWN = "unknown"              # No identity signal at all
    CLAIMED = "claimed"              # User claimed an identity (text only)
    ONBOARDED = "onboarded"          # Profile exists but session not verified
    CHANNEL_VERIFIED = "channel_verified"   # Channel-level evidence binds profile
    DEVICE_VERIFIED = "device_verified"     # Device/node-level evidence
    TEST_VERIFIED = "test_verified"         # Explicit test fixture only


@dataclass
class ChannelIdentityEvidence:
    """Bounded evidence record for session/channel identity."""

    # Who — profile
    profile_name: Optional[str] = None
    profile_status: Optional[str] = None  # "onboarded", "test", etc.

    # How verified — verification method
    identity_status: IdentityStatus = IdentityStatus.UNKNOWN
    channel_type: Optional[str] = None          # e.g. "local_cli", "local_stt", "webchat", "signal"
    channel_id: Optional[str] = None           # platform channel/session ID
    device_id: Optional[str] = None              # node device ID if known
    session_id: Optional[str] = None            # WESLR/OpenClaw session ID

    # Confidence (0.0–1.0) — how much we trust this session belongs to profile
    confidence: float = 0.0

    # Raw evidence list — what sources contributed to this confidence
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    # What we explicitly cannot claim
    limitations: List[str] = field(default_factory=list)

    def is_verified(self) -> bool:
        return self.identity_status in (
            IdentityStatus.CHANNEL_VERIFIED,
            IdentityStatus.DEVICE_VERIFIED,
            IdentityStatus.TEST_VERIFIED,
        )

    def as_metadata(self) -> Dict[str, Any]:
        """Convert to dict for passing through the meaning-vector path."""
        return {
            "sender_identity": self.profile_name,
            "known_user_status": self.identity_status.value,
            "sender_confidence": self.confidence,
            "identity_evidence": self.evidence,
            "profile_status": self.profile_status,
            "channel_type": self.channel_type,
            "channel_id": self.channel_id,
            "session_id": self.session_id,
            "device_id": self.device_id,
        }

    @classmethod
    def from_request_metadata(cls, meta: Dict[str, Any]) -> "ChannelIdentityEvidence":
        """Reconstruct evidence from a metadata dict (e.g. routed through ingress)."""
        status_raw = meta.get("known_user_status", "unknown")
        try:
            status = IdentityStatus(status_raw)
        except ValueError:
            status = IdentityStatus.UNKNOWN

        return cls(
            profile_name=meta.get("sender_identity"),
            profile_status=meta.get("profile_status"),
            identity_status=status,
            channel_type=meta.get("channel_type"),
            channel_id=meta.get("channel_id"),
            device_id=meta.get("device_id"),
            session_id=meta.get("session_id"),
            confidence=meta.get("sender_confidence", 0.0),
            evidence=meta.get("identity_evidence", []),
            limitations=meta.get("identity_limitations", []),
        )


# ── Profile loading ─────────────────────────────────────────────────────────

DEFAULT_WESLR_HOME = "/data/data/com.termux/files/home/.weslr"
PROFILE_FILE = "user_profile.json"
CHANNEL_BINDING_FILE = "channel_identity.json"
BINDING_VERSION = 1

# Evidence type strengths
class EvidenceStrength(str, Enum):
    STRONG = "strong"       # explicit operator binding, local device identity
    MEDIUM = "medium"       # session ID match
    WEAK = "weak"           # IP/LAN match, text self-claim


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_profile(home: str = DEFAULT_WESLR_HOME) -> Optional[Dict[str, Any]]:
    """Load user profile from ~/.weslr/user_profile.json if it exists."""
    import os
    path = os.path.join(home, PROFILE_FILE)
    if os.path.isfile(path):
        try:
            with open(path) as f:
                return _json.load(f)
        except Exception:
            return None
    return None


def load_channel_binding(home: str = DEFAULT_WESLR_HOME) -> Optional[Dict[str, Any]]:
    """Load channel binding from ~/.weslr/channel_identity.json if it exists."""
    import os
    path = os.path.join(home, CHANNEL_BINDING_FILE)
    if os.path.isfile(path):
        try:
            with open(path) as f:
                return _json.load(f)
        except Exception:
            return None
    return None


def binding_exists(home: str = DEFAULT_WESLR_HOME) -> bool:
    """Return True if channel binding file exists."""
    import os
    return os.path.isfile(os.path.join(home, CHANNEL_BINDING_FILE))


# ── Channel binding dataclass ────────────────────────────────────────────────

@dataclass
class ChannelBinding:
    """
    Explicit channel-to-profile binding.
    Created by operator command, references a profile user_id.
    identity_status may be channel_verified only with strong evidence.
    """
    binding_version: int = BINDING_VERSION
    binding_id: str = ""
    channel_type: str = "local_cli"
    channel_id: str = ""
    bound_user_id: str = ""
    bound_profile_name: str = ""
    identity_status: str = "onboarded_unverified"
    confidence: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    created_by: str = ""
    evidence: list = field(default_factory=list)
    limitations: list = field(default_factory=list)
    trusted: bool = False

    def to_dict(self) -> dict:
        return {
            "binding_version": self.binding_version,
            "binding_id": self.binding_id,
            "channel_type": self.channel_type,
            "channel_id": self.channel_id,
            "bound_user_id": self.bound_user_id,
            "bound_profile_name": self.bound_profile_name,
            "identity_status": self.identity_status,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "evidence": self.evidence,
            "limitations": self.limitations,
            "trusted": self.trusted,
        }

    @staticmethod
    def from_dict(d: dict) -> "ChannelBinding":
        return ChannelBinding(
            binding_version=d.get("binding_version", BINDING_VERSION),
            binding_id=d.get("binding_id", ""),
            channel_type=d.get("channel_type", "local_cli"),
            channel_id=d.get("channel_id", ""),
            bound_user_id=d.get("bound_user_id", ""),
            bound_profile_name=d.get("bound_profile_name", ""),
            identity_status=d.get("identity_status", "onboarded_unverified"),
            confidence=d.get("confidence", 0.0),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            created_by=d.get("created_by", ""),
            evidence=d.get("evidence", []),
            limitations=d.get("limitations", []),
            trusted=d.get("trusted", False),
        )


def default_channel_binding(
    profile_user_id: str,
    profile_name: str,
    channel_type: str = "local_cli",
    channel_id: Optional[str] = None,
    created_by: str = "explicit_operator_binding",
) -> ChannelBinding:
    """Create a new channel binding referencing a profile user_id."""
    import uuid, os
    now = _now_iso()
    # Determine default channel_id if not provided
    if not channel_id:
        if channel_type == "local_cli":
            # Use session ID from OpenClaw if available, else generate
            session_id = os.environ.get("OPENCLAW_SESSION_ID", "")
            channel_id = f"local_cli:{session_id or uuid.uuid4().hex[:12]}"
        else:
            channel_id = f"{channel_type}:{uuid.uuid4().hex[:12]}"

    return ChannelBinding(
        binding_id=uuid.uuid4().hex[:16],
        channel_type=channel_type,
        channel_id=channel_id,
        bound_user_id=profile_user_id,
        bound_profile_name=profile_name,
        identity_status="onboarded_unverified",
        confidence=0.0,
        created_at=now,
        updated_at=now,
        created_by=created_by,
        evidence=[
            {
                "type": "explicit_operator_binding",
                "strength": EvidenceStrength.STRONG.value,
                "detail": "Operator explicitly bound this channel to the profile",
            }
        ],
        limitations=[
            "IP address alone is not sufficient for identity verification",
            "This binding verifies the local channel, not a biometric person",
        ],
        trusted=False,
    )


def add_ip_evidence(binding: ChannelBinding, ip_address: str, lan_address: Optional[str] = None) -> ChannelBinding:
    """Add IP/LAN evidence to binding. Strength is weak — never sufficient alone."""
    import copy
    b = copy.deepcopy(binding)
    ip_entry = {
        "type": "local_ip_match",
        "strength": EvidenceStrength.WEAK.value,
        "detail": f"Local IP {ip_address} matched",
        "ip_address": ip_address,
    }
    if lan_address:
        ip_entry["lan_address"] = lan_address
    b.evidence.append(ip_entry)
    return b


def compute_binding_confidence(binding: ChannelBinding) -> float:
    """
    Compute confidence from evidence. Returns 0.0–1.0.
    STRONG evidence alone can give ~0.85. WEAK evidence alone gives max 0.35.
    """
    weights = {
        EvidenceStrength.STRONG.value: 0.85,
        EvidenceStrength.MEDIUM.value: 0.55,
        EvidenceStrength.WEAK.value: 0.30,
    }
    max_score = 0.0
    for ev in binding.evidence:
        strength = ev.get("strength", EvidenceStrength.WEAK.value)
        score = weights.get(strength, 0.0)
        if score > max_score:
            max_score = score
    # If only weak evidence, cap at 0.35 (never verified alone)
    all_weak = all(
        ev.get("strength", EvidenceStrength.WEAK.value) == EvidenceStrength.WEAK.value
        for ev in binding.evidence
    )
    if all_weak:
        return min(max_score, 0.35)
    return max_score


def finalize_binding(binding: ChannelBinding) -> ChannelBinding:
    """
    Finalize binding: compute confidence, set identity_status.
    Only becomes channel_verified when STRONG evidence exists.
    """
    import copy
    b = copy.deepcopy(binding)
    b.updated_at = _now_iso()
    b.confidence = compute_binding_confidence(b)

    # Determine identity_status from evidence strength
    has_strong = any(
        ev.get("strength") == EvidenceStrength.STRONG.value
        for ev in b.evidence
    )
    has_medium = any(
        ev.get("strength") == EvidenceStrength.MEDIUM.value
        for ev in b.evidence
    )
    if has_strong:
        b.identity_status = "channel_verified"
        b.trusted = True
    elif has_medium:
        b.identity_status = "onboarded_unverified"
        b.trusted = False
    else:
        b.identity_status = "onboarded_unverified"
        b.trusted = False
        b.confidence = min(b.confidence, 0.35)

    return b


def save_channel_binding(
    binding: ChannelBinding,
    path: Optional[str] = None,
    backup: bool = True,
) -> None:
    """Save channel binding. Optionally backup existing file."""
    import os
    if path is None:
        path = os.path.join(DEFAULT_WESLR_HOME, CHANNEL_BINDING_FILE)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if backup and os.path.isfile(path):
        try:
            with open(path) as src:
                with open(path + ".bak", "w") as dst:
                    dst.write(src.read())
        except Exception:
            pass

    binding.updated_at = _now_iso()
    with open(path, "w") as f:
        _json.dump(binding.to_dict(), f, indent=2)


def load_binding(path: Optional[str] = None) -> Optional[ChannelBinding]:
    """Load binding from path. Returns None if not found."""
    import os
    if path is None:
        path = os.path.join(DEFAULT_WESLR_HOME, CHANNEL_BINDING_FILE)
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return ChannelBinding.from_dict(_json.load(f))
    except Exception:
        return None


def validate_binding(binding: ChannelBinding, profile_user_id: Optional[str] = None) -> tuple[bool, list[str]]:
    """
    Validate binding. Rejects bindings without profile user_id reference.
    Returns (is_valid, list_of_reasons).
    """
    reasons = []
    if not binding.bound_user_id:
        reasons.append("bound_user_id is required — binding must reference a profile")
    if profile_user_id and binding.bound_user_id != profile_user_id:
        reasons.append(f"bound_user_id '{binding.bound_user_id}' does not match profile user_id '{profile_user_id}'")
    if binding.binding_id and len(binding.binding_id) < 4:
        reasons.append("binding_id must be at least 4 characters")
    valid_statuses = {"onboarded_unverified", "channel_verified", "claimed"}
    if binding.identity_status not in valid_statuses:
        reasons.append(
            f"identity_status must be one of {valid_statuses}, got '{binding.identity_status}'"
        )
    return (len(reasons) == 0, reasons)


def summarize_binding(binding: ChannelBinding) -> str:
    """Bounded summary for display. No overclaim of personhood."""
    parts = [
        f"channel_type={binding.channel_type}",
        f"channel_id={binding.channel_id}",
        f"identity_status={binding.identity_status}",
        f"confidence={binding.confidence:.2f}",
        f"bound_user_id={binding.bound_user_id}",
    ]
    ev_types = [e.get("type") for e in binding.evidence[:3]]
    if ev_types:
        parts.append(f"evidence={[ev_types]}")
    return " ".join(parts)


def build_channel_identity_evidence(
    profile: Optional[Dict[str, Any]] = None,
    channel_binding: Optional[Dict[str, Any]] = None,
    channel_type: str = "local_cli",
    session_id: Optional[str] = None,
    device_id: Optional[str] = None,
    explicit_test_name: Optional[str] = None,
) -> ChannelIdentityEvidence:
    """
    Build identity evidence from available sources.

    Priority (highest → lowest):
    1. explicit_test_name → TEST_VERIFIED (only for test fixtures)
    2. channel_binding[trusted=true] + profile → CHANNEL_VERIFIED / DEVICE_VERIFIED
    3. profile exists → ONBOARDED (no channel verification)
    4. channel_binding untrusted → CLAIMED
    5. nothing → UNKNOWN
    """
    limitations: List[str] = []

    # Explicit test — highest trust, clearly marked
    if explicit_test_name:
        return ChannelIdentityEvidence(
            profile_name=explicit_test_name,
            profile_status="test_verified",
            identity_status=IdentityStatus.TEST_VERIFIED,
            channel_type=channel_type,
            session_id=session_id,
            device_id=device_id,
            confidence=1.0,
            evidence=[{"source": "test_fixture", "name": explicit_test_name}],
            limitations=["Test-only identity — not valid in production."],
        )

    # Channel binding + profile
    if channel_binding and channel_binding.get("trusted") and profile:
        binding_confidence = channel_binding.get("confidence", 0.85)
        return ChannelIdentityEvidence(
            profile_name=channel_binding.get("bound_profile") or profile.get("display_name"),
            profile_status=profile.get("profile_status", "onboarded"),
            identity_status=(
                IdentityStatus.DEVICE_VERIFIED
                if channel_binding.get("channel_type") == "local_device"
                else IdentityStatus.CHANNEL_VERIFIED
            ),
            channel_type=channel_type,
            channel_id=channel_binding.get("channel_id"),
            device_id=device_id,
            session_id=session_id,
            confidence=binding_confidence,
            evidence=[
                {"source": "channel_binding", "file": CHANNEL_BINDING_FILE},
                {"source": "user_profile", "file": PROFILE_FILE},
            ],
            limitations=[
                "Bounded to local device/channel.",
                "Confidence based on file-based binding, not cryptographic proof.",
            ],
        )

    # Profile exists but no channel binding
    if profile:
        status = IdentityStatus.ONBOARDED if channel_binding else IdentityStatus.CLAIMED
        limitations.append("Session not verified against profile.")
        return ChannelIdentityEvidence(
            profile_name=profile.get("display_name"),
            profile_status=profile.get("profile_status"),
            identity_status=status,
            channel_type=channel_type,
            session_id=session_id,
            confidence=0.4 if status == IdentityStatus.CLAIMED else 0.6,
            evidence=[{"source": "user_profile", "file": PROFILE_FILE}]
            if profile
            else [],
            limitations=limitations,
        )

    # Channel binding exists but no profile
    if channel_binding:
        return ChannelIdentityEvidence(
            identity_status=IdentityStatus.UNKNOWN,
            channel_type=channel_type,
            channel_id=channel_binding.get("channel_id"),
            session_id=session_id,
            confidence=0.0,
            evidence=[{"source": "channel_binding", "file": CHANNEL_BINDING_FILE}],
            limitations=["No profile; identity cannot be established."],
        )

    # Nothing
    return ChannelIdentityEvidence(
        identity_status=IdentityStatus.UNKNOWN,
        channel_type=channel_type,
        session_id=session_id,
        confidence=0.0,
        evidence=[],
        limitations=["No identity signal available."],
    )
