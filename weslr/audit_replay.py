# audit_replay.py - WESLR v43: Audit Replay / Decision Forensics Surface
# Creates a governed replay/forensics layer so operators can inspect the full
# decision path behind a proposal, escalation, proof-gate outcome, or other major governance event.
# Additive only, transparent, reversible, role-aware, non-manipulative.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from . import operator_lifecycle


# ============================================================================
# ENUMS
# ============================================================================


class ReplayStatus(str, Enum):
    """Status of a replay/forensics trace."""
    ACTIVE = "active"  # Currently being built
    COMPLETE = "complete"  # Finalized trace
    PARTIAL = "partial"  # Some events missing
    DEGRADED = "degraded"  # Degraded mode trace


class ForensicCategory(str, Enum):
    """Categories for forensic analysis."""
    DECISION_RECONSTRUCTION = "decision_reconstruction"  # Reconstruct decision path
    EVIDENCE_CHAIN = "evidence_chain"  # Track evidence chain
    APPROVAL_HISTORY = "approval_history"  # Track approvals/denials
    STATE_TRANSITION = "state_transition"  # Track state changes
    ESCALATION_PATH = "escalation_path"  # Track escalation path
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"  # Identify root causes


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ReplayEvent:
    """A single event in a replay trace."""
    
    event_id: str
    event_type: str  # LedgerEventType.value
    timestamp: str
    source: str  # AuditSource.value
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None
    
    # Affected object
    affected_object_id: Optional[str] = None
    affected_object_type: Optional[str] = None
    
    # Context
    context_id: Optional[str] = None
    deployment_role: Optional[str] = None
    
    # Approval outcome
    approval_status: Optional[str] = None  # approved/denied/escalated
    approval_notes: Optional[str] = None
    
    # State
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    
    # Evidence
    evidence_references: List[str] = field(default_factory=list)
    
    # Metadata
    level: str = "info"  # AuditLevel.value
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "source": self.source,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "affected_object_id": self.affected_object_id,
            "affected_object_type": self.affected_object_type,
            "context_id": self.context_id,
            "deployment_role": self.deployment_role,
            "approval_status": self.approval_status,
            "approval_notes": self.approval_notes,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "evidence_references": self.evidence_references,
            "level": self.level,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReplayEvent:
        data["evidence_references"] = data.get("evidence_references", [])
        data.setdefault("source", "system")
        data.setdefault("level", "info")
        return cls(**data)


