# outcome_feedback.py - v32: Outcome Feedback / Real-World Calibration Layer
# Creates a governed real-world feedback loop allowing WESLR to learn from actual
# recommendation outcomes and calibrate future guidance quality.
# Additive only, transparent, reversible, user/operator reported outcome first,
# no hidden learning, no repo drift. Local to WESLR scope.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class RecommendationStatus(str, Enum):
    """Status of a recommendation outcome."""
    ISSUED = "issued"  # Recommendation was issued
    FOLLOWED = "followed"  # User followed the recommendation
    IGNORED = "ignored"  # User ignored the recommendation
    REJECTED = "rejected"  # User explicitly rejected the recommendation
    PARTIALLY_FOLLOWED = "partially_followed"  # User partially followed
    EXPIRED = "expired"  # Recommendation expired before action


class OutcomeQuality(str, Enum):
    """Quality of outcome after following recommendation."""
    EXCELLENT = "excellent"  # Better than expected
    GOOD = "good"  # Met expectations
    ADEQUATE = "adequate"  # Barely acceptable
    POOR = "poor"  # Failed to help
    HARMFUL = "harmful"  # Caused problems
    NEUTRAL = "neutral"  # No measurable impact


class ConfidenceAdjustment(str, Enum):
    """Direction of confidence adjustment."""
    INCREASE = "increase"  # Confidence increased
    DECREASE = "decrease"  # Confidence decreased
    MAINTAIN = "maintain"  # Confidence unchanged
    RESET = "reset"  # Reset to base level


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class RecommendationFeedback:
    """Feedback from real-world outcome of a recommendation."""
    
    feedback_id: str  # Unique identifier for this feedback
    recommendation_id: str  # ID of the recommendation this is about
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    # User/operator reported
    status: str = RecommendationStatus.ISSUED.value  # Final status
    outcome_quality: Optional[str] = None  # Quality of outcome if followed
    user_rating: Optional[int] = None  # User rating (1-5)
    user_comment: Optional[str] = None  # User-provided comment
    
    # Impact metrics
    stress_delta: float = 0.0  # Change in stress level (negative = reduction)
    satisfaction: float = 0.0  # User satisfaction (0.0-1.0)
    household_impact: str = "neutral"  # "positive", "neutral", "negative"
    
    # Calibration data
    confidence_adjustment: float = 0.0  # Amount of confidence change
    adjustment_direction: Optional[str] = None  # "increase", "decrease", "maintain"
    calibration_timestamp: Optional[str] = None  # When calibration was applied
    
    # Metadata
    reported_by: str = "operator"  # "user", "operator", "system"
    calibration_reason: Optional[str] = None  # Why calibration was applied
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "feedback_id": self.feedback_id,
            "recommendation_id": self.recommendation_id,
            "timestamp": self.timestamp,
            "status": self.status,
            "outcome_quality": self.outcome_quality,
            "user_rating": self.user_rating,
            "user_comment": self.user_comment,
            "stress_delta": self.stress_delta,
            "satisfaction": self.satisfaction,
            "household_impact": self.household_impact,
            "confidence_adjustment": self.confidence_adjustment,
            "adjustment_direction": self.adjustment_direction,
            "calibration_timestamp": self.calibration_timestamp,
            "reported_by": self.reported_by,
            "calibration_reason": self.calibration_reason,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RecommendationFeedback:
        """Create from dictionary representation."""
        return cls(**data)
    
    def apply_calibration(self, adjustment: float, reason: Optional[str] = None) -> None:
        """Apply calibration to this feedback."""
        self.confidence_adjustment = adjustment
        self.calibration_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.calibration_reason = reason
        
        if adjustment > 0:
            self.adjustment_direction = ConfidenceAdjustment.INCREASE.value
        elif adjustment < 0:
            self.adjustment_direction = ConfidenceAdjustment.DECREASE.value
        else:
            self.adjustment_direction = ConfidenceAdjustment.MAINTAIN.value


