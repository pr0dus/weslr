"""Weslr Test Self-Reflection Layer (v1)

Internal awareness of test system, scorecard, and improvement implications.
Designed to be additive and reversible — no production modifications.

Key Principles:
  - Interpretation only, no autonomous implementation
  - Recommendations remain governed (operator review required)
  - No fake self-awareness claims
  - Clear distinction between analysis and action
  - No self-rewriting or autonomous code changes
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path


__all__ = [
    "WeslrTestReflection",
]


class WeslrTestReflection:
    """Internal self-reflection layer for Weslr.
    
    Allows Weslr to understand its own test results, scorecard, 
    and improvement implications WITHOUT enabling autonomous changes.
    
    This is a GOVERNED interpretation layer:
    - Can analyze and suggest improvements
    - Must recommend operator review for meaningful changes
    - Cannot modify itself or production code
    - No autonomous implementation capability
    """
    
    # Category meanings and implications
    CATEGORY_MEANINGS = {
        "security": {
            "meaning": "Protection against malicious inputs and unauthorized access",
            "implication": "Strong security means Weslr is safe from attack vectors",
            "weakest_implication": "Security gaps could allow malicious inputs to compromise the system"
        },
        "governance": {
            "meaning": "Review process integrity and workflow correctness",
            "implication": "Strong governance means suggestions are properly reviewed",
            "weakest_implication": "Governance gaps could allow unreviewed changes"
        },
        "file_data": {
            "meaning": "File upload and data routing correctness",
            "implication": "Strong file handling means uploads work correctly",
            "weakest_implication": "File handling gaps could cause data loss or misrouting"
        },
        "continuity": {
            "meaning": "State persistence and rollback reliability",
            "implication": "Strong continuity means state is preserved across sessions",
            "weakest_implication": "Continuity gaps could cause data loss on restart"
        },
        "scientific": {
            "meaning": "Scientific analysis correctness and workflow reliability",
            "implication": "Strong scientific handling means analyses are reliable",
            "weakest_implication": "Scientific gaps could produce incorrect analysis results"
        },
        "shell_ux": {
            "meaning": "Shell interface and operator commands reliability",
            "implication": "Strong UX means operators can effectively manage Weslr",
            "weakest_implication": "UX gaps could make Weslr difficult to operate"
        },
        "non_deterministic": {
            "meaning": "Stability under input variation and environmental changes",
            "implication": "Strong stability means Weslr behaves consistently",
            "weakest_implication": "Non-deterministic behavior could cause unpredictable results"
        },
        "privacy": {
            "meaning": "Role boundary enforcement and data isolation",
            "implication": "Strong privacy means sensitive data stays protected",
            "weakest_implication": "Privacy gaps could expose sensitive data"
        },
        "failure_monitoring": {
            "meaning": "Failure handling and operational resilience",
            "implication": "Strong failure handling means Weslr degrades gracefully",
            "weakest_implication": "Poor failure handling could cause crashes"
        },
        "data_quality": {
            "meaning": "Robustness to malformed, sparse, or incomplete inputs",
            "implication": "Strong data quality handling means Weslr works with imperfect data",
            "weakest_implication": "Data quality gaps could cause failures on real-world inputs"
        },
        "explainability": {
            "meaning": "Consistency between reasoning, scores, and explanations",
            "implication": "Strong explainability means Weslr's reasoning is trustworthy",
            "weakest_implication": "Poor explainability could make Weslr untrustworthy"
        },
    }
    
    # Suggested improvement categories
    IMPROVEMENT_CATEGORIES = {
        "security": "Security hardening",
        "governance": "Governance process improvements",
        "file_data": "Data handling robustness",
        "continuity": "State persistence improvements",
        "scientific": "Scientific analysis improvements",
        "shell_ux": "User experience improvements",
        "non_deterministic": "Stability improvements",
        "privacy": "Privacy boundary hardening",
        "failure_monitoring": "Failure resilience improvements",
        "data_quality": "Input robustness improvements",
        "explainability": "Explanation consistency improvements",
    }
    
    # Safety classifications for improvement actions
    SAFETY_LEVELS = {
        "additive_only": {
            "description": "Pure additive changes (new tests, documentation)",
            "requires_review": False,
            "risk_level": "low",
        },
        "operator_review_required": {
            "description": "Changes that affect behavior or require human oversight",
            "requires_review": True,
            "risk_level": "medium",
        },
    }
    
    def __init__(self):
        """Initialize the self-reflection layer.
        
        No production configuration needed - this is purely interpretive.
        """
        self._interpretations = []
    
    def reflect_on_results(
        self,
        test_results: Dict[str, Any],
        scorecard: Dict[str, Any],
        interpretation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Reflect on test results and generate internal understanding.
        
        Args:
            test_results: From WeslrTestHarness (categories, scores)
            scorecard: From WeslrScorecard (readiness, category details)
            interpretation: Optional additional interpretation context
            
        Returns:
            Dict with self-understanding, weakest categories, recommendations
        """
        # Extract data from inputs
        categories = test_results.get("categories", {})
        category_details = scorecard.get("details", {})
        readiness = scorecard.get("readiness", "unknown")
        total_score = scorecard.get("total_score", 0)
        max_score = scorecard.get("max_score", 100)
        
        # Calculate scores as percentages for analysis
        category_scores = {}
        for cat, details in category_details.items():
            max_cat_score = details.get("max_score", 10)
            cat_score = details.get("category_score", 0)
            score_pct = (cat_score / max_cat_score) * 100 if max_cat_score > 0 else 0
            category_scores[cat] = {
                "score": int(cat_score),
                "max_score": max_cat_score,
                "percentage": score_pct,
                "details": details,
            }
        
        # Find weakest categories
        weakest = self.weakest_categories(category_scores)
        
        # Generate recommendations
        recommendations = self.recommended_improvements(category_scores)
        
        # Build self-understanding
        self_understanding = self._build_self_understanding(readiness)
        
        # Determine overall readiness
        if total_score >= 90:
            overall_readiness = "public test ready"
        elif total_score >= 75:
            overall_readiness = "limited/operator-supervised pilot"
        elif total_score >= 60:
            overall_readiness = "private beta only"
        else:
            overall_readiness = "not ready"
        
        return {
            "category": "test_reflection",
            "overall_readiness": overall_readiness,
            "readiness_score": total_score,
            "readiness_max": max_score,
            "weakest_categories": weakest,
            "recommended_improvements": recommendations,
            "self_understanding": self_understanding,
            "interpretation": interpretation or {},
        }
    
    def _build_self_understanding(self, readiness: str) -> Dict[str, str]:
        """Build Weslr's understanding of its own state.
        
        Returns:
            Dict describing what tests mean, current state, and autonomy limits
        """
        return {
            "what_tests_mean": (
                "These tests measure my reliability, governance, safety, "
                "and scientific correctness. Each category validates a different "
                "aspect of my functionality without modifying me."
            ),
            "current_state": (
                "I am strong in many areas but still operator-governed. "
                "My tests verify my behavior without allowing me to change myself."
            ),
            "autonomy_limit": (
                "I may recommend improvements, but operators must approve "
                "meaningful system changes. I cannot modify myself or production code."
            ),
            "readiness_level": readiness,
        }
    
    def weakest_categories(self, category_scores: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Identify the weakest categories that need improvement.
        
        Args:
            category_scores: Dict of category -> {score, max_score, percentage, details}
            
        Returns:
            List of weakest categories with meaning and improvement suggestions
        """
        # Sort by score (ascending)
        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: x[1].get("percentage", 0)
        )
        
        # Get categories below 90%
        weak_categories = []
        for cat, data in sorted_categories:
            if data.get("percentage", 100) < 90:
                meaning = self.CATEGORY_MEANINGS.get(cat, {}).get(
                    "weakest_implication",
                    f"{cat} category needs improvement"
                )
                
                weak_categories.append({
                    "name": cat,
                    "score": data.get("score", 0),
                    "max_score": data.get("max_score", 10),
                    "percentage": data.get("percentage", 0),
                    "meaning": meaning,
                })
        
        # Return up to 3 weakest
        return weak_categories[:3]
    
    def recommended_improvements(
        self,
        category_scores: Dict[str, Dict]
    ) -> List[Dict[str, Any]]:
        """Generate recommended improvements based on weaknesses.
        
        Args:
            category_scores: Dict of category -> {score, max_score, percentage, details}
            
        Returns:
            List of recommended improvements with action, priority, and safety level
        """
        recommendations = []
        
        for cat, data in category_scores.items():
            if data.get("percentage", 100) < 90:
                category_name = self.IMPROVEMENT_CATEGORIES.get(cat, cat)
                
                # Determine priority based on gap size
                gap = 100 - data.get("percentage", 0)
                if gap >= 30:
                    priority = "high"
                elif gap >= 15:
                    priority = "medium"
                else:
                    priority = "low"
                
                # Determine safety level based on category type
                safety_level = self._determine_safety(cat, data)
                
                recommendations.append({
                    "action": f"strengthen {cat} test coverage",
                    "category": cat,
                    "category_name": category_name,
                    "priority": priority,
                    "safety": safety_level,
                    "rationale": f"Category is at {data.get('percentage', 0):.1f}% ({data.get('score', 0)}/{data.get('max_score', 10)})",
                })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))
        
        return recommendations
    
    def _determine_safety(self, category: str, data: Dict) -> str:
        """Determine safety level for improvement action.
        
        Args:
            category: Test category name
            data: Category score data
            
        Returns:
            Safety level: "additive_only" or "operator_review_required"
        """
        # Pure test improvements are additive
        additive_categories = [
            "non_deterministic",
            "data_quality",
            "explainability",
        ]
        
        if category in additive_categories:
            return "additive_only"
        
        # Category-specific safety determinations
        safety_map = {
            "security": "operator_review_required",
            "governance": "operator_review_required",
            "continuity": "operator_review_required",
            "scientific": "additive_only",
            "shell_ux": "additive_only",
            "file_data": "additive_only",
            "privacy": "operator_review_required",
            "failure_monitoring": "operator_review_required",
        }
        
        return safety_map.get(category, "additive_only")
    
    def readiness_trend(
        self,
        historical_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze readiness trend over time.
        
        Args:
            historical_results: List of previous reflection results
            
        Returns:
            Dict with trend analysis and predictions
        """
        if not historical_results:
            return {
                "trend": "insufficient_data",
                "direction": "unknown",
                "confidence": "low",
            }
        
        # Extract readiness scores
        scores = [h.get("readiness_score", 0) for h in historical_results]
        
        if len(scores) < 2:
            return {
                "trend": "insufficient_data",
                "direction": "unknown",
                "confidence": "low",
                "samples": len(scores),
            }
        
        # Calculate trend
        first_half_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
        second_half_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        
        if second_half_avg > first_half_avg:
            direction = "improving"
        elif second_half_avg < first_half_avg:
            direction = "declining"
        else:
            direction = "stable"
        
        # Calculate confidence based on data points
        if len(scores) >= 5:
            confidence = "high"
        elif len(scores) >= 3:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            "trend": direction,
            "direction": direction,
            "confidence": confidence,
            "current_score": scores[-1],
            "samples": len(scores),
            "first_half_avg": round(first_half_avg, 2),
            "second_half_avg": round(second_half_avg, 2),
        }


def create_weslr_reflection() -> WeslrTestReflection:
    """Create a configured WeslrTestReflection instance."""
    return WeslrTestReflection()


def reflect_weslr(
    test_results: Dict[str, Any],
    scorecard: Dict[str, Any],
    interpretation: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Convenience function to reflect on Weslr's test results.
    
    Args:
        test_results: From WeslrTestHarness
        scorecard: From WeslrScorecard
        interpretation: Optional additional interpretation context
        
    Returns:
        Reflection result
    """
    reflection = create_weslr_reflection()
    return reflection.reflect_on_results(test_results, scorecard, interpretation)
