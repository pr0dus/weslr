from __future__ import annotations
from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SelfChangeState:
    change_id: str
    description: str
    approval_ref: str
    checkpoint_ref: str
    rollback_ref: str
    validation_plan: str
    state: str = "pending"
    applied_at: str | None = None
    validation_outcome: str | None = None
    committed_at: str | None = None
    rolled_back_at: str | None = None
    lineage_ref: str | None = None

    def apply(self):
        self.applied_at = _now()
        self.state = "applied"

    def record_validation(self, outcome: str):
        self.validation_outcome = outcome
        if outcome == "pass":
            self.state = "validated"
        else:
            self.state = "failed"

    def commit(self, lineage_ref: str | None = None):
        self.committed_at = _now()
        self.state = "committed"
        self.lineage_ref = lineage_ref

    def rollback(self):
        self.rolled_back_at = _now()
        self.state = "rolled_back"


def orchestrate_self_change(change: SelfChangeState, *, apply_change, run_validation, record_lineage) -> SelfChangeState:
    """Execute the guarded self-change flow.

    - apply_change: callable, performs the change (toggle/enable); should be reversible.
    - run_validation: callable, returns "pass" or "fail" (or a richer string) based on tests/observability.
    - record_lineage: callable, returns lineage_ref string for audit.
    """
    change.apply()
    apply_change()
    outcome = run_validation()
    change.record_validation(outcome)
    if outcome == "pass":
        lineage_ref = record_lineage()
        change.commit(lineage_ref)
    else:
        change.rollback()
    return change


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"
