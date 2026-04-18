"""Remote Execution Receipt / Acknowledgment Protocol (v63)

Acknowledgment layer that closes the loop on remote execution envelopes.
Provides protocol/state only — NOT orchestration logic.

Architecture:
  - ReceiptType — types of execution receipts
  - AcknowledgmentState — receipt acknowledgment states
  - ExecutionReceipt — canonical receipt model
  - ReceiptValidation — receipt authenticity and validation
  - CompletionConfirmation — success completion receipts
  - FailureConfirmation — failure receipts
  - RollbackAcknowledgment — rollback receipts
  - ReceiptAuditTrace — receipt event auditing
  - ReceiptProtocol — protocol handler for receipt lifecycle

Rules:
  - Protocol/state only — no execution logic changes
  - Correlation to execution request ID mandatory
  - Full audit traceability
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No distributed consensus
  - No retry scheduler
  - No orchestration engine
  - No TIA/C#
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from .controlled_execution_envelope import (
    ExecutionRequestEnvelope,
    ExecutionLifecycleState,
    ExecutionEventType,
)


# ============================================================================
# RECEIPT TYPES
# ============================================================================


class ReceiptType(str, Enum):
    """Types of execution receipts."""
    DISPATCH_RECEIVED = "dispatch_received"           # Target received dispatch
    EXECUTION_ACCEPTED = "execution_accepted"         # Target accepted execution
    EXECUTION_REFUSED = "execution_refused"           # Target refused execution
    COMPLETION_CONFIRMED = "completion_confirmed"     # Execution completed
    FAILURE_CONFIRMED = "failure_confirmed"             # Execution failed
    ROLLBACK_ACKNOWLEDGED = "rollback_acknowledged"     # Rollback acknowledged
    ROLLBACK_COMPLETED = "rollback_completed"           # Rollback completed


class AcknowledgmentState(str, Enum):
    """Acknowledgment states for receipts."""
    PENDING = "pending"                 # Receipt not yet received
    RECEIVED = "received"               # Receipt received, not validated
    VALIDATED = "validated"             # Receipt validated
    ACCEPTED = "accepted"               # Receipt accepted
    REFUSED = "refused"                 # Receipt refused
    ACKNOWLEDGED = "acknowledged"       # Receipt acknowledged


class ReceiptEventType(str, Enum):
    """Types of receipt audit events."""
    RECEIPT_CREATED = "receipt_created"
    RECEIPT_SENT = "receipt_sent"
    RECEIPT_RECEIVED = "receipt_received"
    RECEIPT_VALIDATED = "receipt_validated"
    RECEIPT_ACCEPTED = "receipt_accepted"
    RECEIPT_REFUSED = "receipt_refused"
    RECEIPT_ACKNOWLEDGED = "receipt_acknowledged"
    RECEIPT_EXPIRED = "receipt_expired"
    RECEIPT_REJECTED = "receipt_rejected"


# ============================================================================
# EXECUTION RECEIPT
# ============================================================================


@dataclass
class ExecutionReceipt:
    """Canonical receipt model for remote execution acknowledgment.
    
    Correlates to execution request ID for full traceability.
    """
    
    # Identity
    receipt_id: str
    request_id: str                   # Correlates to ExecutionRequestEnvelope
    receipt_type: str
    
    # Nodes
    source_node_id: str               # Node sending receipt
    target_node_id: str               # Node receiving receipt (original source)
    
    # Content
    envelope_state: Optional[str] = None  # Current state of execution envelope
    message: Optional[str] = None       # Human-readable message
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Acknowledgment
    acknowledgment_state: str = AcknowledgmentState.PENDING.value
    acknowledgment_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    sent_at: Optional[str] = None
    received_at: Optional[str] = None
    validated_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    expires_at: Optional[str] = None
    
    # Validation
    validation_errors: List[str] = field(default_factory=list)
    is_valid: bool = False
    
    def mark_sent(self) -> None:
        """Mark receipt as sent."""
        self.sent_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._transition_acknowledgment(AcknowledgmentState.PENDING.value, "Receipt sent")
    
    def mark_received(self) -> None:
        """Mark receipt as received."""
        self.received_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._transition_acknowledgment(AcknowledgmentState.RECEIVED.value, "Receipt received")
    
    def mark_validated(self, valid: bool, errors: Optional[List[str]] = None) -> None:
        """Mark receipt validation result."""
        self.validated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.is_valid = valid
        if errors:
            self.validation_errors = errors
        
        if valid:
            self._transition_acknowledgment(AcknowledgmentState.VALIDATED.value, "Receipt validated")
        else:
            self._transition_acknowledgment(AcknowledgmentState.REFUSED.value, f"Validation failed: {errors}")
    
    def mark_accepted(self) -> None:
        """Mark receipt as accepted."""
        self._transition_acknowledgment(AcknowledgmentState.ACCEPTED.value, "Receipt accepted")
    
    def mark_refused(self, reason: str) -> None:
        """Mark receipt as refused."""
        self._transition_acknowledgment(AcknowledgmentState.REFUSED.value, f"Refused: {reason}")
    
    def mark_acknowledged(self) -> None:
        """Mark receipt as acknowledged."""
        self.acknowledged_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._transition_acknowledgment(AcknowledgmentState.ACKNOWLEDGED.value, "Receipt acknowledged")
    
    def _transition_acknowledgment(self, new_state: str, reason: str) -> None:
        """Transition acknowledgment state."""
        old_state = self.acknowledgment_state
        self.acknowledgment_state = new_state
        self.acknowledgment_history.append({
            "from": old_state,
            "to": new_state,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
    
    def is_terminal(self) -> bool:
        """Check if receipt is in terminal state."""
        return self.acknowledgment_state in (
            AcknowledgmentState.ACKNOWLEDGED.value,
            AcknowledgmentState.REFUSED.value
        )
    
    def check_expiry(self) -> bool:
        """Check if receipt has expired."""
        if not self.expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expiry:
                if not self.is_terminal():
                    self._transition_acknowledgment(AcknowledgmentState.REFUSED.value, "TTL exceeded")
                return True
        except Exception:
            pass
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "request_id": self.request_id,
            "receipt_type": self.receipt_type,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "envelope_state": self.envelope_state,
            "message": self.message,
            "details": self.details,
            "acknowledgment_state": self.acknowledgment_state,
            "acknowledgment_history": self.acknowledgment_history,
            "created_at": self.created_at,
            "sent_at": self.sent_at,
            "received_at": self.received_at,
            "validated_at": self.validated_at,
            "acknowledged_at": self.acknowledged_at,
            "expires_at": self.expires_at,
            "validation_errors": self.validation_errors,
            "is_valid": self.is_valid
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionReceipt":
        receipt = cls(
            receipt_id=data["receipt_id"],
            request_id=data["request_id"],
            receipt_type=data["receipt_type"],
            source_node_id=data["source_node_id"],
            target_node_id=data["target_node_id"],
            envelope_state=data.get("envelope_state"),
            message=data.get("message"),
            details=data.get("details", {}),
            acknowledgment_state=data.get("acknowledgment_state", AcknowledgmentState.PENDING.value),
            acknowledgment_history=data.get("acknowledgment_history", []),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            sent_at=data.get("sent_at"),
            received_at=data.get("received_at"),
            validated_at=data.get("validated_at"),
            acknowledged_at=data.get("acknowledged_at"),
            expires_at=data.get("expires_at"),
            validation_errors=data.get("validation_errors", []),
            is_valid=data.get("is_valid", False)
        )
        return receipt


# ============================================================================
# RECEIPT VALIDATION
# ============================================================================


@dataclass
class ReceiptValidationResult:
    """Result of receipt validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add validation error."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add validation warning."""
        self.warnings.append(warning)


