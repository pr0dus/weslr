# policy_profile.py - WESLR v49: Policy / Governance Profile Layer
# Creates a governed policy profile layer so WESLR can apply coherent strictness,
# evidence, escalation, explanation, and proactive-behavior rules by deployment context
# without scattering those decisions across modules.
# Additive only, transparent, reversible, role-aware, non-manipulative.
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


class StrictnessLevel(str, Enum):
    """Strictness level for policy rules."""
    PERMISSIVE = "permissive"  # Allow most actions, minimal checks
    MODERATE = "moderate"  # Standard checks, balanced approach
    STRICT = "strict"  # Significant checks, conservative approach
    MAXIMUM = "maximum"  # Maximum checks, extremely conservative


class EvidenceStrictness(str, Enum):
    """Evidence strictness level."""
    MINIMAL = "minimal"  # Low confidence acceptable
    MODERATE = "moderate"  # Standard confidence required
    HIGH = "high"  # High confidence required
    MAXIMUM = "maximum"  # Very high confidence, validated only


class EscalationStrictness(str, Enum):
    """Escalation strictness level."""
    RARELY = "rarely"  # Only truly critical escalations
    OCCASIONALLY = "occasionally"  # Some escalations
    FREQUENTLY = "frequently"  # Many escalations
    ALWAYS = "always"  # All uncertain situations escalate


class ExplanationRequirement(str, Enum):
    """Explanation requirement level."""
    NONE = "none"  # No explanation needed
    MINIMAL = "minimal"  # Brief explanation
    STANDARD = "standard"  # Balanced explanation
    ENHANCED = "enhanced"  # Detailed reasoning
    EXHAUSTIVE = "exhaustive"  # Multiple angles, chain of thought


class ProactiveBehaviorLevel(str, Enum):
    """Proactive guidance limits."""
    NONE = "none"  # Only respond to explicit requests
    LOW = "low"  # Minimal proactive suggestions
    MODERATE = "moderate"  # Standard proactive behavior
    HIGH = "high"  # Aggressive suggestion generation
    MAXIMUM = "maximum"  # Full autonomy within bounds


class HoldBackSensitivity(str, Enum):
    """Sensitivity for holding back on actions."""
    LOW = "low"  # Minimal hold-back, direct action
    MODERATE = "moderate"  # Some caution, balanced approach
    HIGH = "high"  # Significant hold-back, more checks
    MAXIMUM = "maximum"  # Maximum hold-back, extensive validation


class AuditStrictness(str, Enum):
    """Audit trail strictness."""
    MINIMAL = "minimal"  # Basic audit, essential events only
    STANDARD = "standard"  # Standard audit coverage
    ENHANCED = "enhanced"  # Detailed audit, significant events
    MAXIMUM = "maximum"  # Maximum audit, all events tracked


class DegradedModeBehavior(str, Enum):
    """Behavior when in degraded mode."""
    CONTINUE_WITH_LIMITS = "continue_with_limits"  # Continue with reduced capabilities
    PAUSE = "pause"  # Pause operations until restored
    FALLBACK = "fallback"  # Use fallback mode
    SHUTDOWN = "shutdown"  # Full shutdown, manual intervention required


# ============================================================================
# POLICY PROFILE MODEL
# ============================================================================


