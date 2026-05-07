"""
weslr/weight_audit.py

Append-only audit log for weight refinement events.
Stored at ~/.weslr/weight_audit.jsonl (project-local: .weslr_state/)

Event types:
- proposal_created
- simulation_run
- proposal_approved
- proposal_rejected
- manual_apply
- auto_apply_blocked
- auto_apply_applied
- rollback_created
- rollback_restored

Each event:
- timestamp, event_type, proposal_id, weight_key,
  old_value, new_value, delta, zone, mode,
  guardrail_result, actor, reason, rollback_id
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, Literal
import json
import os

DEFAULT_STORE_DIR = os.path.expanduser("~/.weslr")
PROJECT_STORE_DIR = ".weslr_state"

EventType = Literal[
    "proposal_created", "simulation_run", "proposal_approved",
    "proposal_rejected", "manual_apply", "auto_apply_blocked",
    "auto_apply_applied", "rollback_created", "rollback_restored",
]
Actor = Literal["operator", "weslr_auto", "test", "system"]


@dataclass
class WeightAuditEvent:
    timestamp: str
    event_type: EventType
    proposal_id: Optional[str]
    weight_key: str
    old_value: Optional[float]
    new_value: Optional[float]
    delta: Optional[float]
    zone: str
    mode: str
    guardrail_result: str  # "passed" | "blocked"
    blocked_reasons: list[str] = field(default_factory=list)
    actor: str = "operator"
    reason: str = ""
    rollback_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json_line(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "WeightAuditEvent":
        return cls(**d)

    @classmethod
    def from_json_line(cls, line: str) -> "WeightAuditEvent":
        return cls.from_dict(json.loads(line))


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _store_path(explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit
    if os.path.exists(PROJECT_STORE_DIR):
        return os.path.join(PROJECT_STORE_DIR, "weight_audit.jsonl")
    return os.path.join(DEFAULT_STORE_DIR, "weight_audit.jsonl")


class WeightAuditLog:
    def __init__(self, path: Optional[str] = None):
        self._path = _store_path(path)

    @property
    def path(self) -> str:
        return self._path

    def append(self, event: WeightAuditEvent) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(event.to_json_line() + "\n")

    def write_event(
        self,
        event_type: EventType,
        weight_key: str,
        proposal_id: Optional[str] = None,
        old_value: Optional[float] = None,
        new_value: Optional[float] = None,
        delta: Optional[float] = None,
        zone: str = "unknown",
        mode: str = "unknown",
        guardrail_result: str = "passed",
        blocked_reasons: Optional[list[str]] = None,
        actor: str = "operator",
        reason: str = "",
        rollback_id: Optional[str] = None,
    ) -> None:
        event = WeightAuditEvent(
            timestamp=_now_iso(),
            event_type=event_type,
            proposal_id=proposal_id,
            weight_key=weight_key,
            old_value=old_value,
            new_value=new_value,
            delta=delta,
            zone=zone,
            mode=mode,
            guardrail_result=guardrail_result,
            blocked_reasons=blocked_reasons or [],
            actor=actor,
            reason=reason,
            rollback_id=rollback_id,
        )
        self.append(event)

    def query(
        self,
        event_type: Optional[EventType] = None,
        weight_key: Optional[str] = None,
        limit: int = 100,
    ) -> list[WeightAuditEvent]:
        events = []
        if not os.path.exists(self._path):
            return events
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = WeightAuditEvent.from_json_line(line)
                except Exception:
                    continue
                if event_type and e.event_type != event_type:
                    continue
                if weight_key and e.weight_key != weight_key:
                    continue
                events.append(e)
                if len(events) >= limit:
                    break
        return events

    def last_auto_apply_count(self) -> int:
        events = self.query(event_type="auto_apply_applied", limit=100)
        today = _now_iso()[:10]  # "YYYY-MM-DD"
        return sum(1 for e in events if e.timestamp.startswith(today))

    def events_for_proposal(self, proposal_id: str) -> list[WeightAuditEvent]:
        events = []
        if not os.path.exists(self._path):
            return events
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = WeightAuditEvent.from_json_line(line)
                except Exception:
                    continue
                if e.proposal_id == proposal_id:
                    events.append(e)
        return events


def load_audit(path: Optional[str] = None) -> WeightAuditLog:
    return WeightAuditLog(path)