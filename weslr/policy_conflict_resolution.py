# policy_conflict_resolution.py - WESLR v50: Policy Conflict Resolution / Override Logic
# Creates a governed precedence/override layer so WESLR can resolve conflicts between
# invariants, safety contracts, capability boundaries, policy profiles, deployment persona,
# domain context, trust/timing softness, and user/household preference layers.
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


class PrecedenceLevel(str, Enum):
    """Precedence level for rule application."""
    LOW = "low"  # Base rules, easily overridden
    MEDIUM = "medium"  # Standard precedence
    HIGH = "high"  # Strong precedence
    SUPREME = "supreme"  # Maximum precedence, rarely overridden


class OverrideType(str, Enum):
    """Type of override behavior."""
    NONE = "none"  # No override, original rule applies
    SOFT = "soft"  # Recommended override, can be bypassed with justification
    BLOCKING = "blocking"  # Hard override, requires explicit override to bypass


class ConflictContext(str, Enum):
    """Context where conflict arises."""
    POLICY_PROFILE_VS_DEPLOYMENT = "policy_profile_vs_deployment"
    POLICY_PROFILE_VS_INVARIANT = "policy_profile_vs_invariant"
    POLICY_PROFILE_VS_CAPABILITY = "policy_profile_vs_capability"
    DEPLOYMENT_VS_INVARIANT = "deployment_vs_invariant"
    DEPLOYMENT_VS_CAPABILITY = "deployment_vs_capability"
    INVARIANT_VS_CAPABILITY = "invariant_vs_capability"
    USER_PREFERENCE_VS_POLICY = "user_preference_vs_policy"
    HOUSEHOLD_VS_POLICY = "household_vs_policy"
    TRUST_VS_POLICY = "trust_vs_policy"
    DOMAIN_VS_POLICY = "domain_vs_policy"
    GENERAL = "general"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class RuleSource:
    """Source of a policy rule."""
    
    source_type: str  # e.g., "policy_profile", "deployment_persona", "invariant", "user"
    source_id: str  # e.g., "profile_home_family", "deployment_role_home"
    source_context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_context": self.source_context,
        }


@dataclass
class ConflictRule:
    """A rule involved in a conflict resolution."""
    
    rule_id: str
    rule_type: str  # e.g., "safety_strictness", "escalation_strictness"
    rule_value: str
    precedence_level: str = PrecedenceLevel.MEDIUM.value
    override_type: str = OverrideType.NONE.value
    source: Optional[RuleSource] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "rule_value": self.rule_value,
            "precedence_level": self.precedence_level,
            "override_type": self.override_type,
            "source": self.source.to_dict() if self.source else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConflictRule:
        data.setdefault("precedence_level", PrecedenceLevel.MEDIUM.value)
        data.setdefault("override_type", OverrideType.NONE.value)
        return cls(**data)


