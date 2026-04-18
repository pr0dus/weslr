"""Evidence Policy Module

Defines evidentiary requirements for requests:
- Minimum evidentiary standard
- Evidence tolerance (how much error is acceptable)
- Fallback policies (what to do when evidence is insufficient)
- Evidence types (what sources can provide evidence)

This enables:
- Intelligent routing (know what evidence is needed)
- Provider suitability (matching providers to evidence needs)
- Uncertainty enforcement (rejecting requests that can't meet requirements)
- Evidence caching (reusing evidence when appropriate)
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class EvidenceType(Enum):
    """Types of evidence that can be provided."""
    TIME = "TIME"  # System time evidence
    WEATHER = "WEATHER"  # Weather data evidence
    WEB = "WEB"  # Web search results
    FILE = "FILE"  # File content analysis
    CALCULATION = "CALCULATION"  # Math/computation results
    CONTEXT = "CONTEXT"  # Existing context/snapshot
    RESEARCH = "RESEARCH"  # Research paper analysis


class EvidenceRequirement:
    """Single evidence requirement."""
    
    def __init__(
        self,
        evidence_type: EvidenceType,
        min_confidence: float = 0.7,
        max_age_seconds: int = 300,  # 5 minutes default
        tolerance: float = 0.1,  # 10% tolerance
        fallback_policy: str = "none",  # none, cached, estimated, fallback
        cache_enabled: bool = True,
    ):
        self.evidence_type = evidence_type
        self.min_confidence = min_confidence
        self.max_age_seconds = max_age_seconds
        self.tolerance = tolerance
        self.fallback_policy = fallback_policy
        self.cache_enabled = cache_enabled
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_type": self.evidence_type.value,
            "min_confidence": self.min_confidence,
            "max_age_seconds": self.max_age_seconds,
            "tolerance": self.tolerance,
            "fallback_policy": self.fallback_policy,
            "cache_enabled": self.cache_enabled,
        }
    
    def __repr__(self) -> str:
        return f"EvidenceRequirement({self.evidence_type.value}, min_confidence={self.min_confidence})"


class EvidencePolicy:
    """Evidence policy for requests.
    
    Defines:
    - What evidence is needed
    - How good the evidence must be
    - How old evidence can be
    - What fallback mechanisms exist
    - Whether caching is allowed
    
    Used by:
    - RequestIntelligence for policy enforcement
    - ProviderSuitability for provider matching
    - UncertaintyDiscipline for enforcement
    """
    
    def __init__(
        self,
        requirements: List[EvidenceRequirement] = None,
        minimum_evidence_count: int = 1,
        evidence_strategy: str = "minimal",  # minimal, comprehensive, conservative
        allow_fallback: bool = True,
        require_all_evidence: bool = False,
    ):
        self.requirements = requirements or []
        self.minimum_evidence_count = minimum_evidence_count
        self.evidence_strategy = evidence_strategy
        self.allow_fallback = allow_fallback
        self.require_all_evidence = require_all_evidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirements": [r.to_dict() for r in self.requirements],
            "minimum_evidence_count": self.minimum_evidence_count,
            "evidence_strategy": self.evidence_strategy,
            "allow_fallback": self.allow_fallback,
            "require_all_evidence": self.require_all_evidence,
        }
    
    def __repr__(self) -> str:
        return f"EvidencePolicy({len(self.requirements)} requirements, strategy={self.evidence_strategy})"
    
    def meets_policy(self, provided_evidence: Dict[str, Any]) -> bool:
        """Check if provided evidence meets the policy requirements."""
        if not self.requirements:
            return True  # No requirements means policy is met
        
        # Count how many requirements are satisfied
        satisfied_count = 0
        for req in self.requirements:
            if self._check_requirement(req, provided_evidence):
                satisfied_count += 1
        
        if self.require_all_evidence:
            return satisfied_count == len(self.requirements)
        else:
            return satisfied_count >= self.minimum_evidence_count
    
    def _check_requirement(self, requirement: EvidenceRequirement, provided_evidence: Dict[str, Any]) -> bool:
        """Check if a single requirement is satisfied."""
        evidence_key = requirement.evidence_type.value.lower()
        
        # Check if evidence type is present
        if evidence_key not in provided_evidence:
            return False
        
        evidence_value = provided_evidence[evidence_key]
        
        # Check confidence if available
        if requirement.min_confidence > 0:
            confidence = evidence_value.get("confidence", 1.0)
            if confidence < requirement.min_confidence:
                return False
        
        # Check age if available
        if requirement.max_age_seconds > 0:
            current_time = evidence_value.get("timestamp", 0)
            evidence_time = evidence_value.get("evidence_time", 0)
            if current_time > 0 and evidence_time > 0:
                age = current_time - evidence_time
                if age > requirement.max_age_seconds:
                    return False
        
        return True
    
    def get_fallback_policy(self) -> str:
        """Get the fallback policy based on evidence strategy."""
        if self.evidence_strategy == "conservative":
            return "none"
        elif self.evidence_strategy == "comprehensive":
            return "estimated"
        else:
            return self.allow_fallback and "cached" or "none"
    
    def requires_evidence(self) -> bool:
        """Check if this policy requires any evidence."""
        return len(self.requirements) > 0


class EvidencePolicyBuilder:
    """Builds evidence policies for requests.
    
    Creates policies based on:
    - Request type
    - Request difficulty
    - Knowledge state analysis
    - Evidence availability
    """
    
    def __init__(self):
        # Policy templates by request type
        self._policy_templates = {
            "time_query": EvidencePolicy(
                requirements=[
                    EvidenceRequirement(EvidenceType.TIME, min_confidence=0.9, max_age_seconds=60),
                ],
                evidence_strategy="conservative",
                require_all_evidence=True,
            ),
            "weather_query": EvidencePolicy(
                requirements=[
                    EvidenceRequirement(EvidenceType.WEATHER, min_confidence=0.8, max_age_seconds=300),
                ],
                evidence_strategy="comprehensive",
                allow_fallback=True,
            ),
            "factual_query": EvidencePolicy(
                requirements=[
                    EvidenceRequirement(EvidenceType.CONTEXT, min_confidence=0.7, max_age_seconds=3600),
                ],
                evidence_strategy="minimal",
                allow_fallback=True,
            ),
            "research_query": EvidencePolicy(
                requirements=[
                    EvidenceRequirement(EvidenceType.WEB, min_confidence=0.6, max_age_seconds=86400),
                    EvidenceRequirement(EvidenceType.RESEARCH, min_confidence=0.7),
                ],
                minimum_evidence_count=1,
                evidence_strategy="comprehensive",
                allow_fallback=True,
            ),
            "calculation_query": EvidencePolicy(
                requirements=[
                    EvidenceRequirement(EvidenceType.CALCULATION, min_confidence=0.99),
                ],
                evidence_strategy="conservative",
                require_all_evidence=True,
            ),
        }
    
    def build_policy(self, request_type: str, difficulty: int = 1) -> EvidencePolicy:
        """Build an evidence policy for a request type."""
        # Get template or create default
        template = self._policy_templates.get(request_type)
        if not template:
            template = EvidencePolicy()
        
        # Adjust based on difficulty (higher difficulty = more lenient)
        if difficulty >= 3:  # HIGH or EXTREME
            template = EvidencePolicy(
                requirements=template.requirements,
                minimum_evidence_count=max(1, template.minimum_evidence_count - 1),
                evidence_strategy="comprehensive",
                allow_fallback=True,
            )
        
        return template
    
    def build_policy_from_requirements(
        self,
        evidence_types: List[EvidenceType],
        min_confidence: float = 0.7,
        max_age_seconds: int = 300,
        fallback_policy: str = "cached",
    ) -> EvidencePolicy:
        """Build policy from explicit requirements."""
        requirements = [
            EvidenceRequirement(
                evidence_type=et,
                min_confidence=min_confidence,
                max_age_seconds=max_age_seconds,
                fallback_policy=fallback_policy,
            )
            for et in evidence_types
        ]
        
        return EvidencePolicy(
            requirements=requirements,
            minimum_evidence_count=len(requirements),
            evidence_strategy="comprehensive",
            allow_fallback=fallback_policy != "none",
            require_all_evidence=False,
        )
    
    def get_default_policy(self) -> EvidencePolicy:
        """Get default policy for general requests."""
        return EvidencePolicy(
            requirements=[
                EvidenceRequirement(EvidenceType.CONTEXT, min_confidence=0.5),
            ],
            minimum_evidence_count=0,  # No strict requirements
            evidence_strategy="minimal",
            allow_fallback=True,
        )
    
    def get_strict_policy(self) -> EvidencePolicy:
        """Get strict policy for critical requests."""
        return EvidencePolicy(
            requirements=[
                EvidenceRequirement(EvidenceType.CONTEXT, min_confidence=0.9),
            ],
            minimum_evidence_count=1,
            evidence_strategy="conservative",
            allow_fallback=False,
            require_all_evidence=True,
        )
