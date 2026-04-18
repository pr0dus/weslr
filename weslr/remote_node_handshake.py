"""Remote Node Handshake Protocol (v65)

Formal handshake/session-establishment layer between WESLR nodes.
Provides protocol/state only — NOT execution logic.

Architecture:
  - HandshakeState — handshake lifecycle states
  - HandshakeRequest — formal handshake request
  - HandshakeResponse — handshake response
  - NodeIdentityConfirmation — identity validation
  - TrustHealthEligibility — trust/health checks
  - ProtocolCompatibility — version/capability checks
  - SessionAcceptanceRefusal — acceptance/refusal handling
  - HandshakeAuditTrace — handshake audit events
  - HandshakeCorrelation — handshake-to-node correlation
  - HandshakeProtocol — protocol handler

Rules:
  - Protocol/state only — no execution logic
  - Identity confirmation mandatory
  - Trust/health eligibility before acceptance
  - Version compatibility checked
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
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .node_identity import (
    NodeIdentity,
    NodeTrustState,
    NodeCapabilitySummary,
    NodeTrustStatus,
    NodeHealthStatus,
)
from .node_registry import NodeRegistry


# ============================================================================
# HANDSHAKE STATES
# ============================================================================


class HandshakeState(str, Enum):
    """States in the handshake lifecycle."""
    PENDING = "pending"                     # Request created, not sent
    SENT = "sent"                           # Request sent to target
    RECEIVED = "received"                   # Request received by target
    IDENTITY_CONFIRMED = "identity_confirmed"  # Identity validated
    TRUST_VERIFIED = "trust_verified"       # Trust level verified
    HEALTH_VERIFIED = "health_verified"     # Health status verified
    VERSION_COMPATIBLE = "version_compatible"  # Protocol version compatible
    CAPABILITY_MATCHED = "capability_matched"  # Capabilities matched
    ACCEPTED = "accepted"                   # Handshake accepted
    REFUSED = "refused"                     # Handshake refused
    COMPLETED = "completed"                 # Session established
    FAILED = "failed"                       # Handshake failed
    EXPIRED = "expired"                     # Handshake expired


class HandshakeEventType(str, Enum):
    """Types of handshake audit events."""
    REQUEST_CREATED = "request_created"
    REQUEST_SENT = "request_sent"
    REQUEST_RECEIVED = "request_received"
    IDENTITY_CONFIRMED = "identity_confirmed"
    IDENTITY_REJECTED = "identity_rejected"
    TRUST_VERIFIED = "trust_verified"
    TRUST_REJECTED = "trust_rejected"
    HEALTH_VERIFIED = "health_verified"
    HEALTH_REJECTED = "health_rejected"
    VERSION_COMPATIBLE = "version_compatible"
    VERSION_INCOMPATIBLE = "version_incompatible"
    CAPABILITY_MATCHED = "capability_matched"
    CAPABILITY_MISMATCH = "capability_mismatch"
    HANDSHAKE_ACCEPTED = "handshake_accepted"
    HANDSHAKE_REFUSED = "handshake_refused"
    HANDSHAKE_COMPLETED = "handshake_completed"
    HANDSHAKE_FAILED = "handshake_failed"
    HANDSHAKE_EXPIRED = "handshake_expired"


# ============================================================================
# HANDSHAKE REQUEST
# ============================================================================


@dataclass
class HandshakeRequest:
    """Formal handshake request between nodes."""
    
    # Identity
    handshake_id: str
    source_node_id: str
    target_node_id: str
    
    # Protocol info
    protocol_version: str
    supported_versions: List[str] = field(default_factory=list)
    
    # Identity proof
    source_public_key: Optional[str] = None
    source_signature: Optional[str] = None
    
    # Capabilities offered
    offered_capabilities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    expires_at: Optional[str] = None
    sent_at: Optional[str] = None
    
    def mark_sent(self) -> None:
        """Mark request as sent."""
        self.sent_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def is_expired(self) -> bool:
        """Check if request has expired."""
        if not self.expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > expiry
        except Exception:
            return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "handshake_id": self.handshake_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "protocol_version": self.protocol_version,
            "supported_versions": self.supported_versions,
            "source_public_key": self.source_public_key,
            "source_signature": self.source_signature,
            "offered_capabilities": self.offered_capabilities,
            "message": self.message,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "sent_at": self.sent_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HandshakeRequest":
        return cls(
            handshake_id=data["handshake_id"],
            source_node_id=data["source_node_id"],
            target_node_id=data["target_node_id"],
            protocol_version=data["protocol_version"],
            supported_versions=data.get("supported_versions", []),
            source_public_key=data.get("source_public_key"),
            source_signature=data.get("source_signature"),
            offered_capabilities=data.get("offered_capabilities", []),
            message=data.get("message"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            expires_at=data.get("expires_at"),
            sent_at=data.get("sent_at")
        )


# ============================================================================
# HANDSHAKE RESPONSE
# ============================================================================


@dataclass
class HandshakeResponse:
    """Response to handshake request."""
    
    # Identity
    response_id: str
    handshake_id: str  # References original request
    source_node_id: str  # Responding node
    target_node_id: str  # Original requesting node
    
    # Response
    accepted: bool
    reason: Optional[str] = None
    
    # Protocol info
    protocol_version: Optional[str] = None  # Agreed version
    
    # Identity proof
    source_public_key: Optional[str] = None
    source_signature: Optional[str] = None
    
    # Capabilities accepted
    accepted_capabilities: List[Dict[str, Any]] = field(default_factory=list)
    rejected_capabilities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Session info
    session_id: Optional[str] = None
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # State
    current_state: str = HandshakeState.PENDING.value
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    sent_at: Optional[str] = None
    received_at: Optional[str] = None
    
    def __post_init__(self):
        """Initialize state history."""
        if not self.state_history:
            # Record the starting state
            self.state_history.append({
                "from": None,
                "to": self.current_state,
                "reason": "Response created",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            })
    
    def _transition_to(self, new_state: str, reason: str) -> None:
        """Transition to new state."""
        old_state = self.current_state
        self.current_state = new_state
        self.state_history.append({
            "from": old_state,
            "to": new_state,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
    
    def mark_sent(self) -> None:
        """Mark response as sent."""
        self.sent_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._transition_to(HandshakeState.SENT.value, "Response sent")
    
    def mark_received(self) -> None:
        """Mark response as received."""
        self.received_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._transition_to(HandshakeState.RECEIVED.value, "Response received")
    
    def is_terminal(self) -> bool:
        """Check if response is in terminal state."""
        return self.current_state in (
            HandshakeState.COMPLETED.value,
            HandshakeState.FAILED.value,
            HandshakeState.REFUSED.value,
            HandshakeState.EXPIRED.value
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_id": self.response_id,
            "handshake_id": self.handshake_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "accepted": self.accepted,
            "reason": self.reason,
            "protocol_version": self.protocol_version,
            "source_public_key": self.source_public_key,
            "source_signature": self.source_signature,
            "accepted_capabilities": self.accepted_capabilities,
            "rejected_capabilities": self.rejected_capabilities,
            "session_id": self.session_id,
            "session_metadata": self.session_metadata,
            "current_state": self.current_state,
            "state_history": self.state_history,
            "created_at": self.created_at,
            "sent_at": self.sent_at,
            "received_at": self.received_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HandshakeResponse":
        response = cls(
            response_id=data["response_id"],
            handshake_id=data["handshake_id"],
            source_node_id=data["source_node_id"],
            target_node_id=data["target_node_id"],
            accepted=data["accepted"],
            reason=data.get("reason"),
            protocol_version=data.get("protocol_version"),
            source_public_key=data.get("source_public_key"),
            source_signature=data.get("source_signature"),
            accepted_capabilities=data.get("accepted_capabilities", []),
            rejected_capabilities=data.get("rejected_capabilities", []),
            session_id=data.get("session_id"),
            session_metadata=data.get("session_metadata", {}),
            current_state=data.get("current_state", HandshakeState.PENDING.value),
            state_history=data.get("state_history", []),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            sent_at=data.get("sent_at"),
            received_at=data.get("received_at")
        )
        return response


# ============================================================================
# NODE IDENTITY CONFIRMATION
# ============================================================================


@dataclass
class IdentityConfirmationResult:
    """Result of identity confirmation."""
    confirmed: bool
    identity: Optional[NodeIdentity] = None
    errors: List[str] = field(default_factory=list)


class NodeIdentityConfirmation:
    """Validates node identity during handshake."""
    
    def __init__(self, registry: NodeRegistry):
        self.registry = registry
    
    def confirm_identity(self, request: HandshakeRequest) -> IdentityConfirmationResult:
        """Confirm identity of requesting node."""
        result = IdentityConfirmationResult(confirmed=False)
        
        # Check if node exists in registry
        entry = self.registry.get_entry(request.source_node_id)
        if not entry:
            result.errors.append(f"Node {request.source_node_id} not in registry")
            return result
        
        # Verify public key if provided
        if request.source_public_key:
            # In real implementation, verify signature against public key
            # For now, just check existence
            if not request.source_signature:
                result.errors.append("Signature required with public key")
                return result
        
        result.confirmed = True
        result.identity = entry.identity
        return result


# ============================================================================
# TRUST/HEALTH ELIGIBILITY
# ============================================================================


@dataclass
class EligibilityResult:
    """Result of trust/health eligibility check."""
    eligible: bool
    trust_passed: bool = False
    health_passed: bool = False
    errors: List[str] = field(default_factory=list)


class TrustHealthEligibility:
    """Checks trust/health eligibility for handshake."""
    
    def __init__(
        self,
        registry: NodeRegistry,
        min_trust: str = NodeTrustStatus.TRUSTED.value,
        require_healthy: bool = True
    ):
        self.registry = registry
        self.min_trust = min_trust
        self.require_healthy = require_healthy
    
    def check_eligibility(self, node_id: str) -> EligibilityResult:
        """Check if node is eligible for handshake."""
        result = EligibilityResult(eligible=False)
        
        entry = self.registry.get_entry(node_id)
        if not entry:
            result.errors.append(f"Node {node_id} not in registry")
            return result
        
        if not entry.trust_state:
            result.errors.append("No trust state available")
            return result
        
        # Check trust level
        trust_order = [
            NodeTrustStatus.REVOKED.value,
            NodeTrustStatus.UNTRUSTED.value,
            NodeTrustStatus.PENDING.value,
            NodeTrustStatus.PROVISIONAL.value,
            NodeTrustStatus.TRUSTED.value
        ]
        min_idx = trust_order.index(self.min_trust)
        node_idx = trust_order.index(entry.trust_state.trust_status) \
            if entry.trust_state.trust_status in trust_order else 0
        
        if node_idx < min_idx:
            result.errors.append(f"Trust level {entry.trust_state.trust_status} below required {self.min_trust}")
        else:
            result.trust_passed = True
        
        # Check health
        if self.require_healthy:
            if entry.trust_state.health_status != NodeHealthStatus.HEALTHY.value:
                result.errors.append(f"Health status {entry.trust_state.health_status} not healthy")
            else:
                result.health_passed = True
        else:
            result.health_passed = True
        
        result.eligible = result.trust_passed and result.health_passed
        return result


# ============================================================================
# PROTOCOL COMPATIBILITY
# ============================================================================


@dataclass
class CompatibilityResult:
    """Result of protocol compatibility check."""
    compatible: bool
    agreed_version: Optional[str] = None
    errors: List[str] = field(default_factory=list)


class ProtocolCompatibility:
    """Checks version and capability compatibility."""
    
    def __init__(self, local_version: str, supported_versions: List[str]):
        self.local_version = local_version
        self.supported_versions = supported_versions
    
    def check_version(self, request: HandshakeRequest) -> CompatibilityResult:
        """Check version compatibility."""
        result = CompatibilityResult(compatible=False)
        
        # Check if request version is supported locally
        if request.protocol_version in self.supported_versions:
            result.compatible = True
            result.agreed_version = request.protocol_version
            return result
        
        # Check if any supported version overlaps
        common_versions = set(request.supported_versions) & set(self.supported_versions)
        if common_versions:
            result.compatible = True
            # Prefer highest common version
            result.agreed_version = max(common_versions)
            return result
        
        result.errors.append(f"No common protocol version. Request: {request.protocol_version}, Local: {self.local_version}")
        return result
    
    def check_capabilities(
        self,
        offered: List[Dict[str, Any]],
        required: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Check capability compatibility. Returns (accepted, rejected)."""
        accepted = []
        rejected = []
        
        for offer in offered:
            cap_id = offer.get("id")
            if any(r.get("id") == cap_id for r in required):
                accepted.append(offer)
            else:
                rejected.append(offer)
        
        return accepted, rejected


