# intervention_timing.py - v36: Intervention Timing / Surfacing Policy Layer
# Creates a governed timing layer so WESLR can decide not only what to recommend,
# but when to surface it, when to hold back, when to retry, and when to stop.
# Additive only, transparent, reversible, suggestion-based, non-manipulative, no repo drift.
# Local to WESLR scope.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class TimingStatus(str, Enum):
    """Status of timing evaluation."""
    READY = "ready"  # Ready to surface now
    DELAYED = "delayed"  # Should be delayed
    COOLDOWN = "cooldown"  # In cooldown period
    SILENT = "silent"  # In silent/sensitive window
    STOPPED = "stopped"  # Should not surface


class TimingStrategy(str, Enum):
    """Timing strategy for intervention."""
    IMMEDIATE = "immediate"  # Surface immediately
    DELAYED = "delayed"  # Delay by configured amount
    COOLDOWN = "cooldown"  # Wait for cooldown period
    SILENT = "silent"  # Don't surface, log for later
    STOP = "stop"  # Don't surface, stop trying


class RetryStrategy(str, Enum):
    """Retry strategy after rejection."""
    SOFTEN = "soften"  # Soften and retry
    ESCALATE = "escalate"  # Escalate urgency
    WITHDRAW = "withdraw"  # Withdraw for now
    COOLDOWN = "cooldown"  # Wait in cooldown


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class TimingEvaluation:
    """Evaluation of timing for an intervention."""
    
    evaluation_id: str  # Unique identifier
    intervention_id: str  # ID of intervention this evaluates
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    # Timing factors
    suitability: float = 0.5  # How suitable is current timing (0.0-1.0)
    interruption_cost: float = 0.0  # Cost of interrupting user
    urgency: float = 0.5  # Urgency of intervention
    readiness: float = 0.5  # User readiness for intervention
    
    # Status
    status: str = TimingStatus.READY.value
    strategy: str = TimingStrategy.IMMEDIATE.value
    
    # Delay information
    delay_seconds: int = 0  # Delay in seconds
    delay_until: Optional[str] = None  # ISO-8601 timestamp
    
    # Retry info
    retry_count: int = 0  # Number of retry attempts
    retry_delay_seconds: int = 60  # Delay between retries (default 60s)
    retry_strategy: str = RetryStrategy.SOFTEN.value
    
    # Cooldown info
    cooldown_until: Optional[str] = None  # ISO-8601 timestamp
    cooldown_reason: Optional[str] = None  # Reason for cooldown
    
    # Silence info
    in_silent_window: bool = False  # In quiet/sensitive window
    sensitive_window_end: Optional[str] = None  # When sensitive window ends
    
    # Confidence
    confidence: float = 0.5  # Confidence in timing evaluation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "evaluation_id": self.evaluation_id,
            "intervention_id": self.intervention_id,
            "timestamp": self.timestamp,
            "suitability": self.suitability,
            "interruption_cost": self.interruption_cost,
            "urgency": self.urgency,
            "readiness": self.readiness,
            "status": self.status,
            "strategy": self.strategy,
            "delay_seconds": self.delay_seconds,
            "delay_until": self.delay_until,
            "retry_count": self.retry_count,
            "retry_delay_seconds": self.retry_delay_seconds,
            "retry_strategy": self.retry_strategy,
            "cooldown_until": self.cooldown_until,
            "cooldown_reason": self.cooldown_reason,
            "in_silent_window": self.in_silent_window,
            "sensitive_window_end": self.sensitive_window_end,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TimingEvaluation:
        """Create from dictionary representation."""
        return cls(**data)
    
    def should_surface(self) -> bool:
        """Check if intervention should be surfaced."""
        return self.status == TimingStatus.READY.value and not self.in_silent_window
    
    def is_in_cooldown(self) -> bool:
        """Check if in cooldown period."""
        if not self.cooldown_until:
            return False
        
        try:
            cooldown_end = datetime.fromisoformat(self.cooldown_until.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return now < cooldown_end
        except Exception:
            return False
    
    def is_delayed(self) -> bool:
        """Check if delayed."""
        return self.delay_seconds > 0
    
    def apply_cooldown(self, seconds: int, reason: str) -> None:
        """Apply cooldown period."""
        self.cooldown_until = (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")
        self.cooldown_reason = reason
        self.status = TimingStatus.COOLDOWN.value


@dataclass
class TimingPolicy:
    """Policy for timing interventions."""
    
    policy_id: str  # Unique identifier
    name: Optional[str] = None  # Display name
    
    # Default settings
    default_suitability_threshold: float = 0.5
    default_delay_seconds: int = 0
    default_retry_delay_seconds: int = 60
    default_cooldown_seconds: int = 300  # 5 minutes
    default_silence_hours: List[int] = field(default_factory=lambda: [22, 23, 0, 1, 2, 3, 4, 5])  # 10 PM - 5 AM
    
    # Retry settings
    max_retry_count: int = 3
    retry_escalation_seconds: int = 300  # Escalate delay after each retry
    
    # Cooldown settings
    cooldown_after_rejection_seconds: int = 600  # 10 minutes
    
    # Silence settings
    enable_silence_windows: bool = True
    quiet_hours: List[int] = field(default_factory=lambda: [22, 23, 0, 1, 2, 3, 4, 5])
    
    # Configuration
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "default_suitability_threshold": self.default_suitability_threshold,
            "default_delay_seconds": self.default_delay_seconds,
            "default_retry_delay_seconds": self.default_retry_delay_seconds,
            "default_cooldown_seconds": self.default_cooldown_seconds,
            "default_silence_hours": self.default_silence_hours,
            "max_retry_count": self.max_retry_count,
            "retry_escalation_seconds": self.retry_escalation_seconds,
            "cooldown_after_rejection_seconds": self.cooldown_after_rejection_seconds,
            "enable_silence_windows": self.enable_silence_windows,
            "quiet_hours": self.quiet_hours,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TimingPolicy:
        """Create from dictionary representation."""
        return cls(**data)
    
    def is_in_silent_window(self, hour: int) -> bool:
        """Check if given hour is in silent window."""
        return hour in self.quiet_hours if self.enable_silence_windows else False


@dataclass
class TimingRecord:
    """Record of timing decisions for an intervention."""
    
    record_id: str  # Unique identifier
    intervention_id: str
    
    # Decision history
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    last_decision: Optional[Dict[str, Any]] = None
    
    # Retry history
    retries: List[Dict[str, Any]] = field(default_factory=list)
    retry_count: int = 0
    
    # Cooldown history
    cooldowns: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "record_id": self.record_id,
            "intervention_id": self.intervention_id,
            "decisions": self.decisions,
            "last_decision": self.last_decision,
            "retries": self.retries,
            "retry_count": self.retry_count,
            "cooldowns": self.cooldowns,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TimingRecord:
        """Create from dictionary representation."""
        data["decisions"] = data.get("decisions", [])
        data["retries"] = data.get("retries", [])
        data["cooldowns"] = data.get("cooldowns", [])
        return cls(**data)
    
    def record_decision(self, decision: Dict[str, Any]) -> None:
        """Record a decision."""
        self.decisions.append(decision)
        self.last_decision = decision
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def record_retry(self, retry_data: Dict[str, Any]) -> None:
        """Record a retry attempt."""
        self.retries.append(retry_data)
        self.retry_count += 1
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def record_cooldown(self, cooldown_data: Dict[str, Any]) -> None:
        """Record a cooldown."""
        self.cooldowns.append(cooldown_data)
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ============================================================================
# TIMING POLICY MANAGER
# ============================================================================


class TimingPolicyManager:
    """Manager for timing policies and evaluations.
    
    Provides transparent, reversible timing management.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize timing policy manager."""
        self.storage_path = storage_path or self._get_default_path()
        self.policies: Dict[str, TimingPolicy] = {}  # policy_id -> Policy
        self.records: Dict[str, TimingRecord] = {}  # record_id -> Record
        self._ensure_storage_exists()
        self._load_policies()
        self._load_records()
    
    def _get_default_path(self) -> str:
        """Get default storage path."""
        return "/data/data/com.termux/files/home/.openclaw/workspace/weslr/intervention_timing/"
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_policies(self) -> None:
        """Load policies from storage."""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith("_policy.json"):
                policy_id = filename[:-12]  # Remove _policy.json
                try:
                    with open(os.path.join(self.storage_path, filename), "r") as f:
                        data = json.load(f)
                        self.policies[policy_id] = TimingPolicy.from_dict(data)
                except Exception:
                    continue
    
    def _load_records(self) -> None:
        """Load records from storage."""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith("_record.json"):
                record_id = filename[:-12]  # Remove _record.json
                try:
                    with open(os.path.join(self.storage_path, filename), "r") as f:
                        data = json.load(f)
                        self.records[record_id] = TimingRecord.from_dict(data)
                except Exception:
                    continue
    
    def _save_policy(self, policy_id: str) -> None:
        """Save a policy to storage."""
        import os
        filepath = os.path.join(self.storage_path, f"{policy_id}_policy.json")
        data = self.policies[policy_id].to_dict()
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def _save_record(self, record_id: str) -> None:
        """Save a record to storage."""
        import os
        filepath = os.path.join(self.storage_path, f"{record_id}_record.json")
        data = self.records[record_id].to_dict()
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def create_policy(
        self,
        policy_id: str,
        name: Optional[str] = None,
    ) -> TimingPolicy:
        """Create a new timing policy."""
        policy = TimingPolicy(policy_id=policy_id, name=name)
        self.policies[policy_id] = policy
        self._save_policy(policy_id)
        return policy
    
    def get_policy(self, policy_id: str) -> Optional[TimingPolicy]:
        """Get a timing policy by ID."""
        return self.policies.get(policy_id)
    
    def get_default_policy(self) -> TimingPolicy:
        """Get the default timing policy (create if needed)."""
        if "default" not in self.policies:
            return self.create_policy("default", "Default Timing Policy")
        return self.policies["default"]
    
    def evaluate_timing(
        self,
        policy_id: str,
        intervention_id: str,
        suitability: float = 0.5,
        interruption_cost: float = 0.0,
        urgency: float = 0.5,
        readiness: float = 0.5,
        retry_count: int = 0,
        in_silent_window: bool = False,
        cooldown_until: Optional[str] = None,
    ) -> TimingEvaluation:
        """Evaluate timing for an intervention."""
        policy = self.get_policy(policy_id) or self.get_default_policy()
        
        # Generate evaluation ID
        intervention_num = intervention_id.split('-')[-1] if '-' in intervention_id else len(self.records) + 1
        if isinstance(intervention_num, str) and intervention_num.isdigit():
            intervention_num = int(intervention_num)
        else:
            intervention_num = len(self.records) + 1
        evaluation_id = f"eval-{intervention_num:04d}"
        
        # Determine strategy based on factors
        suitability_threshold = policy.default_suitability_threshold
        strategy = TimingStrategy.IMMEDIATE.value
        delay_seconds = 0
        status = TimingStatus.READY.value
        
        # Check if in cooldown
        if cooldown_until:
            try:
                cooldown_end = datetime.fromisoformat(cooldown_until.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                if now < cooldown_end:
                    status = TimingStatus.COOLDOWN.value
                    strategy = TimingStrategy.COOLDOWN.value
            except Exception:
                pass
        
        # Check if in silent window
        if in_silent_window and policy.enable_silence_windows:
            status = TimingStatus.SILENT.value
            strategy = TimingStrategy.SILENT.value
        
        # Check suitability
        if suitability < suitability_threshold:
            delay_seconds = policy.default_delay_seconds or 60
            strategy = TimingStrategy.DELAYED.value
            if delay_seconds > 0:
                status = TimingStatus.DELAYED.value
        
        # Check retry count
        if retry_count >= policy.max_retry_count:
            status = TimingStatus.STOPPED.value
            strategy = TimingStrategy.STOP.value
        
        # Calculate delay until
        delay_until = None
        if delay_seconds > 0:
            delay_until = (datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)).isoformat().replace("+00:00", "Z")
        
        evaluation = TimingEvaluation(
            evaluation_id=evaluation_id,
            intervention_id=intervention_id,
            suitability=suitability,
            interruption_cost=interruption_cost,
            urgency=urgency,
            readiness=readiness,
            status=status,
            strategy=strategy,
            delay_seconds=delay_seconds,
            delay_until=delay_until,
            retry_count=retry_count,
            retry_delay_seconds=policy.default_retry_delay_seconds,
            retry_strategy=RetryStrategy.SOFTEN.value,
            cooldown_until=cooldown_until,
            in_silent_window=in_silent_window,
            confidence=suitability,
        )
        
        return evaluation
    
    def create_timing_record(self, intervention_id: str) -> TimingRecord:
        """Create a timing record for an intervention."""
        intervention_num = intervention_id.split('-')[-1] if '-' in intervention_id else len(self.records) + 1
        if isinstance(intervention_num, str) and intervention_num.isdigit():
            intervention_num = int(intervention_num)
        else:
            intervention_num = len(self.records) + 1
        record_id = f"record-{intervention_num:04d}"
        
        record = TimingRecord(record_id=record_id, intervention_id=intervention_id)
        self.records[record_id] = record
        self._save_record(record_id)
        return record
    
    def get_record(self, record_id: str) -> Optional[TimingRecord]:
        """Get a timing record by ID."""
        return self.records.get(record_id)
    
    def record_decision(self, record_id: str, decision: Dict[str, Any]) -> bool:
        """Record a decision."""
        record = self.get_record(record_id)
        if not record:
            return False
        
        record.record_decision(decision)
        self._save_record(record_id)
        return True
    
    def record_retry(self, record_id: str, retry_data: Dict[str, Any]) -> bool:
        """Record a retry attempt."""
        record = self.get_record(record_id)
        if not record:
            return False
        
        record.record_retry(retry_data)
        self._save_record(record_id)
        return True
    
    def record_cooldown(self, record_id: str, cooldown_data: Dict[str, Any]) -> bool:
        """Record a cooldown."""
        record = self.get_record(record_id)
        if not record:
            return False
        
        record.record_cooldown(cooldown_data)
        self._save_record(record_id)
        return True
    
    def get_all_policies(self) -> Dict[str, TimingPolicy]:
        """Get all timing policies."""
        return self.policies
    
    def get_all_records(self) -> Dict[str, TimingRecord]:
        """Get all timing records."""
        return self.records
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary."""
        return {
            "policy_count": len(self.policies),
            "record_count": len(self.records),
            "policies": {k: v.to_dict() for k, v in self.policies.items()},
            "records": {k: v.to_dict() for k, v in self.records.items()},
        }


# ============================================================================
# TIMING ENGINE
# ============================================================================


class TimingEngine:
    """Engine for managing timing decisions.
    
    Uses policies and records to make timing decisions.
    """
    
    def __init__(self, manager: TimingPolicyManager):
        """Initialize timing engine."""
        self.manager = manager
    
    def should_intervene(
        self,
        intervention_id: str,
        policy_id: Optional[str] = None,
        suitability: float = 0.5,
        interruption_cost: float = 0.0,
        urgency: float = 0.5,
        readiness: float = 0.5,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Determine if intervention should occur."""
        policy = self.manager.get_policy(policy_id) or self.manager.get_default_policy()
        
        # Check if policy enabled
        if not policy.enabled:
            return {
                "should_intervene": False,
                "reason": "Policy disabled",
                "status": TimingStatus.STOPPED.value,
            }
        
        # Check silence windows
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        if policy.enable_silence_windows and hour in policy.quiet_hours:
            return {
                "should_intervene": False,
                "reason": "In silent window",
                "status": TimingStatus.SILENT.value,
                "next_opportunity": self._get_next_opportunity(hour, policy.quiet_hours),
            }
        
        # Check retry count
        if retry_count >= policy.max_retry_count:
            return {
                "should_intervene": False,
                "reason": "Max retries reached",
                "status": TimingStatus.STOPPED.value,
            }
        
        # Evaluate timing
        evaluation = self.manager.evaluate_timing(
            policy_id or "default",
            intervention_id,
            suitability,
            interruption_cost,
            urgency,
            readiness,
            retry_count,
            in_silent_window=False,  # Checked above
        )
        
        return {
            "should_intervene": evaluation.should_surface(),
            "status": evaluation.status,
            "strategy": evaluation.strategy,
            "delay_seconds": evaluation.delay_seconds,
            "delay_until": evaluation.delay_until,
            "confidence": evaluation.confidence,
            "interruption_cost": evaluation.interruption_cost,
        }
    
    def _get_next_opportunity(self, current_hour: int, quiet_hours: List[int]) -> Optional[str]:
        """Get next opportunity after current quiet hours."""
        # Find next hour outside quiet hours
        for offset in range(1, 24):
            next_hour = (current_hour + offset) % 24
            if next_hour not in quiet_hours:
                now = datetime.now(timezone.utc)
                next_opportunity = now + timedelta(hours=offset)
                return next_opportunity.isoformat().replace("+00:00", "Z")
        return None
    
    def get_retry_delay(self, retry_count: int, base_delay: int = 60) -> int:
        """Get retry delay based on retry count."""
        if retry_count == 0:
            return base_delay
        
        # Escalate delay after each retry
        return base_delay * (2 ** retry_count)


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timing context to adaptive guidance.
    
    This is purely additive — no migration required.
    """
    if "timing_evaluation" not in guidance_dict:
        guidance_dict["timing_evaluation"] = None
    if "delay_seconds" not in guidance_dict:
        guidance_dict["delay_seconds"] = 0
    if "in_silent_window" not in guidance_dict:
        guidance_dict["in_silent_window"] = False
    if "should_intervene" not in guidance_dict:
        guidance_dict["should_intervene"] = True
    return guidance_dict


def integrate_with_longitudinal_patterns(patterns_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timing context to longitudinal patterns.
    
    This is purely additive — no migration required.
    """
    if "timing_context" not in patterns_dict:
        patterns_dict["timing_context"] = None
    if "retry_count" not in patterns_dict:
        patterns_dict["retry_count"] = 0
    if "last_retry_delay" not in patterns_dict:
        patterns_dict["last_retry_delay"] = 0
    return patterns_dict


def integrate_with_household_context(household_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timing context to household context.
    
    This is purely additive — no migration required.
    """
    if "timing_policy" not in household_dict:
        household_dict["timing_policy"] = None
    if "quiet_hours" not in household_dict:
        household_dict["quiet_hours"] = [22, 23, 0, 1, 2, 3, 4, 5]
    if "interruption_cost" not in household_dict:
        household_dict["interruption_cost"] = 0.0
    return household_dict


def integrate_with_compromise_explanation(explanation_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timing context to compromise explanation.
    
    This is purely additive — no migration required.
    """
    if "timing_rationale" not in explanation_dict:
        explanation_dict["timing_rationale"] = None
    if "delay_explanation" not in explanation_dict:
        explanation_dict["delay_explanation"] = None
    if "silent_window_explanation" not in explanation_dict:
        explanation_dict["silent_window_explanation"] = None
    return explanation_dict
