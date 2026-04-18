"""Weslr Proactive Proposal State Management.

State storage for proactive proposal surfacing (Phase 1H).
Tracks which patterns have been surfaced and which are in cooldown.
"""

from __future__ import annotations

import json
import time
from pathlib import Path


SURFACED_STATE_FILE = "self_improvement_proactive_state.json"
COOLDOWN_FILE = "self_improvement_proactive_cooldowns.json"
BASE_DIR = Path(__file__).resolve().parent


def get_surfaced_state_path() -> Path:
    """Get path to surfaced state file."""
    return BASE_DIR / SURFACED_STATE_FILE


def get_cooldown_path() -> Path:
    """Get path to cooldown file."""
    return BASE_DIR / COOLDOWN_FILE


def load_proactive_state() -> dict:
    """Load proactive state (surfaced patterns)."""
    path = get_surfaced_state_path()
    if not path.exists():
        return {"last_surfaced_patterns": {}, "denied_patterns": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_surfaced_patterns": {}, "denied_patterns": {}}


def save_proactive_state(state: dict) -> None:
    """Save proactive state."""
    path = get_surfaced_state_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def load_cooldowns() -> dict:
    """Load denied patterns cooldown timestamps."""
    path = get_cooldown_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cooldowns(cooldowns: dict) -> None:
    """Save cooldown timestamps."""
    path = get_cooldown_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cooldowns, f, indent=2)


def get_pattern_key(pattern: str, source_layer: str) -> str:
    """Generate pattern key for storage."""
    return f"{pattern}|{source_layer}"


def set_surfaced_pattern(pattern: str, source_layer: str) -> None:
    """Mark pattern as recently surfaced."""
    state = load_proactive_state()
    key = get_pattern_key(pattern, source_layer)
    state["last_surfaced_patterns"][key] = int(time.time())
    save_proactive_state(state)


def is_surfaced(pattern: str, source_layer: str) -> bool:
    """Check if pattern was recently surfaced (within cooldown window)."""
    state = load_proactive_state()
    key = get_pattern_key(pattern, source_layer)
    if key not in state.get("last_surfaced_patterns", {}):
        return False
    last_time = state["last_surfaced_patterns"][key]
    return (int(time.time()) - last_time) < 86400  # 24 hours


def set_denied_pattern(pattern: str, source_layer: str) -> None:
    """Record denial (24h cooldown)."""
    cooldowns = load_cooldowns()
    key = get_pattern_key(pattern, source_layer)
    cooldowns[key] = int(time.time())
    save_cooldowns(cooldowns)


def is_in_cooldown(pattern: str, source_layer: str) -> bool:
    """Check if pattern is in 24h cooldown."""
    cooldowns = load_cooldowns()
    key = get_pattern_key(pattern, source_layer)
    if key not in cooldowns:
        return False
    return (int(time.time()) - cooldowns[key]) < 86400  # 24 hours


def get_surfaced_patterns() -> list[str]:
    """Get list of recently surfaced pattern keys."""
    state = load_proactive_state()
    return list(state.get("last_surfaced_patterns", {}).keys())


def get_denied_patterns() -> dict:
    """Get dict of denied patterns with timestamps."""
    return load_cooldowns()
