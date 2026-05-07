"""
weslr/weight_cooldown.py

Persistent per-weight cooldown tracking.
Stored at ~/.weslr/weight_cooldowns.json (project-local: .weslr_state/)

Tracks:
- last_proposed_at
- last_auto_applied_at
- proposal_count_24h
- auto_apply_count_24h
"""

from dataclasses import dataclass, asdict
from typing import Optional
import json
import os

DEFAULT_STORE_DIR = os.path.expanduser("~/.weslr")
PROJECT_STORE_DIR = ".weslr_state"


def _store_path(explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit
    if os.path.exists(PROJECT_STORE_DIR):
        return os.path.join(PROJECT_STORE_DIR, "weight_cooldowns.json")
    return os.path.join(DEFAULT_STORE_DIR, "weight_cooldowns.json")


def _now_ts() -> float:
    import time
    return time.time()


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_HOUR = 3600.0
_DAY = 86400.0


@dataclass
class WeightCooldownEntry:
    weight_key: str
    last_proposed_at: Optional[float] = None  # Unix timestamp
    last_auto_applied_at: Optional[float] = None  # Unix timestamp
    proposal_count_24h: int = 0
    auto_apply_count_24h: int = 0
    last_24h_reset: Optional[float] = None  # Unix timestamp of last daily reset

    def cooldown_elapsed(self, hours: int) -> bool:
        if self.last_proposed_at is None:
            return True
        return (_now_ts() - self.last_proposed_at) >= (hours * _HOUR)

    def auto_apply_cooldown_elapsed(self, hours: int) -> bool:
        if self.last_auto_applied_at is None:
            return True
        return (_now_ts() - self.last_auto_applied_at) >= (hours * _HOUR)

    def dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "WeightCooldownEntry":
        return cls(**d)


class WeightCooldownTracker:
    def __init__(self, entries: Optional[dict[str, WeightCooldownEntry]] = None):
        self.entries: dict[str, WeightCooldownEntry] = entries or {}

    def get(self, weight_key: str) -> WeightCooldownEntry:
        if weight_key not in self.entries:
            self.entries[weight_key] = WeightCooldownEntry(weight_key=weight_key)
        return self.entries[weight_key]

    def record_proposal(self, weight_key: str) -> None:
        entry = self.get(weight_key)
        now = _now_ts()
        self._reset_24h_if_needed(entry, now)
        entry.last_proposed_at = now
        entry.proposal_count_24h += 1

    def record_auto_apply(self, weight_key: str) -> None:
        entry = self.get(weight_key)
        now = _now_ts()
        self._reset_24h_if_needed(entry, now)
        entry.last_auto_applied_at = now
        entry.auto_apply_count_24h += 1

    def _reset_24h_if_needed(self, entry: WeightCooldownEntry, now: float) -> None:
        if entry.last_24h_reset is None:
            entry.last_24h_reset = now
            return
        if (now - entry.last_24h_reset) >= _DAY:
            entry.proposal_count_24h = 0
            entry.auto_apply_count_24h = 0
            entry.last_24h_reset = now

    def daily_auto_count(self, weight_key: str) -> int:
        return self.get(weight_key).auto_apply_count_24h

    def to_dict(self) -> dict:
        return {k: v.dict() for k, v in self.entries.items()}

    @classmethod
    def from_dict(cls, d: dict) -> "WeightCooldownTracker":
        entries = {k: WeightCooldownEntry.from_dict(v) for k, v in d.items()}
        return cls(entries)

    def save(self, path: Optional[str] = None) -> None:
        p = _store_path(path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "WeightCooldownTracker":
        p = _store_path(path)
        if not os.path.exists(p):
            return cls()
        with open(p) as f:
            return cls.from_dict(json.load(f))


def load_cooldowns(path: Optional[str] = None) -> WeightCooldownTracker:
    return WeightCooldownTracker.load(path)


def save_cooldowns(tracker: WeightCooldownTracker, path: Optional[str] = None) -> None:
    tracker.save(path)