@dataclass
class ConflictResolution:
    """Resolved conflict with governing rule and explanation."""
    
    conflict_id: str
    conflict_context: str
    competing_rules: List[Dict[str, Any]]
    governing_rule: Dict[str, Any]
    overriding_rule: Optional[Dict[str, Any]]
    resolved_value: str
    explanation: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "conflict_context": self.conflict_context,
            "competing_rules": self.competing_rules,
            "governing_rule": self.governing_rule,
            "overriding_rule": self.overriding_rule,
            "resolved_value": self.resolved_value,
            "explanation": self.explanation,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConflictResolution:
        data.setdefault("timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        return cls(**data)


# ============================================================================
# OVERRIDE PRIORITY TABLE
# ============================================================================


OVERRIDE_PRIORITY_TABLE = {
    "invariant": {
        "policy_profile": PrecedenceLevel.SUPREME.value,
        "deployment_persona": PrecedenceLevel.SUPREME.value,
        "capability_boundary": PrecedenceLevel.SUPREME.value,
        "user_preference": PrecedenceLevel.HIGH.value,
        "household_preference": PrecedenceLevel.HIGH.value,
        "domain_context": PrecedenceLevel.MEDIUM.value,
        "trust_softness": PrecedenceLevel.LOW.value,
    },
    "policy_profile": {
        "deployment_persona": PrecedenceLevel.MEDIUM.value,
        "capability_boundary": PrecedenceLevel.MEDIUM.value,
        "user_preference": PrecedenceLevel.LOW.value,
        "household_preference": PrecedenceLevel.LOW.value,
        "domain_context": PrecedenceLevel.MEDIUM.value,
        "trust_softness": PrecedenceLevel.LOW.value,
    },
    "deployment_persona": {
        "capability_boundary": PrecedenceLevel.MEDIUM.value,
        "user_preference": PrecedenceLevel.LOW.value,
        "household_preference": PrecedenceLevel.LOW.value,
        "domain_context": PrecedenceLevel.MEDIUM.value,
        "trust_softness": PrecedenceLevel.LOW.value,
    },
    "capability_boundary": {
        "user_preference": PrecedenceLevel.LOW.value,
        "household_preference": PrecedenceLevel.LOW.value,
        "domain_context": PrecedenceLevel.LOW.value,
        "trust_softness": PrecedenceLevel.LOW.value,
    },
    "user_preference": {
        "household_preference": PrecedenceLevel.LOW.value,
        "domain_context": PrecedenceLevel.LOW.value,
        "trust_softness": PrecedenceLevel.LOW.value,
    },
    "household_preference": {
        "domain_context": PrecedenceLevel.MEDIUM.value,
        "trust_softness": PrecedenceLevel.LOW.value,
    },
    "domain_context": {
        "trust_softness": PrecedenceLevel.LOW.value,
    },
    "trust_softness": {
        # Base level, no lower precedence
    },
}


OVERRIDE_TYPE_TABLE = {
    ("invariant", "policy_profile"): OverrideType.BLOCKING.value,
    ("invariant", "deployment_persona"): OverrideType.BLOCKING.value,
    ("invariant", "capability_boundary"): OverrideType.BLOCKING.value,
    ("policy_profile", "user_preference"): OverrideType.BLOCKING.value,
    ("policy_profile", "household_preference"): OverrideType.BLOCKING.value,
    ("capability_boundary", "user_preference"): OverrideType.SOFT.value,
    ("capability_boundary", "household_preference"): OverrideType.SOFT.value,
    ("deployment_persona", "user_preference"): OverrideType.SOFT.value,
    ("deployment_persona", "household_preference"): OverrideType.SOFT.value,
}


# ============================================================================
# CONFLICT RESOLUTION ENGINE
# ============================================================================


class ConflictResolutionEngine:
    """Engine for resolving policy conflicts deterministically.
    
    Provides transparent, reversible conflict resolution with explanation.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize conflict resolution engine."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/policy_conflict_resolution/"
        self.resolutions: Dict[str, ConflictResolution] = {}
        self.conflict_counter: int = 0
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _generate_conflict_id(self) -> str:
        """Generate unique conflict ID."""
        self.conflict_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"conflict_{timestamp}_{self.conflict_counter:04d}"
    
    def resolve_conflict(
        self,
        rule_a: ConflictRule,
        rule_b: ConflictRule,
        context: str = ConflictContext.GENERAL.value,
    ) -> ConflictResolution:
        """Resolve conflict between two rules."""
        conflict_id = self._generate_conflict_id()
        
        # Determine precedence
        precedence_a_to_b = OVERRIDE_PRIORITY_TABLE.get(rule_a.source.source_type, {}).get(rule_b.source.source_type, PrecedenceLevel.MEDIUM.value)
        precedence_b_to_a = OVERRIDE_PRIORITY_TABLE.get(rule_b.source.source_type, {}).get(rule_a.source.source_type, PrecedenceLevel.MEDIUM.value)
        
        # Determine override type
        override_key = (rule_a.source.source_type, rule_b.source.source_type)
        override_type = OVERRIDE_TYPE_TABLE.get(override_key, OverrideType.NONE.value)
        
        # Apply precedence
        precedence_order = [
            (PrecedenceLevel.SUPREME, "supreme"),
            (PrecedenceLevel.HIGH, "high"),
            (PrecedenceLevel.MEDIUM, "medium"),
            (PrecedenceLevel.LOW, "low"),
        ]
        
        precedence_a_idx = next((i for i, p in enumerate(precedence_order) if p[1] == precedence_a_to_b), 2)
        precedence_b_idx = next((i for i, p in enumerate(precedence_order) if p[1] == precedence_b_to_a), 2)
        
        if precedence_a_idx < precedence_b_idx:
            governing_rule = rule_a
            overriding_rule = None
            resolved_value = rule_a.rule_value
            explanation = f"{rule_a.source.source_type} rule '{rule_a.rule_id}' ({rule_a.rule_value}) takes precedence over {rule_b.source.source_type} rule '{rule_b.rule_id}' ({rule_b.rule_value}) per precedence table"
        elif precedence_b_idx < precedence_a_idx:
            governing_rule = rule_b
            overriding_rule = None
            resolved_value = rule_b.rule_value
            explanation = f"{rule_b.source.source_type} rule '{rule_b.rule_id}' ({rule_b.rule_value}) takes precedence over {rule_a.source.source_type} rule '{rule_a.rule_id}' ({rule_a.rule_value}) per precedence table"
        else:
            # Equal precedence - use override type
            if override_type == OverrideType.BLOCKING.value:
                governing_rule = rule_a
                overriding_rule = None
                resolved_value = rule_a.rule_value
                explanation = f"Equal precedence; {rule_a.source.source_type} rule '{rule_a.rule_id}' takes precedence (blocking override required to change)"
            elif override_type == OverrideType.SOFT.value:
                governing_rule = rule_a
                overriding_rule = None
                resolved_value = rule_a.rule_value
                explanation = f"Equal precedence; {rule_a.source.source_type} rule '{rule_a.rule_id}' takes precedence (soft override available)"
            else:
                # No override - first rule wins by default
                governing_rule = rule_a
                overriding_rule = None
                resolved_value = rule_a.rule_value
                explanation = f"Equal precedence and no override; {rule_a.source.source_type} rule '{rule_a.rule_id}' takes precedence by default"
        
        resolution = ConflictResolution(
            conflict_id=conflict_id,
            conflict_context=context,
            competing_rules=[rule_a.to_dict(), rule_b.to_dict()],
            governing_rule=governing_rule.to_dict(),
            overriding_rule=overriding_rule.to_dict() if overriding_rule else None,
            resolved_value=resolved_value,
            explanation=explanation,
        )
        
        self.resolutions[conflict_id] = resolution
        self._save_resolution(resolution)
        return resolution
    
    def _save_resolution(self, resolution: ConflictResolution) -> None:
        """Save resolution to storage."""
        import os
        
        filepath = os.path.join(self.storage_path, f"{resolution.conflict_id}.json")
        with open(filepath, "w") as f:
            json.dump(resolution.to_dict(), f, indent=2)
    
    def get_resolution(self, conflict_id: str) -> Optional[ConflictResolution]:
        """Get a resolution by ID."""
        return self.resolutions.get(conflict_id)
    
    def get_latest_resolution(self) -> Optional[ConflictResolution]:
        """Get the most recent resolution."""
        if not self.resolutions:
            return None
        return max(self.resolutions.values(), key=lambda r: r.timestamp)
    
    def resolve_profile_vs_deployment(
        self,
        profile_rule: ConflictRule,
        deployment_rule: ConflictRule,
    ) -> ConflictResolution:
        """Resolve conflict between policy profile and deployment persona."""
        return self.resolve_conflict(
            profile_rule,
            deployment_rule,
            ConflictContext.POLICY_PROFILE_VS_DEPLOYMENT.value,
        )
    
    def resolve_profile_vs_capability(
        self,
        profile_rule: ConflictRule,
        capability_rule: ConflictRule,
    ) -> ConflictResolution:
        """Resolve conflict between policy profile and capability boundary."""
        return self.resolve_conflict(
            profile_rule,
            capability_rule,
            ConflictContext.POLICY_PROFILE_VS_CAPABILITY.value,
        )
    
    def resolve_invariant_vs_policy(
        self,
        invariant_rule: ConflictRule,
        policy_rule: ConflictRule,
    ) -> ConflictResolution:
        """Resolve conflict between invariant and policy profile."""
        return self.resolve_conflict(
            invariant_rule,
            policy_rule,
            ConflictContext.POLICY_PROFILE_VS_INVARIANT.value,
        )
    
    def resolve_user_vs_policy(
        self,
        user_rule: ConflictRule,
        policy_rule: ConflictRule,
    ) -> ConflictResolution:
        """Resolve conflict between user preference and policy profile."""
        return self.resolve_conflict(
            user_rule,
            policy_rule,
            ConflictContext.USER_PREFERENCE_VS_POLICY.value,
        )
    
    def resolve_household_vs_policy(
        self,
        household_rule: ConflictRule,
        policy_rule: ConflictRule,
    ) -> ConflictResolution:
        """Resolve conflict between household preference and policy profile."""
        return self.resolve_conflict(
            household_rule,
            policy_rule,
            ConflictContext.HOUSEHOLD_VS_POLICY.value,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "resolution_count": len(self.resolutions),
            "conflict_counter": self.conflict_counter,
            "resolutions": {k: v.to_dict() for k, v in self.resolutions.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_policy_profile(
    profile_dict: Dict[str, Any],
    engine: ConflictResolutionEngine = None,
) -> Dict[str, Any]:
    """Add conflict resolution context to policy profile.
    
    This is purely additive — no migration required.
    
    v50: Conflict resolution provides precedence and override logic for policy rules.
    """
    if "conflict_resolution_context" not in profile_dict:
        profile_dict["conflict_resolution_context"] = None
    
    if engine:
        profile_dict["conflict_resolution_context"] = {
            "engine_storage_path": engine.storage_path,
            "resolution_count": len(engine.resolutions),
            "has_latest_resolution": engine.get_latest_resolution() is not None,
        }
    
    return profile_dict


def integrate_with_capability_boundary(
    capability_dict: Dict[str, Any],
    engine: ConflictResolutionEngine = None,
) -> Dict[str, Any]:
    """Add conflict resolution context to capability boundary.
    
    This is purely additive — no migration required.
    
    v50: Conflict resolution provides precedence for capability permissions.
    """
    if "conflict_resolution_context" not in capability_dict:
        capability_dict["conflict_resolution_context"] = None
    
    if engine:
        capability_dict["conflict_resolution_context"] = {
            "engine_storage_path": engine.storage_path,
            "resolution_count": len(engine.resolutions),
        }
    
    return capability_dict


def integrate_with_proof_gate(
    proof_dict: Dict[str, Any],
    engine: ConflictResolutionEngine = None,
) -> Dict[str, Any]:
    """Add conflict resolution context to proof gate.
    
    This is purely additive — no migration required.
    
    v50: Conflict resolution provides precedence for evidence and safety rules.
    """
    if "conflict_resolution_context" not in proof_dict:
        proof_dict["conflict_resolution_context"] = None
    
    if engine:
        proof_dict["conflict_resolution_context"] = {
            "engine_storage_path": engine.storage_path,
            "resolution_count": len(engine.resolutions),
        }
    
    return proof_dict


def integrate_with_governance_surface(
    governance_dict: Dict[str, Any],
    engine: ConflictResolutionEngine = None,
) -> Dict[str, Any]:
    """Add conflict resolution context to governance surface.
    
    This is purely additive — no migration required.
    
    v50: Conflict resolution provides transparent override logic for governance decisions.
    """
    if "conflict_resolution_context" not in governance_dict:
        governance_dict["conflict_resolution_context"] = None
    
    if engine:
        latest = engine.get_latest_resolution()
        governance_dict["conflict_resolution_context"] = {
            "engine_storage_path": engine.storage_path,
            "resolution_count": len(engine.resolutions),
            "has_latest_resolution": latest is not None,
            "latest_resolution_id": latest.conflict_id if latest else None,
            "latest_resolution_explanation": latest.explanation if latest else None,
        }
    
    return governance_dict
