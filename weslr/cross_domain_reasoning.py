# cross_domain_reasoning.py - Self-Architecture Core v25: Cross-Domain Reasoning / Transfer Layer
# Allow WESLR to reuse reasoning patterns across domains while respecting domain-specific thresholds,
# risk styles, recommendation styles, and safety constraints.
# Additive only, transparent, deterministic-core preserving, reversible, no hidden cross-domain bleed.
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


class TransferType(str, Enum):
    """Types of reasoning transfer between domains."""
    # Direct reuse of pattern
    DIRECT = "direct"  # Exact pattern reuse where applicable
    
    # Adapted pattern
    ADAPTED = "adapted"  # Pattern adjusted for domain nuances
    
    # Abstract pattern
    ABSTRACT = "abstract"  # High-level pattern extracted and applied
    
    # No transfer (domain-specific)
    NONE = "none"  # No transfer, domain-specific reasoning only


class TransferSafety(str, Enum):
    """Safety classification for domain transfer."""
    # Safe transfer
    SAFE = "safe"  # No constraints violated
    
    # Requires review
    REQUIRES_REVIEW = "requires_review"  # Transfer possible but needs operator approval
    
    # Not allowed
    FORBIDDEN = "forbidden"  # Transfer prohibited by domain constraints
    SAFETY_CONSTRAINT = "safety_constraint"  # Safety level too high for target domain
    EVIDENCE_GAP = "evidence_gap"  # Evidence doesn't meet target domain threshold


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ReasoningPattern:
    """A reusable reasoning pattern from a domain.
    
    Captures the essential reasoning steps, heuristics, and evidence types
    that can potentially be transferred to other domains.
    """
    
    pattern_id: str
    domain: str
    pattern_type: str  # e.g., "risk_assessment", "forecast_method", "decision_tree"
    
    # Pattern structure
    reasoning_steps: List[str] = field(default_factory=list)
    evidence_types: List[str] = field(default_factory=list)
    heuristics: List[str] = field(default_factory=list)
    
    # Transfer metadata
    originating_domain: str = ""
    target_domains: List[str] = field(default_factory=list)
    transferability_score: float = 1.0  # 0.0-1.0
    
    # Constraints
    forbidden_transfers: List[str] = field(default_factory=list)  # Domain IDs where transfer is forbidden
    evidence_threshold_adjustment: float = 0.0  # Adjustment to evidence threshold for transfer
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_used_at: Optional[str] = None
    transfer_count: int = 0
    confidence: float = 0.5  # Confidence in pattern validity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pattern_id": self.pattern_id,
            "domain": self.domain,
            "pattern_type": self.pattern_type,
            "reasoning_steps": self.reasoning_steps,
            "evidence_types": self.evidence_types,
            "heuristics": self.heuristics,
            "originating_domain": self.originating_domain,
            "target_domains": self.target_domains,
            "transferability_score": self.transferability_score,
            "forbidden_transfers": self.forbidden_transfers,
            "evidence_threshold_adjustment": self.evidence_threshold_adjustment,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "transfer_count": self.transfer_count,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReasoningPattern:
        """Create from dictionary representation."""
        data["reasoning_steps"] = data.get("reasoning_steps", [])
        data["evidence_types"] = data.get("evidence_types", [])
        data["heuristics"] = data.get("heuristics", [])
        data["target_domains"] = data.get("target_domains", [])
        data["forbidden_transfers"] = data.get("forbidden_transfers", [])
        return cls(**data)
    
    def is_transferable_to(self, target_domain: str) -> TransferSafety:
        """Check if pattern is transferable to a target domain."""
        # Check forbidden transfers
        if target_domain in self.forbidden_transfers:
            return TransferSafety.FORBIDDEN.value
        
        # Check confidence (low confidence patterns aren't transferable)
        if self.confidence < 0.7:
            return TransferSafety.REQUIRES_REVIEW.value
        
        # Default: transferable
        return TransferSafety.SAFE.value
    
    def get_transfer_evidence_threshold(self, target_domain: str) -> float:
        """Get adjusted evidence threshold for target domain."""
        # Base threshold (domain-specific)
        base_threshold = 0.6  # Default
        
        # Apply adjustment
        adjusted = base_threshold + self.evidence_threshold_adjustment
        
        # Clamp to valid range
        return max(0.0, min(1.0, adjusted))
    
    def record_transfer(self) -> ReasoningPattern:
        """Record a successful transfer."""
        self.transfer_count += 1
        self.last_used_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self