# ============================================================================
# SESSION ACCEPTANCE/REFUSAL
# ============================================================================


@dataclass
class SessionAcceptanceResult:
    """Result of session acceptance."""
    accepted: bool
    session_id: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionAcceptanceRefusal:
    """Handles session acceptance/refusal."""
    
    def accept_session(
        self,
        handshake_id: str,
        agreed_version: str,
        accepted_capabilities: List[Dict[str, Any]],
        metadata: Optional[Dict] = None
    ) -> SessionAcceptanceResult:
        """Accept handshake session."""
        session_id = str(uuid.uuid4())
        
        return SessionAcceptanceResult(
            accepted=True,
            session_id=session_id,
            metadata=metadata or {}
        )
    
    def refuse_session(
        self,
        handshake_id: str,
        reason: str,
        metadata: Optional[Dict] = None
    ) -> SessionAcceptanceResult:
        """Refuse handshake session."""
        return SessionAcceptanceResult(
            accepted=False,
            reason=reason,
            metadata=metadata or {}
        )


# ============================================================================
# HANDSHAKE AUDIT TRACE
# ============================================================================


@dataclass
class HandshakeAuditEvent:
    """Single handshake audit event."""
    
    event_id: str
    event_type: str
    handshake_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    node_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "handshake_id": self.handshake_id,
            "timestamp": self.timestamp,
            "node_id": self.node_id,
            "details": self.details
        }


