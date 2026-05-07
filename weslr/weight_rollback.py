"""
weslr/weight_rollback.py

Snapshot-based rollback for weight changes.
Stored at ~/.weslr/weight_rollbacks.jsonl (project-local: .weslr_state/)

Each rollback snapshot:
- rollback_id
- timestamp
- proposal_id
- weight_key
- old_value
- new_value
- delta
- zone
- mode
- full_weight_snapshot_before
- reason
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, Literal
import json
import os
import uuid

DEFAULT_STORE_DIR = os.path.expanduser("~/.weslr")
PROJECT_STORE_DIR = ".weslr_state"

Mode = Literal["manual", "auto"]


@dataclass
class RollbackSnapshot:
    rollback_id: str
    timestamp: str
    proposal_id: Optional[str]
    weight_key: str
    old_value: float
    new_value: float
    delta: float
    zone: str
    mode: Mode
    weight_snapshot_before: dict  # full CognitiveWeight as dict
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json_line(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "RollbackSnapshot":
        return cls(**d)

    @classmethod
    def from_json_line(cls, line: str) -> "RollbackSnapshot":
        return cls.from_dict(json.loads(line))


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _store_path(explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit
    if os.path.exists(PROJECT_STORE_DIR):
        return os.path.join(PROJECT_STORE_DIR, "weight_rollbacks.jsonl")
    return os.path.join(DEFAULT_STORE_DIR, "weight_rollbacks.jsonl")


class RollbackStore:
    def __init__(self, path: Optional[str] = None):
        self._path = _store_path(path)

    @property
    def path(self) -> str:
        return self._path

    def append(self, snap: RollbackSnapshot) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(snap.to_json_line() + "\n")

    def create_snapshot(
        self,
        registry,
        proposal,
        mode: Mode,
        reason: str = "",
    ) -> RollbackSnapshot:
        """Create and persist a rollback snapshot before applying a change."""
        w = registry.get_weight(proposal.weight_key)
        snap = RollbackSnapshot(
            rollback_id=str(uuid.uuid4())[:8],
            timestamp=_now_iso(),
            proposal_id=getattr(proposal, "proposal_id", None),
            weight_key=proposal.weight_key,
            old_value=proposal.old_value,
            new_value=proposal.proposed_value,
            delta=proposal.delta,
            zone=w.zone if w else "unknown",
            mode=mode,
            weight_snapshot_before=w.dict() if w else {},
            reason=reason,
        )
        self.append(snap)
        return snap

    def list_rollbacks(self, weight_key: Optional[str] = None, limit: int = 50) -> list[RollbackSnapshot]:
        snaps = []
        if not os.path.exists(self._path):
            return snaps
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    s = RollbackSnapshot.from_json_line(line)
                except Exception:
                    continue
                if weight_key and s.weight_key != weight_key:
                    continue
                snaps.append(s)
                if len(snaps) >= limit:
                    break
        return list(reversed(snaps))  # newest first

    def get(self, rollback_id: str) -> Optional[RollbackSnapshot]:
        if not os.path.exists(self._path):
            return None
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    s = RollbackSnapshot.from_json_line(line)
                    if s.rollback_id == rollback_id:
                        return s
                except Exception:
                    continue
        return None

    def restore_snapshot(self, rollback_id: str, registry) -> tuple[bool, str]:
        """Restore a specific rollback snapshot. Returns (success, message)."""
        snap = self.get(rollback_id)
        if not snap:
            return False, f"Rollback {rollback_id} not found"
        w = registry.get_weight(snap.weight_key)
        if not w:
            return False, f"Weight {snap.weight_key} not found in registry"
        # Apply the old value
        registry.set_pending(snap.weight_key, snap.old_value,
                             reason=f"rollback {rollback_id}: {snap.reason}")
        registry.save_to_file()
        return True, f"Restored {snap.weight_key} to {snap.old_value}"


def load_rollback_store(path: Optional[str] = None) -> RollbackStore:
    return RollbackStore(path)