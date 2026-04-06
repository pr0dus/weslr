"""Domain Ontology / Domain Overlay Layer (v21)

Domain specialization substrate that prepares WESLR for multi-domain deployment:
home/family, education, hospitals/medicine, science/research, industry, aerospace.

Architecture:
  - DomainType enum — predefined domain identifiers
  - DomainProfile — configuration for domain-specific behavior
  - DomainContext — runtime domain assignment for proposals/evidence
  - DomainOverlay — composition layer for domain-sensitive policies

Rules:
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No cross-domain hardcoding in existing logic
  - Domain-agnostic base layer extended via overlays
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class DomainType(str, Enum):
    """Predefined domain identifiers for WESLR."""
    HOME_FAMILY = "home_family"
    EDUCATION = "education"
    HOSPITALS_MEDICINE = "hospitals_medicine"
    SCIENCE_RESEARCH = "science_research"
    INDUSTRY = "industry"
    AEROSPACE_LONG_MISSION = "aerospace_long_mission"
    OTHER = "other"


class DomainRiskSensitivity(str, Enum):
    """Domain risk tolerance levels."""
    LOW = "low"       # Minimal risk tolerance, high safety margin
    MEDIUM = "medium" # Standard risk tolerance
    HIGH = "high"     # Higher risk tolerance, efficiency focused


class DomainRecommendationStyle(str, Enum):
    """Preferred recommendation style for domain."""
    PREScriptive = "prescriptive"    # Clear directives, minimal ambiguity
    advisory = "advisory"           # Guidance with explanation
    exploratory = "exploratory"     # Multiple options, emphasize tradeoffs
    diagnostic = "diagnostic"       # Focus on problem analysis first


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class DomainProfile:
    """Configuration for domain-specific behavior.
    
    Defines how WESLR should behave in a specific domain context.
    """
    domain_type: str  # DomainType.value
    name: str         # Human-readable name
    description: str  # Domain purpose and scope
    
    # Evidence thresholds
    minimum_evidence_confidence: float = 0.7  # 0.0-1.0
    required_evidence_types: List[str] = field(default_factory=list)  # EvidenceType values
    
    # Risk and trust
    risk_sensitivity: str = DomainRiskSensitivity.MEDIUM.value
    trust_weighting: float = 1.0  # Multiplier for domain-specific evidence
    
    # Recommendation preferences
    recommendation_style: str = DomainRecommendationStyle.advisory.value
    proof_requirements: List[str] = field(default_factory=list)  # Required proof types
    
    # Operational constraints
    max_execution_latency_ms: int = 10000  # 10 seconds default
    requires_online: bool = False  # Can run offline?
    offline_fallback_allowed: bool = True
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "domain_type": self.domain_type,
            "name": self.name,
            "description": self.description,
            "minimum_evidence_confidence": self.minimum_evidence_confidence,
            "required_evidence_types": self.required_evidence_types,
            "risk_sensitivity": self.risk_sensitivity,
            "trust_weighting": self.trust_weighting,
            "recommendation_style": self.recommendation_style,
            "proof_requirements": self.proof_requirements,
            "max_execution_latency_ms": self.max_execution_latency_ms,
            "requires_online": self.requires_online,
            "offline_fallback_allowed": self.offline_fallback_allowed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DomainProfile:
        """Create from dictionary representation."""
        data["required_evidence_types"] = data.get("required_evidence_types", [])
        data["proof_requirements"] = data.get("proof_requirements", [])
        return cls(**data)
    
    def update(self, **kwargs) -> DomainProfile:
        """Update profile with new values and refresh timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self


@dataclass
class DomainContext:
    """Runtime domain assignment for proposals, evidence, and operations.
    
    Bridges domain profiles with active governance decisions.
    """
    context_id: str
    domain_type: str  # DomainType.value
    domain_profile_id: Optional[str] = None  # Reference to profile if applicable
    
    # Scope
    application_scope: List[str] = field(default_factory=list)  # Affected subsystems
    
    # Overrides
    evidence_confidence_override: Optional[float] = None  # If different from profile
    risk_override: Optional[str] = None  # If different from profile
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "context_id": self.context_id,
            "domain_type": self.domain_type,
            "domain_profile_id": self.domain_profile_id,
            "application_scope": self.application_scope,
            "evidence_confidence_override": self.evidence_confidence_override,
            "risk_override": self.risk_override,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DomainContext:
        """Create from dictionary representation."""
        data["application_scope"] = data.get("application_scope", [])
        return cls(**data)


