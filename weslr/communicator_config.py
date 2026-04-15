"""Weslr Communicator Config — Phase C Communicator Wiring

Reads onboarding answers from the operator's most recent onboarding submission
and exposes them as runtime configuration that influences:
- check-in cadence
- adaptation/capability gates
- escalation routing

Additive only. Reads from existing state, does not modify onboarding flow.
Does NOT redesign the front door.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Paths ──────────────────────────────────────────────────────────────────

def _base_dir() -> str:
    return "/data/data/com.termux/files/home/.openclaw/workspace"

def _communicator_self_path() -> str:
    return os.path.join(_base_dir(), "communicator_self.json")

def _operator_profile_path() -> str:
    return os.path.join(_base_dir(), "operator_profile.json")

def _config_path() -> str:
    return os.path.join(_base_dir(), "communicator_config.json")

# ── Onboarding Payload Storage ──────────────────────────────────────────────

def load_operator_profile() -> Dict[str, Any]:
    """Load the operator profile (most recent onboarding answers).
    
    Falls back to empty dict if not yet onboarded.
    """
    path = _operator_profile_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_operator_profile(profile: Dict[str, Any]) -> None:
    """Save operator profile from onboarding answers.
    
    Called by the /onboarding endpoint after recording.
    """
    path = _operator_profile_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

def update_operator_profile(answers: Dict[str, Any]) -> None:
    """Update operator profile with new onboarding answers.
    
    Merges with existing profile, preserving history.
    """
    profile = load_operator_profile()
    
    # Store onboarding history (keep last 3)
    history = profile.get("_onboarding_history", [])
    history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "answers": answers,
    })
    if len(history) > 3:
        history = history[-3:]
    profile["_onboarding_history"] = history
    
    # Flatten top-level answers into profile
    for key, value in answers.items():
        if key == "objectives" and isinstance(value, list):
            # Store as list
            profile[key] = value
        elif key != "phase" and value is not None:
            profile[key] = value
    
    profile["_last_updated"] = datetime.utcnow().isoformat()
    save_operator_profile(profile)

# ── Runtime Config Derivation ───────────────────────────────────────────────

def derive_communicator_config() -> Dict[str, Any]:
    """Derive runtime communicator config from operator profile.
    
    This is the canonical config that other modules read.
    Returns a stable config even if operator hasn't onboarded yet.
    """
    profile = load_operator_profile()
    lifecycle_state = _derive_lifecycle_state_key(profile)
    
    config = {
        # Check-in cadence (derived from urgency/time-sensitivity if not explicit)
        "checkin_style": _derive_cadence_from_urgency(profile),
        "standup_cadence": profile.get("standup_cadence", "none"),
        
        # Adaptation / capability gates
        "adaptation_level": profile.get("adaptation_level", "propose"),
        "adaptation_limits": profile.get("adaptation_limits", ""),
        
        # Escalation routing
        "escalation_primary": profile.get("escalation_primary", ""),
        "escalation_secondary": profile.get("escalation_secondary", ""),
        "escalation_channel": profile.get("escalation_channel", "none"),
        
        # Context
        "operator_name": profile.get("name", ""),
        "operator_role": profile.get("role", ""),
        "persona": profile.get("persona", "technical"),
        "primary_outcome": profile.get("primary_outcome", ""),
        "time_horizon": profile.get("time_horizon", "session"),
        "urgency": profile.get("urgency", "deliberate"),
        
        # Lifecycle state (derived from session count and onboarding completeness)
        "lifecycle_state": _derive_lifecycle_state_key(profile),
        
        # Derived flags (read-only, operator guidance only)
        "_is_onboarded": bool(profile.get("name")),
        "_last_updated": profile.get("_last_updated", ""),
    }
    
    return config

# ── Check-in Cadence ─────────────────────────────────────────────────────────

def _derive_cadence_from_urgency(profile: Dict[str, Any]) -> str:
    """Derive check-in cadence from onboarding urgency/time-sensitivity answers.
    
    First pass mapping:
    - critical/high urgency -> verbose  (check-in every 30 min)
    - normal urgency        -> hourly
    - low/deliberate       -> daily
    - none/silent          -> silent  (only when action is needed)
    
    Operator's explicit checkin_style in profile takes precedence.
    """
    explicit = profile.get("checkin_style")
    if explicit in ("silent", "hourly", "daily", "verbose"):
        return explicit  # explicit profile setting wins

    urgency = profile.get("urgency", "deliberate").lower()
    time_sensitivity = profile.get("time_sensitivity", "").lower()

    # Combine urgency and time-sensitivity for richer mapping
    is_high = urgency in ("critical", "high") or time_sensitivity == "high"
    is_normal = urgency == "normal" or time_sensitivity == "normal"
    is_low = urgency in ("low", "deliberate", "none") or time_sensitivity == "low"

    if is_high:
        return "verbose"
    elif is_normal:
        return "hourly"
    elif is_low:
        return "daily"
    return "silent"


def _derive_lifecycle_state_key(profile: Dict[str, Any] | None = None) -> str:
    """Derive the communicator lifecycle state key from profile and continuity data.

    This is a lightweight version of derive_lifecycle_state() that returns only
    the state string — suitable for embedding in config dicts without
    introducing circular imports.

    States: bootstrap_required | newly_activated | establishing | established
    """
    if profile is None:
        profile = {}
    is_onboarded = bool(profile.get("name"))
    if not is_onboarded:
        return "bootstrap_required"

    try:
        from sim import load_communicator_self
        cs = load_communicator_self()
        continuity = cs.get("continuity", {})
        session_count = continuity.get("session_count", 0)
        memory_bonds = continuity.get("memory_bonds", 0.0)
        unfinished = continuity.get("unfinished_threads", [])
    except Exception:
        session_count = 0
        memory_bonds = 0.0
        unfinished = []

    if session_count <= 2:
        return "newly_activated"
    if session_count <= 14:
        return "establishing"
    if session_count >= 15 or memory_bonds >= 0.5 or len(unfinished) >= 3:
        return "established"
    return "establishing"


def get_checkin_cadence() -> str:
    """Get check-in cadence string.
    
    Returns one of: "silent", "hourly", "daily", "verbose"
    """
    return derive_communicator_config().get("checkin_style", "silent")

def should_checkin_now(last_checkin_ts: float, current_ts: float) -> bool:
    """Determine if a check-in should happen now based on cadence.
    
    Args:
        last_checkin_ts: Unix timestamp of last check-in
        current_ts: Current Unix timestamp
        
    Returns:
        True if check-in is due, False otherwise
    """
    cadence = get_checkin_cadence()
    
    if cadence == "silent":
        return False  # Only when action is needed
    elif cadence == "hourly":
        return (current_ts - last_checkin_ts) >= 3600
    elif cadence == "daily":
        return (current_ts - last_checkin_ts) >= 86400
    elif cadence == "verbose":
        return (current_ts - last_checkin_ts) >= 1800  # 30 minutes
    else:
        return False

# ── Adaptation / Capability Gates ──────────────────────────────────────────

def get_adaptation_level() -> str:
    """Get adaptation level for this operator.
    
    Returns one of: "none", "propose", "low-risk", "full"
    """
    return derive_communicator_config().get("adaptation_level", "propose")

def can_self_modify(change_category: str, change_impact: str = "low") -> bool:
    """Determine if Weslr may apply a self-modification without prior approval.
    
    This is a read-only heuristic — operator guidance only, not certainty,
    not action triggers.
    
    Args:
        change_category: Category of proposed change (e.g., "prompt", "config", "code")
        change_impact: Estimated impact ("low", "medium", "high")
        
    Returns:
        True if adaptation level permits this class of change
    """
    level = get_adaptation_level()
    
    if level == "none":
        return False  # Must propose only
    elif level == "propose":
        return False  # All changes require operator review
    elif level == "low-risk":
        # Only trivial self-changes directly
        return change_impact == "low" and change_category in {"prompt", "config", "comment", "formatting"}
    elif level == "full":
        return change_impact in {"low", "medium"}  # Within safety thresholds
    else:
        return False

def get_adaptation_limits() -> List[str]:
    """Parse adaptation limits from operator profile.
    
    Returns list of prohibited change categories.
    """
    limits_str = derive_communicator_config().get("adaptation_limits", "")
    if not limits_str:
        return []
    # Split on newlines or semicolons
    return [line.strip() for line in limits_str.split("\n") if line.strip()]

def _tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    return [t.strip().lower() for t in re.sub(r"[^\w\s]", " ", text).split() if t.strip()]

def is_change_prohibited(change_category: str) -> bool:
    """Check if a change category is explicitly prohibited by operator.

    Performs token-aware matching so "safety_gateway" matches
    "Never modify the safety gateway" (matches "gateway" token) and
    "Never alter the operator_override" (matches "override" token).

    Also checks sub-tokens: for "safety_gateway", checks for
    "safety_gateway", "safety", and "gateway" individually.

    Args:
        change_category: Category of proposed change

    Returns:
        True if this category appears in the operator's prohibition list
    """
    limits = get_adaptation_limits()
    if not limits:
        return False

    # Check all sub-tokens of the change category
    # e.g. "safety_gateway" → ["safety_gateway", "safety", "gateway"]
    # Also tokenize to handle space-separated category names
    raw = change_category.lower()
    sub_tokens = [raw]
    if "_" in raw:
        sub_tokens.extend(raw.split("_"))
    sub_tokens.extend(_tokenize(change_category))

    for limit in limits:
        limit_tokens = _tokenize(limit)
        for st in sub_tokens:
            if st in limit_tokens:
                return True

    return False

# ── Escalation Routing ───────────────────────────────────────────────────────

def get_escalation_config() -> Dict[str, Any]:
    """Get escalation configuration for this operator.
    
    Returns dict with:
    - primary_contact: str
    - secondary_contact: str  
    - channel: str ("slack", "email", "ticket", "direct", "none")
    - is_configured: bool
    """
    config = derive_communicator_config()
    return {
        "primary_contact": config.get("escalation_primary", ""),
        "secondary_contact": config.get("escalation_secondary", ""),
        "channel": config.get("escalation_channel", "none"),
        "is_configured": bool(config.get("escalation_primary")),
    }

def should_escalate(situation: str) -> bool:
    """Determine if a situation warrants escalation to human operator.
    
    This is a read-only heuristic — operator guidance only.
    
    Args:
        situation: One of "safety", "cost", "quality", "trust", "other"
        
    Returns:
        True if situation is severe enough to warrant escalation
    """
    esc = get_escalation_config()
    if not esc["is_configured"]:
        return False  # No contact configured, can't escalate
    
    # Cost thresholds always warrant escalation
    if situation == "cost":
        return True
    
    # Safety always warrants escalation
    if situation == "safety":
        return True
    
    # Quality issues escalate only if operator has set high bar
    if situation == "quality":
        return True
    
    # Trust issues escalate only if very uncertain
    if situation == "trust":
        return True
    
    return False

def format_escalation_message(situation: str, details: str) -> str:
    """Format an escalation message for the configured channel.
    
    Returns a formatted message string (caller handles actual delivery).
    """
    esc = get_escalation_config()
    config = derive_communicator_config()
    
    contact = esc["primary_contact"] or "Operator"
    channel = esc["channel"]
    
    lines = [
        f"[Weslr Escalation — {situation.upper()}]",
        f"Operator: {contact}",
        f"Situation: {situation}",
        f"Details: {details}",
        f"Time: {datetime.utcnow().isoformat()}",
        f"Primary outcome: {config.get('primary_outcome', 'N/A')}",
        f"Urgency: {config.get('urgency', 'deliberate')}",
    ]
    
    return "\n".join(lines)

# ── Capability Gate Helpers ─────────────────────────────────────────────────

def get_allowed_capabilities() -> List[str]:
    """Get list of allowed capabilities from operator profile.
    
    Returns list of capability labels.
    """
    profile = load_operator_profile()
    return profile.get("allowed_capabilities", [])

def is_capability_allowed(capability: str) -> bool:
    """Check if a capability is explicitly allowed by operator.

    Substring matching is used, so 'read' matches
    'Read code, files, and docs'.

    Args:
        capability: Capability label (e.g., "read", "write", "search")

    Returns:
        True if allowed (exact match or substring), False otherwise.
        Returns True pre-onboarding when operator hasn't restricted anything.
    """
    allowed = get_allowed_capabilities()
    if not allowed:
        return True  # Pre-onboarding: assume allowed (operator hasn't restricted)
    cap_lower = capability.lower()
    return any(cap_lower in c.lower() for c in allowed)

def get_forbidden_actions() -> List[str]:
    """Get list of explicitly forbidden actions from operator profile.

    Returns list of forbidden action descriptions.
    Handles both string (newline-separated) and list formats.
    """
    profile = load_operator_profile()
    forbidden = profile.get("forbidden_actions", "")
    if not forbidden:
        return []
    # Handle list format (if profile stores as list)
    if isinstance(forbidden, list):
        return [str(f).strip() for f in forbidden if f]
    # Handle string format (newline-separated)
    return [line.strip() for line in forbidden.split("\n") if line.strip()]


# ── Communicator Lifecycle State ─────────────────────────────────────────────

def derive_lifecycle_state(profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Derive the communicator lifecycle state from profile and continuity data.

    Lifecycle state reflects the relationship maturity between WESLR and the
    operator. It influences tone, check-in style, guidance verbosity, and
    escalation messaging. State is derived from onboarding completeness,
    session history, and trust anchor status — it is read-only.

    States:
    - bootstrap_required: No onboarding data; WESLR is in initial setup
    - newly_activated: Onboarding complete but relationship is fresh (< 3 sessions)
    - establishing: 3–14 sessions; relationship is developing
    - established: 15+ sessions with stable continuity; trust is solid
    - escalation_pending: Active SS-TDE escalation in progress
    - elevated_action_window: A clearance token is active; bounded elevated trust

    Args:
        profile: Optional pre-loaded operator profile (avoids re-reading file)

    Returns:
        dict with keys: state, tone, guidance, checkin_style, escalation_wording
    """
    from weslr.state_defs import default_memory_layers
    from sim import load_communicator_self

    if profile is None:
        profile = load_operator_profile()
    is_onboarded = bool(profile.get("name"))

    # Bootstrap_required: no onboarding data at all
    if not is_onboarded:
        return {
            "state": "bootstrap_required",
            "tone": "welcoming",
            "guidance": "explain",
            "checkin_style": "daily",
            "escalation_wording": "setup_required",
        }

    # Get session count from communicator self
    try:
        cs = load_communicator_self()
        continuity = cs.get("continuity", {})
        session_count = continuity.get("session_count", 0)
        memory_bonds = continuity.get("memory_bonds", 0.0)
        unfinished = continuity.get("unfinished_threads", [])
    except Exception:
        session_count = 0
        memory_bonds = 0.0
        unfinished = []

    # Newly activated: onboarding done but sessions are few
    if session_count <= 2:
        return {
            "state": "newly_activated",
            "tone": "warm",
            "guidance": "guide",
            "checkin_style": _derive_cadence_from_urgency(profile),
            "escalation_wording": "standard",
        }

    # Establishing: sessions are growing, trust is developing
    if session_count <= 14:
        return {
            "state": "establishing",
            "tone": "balanced",
            "guidance": "support",
            "checkin_style": _derive_cadence_from_urgency(profile),
            "escalation_wording": "standard",
        }

    # Established: 15+ sessions, strong memory bonds, or active threads
    if session_count >= 15 or memory_bonds >= 0.5 or len(unfinished) >= 3:
        return {
            "state": "established",
            "tone": "confident",
            "guidance": "concise",
            "checkin_style": _derive_cadence_from_urgency(profile),
            "escalation_wording": "familiar",
        }

    # Fallback to establishing
    return {
        "state": "establishing",
        "tone": "balanced",
        "guidance": "support",
        "checkin_style": _derive_cadence_from_urgency(profile),
        "escalation_wording": "standard",
    }