class ReceiptValidation:
    """Validates receipt authenticity, correlation, and freshness."""
    
    def __init__(self, expected_request_id: Optional[str] = None, 
                 expected_source: Optional[str] = None,
                 max_age_seconds: int = 3600):
        self.expected_request_id = expected_request_id
        self.expected_source = expected_source
        self.max_age_seconds = max_age_seconds
    
    def validate(self, receipt: ExecutionReceipt) -> ReceiptValidationResult:
        """Validate receipt."""
        result = ReceiptValidationResult(is_valid=True)
        
        # Check correlation
        if self.expected_request_id and receipt.request_id != self.expected_request_id:
            result.add_error(f"Request ID mismatch: expected {self.expected_request_id}, got {receipt.request_id}")
        
        # Check source
        if self.expected_source and receipt.source_node_id != self.expected_source:
            result.add_error(f"Source mismatch: expected {self.expected_source}, got {receipt.source_node_id}")
        
        # Check freshness
        try:
            created = datetime.fromisoformat(receipt.created_at.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - created).total_seconds()
            if age > self.max_age_seconds:
                result.add_error(f"Receipt expired: age {age}s > max {self.max_age_seconds}s")
        except Exception as e:
            result.add_error(f"Could not parse timestamp: {e}")
        
        # Check required fields
        if not receipt.receipt_id:
            result.add_error("Missing receipt_id")
        if not receipt.request_id:
            result.add_error("Missing request_id")
        if not receipt.receipt_type:
            result.add_error("Missing receipt_type")
        if not receipt.source_node_id:
            result.add_error("Missing source_node_id")
        
        return result


