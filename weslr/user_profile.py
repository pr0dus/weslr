"""
WESLR User Profile

Provides explicit user/operator profile management.
Profile != verification — this is what the user has explicitly told WESLR about themselves.

Schema:
- display_name, preferred_name, role, relationship_to_weslr
- primary_projects, language_preferences, communication_preferences
- identity_status: "profile_only" | "onboarded_unverified" (never "verified" here)
- user_id: stable generated ID
- memberships: claims of membership in families/companies/institutions/teams/projects
- created_at, updated_at, created_by, notes

No channel verification, no device binding, no memory truth claims.
Membership claims are NOT verified unless channel/role evidence exists.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Paths ────────────────────────────────────────────────────────────────────

DEFAULT_WESLR_HOME = "/data/data/com.termux/files/home/.weslr"
PROFILE_FILE = "user_profile.json"
PROFILE_VERSION = 1


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class MembershipClaim:
    """A claim of membership/role in an entity. Not verified by default."""
    entity_type: str = ""
    entity_id: str = ""
    display_name: str = ""
    role: str = "unknown"
    relationship_type: str = "unknown"
    verified: bool = False
    confidence: float = 0.0
    source: str = ""
    evidence: list = field(default_factory=list)
    limitations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "MembershipClaim":
        known = {k: v for k, v in d.items() if k in (
            "entity_type", "entity_id", "display_name", "role",
            "relationship_type", "verified", "confidence", "source",
            "evidence", "limitations",
        )}
        return MembershipClaim(**known)


@dataclass
class UserProfile:
    """User/operator profile. identity_status must NOT be set to verified here."""
    profile_version: int = PROFILE_VERSION
    user_id: str = ""
    display_name: str = ""
    preferred_name: str = ""
    role: str = ""
    relationship_to_weslr: str = ""
    primary_projects: list = field(default_factory=list)
    language_preferences: dict = field(default_factory=lambda: {"primary": "en", "secondary": []})
    communication_preferences: dict = field(default_factory=lambda: {"tone": "balanced", "verbosity": "medium", "use_voice": True})
    identity_status: str = "profile_only"
    created_at: str = ""
    updated_at: str = ""
    created_by: str = ""
    notes: str = ""
    memberships: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "profile_version": self.profile_version,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "preferred_name": self.preferred_name,
            "role": self.role,
            "relationship_to_weslr": self.relationship_to_weslr,
            "primary_projects": self.primary_projects,
            "language_preferences": self.language_preferences,
            "communication_preferences": self.communication_preferences,
            "identity_status": self.identity_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "notes": self.notes,
            "memberships": [
                m.to_dict() if hasattr(m, 'to_dict') else m for m in self.memberships
            ],
        }
        return d


def default_profile(created_by: str = "profile_editor") -> UserProfile:
    now = datetime.now(timezone.utc).isoformat()
    return UserProfile(
        profile_version=PROFILE_VERSION,
        user_id=str(uuid.uuid4())[:16],
        display_name="",
        preferred_name="",
        role="",
        relationship_to_weslr="",
        primary_projects=[],
        language_preferences={"primary": "en", "secondary": []},
        communication_preferences={"tone": "balanced", "verbosity": "medium", "use_voice": True},
        identity_status="profile_only",
        created_at=now,
        updated_at=now,
        created_by=created_by,
        notes="",
        memberships=[],
    )


# ── Load / Save ─────────────────────────────────────────────────────────────

def _profile_path(path: Optional[str]) -> str:
    if path:
        return path
    return os.path.join(DEFAULT_WESLR_HOME, PROFILE_FILE)


def profile_exists(path: Optional[str] = None) -> bool:
    return os.path.isfile(_profile_path(path))


def load_user_profile(path: Optional[str] = None) -> Optional[UserProfile]:
    """Load user profile from path. Returns None if not found."""
    full = _profile_path(path)
    if not os.path.isfile(full):
        return None
    try:
        with open(full) as f:
            d = json.load(f)
        if "memberships" in d:
            d["memberships"] = [
                MembershipClaim.from_dict(m) if isinstance(m, dict) else m
                for m in d["memberships"]
            ]
        return UserProfile(**d)
    except Exception:
        return None


def save_user_profile(
    profile: UserProfile,
    path: Optional[str] = None,
    backup: bool = True,
) -> None:
    """Save profile to path. Optionally backup existing file first."""
    full = _profile_path(path)
    os.makedirs(os.path.dirname(full), exist_ok=True)

    if backup and os.path.isfile(full):
        backup_path = full + ".bak"
        try:
            with open(full) as src:
                with open(backup_path, "w") as dst:
                    dst.write(src.read())
        except Exception:
            pass  # backup failure is non-fatal

    profile.updated_at = datetime.now(timezone.utc).isoformat()
    with open(full, "w") as f:
        json.dump(profile.to_dict(), f, indent=2)


def update_user_profile(
    updates: Dict[str, Any],
    path: Optional[str] = None,
    backup: bool = True,
) -> UserProfile:
    """Apply updates to existing profile (or create new). Returns saved profile."""
    existing = load_user_profile(path)
    if existing is None:
        p = default_profile()
    else:
        p = existing

    for key, value in updates.items():
        if hasattr(p, key) and key not in ("profile_version", "user_id", "created_at", "created_by"):
            setattr(p, key, value)

    # Enforce identity_status safety
    if p.identity_status not in ("profile_only", "onboarded_unverified"):
        p.identity_status = "profile_only"

    save_user_profile(p, path=path, backup=backup)
    return p


# ── Validation ─────────────────────────────────────────────────────────────

VALID_IDENTITY_STATUSES = {"profile_only", "onboarded_unverified"}


def validate_user_profile(profile: UserProfile) -> tuple[bool, list[str]]:
    """
    Validate profile. Rejects any identity_status claiming verified identity.
    Returns (is_valid, list_of_reasons).
    """
    reasons = []

    if profile.identity_status not in VALID_IDENTITY_STATUSES:
        reasons.append(
            f"identity_status must be one of {VALID_IDENTITY_STATUSES}, "
            f"got '{profile.identity_status}' — profile cannot claim verified identity"
        )

    if profile.user_id and len(profile.user_id) < 4:
        reasons.append("user_id must be at least 4 characters")

    if profile.language_preferences:
        primary = profile.language_preferences.get("primary", "en")
        if not isinstance(primary, str) or len(primary) != 2:
            reasons.append("language_preferences.primary must be a 2-letter code")

    return (len(reasons) == 0, reasons)


# ── Summary for meaning state ─────────────────────────────────────────────

def summarize_user_profile(profile: UserProfile) -> str:
    """
    Produce a bounded summary of the profile for WESLR state.
    Does NOT imply the current session is verified as this user.
    """
    parts = []
    if profile.preferred_name:
        parts.append(f"profile name: {profile.preferred_name}")
    elif profile.display_name:
        parts.append(f"profile name: {profile.display_name}")
    if profile.role:
        parts.append(f"role: {profile.role}")
    if profile.relationship_to_weslr:
        parts.append(f"relationship: {profile.relationship_to_weslr}")
    if profile.primary_projects:
        parts.append(f"projects: {', '.join(profile.primary_projects[:3])}")

    if not parts:
        return "no profile configured"

    return "; ".join(parts)


# ── Membership helpers ──────────────────────────────────────────────────────

def add_membership(
    profile: UserProfile,
    entity_type: str,
    entity_id: str,
    role: str,
    relationship_type: str,
    display_name: Optional[str] = None,
    verified: bool = False,
    confidence: float = 0.4,
    source: str = "explicit_profile",
) -> UserProfile:
    """
    Add a membership claim to the profile.
    Membership claims are NOT verified unless channel/role evidence exists.
    Does not duplicate identical (entity_type, entity_id) claims.
    """
    claim = MembershipClaim(
        entity_type=entity_type,
        entity_id=entity_id,
        display_name=display_name or entity_id,
        role=role,
        relationship_type=relationship_type,
        verified=verified,
        confidence=confidence,
        source=source,
        evidence=[],
        limitations=[
            "Membership claim is not verified unless channel/role evidence exists",
            "Does not imply access to group memory without verified role",
        ],
    )
    existing = [m for m in profile.memberships
                if m.entity_type == entity_type and m.entity_id == entity_id]
    if not existing:
        profile.memberships.append(claim)
    return profile


def list_memberships(profile: UserProfile) -> list[dict]:
    """List all membership claims from profile."""
    return [
        {
            "entity_type": m.entity_type,
            "entity_id": m.entity_id,
            "display_name": m.display_name,
            "role": m.role,
            "relationship_type": m.relationship_type,
            "verified": m.verified,
            "confidence": m.confidence,
        }
        for m in profile.memberships
    ]


def summarize_memberships(profile: UserProfile) -> str:
    """Summarize profile memberships for display."""
    if not profile.memberships:
        return "no memberships configured"
    parts = []
    for m in profile.memberships:
        parts.append(
            f"{m.entity_type}/{m.display_name} ({m.role}, conf={m.confidence:.2f})"
        )
    return "; ".join(parts)


def get_verified_memberships(profile: UserProfile) -> list[MembershipClaim]:
    """Return only memberships with verified=True."""
    return [m for m in profile.memberships if m.verified]


# ── Backup ─────────────────────────────────────────────────────────────────

def backup_profile(path: Optional[str] = None) -> Optional[str]:
    """Create timestamped backup of existing profile. Returns backup path or None."""
    full = _profile_path(path)
    if not os.path.isfile(full):
        return None
    import datetime
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
    backup_path = full + f".backup-{ts}"
    try:
        with open(full) as src:
            with open(backup_path, "w") as dst:
                dst.write(src.read())
        return backup_path
    except Exception:
        return None