@dataclass
class DomainOverlay:
    """Composition layer for domain-sensitive policies.
    
    Wraps existing components with domain-aware behavior without modifying them.
    """
    overlay_id: str
    domain_type: str  # DomainType.value
    target_component: str  # e.g., "proposal_review", "evidence_assessment"
    rules: Dict[str, Any] = field(default_factory=dict)  # Domain-specific rules
    
    # Activation
    enabled: bool = True
    priority: int = 100  # Lower = higher priority
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "overlay_id": self.overlay_id,
            "domain_type": self.domain_type,
            "target_component": self.target_component,
            "rules": self.rules,
            "enabled": self.enabled,
            "priority": self.priority,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DomainOverlay:
        """Create from dictionary representation."""
        data["rules"] = data.get("rules", {})
        return cls(**data)


# ============================================================================
# DOMAIN PROFILE REGISTRY
# ============================================================================


def get_domain_profile_registry() -> Dict[str, DomainProfile]:
    """Get predefined domain profiles.
    
    Returns a registry of standard domain configurations that WESLR supports.
    """
    return {
        DomainType.HOME_FAMILY.value: DomainProfile(
            domain_type=DomainType.HOME_FAMILY.value,
            name="Home & Family",
            description="Residential living environments, personal safety, education, wellness.",
            minimum_evidence_confidence=0.6,
            risk_sensitivity=DomainRiskSensitivity.LOW.value,
            trust_weighting=0.9,
            recommendation_style=DomainRecommendationStyle.advisory.value,
            max_execution_latency_ms=5000,
            requires_online=False,
            offline_fallback_allowed=True,
        ),
        DomainType.EDUCATION.value: DomainProfile(
            domain_type=DomainType.EDUCATION.value,
            name="Education",
            description="Academic environments, curriculum delivery, student support, assessment.",
            minimum_evidence_confidence=0.65,
            risk_sensitivity=DomainRiskSensitivity.LOW.value,
            trust_weighting=0.85,
            recommendation_style=DomainRecommendationStyle.exploratory.value,
            max_execution_latency_ms=15000,
            requires_online=False,
            offline_fallback_allowed=True,
        ),
        DomainType.HOSPITALS_MEDICINE.value: DomainProfile(
            domain_type=DomainType.HOSPITALS_MEDICINE.value,
            name="Hospitals & Medicine",
            description="Clinical care, diagnostics, treatment planning, patient safety.",
            minimum_evidence_confidence=0.9,
            required_evidence_types=["observation", "measurement", "validation"],
            risk_sensitivity=DomainRiskSensitivity.LOW.value,
            trust_weighting=0.7,
            recommendation_style=DomainRecommendationStyle.diagnostic.value,
            proof_requirements=["validation", "audit_trail"],
            max_execution_latency_ms=2000,
            requires_online=True,
            offline_fallback_allowed=False,
        ),
        DomainType.SCIENCE_RESEARCH.value: DomainProfile(
            domain_type=DomainType.SCIENCE_RESEARCH.value,
            name="Science & Research",
            description="Experimental design, data analysis, hypothesis testing, publication.",
            minimum_evidence_confidence=0.75,
            risk_sensitivity=DomainRiskSensitivity.HIGH.value,
            trust_weighting=0.95,
            recommendation_style=DomainRecommendationStyle.exploratory.value,
            max_execution_latency_ms=30000,
            requires_online=True,
            offline_fallback_allowed=True,
        ),
        DomainType.INDUSTRY.value: DomainProfile(
            domain_type=DomainType.INDUSTRY.value,
            name="Industry",
            description="Manufacturing, process control, maintenance, supply chain.",
            minimum_evidence_confidence=0.7,
            risk_sensitivity=DomainRiskSensitivity.MEDIUM.value,
            trust_weighting=0.8,
            recommendation_style=DomainRecommendationStyle.PREScriptive.value,
            max_execution_latency_ms=1000,
            requires_online=False,
            offline_fallback_allowed=True,
        ),
        DomainType.AEROSPACE_LONG_MISSION.value: DomainProfile(
            domain_type=DomainType.AEROSPACE_LONG_MISSION.value,
            name="Aerospace & Long-Mission",
            description="Spaceflight, deep-space operations, long-duration autonomy.",
            minimum_evidence_confidence=0.85,
            required_evidence_types=["validation", "forecast"],
            risk_sensitivity=DomainRiskSensitivity.LOW.value,
            trust_weighting=0.6,
            recommendation_style=DomainRecommendationStyle.diagnostic.value,
            proof_requirements=["validation", "rollback_coverage", "autonomy"],
            max_execution_latency_ms=5000,
            requires_online=False,
            offline_fallback_allowed=False,  # Must be autonomous
        ),
    }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================


