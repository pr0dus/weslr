"""Distributed Execution Integration Layer (v64)

Integrates v61 + v62 + v63 into one coherent distributed execution flow.
Provides proposal → envelope → dispatch → receipt → acknowledgment flow
with correlation continuity across all stages.

Architecture:
  - ExecutionOrchestrator — main integration controller
  - ProposalToEnvelopeBridge — proposal to envelope conversion
  - ExecutionFlowState — tracks execution across stages
  - StageCorrelation — maintains ID correlation continuity
  - RejectionPropagation — rejection handling across stages
  - FailurePropagation — failure handling across stages
  - RollbackCoordination — rollback coordination
  - IntegratedAuditTrace — unified audit across v61-v63
  - ExecutionFlowController — single-point control

Rules:
  - Integration only — no new orchestration logic
  - Correlation continuity mandatory
  - Audit trace continuity across all stages
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No consensus
  - No scheduler/retry engine
  - No handshake protocol
  - No TIA/C#
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .remote_action_proposal import (
    RemoteActionProposal,
    ProposalStatus,
    RejectionReason,
    RejectionCategory,
    ApprovalMode,
    ProposalAuditTrace,
)
from .controlled_execution_envelope import (
    ExecutionRequestEnvelope,
    ExecutionLifecycleState,
    ExecutionGates,
    ExecutionAuditTrace,
    ExecutionEventType,
    ExplicitExecutionController,
)
from .remote_execution_receipt import (
    ExecutionReceipt,
    ReceiptType,
    AcknowledgmentState,
    ReceiptEventType,
    ReceiptProtocol,
    ReceiptAuditTrace,
    CompletionConfirmation,
    FailureConfirmation,
)
from .node_registry import NodeRegistry
from .node_identity import NodeTrustState


# ============================================================================
# EXECUTION FLOW STATE
# ============================================================================


class FlowStage(str, Enum):
    """Stages in the integrated execution flow."""
    PROPOSAL_CREATED = "proposal_created"
    PROPOSAL_APPROVED = "proposal_approved"
    ENVELOPE_CREATED = "envelope_created"
    GATES_EVALUATED = "gates_evaluated"
    ENVELOPE_AUTHORIZED = "envelope_authorized"
    ENVELOPE_DISPATCHED = "envelope_dispatched"
    RECEIPT_RECEIVED = "receipt_received"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_REJECTED = "execution_rejected"
    ROLLBACK_INITIATED = "rollback_initiated"
    ROLLBACK_COMPLETED = "rollback_completed"


@dataclass
class ExecutionFlowState:
    """Tracks execution across all integrated stages."""
    
    flow_id: str
    current_stage: str = FlowStage.PROPOSAL_CREATED.value
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Component references
    proposal_id: Optional[str] = None
    request_id: Optional[str] = None
    receipt_ids: List[str] = field(default_factory=list)
    
    # Status
    is_complete: bool = False
    is_failed: bool = False
    is_rejected: bool = False
    is_rolled_back: bool = False
    
    def __post_init__(self):
        """Initialize stage history."""
        if not self.stage_history:
            self._transition_to(FlowStage.PROPOSAL_CREATED.value, "Flow initialized")
    
    def _transition_to(self, new_stage: str, reason: str) -> None:
        """Transition to new stage."""
        old_stage = self.current_stage
        self.current_stage = new_stage
        self.stage_history.append({
            "from": old_stage,
            "to": new_stage,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
    
    def mark_proposal_approved(self, proposal_id: str) -> None:
        """Mark proposal as approved."""
        self.proposal_id = proposal_id
        self._transition_to(FlowStage.PROPOSAL_APPROVED.value, f"Proposal {proposal_id} approved")
    
    def mark_envelope_created(self, request_id: str) -> None:
        """Mark envelope created."""
        self.request_id = request_id
        self._transition_to(FlowStage.ENVELOPE_CREATED.value, f"Envelope {request_id} created")
    
    def mark_gates_evaluated(self) -> None:
        """Mark gates evaluated."""
        self._transition_to(FlowStage.GATES_EVALUATED.value, "Gates evaluated")
    
    def mark_envelope_authorized(self) -> None:
        """Mark envelope authorized."""
        self._transition_to(FlowStage.ENVELOPE_AUTHORIZED.value, "Envelope authorized")
    
    def mark_envelope_dispatched(self) -> None:
        """Mark envelope dispatched."""
        self._transition_to(FlowStage.ENVELOPE_DISPATCHED.value, "Envelope dispatched")
    
    def mark_receipt_received(self, receipt_id: str) -> None:
        """Mark receipt received."""
        self.receipt_ids.append(receipt_id)
        self._transition_to(FlowStage.RECEIPT_RECEIVED.value, f"Receipt {receipt_id} received")
    
    def mark_execution_completed(self) -> None:
        """Mark execution completed."""
        self.is_complete = True
        self._transition_to(FlowStage.EXECUTION_COMPLETED.value, "Execution completed")
    
    def mark_execution_failed(self, reason: str) -> None:
        """Mark execution failed."""
        self.is_failed = True
        self._transition_to(FlowStage.EXECUTION_FAILED.value, f"Execution failed: {reason}")
    
    def mark_execution_rejected(self, reason: str) -> None:
        """Mark execution rejected."""
        self.is_rejected = True
        self._transition_to(FlowStage.EXECUTION_REJECTED.value, f"Execution rejected: {reason}")
    
    def mark_rollback_initiated(self) -> None:
        """Mark rollback initiated."""
        self._transition_to(FlowStage.ROLLBACK_INITIATED.value, "Rollback initiated")
    
    def mark_rollback_completed(self) -> None:
        """Mark rollback completed."""
        self.is_rolled_back = True
        self._transition_to(FlowStage.ROLLBACK_COMPLETED.value, "Rollback completed")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "current_stage": self.current_stage,
            "stage_history": self.stage_history,
            "proposal_id": self.proposal_id,
            "request_id": self.request_id,
            "receipt_ids": self.receipt_ids,
            "is_complete": self.is_complete,
            "is_failed": self.is_failed,
            "is_rejected": self.is_rejected,
            "is_rolled_back": self.is_rolled_back
        }


# ============================================================================
# STAGE CORRELATION
# ============================================================================


@dataclass
class StageCorrelation:
    """Maintains ID correlation continuity across stages."""
    
    flow_id: str
    proposal_id: Optional[str] = None
    request_id: Optional[str] = None
    receipt_ids: List[str] = field(default_factory=list)
    correlation_map: Dict[str, str] = field(default_factory=dict)
    
    def link_proposal(self, proposal_id: str) -> None:
        """Link proposal to flow."""
        self.proposal_id = proposal_id
        self.correlation_map["proposal"] = proposal_id
    
    def link_envelope(self, request_id: str) -> None:
        """Link envelope to flow."""
        self.request_id = request_id
        self.correlation_map["envelope"] = request_id
    
    def link_receipt(self, receipt_id: str) -> None:
        """Link receipt to flow."""
        self.receipt_ids.append(receipt_id)
        if "receipts" not in self.correlation_map:
            self.correlation_map["receipts"] = []
        self.correlation_map["receipts"].append(receipt_id)
    
    def get_correlated_ids(self) -> Dict[str, Any]:
        """Get all correlated IDs."""
        return {
            "flow_id": self.flow_id,
            "proposal_id": self.proposal_id,
            "request_id": self.request_id,
            "receipt_ids": self.receipt_ids
        }
    
    def resolve_to_request_id(self) -> Optional[str]:
        """Resolve to execution request ID."""
        return self.request_id
    
    def resolve_to_proposal_id(self) -> Optional[str]:
        """Resolve to proposal ID."""
        return self.proposal_id


# ============================================================================
# REJECTION PROPAGATION
# ============================================================================


@dataclass
class RejectionPropagation:
    """Propagates rejections across proposal → envelope → receipt stages."""
    
    flow_id: str
    rejection_source: str  # proposal, envelope, receipt
    rejection_reason: Optional[RejectionReason] = None
    propagated_stages: List[str] = field(default_factory=list)
    propagated_at: Optional[str] = None
    
    def propagate_from_proposal(self, proposal: RemoteActionProposal) -> None:
        """Propagate rejection from proposal stage."""
        if proposal.rejection_reason:
            self.rejection_source = "proposal"
            self.rejection_reason = proposal.rejection_reason
            self.propagated_stages.append("proposal")
            self.propagated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def propagate_from_envelope(self, envelope: ExecutionRequestEnvelope) -> None:
        """Propagate rejection from envelope stage."""
        if envelope.rejection_reason:
            self.rejection_source = "envelope"
            self.rejection_reason = envelope.rejection_reason
            self.propagated_stages.append("envelope")
            self.propagated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "rejection_source": self.rejection_source,
            "rejection_reason": self.rejection_reason.to_dict() if self.rejection_reason else None,
            "propagated_stages": self.propagated_stages,
            "propagated_at": self.propagated_at
        }


# ============================================================================
# FAILURE PROPAGATION
# ============================================================================


@dataclass
class FailurePropagation:
    """Propagates failures across stages with context preservation."""
    
    flow_id: str
    failure_source: str  # envelope, receipt
    failure_reason: Optional[str] = None
    failure_context: Dict[str, Any] = field(default_factory=dict)
    propagated_stages: List[str] = field(default_factory=list)
    propagated_at: Optional[str] = None
    
    def propagate_from_envelope(self, envelope: ExecutionRequestEnvelope) -> None:
        """Propagate failure from envelope stage."""
        if envelope.failure_reason:
            self.failure_source = "envelope"
            self.failure_reason = envelope.failure_reason
            self.propagated_stages.append("envelope")
            self.propagated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self.failure_context["envelope_state"] = envelope.state
            self.failure_context["envelope_id"] = envelope.request_id
    
    def propagate_from_receipt(self, receipt: ExecutionReceipt) -> None:
        """Propagate failure from receipt stage."""
        if receipt.receipt_type == ReceiptType.FAILURE_CONFIRMED.value:
            self.failure_source = "receipt"
            self.failure_reason = receipt.message
            self.propagated_stages.append("receipt")
            self.propagated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self.failure_context["receipt_details"] = receipt.details
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "failure_source": self.failure_source,
            "failure_reason": self.failure_reason,
            "failure_context": self.failure_context,
            "propagated_stages": self.propagated_stages,
            "propagated_at": self.propagated_at
        }


# ============================================================================
# ROLLBACK COORDINATION
# ============================================================================


@dataclass
class RollbackCoordination:
    """Coordinates rollback across proposal/envelope/receipt stages."""
    
    flow_id: str
    rollback_initiated: bool = False
    rollback_completed: bool = False
    rollback_initiated_at: Optional[str] = None
    rollback_completed_at: Optional[str] = None
    affected_stages: List[str] = field(default_factory=list)
    rollback_reason: Optional[str] = None
    
    def initiate_rollback(self, reason: str) -> None:
        """Initiate rollback across stages."""
        self.rollback_initiated = True
        self.rollback_reason = reason
        self.rollback_initiated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def mark_stage_rollback(self, stage: str) -> None:
        """Mark stage as rolled back."""
        if stage not in self.affected_stages:
            self.affected_stages.append(stage)
    
    def complete_rollback(self) -> None:
        """Mark rollback as completed."""
        self.rollback_completed = True
        self.rollback_completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "rollback_initiated": self.rollback_initiated,
            "rollback_completed": self.rollback_completed,
            "rollback_initiated_at": self.rollback_initiated_at,
            "rollback_completed_at": self.rollback_completed_at,
            "affected_stages": self.affected_stages,
            "rollback_reason": self.rollback_reason
        }


# ============================================================================
# INTEGRATED AUDIT TRACE
# ============================================================================


class IntegratedAuditTrace:
    """Unified audit trace across all v61-v63 components."""
    
    def __init__(self, local_node_id: str):
        self.local_node_id = local_node_id
        self.proposal_audit = ProposalAuditTrace(local_node_id)
        self.execution_audit = ExecutionAuditTrace(local_node_id)
        self.receipt_audit = ReceiptAuditTrace(local_node_id)
        self._integrated_events: List[Dict[str, Any]] = []
    
    def log_flow_event(
        self,
        flow_id: str,
        stage: str,
        event_type: str,
        details: Optional[Dict] = None,
        correlation: Optional[StageCorrelation] = None
    ) -> None:
        """Log integrated flow event."""
        event = {
            "event_id": str(uuid.uuid4()),
            "flow_id": flow_id,
            "stage": stage,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "node_id": self.local_node_id,
            "details": details or {},
            "correlation": correlation.get_correlated_ids() if correlation else {}
        }
        self._integrated_events.append(event)
    
    def get_flow_trace(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get full audit trace for a flow."""
        return [e for e in self._integrated_events if e["flow_id"] == flow_id]
    
    def get_stats(self) -> Dict[str, int]:
        """Get audit statistics."""
        return {
            "integrated_events": len(self._integrated_events),
            "proposal_events": self.proposal_audit.get_stats()["total_events"],
            "execution_events": self.execution_audit.get_stats()["total_events"],
            "receipt_events": self.receipt_audit.get_stats()["total_events"]
        }


