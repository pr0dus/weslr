"""Cross-Node Diagnostic Reasoning Hooks (v70)

Read-only diagnostic reasoning layer for distributed execution failures.
Analyzes failures across proposal, handshake, execution envelope, receipt,
and deadline stages without orchestration or aggregation.

Architecture:
  - FailureClassifier — classifies failures by type/stage
  - StageDiagnosis — localized diagnosis with root cause hypothesis
  - CrossStageCorrelator — correlates failures across stages
  - DiagnosticSummary — aggregates diagnosis into summary
  - DiagnosticHooks — read-only API surface for operators

Rules:
  - Read-only diagnostics only
  - Separate observed facts from inferred likely cause
  - Recovery hints are suggestions, not certainty
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No orchestration, sharding, aggregation
  - No consensus, scheduler/task engine
  - No TIA/C#
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .execution_telemetry import (
    TelemetryEventEmitter,
    TelemetryEvent,
    TelemetryEventType,
)
from .execution_deadline import DeadlineStatus
from .node_identity import NodeTrustStatus, NodeHealthStatus
from .remote_action_proposal import (
    RemoteActionProposal,
    ProposalStatus,
    RejectionReason,
)


# ============================================================================
# FAILURE CLASSIFICATION
# ============================================================================


class FailureType(str, Enum):
    """Categories of distributed execution failure."""
    # Proposal stage
    PROPOSAL_REJECTED = "proposal_rejected"
    PROPOSAL_EXPIRED = "proposal_expired"
    PROPOSAL_VALIDATION_FAILED = "proposal_validation_failed"
    
    # Handshake stage
    HANDSHAKE_FAILED = "handshake_failed"
    HANDSHAKE_TIMEOUT = "handshake_timeout"
    HANDSHAKE_IDENTITY_MISMATCH = "handshake_identity_mismatch"
    HANDSHAKE_TRUST_REJECTED = "handshake_trust_rejected"
    HANDSHAKE_HEALTH_REJECTED = "handshake_health_rejected"
    
    # Envelope stage
    ENVELOPE_GATE_FAILED = "envelope_gate_failed"
    ENVELOPE_AUTHORIZATION_FAILED = "envelope_authorization_failed"
    ENVELOPE_DISPATCH_FAILED = "envelope_dispatch_failed"
    
    # Receipt stage
    RECEIPT_FAILED = "receipt_failed"
    RECEIPT_TIMEOUT = "receipt_timeout"
    
    # Deadline stage
    DEADLINE_BREACHED = "deadline_breached"
    
    # Unknown/other
    UNKNOWN = "unknown"


class FailureStage(str, Enum):
    """Stages in the distributed execution lifecycle."""
    PROPOSAL = "proposal"
    HANDSHAKE = "handshake"
    ENVELOPE = "envelope"
    RECEIPT = "receipt"
    DEADLINE = "deadline"
    COMPLETED = "completed"
    UNKNOWN = "unknown"


@dataclass
class FailureClassification:
    """Classification of a failure with observed facts."""
    
    failure_type: str
    stage: str
    node_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    # Observed facts (not inferences)
    observed_error: Optional[str] = None
    observed_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    correlation_ids: Dict[str, str] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_type": self.failure_type,
            "stage": self.stage,
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "observed_error": self.observed_error,
            "observed_events": self.observed_events,
            "correlation_ids": self.correlation_ids,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailureClassification":
        return cls(
            failure_type=data["failure_type"],
            stage=data["stage"],
            node_id=data.get("node_id"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            observed_error=data.get("observed_error"),
            observed_events=data.get("observed_events", []),
            correlation_ids=data.get("correlation_ids", {}),
            context=data.get("context", {})
        )


class FailureClassifier:
    """Classifies failures by type and stage from telemetry and proposal data.
    
    Observes actual events and classifies failures based on evidence.
    Does NOT make orchestration decisions.
    """
    
    def __init__(self, emitter: TelemetryEventEmitter):
        """Initialize classifier with telemetry emitter reference."""
        self._emitter = emitter
    
    def classify_flow_failure(self, flow_id: str) -> Optional[FailureClassification]:
        """Classify failure for a specific flow.
        
        Args:
            flow_id: The flow ID to analyze
            
        Returns:
            FailureClassification if failure detected, None if flow completed
        """
        events = self._emitter.get_events_by_flow(flow_id)
        if not events:
            return None
        
        # Check for failure events
        failure_types = [
            TelemetryEventType.FLOW_FAILED.value,
            TelemetryEventType.FLOW_REJECTED.value,
            TelemetryEventType.HANDSHAKE_FAILURE.value,
            TelemetryEventType.DEADLINE_BREACH.value,
        ]
        
        for event in events:
            if event.event_type in failure_types:
                return self._build_classification(flow_id, events, event)
        
        # Check if flow never completed
        has_completion = any(
            e.event_type == TelemetryEventType.FLOW_COMPLETED.value
            for e in events
        )
        if not has_completion:
            # Check for proposal rejection
            proposal_rejections = [
                e for e in events
                if "rejection" in e.properties.get("status", "").lower()
            ]
            if proposal_rejections:
                return FailureClassification(
                    failure_type=FailureType.PROPOSAL_REJECTED.value,
                    stage=FailureStage.PROPOSAL.value,
                    correlation_ids={"flow_id": flow_id},
                    observed_error="Proposal was rejected",
                    observed_events=[e.to_dict() for e in proposal_rejections]
                )
        
        return None
    
    def _build_classification(
        self,
        flow_id: str,
        all_events: List[TelemetryEvent],
        failure_event: TelemetryEvent
    ) -> FailureClassification:
        """Build classification from failure event and context."""
        correlation_ids = {
            k: v for k, v in failure_event.correlation_ids.items()
            if v
        }
        correlation_ids["flow_id"] = flow_id
        
        # Determine stage from event type
        stage_map = {
            TelemetryEventType.FLOW_FAILED.value: FailureStage.ENVELOPE.value,
            TelemetryEventType.FLOW_REJECTED.value: FailureStage.PROPOSAL.value,
            TelemetryEventType.HANDSHAKE_FAILURE.value: FailureStage.HANDSHAKE.value,
            TelemetryEventType.DEADLINE_BREACH.value: FailureStage.DEADLINE.value,
        }
        stage = stage_map.get(failure_event.event_type, FailureStage.UNKNOWN.value)
        
        # Extract observed error from properties
        observed_error = None
        if failure_event.properties:
            observed_error = (
                failure_event.properties.get("error")
                or failure_event.properties.get("reason")
                or failure_event.properties.get("description")
            )
        
        # Get all events for context
        observed_events = [e.to_dict() for e in all_events]
        
        return FailureClassification(
            failure_type=self._map_to_failure_type(failure_event.event_type, stage),
            stage=stage,
            correlation_ids=correlation_ids,
            observed_error=observed_error,
            observed_events=observed_events,
            context={"flow_id": flow_id}
        )
    
    def _map_to_failure_type(self, event_type: str, stage: str) -> str:
        """Map telemetry event to failure type."""
        type_map = {
            TelemetryEventType.FLOW_FAILED.value: FailureType.UNKNOWN.value,
            TelemetryEventType.FLOW_REJECTED.value: FailureType.PROPOSAL_REJECTED.value,
            TelemetryEventType.HANDSHAKE_FAILURE.value: FailureType.HANDSHAKE_FAILED.value,
            TelemetryEventType.DEADLINE_BREACH.value: FailureType.DEADLINE_BREACHED.value,
        }
        return type_map.get(event_type, FailureType.UNKNOWN.value)
    
    def classify_all_failures(self) -> List[FailureClassification]:
        """Classify all failures across all flows.
        
        Returns:
            List of failure classifications
        """
        failures = []
        flows = self._emitter.get_all_flows()
        
        for flow_id in flows:
            classification = self.classify_flow_failure(flow_id)
            if classification:
                failures.append(classification)
        
        return failures
    
    def classify_by_node(self, node_id: str) -> List[FailureClassification]:
        """Classify failures associated with a specific node.
        
        Args:
            node_id: Node ID to filter by
            
        Returns:
            List of failure classifications for this node
        """
        all_failures = self.classify_all_failures()
        return [
            f for f in all_failures
            if f.node_id == node_id
            or node_id in f.correlation_ids.values()
        ]


# ============================================================================
# STAGE DIAGNOSIS
# ============================================================================


@dataclass
class StageDiagnosis:
    """Diagnosis for a single stage with root cause hypothesis.
    
    Separates observed facts from inferred likely cause.
    """
    
    stage: str
    failure_type: str
    
    # Observed facts
    observed_errors: List[str] = field(default_factory=list)
    observed_events: List[Dict[str, Any]] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)
    
    # Root cause hypothesis (inference, not certainty)
    likely_cause: Optional[str] = None
    contributing_factors: List[str] = field(default_factory=list)
    
    # Recovery hint (suggestion, not certainty)
    recovery_hint: Optional[str] = None
    
    # Metadata
    correlation_ids: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "failure_type": self.failure_type,
            "observed_errors": self.observed_errors,
            "observed_events": self.observed_events,
            "timestamps": self.timestamps,
            "likely_cause": self.likely_cause,
            "contributing_factors": self.contributing_factors,
            "recovery_hint": self.recovery_hint,
            "correlation_ids": self.correlation_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StageDiagnosis":
        return cls(
            stage=data["stage"],
            failure_type=data["failure_type"],
            observed_errors=data.get("observed_errors", []),
            observed_events=data.get("observed_events", []),
            timestamps=data.get("timestamps", []),
            likely_cause=data.get("likely_cause"),
            contributing_factors=data.get("contributing_factors", []),
            recovery_hint=data.get("recovery_hint"),
            correlation_ids=data.get("correlation_ids", {})
        )


class StageDiagnosisBuilder:
    """Builds detailed diagnosis for a single failure stage.
    
    Analyzes failure classification and builds stage-local diagnosis.
    """
    
    def build_diagnosis(self, classification: FailureClassification) -> StageDiagnosis:
        """Build diagnosis from failure classification.
        
        Args:
            classification: Failure classification from classifier
            
        Returns:
            StageDiagnosis with root cause hypothesis and recovery hint
        """
        correlation_ids = classification.correlation_ids
        stage = classification.stage
        failure_type = classification.failure_type
        
        # Build list of observed errors
        observed_errors = [classification.observed_error] if classification.observed_error else []
        
        # Infer likely cause based on failure type and stage
        likely_cause, contributing_factors, recovery_hint = self._infer_diagnosis(
            stage, failure_type, classification.context
        )
        
        return StageDiagnosis(
            stage=stage,
            failure_type=failure_type,
            observed_errors=observed_errors,
            observed_events=classification.observed_events,
            timestamps=[classification.timestamp],
            likely_cause=likely_cause,
            contributing_factors=contributing_factors,
            recovery_hint=recovery_hint,
            correlation_ids=correlation_ids
        )
    
    def _infer_diagnosis(
        self,
        stage: str,
        failure_type: str,
        context: Dict[str, Any]
    ) -> Tuple[Optional[str], List[str], Optional[str]]:
        """Infer likely cause and recovery hint.
        
        Returns (likely_cause, contributing_factors, recovery_hint)
        where hints are suggestions, not certainty.
        """
        # Stage-specific inference
        if stage == FailureStage.PROPOSAL.value:
            if failure_type == FailureType.PROPOSAL_REJECTED.value:
                return (
                    "Proposal was rejected by validation gates",
                    ["Trust threshold not met", "Health check failed", "Safety hooks blocked"],
                    "Review rejection reason and address blocking criteria"
                )
            elif failure_type == FailureType.PROPOSAL_EXPIRED.value:
                return (
                    "Proposal expired before approval",
                    ["TTL too short", "Operator delay in approval"],
                    "Increase proposal TTL or expedite approval workflow"
                )
            elif failure_type == FailureType.PROPOSAL_VALIDATION_FAILED.value:
                return (
                    "Proposal validation failed capability/trust checks",
                    ["Missing capability on target", "Insufficient trust level"],
                    "Verify target node capabilities and trust status"
                )
        
        elif stage == FailureStage.HANDSHAKE.value:
            if failure_type == FailureType.HANDSHAKE_FAILED.value:
                return (
                    "Handshake failed during protocol exchange",
                    ["Protocol version mismatch", "Capability negotiation failed"],
                    "Verify node protocol compatibility and capability registration"
                )
            elif failure_type == FailureType.HANDSHAKE_TRUST_REJECTED.value:
                return (
                    "Handshake rejected due to insufficient trust",
                    ["Target trust status below threshold", "Trust verification failed"],
                    "Review and update trust state for target node"
                )
            elif failure_type == FailureType.HANDSHAKE_HEALTH_REJECTED.value:
                return (
                    "Handshake rejected due to unhealthy target",
                    ["Target health status unhealthy", "Health check timeout"],
                    "Verify target node health or adjust health threshold"
                )
        
        elif stage == FailureStage.ENVELOPE.value:
            if failure_type == FailureType.ENVELOPE_GATE_FAILED.value:
                return (
                    "Execution envelope failed gate validation",
                    ["Trust gate failed", "Health gate failed", "Safety gate failed"],
                    "Review gate failure logs and address blocking criteria"
                )
            elif failure_type == FailureType.ENVELOPE_DISPATCH_FAILED.value:
                return (
                    "Execution envelope dispatch failed",
                    ["Target unreachable", "Network timeout", "Target not acknowledged"],
                    "Verify target availability and network connectivity"
                )
        
        elif stage == FailureStage.DEADLINE.value:
            if failure_type == FailureType.DEADLINE_BREACHED.value:
                return (
                    "Execution exceeded deadline",
                    ["Task duration exceeded limit", "No heartbeat within timeout"],
                    "Increase deadline threshold or optimize task execution"
                )
        
        elif stage == FailureStage.RECEIPT.value:
            return (
                "Receipt acknowledgment failed",
                ["Target did not acknowledge", "Receipt timeout", "Network partition"],
                "Verify target availability and receipt processing workflow"
            )
        
        return (
            "Unknown failure type",
            ["Insufficient diagnostic context"],
            "Review raw event logs for detailed failure information"
        )


# ============================================================================
# CROSS-STAGE CORRELATION
# ============================================================================


@dataclass
class CrossStageCorrelation:
    """Correlation of failures across multiple stages.
    
    Tracks failure chain through the execution lifecycle.
    """
    
    flow_id: str
    
    # Failure events by stage
    failures_by_stage: Dict[str, StageDiagnosis] = field(default_factory=dict)
    
    # Timeline of events
    event_timeline: List[Dict[str, Any]] = field(default_factory=list)
    
    # Root cause hypothesis across stages
    primary_cause: Optional[str] = None
    cascade_triggers: List[str] = field(default_factory=list)
    
    # Recovery hint
    recovery_hint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "failures_by_stage": {k: v.to_dict() for k, v in self.failures_by_stage.items()},
            "event_timeline": self.event_timeline,
            "primary_cause": self.primary_cause,
            "cascade_triggers": self.cascade_triggers,
            "recovery_hint": self.recovery_hint
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrossStageCorrelation":
        failures_by_stage = {}
        for k, v in data.get("failures_by_stage", {}).items():
            failures_by_stage[k] = StageDiagnosis.from_dict(v)
        
        return cls(
            flow_id=data["flow_id"],
            failures_by_stage=failures_by_stage,
            event_timeline=data.get("event_timeline", []),
            primary_cause=data.get("primary_cause"),
            cascade_triggers=data.get("cascade_triggers", []),
            recovery_hint=data.get("recovery_hint")
        )


class CrossStageCorrelator:
    """Correlates failures across stages to identify failure chains.
    
    Analyzes how failures in one stage propagate to others.
    """
    
    def __init__(self, emitter: TelemetryEventEmitter):
        """Initialize correlator with telemetry emitter reference."""
        self._emitter = emitter
        self._diagnosis_builder = StageDiagnosisBuilder()
    
    def correlate_flow(self, flow_id: str) -> Optional[CrossStageCorrelation]:
        """Correlate failures for a specific flow.
        
        Args:
            flow_id: The flow ID to analyze
            
        Returns:
            CrossStageCorrelation if failures detected, None otherwise
        """
        # Get all events for this flow
        events = self._emitter.get_events_by_flow(flow_id)
        if not events:
            return None
        
        # Classify all failures in this flow
        failures = self._build_all_failures(events, flow_id)
        if not failures:
            return None
        
        # Build correlation
        correlation = CrossStageCorrelation(flow_id=flow_id)
        correlation.failures_by_stage = failures
        
        # Build event timeline
        correlation.event_timeline = [
            {
                "timestamp": e.timestamp.isoformat().replace("+00:00", "Z"),
                "event_type": e.event_type,
                "stage": self._event_to_stage(e.event_type)
            }
            for e in sorted(events, key=lambda x: x.timestamp)
        ]
        
        # Infer primary cause and cascade
        self._infer_cascade(correlation)
        
        return correlation
    
    def _build_all_failures(
        self,
        events: List[TelemetryEvent],
        flow_id: str
    ) -> Dict[str, StageDiagnosis]:
        """Build all stage failures from events."""
        failures = {}
        
        # Get unique failure stages from events
        failure_types = [
            TelemetryEventType.FLOW_FAILED.value,
            TelemetryEventType.FLOW_REJECTED.value,
            TelemetryEventType.HANDSHAKE_FAILURE.value,
            TelemetryEventType.DEADLINE_BREACH.value,
        ]
        
        for event in events:
            if event.event_type in failure_types:
                # Create classification
                classification = FailureClassification(
                    failure_type=self._map_to_failure_type(event.event_type),
                    stage=self._event_to_stage(event.event_type),
                    observed_error=self._extract_error(event),
                    observed_events=[e.to_dict() for e in events],
                    correlation_ids={
                        "flow_id": flow_id,
                        "event_id": event.event_id
                    }
                )
                
                # Build diagnosis
                diagnosis = self._diagnosis_builder.build_diagnosis(classification)
                failures[diagnosis.stage] = diagnosis
        
        return failures
    
    def _infer_cascade(self, correlation: CrossStageCorrelation) -> None:
        """Infer primary cause and cascade triggers.
        
        Analyzes failure chain to identify root cause.
        """
        if not correlation.failures_by_stage:
            return
        
        # Get stages in order of execution
        stage_order = [
            FailureStage.PROPOSAL.value,
            FailureStage.HANDSHAKE.value,
            FailureStage.ENVELOPE.value,
            FailureStage.RECEIPT.value,
            FailureStage.DEADLINE.value,
        ]
        
        # Find first failure
        first_failure = None
        for stage in stage_order:
            if stage in correlation.failures_by_stage:
                first_failure = correlation.failures_by_stage[stage]
                break
        
        if first_failure:
            correlation.primary_cause = first_failure.likely_cause
            correlation.recovery_hint = first_failure.recovery_hint
        
        # Identify cascade triggers
        stages = list(correlation.failures_by_stage.keys())
        if len(stages) > 1:
            for i, stage in enumerate(stages[1:], 1):
                prev_stage = stages[i - 1]
                prev_diag = correlation.failures_by_stage[prev_stage]
                
                # Determine if this failure was cascaded
                if prev_stage == FailureStage.PROPOSAL.value and stage == FailureStage.HANDSHAKE.value:
                    correlation.cascade_triggers.append(
                        f"Handshake failed after proposal rejection"
                    )
                elif prev_stage == FailureStage.HANDSHAKE.value and stage == FailureStage.ENVELOPE.value:
                    correlation.cascade_triggers.append(
                        f"Envelope failed after handshake failure"
                    )
                elif prev_stage == FailureStage.ENVELOPE.value and stage == FailureStage.DEADLINE.value:
                    correlation.cascade_triggers.append(
                        f"Deadline breach after execution failure"
                    )
    
    def _event_to_stage(self, event_type: str) -> str:
        """Map event type to stage."""
        stage_map = {
            TelemetryEventType.FLOW_FAILED.value: FailureStage.ENVELOPE.value,
            TelemetryEventType.FLOW_REJECTED.value: FailureStage.PROPOSAL.value,
            TelemetryEventType.HANDSHAKE_FAILURE.value: FailureStage.HANDSHAKE.value,
            TelemetryEventType.DEADLINE_BREACH.value: FailureStage.DEADLINE.value,
            TelemetryEventType.HANDSHAKE_SUCCESS.value: FailureStage.HANDSHAKE.value,
            TelemetryEventType.FLOW_COMPLETED.value: FailureStage.COMPLETED.value,
        }
        return stage_map.get(event_type, FailureStage.UNKNOWN.value)
    
    def _extract_error(self, event: TelemetryEvent) -> Optional[str]:
        """Extract error from event properties."""
        if event.properties:
            return (
                event.properties.get("error")
                or event.properties.get("reason")
                or event.properties.get("description")
            )
        return None
    
    def _map_to_failure_type(self, event_type: str) -> str:
        """Map event type to failure type."""
        type_map = {
            TelemetryEventType.FLOW_FAILED.value: FailureType.UNKNOWN.value,
            TelemetryEventType.FLOW_REJECTED.value: FailureType.PROPOSAL_REJECTED.value,
            TelemetryEventType.HANDSHAKE_FAILURE.value: FailureType.HANDSHAKE_FAILED.value,
            TelemetryEventType.DEADLINE_BREACH.value: FailureType.DEADLINE_BREACHED.value,
        }
        return type_map.get(event_type, FailureType.UNKNOWN.value)
    
    def correlate_all_flows(self) -> List[CrossStageCorrelation]:
        """Correlate all flows with failures.
        
        Returns:
            List of cross-stage correlations
        """
        correlations = []
        flows = self._emitter.get_all_flows()
        
        for flow_id in flows:
            correlation = self.correlate_flow(flow_id)
            if correlation:
                correlations.append(correlation)
        
        return correlations


# ============================================================================
# DIAGNOSTIC SUMMARY
# ============================================================================


@dataclass
class DiagnosticSummary:
    """Aggregated diagnostic summary for operator consumption.
    
    Combines multiple correlations into a readable summary.
    """
    
    flow_id: str
    
    # Failure count by stage
    failures_by_stage: Dict[str, int] = field(default_factory=dict)
    
    # Summary of root causes
    root_cause_summary: List[str] = field(default_factory=list)
    
    # Summary of recovery hints
    recovery_hints: List[str] = field(default_factory=list)
    
    # Overall status
    status: str = "unknown"  # active, resolved, needs_review
    
    # Metadata
    summary_created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    correlation_ids: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "failures_by_stage": self.failures_by_stage,
            "root_cause_summary": self.root_cause_summary,
            "recovery_hints": self.recovery_hints,
            "status": self.status,
            "summary_created_at": self.summary_created_at,
            "correlation_ids": self.correlation_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiagnosticSummary":
        return cls(
            flow_id=data["flow_id"],
            failures_by_stage=data.get("failures_by_stage", {}),
            root_cause_summary=data.get("root_cause_summary", []),
            recovery_hints=data.get("recovery_hints", []),
            status=data.get("status", "unknown"),
            summary_created_at=data.get("summary_created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            correlation_ids=data.get("correlation_ids", {})
        )


class DiagnosticSummaryBuilder:
    """Builds diagnostic summaries from correlations.
    
    Aggregates failure data into operator-readable summaries.
    """
    
    def build_summary(self, correlation: CrossStageCorrelation) -> DiagnosticSummary:
        """Build summary from cross-stage correlation.
        
        Args:
            correlation: CrossStageCorrelation from correlator
            
        Returns:
            DiagnosticSummary for operator consumption
        """
        summary = DiagnosticSummary(flow_id=correlation.flow_id)
        
        # Count failures by stage
        for stage in correlation.failures_by_stage:
            summary.failures_by_stage[stage] = summary.failures_by_stage.get(stage, 0) + 1
        
        # Collect root cause summaries
        if correlation.primary_cause:
            summary.root_cause_summary.append(
                f"Primary cause: {correlation.primary_cause}"
            )
        
        for stage, diagnosis in correlation.failures_by_stage.items():
            if diagnosis.likely_cause and diagnosis.likely_cause != "Unknown failure type":
                summary.root_cause_summary.append(
                    f"[{stage}] {diagnosis.likely_cause}"
                )
        
        # Collect recovery hints (deduplicate)
        seen_hints = set()
        if correlation.recovery_hint:
            summary.recovery_hints.append(correlation.recovery_hint)
            seen_hints.add(correlation.recovery_hint)
        
        for stage, diagnosis in correlation.failures_by_stage.items():
            if diagnosis.recovery_hint and diagnosis.recovery_hint not in seen_hints:
                summary.recovery_hints.append(diagnosis.recovery_hint)
                seen_hints.add(diagnosis.recovery_hint)
        
        # Set status based on failure count
        if len(correlation.failures_by_stage) == 0:
            summary.status = "resolved"
        elif len(correlation.failures_by_stage) == 1:
            summary.status = "needs_review"
        else:
            summary.status = "needs_review"
        
        # Add correlation IDs
        summary.correlation_ids = {"flow_id": correlation.flow_id}
        
        return summary
    
    def build_summary_list(
        self,
        correlations: List[CrossStageCorrelation]
    ) -> List[DiagnosticSummary]:
        """Build summaries for multiple correlations.
        
        Args:
            correlations: List of correlations
            
        Returns:
            List of diagnostic summaries
        """
        return [self.build_summary(c) for c in correlations]


# ============================================================================
# DIAGNOSTIC HOOKS
# ============================================================================


class DiagnosticHooks:
    """Read-only diagnostic hooks for operator workflow.
    
    Provides analysis of distributed execution failures without
    orchestration, sharding, or aggregation.
    """
    
    def __init__(self, emitter: TelemetryEventEmitter):
        """Initialize hooks with telemetry emitter reference."""
        self._emitter = emitter
        self._classifier = FailureClassifier(emitter)
        self._correlator = CrossStageCorrelator(emitter)
        self._summary_builder = DiagnosticSummaryBuilder()
    
    def get_failure_summary(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get failure summary for a specific flow.
        
        Args:
            flow_id: The flow ID to analyze
            
        Returns:
            Summary dict or None if no failures
        """
        correlation = self._correlator.correlate_flow(flow_id)
        if not correlation:
            return None
        
        summary = self._summary_builder.build_summary(correlation)
        return summary.to_dict()
    
    def get_all_failure_summaries(self) -> List[Dict[str, Any]]:
        """Get failure summaries for all flows.
        
        Returns:
            List of summary dicts
        """
        correlations = self._correlator.correlate_all_flows()
        summaries = self._summary_builder.build_summary_list(correlations)
        return [s.to_dict() for s in summaries]
    
    def get_detailed_diagnosis(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed diagnosis with stage-by-stage breakdown.
        
        Args:
            flow_id: The flow ID to analyze
            
        Returns:
            Detailed diagnosis dict or None if no failures
        """
        correlation = self._correlator.correlate_flow(flow_id)
        if not correlation:
            return None
        
        return {
            "flow_id": correlation.flow_id,
            "failures_by_stage": {
                k: v.to_dict() for k, v in correlation.failures_by_stage.items()
            },
            "event_timeline": correlation.event_timeline,
            "primary_cause": correlation.primary_cause,
            "cascade_triggers": correlation.cascade_triggers,
            "recovery_hint": correlation.recovery_hint
        }
    
    def get_failure_classification(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get failure classification for a specific flow.
        
        Args:
            flow_id: The flow ID to analyze
            
        Returns:
            Classification dict or None if no failures
        """
        classification = self._classifier.classify_flow_failure(flow_id)
        if not classification:
            return None
        
        return classification.to_dict()
    
    def classify_all_failures(self) -> List[Dict[str, Any]]:
        """Classify all failures across all flows.
        
        Returns:
            List of failure classifications
        """
        classifications = self._classifier.classify_all_failures()
        return [c.to_dict() for c in classifications]
    
    def get_diagnostic_status(self) -> Dict[str, Any]:
        """Get high-level diagnostic status.
        
        Returns:
            Status dict with counts
        """
        all_failures = self.classify_all_failures()
        
        # Count by type
        type_counts: Dict[str, int] = {}
        for f in all_failures:
            type_counts[f.get("failure_type", "unknown")] = type_counts.get(f.get("failure_type"), 0) + 1
        
        # Count by stage
        stage_counts: Dict[str, int] = {}
        for f in all_failures:
            stage_counts[f.get("stage", "unknown")] = stage_counts.get(f.get("stage"), 0) + 1
        
        return {
            "total_flows_analyzed": self._emitter.get_flow_count(),
            "flows_with_failures": len(all_failures),
            "failures_by_type": type_counts,
            "failures_by_stage": stage_counts
        }
    
    def get_operator_readable_summary(self) -> str:
        """Get human-readable operator summary.
        
        Returns:
            Multi-line string for operator console
        """
        status = self.get_diagnostic_status()
        summaries = self.get_all_failure_summaries()
        
        lines = [
            "=== DISTRIBUTED DIAGNOSTIC SUMMARY ===",
            f"Total Flows Analyzed: {status['total_flows_analyzed']}",
            f"Flows with Failures: {status['flows_with_failures']}",
            "",
            "=== FAILURES BY TYPE ===",
        ]
        
        for ftype, count in sorted(status["failures_by_type"].items()):
            lines.append(f"  {ftype}: {count}")
        
        lines.append("")
        lines.append("=== FAILURES BY STAGE ===")
        for stage, count in sorted(status["failures_by_stage"].items()):
            lines.append(f"  {stage}: {count}")
        
        if summaries:
            lines.append("")
            lines.append("=== FAILURE DETAILS ===")
            for i, summary in enumerate(summaries, 1):
                lines.append(f"--- Flow {i}: {summary.get('flow_id', 'unknown')} ---")
                lines.append(f"  Status: {summary.get('status', 'unknown')}")
                lines.append(f"  Root Cause: {summary.get('root_cause_summary', ['None'])}")
                lines.append(f"  Recovery Hint: {summary.get('recovery_hints', ['None'])}")
        
        return "\n".join(lines)


def create_diagnostic_hooks(emitter: TelemetryEventEmitter) -> DiagnosticHooks:
    """Factory function to create diagnostic hooks.
    
    Args:
        emitter: TelemetryEventEmitter for event data
        
    Returns:
        DiagnosticHooks instance
    """
    return DiagnosticHooks(emitter)