def create_domain_profile(
    domain_type: str,
    name: str,
    description: str,
    minimum_evidence_confidence: float = 0.7,
    risk_sensitivity: str = DomainRiskSensitivity.MEDIUM.value,
    trust_weighting: float = 1.0,
    recommendation_style: str = DomainRecommendationStyle.advisory.value,
    requires_online: bool = False,
    offline_fallback_allowed: bool = True,
    author: Optional[str] = None,
) -> DomainProfile:
    """Factory function to create a domain profile with sensible defaults."""
    return DomainProfile(
        domain_type=domain_type,
        name=name,
        description=description,
        minimum_evidence_confidence=minimum_evidence_confidence,
        risk_sensitivity=risk_sensitivity,
        trust_weighting=trust_weighting,
        recommendation_style=recommendation_style,
        requires_online=requires_online,
        offline_fallback_allowed=offline_fallback_allowed,
        author=author,
    )


def create_domain_context(
    domain_type: str,
    domain_profile_id: Optional[str] = None,
    application_scope: List[str] = None,
    evidence_confidence_override: Optional[float] = None,
    author: Optional[str] = None,
) -> DomainContext:
    """Factory function to create a domain context."""
    return DomainContext(
        context_id=str(uuid.uuid4()),
        domain_type=domain_type,
        domain_profile_id=domain_profile_id,
        application_scope=application_scope or [],
        evidence_confidence_override=evidence_confidence_override,
        author=author,
    )


def create_domain_overlay(
    domain_type: str,
    target_component: str,
    rules: Dict[str, Any] = None,
    enabled: bool = True,
    priority: int = 100,
    author: Optional[str] = None,
) -> DomainOverlay:
    """Factory function to create a domain overlay."""
    return DomainOverlay(
        overlay_id=str(uuid.uuid4()),
        domain_type=domain_type,
        target_component=target_component,
        rules=rules or {},
        enabled=enabled,
        priority=priority,
        author=author,
    )


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_evidence_claim(claim_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add domain context to evidence claim.
    
    This is purely additive — no migration required.
    """
    if "domain_tags" not in claim_dict:
        claim_dict["domain_tags"] = []
    if "domain_profile_id" not in claim_dict:
        claim_dict["domain_profile_id"] = None
    return claim_dict


def integrate_with_change_proposal(proposal_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add domain context to change proposal.
    
    This is purely additive — no migration required.
    """
    if "domain_context" not in proposal_dict:
        proposal_dict["domain_context"] = None
    if "domain_tag" not in proposal_dict:
        proposal_dict["domain_tag"] = None
    return proposal_dict


def integrate_with_governance_view(governance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add domain-sensitive fields to governance view.
    
    This is purely additive — no migration required.
    """
    if "domain_tag" not in governance_dict:
        governance_dict["domain_tag"] = None
    if "domain_profile_id" not in governance_dict:
        governance_dict["domain_profile_id"] = None
    if "domain_risk_override" not in governance_dict:
        governance_dict["domain_risk_override"] = None
    return governance_dict
