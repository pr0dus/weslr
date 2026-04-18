# deployment_persona.py - WESLR v39: Role / Deployment Persona Layer
# Creates a governed deployment-role layer so WESLR can adapt its communication,
# caution, explanation depth, and initiative level across deployment contexts.
# Additive only, transparent, reversible, role-based (not identity), non-manipulative.
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


class DeploymentRole(str, Enum):
    """Predefined deployment roles for WESLR."""
    HOME_FAMILY = "home_family"  # Residential living, personal safety, wellness
    EDUCATION = "education"  # Academic, curriculum, student support
    HOSPITALS_MEDICINE = "hospitals_medicine"  # Clinical care, diagnostics
    SCIENCE_RESEARCH = "science_research"  # Experimental, data analysis
    INDUSTRY = "industry"  # Manufacturing, process control
    AEROSPACE_LONG_MISSION = "aerospace_long_mission"  # Spaceflight, long-duration


class CommunicationPosture(str, Enum):
    """Preferred communication style for role."""
    PRESCRIPTIVE = "prescriptive"  # Clear directives, minimal ambiguity
    ADVISORY = "advisory"  # Guidance with explanation
    EXPLORATORY = "exploratory"  # Multiple options, emphasize tradeoffs
    DIAGNOSTIC = "diagnostic"  # Focus on problem analysis first
    SUPPORTIVE = "supportive"  # Reassuring, slow pace, extra context


class EvidenceStrictness(str, Enum):
    """Evidence strictness level for role."""
    MINIMAL = "minimal"  # Low confidence acceptable, exploratory
    MODERATE = "moderate"  # Standard confidence required
    HIGH = "high"  # High confidence required
    MAXIMUM = "maximum"  # Very high confidence, validated only


class CautionLevel(str, Enum):
    """Caution level for action selection."""
    MINIMAL = "minimal"  # Direct action, minimal warnings
    NORMAL = "normal"  # Standard caution, balanced approach
    ELEVATED = "elevated"  # Enhanced warnings, more checks
    MAXIMUM = "maximum"  # Maximum caution, extensive validation


class InitiativeLevel(str, Enum):
    """Initiative level for proactive suggestions."""
    NONE = "none"  # Only respond to explicit requests
    LOW = "low"  # Minimal proactive suggestions
    MODERATE = "moderate"  # Standard proactive behavior
    HIGH = "high"  # Aggressive suggestion generation
    MAXIMUM = "maximum"  # Full autonomy within bounds


class ExplanationDensity(str, Enum):
    """Density of explanation to provide."""
    MINIMAL = "minimal"  # Short, direct answers
    STANDARD = "standard"  # Balanced explanation depth
    ENHANCED = "enhanced"  # Detailed reasoning, chain of thought
    MAXIMUM = "maximum"  # Exhaustive explanation, multiple angles


class EscalationStyle(str, Enum):
    """How to escalate uncertain or risky situations."""
    DIRECT = "direct"  # Immediate escalation to human
    GRADUAL = "gradual"  # Incremental escalation with warnings
    HESITANT = "hesitant"  # Minimal escalation, prefer fallback


