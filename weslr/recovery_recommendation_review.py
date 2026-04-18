"""Recovery Recommendation Review Surface (v77)

Read-only operator-facing review surface for distributed recovery recommendations.

Architecture:
  - RecoveryRecommendationReviewSurface — operator-readable review layer
  - Provides summary, rationale, confidence guidance, alternatives, safe-next-action
  - Correlates by flow/request/handshake/deadline IDs where relevant
  - Machine-readable export for operator tooling integration

Rules:
  - Read-only review only (no generation, no orchestration)
  - Confidence shown as guidance, not certainty
  - Alternative recommendations visible
  - Safe-next-action summary provided
  - Correlation visibility across flow/request/handshake/deadline IDs
  - Machine-readable export if needed for operator tooling
  - No TIA/C#
  - No execution logic
  - No backend/service/UI
  - Additive only (no breaking changes)
  - Reversible (single file removal)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# RECOVERY RECOMMENDATION REVIEW SURFACE
# ============================================================================


class RecoveryRecommendationReviewSurface:
    """Operator-facing read-only review surface for recovery recommendations.
    
    Provides operator-readable summaries of v75 recovery recommendations
    with visibility into rationale, confidence (as guidance, not certainty),
    alternative recommendations, and safe-next-action guidance.
    
    Does NOT generate recommendations (delegated to v75 RecoveryRecommendationService).
    Does NOT execute or orchestrate recovery actions.
    """
    
    def __init__(self):
        """Initialize review surface."""
        self._recommendations: Dict[str, Dict[str, Any]] = {}
        self._reviewed_recommendations: Dict[str, Dict[str, Any]] = {}
    
    def load_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
    ) -> None:
        """Load recommendations for review.
        
        Args:
            recommendations: List of recommendation dicts from v75 service
        """
        for rec in recommendations:
            rec_id = rec.get("recommendation_id", "")
            if rec_id:
                self._recommendations[rec_id] = rec.copy()
    
    def get_recommendation_summary(self) -> Dict[str, Any]:
        """Generate operator-readable summary of loaded recommendations.
        
        Returns:
            Summary dict with:
            - total_recommendations: Count
            - confidence_distribution: Operator guidance breakdown
            - most_common_cause: Most frequent likely cause
            - recommended_actions: Deduplicated recovery hints
            - correlation_ids_present: Summary of correlation coverage
        """
        if not self._recommendations:
            return {
                "total_recommendations": 0,
                "confidence_distribution": {},
                "most_common_cause": None,
                "recommended_actions": [],
                "correlation_ids_present": False,
                "correlation_summary": {},
            }
        
        # Count confidence levels (operator guidance)
        confidence_dist: Dict[str, int] = {}
        for rec in self._recommendations.values():
            conf = rec.get("confidence", "unknown")
            confidence_dist[conf] = confidence_dist.get(conf, 0) + 1
        
        # Find most common cause
        cause_counts: Dict[str, int] = {}
        for rec in self._recommendations.values():
            cause = rec.get("likely_cause", "Unknown")
            cause_counts[cause] = cause_counts.get(cause, 0) + 1
        
        most_common_cause = (
            max(cause_counts.keys(), key=lambda k: cause_counts[k])
            if cause_counts else None
        )
        
        # Deduplicate recovery hints
        actions = list(set(
            rec.get("recovery_hint", "None")
            for rec in self._recommendations.values()
            if rec.get("recovery_hint")
        ))
        
        # Check correlation coverage
        correlation_ids_present = any(
            rec.get("correlation_ids")
            for rec in self._recommendations.values()
        )
        
        # Correlation summary
        correlation_summary: Dict[str, int] = {}
        for rec in self._recommendations.values():
            corrs = rec.get("correlation_ids", {})
            for key in ["flow_id", "request_id", "handshake_id", "deadline_id"]:
                if corrs.get(key):
                    correlation_summary[key] = correlation_summary.get(key, 0) + 1
        
        return {
            "total_recommendations": len(self._recommendations),
            "confidence_distribution": confidence_dist,
            "most_common_cause": most_common_cause,
            "recommended_actions": actions,
            "correlation_ids_present": correlation_ids_present,
            "correlation_summary": correlation_summary,
        }
    
    def get_alternative_recommendations(self) -> List[Dict[str, Any]]:
        """Get alternative recommendation views.
        
        Returns:
            List of alternative recommendations (same recommendations, different view)
        """
        return list(self._recommendations.values())
    
    def get_safe_next_action(self) -> Dict[str, Any]:
        """Get operator-safe next-step guidance.
        
        Returns:
            Safe-next-action summary with:
            - recommended_action: Recommended next step
            - risk_level: Low/medium/high risk assessment
            - required_verification: What operator should verify before proceeding
            - fallback_options: Available fallback actions if recommended action fails
        """
        if not self._recommendations:
            return {
                "recommended_action": None,
                "risk_level": "unknown",
                "required_verification": [],
                "fallback_options": [],
            }
        
        # Determine risk level based on confidence and context
        confidences = [rec.get("confidence", "low") for rec in self._recommendations.values()]
        if "high" in confidences or "very_high" in confidences:
            risk_level = "low"
        elif "medium" in confidences:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Required verification based on failure stage
        stages = set(rec.get("stage", "") for rec in self._recommendations.values())
        required_verification = []
        if "proposal" in stages:
            required_verification.append("Verify proposal validation criteria")
        if "handshake" in stages:
            required_verification.append("Verify node capability and trust state")
        if "envelope" in stages:
            required_verification.append("Verify gate status and target availability")
        if "deadline" in stages:
            required_verification.append("Verify execution duration and heartbeat status")
        if not required_verification:
            required_verification.append("Review raw event logs for failure context")
        
        # Fallback options
        fallback_options = [
            "Retry with increased timeout thresholds",
            "Switch to alternative target node",
            "Reduce scope and retry with simpler proposal",
            "Escalate to operator for manual review",
        ]
        
        # Recommended action based on most common recovery hint
        actions = [rec.get("recovery_hint") for rec in self._recommendations.values() if rec.get("recovery_hint")]
        if actions:
            # Most common action
            action_counts: Dict[str, int] = {}
            for action in actions:
                action_counts[action] = action_counts.get(action, 0) + 1
            recommended_action = max(action_counts.keys(), key=lambda k: action_counts[k])
        else:
            recommended_action = "Review recovery hints and apply most appropriate action"
        
        return {
            "recommended_action": recommended_action,
            "risk_level": risk_level,
            "required_verification": required_verification,
            "fallback_options": fallback_options,
        }
    
    def get_confidence_guidance(self) -> Dict[str, Any]:
        """Get confidence levels presented as operator guidance.
        
        Returns:
            Confidence guidance dict with:
            - distribution: Confidence breakdown
            - meaning: Explanation that confidence indicates reliability, not guaranteed success
            - recommendations_by_confidence: Recommendations grouped by confidence level
        """
        if not self._recommendations:
            return {
                "distribution": {},
                "meaning": "No recommendations loaded",
                "recommendations_by_confidence": {},
            }
        
        # Distribution
        distribution: Dict[str, int] = {}
        for rec in self._recommendations.values():
            conf = rec.get("confidence", "unknown")
            distribution[conf] = distribution.get(conf, 0) + 1
        
        # Meaning (operator guidance)
        meaning = (
            "Confidence indicates reliability of the recommendation, "
            "not guaranteed success of the recovery action. "
            "Operator should verify conditions before proceeding."
        )
        
        # Group recommendations by confidence
        recommendations_by_confidence: Dict[str, List[Dict[str, Any]]] = {}
        for rec_id, rec in self._recommendations.items():
            conf = rec.get("confidence", "unknown")
            if conf not in recommendations_by_confidence:
                recommendations_by_confidence[conf] = []
            recommendations_by_confidence[conf].append({
                "recommendation_id": rec_id,
                "likely_cause": rec.get("likely_cause"),
                "recovery_hint": rec.get("recovery_hint"),
                "stage": rec.get("stage"),
                "failure_type": rec.get("failure_type"),
            })
        
        return {
            "distribution": distribution,
            "meaning": meaning,
            "recommendations_by_confidence": recommendations_by_confidence,
        }
    
    def get_recommendation_json(self) -> str:
        """Get machine-readable export of recommendations.
        
        Returns:
            JSON string with all recommendations and review metadata
        """
        export_data = {
            "review_surface_version": "v77",
            "export_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "summary": self.get_recommendation_summary(),
            "alternatives": self.get_alternative_recommendations(),
            "safe_next_action": self.get_safe_next_action(),
            "confidence_guidance": self.get_confidence_guidance(),
            "recommendations_by_id": {
                rec_id: {
                    **rec,
                    "hint_certainty": rec.get("hint_certainty", "suggestion"),
                }
                for rec_id, rec in self._recommendations.items()
            },
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def get_correlated_recommendations(
        self,
        flow_id: Optional[str] = None,
        request_id: Optional[str] = None,
        handshake_id: Optional[str] = None,
        deadline_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get recommendations filtered by correlation ID.
        
        Args:
            flow_id: Filter by flow ID
            request_id: Filter by request ID
            handshake_id: Filter by handshake ID
            deadline_id: Filter by deadline ID
            
        Returns:
            List of matching recommendations
        """
        matching: List[Dict[str, Any]] = []
        
        for rec_id, rec in self._recommendations.items():
            corrs = rec.get("correlation_ids", {})
            
            if flow_id and corrs.get("flow_id") == flow_id:
                matching.append({**rec, "recommendation_id": rec_id})
            elif request_id and corrs.get("request_id") == request_id:
                matching.append({**rec, "recommendation_id": rec_id})
            elif handshake_id and corrs.get("handshake_id") == handshake_id:
                matching.append({**rec, "recommendation_id": rec_id})
            elif deadline_id and corrs.get("deadline_id") == deadline_id:
                matching.append({**rec, "recommendation_id": rec_id})
            elif not any([flow_id, request_id, handshake_id, deadline_id]):
                matching.append({**rec, "recommendation_id": rec_id})
        
        return matching


# ============================================================================
# INTEGRATION HOOK
# ============================================================================


def integrate_with_v75_service(
    v75_service: Any,
) -> RecoveryRecommendationReviewSurface:
    """Integrate v75 recovery recommendation service with v77 review surface.
    
    This is purely additive — no migration required.
    
    v75: RecoveryRecommendationService handles recommendation generation.
    v77: RecoveryRecommendationReviewSurface presents recommendations for review.
    
    Args:
        v75_service: RecoveryRecommendationService instance
        
    Returns:
        RecoveryRecommendationReviewSurface with v75 recommendations loaded
    """
    review_surface = RecoveryRecommendationReviewSurface()
    
    recommendations = v75_service.get_all_recommendations()
    review_surface.load_recommendations(recommendations)
    
    return review_surface
