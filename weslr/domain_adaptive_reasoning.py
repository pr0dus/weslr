# domain_adaptive_reasoning.py - WESLR v55: Domain Adaptive Reasoning Hardening Layer
# Creates a governed domain adaptive reasoning layer so WESLR can generalize reasoning
# patterns across new domains without manual intervention, while maintaining safety.
# Additive only, transparent, reversible, role-aware, non-manipulative.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from . import scenario_model
from . import adaptive_guidance


# ============================================================================
# ENUMS
# ============================================================================


class DomainType(str, Enum):
    """Types of domains WESLR can reason about."""
    GENERAL = "general"  # General reasoning, no domain-specific constraints
    TECHNICAL = "technical"  # Technical/system reasoning
    OPERATIONAL = "operational"  # Operational/process reasoning
    STRATEGIC = "strategic"  # Strategic/planning reasoning
    TACTICAL = "tactical"  # Tactical/execution reasoning


class DomainAdaptationMode(str, Enum):
    """Mode for domain adaptation."""
    OFF = "off"  # No domain adaptation
    PASSIVE = "passive"  # Track domain but don't adapt reasoning
    ACTIVE = "active"  # Adapt reasoning to domain characteristics
    TRANSFER = "transfer"  # Apply knowledge transfer between domains


class KnowledgeTransferStrategy(str, Enum):
    """Strategy for knowledge transfer between domains."""
    NONE = "none"  # No knowledge transfer
    DIRECT = "direct"  # Direct transfer of patterns
    ABSTRACT = "abstract"  # Transfer abstract principles
    GENERALIZE = "generalize"  # Generalize patterns to broader context


class DomainConstraintScope(str, Enum):
    """Scope of domain constraints."""
    LOCAL = "local"  # Applies only within this domain
    GLOBAL = "global"  # Applies across all domains
    HIERARCHICAL = "hierarchical"  # Applies to sub-domains


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class DomainDefinition:
    """Definition of a domain with its characteristics."""
    
    domain_id: str  # Unique identifier
    domain_type: str = DomainType.GENERAL.value  # Type of domain
    domain_name: str = "default"  # Human-readable name
    description: str = ""  # Domain description
    
    # Domain characteristics
    complexity_level: float = 5.0  # 0-10, higher is more complex
    rate_of_change: float = 5.0  # 0-10, higher is faster changing
    safety_criticality: float = 5.0  # 0-10, higher is more safety-critical
    
    # Reasoning constraints
    max_evidence_required: int = 3  # Minimum evidence required
    min_confidence_threshold: float = 0.5  # Minimum confidence for recommendations
    
    # Knowledge transfer settings
    transfer_strategy: str = KnowledgeTransferStrategy.ABSTRACT.value
    transfer_target_domains: List[str] = field(default_factory=list)  # Domains to transfer to
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "domain_type": self.domain_type,
            "domain_name": self.domain_name,
            "description": self.description,
            "complexity_level": self.complexity_level,
            "rate_of_change": self.rate_of_change,
            "safety_criticality": self.safety_criticality,
            "max_evidence_required": self.max_evidence_required,
            "min_confidence_threshold": self.min_confidence_threshold,
            "transfer_strategy": self.transfer_strategy,
            "transfer_target_domains": self.transfer_target_domains,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DomainDefinition:
        data["transfer_target_domains"] = data.get("transfer_target_domains", [])
        return cls(**data)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> DomainDefinition:
        return cls.from_dict(json.loads(json_str))


@dataclass
class DomainReasoningState:
    """State of reasoning for a specific domain."""
    
    domain_id: str
    active_adaptation_mode: str = DomainAdaptationMode.PASSIVE.value
    confidence_adjustment: float = 1.0  # Multiplier for domain-specific confidence
    evidence_count: int = 0  # Number of evidence items processed
    last_adaptation_time: str = ""
    
    # Domain-specific metrics
    average_confidence: float = 0.0
    recommendation_count: int = 0
    adjustment_reasons: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "active_adaptation_mode": self.active_adaptation_mode,
            "confidence_adjustment": self.confidence_adjustment,
            "evidence_count": self.evidence_count,
            "last_adaptation_time": self.last_adaptation_time,
            "average_confidence": self.average_confidence,
            "recommendation_count": self.recommendation_count,
            "adjustment_reasons": self.adjustment_reasons,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DomainReasoningState:
        data["adjustment_reasons"] = data.get("adjustment_reasons", [])
        return cls(**data)