class DegradedModeBehavior(str, Enum):
    """Behavior when in degraded mode (limited capabilities)."""
    CONSULTATIVE = "consultative"  # Recommend human consultation
    FALLBACK = "fallback"  # Use conservative fallback behavior
    SILENT = "silent"  # Minimize output, avoid risk


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class DeploymentRoleProfile:
    """Configuration for a deployment role."""
    
    role: str  # DeploymentRole.value
    name: str
    description: str
    
    # Communication
    communication_posture: str = CommunicationPosture.ADVISORY.value
    
    # Evidence requirements
    evidence_strictness: str = EvidenceStrictness.MODERATE.value
    minimum_evidence_confidence: float = 0.6  # 0.0-1.0
    
    # Safety margins
    caution_level: str = CautionLevel.NORMAL.value
    max_single_step_confidence: float = 0.85  # Stop if confidence exceeds
    
    # Proactivity
    initiative_level: str = InitiativeLevel.MODERATE.value
    max_suggestions_per_session: int = 5
    
    # Explanations
    explanation_density: str = ExplanationDensity.STANDARD.value
    min_explanation_length: int = 50  # Minimum chars
    
    # Escalation
    escalation_style: str = EscalationStyle.GRADUAL.value
    
    # Degraded mode
    degraded_mode_behavior: str = DegradedModeBehavior.CONSULTATIVE.value
    
    # Operational constraints
    max_execution_latency_ms: int = 10000
    requires_online: bool = False
    offline_fallback_allowed: bool = True
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "role": self.role,
            "name": self.name,
            "description": self.description,
            "communication_posture": self.communication_posture,
            "evidence_strictness": self.evidence_strictness,
            "minimum_evidence_confidence": self.minimum_evidence_confidence,
            "caution_level": self.caution_level,
            "max_single_step_confidence": self.max_single_step_confidence,
            "initiative_level": self.initiative_level,
            "max_suggestions_per_session": self.max_suggestions_per_session,
            "explanation_density": self.explanation_density,
            "min_explanation_length": self.min_explanation_length,
            "escalation_style": self.escalation_style,
            "degraded_mode_behavior": self.degraded_mode_behavior,
            "max_execution_latency_ms": self.max_execution_latency_ms,
            "requires_online": self.requires_online,
            "offline_fallback_allowed": self.offline_fallback_allowed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DeploymentRoleProfile:
        """Create from dictionary representation."""
        return cls(**data)
    
    def update(self, **kwargs) -> DeploymentRoleProfile:
        """Update profile with new values and refresh timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self


@dataclass
class DeploymentContext:
    """Runtime deployment role assignment."""
    
    context_id: str
    role: str  # DeploymentRole.value
    role_profile_id: Optional[str] = None  # Reference to profile if applicable
    
    # Overrides
    evidence_confidence_override: Optional[float] = None
    caution_override: Optional[str] = None
    initiative_override: Optional[str] = None
    
    # Scope
    application_scope: List[str] = field(default_factory=list)  # Affected subsystems
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "context_id": self.context_id,
            "role": self.role,
            "role_profile_id": self.role_profile_id,
            "evidence_confidence_override": self.evidence_confidence_override,
            "caution_override": self.caution_override,
            "initiative_override": self.initiative_override,
            "application_scope": self.application_scope,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DeploymentContext:
        """Create from dictionary representation."""
        data["application_scope"] = data.get("application_scope", [])
        return cls(**data)


@dataclass
class RoleBehaviorAdaptation:
    """Computed behavior adaptation for current role."""
    
    role: str
    effective_communication_posture: str
    effective_evidence_strictness: str
    effective_caution_level: str
    effective_initiative_level: str
    effective_explanation_density: str
    effective_escalation_style: str
    effective_degraded_mode_behavior: str
    
    # Evidence thresholds
    minimum_evidence_confidence: float
    max_single_step_confidence: float
    
    # Proactivity
    max_suggestions_per_session: int
    can_be_proactive: bool
    
    # Output control
    requires_explanation: bool
    min_explanation_length: int
    
    # Escalation
    escalation_delay_ms: int  # Delay before escalation
    
    # Metadata
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    computed_by: str = "deployment_persona_layer_v39"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "role": self.role,
            "effective_communication_posture": self.effective_communication_posture,
            "effective_evidence_strictness": self.effective_evidence_strictness,
            "effective_caution_level": self.effective_caution_level,
            "effective_initiative_level": self.effective_initiative_level,
            "effective_explanation_density": self.effective_explanation_density,
            "effective_escalation_style": self.effective_escalation_style,
            "effective_degraded_mode_behavior": self.effective_degraded_mode_behavior,
            "minimum_evidence_confidence": self.minimum_evidence_confidence,
            "max_single_step_confidence": self.max_single_step_confidence,
            "max_suggestions_per_session": self.max_suggestions_per_session,
            "can_be_proactive": self.can_be_proactive,
            "requires_explanation": self.requires_explanation,
            "min_explanation_length": self.min_explanation_length,
            "escalation_delay_ms": self.escalation_delay_ms,
            "computed_at": self.computed_at,
            "computed_by": self.computed_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RoleBehaviorAdaptation:
        """Create from dictionary representation."""
        return cls(**data)


# ============================================================================
# DEPLOYMENT ROLE REGISTRY
# ============================================================================


def get_deployment_role_registry() -> Dict[str, DeploymentRoleProfile]:
    """Get predefined deployment role profiles.
    
    Returns a registry of standard deployment configurations that WESLR supports.
    """
    return {
        DeploymentRole.HOME_FAMILY.value: DeploymentRoleProfile(
            role=DeploymentRole.HOME_FAMILY.value,
            name="Home & Family",
            description="Residential living environments, personal safety, education, wellness.",
            communication_posture=CommunicationPosture.SUPPORTIVE.value,
            evidence_strictness=EvidenceStrictness.MODERATE.value,
            minimum_evidence_confidence=0.6,
            caution_level=CautionLevel.ELEVATED.value,
            initiative_level=InitiativeLevel.LOW.value,
            explanation_density=ExplanationDensity.STANDARD.value,
            escalation_style=EscalationStyle.DIRECT.value,
            degraded_mode_behavior=DegradedModeBehavior.CONSULTATIVE.value,
            max_execution_latency_ms=5000,
            requires_online=False,
            offline_fallback_allowed=True,
        ),
        DeploymentRole.EDUCATION.value: DeploymentRoleProfile(
            role=DeploymentRole.EDUCATION.value,
            name="Education",
            description="Academic environments, curriculum delivery, student support, assessment.",
            communication_posture=CommunicationPosture.EXPLORATORY.value,
            evidence_strictness=EvidenceStrictness.MODERATE.value,
            minimum_evidence_confidence=0.65,
            caution_level=CautionLevel.NORMAL.value,
            initiative_level=InitiativeLevel.MODERATE.value,
            explanation_density=ExplanationDensity.ENHANCED.value,
            escalation_style=EscalationStyle.GRADUAL.value,
            degraded_mode_behavior=DegradedModeBehavior.FALLBACK.value,
            max_execution_latency_ms=15000,
            requires_online=False,
            offline_fallback_allowed=True,
        ),
        DeploymentRole.HOSPITALS_MEDICINE.value: DeploymentRoleProfile(
            role=DeploymentRole.HOSPITALS_MEDICINE.value,
            name="Hospitals & Medicine",
            description="Clinical care, diagnostics, treatment planning, patient safety.",
            communication_posture=CommunicationPosture.DIAGNOSTIC.value,
            evidence_strictness=EvidenceStrictness.MAXIMUM.value,
            minimum_evidence_confidence=0.9,
            caution_level=CautionLevel.MAXIMUM.value,
            initiative_level=InitiativeLevel.NONE.value,
            explanation_density=ExplanationDensity.MAXIMUM.value,
            escalation_style=EscalationStyle.DIRECT.value,
            degraded_mode_behavior=DegradedModeBehavior.SILENT.value,
            max_execution_latency_ms=2000,
            requires_online=True,
            offline_fallback_allowed=False,
        ),
        DeploymentRole.SCIENCE_RESEARCH.value: DeploymentRoleProfile(
            role=DeploymentRole.SCIENCE_RESEARCH.value,
            name="Science & Research",
            description="Experimental design, data analysis, hypothesis testing, publication.",
            communication_posture=CommunicationPosture.EXPLORATORY.value,
            evidence_strictness=EvidenceStrictness.HIGH.value,
            minimum_evidence_confidence=0.75,
            caution_level=CautionLevel.NORMAL.value,
            initiative_level=InitiativeLevel.HIGH.value,
            explanation_density=ExplanationDensity.ENHANCED.value,
            escalation_style=EscalationStyle.GRADUAL.value,
            degraded_mode_behavior=DegradedModeBehavior.CONSULTATIVE.value,
            max_execution_latency_ms=30000,
            requires_online=True,
            offline_fallback_allowed=True,
        ),
        DeploymentRole.INDUSTRY.value: DeploymentRoleProfile(
            role=DeploymentRole.INDUSTRY.value,
            name="Industry",
            description="Manufacturing, process control, maintenance, supply chain.",
            communication_posture=CommunicationPosture.PRESCRIPTIVE.value,
            evidence_strictness=EvidenceStrictness.HIGH.value,
            minimum_evidence_confidence=0.7,
            caution_level=CautionLevel.ELEVATED.value,
            initiative_level=InitiativeLevel.MODERATE.value,
            explanation_density=ExplanationDensity.STANDARD.value,
            escalation_style=EscalationStyle.GRADUAL.value,
            degraded_mode_behavior=DegradedModeBehavior.FALLBACK.value,
            max_execution_latency_ms=1000,
            requires_online=False,
            offline_fallback_allowed=True,
        ),
        DeploymentRole.AEROSPACE_LONG_MISSION.value: DeploymentRoleProfile(
            role=DeploymentRole.AEROSPACE_LONG_MISSION.value,
            name="Aerospace & Long-Mission",
            description="Spaceflight, deep-space operations, long-duration autonomy.",
            communication_posture=CommunicationPosture.DIAGNOSTIC.value,
            evidence_strictness=EvidenceStrictness.MAXIMUM.value,
            minimum_evidence_confidence=0.85,
            caution_level=CautionLevel.MAXIMUM.value,
            initiative_level=InitiativeLevel.LOW.value,
            explanation_density=ExplanationDensity.MINIMAL.value,
            escalation_style=EscalationStyle.GRADUAL.value,
            degraded_mode_behavior=DegradedModeBehavior.FALLBACK.value,
            max_execution_latency_ms=5000,
            requires_online=False,
            offline_fallback_allowed=False,  # Must be autonomous
        ),
    }


# ============================================================================
# DEPLOYMENT PERSONA ENGINE
# ============================================================================


class DeploymentPersonaEngine:
    """Engine for managing deployment personas and behavior adaptation.
    
    Provides transparent, reversible role-based adaptation.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize deployment persona engine."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/deployment_persona/"
        self.role_profiles: Dict[str, DeploymentRoleProfile] = {}
        self.active_contexts: Dict[str, DeploymentContext] = {}  # context_id -> Context
        self._load_profiles()
        self._ensure_storage_exists()
        self._load_contexts()
    
    def _load_profiles(self) -> None:
        """Load role profiles from registry."""
        registry = get_deployment_role_registry()
        self.role_profiles = registry
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_contexts(self) -> None:
        """Load active contexts from storage."""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith("_deployment_context.json"):
                context_id = filename[:-27]  # Remove _deployment_context.json
                try:
                    with open(os.path.join(self.storage_path, filename), "r") as f:
                        data = json.load(f)
                        self.active_contexts[context_id] = DeploymentContext.from_dict(data)
                except Exception:
                    continue
    
    def _save_context(self, context_id: str) -> None:
        """Save a context to storage."""
        import os
        filepath = os.path.join(self.storage_path, f"{context_id}_deployment_context.json")
        data = self.active_contexts[context_id].to_dict()
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def create_role_profile(
        self,
        role: str,
        name: str,
        description: str,
        communication_posture: str = CommunicationPosture.ADVISORY.value,
        evidence_strictness: str = EvidenceStrictness.MODERATE.value,
        minimum_evidence_confidence: float = 0.6,
        caution_level: str = CautionLevel.NORMAL.value,
        initiative_level: str = InitiativeLevel.MODERATE.value,
        explanation_density: str = ExplanationDensity.STANDARD.value,
        escalation_style: str = EscalationStyle.GRADUAL.value,
        degraded_mode_behavior: str = DegradedModeBehavior.CONSULTATIVE.value,
        author: Optional[str] = None,
    ) -> DeploymentRoleProfile:
        """Create a custom role profile."""
        profile = DeploymentRoleProfile(
            role=role,
            name=name,
            description=description,
            communication_posture=communication_posture,
            evidence_strictness=evidence_strictness,
            minimum_evidence_confidence=minimum_evidence_confidence,
            caution_level=caution_level,
            initiative_level=initiative_level,
            explanation_density=explanation_density,
            escalation_style=escalation_style,
            degraded_mode_behavior=degraded_mode_behavior,
            author=author,
        )
        self.role_profiles[role] = profile
        return profile
    
    def get_role_profile(self, role: str) -> Optional[DeploymentRoleProfile]:
        """Get a role profile by name."""
        return self.role_profiles.get(role)
    
    def get_default_role_profile(self) -> DeploymentRoleProfile:
        """Get the default role profile (create if needed)."""
        default_role = DeploymentRole.HOME_FAMILY.value
        if default_role not in self.role_profiles:
            return self.create_role_profile(default_role, "Default", "Default deployment role")
        return self.role_profiles[default_role]
    
    def set_active_context(
        self,
        context_id: str,
        role: str,
        role_profile_id: Optional[str] = None,
        evidence_confidence_override: Optional[float] = None,
        caution_override: Optional[str] = None,
        initiative_override: Optional[str] = None,
        application_scope: List[str] = None,
        author: Optional[str] = None,
    ) -> DeploymentContext:
        """Set the active deployment context."""
        context = DeploymentContext(
            context_id=context_id,
            role=role,
            role_profile_id=role_profile_id,
            evidence_confidence_override=evidence_confidence_override,
            caution_override=caution_override,
            initiative_override=initiative_override,
            application_scope=application_scope or [],
            author=author,
        )
        self.active_contexts[context_id] = context
        self._save_context(context_id)
        return context
    
    def get_active_context(self, context_id: str) -> Optional[DeploymentContext]:
        """Get an active context by ID."""
        return self.active_contexts.get(context_id)
    
    def get_default_context(self) -> DeploymentContext:
        """Get the default deployment context (create if needed)."""
        if "default" not in self.active_contexts:
            return self.set_active_context("default", DeploymentRole.HOME_FAMILY.value)
        return self.active_contexts["default"]
    
    def compute_behavior_adaptation(self, context_id: str) -> RoleBehaviorAdaptation:
        """Compute behavior adaptation for active context."""
        context = self.get_active_context(context_id)
        if not context:
            context = self.get_default_context()
        
        # Get role profile
        profile = self.get_role_profile(context.role)
        if not profile:
            profile = self.get_default_role_profile()
        
        # Apply overrides
        evidence_confidence = (
            context.evidence_confidence_override
            if context.evidence_confidence_override is not None
            else profile.minimum_evidence_confidence
        )
        
        caution = (
            context.caution_override
            if context.caution_override is not None
            else profile.caution_level
        )
        
        initiative = (
            context.initiative_override
            if context.initiative_override is not None
            else profile.initiative_level
        )
        
        return RoleBehaviorAdaptation(
            role=context.role,
            effective_communication_posture=context.communication_posture if hasattr(context, 'communication_posture') else profile.communication_posture,
            effective_evidence_strictness=context.evidence_strictness if hasattr(context, 'evidence_strictness') else profile.evidence_strictness,
            effective_caution_level=caution,
            effective_initiative_level=initiative,
            effective_explanation_density=context.explanation_density if hasattr(context, 'explanation_density') else profile.explanation_density,
            effective_escalation_style=context.escalation_style if hasattr(context, 'escalation_style') else profile.escalation_style,
            effective_degraded_mode_behavior=context.degraded_mode_behavior if hasattr(context, 'degraded_mode_behavior') else profile.degraded_mode_behavior,
            minimum_evidence_confidence=evidence_confidence,
            max_single_step_confidence=profile.max_single_step_confidence,
            max_suggestions_per_session=profile.max_suggestions_per_session,
            can_be_proactive=initiative in [InitiativeLevel.LOW.value, InitiativeLevel.MODERATE.value, InitiativeLevel.HIGH.value, InitiativeLevel.MAXIMUM.value],
            requires_explanation=context.explanation_density if hasattr(context, 'explanation_density') else profile.explanation_density in [ExplanationDensity.ENHANCED.value, ExplanationDensity.MAXIMUM.value],
            min_explanation_length=profile.min_explanation_length,
            escalation_delay_ms=self._compute_escalation_delay(caution, profile.escalation_style),
            computed_by="deployment_persona_layer_v39",
        )
    
    def _compute_escalation_delay(self, caution: str, escalation_style: str) -> int:
        """Compute delay before escalation based on caution and style."""
        base_delay = 1000  # 1 second base
        
        # Caution multiplier
        caution_multiplier = {
            CautionLevel.MINIMAL.value: 1,
            CautionLevel.NORMAL.value: 1,
            CautionLevel.ELEVATED.value: 2,
            CautionLevel.MAXIMUM.value: 3,
        }.get(caution, 1)
        
        # Escalation style modifier
        style_modifier = {
            EscalationStyle.DIRECT.value: 0,
            EscalationStyle.GRADUAL.value: 2,
            EscalationStyle.HESITANT.value: 3,
        }.get(escalation_style, 1)
        
        return base_delay * caution_multiplier * style_modifier
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "role_profile_count": len(self.role_profiles),
            "active_context_count": len(self.active_contexts),
            "role_profiles": {k: v.to_dict() for k, v in self.role_profiles.items()},
            "active_contexts": {k: v.to_dict() for k, v in self.active_contexts.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any], role_engine: DeploymentPersonaEngine = None, context_id: str = None) -> Dict[str, Any]:
    """Add deployment role context to adaptive guidance.
    
    This is purely additive — no migration required.
    
    v39: Role-based evidence strictness and caution levels influence
    guidance confidence thresholds and recommendation strength.
    """
    if "deployment_role_context" not in guidance_dict:
        guidance_dict["deployment_role_context"] = None
    
    if role_engine and context_id:
        try:
            adaptation = role_engine.compute_behavior_adaptation(context_id)
            guidance_dict["deployment_role_context"] = {
                "role": adaptation.role,
                "effective_evidence_strictness": adaptation.effective_evidence_strictness,
                "effective_caution_level": adaptation.effective_caution_level,
                "minimum_evidence_confidence": adaptation.minimum_evidence_confidence,
                "max_suggestions_per_session": adaptation.max_suggestions_per_session,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return guidance_dict


def integrate_with_narrative(narrative_dict: Dict[str, Any], role_engine: DeploymentPersonaEngine = None, context_id: str = None) -> Dict[str, Any]:
    """Add deployment role context to narrative generation.
    
    This is purely additive — no migration required.
    
    v39: Role-based explanation density influences narrative detail level.
    """
    if "deployment_role_context" not in narrative_dict:
        narrative_dict["deployment_role_context"] = None
    
    if role_engine and context_id:
        try:
            adaptation = role_engine.compute_behavior_adaptation(context_id)
            narrative_dict["deployment_role_context"] = {
                "role": adaptation.role,
                "effective_explanation_density": adaptation.effective_explanation_density,
                "requires_explanation": adaptation.requires_explanation,
                "min_explanation_length": adaptation.min_explanation_length,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return narrative_dict


def integrate_with_domain_ontology(domain_dict: Dict[str, Any], role_engine: DeploymentPersonaEngine = None, context_id: str = None) -> Dict[str, Any]:
    """Add deployment role context to domain ontology.
    
    This is purely additive — no migration required.
    
    v39: Role-based evidence strictness influences domain evidence thresholds.
    """
    if "deployment_role_context" not in domain_dict:
        domain_dict["deployment_role_context"] = None
    
    if role_engine and context_id:
        try:
            adaptation = role_engine.compute_behavior_adaptation(context_id)
            domain_dict["deployment_role_context"] = {
                "role": adaptation.role,
                "effective_evidence_strictness": adaptation.effective_evidence_strictness,
                "minimum_evidence_confidence": adaptation.minimum_evidence_confidence,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return domain_dict


def integrate_with_trust_dynamics(trust_dict: Dict[str, Any], role_engine: DeploymentPersonaEngine = None, context_id: str = None) -> Dict[str, Any]:
    """Add deployment role context to trust dynamics.
    
    This is purely additive — no migration required.
    
    v39: Role-based initiative level influences proactivity in trust management.
    """
    if "deployment_role_context" not in trust_dict:
        trust_dict["deployment_role_context"] = None
    
    if role_engine and context_id:
        try:
            adaptation = role_engine.compute_behavior_adaptation(context_id)
            trust_dict["deployment_role_context"] = {
                "role": adaptation.role,
                "effective_initiative_level": adaptation.effective_initiative_level,
                "can_be_proactive": adaptation.can_be_proactive,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return trust_dict


def integrate_with_intervention_timing(timing_dict: Dict[str, Any], role_engine: DeploymentPersonaEngine = None, context_id: str = None) -> Dict[str, Any]:
    """Add deployment role context to intervention timing.
    
    This is purely additive — no migration required.
    
    v39: Role-based escalation style influences timing delays.
    """
    if "deployment_role_context" not in timing_dict:
        timing_dict["deployment_role_context"] = None
    
    if role_engine and context_id:
        try:
            adaptation = role_engine.compute_behavior_adaptation(context_id)
            timing_dict["deployment_role_context"] = {
                "role": adaptation.role,
                "effective_escalation_style": adaptation.effective_escalation_style,
                "escalation_delay_ms": adaptation.escalation_delay_ms,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return timing_dict
