"""External Action Safety Contract Layer (v23)

Formal safety contract for recommendations and any future external actions.
Defines approval requirements, safety levels, and execution permissions.

Architecture:
  - ActionType enum — types of external actions
  - SafetyLevel enum — risk tolerance levels
  - ApprovalRequirement enum — required approval types
  - ExecutionPermission — permission status for actions
  - SafetyContract — full safety contract for a proposal/action
  - SafetyEngine — assessment and validation

Rules:
  - Additive only (no breaking changes)
  - Operator-first (status visible to operators)
  - Reversible (single file removal)
  - No autonomous external execution (all require operator approval)
  - No repo drift (local to WESLR scope)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class ActionType(str, Enum):
    """Types of external actions that may be recommended or executed."""
    # Informational (read-only)
    READ_DATA = "read_data"
    READ_FILES = "read_files"
    READ_MEMORY = "read_memory"
    ANALYZE = "analyze"
    
    # Configuration changes
    CONFIGURE = "configure"
    UPDATE_CONFIG = "update_config"
    DELETE_CONFIG = "delete_config"
    
    # External system interaction
    API_CALL = "api_call"
    HTTP_REQUEST = "http_request"
    DATABASE_WRITE = "database_write"
    
    # System modification
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    SYSTEM_COMMAND = "system_command"
    
    # Actuation (high-risk)
    ACTUATE = "actuate"
    EXECUTE = "execute"
    
    # Autonomous actions (highest risk)
    AUTONOMOUS = "autonomous"
    
    OTHER = "other"


class SafetyLevel(str, Enum):
    """Safety tolerance level for an action."""
    # Informational - no actual change
    INFORMATIONAL = "informational"
    
    # Low risk - reversible changes to configuration
    LOW = "low"
    
    # Medium risk - changes to external systems
    MEDIUM = "medium"
    
    # High risk - system modification or actuation
    HIGH = "high"
    
    # Critical risk - autonomous execution
    CRITICAL = "critical"


class ApprovalRequirement(str, Enum):
    """Required approval type for an action."""
    NONE = "none"  # No approval required (read-only)
    REVIEW = "review"  # Manual review only
    APPROVAL = "approval"  # Explicit approval required
    MULTI_STAGED = "multi_staged"  # Multiple approvals or staged execution
    AUDIT_ONLY = "audit_only"  # No execution, only audit logging


class ExecutionPermission(str, Enum):
    """Permission status for execution."""
    # Fully permitted
    PERMITTED = "permitted"
    
    # Not permitted without approval
    BLOCKED = "blocked"
    
    # Not permitted in offline/degraded mode
    OFFLINE_BLOCKED = "offline_blocked"
    
    # Not permitted due to insufficient evidence
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    
    # Not permitted - domain restriction
    DOMAIN_PROHIBITED = "domain_prohibited"
    
    # Not permitted - requires additional proof
    PROOF_REQUIRED = "proof_required"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class SafetyRequirement:
    """Safety requirement for an action type."""
    action_type: str  # ActionType.value
    safety_level: str  # SafetyLevel.value
    approval_requirement: str  # ApprovalRequirement.value
    min_evidence_confidence: float = 0.0  # 0.0-1.0
    requires_rollback: bool = False
    requires_audit: bool = False
    requires_domain_context: bool = False
    requires_proof: List[str] = field(default_factory=list)  # ProofType values


@dataclass
class SafetyContract:
    """Full safety contract for a proposal or action.
    
    Combines action type, safety level, and approval requirements.
    """
    action_type: str  # ActionType.value
    safety_level: str  # SafetyLevel.value
    approval_requirement: str  # ApprovalRequirement.value
    
    # Evidence requirements
    min_evidence_confidence: float = 0.0
    requires_rollback: bool = False
    requires_audit: bool = False
    requires_domain_context: bool = False
    
    # Execution permissions
    execution_permission: str = ExecutionPermission.PERMITTED.value
    blocked_reasons: List[str] = field(default_factory=list)
    proof_requirements: List[str] = field(default_factory=list)
    
    # Metadata
    assessed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    assessed_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "action_type": self.action_type,
            "safety_level": self.safety_level,
            "approval_requirement": self.approval_requirement,
            "min_evidence_confidence": self.min_evidence_confidence,
            "requires_rollback": self.requires_rollback,
            "requires_audit": self.requires_audit,
            "requires_domain_context": self.requires_domain_context,
            "execution_permission": self.execution_permission,
            "blocked_reasons": self.blocked_reasons,
            "proof_requirements": self.proof_requirements,
            "assessed_at": self.assessed_at,
            "assessed_by": self.assessed_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SafetyContract:
        """Create from dictionary representation."""
        data["blocked_reasons"] = data.get("blocked_reasons", [])
        data["proof_requirements"] = data.get("proof_requirements", [])
        return cls(**data)
    
    def is_permitted(self) -> bool:
        """Check if action is permitted."""
        return self.execution_permission == ExecutionPermission.PERMITTED.value
    
    def is_blocked(self) -> bool:
        """Check if action is blocked."""
        return self.execution_permission in [
            ExecutionPermission.BLOCKED.value,
            ExecutionPermission.OFFLINE_BLOCKED.value,
            ExecutionPermission.INSUFFICIENT_EVIDENCE.value,
            ExecutionPermission.DOMAIN_PROHIBITED.value,
            ExecutionPermission.PROOF_REQUIRED.value,
        ]
    
    def add_blocked_reason(self, reason: str) -> SafetyContract:
        """Add a blocked reason."""
        if reason not in self.blocked_reasons:
            self.blocked_reasons.append(reason)
        return self
    
    def add_proof_requirement(self, proof_type: str) -> SafetyContract:
        """Add a proof requirement."""
        if proof_type not in self.proof_requirements:
            self.proof_requirements.append(proof_type)
        return self
    
    def set_permission(self, permission: str, reason: Optional[str] = None) -> SafetyContract:
        """Set execution permission."""
        self.execution_permission = permission
        if reason and reason not in self.blocked_reasons:
            self.blocked_reasons.append(reason)
        return self


# ============================================================================
# SAFETY CONTRACT REGISTRY
# ============================================================================


def get_safety_contract_registry() -> Dict[str, SafetyRequirement]:
    """Get predefined safety contract registry.
    
    Returns a registry of safety requirements for standard action types.
    """
    registry = {}
    
    # Informational actions (read-only)
    for atype in [ActionType.READ_DATA, ActionType.READ_FILES, ActionType.READ_MEMORY, ActionType.ANALYZE]:
        registry[atype.value] = SafetyRequirement(
            action_type=atype.value,
            safety_level=SafetyLevel.INFORMATIONAL.value,
            approval_requirement=ApprovalRequirement.NONE.value,
            min_evidence_confidence=0.0,
            requires_rollback=False,
            requires_audit=False,
            requires_domain_context=False,
        )
    
    # Configuration changes
    registry[ActionType.CONFIGURE.value] = SafetyRequirement(
        action_type=ActionType.CONFIGURE.value,
        safety_level=SafetyLevel.LOW.value,
        approval_requirement=ApprovalRequirement.REVIEW.value,
        min_evidence_confidence=0.5,
        requires_rollback=True,
        requires_audit=True,
        requires_domain_context=False,
    )
    
    # External system interaction
    registry[ActionType.API_CALL.value] = SafetyRequirement(
        action_type=ActionType.API_CALL.value,
        safety_level=SafetyLevel.MEDIUM.value,
        approval_requirement=ApprovalRequirement.APPROVAL.value,
        min_evidence_confidence=0.6,
        requires_rollback=True,
        requires_audit=True,
        requires_domain_context=True,
    )
    
    registry[ActionType.HTTP_REQUEST.value] = SafetyRequirement(
        action_type=ActionType.HTTP_REQUEST.value,
        safety_level=SafetyLevel.MEDIUM.value,
        approval_requirement=ApprovalRequirement.APPROVAL.value,
        min_evidence_confidence=0.6,
        requires_rollback=True,
        requires_audit=True,
        requires_domain_context=True,
    )
    
    # System modification
    registry[ActionType.FILE_WRITE.value] = SafetyRequirement(
        action_type=ActionType.FILE_WRITE.value,
        safety_level=SafetyLevel.HIGH.value,
        approval_requirement=ApprovalRequirement.MULTI_STAGED.value,
        min_evidence_confidence=0.7,
        requires_rollback=True,
        requires_audit=True,
        requires_domain_context=True,
    )
    
    registry[ActionType.SYSTEM_COMMAND.value] = SafetyRequirement(
        action_type=ActionType.SYSTEM_COMMAND.value,
        safety_level=SafetyLevel.CRITICAL.value,
        approval_requirement=ApprovalRequirement.MULTI_STAGED.value,
        min_evidence_confidence=0.85,
        requires_rollback=True,
        requires_audit=True,
        requires_domain_context=True,
        requires_proof=["validation", "rollback_coverage", "impact_analysis"],
    )
    
    # Autonomous actions
    registry[ActionType.AUTONOMOUS.value] = SafetyRequirement(
        action_type=ActionType.AUTONOMOUS.value,
        safety_level=SafetyLevel.CRITICAL.value,
        approval_requirement=ApprovalRequirement.MULTI_STAGED.value,
        min_evidence_confidence=0.9,
        requires_rollback=True,
        requires_audit=True,
        requires_domain_context=True,
        requires_proof=["validation", "rollback_coverage", "impact_analysis", "autonomy_proof"],
    )
    
    return registry


# ============================================================================
# SAFETY ENGINE
# ============================================================================


class SafetyEngine:
    """Engine for assessing and validating external action safety.
    
    Operates independently - no network access required.
    """
    
    def __init__(self, storage_path: Optional[Any] = None):
        """Initialize safety engine."""
        self.storage_path = storage_path
        self.registry = get_safety_contract_registry()
    
    def assess(
        self,
        action_type: str,
        safety_level: Optional[str] = None,
        evidence_confidence: float = 0.0,
        domain_context: Optional[str] = None,
        is_offline: bool = False,
    ) -> SafetyContract:
        """Assess safety contract for an action type.
        
        Args:
            action_type: Type of action being assessed
            safety_level: Override safety level if known
            evidence_confidence: Current evidence confidence (0.0-1.0)
            domain_context: Domain context if applicable
            is_offline: Whether operating in offline mode
            
        Returns:
            SafetyContract with assessment result
        """
        # Get registry entry
        registry_entry = self.registry.get(action_type)
        if not registry_entry:
            # Unknown action type - default to restrictive
            registry_entry = SafetyRequirement(
                action_type=action_type,
                safety_level=SafetyLevel.MEDIUM.value,
                approval_requirement=ApprovalRequirement.APPROVAL.value,
                min_evidence_confidence=0.5,
                requires_rollback=False,
                requires_audit=False,
                requires_domain_context=False,
            )
        
        # Create safety contract
        contract = SafetyContract(
            action_type=action_type,
            safety_level=safety_level or registry_entry.safety_level,
            approval_requirement=registry_entry.approval_requirement,
            min_evidence_confidence=registry_entry.min_evidence_confidence,
            requires_rollback=registry_entry.requires_rollback,
            requires_audit=registry_entry.requires_audit,
            requires_domain_context=registry_entry.requires_domain_context,
            proof_requirements=list(registry_entry.requires_proof) if registry_entry.requires_proof else [],
        )
        
        # Check offline mode
        if is_offline:
            if action_type in [
                ActionType.API_CALL.value,
                ActionType.HTTP_REQUEST.value,
                ActionType.ACTUATE.value,
                ActionType.AUTONOMOUS.value,
            ]:
                contract.set_permission(
                    ExecutionPermission.OFFLINE_BLOCKED.value,
                    "External action blocked in offline mode",
                )
        
        # Check evidence confidence
        if evidence_confidence < contract.min_evidence_confidence:
            contract.set_permission(
                ExecutionPermission.INSUFFICIENT_EVIDENCE.value,
                f"Evidence confidence {evidence_confidence:.2f} below required {contract.min_evidence_confidence:.2f}",
            )
        
        # Check domain context requirement
        if contract.requires_domain_context and not domain_context:
            contract.set_permission(
                ExecutionPermission.DOMAIN_PROHIBITED.value,
                "Domain context required but not provided",
            )
        
        # Check proof requirements
        if contract.proof_requirements and not is_offline:
            # In offline mode, some proofs may be unavailable
            if is_offline and "validation" in contract.proof_requirements:
                contract.add_blocked_reason("Validation proof unavailable in offline mode")
        
        # Determine final permission
        if not contract.is_blocked():
            contract.set_permission(ExecutionPermission.PERMITTED.value)
        
        # Set assessed metadata
        contract.assessed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        contract.assessed_by = "safety_engine_v23"
        
        return contract
    
    def get_contract_summary(self, contract: SafetyContract) -> Dict[str, Any]:
        """Get a human-readable summary of the safety contract."""
        return {
            "action_type": contract.action_type,
            "safety_level": contract.safety_level,
            "approval_requirement": contract.approval_requirement,
            "evidence_required": contract.min_evidence_confidence,
            "requires_rollback": contract.requires_rollback,
            "requires_audit": contract.requires_audit,
            "requires_domain_context": contract.requires_domain_context,
            "execution_permission": contract.execution_permission,
            "blocked_reasons": contract.blocked_reasons,
            "proof_requirements": contract.proof_requirements,
            "assessed_at": contract.assessed_at,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "registry_size": len(self.registry),
            "registry": {k: v.to_dict() if hasattr(v, 'to_dict') else v.__dict__ for k, v in self.registry.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def add_safety_to_change_proposal(proposal_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add safety contract to change proposal.
    
    This is purely additive — no migration required.
    """
    if "action_type" not in proposal_dict:
        proposal_dict["action_type"] = None
    if "safety_contract" not in proposal_dict:
        proposal_dict["safety_contract"] = None
    if "safety_contract_summary" not in proposal_dict:
        proposal_dict["safety_contract_summary"] = None
    return proposal_dict