@dataclass
class ReplayTrace:
    """Complete replay trace for an object."""
    
    trace_id: str
    affected_object_id: str
    affected_object_type: str
    
    # Events in chronological order
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Forensic analysis
    category: str = ForensicCategory.DECISION_RECONSTRUCTION.value
    forensic_summary: Optional[str] = None
    
    # Status
    status: str = ReplayStatus.ACTIVE.value
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def add_event(self, event: Dict[str, Any]) -> None:
        """Add an event to the trace."""
        self.events.append(event)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def get_events_by_actor(self, actor_id: str) -> List[Dict[str, Any]]:
        """Get events by actor ID."""
        return [e for e in self.events if e.get("actor_id") == actor_id]
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get events by type."""
        return [e for e in self.events if e.get("event_type") == event_type]
    
    def get_approval_events(self) -> List[Dict[str, Any]]:
        """Get all approval-related events."""
        approval_types = [
            "proposal_approved",
            "proposal_denied",
            "escalation_approved",
            "escalation_denied",
            "escalation_escalated",
        ]
        return [e for e in self.events if e.get("event_type") in approval_types]
    
    def generate_forensic_summary(self) -> str:
        """Generate a concise forensic summary."""
        if not self.events:
            return "No events in trace"
        
        summary_parts = []
        
        # Count event types
        event_types = {}
        for event in self.events:
            event_type = event.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Build summary
        event_list = sorted(event_types.items(), key=lambda x: x[1], reverse=True)
        event_str = ", ".join(f"{t}({c})" for t, c in event_list[:5])
        summary_parts.append(f"Events: {event_str}")
        
        # Approval summary
        approval_events = self.get_approval_events()
        if approval_events:
            approvals = sum(1 for e in approval_events if e.get("approval_status") == "approved")
            denials = sum(1 for e in approval_events if e.get("approval_status") == "denied")
            summary_parts.append(f"Approvals: {approvals}, Denials: {denials}")
        
        # Actor summary
        actors = set(e.get("actor_id") for e in self.events if e.get("actor_id"))
        if actors:
            summary_parts.append(f"Actors: {', '.join(sorted(actors))}")
        
        self.forensic_summary = "; ".join(summary_parts)
        return self.forensic_summary
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "affected_object_id": self.affected_object_id,
            "affected_object_type": self.affected_object_type,
            "event_count": len(self.events),
            "events": self.events,
            "category": self.category,
            "forensic_summary": self.forensic_summary,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReplayTrace:
        # Filter out computed fields
        data = {k: v for k, v in data.items() if k in ["trace_id", "affected_object_id", "affected_object_type", "events", "category", "forensic_summary", "status", "created_at", "updated_at", "author"]}
        data["events"] = data.get("events", [])
        data.setdefault("category", "decision_reconstruction")
        return cls(**data)


@dataclass
class ForensicReport:
    """Complete forensic report for governance review."""
    
    report_id: str
    affected_object_id: str
    affected_object_type: str
    
    # Traces
    traces: List[Dict[str, Any]] = field(default_factory=list)
    
    # Analysis
    analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Status
    status: str = "draft"  # draft, reviewed, published
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "affected_object_id": self.affected_object_id,
            "affected_object_type": self.affected_object_type,
            "trace_count": len(self.traces),
            "traces": self.traces,
            "analysis": self.analysis,
            "recommendations": self.recommendations,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ForensicReport:
        # Filter out computed fields
        data = {k: v for k, v in data.items() if k in ["report_id", "affected_object_id", "affected_object_type", "traces", "analysis", "recommendations", "status", "created_at", "updated_at", "author"]}
        data["traces"] = data.get("traces", [])
        data["recommendations"] = data.get("recommendations", [])
        data.setdefault("status", "draft")
        return cls(**data)


# ============================================================================
# FORENSICS ENGINE
# ============================================================================


class AuditReplayEngine:
    """Engine for managing audit replay and decision forensics.
    
    Provides transparent, reversible replay capabilities.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize audit replay engine."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/audit_replay/"
        self.traces: Dict[str, ReplayTrace] = {}
        self.reports: Dict[str, ForensicReport] = {}
        self._ensure_storage_exists()
        self._load_traces()
        self._load_reports()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_traces(self) -> None:
        """Load traces from storage."""
        import os
        import glob
        
        if not os.path.exists(self.storage_path):
            return
        
        for filepath in glob.glob(os.path.join(self.storage_path, "*_trace.json")):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    trace = ReplayTrace.from_dict(data)
                    self.traces[trace.trace_id] = trace
            except Exception:
                continue
    
    def _load_reports(self) -> None:
        """Load reports from storage."""
        import os
        import glob
        
        if not os.path.exists(self.storage_path):
            return
        
        for filepath in glob.glob(os.path.join(self.storage_path, "*_report.json")):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    report = ForensicReport.from_dict(data)
                    self.reports[report.report_id] = report
            except Exception:
                continue
    
    def create_trace(
        self,
        trace_id: str,
        affected_object_id: str,
        affected_object_type: str,
        category: str = ForensicCategory.DECISION_RECONSTRUCTION.value,
        author: Optional[str] = None,
    ) -> ReplayTrace:
        """Create a new replay trace."""
        trace = ReplayTrace(
            trace_id=trace_id,
            affected_object_id=affected_object_id,
            affected_object_type=affected_object_type,
            category=category,
            author=author,
        )
        self.traces[trace_id] = trace
        self._save_trace(trace)
        return trace
    
    def get_trace(self, trace_id: str) -> Optional[ReplayTrace]:
        """Get a trace by ID."""
        return self.traces.get(trace_id)
    
    def create_trace_from_events(
        self,
        trace_id: str,
        affected_object_id: str,
        affected_object_type: str,
        events: List[Dict[str, Any]],
        category: str = ForensicCategory.DECISION_RECONSTRUCTION.value,
        author: Optional[str] = None,
    ) -> ReplayTrace:
        """Create a trace from existing events."""
        trace = ReplayTrace(
            trace_id=trace_id,
            affected_object_id=affected_object_id,
            affected_object_type=affected_object_type,
            category=category,
            events=events,
            author=author,
        )
        self.traces[trace_id] = trace
        self._save_trace(trace)
        return trace
    
    def _save_trace(self, trace: ReplayTrace) -> None:
        """Save a trace to storage."""
        import os
        
        filepath = os.path.join(self.storage_path, f"{trace.trace_id}_trace.json")
        with open(filepath, "w") as f:
            json.dump(trace.to_dict(), f, indent=2)
    
    def create_report(
        self,
        report_id: str,
        affected_object_id: str,
        affected_object_type: str,
        traces: List[str],
        author: Optional[str] = None,
    ) -> ForensicReport:
        """Create a forensic report from traces."""
        report = ForensicReport(
            report_id=report_id,
            affected_object_id=affected_object_id,
            affected_object_type=affected_object_type,
            author=author,
        )
        
        # Load traces
        for trace_id in traces:
            trace = self.get_trace(trace_id)
            if trace:
                report.traces.append(trace.to_dict())
        
        self.reports[report_id] = report
        self._save_report(report)
        return report
    
    def get_report(self, report_id: str) -> Optional[ForensicReport]:
        """Get a report by ID."""
        return self.reports.get(report_id)
    
    def _save_report(self, report: ForensicReport) -> None:
        """Save a report to storage."""
        import os
        
        filepath = os.path.join(self.storage_path, f"{report.report_id}_report.json")
        with open(filepath, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
    
    def get_trace_summary(self, object_id: str) -> Dict[str, Any]:
        """Get trace summary for an object."""
        trace_id = f"trace_{object_id}"
        trace = self.get_trace(trace_id)
        
        if not trace:
            # Try to find any trace for this object
            for t in self.traces.values():
                if t.affected_object_id == object_id:
                    trace = t
                    break
        
        if not trace:
            return {
                "object_id": object_id,
                "trace_exists": False,
                "event_count": 0,
                "status": "not_found",
            }
        
        trace.generate_forensic_summary()
        
        return {
            "object_id": object_id,
            "trace_id": trace.trace_id,
            "trace_exists": True,
            "event_count": len(trace.events),
            "category": trace.category,
            "forensic_summary": trace.forensic_summary,
            "status": trace.status,
            "traces": [trace.to_dict()],
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "trace_count": len(self.traces),
            "report_count": len(self.reports),
            "traces": {k: v.to_dict() for k, v in self.traces.items()},
            "reports": {k: v.to_dict() for k, v in self.reports.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_audit_ledger(
    audit_dict: Dict[str, Any],
    replay_engine: AuditReplayEngine = None,
    object_id: str = None,
) -> Dict[str, Any]:
    """Add replay context to audit ledger.
    
    This is purely additive — no migration required.
    
    v43: Replay engine provides forensics traces for audit events.
    """
    if "audit_replay_context" not in audit_dict:
        audit_dict["audit_replay_context"] = None
    
    if replay_engine and object_id:
        try:
            summary = replay_engine.get_trace_summary(object_id)
            audit_dict["audit_replay_context"] = {
                "trace_summary": summary,
                "trace_exists": summary.get("trace_exists", False),
                "event_count": summary.get("event_count", 0),
            }
        except Exception:
            pass  # Silent fallback to default
    
    return audit_dict


def integrate_with_governance_surface(
    governance_dict: Dict[str, Any],
    replay_engine: AuditReplayEngine = None,
    context_id: str = None,
) -> Dict[str, Any]:
    """Add replay context to governance surface.
    
    This is purely additive — no migration required.
    
    v43: Replay surfaces decision traces clearly to operators.
    """
    if "audit_replay_context" not in governance_dict:
        governance_dict["audit_replay_context"] = None
    
    if replay_engine and context_id:
        try:
            # Find all traces related to this context
            traces = []
            for trace in replay_engine.traces.values():
                for event in trace.events:
                    if event.get("context_id") == context_id:
                        traces.append(trace.to_dict())
                        break
            
            governance_dict["audit_replay_context"] = {
                "trace_count": len(traces),
                "traces": traces[:3],  # First 3 traces for review
                "has_trace": len(traces) > 0,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return governance_dict


def integrate_with_operator_views(
    operator_dict: Dict[str, Any],
    replay_engine: AuditReplayEngine = None,
    object_id: str = None,
) -> Dict[str, Any]:
    """Add replay context to operator-facing views.
    
    This is purely additive — no migration required.
    
    v43: Replay provides concise forensic summaries for operators.
    """
    if "audit_replay_context" not in operator_dict:
        operator_dict["audit_replay_context"] = None
    
    if replay_engine and object_id:
        try:
            summary = replay_engine.get_trace_summary(object_id)
            
            if summary.get("trace_exists"):
                operator_dict["audit_replay_context"] = {
                    "trace_summary": summary.get("forensic_summary", "No summary"),
                    "event_count": summary.get("event_count", 0),
                    "has_approval": summary.get("event_count", 0) > 0,
                }
        except Exception:
            pass  # Silent fallback to default
    
    return operator_dict
