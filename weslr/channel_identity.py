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
from enum import Enum
from typing import Any, Dict, List, Optional


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


def load_profile(home: str = DEFAULT_WESLR_HOME) -> Optional[Dict[str, Any]]:
    """Load user profile from ~/.weslr/user_profile.json if it exists."""
    import os, json as _json
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
    import os, json as _json
    path = os.path.join(home, CHANNEL_BINDING_FILE)
    if os.path.isfile(path):
        try:
            with open(path) as f:
                return _json.load(f)
        except Exception:
            return None
    return None


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