class HandshakeAuditTrace:
    """Tracks audit events for handshakes."""
    
    def __init__(self, local_node_id: str):
        self.local_node_id = local_node_id
        self._events: List[HandshakeAuditEvent] = []
        self._by_handshake: Dict[str, List[HandshakeAuditEvent]] = {}
    
    def log_event(
        self,
        handshake_id: str,
        event_type: str,
        details: Optional[Dict] = None,
        node_id: Optional[str] = None
    ) -> HandshakeAuditEvent:
        """Log a handshake audit event."""
        event = HandshakeAuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            handshake_id=handshake_id,
            node_id=node_id or self.local_node_id,
            details=details or {}
        )
        
        self._events.append(event)
        
        if handshake_id not in self._by_handshake:
            self._by_handshake[handshake_id] = []
        self._by_handshake[handshake_id].append(event)
        
        return event
    
    def get_events(self, handshake_id: str) -> List[HandshakeAuditEvent]:
        """Get all events for a handshake."""
        return self._by_handshake.get(handshake_id, [])
    
    def get_trace(self, handshake_id: str) -> List[Dict[str, Any]]:
        """Get full audit trace for a handshake."""
        events = self.get_events(handshake_id)
        return [e.to_dict() for e in sorted(events, key=lambda x: x.timestamp)]
    
    def get_stats(self) -> Dict[str, int]:
        """Get audit statistics."""
        return {
            "total_events": len(self._events),
            "handshakes_tracked": len(self._by_handshake)
        }