@dataclass
class PolicyProfile:
    """Governance policy profile for a deployment context.
    
    Defines coherent rules for strictness, evidence, escalation,
    explanation, and proactive behavior across all governance layers.
    """
    
    profile_id: str
    deployment_context: str  # e.g., "home_family", "industry", "science_research"
    
    # Strictness controls
    evidence_strictness: str = EvidenceStrictness.MODERATE.value
    safety_strictness: str = StrictnessLevel.MODERATE.value
    escalation_strictness: str = EscalationStrictness.FREQUENTLY.value
    explanation_requirement: str = ExplanationRequirement.STANDARD.value
    proactive_behavior_limit: str = ProactiveBehaviorLevel.MODERATE.value
    hold_back_sensitivity: str = HoldBackSensitivity.MODERATE.value
    audit_strictness: str = AuditStrictness.STANDARD.value
    
    # Degraded mode behavior
    degraded_mode_behavior: str = DegradedModeBehavior.CONTINUE_WITH_LIMITS.value
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    description: Optional[str] = None
    
    # Predefined profiles for common contexts
    @staticmethod
    def create_home_family() -> PolicyProfile:
        """Create a policy profile for home/family deployment."""
        return PolicyProfile(
            profile_id="profile_home_family",
            deployment_context="home_family",
            evidence_strictness=EvidenceStrictness.HIGH.value,
            safety_strictness=StrictnessLevel.STRICT.value,
            escalation_strictness=EscalationStrictness.ALWAYS.value,
            explanation_requirement=ExplanationRequirement.ENHANCED.value,
            proactive_behavior_limit=ProactiveBehaviorLevel.LOW.value,
            hold_back_sensitivity=HoldBackSensitivity.HIGH.value,
            audit_strictness=AuditStrictness.MAXIMUM.value,
            degraded_mode_behavior=DegradedModeBehavior.PAUSE.value,
            description="Home/Family deployment: highest safety and explanation standards",
        )
    
    @staticmethod
    def create_education() -> PolicyProfile:
        """Create a policy profile for education deployment."""
        return PolicyProfile(
            profile_id="profile_education",
            deployment_context="education",
            evidence_strictness=EvidenceStrictness.MODERATE.value,
            safety_strictness=StrictnessLevel.MODERATE.value,
            escalation_strictness=EscalationStrictness.OCCASIONALLY.value,
            explanation_requirement=ExplanationRequirement.STANDARD.value,
            proactive_behavior_limit=ProactiveBehaviorLevel.MODERATE.value,
            hold_back_sensitivity=HoldBackSensitivity.MODERATE.value,
            audit_strictness=AuditStrictness.STANDARD.value,
            degraded_mode_behavior=DegradedModeBehavior.CONTINUE_WITH_LIMITS.value,
            description="Education deployment: balanced safety and educational value",
        )
    
    @staticmethod
    def create_hospitals_medicine() -> PolicyProfile:
        """Create a policy profile for hospitals/medicine deployment."""
        return PolicyProfile(
            profile_id="profile_hospitals_medicine",
            deployment_context="hospitals_medicine",
            evidence_strictness=EvidenceStrictness.MAXIMUM.value,
            safety_strictness=StrictnessLevel.MAXIMUM.value,
            escalation_strictness=EscalationStrictness.ALWAYS.value,
            explanation_requirement=ExplanationRequirement.EXHAUSTIVE.value,
            proactive_behavior_limit=ProactiveBehaviorLevel.NONE.value,
            hold_back_sensitivity=HoldBackSensitivity.MAXIMUM.value,
            audit_strictness=AuditStrictness.MAXIMUM.value,
            degraded_mode_behavior=DegradedModeBehavior.SHUTDOWN.value,
            description="Hospital/Medicine deployment: maximum safety and audit requirements",
        )
    
    @staticmethod
    def create_science_research() -> PolicyProfile:
        """Create a policy profile for science research deployment."""
        return PolicyProfile(
            profile_id="profile_science_research",
            deployment_context="science_research",
            evidence_strictness=EvidenceStrictness.MODERATE.value,
            safety_strictness=StrictnessLevel.MODERATE.value,
            escalation_strictness=EscalationStrictness.RARELY.value,
            explanation_requirement=ExplanationRequirement.MINIMAL.value,
            proactive_behavior_limit=ProactiveBehaviorLevel.MAXIMUM.value,
            hold_back_sensitivity=HoldBackSensitivity.LOW.value,
            audit_strictness=AuditStrictness.STANDARD.value,
            degraded_mode_behavior=DegradedModeBehavior.CONTINUE_WITH_LIMITS.value,
            description="Science Research deployment: maximum autonomy for exploration",
        )
    
    @staticmethod
    def create_industry() -> PolicyProfile:
        """Create a policy profile for industry deployment."""
        return PolicyProfile(
            profile_id="profile_industry",
            deployment_context="industry",
            evidence_strictness=EvidenceStrictness.HIGH.value,
            safety_strictness=StrictnessLevel.STRICT.value,
            escalation_strictness=EscalationStrictness.FREQUENTLY.value,
            explanation_requirement=ExplanationRequirement.STANDARD.value,
            proactive_behavior_limit=ProactiveBehaviorLevel.LOW.value,
            hold_back_sensitivity=HoldBackSensitivity.HIGH.value,
            audit_strictness=AuditStrictness.ENHANCED.value,
            degraded_mode_behavior=DegradedModeBehavior.PAUSE.value,
            description="Industry deployment: balanced safety and operational efficiency",
        )
    
    @staticmethod
    def create_aerospace_long_mission() -> PolicyProfile:
        """Create a policy profile for aerospace long mission deployment."""
        return PolicyProfile(
            profile_id="profile_aerospace_long_mission",
            deployment_context="aerospace_long_mission",
            evidence_strictness=EvidenceStrictness.MAXIMUM.value,
            safety_strictness=StrictnessLevel.MAXIMUM.value,
            escalation_strictness=EscalationStrictness.ALWAYS.value,
            explanation_requirement=ExplanationRequirement.EXHAUSTIVE.value,
            proactive_behavior_limit=ProactiveBehaviorLevel.HIGH.value,
            hold_back_sensitivity=HoldBackSensitivity.MAXIMUM.value,
            audit_strictness=AuditStrictness.MAXIMUM.value,
            degraded_mode_behavior=DegradedModeBehavior.FALLBACK.value,
            description="Aerospace Long Mission: maximum safety and autonomy within constraints",
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert policy profile to dictionary."""
        return {
            "profile_id": self.profile_id,
            "deployment_context": self.deployment_context,
            "evidence_strictness": self.evidence_strictness,
            "safety_strictness": self.safety_strictness,
            "escalation_strictness": self.escalation_strictness,
            "explanation_requirement": self.explanation_requirement,
            "proactive_behavior_limit": self.proactive_behavior_limit,
            "hold_back_sensitivity": self.hold_back_sensitivity,
            "audit_strictness": self.audit_strictness,
            "degraded_mode_behavior": self.degraded_mode_behavior,
            "created_at": self.created_at,
            "author": self.author,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PolicyProfile:
        """Create policy profile from dictionary."""
        data.setdefault("evidence_strictness", EvidenceStrictness.MODERATE.value)
        data.setdefault("safety_strictness", StrictnessLevel.MODERATE.value)
        data.setdefault("escalation_strictness", EscalationStrictness.FREQUENTLY.value)
        data.setdefault("explanation_requirement", ExplanationRequirement.STANDARD.value)
        data.setdefault("proactive_behavior_limit", ProactiveBehaviorLevel.MODERATE.value)
        data.setdefault("hold_back_sensitivity", HoldBackSensitivity.MODERATE.value)
        data.setdefault("audit_strictness", AuditStrictness.STANDARD.value)
        data.setdefault("degraded_mode_behavior", DegradedModeBehavior.CONTINUE_WITH_LIMITS.value)
        data.setdefault("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        return cls(**data)
    
    @classmethod
    def create_for_context(cls, context_name: str) -> Optional[PolicyProfile]:
        """Create a predefined policy profile for a deployment context."""
        context_map = {
            "home_family": cls.create_home_family,
            "education": cls.create_education,
            "hospitals_medicine": cls.create_hospitals_medicine,
            "science_research": cls.create_science_research,
            "industry": cls.create_industry,
            "aerospace_long_mission": cls.create_aerospace_long_mission,
        }
        factory = context_map.get(context_name)
        if factory:
            return factory()
        return None


# ============================================================================
# POLICY PROFILE ENGINE
# ============================================================================


class PolicyProfileEngine:
    """Engine for managing policy profiles across governance layers.
    
    Provides transparent, reversible policy enforcement.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize policy profile engine."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/policy_profile/"
        self.profiles: Dict[str, PolicyProfile] = {}
        self.active_profile_id: Optional[str] = None
        self._ensure_storage_exists()
        self._load_profiles()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_profiles(self) -> None:
        """Load profiles from storage."""
        import os
        import glob
        
        if not os.path.exists(self.storage_path):
            return
        
        for filepath in glob.glob(os.path.join(self.storage_path, "*.json")):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    profile = PolicyProfile.from_dict(data)
                    self.profiles[profile.profile_id] = profile
                    if data.get("active"):
                        self.active_profile_id = profile.profile_id
            except Exception:
                continue
    
    def create_profile(self, profile: PolicyProfile, active: bool = False) -> PolicyProfile:
        """Create a new policy profile."""
        self.profiles[profile.profile_id] = profile
        if active:
            self.active_profile_id = profile.profile_id
        self._save_profile(profile)
        return profile
    
    def get_profile(self, profile_id: str) -> Optional[PolicyProfile]:
        """Get a policy profile by ID."""
        return self.profiles.get(profile_id)
    
    def get_active_profile(self) -> Optional[PolicyProfile]:
        """Get the currently active policy profile."""
        if self.active_profile_id:
            return self.profiles.get(self.active_profile_id)
        # Default to home_family if no active profile
        if not self.profiles:
            return PolicyProfile.create_home_family()
        # Return first profile as default
        return next(iter(self.profiles.values()), None)
    
    def set_active_profile(self, profile_id: str) -> bool:
        """Set the active policy profile."""
        if profile_id in self.profiles:
            self.active_profile_id = profile_id
            # Update active flag in saved file
            profile = self.profiles[profile_id]
            self._save_profile(profile)
            return True
        return False
    
    def _save_profile(self, profile: PolicyProfile) -> None:
        """Save a policy profile to storage."""
        import os
        
        data = profile.to_dict()
        data["active"] = (self.active_profile_id == profile.profile_id)
        filepath = os.path.join(self.storage_path, f"{profile.profile_id}.json")
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_policy_for_context(self, context_name: str) -> PolicyProfile:
        """Get or create a policy profile for a deployment context."""
        profile = self.get_profile(context_name)
        if not profile:
            profile = PolicyProfile.create_for_context(context_name)
            if profile:
                self.profiles[profile.profile_id] = profile
        return profile or PolicyProfile.create_home_family()
    
    def check_strictness(self, policy: PolicyProfile, category: str) -> str:
        """Check the strictness level for a policy category."""
        strictness_map = {
            "evidence": policy.evidence_strictness,
            "safety": policy.safety_strictness,
            "escalation": policy.escalation_strictness,
            "explanation": policy.explanation_requirement,
            "proactive": policy.proactive_behavior_limit,
            "holdback": policy.hold_back_sensitivity,
            "audit": policy.audit_strictness,
        }
        return strictness_map.get(category, "moderate")
    
    def get_degraded_mode_behavior(self, policy: PolicyProfile) -> str:
        """Get the degraded mode behavior for a policy."""
        return policy.degraded_mode_behavior
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "profile_count": len(self.profiles),
            "active_profile_id": self.active_profile_id,
            "profiles": {k: v.to_dict() for k, v in self.profiles.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_deployment_persona(
    persona_dict: Dict[str, Any],
    profile: PolicyProfile = None,
) -> Dict[str, Any]:
    """Add policy profile context to deployment persona.
    
    This is purely additive — no migration required.
    
    v49: Policy profile provides governance context for deployment roles.
    """
    if "policy_context" not in persona_dict:
        persona_dict["policy_context"] = None
    
    if profile:
        persona_dict["policy_context"] = {
            "profile_id": profile.profile_id,
            "deployment_context": profile.deployment_context,
            "evidence_strictness": profile.evidence_strictness,
            "safety_strictness": profile.safety_strictness,
            "escalation_strictness": profile.escalation_strictness,
            "explanation_requirement": profile.explanation_requirement,
            "proactive_behavior_limit": profile.proactive_behavior_limit,
            "hold_back_sensitivity": profile.hold_back_sensitivity,
            "audit_strictness": profile.audit_strictness,
            "degraded_mode_behavior": profile.degraded_mode_behavior,
        }
    
    return persona_dict


def integrate_with_capability_boundary(
    capability_dict: Dict[str, Any],
    profile: PolicyProfile = None,
) -> Dict[str, Any]:
    """Add policy profile context to capability boundary.
    
    This is purely additive — no migration required.
    
    v49: Policy profile defines capability strictness per deployment context.
    """
    if "policy_context" not in capability_dict:
        capability_dict["policy_context"] = None
    
    if profile:
        capability_dict["policy_context"] = {
            "safety_strictness": profile.safety_strictness,
            "hold_back_sensitivity": profile.hold_back_sensitivity,
            "audit_strictness": profile.audit_strictness,
        }
    
    return capability_dict


def integrate_with_proof_gate(
    proof_dict: Dict[str, Any],
    profile: PolicyProfile = None,
) -> Dict[str, Any]:
    """Add policy profile context to proof gate.
    
    This is purely additive — no migration required.
    
    v49: Policy profile determines evidence and explanation requirements.
    """
    if "policy_context" not in proof_dict:
        proof_dict["policy_context"] = None
    
    if profile:
        proof_dict["policy_context"] = {
            "evidence_strictness": profile.evidence_strictness,
            "explanation_requirement": profile.explanation_requirement,
            "audit_strictness": profile.audit_strictness,
        }
    
    return proof_dict


def integrate_with_escalation(
    escalation_dict: Dict[str, Any],
    profile: PolicyProfile = None,
) -> Dict[str, Any]:
    """Add policy profile context to escalation layer.
    
    This is purely additive — no migration required.
    
    v49: Policy profile defines escalation strictness.
    """
    if "policy_context" not in escalation_dict:
        escalation_dict["policy_context"] = None
    
    if profile:
        escalation_dict["policy_context"] = {
            "escalation_strictness": profile.escalation_strictness,
            "degraded_mode_behavior": profile.degraded_mode_behavior,
        }
    
    return escalation_dict


def integrate_with_governance_surface(
    governance_dict: Dict[str, Any],
    profile: PolicyProfile = None,
) -> Dict[str, Any]:
    """Add policy profile context to governance surface.
    
    This is purely additive — no migration required.
    
    v49: Policy profile provides coherent governance across all layers.
    """
    if "policy_context" not in governance_dict:
        governance_dict["policy_context"] = None
    
    if profile:
        governance_dict["policy_context"] = {
            "profile_id": profile.profile_id,
            "deployment_context": profile.deployment_context,
            "all_strictness_levels": {
                "evidence": profile.evidence_strictness,
                "safety": profile.safety_strictness,
                "escalation": profile.escalation_strictness,
                "explanation": profile.explanation_requirement,
                "proactive": profile.proactive_behavior_limit,
                "holdback": profile.hold_back_sensitivity,
                "audit": profile.audit_strictness,
            },
            "degraded_mode_behavior": profile.degraded_mode_behavior,
        }
    
    return governance_dict
