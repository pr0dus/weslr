# recovery_recommendation_service.py - WESLR v75: Recovery Recommendation Service
# Handles recovery recommendation generation and confidence presentation.
# Additive only, read-only, no orchestration, reversible.
# No TIA/C#, no telemetry backend, no dashboard.

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from .distributed_diagnostic_hooks import (
    FailureClassification,
    FailureStage,
    FailureType,
    StageDiagnosis,
)


# ============================================================================
# RECOVERY RECOMMENDATION SERVICE
# ============================================================================


class RecoveryRecommendationService:
    """Generates recovery recommendations with confidence guidance.
    
    Provides recovery hints as operator guidance, not certainty.
    Confidence levels indicate reliability of the recommendation,
    not guaranteed success.
    """
    
    def __init__(self):
        """Initialize recovery recommendation service."""
        self._recommendations: Dict[str, Dict[str, Any]] = {}
    
    def generate_recommendation(
        self,
        stage: str,
        failure_type: str,
        context: Dict[str, Any],
        correlation_ids: Dict[str, str],
    ) -> Dict[str, Any]:
        """Generate recovery recommendation for a failure.
        
        Args:
            stage: Failure stage (proposal, handshake, envelope, receipt, deadline)
            failure_type: Type of failure (failure_type enum value)
            context: Additional context for the failure
            correlation_ids: Correlation IDs for tracking
            
        Returns:
            Recommendation dict with:
            - recovery_hint: Suggested recovery action
            - confidence: Operator guidance level (low/medium/high)
            - likely_cause: Inferred root cause
            - contributing_factors: Additional context
            - hint_certainty: "suggestion" (not certainty)
        """
        recommendation_id = f"recovery_{len(self._recommendations)}"
        
        # Generate diagnosis (inference, not certainty)
        likely_cause, contributing_factors, recovery_hint = self._infer_diagnosis(
            stage, failure_type, context
        )
        
        # Determine confidence level as operator guidance
        confidence = self._determine_confidence(stage, failure_type, likely_cause)
        
        recommendation = {
            "recommendation_id": recommendation_id,
            "stage": stage,
            "failure_type": failure_type,
            "likely_cause": likely_cause,
            "contributing_factors": contributing_factors,
            "recovery_hint": recovery_hint,
            "confidence": confidence,  # Operator guidance level
            "hint_certainty": "suggestion",  # Not certainty
            "correlation_ids": correlation_ids,
            "generated_at": context.get("timestamp", "")
        }
        
        self._recommendations[recommendation_id] = recommendation
        return recommendation
    
    def _infer_diagnosis(
        self,
        stage: str,
        failure_type: str,
        context: Dict[str, Any]
    ) -> Tuple[Optional[str], List[str], Optional[str]]:
        """Infer likely cause and recovery hint.
        
        Returns (likely_cause, contributing_factors, recovery_hint)
        where hints are suggestions, not certainty.
        """
        # Stage-specific inference
        if stage == FailureStage.PROPOSAL.value:
            if failure_type == FailureType.PROPOSAL_REJECTED.value:
                return (
                    "Proposal was rejected by validation gates",
                    ["Trust threshold not met", "Health check failed", "Safety hooks blocked"],
                    "Review rejection reason and address blocking criteria"
                )
            elif failure_type == FailureType.PROPOSAL_EXPIRED.value:
                return (
                    "Proposal expired before approval",
                    ["TTL too short", "Operator delay in approval"],
                    "Increase proposal TTL or expedite approval workflow"
                )
            elif failure_type == FailureType.PROPOSAL_VALIDATION_FAILED.value:
                return (
                    "Proposal validation failed capability/trust checks",
                    ["Missing capability on target", "Insufficient trust level"],
                    "Verify target node capabilities and trust status"
                )
        
        elif stage == FailureStage.HANDSHAKE.value:
            if failure_type == FailureType.HANDSHAKE_FAILED.value:
                return (
                    "Handshake failed during protocol exchange",
                    ["Protocol version mismatch", "Capability negotiation failed"],
                    "Verify node protocol compatibility and capability registration"
                )
            elif failure_type == FailureType.HANDSHAKE_TRUST_REJECTED.value:
                return (
                    "Handshake rejected due to insufficient trust",
                    ["Target trust status below threshold", "Trust verification failed"],
                    "Review and update trust state for target node"
                )
            elif failure_type == FailureType.HANDSHAKE_HEALTH_REJECTED.value:
                return (
                    "Handshake rejected due to unhealthy target",
                    ["Target health status unhealthy", "Health check timeout"],
                    "Verify target node health or adjust health threshold"
                )
        
        elif stage == FailureStage.ENVELOPE.value:
            if failure_type == FailureType.ENVELOPE_GATE_FAILED.value:
                return (
                    "Execution envelope failed gate validation",
                    ["Trust gate failed", "Health gate failed", "Safety gate failed"],
                    "Review gate failure logs and address blocking criteria"
                )
            elif failure_type == FailureType.ENVELOPE_DISPATCH_FAILED.value:
                return (
                    "Execution envelope dispatch failed",
                    ["Target unreachable", "Network timeout", "Target not acknowledged"],
                    "Verify target availability and network connectivity"
                )
        
        elif stage == FailureStage.DEADLINE.value:
            if failure_type == FailureType.DEADLINE_BREACHED.value:
                return (
                    "Execution exceeded deadline",
                    ["Task duration exceeded limit", "No heartbeat within timeout"],
                    "Increase deadline threshold or optimize task execution"
                )
        
        elif stage == FailureStage.RECEIPT.value:
            return (
                "Receipt acknowledgment failed",
                ["Target did not acknowledge", "Receipt timeout", "Network partition"],
                "Verify target availability and receipt processing workflow"
            )
        
        return (
            "Unknown failure type",
            ["Insufficient diagnostic context"],
            "Review raw event logs for detailed failure information"
        )
    
    def _determine_confidence(
        self,
        stage: str,
        failure_type: str,
        likely_cause: Optional[str]
    ) -> str:
        """Determine confidence level as operator guidance.
        
        Confidence indicates reliability of the recommendation,
        not guaranteed success of the recovery action.
        
        Returns: "low", "medium", "high", or "very_high"
        """
        # Base confidence on failure type specificity
        if likely_cause is None or likely_cause == "Unknown failure type":
            return "low"
        
        # Stage-specific confidence modifiers
        stage_specificity = {
            FailureStage.PROPOSAL.value: 0.8,
            FailureStage.HANDSHAKE.value: 0.75,
            FailureStage.ENVELOPE.value: 0.7,
            FailureStage.DEADLINE.value: 0.85,
            FailureStage.RECEIPT.value: 0.65,
        }
        
        stage_multiplier = stage_specificity.get(stage, 0.6)
        
        # Calculate final confidence
        base_confidence = 0.6  # Baseline confidence level
        
        if "trust" in likely_cause.lower():
            confidence = base_confidence + 0.15
        elif "capability" in likely_cause.lower():
            confidence = base_confidence + 0.1
        elif "timeout" in likely_cause.lower():
            confidence = base_confidence + 0.2
        elif "validation" in likely_cause.lower():
            confidence = base_confidence + 0.05
        else:
            confidence = base_confidence + 0.05
        
        # Apply stage multiplier
        confidence *= stage_multiplier
        
        # Map to guidance levels
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        elif confidence >= 0.4:
            return "low"
        else:
            return "very_high"  # Very high confidence when clear pattern
    
    def build_recommendation_summary(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build summary of multiple recommendations.
        
        Args:
            recommendations: List of recommendation dicts
            
        Returns:
            Summary dict with:
            - total_recommendations: Count
            - confidence_distribution: Operator guidance breakdown
            - most_common_cause: Most frequent likely cause
            - recommended_actions: Deduplicated recovery hints
        """
        if not recommendations:
            return {
                "total_recommendations": 0,
                "confidence_distribution": {},
                "most_common_cause": None,
                "recommended_actions": []
            }
        
        # Count confidence levels (operator guidance)
        confidence_dist: Dict[str, int] = {}
        for rec in recommendations:
            conf = rec.get("confidence", "unknown")
            confidence_dist[conf] = confidence_dist.get(conf, 0) + 1
        
        # Find most common cause
        cause_counts: Dict[str, int] = {}
        for rec in recommendations:
            cause = rec.get("likely_cause", "Unknown")
            cause_counts[cause] = cause_counts.get(cause, 0) + 1
        
        most_common_cause = max(cause_counts.keys(), key=lambda k: cause_counts[k]) if cause_counts else None
        
        # Deduplicate recovery hints
        actions = list(set(
            rec.get("recovery_hint", "None") 
            for rec in recommendations 
            if rec.get("recovery_hint")
        ))
        
        return {
            "total_recommendations": len(recommendations),
            "confidence_distribution": confidence_dist,
            "most_common_cause": most_common_cause,
            "recommended_actions": actions
        }
    
    def get_recommendation_by_id(self, rec_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific recommendation by ID.
        
        Args:
            rec_id: Recommendation ID
            
        Returns:
            Recommendation dict or None
        """
        return self._recommendations.get(rec_id)
    
    def get_all_recommendations(self) -> List[Dict[str, Any]]:
        """Get all generated recommendations.
        
        Returns:
            List of recommendation dicts
        """
        return list(self._recommendations.values())


# ============================================================================
# INTEGRATION HOOKS
# ============================================================================


def integrate_with_distributed_diagnostic_hooks(
    stage: str,
    failure_type: str,
    context: Dict[str, Any],
    correlation_ids: Dict[str, str],
    service: RecoveryRecommendationService = None
) -> Dict[str, Any]:
    """Integrate recovery recommendation service with distributed diagnostics.
    
    This is purely additive — no migration required.
    
    v75: RecoveryRecommendationService handles recommendation logic;
    exporters format and present guidance (not certainty).
    """
    if service is None:
        service = RecoveryRecommendationService()
    
    recommendation = service.generate_recommendation(
        stage=stage,
        failure_type=failure_type,
        context=context,
        correlation_ids=correlation_ids
    )
    
    return recommendation


def integrate_with_exporters(
    recommendation: Dict[str, Any]
) -> Dict[str, Any]:
    """Prepare recommendation for export with confidence guidance.
    
    v75: Confidence presented as operator guidance, not certainty.
    Exports should include "hint_certainty": "suggestion" to clarify.
    
    Args:
        recommendation: Recommendation dict from service
        
    Returns:
        Export-ready dict with proper guidance markers
    """
    # Ensure hint_certainty is set for operators
    if "hint_certainty" not in recommendation:
        recommendation["hint_certainty"] = "suggestion"
    
    # Add confidence explanation for operators
    confidence = recommendation.get("confidence", "medium")
    recommendation["confidence_explanation"] = {
        "level": confidence,
        "meaning": f"Operator guidance level: {confidence}. "
                   "This indicates reliability of the recommendation, "
                   "not guaranteed success of the recovery action."
    }
    
    return recommendation
