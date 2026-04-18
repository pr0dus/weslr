# escalation.py - WESLR v41: Escalation / Human Handoff Layer
# Creates a governed escalation layer so WESLR can explicitly hand off blocked,
# restricted, high-risk, or specialist-required situations to the appropriate human role.
# Additive only, transparent, reversible, role-based, non-manipulative.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class EscalationTrigger(str, Enum):
    """Triggers that cause escalation."""
    BLOCKED_BY_CAPABILITY = "blocked_by_capability"  # Capability explicitly blocked
    RESTRICTED_BY_CAPABILITY = "restricted_by_capability"  # Capability restricted
    REQUIRES_APPROVAL = "requires_approval"  # Approval-gated capability
    HIGH_RISK = "high_risk"  # Action exceeds safety threshold
    NO_EXPLANATION = "no_explanation"  # Can't generate sufficient explanation
    SPECIALIST_REQUIRED = "specialist_required"  # Needs domain expertise
    UNRELIABLE_CONNECTION = "unreliable_connection"  # Network issues during critical operation
    DEGRADED_MODE = "degraded_mode"  # Operating in degraded mode with limited capabilities
    OTHER = "other"


class EscalationReason(str, Enum):
    """Human-readable escalation reasons."""
    CAPABILITY_PROHIBITED = "capability_prohibited"
    CAPABILITY_RESTRICTED = "capability_restricted"
    CAPABILITY_APPROVAL_NEEDED = "capability_approval_needed"
    SAFETY_THRESHOLD_EXCEEDED = "safety_threshold_exceeded"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    LACKS_SPECIALIST = "lacks_specialist"
    NETWORK_FAILURE = "network_failure"
    DEGRADED_OPERATIONS = "degraded_operations"
    UNKNOWN = "unknown"


class RequiredHumanRole(str, Enum):
    """Required human role for handoff."""
    OPERATOR = "operator"  # General operator
    ADMINISTRATOR = "administrator"  # Administrative approval
    DOMAIN_EXPERT = "domain_expert"  # Domain specialist
    OPERATIONS_SPECIALIST = "operations_specialist"  # Operations team
    SECURITY_SPECIALIST = "security_specialist"  # Security review
    AUDITOR = "auditor"  # Audit trail
    EMERGENCY_CONTACT = "emergency_contact"  # Emergency situation
    LEGAL_REVIEWER = "legal_reviewer"  # Legal compliance
    CUSTOMER = "customer"  # Direct customer approval
    TECHNICAL_SUPPORT = "technical_support"  # Technical help


class UrgencyLevel(str, Enum):
    """Urgency level for handoff."""
    LOW = "low"  # Can wait for next routine check
    NORMAL = "normal"  # Review needed soon
    HIGH = "high"  # Review needed now
    CRITICAL = "critical"  # Immediate review required


class HandoffStatus(str, Enum):
    """Status of a handoff."""
    PENDING = "pending"  # Awaiting human response
    AWAITING_REVIEW = "awaiting_review"  # In review queue
    REVIEWED = "reviewed"  # Human has reviewed
    APPROVED = "approved"  # Human approved
    DENIED = "denied"  # Human denied
    ESCALATED = "escalated"  # Escalated to higher authority
    TIMEOUT = "timeout"  # Handoff timed out
    CANCELLED = "cancelled"  # Manually cancelled


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class HandoffPackage:
    """Complete package for human handoff."""
    
    package_id: str
    context_id: str  # Reference to original context
    capability: Optional[str] = None  # What capability triggered
    action: Optional[str] = None  # What action was attempted
    reason: Optional[str] = None  # Why handoff is needed
    
    # Risk assessment
    risk_level: float = 0.0  # 0.0-1.0
    confidence: float = 0.0  # 0.0-1.0
    safety_impact: Optional[str] = None
    
    # Context for human
    background: Optional[str] = None  # Background information
    options: List[str] = field(default_factory=list)  # What human can do
    recommended_action: Optional[str] = None  # What agent recommends
    alternative_actions: List[str] = field(default_factory=list)  # Other options
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "context_id": self.context_id,
            "capability": self.capability,
            "action": self.action,
            "reason": self.reason,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "safety_impact": self.safety_impact,
            "background": self.background,
            "options": self.options,
            "recommended_action": self.recommended_action,
            "alternative_actions": self.alternative_actions,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HandoffPackage:
        data["options"] = data.get("options", [])
        data["alternative_actions"] = data.get("alternative_actions", [])
        return cls(**data)


