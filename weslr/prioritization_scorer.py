"""Prioritization Scorer - WESLR Decision Layer v1

Scoring logic for urgency, impact, and confidence in decision prioritization.

Contract:
- WESLR synthesizes scores transparently
- All scoring factors are documented and auditable
- No hidden weights or unexplainable factors

Scope:
- score_urgency: compute urgency score from escalation/governance data
- score_impact: compute impact score from state/context
- score_confidence: compute confidence from evidence/precedent
- composite_score: combine scores with documented weights

Non-scope:
- emotional weighting
- hidden bias
- autonomous prioritization without operator visibility

Additive only. Pure functions. No state mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ScoringFactors:
    """Factors contributing to a priority score.
    
    All factors are documented and auditable.
    No hidden weights or unexplainable factors.
    """
    
    urgency_level: str  # "low", "normal", "high", "critical"
    safety_impact: float  # 0.0-1.0
    trust_confidence: float  # 0.0-1.0
    evidence_count: int  # Number of supporting evidence items
    precedent_match: float  # 0.0-1.0 similarity to historical cases
    launch_readiness: float  # 0.0-1.0 readiness to proceed
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "urgency_level": self.urgency_level,
            "safety_impact": self.safety_impact,
            "trust_confidence": self.trust_confidence,
            "evidence_count": self.evidence_count,
            "precedent_match": self.precedent_match,
            "launch_readiness": self.launch_readiness,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ScoringFactors:
        """Deserialize from dictionary."""
        return cls(
            urgency_level=data["urgency_level"],
            safety_impact=data["safety_impact"],
            trust_confidence=data["trust_confidence"],
            evidence_count=data["evidence_count"],
            precedent_match=data["precedent_match"],
            launch_readiness=data["launch_readiness"],
        )


# Documented weight configuration
# These weights are transparent and operator-adjustable
SCORING_WEIGHTS = {
    "urgency_weight": 0.30,
    "safety_impact_weight": 0.25,
    "trust_confidence_weight": 0.20,
    "evidence_weight": 0.10,
    "precedent_weight": 0.10,
    "launch_readiness_weight": 0.05,
}

# Urgency level to numeric mapping
URGENCY_SCORES = {
    "low": 0.25,
    "normal": 0.50,
    "high": 0.75,
    "critical": 1.00,
}


def score_urgency(urgency_level: str) -> float:
    """Convert urgency level to numeric score.
    
    Args:
        urgency_level: "low", "normal", "high", or "critical"
    
    Returns:
        Float score 0.0-1.0
    """
    return URGENCY_SCORES.get(urgency_level, 0.50)


def score_impact(safety_impact: float) -> float:
    """Score safety impact factor.
    
    Args:
        safety_impact: Float 0.0-1.0 representing safety impact
    
    Returns:
        Float score 0.0-1.0
    """
    if not 0.0 <= safety_impact <= 1.0:
        raise ValueError(f"safety_impact must be 0.0-1.0, got {safety_impact}")
    return safety_impact


def score_confidence(trust_confidence: float) -> float:
    """Score trust confidence factor.
    
    Args:
        trust_confidence: Float 0.0-1.0 representing trust in the assessment
    
    Returns:
        Float score 0.0-1.0
    """
    if not 0.0 <= trust_confidence <= 1.0:
        raise ValueError(f"trust_confidence must be 0.0-1.0, got {trust_confidence}")
    return trust_confidence


def score_evidence(evidence_count: int) -> float:
    """Score evidence count factor.
    
    Uses diminishing returns: more evidence helps, but with decreasing marginal value.
    
    Args:
        evidence_count: Number of supporting evidence items
    
    Returns:
        Float score 0.0-1.0
    """
    if evidence_count <= 0:
        return 0.0
    # Diminishing returns: log scale with floor
    # 1 evidence = 0.30, 3 = 0.55, 5 = 0.70, 10 = 0.85
    import math
    return min(0.30 + 0.25 * math.log(evidence_count), 1.0)


def score_precedent(precedent_match: float) -> float:
    """Score precedent match factor.
    
    Args:
        precedent_match: Float 0.0-1.0 similarity to historical cases
    
    Returns:
        Float score 0.0-1.0
    """
    if not 0.0 <= precedent_match <= 1.0:
        raise ValueError(f"precedent_match must be 0.0-1.0, got {precedent_match}")
    return precedent_match


def score_launch_readiness(launch_readiness: float) -> float:
    """Score launch readiness factor.
    
    Args:
        launch_readiness: Float 0.0-1.0 representing readiness to proceed
    
    Returns:
        Float score 0.0-1.0
    """
    if not 0.0 <= launch_readiness <= 1.0:
        raise ValueError(f"launch_readiness must be 0.0-1.0, got {launch_readiness}")
    return launch_readiness


def composite_score(factors: ScoringFactors, weights: Optional[Dict[str, float]] = None) -> float:
    """Compute composite priority score from all factors.
    
    Uses documented weights that are transparent and operator-adjustable.
    
    Args:
        factors: ScoringFactors containing all input factors
        weights: Optional custom weights (defaults to SCORING_WEIGHTS)
    
    Returns:
        Composite score 0.0-1.0
    """
    if weights is None:
        weights = SCORING_WEIGHTS
    
    urgency = score_urgency(factors.urgency_level)
    impact = score_impact(factors.safety_impact)
    confidence = score_confidence(factors.trust_confidence)
    evidence = score_evidence(factors.evidence_count)
    precedent = score_precedent(factors.precedent_match)
    readiness = score_launch_readiness(factors.launch_readiness)
    
    composite = (
        weights["urgency_weight"] * urgency +
        weights["safety_impact_weight"] * impact +
        weights["trust_confidence_weight"] * confidence +
        weights["evidence_weight"] * evidence +
        weights["precedent_weight"] * precedent +
        weights["launch_readiness_weight"] * readiness
    )
    
    # Clamp to 0.0-1.0
    return max(0.0, min(1.0, composite))


def score_with_explanation(factors: ScoringFactors, weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Compute composite score with full explanation for transparency.
    
    Returns both the score and the breakdown of factors.
    This supports the transparency contract: all scoring is documented.
    
    Args:
        factors: ScoringFactors containing all input factors
        weights: Optional custom weights (defaults to SCORING_WEIGHTS)
    
    Returns:
        Dictionary with score, factors, weights, and contribution breakdown
    """
    if weights is None:
        weights = SCORING_WEIGHTS
    
    urgency = score_urgency(factors.urgency_level)
    impact = score_impact(factors.safety_impact)
    confidence = score_confidence(factors.trust_confidence)
    evidence = score_evidence(factors.evidence_count)
    precedent = score_precedent(factors.precedent_match)
    readiness = score_launch_readiness(factors.launch_readiness)
    
    contributions = {
        "urgency": {
            "value": urgency,
            "weight": weights["urgency_weight"],
            "contribution": weights["urgency_weight"] * urgency,
        },
        "safety_impact": {
            "value": impact,
            "weight": weights["safety_impact_weight"],
            "contribution": weights["safety_impact_weight"] * impact,
        },
        "trust_confidence": {
            "value": confidence,
            "weight": weights["trust_confidence_weight"],
            "contribution": weights["trust_confidence_weight"] * confidence,
        },
        "evidence": {
            "value": evidence,
            "weight": weights["evidence_weight"],
            "contribution": weights["evidence_weight"] * evidence,
        },
        "precedent": {
            "value": precedent,
            "weight": weights["precedent_weight"],
            "contribution": weights["precedent_weight"] * precedent,
        },
        "launch_readiness": {
            "value": readiness,
            "weight": weights["launch_readiness_weight"],
            "contribution": weights["launch_readiness_weight"] * readiness,
        },
    }
    
    composite = composite_score(factors, weights)
    
    return {
        "composite_score": composite,
        "factors": factors.to_dict(),
        "weights": weights,
        "contributions": contributions,
        "explanation": f"Composite score {composite:.3f} from urgency={urgency:.2f}, impact={impact:.2f}, confidence={confidence:.2f}, evidence={evidence:.2f}, precedent={precedent:.2f}, readiness={readiness:.2f}",
    }