# ============================================================================
# COMPLETION CONFIRMATION
# ============================================================================


@dataclass
class CompletionConfirmation:
    """Successful execution completion receipt."""
    
    result_summary: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    
    def create_receipt(self, request_id: str, source_node: str, target_node: str,
                       message: Optional[str] = None) -> ExecutionReceipt:
        """Create completion receipt."""
        return ExecutionReceipt(
            receipt_id=str(uuid.uuid4()),
            request_id=request_id,
            receipt_type=ReceiptType.COMPLETION_CONFIRMED.value,
            source_node_id=source_node,
            target_node_id=target_node,
            envelope_state=ExecutionLifecycleState.COMPLETED.value,
            message=message or "Execution completed successfully",
            details={
                "result_summary": self.result_summary,
                "metrics": self.metrics,
                "artifacts": self.artifacts
            }
        )


# ============================================================================
# FAILURE CONFIRMATION
# ============================================================================


@dataclass
class FailureConfirmation:
    """Execution failure receipt."""
    
    error_code: Optional[str] = None
    error_message: str = "Unknown error"
    error_details: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = False
    
    def create_receipt(self, request_id: str, source_node: str, target_node: str,
                       message: Optional[str] = None) -> ExecutionReceipt:
        """Create failure receipt."""
        return ExecutionReceipt(
            receipt_id=str(uuid.uuid4()),
            request_id=request_id,
            receipt_type=ReceiptType.FAILURE_CONFIRMED.value,
            source_node_id=source_node,
            target_node_id=target_node,
            envelope_state=ExecutionLifecycleState.FAILED.value,
            message=message or f"Execution failed: {self.error_message}",
            details={
                "error_code": self.error_code,
                "error_message": self.error_message,
                "error_details": self.error_details,
                "recoverable": self.recoverable
            }
        )


# ============================================================================
# ROLLBACK ACKNOWLEDGMENT
# ============================================================================


@dataclass
class RollbackAcknowledgment:
    """Rollback acknowledgment receipt."""
    
    rollback_status: str = "pending"  # pending, in_progress, completed, failed
    rollback_reason: Optional[str] = None
    rollback_details: Dict[str, Any] = field(default_factory=dict)
    
    def create_initiation_receipt(self, request_id: str, source_node: str, target_node: str,
                                  reason: str) -> ExecutionReceipt:
        """Create rollback initiation receipt."""
        return ExecutionReceipt(
            receipt_id=str(uuid.uuid4()),
            request_id=request_id,
            receipt_type=ReceiptType.ROLLBACK_ACKNOWLEDGED.value,
            source_node_id=source_node,
            target_node_id=target_node,
            envelope_state=ExecutionLifecycleState.ROLLED_BACK.value,
            message=f"Rollback initiated: {reason}",
            details={
                "rollback_status": "initiated",
                "rollback_reason": reason
            }
        )
    
    def create_completion_receipt(self, request_id: str, source_node: str, target_node: str,
                                  success: bool, details: Optional[Dict] = None) -> ExecutionReceipt:
        """Create rollback completion receipt."""
        receipt_type = ReceiptType.ROLLBACK_COMPLETED.value if success else ReceiptType.FAILURE_CONFIRMED.value
        status = "completed" if success else "failed"
        
        return ExecutionReceipt(
            receipt_id=str(uuid.uuid4()),
            request_id=request_id,
            receipt_type=receipt_type,
            source_node_id=source_node,
            target_node_id=target_node,
            envelope_state=ExecutionLifecycleState.ROLLED_BACK.value,
            message=f"Rollback {status}",
            details={
                "rollback_status": status,
                "rollback_details": details or {}
            }
        )