# ============================================================================
# EXECUTION ORCHESTRATOR
# ============================================================================


class ExecutionOrchestrator:
    """Main integration controller for distributed execution flow.
    
    Integrates proposal (v61) → envelope (v62) → receipt (v63).
    """
    
    def __init__(
        self,
        local_node_id: str,
        registry: NodeRegistry,
        proposal_audit: Optional[ProposalAuditTrace] = None,
        execution_audit: Optional[ExecutionAuditTrace] = None,
        receipt_audit: Optional[ReceiptAuditTrace] = None
    ):
        self.local_node_id = local_node_id
        self.registry = registry
        self.audit = IntegratedAuditTrace(local_node_id)
        
        # Wire up sub-audits
        if proposal_audit:
            self.audit.proposal_audit = proposal_audit
        if execution_audit:
            self.audit.execution_audit = execution_audit
        if receipt_audit:
            self.audit.receipt_audit = receipt_audit
        
        # Controllers
        self.execution_controller = ExplicitExecutionController(
            local_node_id=local_node_id,
            registry=registry,
            audit_trace=self.audit.execution_audit
        )
        self.receipt_protocol = ReceiptProtocol(
            local_node_id=local_node_id,
            audit_trace=self.audit.receipt_audit
        )
        
        # Flow tracking
        self._flows: Dict[str, ExecutionFlowState] = {}
        self._correlations: Dict[str, StageCorrelation] = {}
        self._rejections: Dict[str, RejectionPropagation] = {}
        self._failures: Dict[str, FailurePropagation] = {}
        self._rollbacks: Dict[str, RollbackCoordination] = {}
    
    def create_flow(self, proposal: RemoteActionProposal) -> ExecutionFlowState:
        """Create new execution flow from proposal."""
        flow_id = str(uuid.uuid4())
        
        flow = ExecutionFlowState(flow_id=flow_id)
        flow.proposal_id = proposal.proposal_id
        
        correlation = StageCorrelation(flow_id=flow_id)
        correlation.link_proposal(proposal.proposal_id)
        
        self._flows[flow_id] = flow
        self._correlations[flow_id] = correlation
        
        self.audit.log_flow_event(
            flow_id=flow_id,
            stage="proposal",
            event_type="flow_created",
            correlation=correlation
        )
        
        return flow
    
    def approved_to_envelope(
        self,
        flow_id: str,
        proposal: RemoteActionProposal,
        execution_intent: str
    ) -> Tuple[Optional[ExecutionRequestEnvelope], Optional[str]]:
        """Convert approved proposal to execution envelope."""
        flow = self._flows.get(flow_id)
        correlation = self._correlations.get(flow_id)
        
        if not flow or not correlation:
            return None, "Flow not found"
        
        # Check proposal is approved
        if proposal.status != ProposalStatus.APPROVED.value:
            return None, f"Proposal not approved: {proposal.status}"
        
        flow.mark_proposal_approved(proposal.proposal_id)
        
        # Create envelope
        envelope = self.execution_controller.create_envelope(
            proposal=proposal,
            execution_intent=execution_intent
        )
        
        flow.mark_envelope_created(envelope.request_id)
        correlation.link_envelope(envelope.request_id)
        
        self.audit.log_flow_event(
            flow_id=flow_id,
            stage="envelope",
            event_type="envelope_created",
            details={"request_id": envelope.request_id},
            correlation=correlation
        )
        
        return envelope, None
    
    def evaluate_and_authorize(self, flow_id: str) -> Tuple[bool, Optional[str]]:
        """Evaluate gates and authorize execution."""
        flow = self._flows.get(flow_id)
        correlation = self._correlations.get(flow_id)
        
        if not flow or not correlation:
            return False, "Flow not found"
        
        if not correlation.request_id:
            return False, "No envelope created"
        
        # Evaluate gates
        passed, failures = self.execution_controller.evaluate_gates(correlation.request_id)
        flow.mark_gates_evaluated()
        
        if not passed:
            # Rejection
            envelope = self.execution_controller.get_envelope(correlation.request_id)
            rejection = RejectionPropagation(flow_id=flow_id, rejection_source="envelope")
            rejection.propagate_from_envelope(envelope)
            self._rejections[flow_id] = rejection
            flow.mark_execution_rejected(rejection.rejection_reason.description if rejection.rejection_reason else "Unknown")
            
            self.audit.log_flow_event(
                flow_id=flow_id,
                stage="gates",
                event_type="gates_failed",
                details={"reasons": [f.to_dict() for f in failures]},
                correlation=correlation
            )
            
            return False, "Gates failed"
        
        # Request and grant approval (automatic in this flow)
        self.execution_controller.request_approval(correlation.request_id)
        self.execution_controller.grant_approval(correlation.request_id, self.local_node_id)
        flow.mark_envelope_authorized()
        
        self.audit.log_flow_event(
            flow_id=flow_id,
            stage="authorization",
            event_type="envelope_authorized",
            correlation=correlation
        )
        
        return True, None
    
    def dispatch_and_receive_receipt(
        self,
        flow_id: str
    ) -> Tuple[Optional[ExecutionReceipt], Optional[str]]:
        """Dispatch envelope and receive receipt."""
        flow = self._flows.get(flow_id)
        correlation = self._correlations.get(flow_id)
        
        if not flow or not correlation or not correlation.request_id:
            return None, "Flow or envelope not found"
        
        # Dispatch
        self.execution_controller.dispatch(correlation.request_id)
        flow.mark_envelope_dispatched()
        
        # Create dispatch received receipt (as target would)
        envelope = self.execution_controller.get_envelope(correlation.request_id)
        receipt = self.receipt_protocol.create_dispatch_received_receipt(
            request_id=correlation.request_id,
            original_source=flow.proposal_id or "unknown",
            envelope_state=envelope.state
        )
        
        self.receipt_protocol.send_receipt(receipt)
        
        # Receive and validate (as source would)
        result = self.receipt_protocol.receive_receipt(
            receipt,
            expected_request_id=correlation.request_id,
            expected_source=self.local_node_id  # Simulating target
        )
        
        if not result.is_valid:
            return None, f"Receipt validation failed: {result.errors}"
        
        self.receipt_protocol.acknowledge_receipt(receipt)
        
        # Also acknowledge the envelope (as target would)
        self.execution_controller.acknowledge(correlation.request_id)
        
        flow.mark_receipt_received(receipt.receipt_id)
        correlation.link_receipt(receipt.receipt_id)
        
        self.audit.log_flow_event(
            flow_id=flow_id,
            stage="receipt",
            event_type="receipt_acknowledged",
            details={"receipt_id": receipt.receipt_id},
            correlation=correlation
        )
        
        return receipt, None
    
    def complete_flow(self, flow_id: str, result: Dict[str, Any]) -> None:
        """Mark flow as completed."""
        flow = self._flows.get(flow_id)
        correlation = self._correlations.get(flow_id)
        
        if not flow or not correlation:
            return
        
        if correlation.request_id:
            self.execution_controller.complete(correlation.request_id, result)
        
        flow.mark_execution_completed()
        
        self.audit.log_flow_event(
            flow_id=flow_id,
            stage="completion",
            event_type="execution_completed",
            details={"result": result},
            correlation=correlation
        )
    
    def fail_flow(self, flow_id: str, reason: str) -> None:
        """Mark flow as failed."""
        flow = self._flows.get(flow_id)
        correlation = self._correlations.get(flow_id)
        
        if not flow or not correlation:
            return
        
        # Propagate failure
        failure = FailurePropagation(flow_id=flow_id, failure_source="orchestrator")
        failure.failure_reason = reason
        self._failures[flow_id] = failure
        
        flow.mark_execution_failed(reason)
        
        self.audit.log_flow_event(
            flow_id=flow_id,
            stage="failure",
            event_type="execution_failed",
            details={"reason": reason},
            correlation=correlation
        )
    
    def initiate_rollback(self, flow_id: str, reason: str) -> bool:
        """Initiate rollback for flow."""
        flow = self._flows.get(flow_id)
        correlation = self._correlations.get(flow_id)
        
        if not flow or not correlation:
            return False
        
        rollback = RollbackCoordination(flow_id=flow_id)
        rollback.initiate_rollback(reason)
        
        if correlation.request_id:
            self.execution_controller.initiate_rollback(correlation.request_id, reason)
        
        self._rollbacks[flow_id] = rollback
        flow.mark_rollback_initiated()
        
        self.audit.log_flow_event(
            flow_id=flow_id,
            stage="rollback",
            event_type="rollback_initiated",
            details={"reason": reason},
            correlation=correlation
        )
        
        return True
    
    def complete_rollback(self, flow_id: str) -> None:
        """Complete rollback for flow."""
        flow = self._flows.get(flow_id)
        correlation = self._correlations.get(flow_id)
        rollback = self._rollbacks.get(flow_id)
        
        if not flow or not correlation or not rollback:
            return
        
        if correlation.request_id:
            self.execution_controller.complete_rollback(correlation.request_id)
        
        rollback.complete_rollback()
        flow.mark_rollback_completed()
        
        self.audit.log_flow_event(
            flow_id=flow_id,
            stage="rollback",
            event_type="rollback_completed",
            correlation=correlation
        )
    
    def get_flow(self, flow_id: str) -> Optional[ExecutionFlowState]:
        """Get flow by ID."""
        return self._flows.get(flow_id)
    
    def get_correlation(self, flow_id: str) -> Optional[StageCorrelation]:
        """Get correlation by flow ID."""
        return self._correlations.get(flow_id)
    
    def get_flow_trace(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get full audit trace for flow."""
        return self.audit.get_flow_trace(flow_id)
