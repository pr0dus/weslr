"""WESLR Capsule Freshness / Acceptance Policy (v93d)

Conservative validation and acceptance policy for restored capsule state.
Silent internal policy only, no user-visible commands.

Rules:
- Fully conservative (no partial-acceptance unless strictly necessary)
- Explicit freshness/invalidity gates
- Simple outcomes: fresh, stale, invalid
- Internal/silent only, no /new semantic changes

v93d: Add CapsuleFreshnessPolicy class with staleness and validity checks
for capsule state restored from persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

# Maximum age of capsule in seconds (24 hours)
MAX_CAPSULE_AGE_SECONDS = 24 * 60 * 60

# Valid phases that can be restored
VALID_RESTORE_PHASES = {"planning", "implementation", "seal"}


@dataclass
class FreshnessResult:
    """Result of capsule freshness validation.
    
    Simple three-state outcome:
    - fresh: capsule is valid and within age threshold
    - stale: capsule exists but is older than MAX_AGE_SECONDS
    - invalid: capsule structure or content is malformed
    
    This is intentionally conservative — no partial-acceptance behavior
    in this slice.
    """
    
    status: str  # "fresh" | "stale" | "invalid"
    reason: str  # operator-readable explanation
    timestamp: str  # ISO-8601 UTC timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def fresh(cls, reason: str = "all_checks_passed") -> "FreshnessResult":
        """Create fresh result."""
        return cls(
            status="fresh",
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    @classmethod
    def stale(cls, age_seconds: int) -> "FreshnessResult":
        """Create stale result."""
        return cls(
            status="stale",
            reason=f"capsule_age: {age_seconds}s > {MAX_CAPSULE_AGE_SECONDS}s",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    @classmethod
    def invalid(cls, reason: str) -> "FreshnessResult":
        """Create invalid result."""
        return cls(
            status="invalid",
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class CapsuleFreshnessPolicy:
    """Validate capsule state before application.
    
    v93d: Capsule Freshness / Acceptance Policy Layer.
    Ensures restored capsules are fresh and valid before application.
    
    Conservative by design:
    - Stale capsules are rejected (age > 24h)
    - Invalid capsules are rejected (missing fields, bad format)
    - No partial-acceptance behavior in this slice
    - Simple binary outcome: pass or fail
    """
    
    @staticmethod
    def validate_freshness(capsule: Dict[str, Any]) -> FreshnessResult:
        """Validate capsule freshness and validity.
        
        Returns FreshnessResult with one of:
        - status="fresh" if capsule passes all checks
        - status="stale" if capsule age exceeds threshold
        - status="invalid" if structure or content is malformed
        
        This is intentionally conservative — no partial-acceptance behavior
        in this slice.
        """
        # Check required fields exist
        if not capsule:
            return FreshnessResult.invalid("empty_context")
        
        required = {"current_layer", "current_phase", "timestamp"}
        missing = required - set(capsule.keys())
        if missing:
            return FreshnessResult.invalid(f"missing_fields: {missing}")
        
        # Check phase is valid
        phase = capsule.get("current_phase")
        if phase not in VALID_RESTORE_PHASES:
            return FreshnessResult.invalid(f"invalid_phase: {phase}")
        
        # Check timestamp age (staleness)
        timestamp = capsule.get("timestamp")
        try:
            capsule_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_seconds = int((now - capsule_time).total_seconds())
            if age_seconds > MAX_CAPSULE_AGE_SECONDS:
                return FreshnessResult.stale(age_seconds)
        except Exception:
            return FreshnessResult.invalid("invalid_timestamp_format")
        
        return FreshnessResult.fresh()
    
    @staticmethod
    def is_stale(capsule: Dict[str, Any]) -> bool:
        """Check if capsule is stale (age > MAX_AGE_SECONDS)."""
        result = CapsuleFreshnessPolicy.validate_freshness(capsule)
        return result.status == "stale"
    
    @staticmethod
    def is_invalid(capsule: Dict[str, Any]) -> bool:
        """Check if capsule is invalid (missing fields, bad format)."""
        result = CapsuleFreshnessPolicy.validate_freshness(capsule)
        return result.status == "invalid"
    
    @staticmethod
    def should_reject_fully(capsule: Dict[str, Any]) -> bool:
        """Check if capsule should be fully rejected (stale or invalid).
        
        Conservative policy: reject if stale OR invalid.
        No partial-acceptance in this slice.
        """
        return CapsuleFreshnessPolicy.is_stale(capsule) or CapsuleFreshnessPolicy.is_invalid(capsule)
    
    @staticmethod
    def get_rejection_reason(capsule: Dict[str, Any]) -> str:
        """Get rejection reason for capsule (stale or invalid)."""
        result = CapsuleFreshnessPolicy.validate_freshness(capsule)
        return result.reason
