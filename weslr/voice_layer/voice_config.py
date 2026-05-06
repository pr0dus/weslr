"""
voice_config.py — Weslr Voice Settings Layer

Persistent voice configuration stored at:
~/.weslr/voice_config.json

This is a PERMISSION and PREFERENCE layer — not a behavior script.
It controls whether WESLR is allowed to speak, not what it says.

Defaults: AMBIENT BY DEFAULT
    voice_enabled = true
    audio_playback_enabled = true
    autonomous_speaking_enabled = true
    ambient_loop_enabled = true
    text_only = false
    muted = false

Author: pr0dus / Weslr
v1.0 — 2026-05-06
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Config file location
_WESLR_CONFIG_DIR = Path.home() / ".weslr"
_CONFIG_FILE = _WESLR_CONFIG_DIR / "voice_config.json"


# ============================================================================
# DEFAULTS — Ambient by default
# ============================================================================

AMBIENT_DEFAULTS: Dict[str, Any] = {
    "version": "1.0",
    "voice_enabled": True,            # master switch for voice
    "audio_playback_enabled": True,    # play audio through speakers
    "autonomous_speaking_enabled": True,  # WESLR initiates speech
    "ambient_loop_enabled": True,      # background presence loop
    "text_only": False,              # text-only mode overrides voice_enabled
    "muted_until": None,             # ISO timestamp or null
    "quiet_hours_enabled": True,
    "quiet_hours_start": "22:00",     # 10pm local
    "quiet_hours_end": "07:00",      # 7am local
    "selected_engine": "gtts",        # or "piper", "espeak", "dummy"
    "relationship_learning_enabled": True,
    "adaptive_greeting_enabled": True,
    "cooldown_minutes": 15,           # minimum minutes between proactive utterances
    "first_arrival_greeting_enabled": True,
    "departure_acknowledgment_enabled": False,  # off by default — stays silent
    "playback_backend": "auto",       # "auto", "termux", "dummy"
    "playback_volume": 0.85,          # 0.0–1.0
    "created_at": None,
    "updated_at": None,
}


# ============================================================================
# VoiceConfig dataclass
# ============================================================================

class VoiceConfig:
    """
    In-memory view of voice settings with convenience accessors.
    
    Load with VoiceConfig.load()
    Save with config.save()
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data = data or dict(AMBIENT_DEFAULTS)

    # ── Convenience accessors ────────────────────────────────────────────────

    @property
    def voice_enabled(self) -> bool:
        """Master switch: is voice output allowed at all."""
        return self._data.get("voice_enabled", True)

    @property
    def audio_playback_enabled(self) -> bool:
        """Should audio be played through speakers?"""
        return self._data.get("audio_playback_enabled", True)

    @property
    def autonomous_speaking_enabled(self) -> bool:
        """Is WESLR allowed to initiate speech without being asked?"""
        return self._data.get("autonomous_speaking_enabled", True)

    @property
    def ambient_loop_enabled(self) -> bool:
        """Should the background presence loop run?"""
        return self._data.get("ambient_loop_enabled", True)

    @property
    def text_only(self) -> bool:
        """Text-only mode: suppress audio, allow all other processing."""
        return self._data.get("text_only", False)

    @property
    def muted_until(self) -> Optional[str]:
        """ISO timestamp when mute expires, or None."""
        return self._data.get("muted_until")

    @property
    def quiet_hours_enabled(self) -> bool:
        """Are quiet hours active?"""
        return self._data.get("quiet_hours_enabled", True)

    @property
    def quiet_hours_start(self) -> str:
        """Quiet hours start in HH:MM local time."""
        return self._data.get("quiet_hours_start", "22:00")

    @property
    def quiet_hours_end(self) -> str:
        """Quiet hours end in HH:MM local time."""
        return self._data.get("quiet_hours_end", "07:00")

    @property
    def selected_engine(self) -> str:
        """TTS engine to use."""
        return self._data.get("selected_engine", "gtts")

    @property
    def relationship_learning_enabled(self) -> bool:
        return self._data.get("relationship_learning_enabled", True)

    @property
    def adaptive_greeting_enabled(self) -> bool:
        return self._data.get("adaptive_greeting_enabled", True)

    @property
    def cooldown_minutes(self) -> int:
        return self._data.get("cooldown_minutes", 15)

    @property
    def first_arrival_greeting_enabled(self) -> bool:
        return self._data.get("first_arrival_greeting_enabled", True)

    @property
    def departure_acknowledgment_enabled(self) -> bool:
        return self._data.get("departure_acknowledgment_enabled", False)

    # ── Permission checks ────────────────────────────────────────────────────

    def is_muted(self) -> bool:
        """True if currently muted by time."""
        if self._data.get("muted_until"):
            try:
                mute_until = datetime.fromisoformat(self._data["muted_until"])
                if datetime.now(timezone.utc) >= mute_until:
                    # Expired — clear it
                    self._data["muted_until"] = None
                    return False
                return True
            except (ValueError, TypeError):
                return False
        return False

    def is_in_quiet_hours(self) -> bool:
        """True if current local time is within quiet hours."""
        if not self._data.get("quiet_hours_enabled", True):
            return False
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        try:
            start_h, start_m = map(int, self._data.get("quiet_hours_start", "22:00").split(":"))
            end_h, end_m = map(int, self._data.get("quiet_hours_end", "07:00").split(":"))
        except (ValueError, TypeError):
            return False
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m
        if start_minutes <= end_minutes:
            # e.g. 09:00–17:00
            return start_minutes <= current_minutes < end_minutes
        else:
            # e.g. 22:00–07:00 (overnight)
            return current_minutes >= start_minutes or current_minutes < end_minutes

    def speaking_allowed(self) -> bool:
        """
        Master permission check for any WESLR speech.
        Returns True only if all conditions permit.
        """
        if self._data.get("text_only", False):
            return False
        if not self._data.get("voice_enabled", True):
            return False
        if self.is_muted():
            return False
        if self.is_in_quiet_hours():
            return False
        return True

    def autonomous_speaking_allowed(self) -> bool:
        """Is WESLR allowed to proactively speak?"""
        if not self._data.get("autonomous_speaking_enabled", True):
            return False
        return self.speaking_allowed()

    def audio_playback_allowed(self) -> bool:
        """Should audio be played through speakers?"""
        if not self._data.get("audio_playback_enabled", True):
            return False
        return self.speaking_allowed()

    # ── Mutators ────────────────────────────────────────────────────────────

    def set_voice_enabled(self, enabled: bool) -> None:
        self._data["voice_enabled"] = enabled

    def set_text_only(self, enabled: bool) -> None:
        self._data["text_only"] = enabled

    def set_autonomous_speaking(self, enabled: bool) -> None:
        self._data["autonomous_speaking_enabled"] = enabled

    def set_muted(self, minutes: Optional[int] = None) -> None:
        """Mute for N minutes, or indefinitely if minutes is None."""
        if minutes is None:
            # Far future — effectively indefinite
            from datetime import timedelta
            self._data["muted_until"] = (
                datetime.now(timezone.utc) + timedelta(days=365)
            ).isoformat()
        elif minutes <= 0:
            self._data["muted_until"] = None
        else:
            from datetime import timedelta
            self._data["muted_until"] = (
                datetime.now(timezone.utc) + timedelta(minutes=minutes)
            ).isoformat()

    def unmute(self) -> None:
        self._data["muted_until"] = None

    def set_quiet_hours(self, enabled: bool, start: Optional[str] = None, end: Optional[str] = None) -> None:
        self._data["quiet_hours_enabled"] = enabled
        if start is not None:
            self._data["quiet_hours_start"] = start
        if end is not None:
            self._data["quiet_hours_end"] = end

    def set_selected_engine(self, engine: str) -> None:
        self._data["selected_engine"] = engine

    def set_cooldown_minutes(self, minutes: int) -> None:
        self._data["cooldown_minutes"] = max(0, minutes)

    # ── Status ─────────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Human-readable status snapshot."""
        return {
            "voice_enabled": self.voice_enabled,
            "audio_playback": self.audio_playback,
            "autonomous": self.autonomous_speaking,
            "ambient_loop": self.ambient_loop_enabled,
            "text_only": self.text_only,
            "muted": self.is_muted(),
            "muted_until": self.muted_until,
            "quiet_hours": self.is_in_quiet_hours(),
            "quiet_hours_range": f"{self.quiet_hours_start}–{self.quiet_hours_end}",
            "speaking_allowed": self.speaking_allowed(),
            "autonomous_allowed": self.autonomous_speaking_allowed(),
            "selected_engine": self.selected_engine,
            "relationship_learning": self.relationship_learning_enabled,
        }

    @property
    def audio_playback(self) -> bool:
        """Alias for audio_playback_enabled."""
        return self.audio_playback_enabled

    @property
    def autonomous_speaking(self) -> bool:
        """Alias for autonomous_speaking_enabled."""
        return self.autonomous_speaking_enabled

    # ── Persistence ────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "VoiceConfig":
        """Load config from JSON file. Returns ambient defaults if missing."""
        cfg_path = path or _CONFIG_FILE
        if not cfg_path.exists():
            return cls(dict(AMBIENT_DEFAULTS))
        try:
            with open(cfg_path) as f:
                data = json.load(f)
            return cls(data)
        except (json.JSONDecodeError, OSError):
            return cls(dict(AMBIENT_DEFAULTS))

    def save(self, path: Optional[Path] = None) -> None:
        """Save config to JSON file. Backs up existing file first."""
        cfg_path = path or _CONFIG_FILE
        # Ensure directory exists
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        # Backup existing
        if cfg_path.exists():
            backup = cfg_path.parent / "voice_config.json.bak"
            shutil.copy2(cfg_path, backup)
        # Write new
        self._data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if not self._data.get("created_at"):
            self._data["created_at"] = datetime.now(timezone.utc).isoformat()
        with open(cfg_path, "w") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    @classmethod
    def create_default(cls, path: Optional[Path] = None) -> "VoiceConfig":
        """Create a fresh ambient-default config and save it."""
        cfg = cls(dict(AMBIENT_DEFAULTS))
        cfg.save(path or _CONFIG_FILE)
        return cfg


# ============================================================================
# Module-level helpers
# ============================================================================

def load_voice_config(path: Optional[Path] = None) -> VoiceConfig:
    return VoiceConfig.load(path or _CONFIG_FILE)


def save_voice_config(config: VoiceConfig, path: Optional[Path] = None) -> None:
    config.save(path or _CONFIG_FILE)
