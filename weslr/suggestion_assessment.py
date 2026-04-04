# suggestion_assessment.py - Weslr Capability Slice: Internal Assessment Layer
# Provides internal Weslr assessment of suggestion requests and bridged proposal candidates.
# Assessment is internal-only; operator approval remains required for all actions.
# Additive only, reversible, continuity-compatible.

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# ASSESSMENT CONSTANTS
# ============================================================================

# Priority levels
PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"
PRIORITY_CRITICAL = "critical"

# Risk levels
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"

# Fit score range
FIT_SCORE_MIN = 0.0
FIT_SCORE_MAX = 1.0


# ============================================================================
# ASSESSMENT ENGINE
# ============================================================================

class WeslrAssessment:
    """Internal assessment of suggestion requests and proposal candidates."""

    def __init__(self):
        # Default assessment thresholds
        self._priority_thresholds = {
            "high": {"score": 0.7, "risk": RISK_MEDIUM, "action": "review_immediately"},
            "medium": {"score": 0.4, "risk": RISK_MEDIUM, "action": "review_soon"},
            "low": {"score": 0.0, "risk": RISK_LOW, "action": "review_later"},
        }
        self._fit_keywords = {
            "astronomy": ["telescope", "observation", "spectral", "cosmic", "galaxy", "star"],
            "physics": ["quantum", "particle", "field", "energy", "motion", "force"],
            "chemistry": ["molecular", "reaction", "compound", "element", "bond"],
            "biology": ["cell", "protein", "dna", "organism", "evolution"],
            "engineering": ["design", "system", "architecture", "optimization", "integration"],
        }

    # --------------------------------------------------------------------------
    # CORE ASSESSMENT METHODS
    # --------------------------------------------------------------------------

    def assess_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Assess a suggestion request internally.

        Args:
            request: Suggestion request dict from suggestion_box

        Returns:
            Assessment dict with priority, fit_score, risk, recommended action
        """
        domain = request.get("domain", "unknown").lower()
        capability = request.get("requested_capability", "")
        problem = request.get("problem_statement", "")

        # Calculate fit score
        fit_score = self._calculate_fit_score(domain, capability, problem)

        # Determine priority
        priority = self._determine_priority(fit_score)

        # Assess implementation risk
        risk = self._assess_implementation_risk(domain, capability, problem)

        # Build reasoning
        reasoning = self._build_reasoning(domain, capability, problem, fit_score, priority, risk)

        return {
            "weslr_assessment": {
                "priority": priority,
                "fit_score": round(fit_score, 2),
                "implementation_risk": risk,
                "recommended_action": self._get_recommended_action(priority, risk),
                "reasoning": reasoning,
                "assessed_at": datetime.utcnow().isoformat() + "Z",
            }
        }

    def assess_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Assess a proposal candidate internally.

        Args:
            candidate: Proposal candidate dict from suggestion_bridge

        Returns:
            Assessment dict with priority, fit_score, risk, recommended action
        """
        # Extract data from candidate
        source = candidate.get("source", {})
        original_data = source.get("original_data", {})
        domain = original_data.get("domain", "unknown").lower()
        capability = original_data.get("requested_capability", "")
        problem = original_data.get("problem_statement", "")

        # Calculate fit score
        fit_score = self._calculate_fit_score(domain, capability, problem)

        # Determine priority
        priority = self._determine_priority(fit_score)

        # Assess implementation risk
        risk = self._assess_implementation_risk(domain, capability, problem)

        # Build reasoning
        reasoning = self._build_reasoning(domain, capability, problem, fit_score, priority, risk)

        return {
            "weslr_assessment": {
                "priority": priority,
                "fit_score": round(fit_score, 2),
                "implementation_risk": risk,
                "recommended_action": self._get_recommended_action(priority, risk),
                "reasoning": reasoning,
                "assessed_at": datetime.utcnow().isoformat() + "Z",
            }
        }

    # --------------------------------------------------------------------------
    # INTERNAL ASSESSMENT HELPERS
    # --------------------------------------------------------------------------

    def _calculate_fit_score(self, domain: str, capability: str, problem: str) -> float:
        """Calculate fit score based on domain, capability, and problem statements."""
        score = 0.5  # Base score

        # Domain match bonus
        domain_keywords = self._fit_keywords.get(domain, [])
        if domain_keywords:
            text = f"{capability} {problem}".lower()
            keyword_count = sum(1 for kw in domain_keywords if kw in text)
            score += min(0.2, keyword_count * 0.03)  # Max +0.2 for domain match

        # Capability clarity bonus
        if len(capability) > 10:
            score += 0.1
        if re.search(r"[a-z]", capability):
            score += 0.05

        # Problem specificity bonus
        if len(problem) > 20:
            score += 0.1
        if "need" in problem.lower() or "better" in problem.lower():
            score += 0.05

        # Clamp to valid range
        return max(FIT_SCORE_MIN, min(FIT_SCORE_MAX, round(score, 2)))

    def _determine_priority(self, fit_score: float) -> str:
        """Determine priority based on fit score."""
        if fit_score >= 0.7:
            return PRIORITY_HIGH
        elif fit_score >= 0.4:
            return PRIORITY_MEDIUM
        else:
            return PRIORITY_LOW

    def _assess_implementation_risk(self, domain: str, capability: str, problem: str) -> str:
        """Assess implementation risk based on domain complexity and clarity."""
        # Domain-based risk
        complex_domains = ["quantum", "neural", "genetic", "cryogenic", "plasma"]
        if any(d in domain.lower() for d in complex_domains):
            return RISK_HIGH
        elif domain in self._fit_keywords:
            return RISK_MEDIUM

        # Capability complexity
        if len(capability) > 50 or any(c in capability.lower() for c in ["complex", "sophisticated", "advanced"]):
            return RISK_HIGH

        return RISK_LOW

    def _get_recommended_action(self, priority: str, risk: str) -> str:
        """Get recommended action based on priority and risk."""
        if priority == PRIORITY_CRITICAL:
            return "convert_to_proposal_immediate"
        elif priority == PRIORITY_HIGH:
            return "convert_to_proposal"
        elif priority == PRIORITY_MEDIUM and risk in [RISK_LOW, RISK_MEDIUM]:
            return "review_for_conversion"
        elif priority == PRIORITY_LOW:
            return "archive_or_reject"
        else:
            return "review_with_caveats"

    def _build_reasoning(
        self, domain: str, capability: str, problem: str, fit_score: float,
        priority: str, risk: str
    ) -> str:
        """Build human-readable reasoning for assessment."""
        reasoning_parts = [
            f"Assessed fit score of {fit_score} based on domain '{domain}' alignment.",
            f"Priority set to '{priority}' due to fit characteristics.",
        ]

        # Add specific reasoning
        if fit_score >= 0.7:
            reasoning_parts.append(
                "Strong alignment with current capability patterns and scientific direction."
            )
        elif fit_score >= 0.4:
            reasoning_parts.append(
                "Moderate alignment - potential fit with some customization."
            )
        else:
            reasoning_parts.append(
                "Limited alignment - may require significant adaptation."
            )

        reasoning_parts.append(f"Implementation risk assessed as '{risk}'.")
        reasoning_parts.append("Recommend operator review before conversion to proposal.")

        return " ".join(reasoning_parts)

    # --------------------------------------------------------------------------
    # BATCH ASSESSMENT
    # --------------------------------------------------------------------------

    def assess_requests_batch(
        self, requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Assess multiple requests at once."""
        return [self.assess_request(req) for req in requests]

    def assess_candidates_batch(
        self, candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Assess multiple candidates at once."""
        return [self.assess_candidate(cand) for cand in candidates]


# ============================================================================
# ASSESSMENT WRAPPER (for integration with bridge)
# ============================================================================

def apply_assessment_to_candidate(
    candidate: Dict[str, Any]
) -> Dict[str, Any]:
    """Apply Weslr assessment to a candidate and return updated candidate."""
    assessment = WeslrAssessment().assess_candidate(candidate)
    candidate["weslr_assessment"] = assessment["weslr_assessment"]
    candidate["updated_at"] = datetime.utcnow().isoformat() + "Z"
    return candidate


def get_recommendations(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get assessment recommendations for candidates."""
    assessment = WeslrAssessment()
    recommendations = []

    for cand in candidates:
        result = assessment.assess_candidate(cand)
        recommendations.append({
            "candidate_id": cand.get("id"),
            "assessment": result["weslr_assessment"],
            "recommended_action": result["weslr_assessment"].get("recommended_action"),
        })

    return recommendations


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python suggestion_assessment.py <command> [args]")
        print("Commands:")
        print("  assess_request <domain> <capability> <problem>")
        print("  assess_candidate <json_file>")
        print("  batch_assess <json_file>")
        print("  recommendations <candidates_json_file>")
        sys.exit(1)

    command = sys.argv[1]
    assessment = WeslrAssessment()

    if command == "assess_request":
        if len(sys.argv) < 5:
            print("Usage: assess_request <domain> <capability> <problem>")
            sys.exit(1)
        domain = sys.argv[2]
        capability = sys.argv[3]
        problem = sys.argv[4]
        result = assessment.assess_request({
            "domain": domain,
            "requested_capability": capability,
            "problem_statement": problem,
        })
        print(json.dumps(result, indent=2))

    elif command == "assess_candidate":
        if len(sys.argv) < 3:
            print("Usage: assess_candidate <json_file>")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            candidate = json.load(f)
        result = assessment.assess_candidate(candidate)
        print(json.dumps(result, indent=2))

    elif command == "batch_assess":
        if len(sys.argv) < 3:
            print("Usage: batch_assess <json_file>")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            items = json.load(f)
        if isinstance(items, list):
            results = assessment.assess_requests_batch(items) if items and "domain" in items[0] else assessment.assess_candidates_batch(items)
        else:
            results = [assessment.assess_candidate(items)] if "source" in items else [assessment.assess_request(items)]
        print(json.dumps(results, indent=2))

    elif command == "recommendations":
        if len(sys.argv) < 3:
            print("Usage: recommendations <candidates_json_file>")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            candidates = json.load(f)
        recs = get_recommendations(candidates)
        print(json.dumps(recs, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