# ============================================================================
# RECEIPT AUDIT TRACE
# ============================================================================


@dataclass
class ReceiptAuditEvent:
    """Single receipt audit event."""
    
    event_id: str
    event_type: str
    receipt_id: str
    request_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    node_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "receipt_id": self.receipt_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "node_id": self.node_id,
            "details": self.details
        }


class ReceiptAuditTrace:
    """Tracks audit events for receipts."""
    
    def __init__(self, local_node_id: str):
        self.local_node_id = local_node_id
        self._events: List[ReceiptAuditEvent] = []
        self._by_receipt: Dict[str, List[ReceiptAuditEvent]] = {}
        self._by_request: Dict[str, List[ReceiptAuditEvent]] = {}
    
    def log_event(
        self,
        receipt_id: str,
        request_id: str,
        event_type: str,
        details: Optional[Dict] = None,
        node_id: Optional[str] = None
    ) -> ReceiptAuditEvent:
        """Log a receipt audit event."""
        event = ReceiptAuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            receipt_id=receipt_id,
            request_id=request_id,
            node_id=node_id or self.local_node_id,
            details=details or {}
        )
        
        self._events.append(event)
        
        if receipt_id not in self._by_receipt:
            self._by_receipt[receipt_id] = []
        self._by_receipt[receipt_id].append(event)
        
        if request_id not in self._by_request:
            self._by_request[request_id] = []
        self._by_request[request_id].append(event)
        
        return event
    
    def get_events_for_receipt(self, receipt_id: str) -> List[ReceiptAuditEvent]:
        """Get all events for a receipt."""
        return self._by_receipt.get(receipt_id, [])
    
    def get_events_for_request(self, request_id: str) -> List[ReceiptAuditEvent]:
        """Get all events for a request."""
        return self._by_request.get(request_id, [])
    
    def get_trace(self, receipt_id: str) -> List[Dict[str, Any]]:
        """Get full audit trace for a receipt."""
        events = self.get_events_for_receipt(receipt_id)
        return [e.to_dict() for e in sorted(events, key=lambda x: x.timestamp)]
    
    def get_stats(self) -> Dict[str, int]:
        """Get audit statistics."""
        return {
            "total_events": len(self._events),
            "receipts_tracked": len(self._by_receipt),
            "requests_tracked": len(self._by_request)
        }


# ============================================================================
# RECEIPT PROTOCOL
# ============================================================================


