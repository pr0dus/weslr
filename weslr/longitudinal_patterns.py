# longitudinal_patterns.py - v28: Longitudinal User Pattern / Routine Memory Layer
# Creates a governed temporal memory layer to help WESLR learn user routines,
# recurring goals, successful guidance patterns, and overload/stress patterns over time.
# Additive only, transparent, suggestion-based, non-manipulative, reversible.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class PatternType(str, Enum):
    """Types of patterns tracked in longitudinal memory."""
    ROUTINE = "routine"  # Recurring temporal patterns
    GOAL = "goal"  # Recurring goals
    SUCCESSFUL_GUIDANCE = "successful_guidance"  # Guidance that was accepted
    IGNORED_GUIDANCE = "ignored_guidance"  # Guidance that was not acted upon
    OVERLOAD_MARKER = "overload_marker"  # User stress/cognitive overload
    HOUSEHOLD_RHYTHM = "household_rhythm"  # Household activity patterns
    CONTEXT_PATTERN = "context_pattern"  # Recurring context combinations


class PatternStability(str, Enum):
    """Stability level of a pattern."""
    FLUID = "fluid"  # New, unstable, changing rapidly
    DEVELOPING = "developing"  # Gaining consistency
    STABLE = "stable"  # Well-established, consistent
    LOCKED = "locked"  # High confidence, rarely changes


class GuidanceAdaptationMode(str, Enum):
    """Mode for adapting guidance based on patterns."""
    ACTIVE = "active"  # Apply pattern-based adaptation
    RESTRICTED = "restricted"  # Apply with caution
    SILENT = "silent"  # Apply internally without explicit output
    OFF = "off"  # Disable pattern-based adaptation


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class PatternObservation:
    """A single observation of a pattern."""
    
    timestamp: str  # ISO-8601 UTC timestamp
    context: Dict[str, Any]  # Context at time of observation
    outcome: Optional[str] = None  # Outcome (e.g., "accepted", "ignored", "pending")
    confidence: float = 0.5  # Confidence in this observation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "context": self.context,
            "outcome": self.outcome,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PatternObservation:
        """Create from dictionary representation."""
        return cls(**data)


@dataclass
class PatternSummary:
    """Summary statistics for a pattern."""
    
    pattern_id: str
    pattern_type: str  # PatternType value
    first_observed: str  # ISO-8601 UTC timestamp
    last_observed: str  # ISO-8601 UTC timestamp
    frequency: int = 0  # Number of observations
    stability: str = PatternStability.FLUID.value  # PatternStability value
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    # Context signature (hash of recurring context elements)
    context_signature: Optional[str] = None
    
    # Pattern-specific metrics
    success_count: int = 0  # For guidance patterns
    ignore_count: int = 0  # For guidance patterns
    average_confidence: float = 0.5
    
    # Recurrence info
    avg_interval_hours: Optional[float] = None
    predicted_next_occurrence: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "first_observed": self.first_observed,
            "last_observed": self.last_observed,
            "frequency": self.frequency,
            "stability": self.stability,
            "last_updated": self.last_updated,
            "context_signature": self.context_signature,
            "success_count": self.success_count,
            "ignore_count": self.ignore_count,
            "average_confidence": self.average_confidence,
            "avg_interval_hours": self.avg_interval_hours,
            "predicted_next_occurrence": self.predicted_next_occurrence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PatternSummary:
        """Create from dictionary representation."""
        return cls(**data)
    
    def update_from_observation(self, observation: PatternObservation) -> None:
        """Update summary from a new observation."""
        self.frequency += 1
        self.last_observed = observation.timestamp
        
        # Update confidence average
        total_conf = self.average_confidence * (self.frequency - 1) + observation.confidence
        self.average_confidence = total_conf / self.frequency
        
        # Update stability based on frequency
        if self.frequency >= 20:
            self.stability = PatternStability.LOCKED.value
        elif self.frequency >= 10:
            self.stability = PatternStability.STABLE.value
        elif self.frequency >= 5:
            self.stability = PatternStability.DEVELOPING.value
        else:
            self.stability = PatternStability.FLUID.value
        
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def get_pattern_age_hours(self) -> float:
        """Get age of pattern in hours."""
        try:
            first = datetime.fromisoformat(self.first_observed.replace("Z", "+00:00"))
            last = datetime.fromisoformat(self.last_observed.replace("Z", "+00:00"))
            delta = last - first
            return delta.total_seconds() / 3600
        except Exception:
            return 0.0