@dataclass
class FeedbackSummary:
    """Summary of feedback statistics for a recommendation or pattern."""
    
    recommendation_id: str
    feedback_count: int = 0
    status_counts: Dict[str, int] = field(default_factory=dict)
    average_outcome_quality: float = 0.0
    average_confidence_adjustment: float = 0.0
    average_stress_delta: float = 0.0
    average_satisfaction: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "recommendation_id": self.recommendation_id,
            "feedback_count": self.feedback_count,
            "status_counts": self.status_counts,
            "average_outcome_quality": self.average_outcome_quality,
            "average_confidence_adjustment": self.average_confidence_adjustment,
            "average_stress_delta": self.average_stress_delta,
            "average_satisfaction": self.average_satisfaction,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FeedbackSummary:
        """Create from dictionary representation."""
        data["status_counts"] = data.get("status_counts", {})
        return cls(**data)
    
    def update_from_feedback(self, feedback: RecommendationFeedback) -> None:
        """Update summary from a new feedback."""
        self.feedback_count += 1
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Update status counts
        if feedback.status not in self.status_counts:
            self.status_counts[feedback.status] = 0
        self.status_counts[feedback.status] += 1
        
        # Update averages
        total = self.feedback_count
        
        # Outcome quality (0.0-1.0 where excellent=1.0, good=0.8, etc.)
        quality_map = {
            "excellent": 1.0,
            "good": 0.8,
            "adequate": 0.6,
            "poor": 0.3,
            "harmful": 0.0,
            "neutral": 0.5,
        }
        if feedback.outcome_quality:
            quality = quality_map.get(feedback.outcome_quality, 0.5)
            self.average_outcome_quality = (
                (self.average_outcome_quality * (total - 1) + quality) / total
            )
        
        # Satisfaction
        if feedback.satisfaction > 0:
            self.average_satisfaction = (
                (self.average_satisfaction * (total - 1) + feedback.satisfaction) / total
            )
        
        # Confidence adjustment
        self.average_confidence_adjustment = (
            (self.average_confidence_adjustment * (total - 1) + feedback.confidence_adjustment) / total
        )
        
        # Stress delta
        self.average_stress_delta = (
            (self.average_stress_delta * (total - 1) + feedback.stress_delta) / total
        )


@dataclass
class CalibrationRecord:
    """Record of calibration adjustments made to recommendations."""
    
    record_id: str  # Unique identifier
    recommendation_id: str
    adjustment_amount: float  # Amount of confidence adjustment
    adjustment_reason: str  # Why this adjustment was made
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "record_id": self.record_id,
            "recommendation_id": self.recommendation_id,
            "adjustment_amount": self.adjustment_amount,
            "adjustment_reason": self.adjustment_reason,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CalibrationRecord:
        """Create from dictionary representation."""
        return cls(**data)


# ============================================================================
# FEEDBACK MANAGER
# ============================================================================