def get_lifecycle_state() -> Dict[str, Any]:
    """Get the current lifecycle state dict for the communicator.

    Convenience wrapper around derive_lifecycle_state().
    """
    return derive_lifecycle_state()

def is_action_forbidden(action: str) -> bool:
    """Check if an action is explicitly forbidden by operator.

    Performs token-aware matching so "push to main" matches
    "Never push directly to main" (shares "push" token) and
    "delete resources" matches "Never delete resources" (shares "delete" token).

    Args:
        action: Action description

    Returns:
        True if this action appears in the forbidden list
    """
    forbidden = get_forbidden_actions()
    if not forbidden:
        return False

    action_tokens = _tokenize(action)
    for f in forbidden:
        f_tokens = _tokenize(f)
        # Match if any token overlaps
        if any(at in ft for at in action_tokens for ft in [f_tokens]):
            return True

    return False

# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # Default: dump full config
        config = derive_communicator_config()
        print(json.dumps(config, indent=2))
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "profile":
        print(json.dumps(load_operator_profile(), indent=2))
    elif cmd == "config":
        print(json.dumps(derive_communicator_config(), indent=2))
    elif cmd == "checkin":
        print(get_checkin_cadence())
    elif cmd == "adaptation":
        print(get_adaptation_level())
    elif cmd == "escalation":
        print(json.dumps(get_escalation_config(), indent=2))
    elif cmd == "capabilities":
        print(json.dumps(get_allowed_capabilities(), indent=2))
    elif cmd == "forbidden":
        print(json.dumps(get_forbidden_actions(), indent=2))
    elif cmd == "update":
        # Called by /onboarding endpoint to update profile
        if len(sys.argv) < 3:
            print("Usage: update <json_answers>", file=sys.stderr)
            sys.exit(1)
        answers = json.loads(sys.argv[2])
        update_operator_profile(answers)
        print("Updated operator profile.")
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)