@dataclass
class DomainConstraint:
    """Constraint that applies to a domain."""
    
    constraint_id: str
    constraint_type: str  # e.g., "safety", "performance", "cost"
    constraint_value: str  # The constraint value or threshold
    domain_scope: str = DomainConstraintScope.LOCAL.value  # Scope of application
    applies_to_subdomains: bool = True  # Whether subdomains inherit constraint
    min_evidence_required: Optional[int] = None  # Override default evidence requirement
    min_confidence_threshold: Optional[float] = None  # Override default confidence threshold
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "constraint_type": self.constraint_type,
            "constraint_value": self.constraint_value,
            "domain_scope": self.domain_scope,
            "applies_to_subdomains": self.applies_to_subdomains,
            "min_evidence_required": self.min_evidence_required,
            "min_confidence_threshold": self.min_confidence_threshold,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DomainConstraint:
        return cls(**data)


@dataclass
class DomainAdaptiveContext:
    """Complete context for domain-adaptive reasoning."""
    
    current_domain: str  # Current domain ID
    active_domains: List[str] = field(default_factory=list)  # All active domains
    adaptation_mode: str = DomainAdaptationMode.PASSIVE.value
    knowledge_transfer_enabled: bool = False
    transfer_strategies: List[str] = field(default_factory=list)
    
    # Domain definitions
    domain_definitions: Dict[str, DomainDefinition] = field(default_factory=dict)
    
    # Reasoning states
    domain_states: Dict[str, DomainReasoningState] = field(default_factory=dict)
    
    # Constraints
    constraints: List[DomainConstraint] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_domain": self.current_domain,
            "active_domains": self.active_domains,
            "adaptation_mode": self.adaptation_mode,
            "knowledge_transfer_enabled": self.knowledge_transfer_enabled,
            "transfer_strategies": self.transfer_strategies,
            "domain_definitions": {k: v.to_dict() for k, v in self.domain_definitions.items()},
            "domain_states": {k: v.to_dict() for k, v in self.domain_states.items()},
            "constraints": [c.to_dict() for c in self.constraints],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DomainAdaptiveContext:
        data["active_domains"] = data.get("active_domains", [])
        data["transfer_strategies"] = data.get("transfer_strategies", [])
        data["domain_definitions"] = {
            k: DomainDefinition.from_dict(v) for k, v in data.get("domain_definitions", {}).items()
        }
        data["domain_states"] = {
            k: DomainReasoningState.from_dict(v) for k, v in data.get("domain_states", {}).items()
        }
        data["constraints"] = [DomainConstraint.from_dict(c) for c in data.get("constraints", [])]
        return cls(**data)


# ============================================================================
# DOMAIN ADAPTIVE REASONING ENGINE
# ============================================================================