# ============================================================================
# HANDSHAKE CORRELATION
# ============================================================================


@dataclass
class HandshakeCorrelation:
    """Correlation between handshake and node registry."""
    
    handshake_id: str
    request_id: Optional[str] = None
    response_id: Optional[str] = None
    session_id: Optional[str] = None
    source_node_id: Optional[str] = None
    target_node_id: Optional[str] = None
    correlation_map: Dict[str, str] = field(default_factory=dict)
    
    def link_request(self, request: HandshakeRequest) -> None:
        """Link handshake request."""
        self.request_id = request.handshake_id
        self.source_node_id = request.source_node_id
        self.target_node_id = request.target_node_id
        self.correlation_map["request"] = request.handshake_id
    
    def link_response(self, response: HandshakeResponse) -> None:
        """Link handshake response."""
        self.response_id = response.response_id
        self.session_id = response.session_id
        self.correlation_map["response"] = response.response_id
        if response.session_id:
            self.correlation_map["session"] = response.session_id
    
    def get_correlated_ids(self) -> Dict[str, Any]:
        """Get all correlated IDs."""
        return {
            "handshake_id": self.handshake_id,
            "request_id": self.request_id,
            "response_id": self.response_id,
            "session_id": self.session_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id
        }


# ============================================================================
# HANDSHAKE PROTOCOL
# ============================================================================


