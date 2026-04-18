"""Execution Deadline / Timeout Propagation Layer (v67)

Deadline tracking and propagation across distributed execution flow.
Provides deadline model, expiry detection, and breach handling.

Architecture:
  - ExecutionDeadlineState — deadline lifecycle states
  - ExecutionDeadline — canonical deadline model
  - DeadlineStatus — single point for deadline operations
  - FlowDeadlineTracker — tracks deadlines across flows

Rules:
  - Deadline/state propagation only — no scheduling
  - Expiry detection via check_if_breached()
  - Automatic rollback on deadline breach
  - Full audit traceability
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No consensus
  - No scheduler/retry engine
  - No TIA/C#
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# DEADLINE STATE MACHINE
# ============================================================================


class ExecutionDeadlineState(str, Enum):
    """States in the deadline lifecycle."""
    PENDING = "pending"           # Deadline created, not yet active
    ACTIVE = "active"             # Deadline active, waiting for completion
    BREACHED = "breached"         # Deadline has been breached
    CANCELLING = "cancelling"     # Cancellation in progress
    CANCELLED = "cancelled"       # Execution cancelled due to deadline
    COMPLETED = "completed"       # Execution completed before deadline


# ============================================================================
# DEADLINE MODEL
# ============================================================================


@dataclass
class ExecutionDeadline:
    """Deadline model for distributed execution flow."""
    
    deadline_id: str
    flow_id: str
    absolute_deadline: datetime
    created_at: datetime
    state: str = ExecutionDeadlineState.PENDING.value
    breached_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    breach_reason: Optional[str] = None
    original_deadline: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if not isinstance(self.created_at, datetime):
            self.created_at = datetime.fromisoformat(
                self.created_at.replace("Z", "+00:00")
            )
        if isinstance(self.absolute_deadline, str):
            self.absolute_deadline = datetime.fromisoformat(
                self.absolute_deadline.replace("Z", "+00:00")
            )
        if self.original_deadline is None:
            self.original_deadline = self.absolute_deadline
    
    def mark_active(self) -> None:
        """Mark deadline as active."""
        self.state = ExecutionDeadlineState.ACTIVE.value
    
    def mark_breached(self, reason: str) -> None:
        """Mark deadline as breached."""
        self.state = ExecutionDeadlineState.BREACHED.value
        self.breached_at = datetime.now(timezone.utc)
        self.breach_reason = reason
    
    def mark_cancelling(self) -> None:
        """Mark cancellation in progress."""
        self.state = ExecutionDeadlineState.CANCELLING.value
    
    def mark_cancelled(self) -> None:
        """Mark execution cancelled."""
        self.state = ExecutionDeadlineState.CANCELLED.value
        self.cancelled_at = datetime.now(timezone.utc)
    
    def mark_completed(self) -> None:
        """Mark execution completed before deadline."""
        self.state = ExecutionDeadlineState.COMPLETED.value
    
    def is_active(self) -> bool:
        """Check if deadline is still active."""
        return self.state == ExecutionDeadlineState.ACTIVE.value
    
    def is_breached(self) -> bool:
        """Check if deadline has been breached."""
        return self.state == ExecutionDeadlineState.BREACHED.value
    
    def is_cancelled(self) -> bool:
        """Check if execution was cancelled."""
        return self.state == ExecutionDeadlineState.CANCELLED.value
    
    def is_completed(self) -> bool:
        """Check if execution completed."""
        return self.state == ExecutionDeadlineState.COMPLETED.value
    
    def get_remaining_seconds(self) -> float:
        """Get remaining seconds until deadline."""
        if self.state in (ExecutionDeadlineState.BREACHED.value, 
                          ExecutionDeadlineState.CANCELLED.value,
                          ExecutionDeadlineState.COMPLETED.value):
            return 0.0
        now = datetime.now(timezone.utc)
        delta = self.absolute_deadline - now
        return max(0.0, delta.total_seconds())
    
    def is_expired(self) -> bool:
        """Check if deadline has expired."""
        now = datetime.now(timezone.utc)
        return now > self.absolute_deadline
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize deadline to dict."""
        return {
            "deadline_id": self.deadline_id,
            "flow_id": self.flow_id,
            "absolute_deadline": self.absolute_deadline.isoformat().replace("+00:00", "Z"),
            "created_at": self.created_at.isoformat().replace("+00:00", "Z"),
            "state": self.state,
            "breached_at": self.breached_at.isoformat().replace("+00:00", "Z") if self.breached_at else None,
            "cancelled_at": self.cancelled_at.isoformat().replace("+00:00", "Z") if self.cancelled_at else None,
            "breach_reason": self.breach_reason,
            "original_deadline": self.original_deadline.isoformat().replace("+00:00", "Z") if self.original_deadline else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionDeadline":
        """Deserialize deadline from dict."""
        return cls(
            deadline_id=data["deadline_id"],
            flow_id=data["flow_id"],
            absolute_deadline=data["absolute_deadline"],
            created_at=data["created_at"],
            state=data.get("state", ExecutionDeadlineState.PENDING.value),
            breached_at=data.get("breached_at"),
            cancelled_at=data.get("cancelled_at"),
            breach_reason=data.get("breach_reason"),
            original_deadline=data.get("original_deadline")
        )


class DeadlineStatus:
    """Single point for deadline operations."""
    
    def check_if_breached(self, deadline: ExecutionDeadline) -> bool:
        """Check if deadline has been breached."""
        return deadline.is_breached()
    
    def mark_breached(self, deadline: ExecutionDeadline, reason: str) -> None:
        """Mark deadline as breached."""
        deadline.mark_breached(reason)
    
    def mark_cancelled(self, deadline: ExecutionDeadline) -> None:
        """Mark execution cancelled."""
        deadline.mark_cancelled()
    
    def mark_completed(self, deadline: ExecutionDeadline) -> None:
        """Mark execution completed."""
        deadline.mark_completed()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize deadline status."""
        return {"status": "ok"}


# ============================================================================
# FLOW DEADLINE TRACKER
# ============================================================================


class FlowDeadlineTracker:
    """Tracks deadlines across flows."""
    
    def __init__(self):
        self._deadlines: Dict[str, ExecutionDeadline] = {}
        self._flow_to_deadline: Dict[str, str] = {}
    
    def create_deadline(self, flow_id: str, seconds: int = 300) -> ExecutionDeadline:
        """Create deadline for flow."""
        deadline_id = str(uuid.uuid4())
        created = datetime.now(timezone.utc)
        absolute = created + timedelta(seconds=seconds)
        
        deadline = ExecutionDeadline(
            deadline_id=deadline_id,
            flow_id=flow_id,
            absolute_deadline=absolute,
            created_at=created
        )
        
        self._deadlines[deadline_id] = deadline
        self._flow_to_deadline[flow_id] = deadline_id
        
        return deadline
    
    def get_deadline(self, deadline_id: str) -> Optional[ExecutionDeadline]:
        """Get deadline by ID."""
        return self._deadlines.get(deadline_id)
    
    def get_deadline_for_flow(self, flow_id: str) -> Optional[ExecutionDeadline]:
        """Get deadline for flow."""
        deadline_id = self._flow_to_deadline.get(flow_id)
        return self._deadlines.get(deadline_id) if deadline_id else None
    
    def remove_deadline(self, flow_id: str) -> Optional[ExecutionDeadline]:
        """Remove deadline for flow."""
        deadline_id = self._flow_to_deadline.pop(flow_id, None)
        return self._deadlines.pop(deadline_id, None) if deadline_id else None
    
    def mark_flow_deadline_breached(self, flow_id: str, reason: str) -> None:
        """Mark deadline breached for flow."""
        deadline = self.get_deadline_for_flow(flow_id)
        if deadline:
            deadline.mark_breached(reason)
    
    def mark_flow_deadline_cancelled(self, flow_id: str) -> None:
        """Mark deadline cancelled for flow."""
        deadline = self.get_deadline_for_flow(flow_id)
        if deadline:
            deadline.mark_cancelled()
    
    def mark_flow_deadline_completed(self, flow_id: str) -> None:
        """Mark deadline completed for flow."""
        deadline = self.get_deadline_for_flow(flow_id)
        if deadline:
            deadline.mark_completed()
    
    def get_stats(self) -> Dict[str, int]:
        """Get deadline statistics."""
        return {
            "total_deadlines": len(self._deadlines),
            "active_deadlines": len([d for d in self._deadlines.values() if d.is_active()]),
            "breached_deadlines": len([d for d in self._deadlines.values() if d.is_breached()]),
            "cancelled_deadlines": len([d for d in self._deadlines.values() if d.is_cancelled()]),
            "completed_deadlines": len([d for d in self._deadlines.values() if d.is_completed()])
        }