class ReceiptProtocol:
    """Protocol handler for receipt lifecycle.
    
    Manages receipt creation, validation, acknowledgment flow.
    No execution logic — protocol/state only.
    """
    
    def __init__(
        self,
        local_node_id: str,
        audit_trace: Optional[ReceiptAuditTrace] = None,
        max_receipt_age_seconds: int = 3600
    ):
        self.local_node_id = local_node_id
        self.audit = audit_trace or ReceiptAuditTrace(local_node_id)
        self.max_receipt_age_seconds = max_receipt_age_seconds
        self._receipts: Dict[str, ExecutionReceipt] = {}
    
    def create_dispatch_received_receipt(
        self,
        request_id: str,
        original_source: str,
        envelope_state: str
    ) -> ExecutionReceipt:
        """Create receipt confirming dispatch received."""
        receipt = ExecutionReceipt(
            receipt_id=str(uuid.uuid4()),
            request_id=request_id,
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id=self.local_node_id,
            target_node_id=original_source,
            envelope_state=envelope_state,
            message="Dispatch received"
        )
        
        self._receipts[receipt.receipt_id] = receipt
        
        self.audit.log_event(
            receipt_id=receipt.receipt_id,
            request_id=request_id,
            event_type=ReceiptEventType.RECEIPT_CREATED.value,
            details={"type": ReceiptType.DISPATCH_RECEIVED.value}
        )
        
        return receipt
    
    def create_execution_accepted_receipt(
        self,
        request_id: str,
        original_source: str
    ) -> ExecutionReceipt:
        """Create receipt accepting execution."""
        receipt = ExecutionReceipt(
            receipt_id=str(uuid.uuid4()),
            request_id=request_id,
            receipt_type=ReceiptType.EXECUTION_ACCEPTED.value,
            source_node_id=self.local_node_id,
            target_node_id=original_source,
            envelope_state=ExecutionLifecycleState.ACKNOWLEDGED.value,
            message="Execution accepted"
        )
        
        self._receipts[receipt.receipt_id] = receipt
        
        self.audit.log_event(
            receipt_id=receipt.receipt_id,
            request_id=request_id,
            event_type=ReceiptEventType.RECEIPT_CREATED.value,
            details={"type": ReceiptType.EXECUTION_ACCEPTED.value}
        )
        
        return receipt
    
    def create_execution_refused_receipt(
        self,
        request_id: str,
        original_source: str,
        reason: str
    ) -> ExecutionReceipt:
        """Create receipt refusing execution."""
        receipt = ExecutionReceipt(
            receipt_id=str(uuid.uuid4()),
            request_id=request_id,
            receipt_type=ReceiptType.EXECUTION_REFUSED.value,
            source_node_id=self.local_node_id,
            target_node_id=original_source,
            envelope_state=ExecutionLifecycleState.REJECTED.value,
            message=f"Execution refused: {reason}"
        )
        
        self._receipts[receipt.receipt_id] = receipt
        
        self.audit.log_event(
            receipt_id=receipt.receipt_id,
            request_id=request_id,
            event_type=ReceiptEventType.RECEIPT_CREATED.value,
            details={"type": ReceiptType.EXECUTION_REFUSED.value, "reason": reason}
        )
        
        return receipt
    
    def send_receipt(self, receipt: ExecutionReceipt) -> None:
        """Mark receipt as sent."""
        receipt.mark_sent()
        self.audit.log_event(
            receipt_id=receipt.receipt_id,
            request_id=receipt.request_id,
            event_type=ReceiptEventType.RECEIPT_SENT.value
        )
    
    def receive_receipt(
        self,
        receipt: ExecutionReceipt,
        expected_request_id: Optional[str] = None,
        expected_source: Optional[str] = None
    ) -> ReceiptValidationResult:
        """Receive and validate receipt."""
        receipt.mark_received()
        self._receipts[receipt.receipt_id] = receipt
        
        self.audit.log_event(
            receipt_id=receipt.receipt_id,
            request_id=receipt.request_id,
            event_type=ReceiptEventType.RECEIPT_RECEIVED.value
        )
        
        # Validate
        validator = ReceiptValidation(
            expected_request_id=expected_request_id,
            expected_source=expected_source,
            max_age_seconds=self.max_receipt_age_seconds
        )
        result = validator.validate(receipt)
        
        receipt.mark_validated(result.is_valid, result.errors if not result.is_valid else None)
        
        if result.is_valid:
            self.audit.log_event(
                receipt_id=receipt.receipt_id,
                request_id=receipt.request_id,
                event_type=ReceiptEventType.RECEIPT_VALIDATED.value
            )
        else:
            self.audit.log_event(
                receipt_id=receipt.receipt_id,
                request_id=receipt.request_id,
                event_type=ReceiptEventType.RECEIPT_REJECTED.value,
                details={"errors": result.errors}
            )
        
        return result
    
    def acknowledge_receipt(self, receipt: ExecutionReceipt) -> None:
        """Acknowledge receipt."""
        receipt.mark_acknowledged()
        self.audit.log_event(
            receipt_id=receipt.receipt_id,
            request_id=receipt.request_id,
            event_type=ReceiptEventType.RECEIPT_ACKNOWLEDGED.value
        )
    
    def get_receipt(self, receipt_id: str) -> Optional[ExecutionReceipt]:
        """Get receipt by ID."""
        return self._receipts.get(receipt_id)
    
    def get_receipts_for_request(self, request_id: str) -> List[ExecutionReceipt]:
        """Get all receipts for a request."""
        return [r for r in self._receipts.values() if r.request_id == request_id]