@dataclass
class DomainTransferContext:
    """Context for a cross-domain transfer operation.
    
    Captures the relationship between originating and target domains,
    including any necessary adaptations or constraints.
    """
    
    pattern_id: str
    originating_domain: str
    target_domain: str
    transfer_type: str  # TransferType.value
    safety_classification: str  # TransferSafety.value
    
    # Transfer details
    adaptations_made: List[str] = field(default_factory=list)
    evidence_threshold: float = 0.6
    safety_constraints_applied: List[str] = field(default_factory=list)
    
    # Evidence requirements
    required_evidence_confidence: float = 0.7
    evidence_adjustment_reason: Optional[str] = None
    
    # Metadata
    assessed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    assessed_by: Optional[str] = None
    approved: bool = False
    approval_reason: Optional[str] = None
    rejected: bool = False
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pattern_id": self.pattern_id,
            "originating_domain": self.originating_domain,
            "target_domain": self.target_domain,
            "transfer_type": self.transfer_type,
            "safety_classification": self.safety_classification,
            "adaptations_made": self.adaptations_made,
            "evidence_threshold": self.evidence_threshold,
            "safety_constraints_applied": self.safety_constraints_applied,
            "required_evidence_confidence": self.required_evidence_confidence,
            "evidence_adjustment_reason": self.evidence_adjustment_reason,
            "assessed_at": self.assessed_at,
            "assessed_by": self.assessed_by,
            "approved": self.approved,
            "approval_reason": self.approval_reason,
            "rejected": self.rejected,
            "rejection_reason": self.rejection_reason,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DomainTransferContext:
        """Create from dictionary representation."""
        data["adaptations_made"] = data.get("adaptations_made", [])
        data["safety_constraints_applied"] = data.get("safety_constraints_applied", [])
        return cls(**data)
    
    def is_allowed(self) -> bool:
        """Check if transfer is allowed (not rejected or forbidden)."""
        if self.rejected or self.safety_classification == TransferSafety.FORBIDDEN.value:
            return False
        if self.safety_classification == TransferSafety.REQUIRES_REVIEW.value and not self.approved:
            return False
        return True
    
    def set_approval(self, approved: bool, reason: str) -> DomainTransferContext:
        """Set approval status for a transfer."""
        self.approved = approved
        self.rejected = not approved
        if approved:
            self.approval_reason = reason
        else:
            self.rejection_reason = reason
        return self


# ============================================================================
# TRANSFER ENGINE
# ============================================================================