@dataclass
class EscalationRequest:
    """Escalation request with all required information."""
    
    escalation_id: str
    trigger: str  # EscalationTrigger.value
    reason: str  # EscalationReason.value
    
    # Human requirements
    required_role: str = RequiredHumanRole.OPERATOR.value
    urgency: str = UrgencyLevel.NORMAL.value
    handoff_package: Optional[Dict[str, Any]] = None
    
    # Context
    context_id: Optional[str] = None
    capability_boundary_id: Optional[str] = None
    
    # Status
    status: str = HandoffStatus.PENDING.value
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    # Timing
    timeout_ms: int = 300000  # Default 5 minutes
    deadline_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "escalation_id": self.escalation_id,
            "trigger": self.trigger,
            "reason": self.reason,
            "required_role": self.required_role,
            "urgency": self.urgency,
            "handoff_package": self.handoff_package,
            "context_id": self.context_id,
            "capability_boundary_id": self.capability_boundary_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
            "timeout_ms": self.timeout_ms,
            "deadline_at": self.deadline_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EscalationRequest:
        data["handoff_package"] = data.get("handoff_package")
        return cls(**data)
    
    def update(self, **kwargs) -> EscalationRequest:
        """Update escalation and refresh timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self
    
    def set_status(self, status: str) -> EscalationRequest:
        """Set status and update timestamp."""
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self


# ============================================================================
# ESCALATION HUMAN ROLES
# ============================================================================


def get_escalation_human_roles() -> Dict[str, Dict[str, Any]]:
    """Get predefined human roles for escalation handoff.
    
    Returns a registry of human roles with their capabilities and response expectations.
    """
    return {
        RequiredHumanRole.OPERATOR.value: {
            "name": "Operator",
            "description": "General operator with system access",
            "response_time_hours": 24,
            "capabilities": ["approval", "rejection", "escalation"],
            "notifications": ["email", "sms"],
        },
        RequiredHumanRole.ADMINISTRATOR.value: {
            "name": "Administrator",
            "description": "System administrator with full access",
            "response_time_hours": 12,
            "capabilities": ["full_access", "configuration", "approval"],
            "notifications": ["email", "slack"],
        },
        RequiredHumanRole.DOMAIN_EXPERT.value: {
            "name": "Domain Expert",
            "description": "Expert in specific domain (medicine, aerospace, etc.)",
            "response_time_hours": 48,
            "capabilities": ["expert_review", "guidance", "approval"],
            "notifications": ["email"],
        },
        RequiredHumanRole.OPERATIONS_SPECIALIST.value: {
            "name": "Operations Specialist",
            "description": "Operations team member for procedural review",
            "response_time_hours": 8,
            "capabilities": ["procedure_review", "approval", "delegation"],
            "notifications": ["email", "pager"],
        },
        RequiredHumanRole.SECURITY_SPECIALIST.value: {
            "name": "Security Specialist",
            "description": "Security team member for security review",
            "response_time_hours": 4,
            "capabilities": ["security_review", "approval", "blocking"],
            "notifications": ["pager", "slack"],
        },
        RequiredHumanRole.AUDITOR.value: {
            "name": "Auditor",
            "description": "Audit team member for compliance review",
            "response_time_hours": 72,
            "capabilities": ["audit", "compliance_review"],
            "notifications": ["email"],
        },
        RequiredHumanRole.EMERGENCY_CONTACT.value: {
            "name": "Emergency Contact",
            "description": "Emergency contact for critical situations",
            "response_time_hours": 1,
            "capabilities": ["emergency_action", "escalation"],
            "notifications": ["pager", "phone"],
        },
        RequiredHumanRole.LEGAL_REVIEWER.value: {
            "name": "Legal Reviewer",
            "description": "Legal team member for compliance review",
            "response_time_hours": 168,  # 1 week
            "capabilities": ["legal_review", "compliance"],
            "notifications": ["email"],
        },
        RequiredHumanRole.CUSTOMER.value: {
            "name": "Customer",
            "description": "Direct customer approval",
            "response_time_hours": 24,
            "capabilities": ["approval", "rejection", "modification"],
            "notifications": ["email", "sms"],
        },
        RequiredHumanRole.TECHNICAL_SUPPORT.value: {
            "name": "Technical Support",
            "description": "Technical support for operational help",
            "response_time_hours": 4,
            "capabilities": ["technical_help", "troubleshooting"],
            "notifications": ["email", "chat"],
        },
    }


# ============================================================================
# ESCALATION ENGINE
# ============================================================================


class EscalationEngine:
    """Engine for managing escalations and human handoffs.
    
    Provides transparent, reversible escalation handling.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize escalation engine."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/escalation/"
        self.escalations: Dict[str, EscalationRequest] = {}
        self.handoffs: Dict[str, HandoffPackage] = {}
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def create_handoff(
        self,
        context_id: str,
        capability: str,
        action: str,
        reason: str,
        risk_level: float = 0.5,
        confidence: float = 0.0,
        background: Optional[str] = None,
        recommended_action: Optional[str] = None,
        options: List[str] = None,
        alternative_actions: List[str] = None,
        author: Optional[str] = None,
    ) -> HandoffPackage:
        """Create a handoff package for human review."""
        import uuid
        package_id = f"handoff_{uuid.uuid4().hex[:8]}"
        
        package = HandoffPackage(
            package_id=package_id,
            context_id=context_id,
            capability=capability,
            action=action,
            reason=reason,
            risk_level=risk_level,
            confidence=confidence,
            background=background,
            recommended_action=recommended_action,
            options=options or [],
            alternative_actions=alternative_actions or [],
            author=author,
        )
        
        self.handoffs[package_id] = package
        return package
    
    def create_escalation(
        self,
        trigger: str,
        reason: str,
        required_role: str = RequiredHumanRole.OPERATOR.value,
        urgency: str = UrgencyLevel.NORMAL.value,
        handoff_package_id: Optional[str] = None,
        context_id: Optional[str] = None,
        capability_boundary_id: Optional[str] = None,
        author: Optional[str] = None,
    ) -> EscalationRequest:
        """Create an escalation request."""
        import uuid
        escalation_id = f"escalation_{uuid.uuid4().hex[:8]}"
        
        package = None
        if handoff_package_id:
            package = self.handoffs.get(handoff_package_id)
        
        escalation = EscalationRequest(
            escalation_id=escalation_id,
            trigger=trigger,
            reason=reason,
            required_role=required_role,
            urgency=urgency,
            handoff_package=package.to_dict() if package else None,
            context_id=context_id,
            capability_boundary_id=capability_boundary_id,
            author=author,
        )
        
        self.escalations[escalation_id] = escalation
        return escalation
    
    def get_escalation(self, escalation_id: str) -> Optional[EscalationRequest]:
        """Get an escalation by ID."""
        return self.escalations.get(escalation_id)
    
    def get_handoff(self, package_id: str) -> Optional[HandoffPackage]:
        """Get a handoff package by ID."""
        return self.handoffs.get(package_id)
    
    def create_escalation_from_capability_check(
        self,
        capability_check_result: Dict[str, Any],
        context_id: str,
        author: Optional[str] = None,
    ) -> Optional[EscalationRequest]:
        """Create an escalation from a capability boundary check result.
        
        Returns None if capability was permitted.
        """
        if capability_check_result.get("permitted", False):
            return None
        
        trigger = EscalationTrigger.BLOCKED_BY_CAPABILITY.value
        reason = EscalationReason.CAPABILITY_PROHIBITED.value
        required_role = RequiredHumanRole.OPERATOR.value
        urgency = UrgencyLevel.NORMAL.value
        
        reason_text = capability_check_result.get("reason", "Unknown reason")
        if "prohibited" in reason_text.lower():
            trigger = EscalationTrigger.BLOCKED_BY_CAPABILITY.value
            reason = EscalationReason.CAPABILITY_PROHIBITED.value
            required_role = RequiredHumanRole.OPERATOR.value
        elif "restricted" in reason_text.lower():
            trigger = EscalationTrigger.RESTRICTED_BY_CAPABILITY.value
            reason = EscalationReason.CAPABILITY_RESTRICTED.value
            required_role = RequiredHumanRole.OPERATOR.value
        elif "requires approval" in reason_text.lower():
            trigger = EscalationTrigger.REQUIRES_APPROVAL.value
            reason = EscalationReason.CAPABILITY_APPROVAL_NEEDED.value
            required_role = RequiredHumanRole.OPERATOR.value
        elif "safety" in reason_text.lower():
            trigger = EscalationTrigger.HIGH_RISK.value
            reason = EscalationReason.SAFETY_THRESHOLD_EXCEEDED.value
            required_role = RequiredHumanRole.OPERATIONS_SPECIALIST.value
        elif "specialist" in reason_text.lower():
            trigger = EscalationTrigger.SPECIALIST_REQUIRED.value
            reason = EscalationReason.LACKS_SPECIALIST.value
            required_role = RequiredHumanRole.DOMAIN_EXPERT.value
        elif "urgency" in reason_text.lower():
            urgency = UrgencyLevel.HIGH.value
        
        # Create handoff package
        handoff = self.create_handoff(
            context_id=context_id,
            capability=capability_check_result.get("capability", "unknown"),
            action="attempted",
            reason=reason_text,
            risk_level=0.7,
            confidence=0.0,
            author=author,
        )
        
        # Create escalation
        escalation = self.create_escalation(
            trigger=trigger,
            reason=reason,
            required_role=required_role,
            urgency=urgency,
            handoff_package_id=handoff.package_id,
            context_id=context_id,
            author=author,
        )
        
        return escalation
    
    def approve_escalation(
        self,
        escalation_id: str,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> EscalationRequest:
        """Approve an escalation."""
        escalation = self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation not found: {escalation_id}")
        
        escalation.set_status(HandoffStatus.APPROVED.value)
        if notes and escalation.handoff_package:
            escalation.handoff_package["approved_notes"] = notes
        return escalation
    
    def deny_escalation(
        self,
        escalation_id: str,
        denied_by: str,
        notes: Optional[str] = None,
    ) -> EscalationRequest:
        """Deny an escalation."""
        escalation = self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation not found: {escalation_id}")
        
        escalation.set_status(HandoffStatus.DENIED.value)
        if notes and escalation.handoff_package:
            escalation.handoff_package["denied_notes"] = notes
        return escalation
    
    def get_pending_escalations(self) -> List[EscalationRequest]:
        """Get all pending escalations."""
        return [
            e for e in self.escalations.values()
            if e.status in [HandoffStatus.PENDING.value, HandoffStatus.AWAITING_REVIEW.value]
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "escalation_count": len(self.escalations),
            "handoff_count": len(self.handoffs),
            "pending_count": len(self.get_pending_escalations()),
            "escalations": {k: v.to_dict() for k, v in self.escalations.items()},
            "handoffs": {k: v.to_dict() for k, v in self.handoffs.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_capability_boundary(
    capability_dict: Dict[str, Any],
    escalation_engine: EscalationEngine = None,
    context_id: str = None,
) -> Dict[str, Any]:
    """Add escalation context to capability boundary check.
    
    This is purely additive — no migration required.
    
    v41: Escalation layer provides handoff packages when capability checks fail.
    """
    if "escalation_context" not in capability_dict:
        capability_dict["escalation_context"] = None
    
    if escalation_engine and context_id:
        try:
            pending = escalation_engine.get_pending_escalations()
            capability_dict["escalation_context"] = {
                "pending_count": len(pending),
                "requires_review": len(pending) > 0,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return capability_dict


def integrate_with_safety_contract(
    safety_dict: Dict[str, Any],
    escalation_engine: EscalationEngine = None,
    context_id: str = None,
) -> Dict[str, Any]:
    """Add escalation context to safety contract.
    
    This is purely additive — no migration required.
    
    v41: Escalation layer flags safety-related handoffs.
    """
    if "escalation_context" not in safety_dict:
        safety_dict["escalation_context"] = None
    
    if escalation_engine and context_id:
        try:
            pending = escalation_engine.get_pending_escalations()
            safety_dict["escalation_context"] = {
                "pending_count": len(pending),
                "requires_human_review": len(pending) > 0,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return safety_dict


def integrate_with_proof_gate(
    proof_dict: Dict[str, Any],
    escalation_engine: EscalationEngine = None,
    context_id: str = None,
) -> Dict[str, Any]:
    """Add escalation context to proof gate.
    
    This is purely additive — no migration required.
    
    v41: Escalation layer indicates proof requires human review.
    """
    if "escalation_context" not in proof_dict:
        proof_dict["escalation_context"] = None
    
    if escalation_engine and context_id:
        try:
            pending = escalation_engine.get_pending_escalations()
            proof_dict["escalation_context"] = {
                "pending_count": len(pending),
                "requires_approval": len(pending) > 0,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return proof_dict


def integrate_with_governance_surface(
    governance_dict: Dict[str, Any],
    escalation_engine: EscalationEngine = None,
    context_id: str = None,
) -> Dict[str, Any]:
    """Add escalation context to governance surface.
    
    This is purely additive — no migration required.
    
    v41: Escalation layer surfaces handoff requirements clearly to operators.
    """
    if "escalation_context" not in governance_dict:
        governance_dict["escalation_context"] = None
    
    if escalation_engine and context_id:
        try:
            pending = escalation_engine.get_pending_escalations()
            governance_dict["escalation_context"] = {
                "pending_count": len(pending),
                "requires_review": len(pending) > 0,
                "urgency": pending[0].urgency if pending else UrgencyLevel.LOW.value,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return governance_dict