def add_safety_to_governance_view(governance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add safety contract to governance view.
    
    This is purely additive — no migration required.
    """
    if "action_type" not in governance_dict:
        governance_dict["action_type"] = None
    if "safety_contract" not in governance_dict:
        governance_dict["safety_contract"] = None
    if "safety_status" not in governance_dict:
        governance_dict["safety_status"] = None
    if "safety_blocked" not in governance_dict:
        governance_dict["safety_blocked"] = False
    return governance_dict


def add_safety_to_proposal_realization(realization_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add safety contract to proposal realization.
    
    This is purely additive — no migration required.
    """
    if "action_type" not in realization_dict:
        realization_dict["action_type"] = None
    if "safety_contract" not in realization_dict:
        realization_dict["safety_contract"] = None
    if "safety_approved" not in realization_dict:
        realization_dict["safety_approved"] = False
    if "safety_blocked_reasons" not in realization_dict:
        realization_dict["safety_blocked_reasons"] = []
    return realization_dict


def add_safety_to_proof_gate(proof_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add safety status to proof gate.
    
    This is purely additive — no migration required.
    """
    if "safety_approved" not in proof_dict:
        proof_dict["safety_approved"] = False
    if "safety_blocked" not in proof_dict:
        proof_dict["safety_blocked"] = False
    if "safety_blocked_reasons" not in proof_dict:
        proof_dict["safety_blocked_reasons"] = []
    return proof_dict