class DomainAdaptiveReasoningEngine:
    """Engine for domain-adaptive reasoning with hardening."""
    
    def __init__(self):
        self.context: DomainAdaptiveContext = DomainAdaptiveContext(current_domain="default")
        self.last_adaptation: Optional[DomainReasoningState] = None
    
    def register_domain(self, domain: DomainDefinition) -> None:
        """Register a new domain with its characteristics."""
        self.context.domain_definitions[domain.domain_id] = domain
        if domain.domain_id not in self.context.active_domains:
            self.context.active_domains.append(domain.domain_id)
        
        # Initialize domain state
        if domain.domain_id not in self.context.domain_states:
            self.context.domain_states[domain.domain_id] = DomainReasoningState(
                domain_id=domain.domain_id
            )
    
    def set_adaptation_mode(self, mode: str, domain_id: Optional[str] = None) -> None:
        """Set adaptation mode for current or specific domain."""
        self.context.adaptation_mode = mode
        if domain_id and domain_id in self.context.domain_states:
            self.context.domain_states[domain_id].active_adaptation_mode = mode
    
    def adapt_reasoning(self, domain_id: str) -> DomainReasoningState:
        """Adapt reasoning for a domain based on its characteristics."""
        domain = self.context.domain_definitions.get(domain_id)
        state = self.context.domain_states.get(domain_id)
        
        if not domain or not state:
            return state or DomainReasoningState(domain_id=domain_id)
        
        # Adjust confidence based on domain characteristics
        confidence_adjustment = 1.0
        
        if domain.safety_criticality >= 7.0:
            # Safety-critical domains need higher confidence
            confidence_adjustment = 0.9
            state.adjustment_reasons.append("safety_criticality_high")
        
        if domain.complexity_level >= 7.0:
            # Complex domains may have more uncertainty
            confidence_adjustment *= 0.95
            state.adjustment_reasons.append("complexity_high")
        
        if domain.rate_of_change >= 7.0:
            # Fast-changing domains may have stale knowledge
            confidence_adjustment *= 0.9
            state.adjustment_reasons.append("rate_of_change_high")
        
        state.confidence_adjustment = max(0.1, min(1.0, confidence_adjustment))
        state.last_adaptation_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        state.active_adaptation_mode = self.context.adaptation_mode
        
        self.last_adaptation = state
        return state
    
    def transfer_knowledge(self, from_domain: str, to_domain: str) -> Optional[Dict[str, Any]]:
        """Transfer knowledge from one domain to another."""
        from_def = self.context.domain_definitions.get(from_domain)
        to_def = self.context.domain_definitions.get(to_domain)
        
        if not from_def or not to_def:
            return None
        
        strategy = from_def.transfer_strategy
        if strategy == KnowledgeTransferStrategy.NONE.value:
            return None
        
        # Apply transfer strategy
        transfer_result = {
            "from_domain": from_domain,
            "to_domain": to_domain,
            "strategy": strategy,
            "transferred_features": []
        }
        
        if strategy == KnowledgeTransferStrategy.DIRECT.value:
            # Direct pattern transfer
            transfer_result["transferred_features"].append("recommendation_patterns")
            transfer_result["transferred_features"].append("evidence_thresholds")
        
        elif strategy == KnowledgeTransferStrategy.ABSTRACT.value:
            # Abstract principle transfer
            transfer_result["transferred_features"].append("reasoning_principles")
            transfer_result["transferred_features"].append("constraint_patterns")
        
        elif strategy == KnowledgeTransferStrategy.GENERALIZE.value:
            # Generalization transfer
            transfer_result["transferred_features"].append("abstract_patterns")
            transfer_result["transferred_features"].append("cross_domain_patterns")
        
        # Update to domain
        if to_def.domain_id not in self.context.domain_states:
            self.context.domain_states[to_def.domain_id] = DomainReasoningState(domain_id=to_def.domain_id)
        
        self.context.domain_states[to_def.domain_id].adjustment_reasons.append(f"knowledge_transfer_from_{from_domain}")
        
        return transfer_result
    
    def apply_constraints(self, domain_id: str, evidence_count: int, confidence: float) -> Dict[str, Any]:
        """Apply domain constraints to evidence and confidence."""
        domain = self.context.domain_definitions.get(domain_id)
        
        result = {
            "applied": True,
            "original_evidence": evidence_count,
            "original_confidence": confidence,
            "adjusted_evidence": evidence_count,
            "adjusted_confidence": confidence,
            "reasons": []
        }
        
        if not domain:
            return result
        
        # Check evidence requirement
        if evidence_count < domain.max_evidence_required:
            result["adjusted_evidence"] = domain.max_evidence_required
            result["reasons"].append(f"evidence_insufficient: need {domain.max_evidence_required}, got {evidence_count}")
        
        # Check confidence threshold
        if confidence < domain.min_confidence_threshold:
            result["adjusted_confidence"] = domain.min_confidence_threshold
            result["reasons"].append(f"confidence_below_threshold: need {domain.min_confidence_threshold}, got {confidence}")
        
        # Apply domain-specific confidence adjustment
        state = self.context.domain_states.get(domain_id)
        if state:
            result["adjusted_confidence"] *= state.confidence_adjustment
            result["adjusted_confidence"] = max(0.0, min(1.0, result["adjusted_confidence"]))
        
        return result
    
    def get_current_domain_context(self) -> DomainAdaptiveContext:
        """Get the current domain adaptive context."""
        return self.context


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "DomainType",
    "DomainAdaptationMode",
    "KnowledgeTransferStrategy",
    "DomainConstraintScope",
    "DomainDefinition",
    "DomainReasoningState",
    "DomainConstraint",
    "DomainAdaptiveContext",
    "DomainAdaptiveReasoningEngine",
]