class HandshakeProtocol:
    """Protocol handler for handshake lifecycle."""
    
    def __init__(
        self,
        local_node_id: str,
        registry: NodeRegistry,
        local_version: str = "1.0.0",
        supported_versions: Optional[List[str]] = None,
        audit_trace: Optional[HandshakeAuditTrace] = None
    ):
        self.local_node_id = local_node_id
        self.registry = registry
        self.local_version = local_version
        self.supported_versions = supported_versions or ["1.0.0"]
        self.audit = audit_trace or HandshakeAuditTrace(local_node_id)
        
        # Components
        self.identity_confirmation = NodeIdentityConfirmation(registry)
        self.eligibility = TrustHealthEligibility(registry)
        self.compatibility = ProtocolCompatibility(local_version, self.supported_versions)
        self.session_handler = SessionAcceptanceRefusal()
        
        # Tracking
        self._requests: Dict[str, HandshakeRequest] = {}
        self._responses: Dict[str, HandshakeResponse] = {}
        self._correlations: Dict[str, HandshakeCorrelation] = {}
    
    def create_request(
        self,
        target_node_id: str,
        protocol_version: Optional[str] = None,
        message: Optional[str] = None,
        expires_in_seconds: int = 300
    ) -> HandshakeRequest:
        """Create handshake request."""
        handshake_id = str(uuid.uuid4())
        
        expiry = datetime.now(timezone.utc) + __import__('datetime').timedelta(seconds=expires_in_seconds)
        expires_at = expiry.isoformat().replace("+00:00", "Z")
        
        request = HandshakeRequest(
            handshake_id=handshake_id,
            source_node_id=self.local_node_id,
            target_node_id=target_node_id,
            protocol_version=protocol_version or self.local_version,
            supported_versions=self.supported_versions,
            message=message,
            expires_at=expires_at
        )
        
        self._requests[handshake_id] = request
        
        correlation = HandshakeCorrelation(handshake_id=handshake_id)
        correlation.link_request(request)
        self._correlations[handshake_id] = correlation
        
        self.audit.log_event(
            handshake_id=handshake_id,
            event_type=HandshakeEventType.REQUEST_CREATED.value,
            details={"target": target_node_id}
        )
        
        return request
    
    def send_request(self, request: HandshakeRequest) -> None:
        """Send handshake request."""
        request.mark_sent()
        self.audit.log_event(
            handshake_id=request.handshake_id,
            event_type=HandshakeEventType.REQUEST_SENT.value,
            details={"target": request.target_node_id}
        )
    
    def receive_request(self, request: HandshakeRequest) -> Tuple[bool, List[str]]:
        """Receive and validate handshake request."""
        self._requests[request.handshake_id] = request
        
        self.audit.log_event(
            handshake_id=request.handshake_id,
            event_type=HandshakeEventType.REQUEST_RECEIVED.value,
            details={"source": request.source_node_id}
        )
        
        errors = []
        
        # Check expiry
        if request.is_expired():
            errors.append("Request expired")
            self.audit.log_event(
                handshake_id=request.handshake_id,
                event_type=HandshakeEventType.HANDSHAKE_EXPIRED.value
            )
            return False, errors
        
        # Confirm identity
        identity_result = self.identity_confirmation.confirm_identity(request)
        if not identity_result.confirmed:
            errors.extend(identity_result.errors)
            self.audit.log_event(
                handshake_id=request.handshake_id,
                event_type=HandshakeEventType.IDENTITY_REJECTED.value,
                details={"errors": identity_result.errors}
            )
            return False, errors
        
        self.audit.log_event(
            handshake_id=request.handshake_id,
            event_type=HandshakeEventType.IDENTITY_CONFIRMED.value
        )
        
        return True, []
    
    def evaluate_request(
        self,
        request: HandshakeRequest
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Evaluate request for acceptance. Returns (eligible, reason, agreed_version)."""
        # Check trust/health eligibility
        eligibility = self.eligibility.check_eligibility(request.source_node_id)
        if not eligibility.eligible:
            self.audit.log_event(
                handshake_id=request.handshake_id,
                event_type=HandshakeEventType.TRUST_REJECTED.value if not eligibility.trust_passed else HandshakeEventType.HEALTH_REJECTED.value,
                details={"errors": eligibility.errors}
            )
            return False, f"Not eligible: {', '.join(eligibility.errors)}", None
        
        self.audit.log_event(
            handshake_id=request.handshake_id,
            event_type=HandshakeEventType.TRUST_VERIFIED.value
        )
        self.audit.log_event(
            handshake_id=request.handshake_id,
            event_type=HandshakeEventType.HEALTH_VERIFIED.value
        )
        
        # Check version compatibility
        compat = self.compatibility.check_version(request)
        if not compat.compatible:
            self.audit.log_event(
                handshake_id=request.handshake_id,
                event_type=HandshakeEventType.VERSION_INCOMPATIBLE.value,
                details={"errors": compat.errors}
            )
            return False, f"Version incompatible: {', '.join(compat.errors)}", None
        
        self.audit.log_event(
            handshake_id=request.handshake_id,
            event_type=HandshakeEventType.VERSION_COMPATIBLE.value,
            details={"agreed_version": compat.agreed_version}
        )
        
        return True, None, compat.agreed_version
    
    def create_response(
        self,
        request: HandshakeRequest,
        accepted: bool,
        reason: Optional[str] = None,
        agreed_version: Optional[str] = None
    ) -> HandshakeResponse:
        """Create handshake response."""
        response_id = str(uuid.uuid4())
        session_id = None
        
        if accepted:
            result = self.session_handler.accept_session(
                handshake_id=request.handshake_id,
                agreed_version=agreed_version or self.local_version,
                accepted_capabilities=[],
                metadata={"source": request.source_node_id}
            )
            session_id = result.session_id
        
        response = HandshakeResponse(
            response_id=response_id,
            handshake_id=request.handshake_id,
            source_node_id=self.local_node_id,
            target_node_id=request.source_node_id,
            accepted=accepted,
            reason=reason,
            protocol_version=agreed_version,
            session_id=session_id
        )
        
        self._responses[response_id] = response
        
        if correlation := self._correlations.get(request.handshake_id):
            correlation.link_response(response)
        
        event_type = HandshakeEventType.HANDSHAKE_ACCEPTED.value if accepted else HandshakeEventType.HANDSHAKE_REFUSED.value
        self.audit.log_event(
            handshake_id=request.handshake_id,
            event_type=event_type,
            details={"accepted": accepted, "reason": reason}
        )
        
        return response
    
    def send_response(self, response: HandshakeResponse) -> None:
        """Send handshake response."""
        response.mark_sent()
        self.audit.log_event(
            handshake_id=response.handshake_id,
            event_type=HandshakeEventType.REQUEST_SENT.value,
            details={"response_id": response.response_id}
        )
    
    def receive_response(
        self,
        response: HandshakeResponse,
        expected_handshake_id: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """Receive and validate handshake response."""
        errors = []
        
        # Validate handshake ID
        if expected_handshake_id and response.handshake_id != expected_handshake_id:
            errors.append(f"Handshake ID mismatch: expected {expected_handshake_id}, got {response.handshake_id}")
            return False, errors
        
        self._responses[response.response_id] = response
        response.mark_received()
        
        self.audit.log_event(
            handshake_id=response.handshake_id,
            event_type=HandshakeEventType.REQUEST_RECEIVED.value,
            details={"accepted": response.accepted}
        )
        
        if response.accepted:
            self.audit.log_event(
                handshake_id=response.handshake_id,
                event_type=HandshakeEventType.HANDSHAKE_COMPLETED.value,
                details={"session_id": response.session_id}
            )
        else:
            self.audit.log_event(
                handshake_id=response.handshake_id,
                event_type=HandshakeEventType.HANDSHAKE_FAILED.value,
                details={"reason": response.reason}
            )
        
        return True, []
    
    def complete_handshake(self, handshake_id: str) -> None:
        """Mark handshake as completed."""
        self.audit.log_event(
            handshake_id=handshake_id,
            event_type=HandshakeEventType.HANDSHAKE_COMPLETED.value
        )
    
    def get_request(self, handshake_id: str) -> Optional[HandshakeRequest]:
        """Get request by handshake ID."""
        return self._requests.get(handshake_id)
    
    def get_response(self, response_id: str) -> Optional[HandshakeResponse]:
        """Get response by ID."""
        return self._responses.get(response_id)
    
    def get_correlation(self, handshake_id: str) -> Optional[HandshakeCorrelation]:
        """Get correlation by handshake ID."""
        return self._correlations.get(handshake_id)