class OutcomeFeedbackManager:
    """Manager for outcome feedback and calibration.
    
    Provides add-only, persistent storage with transparency.
    All feedback is user/operator reported and reversible.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize outcome feedback manager."""
        self.storage_path = storage_path or self._get_default_path()
        self.feedback: Dict[str, RecommendationFeedback] = {}  # feedback_id -> Feedback
        self.summaries: Dict[str, FeedbackSummary] = {}  # recommendation_id -> Summary
        self.calibration_records: List[CalibrationRecord] = []
        self._ensure_storage_exists()
        self._load_feedback()
    
    def _get_default_path(self) -> str:
        """Get default storage path."""
        return "/data/data/com.termux/files/home/.openclaw/workspace/weslr/outcome_feedback/"
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_feedback(self) -> None:
        """Load feedback from storage."""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith("_feedback.json"):
                feedback_id = filename[:-14]  # Remove _feedback.json
                try:
                    with open(os.path.join(self.storage_path, filename), "r") as f:
                        data = json.load(f)
                        self.feedback[feedback_id] = RecommendationFeedback.from_dict(data)
                        # Also create summary if needed
                        rec_id = data.get("recommendation_id")
                        if rec_id and rec_id not in self.summaries:
                            self.summaries[rec_id] = FeedbackSummary(recommendation_id=rec_id)
                except Exception:
                    # Skip malformed files
                    continue
        
        # Load calibration records
        calib_path = os.path.join(self.storage_path, "calibration_records.json")
        if os.path.exists(calib_path):
            try:
                with open(calib_path, "r") as f:
                    data = json.load(f)
                    for record_data in data.get("records", []):
                        self.calibration_records.append(CalibrationRecord.from_dict(record_data))
            except Exception:
                pass
    
    def _save_feedback(self, feedback_id: str) -> None:
        """Save a feedback item to storage."""
        import os
        filepath = os.path.join(self.storage_path, f"{feedback_id}_feedback.json")
        data = self.feedback[feedback_id].to_dict()
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def _save_summaries(self) -> None:
        """Save all summaries to storage."""
        import os
        filepath = os.path.join(self.storage_path, "summaries.json")
        data = {
            "summaries": {k: v.to_dict() for k, v in self.summaries.items()},
            "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def _save_calibrations(self) -> None:
        """Save calibration records to storage."""
        import os
        filepath = os.path.join(self.storage_path, "calibration_records.json")
        data = {
            "records": [r.to_dict() for r in self.calibration_records],
            "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def record_feedback(
        self,
        recommendation_id: str,
        status: str,
        reported_by: str = "operator",
        outcome_quality: Optional[str] = None,
        user_rating: Optional[int] = None,
        user_comment: Optional[str] = None,
        stress_delta: float = 0.0,
        satisfaction: float = 0.0,
        household_impact: str = "neutral",
        confidence_adjustment: float = 0.0,
        calibration_reason: Optional[str] = None,
    ) -> RecommendationFeedback:
        """Record feedback for a recommendation."""
        feedback_id = f"fb-{len(self.feedback) + 1:04d}"
        
        feedback = RecommendationFeedback(
            feedback_id=feedback_id,
            recommendation_id=recommendation_id,
            status=status,
            reported_by=reported_by,
            outcome_quality=outcome_quality,
            user_rating=user_rating,
            user_comment=user_comment,
            stress_delta=stress_delta,
            satisfaction=satisfaction,
            household_impact=household_impact,
            confidence_adjustment=confidence_adjustment,
        )
        
        # Apply calibration if adjustment is non-zero
        if confidence_adjustment != 0 and calibration_reason:
            feedback.apply_calibration(confidence_adjustment, calibration_reason)
        
        self.feedback[feedback_id] = feedback
        self._save_feedback(feedback_id)
        
        # Update summary
        if recommendation_id not in self.summaries:
            self.summaries[recommendation_id] = FeedbackSummary(recommendation_id=recommendation_id)
        self.summaries[recommendation_id].update_from_feedback(feedback)
        self._save_summaries()
        
        return feedback
    
    def apply_calibration(
        self,
        recommendation_id: str,
        adjustment_amount: float,
        reason: str,
    ) -> CalibrationRecord:
        """Apply calibration to a recommendation's future guidance."""
        record_id = f"cal-{len(self.calibration_records) + 1:04d}"
        
        record = CalibrationRecord(
            record_id=record_id,
            recommendation_id=recommendation_id,
            adjustment_amount=adjustment_amount,
            adjustment_reason=reason,
        )
        
        self.calibration_records.append(record)
        self._save_calibrations()
        
        return record
    
    def get_summary(self, recommendation_id: str) -> Optional[FeedbackSummary]:
        """Get feedback summary for a recommendation."""
        return self.summaries.get(recommendation_id)
    
    def get_feedback(self, feedback_id: str) -> Optional[RecommendationFeedback]:
        """Get feedback by ID."""
        return self.feedback.get(feedback_id)
    
    def get_all_feedback_for_recommendation(self, recommendation_id: str) -> List[RecommendationFeedback]:
        """Get all feedback for a specific recommendation."""
        return [
            fb for fb in self.feedback.values()
            if fb.recommendation_id == recommendation_id
        ]
    
    def get_all_calibrations(self) -> List[CalibrationRecord]:
        """Get all calibration records."""
        return self.calibration_records
    
    def get_all_feedback(self) -> Dict[str, RecommendationFeedback]:
        """Get all feedback."""
        return self.feedback
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary."""
        return {
            "feedback_count": len(self.feedback),
            "summary_count": len(self.summaries),
            "calibration_count": len(self.calibration_records),
            "feedback": {k: v.to_dict() for k, v in self.feedback.items()},
            "summaries": {k: v.to_dict() for k, v in self.summaries.items()},
        }


# ============================================================================
# CALIBRATION ENGINE
# ============================================================================


class CalibrationEngine:
    """Engine for applying feedback-based calibration to guidance.
    
    Uses real-world outcomes to adjust future confidence and recommendations.
    """
    
    def __init__(self, feedback_manager: OutcomeFeedbackManager):
        """Initialize calibration engine."""
        self.feedback_manager = feedback_manager
    
    def get_calibration_impact(self, recommendation_id: str) -> Dict[str, Any]:
        """Get the calibration impact for a recommendation."""
        summary = self.feedback_manager.get_summary(recommendation_id)
        if not summary:
            return {
                "has_calibration": False,
                "recommendation": "No feedback available",
                "confidence_impact": 0.0,
            }
        
        impact = summary.average_confidence_adjustment
        
        return {
            "has_calibration": True,
            "feedback_count": summary.feedback_count,
            "average_outcome_quality": summary.average_outcome_quality,
            "average_satisfaction": summary.average_satisfaction,
            "average_stress_delta": summary.average_stress_delta,
            "average_confidence_adjustment": impact,
            "recommendation": self._get_calibration_recommendation(impact, summary),
            "confidence_impact": impact,
        }
    
    def _get_calibration_recommendation(self, impact: float, summary: FeedbackSummary) -> str:
        """Get recommendation based on calibration impact."""
        if impact > 0.1:
            return "Recommendation has been effective - maintain or increase confidence"
        elif impact > 0.05:
            return "Recommendation is generally effective - minor confidence adjustment"
        elif impact > -0.05:
            return "Recommendation is neutral - maintain current confidence"
        elif impact > -0.15:
            return "Recommendation needs slight adjustment - reduce confidence slightly"
        elif impact > -0.3:
            return "Recommendation is often ignored or ineffective - significantly reduce confidence"
        else:
            return "Recommendation is frequently harmful or ignored - reconsider implementation"
    
    def adjust_recommendation_confidence(
        self,
        recommendation_id: str,
        base_confidence: float,
    ) -> float:
        """Adjust confidence based on real-world calibration."""
        summary = self.feedback_manager.get_summary(recommendation_id)
        if not summary or summary.feedback_count < 2:
            return base_confidence  # Not enough data for calibration
        
        calibration_impact = summary.average_confidence_adjustment
        adjusted_confidence = base_confidence + calibration_impact
        
        # Clamp to valid range
        return max(0.0, min(1.0, adjusted_confidence))
    
    def get_future_recommendation_quality(
        self,
        recommendation_id: str,
        base_confidence: float,
    ) -> Dict[str, Any]:
        """Predict future recommendation quality based on calibration."""
        calibration = self.get_calibration_impact(recommendation_id)
        adjusted_confidence = self.adjust_recommendation_confidence(
            recommendation_id, base_confidence
        )
        
        return {
            "recommendation_id": recommendation_id,
            "base_confidence": base_confidence,
            "adjusted_confidence": adjusted_confidence,
            "calibration_impact": calibration["confidence_impact"],
            "expected_outcome": self._get_expected_outcome(adjusted_confidence, calibration),
        }
    
    def _get_expected_outcome(self, adjusted_confidence: float, calibration: Dict[str, Any]) -> str:
        """Get expected outcome based on adjusted confidence."""
        if adjusted_confidence >= 0.7:
            return "high quality, likely effective"
        elif adjusted_confidence >= 0.5:
            return "moderate quality, may be effective"
        elif adjusted_confidence >= 0.3:
            return "low quality, may need adjustment"
        else:
            return "very low quality, reconsider implementation"


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add outcome feedback context to adaptive guidance.
    
    This is purely additive — no migration required.
    """
    if "feedback_available" not in guidance_dict:
        guidance_dict["feedback_available"] = False
    if "calibration_impact" not in guidance_dict:
        guidance_dict["calibration_impact"] = 0.0
    if "adjusted_confidence" not in guidance_dict:
        guidance_dict["adjusted_confidence"] = None
    return guidance_dict


def integrate_with_longitudinal_patterns(patterns_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add outcome feedback to longitudinal patterns.
    
    This is purely additive — no migration required.
    """
    if "feedback_impact" not in patterns_dict:
        patterns_dict["feedback_impact"] = None
    if "calibration_history" not in patterns_dict:
        patterns_dict["calibration_history"] = []
    return patterns_dict


def integrate_with_operator_context(context_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add outcome feedback awareness to operator context.
    
    This is purely additive — no migration required.
    """
    if "feedback_available" not in context_dict:
        context_dict["feedback_available"] = False
    if "calibration_summary" not in context_dict:
        context_dict["calibration_summary"] = None
    if "reliability_from_feedback" not in context_dict:
        context_dict["reliability_from_feedback"] = None
    return context_dict