@dataclass
class PatternMemory:
    """A complete pattern memory with observations and summary."""
    
    summary: PatternSummary
    observations: List[PatternObservation] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "summary": self.summary.to_dict(),
            "observations": [obs.to_dict() for obs in self.observations],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PatternMemory:
        """Create from dictionary representation."""
        summary_data = data.get("summary", {})
        observations_data = data.get("observations", [])
        
        summary = PatternSummary.from_dict(summary_data)
        observations = [PatternObservation.from_dict(obs) for obs in observations_data]
        
        return cls(summary=summary, observations=observations)
    
    def add_observation(self, observation: PatternObservation) -> None:
        """Add an observation and update summary."""
        self.observations.append(observation)
        self.summary.update_from_observation(observation)


# ============================================================================
# PATTERN MEMORY STORAGE
# ============================================================================


class PatternMemoryStorage:
    """Storage layer for pattern memory.
    
    Provides add-only, persistent storage with transparency.
    All patterns are reversible and non-manipulative.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize pattern memory storage."""
        self.storage_path = storage_path or self._get_default_path()
        self.patterns: Dict[str, PatternMemory] = {}  # pattern_id -> PatternMemory
        self._ensure_storage_exists()
        self._load_patterns()
    
    def _get_default_path(self) -> str:
        """Get default storage path."""
        return "/data/data/com.termux/files/home/.openclaw/workspace/weslr/pattern_memory/"
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_patterns(self) -> None:
        """Load patterns from storage."""
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".json"):
                pattern_id = filename[:-5]  # Remove .json extension
                try:
                    with open(os.path.join(self.storage_path, filename), "r") as f:
                        data = json.load(f)
                        self.patterns[pattern_id] = PatternMemory.from_dict(data)
                except Exception:
                    # Skip malformed files
                    continue
    
    def _save_pattern(self, pattern_id: str) -> None:
        """Save a pattern to storage."""
        if pattern_id not in self.patterns:
            return
        
        filepath = os.path.join(self.storage_path, f"{pattern_id}.json")
        data = self.patterns[pattern_id].to_dict()
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def create_pattern(
        self,
        pattern_type: str,
        context: Dict[str, Any],
        initial_confidence: float = 0.5,
        outcome: Optional[str] = None,
    ) -> PatternMemory:
        """Create a new pattern memory."""
        pattern_id = self._generate_pattern_id(pattern_type, context)
        
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        summary = PatternSummary(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            first_observed=timestamp,
            last_observed=timestamp,
            frequency=0,
            context_signature=self._generate_context_signature(context),
        )
        
        observation = PatternObservation(
            timestamp=timestamp,
            context=context,
            confidence=initial_confidence,
            outcome=outcome,
        )
        
        pattern_memory = PatternMemory(
            summary=summary,
            observations=[observation],
        )
        
        # Immediately update summary with the first observation
        pattern_memory.summary.update_from_observation(observation)
        
        self.patterns[pattern_id] = pattern_memory
        self._save_pattern(pattern_id)
        
        return pattern_memory
    
    def _generate_pattern_id(self, pattern_type: str, context: Dict[str, Any]) -> str:
        """Generate a unique pattern ID."""
        # Create a hash-like ID from type and key context elements
        key_elements = [pattern_type]
        for k, v in sorted(context.items()):
            if k in ["task", "domain", "time_of_day", "day_of_week"]:
                key_elements.append(f"{k}:{v}")
        
        import hashlib
        hash_input = "|".join(key_elements)
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        
        return f"{pattern_type}_{hash_value}"
    
    def _generate_context_signature(self, context: Dict[str, Any]) -> Optional[str]:
        """Generate a signature for recurring context patterns."""
        # Use key temporal/context elements
        key_elements = []
        for k, v in sorted(context.items()):
            if k in ["time_of_day", "day_of_week", "task", "domain", "user_state"]:
                key_elements.append(f"{k}:{v}")
        
        if not key_elements:
            return None
        
        import hashlib
        return hashlib.md5("|".join(key_elements).encode()).hexdigest()[:16]
    
    def get_pattern(self, pattern_id: str) -> Optional[PatternMemory]:
        """Get a pattern memory by ID."""
        return self.patterns.get(pattern_id)
    
    def find_patterns_by_type(self, pattern_type: str) -> List[PatternMemory]:
        """Find all patterns of a given type."""
        return [
            pattern for pattern in self.patterns.values()
            if pattern.summary.pattern_type == pattern_type
        ]
    
    def find_patterns_by_signature(self, context_signature: str) -> List[PatternMemory]:
        """Find patterns matching a context signature."""
        return [
            pattern for pattern in self.patterns.values()
            if pattern.summary.context_signature == context_signature
        ]
    
    def record_observation(
        self,
        pattern_type: str,
        context: Dict[str, Any],
        outcome: Optional[str] = None,
        confidence: float = 0.5,
    ) -> PatternMemory:
        """Record a new observation, creating pattern if needed."""
        pattern_id = self._generate_pattern_id(pattern_type, context)
        
        pattern_existed = pattern_id in self.patterns
        
        if pattern_existed:
            pattern_memory = self.patterns[pattern_id]
        else:
            pattern_memory = self.create_pattern(pattern_type, context, confidence, outcome)
        
        # Only add another observation if pattern already existed
        # If it was just created, the initial observation is already there
        if pattern_existed:
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            observation = PatternObservation(
                timestamp=timestamp,
                context=context,
                outcome=outcome,
                confidence=confidence,
            )
            pattern_memory.add_observation(observation)
        
        self._save_pattern(pattern_id)
        
        return pattern_memory
    
    def update_pattern_stability(self, pattern_id: str, new_stability: str) -> None:
        """Update pattern stability (for manual intervention)."""
        if pattern_id not in self.patterns:
            return
        
        self.patterns[pattern_id].summary.stability = new_stability
        self._save_pattern(pattern_id)
    
    def get_all_patterns(self) -> Dict[str, PatternMemory]:
        """Get all pattern memories."""
        return self.patterns
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert storage to dictionary representation."""
        return {
            "pattern_count": len(self.patterns),
            "patterns": {
                pattern_id: pattern.summary.to_dict()
                for pattern_id, pattern in self.patterns.items()
            },
        }


# ============================================================================
# PATTERN ANALYZER
# ============================================================================


class PatternAnalyzer:
    """Analyzer for longitudinal patterns.
    
    Provides insights on patterns without modifying them.
    """
    
    def __init__(self, storage: PatternMemoryStorage):
        """Initialize pattern analyzer."""
        self.storage = storage
    
    def analyze_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """Analyze a pattern and return insights."""
        pattern = self.storage.get_pattern(pattern_id)
        if not pattern:
            return {"error": "Pattern not found"}
        
        summary = pattern.summary
        observations = pattern.observations
        
        # Calculate frequency metrics
        total_obs = len(observations)
        
        # Calculate stability indicators
        stability_indicators = self._calculate_stability_indicators(observations)
        
        # Calculate pattern regularity
        regularity = self._calculate_regularity(observations)
        
        # Calculate outcome distribution (for guidance patterns)
        outcome_dist = self._calculate_outcome_distribution(observations)
        
        return {
            "pattern_id": summary.pattern_id,
            "pattern_type": summary.pattern_type,
            "frequency": summary.frequency,
            "stability": summary.stability,
            "first_observed": summary.first_observed,
            "last_observed": summary.last_observed,
            "total_observations": total_obs,
            "stability_indicators": stability_indicators,
            "regularity": regularity,
            "outcome_distribution": outcome_dist,
            "avg_confidence": summary.average_confidence,
        }
    
    def _calculate_stability_indicators(self, observations: List[PatternObservation]) -> Dict[str, Any]:
        """Calculate stability indicators from observations."""
        if len(observations) < 2:
            return {
                "confidence": 0.0,
                "variance": None,
                "recommendation": PatternStability.FLUID.value,
            }
        
        # Calculate confidence variance
        confidences = [obs.confidence for obs in observations]
        mean_conf = sum(confidences) / len(confidences)
        variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
        
        # Recommendation based on variance and count
        if variance < 0.05 and len(observations) >= 10:
            recommendation = PatternStability.STABLE.value
        elif variance < 0.15 and len(observations) >= 5:
            recommendation = PatternStability.DEVELOPING.value
        else:
            recommendation = PatternStability.FLUID.value
        
        return {
            "confidence": mean_conf,
            "variance": variance,
            "observation_count": len(confidences),
            "recommendation": recommendation,
        }
    
    def _calculate_regularity(self, observations: List[PatternObservation]) -> Dict[str, Any]:
        """Calculate temporal regularity of observations."""
        if len(observations) < 2:
            return {
                "regularity_score": 0.0,
                "interval_variance": None,
                "pattern": "insufficient_data",
            }
        
        # Sort by timestamp
        sorted_obs = sorted(observations, key=lambda o: o.timestamp)
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(sorted_obs)):
            try:
                t1 = datetime.fromisoformat(sorted_obs[i-1].timestamp.replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(sorted_obs[i].timestamp.replace("Z", "+00:00"))
                delta = (t2 - t1).total_seconds() / 3600  # Hours
                intervals.append(delta)
            except Exception:
                continue
        
        if not intervals:
            return {
                "regularity_score": 0.0,
                "interval_variance": None,
                "pattern": "insufficient_data",
            }
        
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((i - mean_interval) ** 2 for i in intervals) / len(intervals)
        
        # Score regularity (lower variance = more regular)
        regularity_score = max(0, 1 - (variance / 24))  # 24 hours variance baseline
        
        # Determine pattern type
        if variance < 1:
            pattern = "highly_regular"
        elif variance < 6:
            pattern = "moderately_regular"
        elif variance < 24:
            pattern = "irregular"
        else:
            pattern = "very_irregular"
        
        return {
            "regularity_score": regularity_score,
            "interval_variance": variance,
            "mean_interval_hours": mean_interval,
            "pattern": pattern,
        }
    
    def _calculate_outcome_distribution(self, observations: List[PatternObservation]) -> Dict[str, Any]:
        """Calculate outcome distribution for guidance patterns."""
        outcomes = {"accepted": 0, "ignored": 0, "pending": 0, "unknown": 0}
        
        for obs in observations:
            if obs.outcome == "accepted":
                outcomes["accepted"] += 1
            elif obs.outcome == "ignored":
                outcomes["ignored"] += 1
            elif obs.outcome == "pending":
                outcomes["pending"] += 1
            else:
                outcomes["unknown"] += 1
        
        total = sum(outcomes.values())
        if total == 0:
            return outcomes
        
        return {
            "accepted": outcomes["accepted"],
            "ignored": outcomes["ignored"],
            "pending": outcomes["pending"],
            "unknown": outcomes["unknown"],
            "total": total,
            "acceptance_rate": outcomes["accepted"] / total if total > 0 else 0,
        }


# ============================================================================
# GUIDANCE ADAPTATION ENGINE
# ============================================================================


class LongitudinalGuidanceAdapter:
    """Adapt guidance based on longitudinal patterns.
    
    Uses pattern memory to inform guidance behavior:
    - Successful guidance increases confidence
    - Repeated ignored guidance reduces aggressiveness
    - Overload patterns trigger hold-back
    """
    
    def __init__(self, storage: PatternMemoryStorage):
        """Initialize longitudinal guidance adapter."""
        self.storage = storage
        self.pattern_analyzer = PatternAnalyzer(storage)
    
    def get_guidance_adaptation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get guidance adaptation based on patterns."""
        adaptations = []
        
        # Check for overload patterns
        overload_adaptation = self._check_overload_pattern(context)
        if overload_adaptation:
            adaptations.append(overload_adaptation)
        
        # Check for successful guidance patterns
        successful_adaptation = self._check_successful_guidance_pattern(context)
        if successful_adaptation:
            adaptations.append(successful_adaptation)
        
        # Check for ignored guidance patterns
        ignored_adaptation = self._check_ignored_guidance_pattern(context)
        if ignored_adaptation:
            adaptations.append(ignored_adaptation)
        
        # Check for routine context
        routine_adaptation = self._check_routine_pattern(context)
        if routine_adaptation:
            adaptations.append(routine_adaptation)
        
        return {
            "adaptations": adaptations,
            "adaptation_count": len(adaptations),
            "should_hold_back": any(a.get("type") == "overload" for a in adaptations),
            "confidence_boost": sum(a.get("confidence_boost", 0) for a in adaptations),
            "aggressiveness_reduction": sum(a.get("aggressiveness_reduction", 0) for a in adaptations),
        }
    
    def _check_overload_pattern(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for overload patterns and return adaptation."""
        overload_patterns = self.storage.find_patterns_by_type(PatternType.OVERLOAD_MARKER.value)
        
        for pattern in overload_patterns:
            if self._context_matches_pattern(context, pattern):
                return {
                    "type": "overload",
                    "pattern_id": pattern.summary.pattern_id,
                    "confidence_boost": -0.3,
                    "aggressiveness_reduction": 0.4,
                    "explanation": "User recently shown to be in overload state",
                }
        
        return None
    
    def _check_successful_guidance_pattern(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for successful guidance patterns and return adaptation."""
        successful_patterns = self.storage.find_patterns_by_type(PatternType.SUCCESSFUL_GUIDANCE.value)
        
        for pattern in successful_patterns:
            if self._context_matches_pattern(context, pattern):
                analysis = self.pattern_analyzer.analyze_pattern(pattern.summary.pattern_id)
                acceptance_rate = analysis.get("outcome_distribution", {}).get("acceptance_rate", 0)
                
                return {
                    "type": "successful_guidance",
                    "pattern_id": pattern.summary.pattern_id,
                    "confidence_boost": 0.1 * acceptance_rate,
                    "aggressiveness_reduction": 0,
                    "explanation": f"Previous similar guidance had {acceptance_rate:.0%} acceptance rate",
                }
        
        return None
    
    def _check_ignored_guidance_pattern(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for ignored guidance patterns and return adaptation."""
        ignored_patterns = self.storage.find_patterns_by_type(PatternType.IGNORED_GUIDANCE.value)
        
        for pattern in ignored_patterns:
            if self._context_matches_pattern(context, pattern):
                analysis = self.pattern_analyzer.analyze_pattern(pattern.summary.pattern_id)
                ignore_rate = analysis.get("outcome_distribution", {}).get("ignored", 0) / max(
                    analysis.get("outcome_distribution", {}).get("total", 1), 1
                )
                
                return {
                    "type": "ignored_guidance",
                    "pattern_id": pattern.summary.pattern_id,
                    "confidence_boost": -0.1 * ignore_rate,
                    "aggressiveness_reduction": 0.2 * ignore_rate,
                    "explanation": f"Previous similar guidance was ignored {ignore_rate:.0%} of time",
                }
        
        return None
    
    def _check_routine_pattern(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for routine patterns and return adaptation."""
        routine_patterns = self.storage.find_patterns_by_type(PatternType.ROUTINE.value)
        
        for pattern in routine_patterns:
            if self._context_matches_pattern(context, pattern):
                analysis = self.pattern_analyzer.analyze_pattern(pattern.summary.pattern_id)
                regularity = analysis.get("regularity", {})
                
                if regularity.get("pattern") in ["highly_regular", "moderately_regular"]:
                    return {
                        "type": "routine",
                        "pattern_id": pattern.summary.pattern_id,
                        "confidence_boost": 0.05,
                        "aggressiveness_reduction": 0,
                        "explanation": "Context matches established routine pattern",
                    }
        
        return None
    
    def _context_matches_pattern(self, context: Dict[str, Any], pattern: PatternMemory) -> bool:
        """Check if context matches a pattern's context signature."""
        if not pattern.summary.context_signature:
            return True  # No signature means match any context
        
        # Simple check - could be enhanced with better context matching
        pattern_context = {}
        for obs in pattern.observations:
            pattern_context.update(obs.context)
        
        # Check for key matches
        key_elements = ["task", "domain", "time_of_day", "day_of_week"]
        for key in key_elements:
            if key in context and key in pattern_context:
                if context[key] != pattern_context[key]:
                    return False
        
        return True
    
    def record_successful_guidance(self, context: Dict[str, Any]) -> str:
        """Record a successful guidance event."""
        pattern = self.storage.record_observation(
            pattern_type=PatternType.SUCCESSFUL_GUIDANCE.value,
            context=context,
            outcome="accepted",
            confidence=0.9,
        )
        return pattern.summary.pattern_id
    
    def record_ignored_guidance(self, context: Dict[str, Any]) -> str:
        """Record an ignored guidance event."""
        pattern = self.storage.record_observation(
            pattern_type=PatternType.IGNORED_GUIDANCE.value,
            context=context,
            outcome="ignored",
            confidence=0.5,
        )
        return pattern.summary.pattern_id
    
    def record_overload(self, context: Dict[str, Any]) -> str:
        """Record an overload marker."""
        pattern = self.storage.record_observation(
            pattern_type=PatternType.OVERLOAD_MARKER.value,
            context=context,
            outcome="pending",
            confidence=0.8,
        )
        return pattern.summary.pattern_id
    
    def record_routine_observation(self, context: Dict[str, Any]) -> str:
        """Record a routine pattern observation."""
        pattern = self.storage.record_observation(
            pattern_type=PatternType.ROUTINE.value,
            context=context,
            confidence=0.7,
        )
        return pattern.summary.pattern_id


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_profile(profile_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add longitudinal pattern integration to user profile.
    
    This is purely additive — no migration required.
    """
    if "pattern_memory_enabled" not in profile_dict:
        profile_dict["pattern_memory_enabled"] = True
    if "pattern_adaptation_mode" not in profile_dict:
        profile_dict["pattern_adaptation_mode"] = GuidanceAdaptationMode.ACTIVE.value
    if "max_pattern_memories" not in profile_dict:
        profile_dict["max_pattern_memories"] = 100
    return profile_dict


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add longitudinal pattern insights to adaptive guidance.
    
    This is purely additive — no migration required.
    """
    if "pattern_context" not in guidance_dict:
        guidance_dict["pattern_context"] = None
    if "confidence_boost_from_patterns" not in guidance_dict:
        guidance_dict["confidence_boost_from_patterns"] = 0.0
    if "should_hold_back" not in guidance_dict:
        guidance_dict["should_hold_back"] = False
    return guidance_dict


def integrate_with_narrative(narrative_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add pattern-based explanation to narrative generation.
    
    This is purely additive — no migration required.
    """
    if "pattern_basis" not in narrative_dict:
        narrative_dict["pattern_basis"] = None
    if "confidence_from_patterns" not in narrative_dict:
        narrative_dict["confidence_from_patterns"] = None
    return narrative_dict