class CrossDomainReasoningEngine:
    """Engine for managing cross-domain reasoning transfers.
    
    Operates independently - no network access required.
    All transfers are transparent and reversible.
    """
    
    def __init__(self, storage_path: Optional[Any] = None):
        """Initialize cross-domain reasoning engine."""
        self.storage_path = storage_path
        self.patterns: Dict[str, ReasoningPattern] = {}  # pattern_id -> Pattern
        self.transfers: Dict[str, DomainTransferContext] = {}  # transfer_id -> Context
    
    def register_pattern(self, pattern: ReasoningPattern) -> ReasoningPattern:
        """Register a reasoning pattern."""
        self.patterns[pattern.pattern_id] = pattern
        return pattern
    
    def get_pattern(self, pattern_id: str) -> Optional[ReasoningPattern]:
        """Get a pattern by ID."""
        return self.patterns.get(pattern_id)
    
    def find_transferable_patterns(self, domain: str) -> List[ReasoningPattern]:
        """Find patterns that could be transferred to a domain."""
        transferable = []
        for pattern in self.patterns.values():
            safety = pattern.is_transferable_to(domain)
            if safety in [TransferSafety.SAFE.value, TransferSafety.REQUIRES_REVIEW.value]:
                transferable.append(pattern)
        return transferable
    
    def assess_transfer(
        self,
        pattern_id: str,
        target_domain: str,
        evidence_confidence: float = 0.0,
    ) -> DomainTransferContext:
        """Assess a potential transfer to a target domain."""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return DomainTransferContext(
                pattern_id=pattern_id,
                originating_domain="unknown",
                target_domain=target_domain,
                transfer_type=TransferType.NONE.value,
                safety_classification=TransferSafety.FORBIDDEN.value,
                rejection_reason="Pattern not found",
                rejected=True,
            )
        
        # Determine transfer type
        if pattern.originating_domain == target_domain:
            transfer_type = TransferType.DIRECT.value
        elif pattern.target_domains and target_domain in pattern.target_domains:
            transfer_type = TransferType.ADAPTED.value
        else:
            transfer_type = TransferType.ABSTRACT.value
        
        # Assess safety
        safety = pattern.is_transferable_to(target_domain)
        
        # Get evidence threshold
        evidence_threshold = pattern.get_transfer_evidence_threshold(target_domain)
        
        # Create context
        context = DomainTransferContext(
            pattern_id=pattern_id,
            originating_domain=pattern.domain,
            target_domain=target_domain,
            transfer_type=transfer_type,
            safety_classification=safety,
            evidence_threshold=evidence_threshold,
            required_evidence_confidence=evidence_threshold,
        )
        
        # Check evidence confidence
        if evidence_confidence < evidence_threshold:
            context.safety_classification = TransferSafety.EVIDENCE_GAP.value
            context.evidence_adjustment_reason = f"Required {evidence_threshold:.2f}, got {evidence_confidence:.2f}"
        
        # Set metadata
        context.assessed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        context.assessed_by = "cross_domain_engine_v25"
        
        return context
    
    def approve_transfer(
        self,
        pattern_id: str,
        target_domain: str,
        reason: str,
    ) -> bool:
        """Approve a transfer."""
        transfer_key = f"{pattern_id}:{target_domain}"
        if transfer_key not in self.transfers:
            return False
        self.transfers[transfer_key].set_approval(True, reason)
        return True
    
    def reject_transfer(
        self,
        pattern_id: str,
        target_domain: str,
        reason: str,
    ) -> bool:
        """Reject a transfer."""
        transfer_key = f"{pattern_id}:{target_domain}"
        if transfer_key not in self.transfers:
            return False
        self.transfers[transfer_key].set_approval(False, reason)
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "pattern_count": len(self.patterns),
            "patterns": {k: v.to_dict() for k, v in self.patterns.items()},
            "transfer_count": len(self.transfers),
            "transfers": {k: v.to_dict() for k, v in self.transfers.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_domain_ontology(ontology_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add transfer metadata to domain ontology.
    
    This is purely additive — no migration required.
    """
    if "transferable_patterns" not in ontology_dict:
        ontology_dict["transferable_patterns"] = []
    if "forbidden_transfers" not in ontology_dict:
        ontology_dict["forbidden_transfers"] = []
    if "transfer_constraints" not in ontology_dict:
        ontology_dict["transfer_constraints"] = {}
    return ontology_dict


def integrate_with_governance_view(governance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add transfer context to governance view.
    
    This is purely additive — no migration required.
    """
    if "transfer_context" not in governance_dict:
        governance_dict["transfer_context"] = None
    if "transfer_safety" not in governance_dict:
        governance_dict["transfer_safety"] = None
    if "transfer_blocked" not in governance_dict:
        governance_dict["transfer_blocked"] = False
    if "transfer_blocked_reasons" not in governance_dict:
        governance_dict["transfer_blocked_reasons"] = []
    return governance_dict


def integrate_with_narrative(narrative_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add transfer context to narrative.
    
    This is purely additive — no migration required.
    """
    if "transfer_hint" not in narrative_dict:
        narrative_dict["transfer_hint"] = None
    if "domain_transfer_safe" not in narrative_dict:
        narrative_dict["domain_transfer_safe"] = True
    return narrative_dict


def integrate_with_proposal_realization(realization_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add transfer context to proposal realization.
    
    This is purely additive — no migration required.
    """
    if "transfer_context" not in realization_dict:
        realization_dict["transfer_context"] = None
    if "transfer_required_evidence" not in realization_dict:
        realization_dict["transfer_required_evidence"] = 0.0
    if "transfer_blocked" not in realization_dict:
        realization_dict["transfer_blocked"] = False
    return realization_dict
