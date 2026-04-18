"""WESLR Capsule Observability (v93h)

Silent Continuity Observability / Debug Summary for operator workflow.
Read-only observability layer for silent continuity subsystem.

Rules:
- Additive only (no breaking changes)
- Reversible (single file removal)
- Silent/internal only (no user-visible commands)
- Read-only observability (no mutation of continuity state)
- No capture/restore triggers
- No control surface behavior
- Correlation identifiers only if already present in observed state

v93h: Silent Continuity Observability / Debug Summary.
Provides read-only operator-facing observability for silent continuity state.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

from .active_work_capsule import ActiveWorkCapsule
from .capsule_policy import CapsuleFreshnessPolicy
from .capsule_recovery import CapsuleRebuilder


@dataclass
class CapsuleObservabilityResult:
    """Result of capsule observability observation."""
    
    status: str  # "observed" | "absent" | "error"
    capsule_present: bool
    capture_timestamp: Optional[str]
    last_restore_decision: Optional[str]  # "applied" | "ignored" | "stale" | "invalid"
    freshness_status: Optional[str]  # "fresh" | "stale" | "invalid"
    last_apply_status: Optional[str]  # "applied" | "ignored" | "stale" | "invalid"
    raw_capsule: Optional[Dict[str, Any]]
    reason: str
    timestamp: str  # ISO-8601 UTC timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status,
            "capsule_present": self.capsule_present,
            "capture_timestamp": self.capture_timestamp,
            "last_restore_decision": self.last_restore_decision,
            "freshness_status": self.freshness_status,
            "last_apply_status": self.last_apply_status,
            "raw_capsule": self.raw_capsule,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def observed(cls, capsule_present: bool, reason: str, raw_capsule: Dict[str, Any] = None) -> "CapsuleObservabilityResult":
        """Create observed result."""
        return cls(
            status="observed",
            capsule_present=capsule_present,
            capture_timestamp=None,
            last_restore_decision=None,
            freshness_status=None,
            last_apply_status=None,
            raw_capsule=raw_capsule,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    @classmethod
    def absent(cls, reason: str) -> "CapsuleObservabilityResult":
        """Create absent result."""
        return cls(
            status="absent",
            capsule_present=False,
            capture_timestamp=None,
            last_restore_decision=None,
            freshness_status=None,
            last_apply_status=None,
            raw_capsule=None,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    @classmethod
    def error(cls, reason: str) -> "CapsuleObservabilityResult":
        """Create error result."""
        return cls(
            status="error",
            capsule_present=False,
            capture_timestamp=None,
            last_restore_decision=None,
            freshness_status=None,
            last_apply_status=None,
            raw_capsule=None,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class CapsuleObservability:
    """Read-only observability layer for silent continuity subsystem.
    
    v93h: Silent Continuity Observability / Debug Summary.
    Provides read-only operator-facing observability for silent continuity state.
    
    Constraints:
    - No capture/restore triggers
    - No mutation of continuity state
    - No control surface behavior
    - Internal only, no user-visible commands
    - Correlation identifiers only if already present
    """
    
    def __init__(self, base_dir: str = None):
        """Initialize observability with optional base directory."""
        self.base_dir = base_dir
        self.continuity_dir = None
        self.capsule_path = None
        if base_dir:
            self.continuity_dir = os.path.join(base_dir, "continuity")
            self.capsule_path = os.path.join(self.continuity_dir, "active_work_capsule.json")
    
    def _store_capsule_for_test(self, capsule: ActiveWorkCapsule) -> Dict[str, Any]:
        """Internal helper to store capsule for testing.
        
        This method is only for test use and should not be exposed publicly.
        """
        if self.base_dir is None:
            return {"status": "error", "reason": "no_base_dir"}
        
        if self.continuity_dir is None:
            self.continuity_dir = os.path.join(self.base_dir, "continuity")
        os.makedirs(self.continuity_dir, exist_ok=True)
        
        if self.capsule_path is None:
            self.capsule_path = os.path.join(self.continuity_dir, "active_work_capsule.json")
        
        try:
            capsule_data = capsule.to_dict()
            with open(self.capsule_path, "w", encoding="utf-8") as f:
                json.dump(capsule_data, f, indent=2)
            return {"status": "stored", "path": self.capsule_path}
        except Exception as e:
            return {"status": "error", "reason": f"write_error: {str(e)}"}
    
    # ===== v93h: Read-Only Observability =====
    
    def observe(self) -> Dict[str, Any]:
        """Observe current capsule state.
        
        Returns observability result dict with status and details.
        Silent/internal only, no user-visible output.
        """
        # Check if capsule_path is available
        if self.capsule_path is None:
            return CapsuleObservabilityResult.absent("no_capsule_path_set").to_dict()
        
        # Initialize continuity dir if not already done (when base_dir is set)
        if self.base_dir:
            if self.continuity_dir is None:
                self.continuity_dir = os.path.join(self.base_dir, "continuity")
        
        # Step 1: Check if capsule file exists
        if not os.path.exists(self.capsule_path):
            return CapsuleObservabilityResult.absent("capsule_file_not_found").to_dict()
        
        # Step 2: Load capsule
        try:
            with open(self.capsule_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return CapsuleObservabilityResult.error(f"read_error: {str(e)}").to_dict()
        
        # Step 3: Rebuild capsule object
        try:
            capsule = ActiveWorkCapsule.from_dict(data)
        except Exception as e:
            return CapsuleObservabilityResult.error(f"parse_error: {str(e)}").to_dict()
        
        # Step 4: Get capture timestamp (from capsule)
        capture_timestamp = capsule.timestamp if capsule else None
        
        # Step 5: Validate capsule (freshness check)
        context = CapsuleRebuilder.rebuild_from_capsule(capsule)
        freshness = CapsuleFreshnessPolicy.validate_freshness(context)
        
        # Step 6: Record last restore decision
        if freshness.status == "fresh":
            last_restore_decision = "applied"
        elif freshness.status == "stale":
            last_restore_decision = "stale"
        else:  # invalid
            last_restore_decision = "invalid"
        
        # Step 7: Record freshness status
        freshness_status = freshness.status
        
        # Step 8: Record last apply status (same as last restore decision for v93h)
        last_apply_status = last_restore_decision
        
        # Build result with all fields
        result_obj = CapsuleObservabilityResult.observed(
            capsule_present=True,
            reason="capsule_observed",
            raw_capsule=data,
        )
        
        # Add additional fields to result
        result_obj.capture_timestamp = capture_timestamp
        result_obj.last_restore_decision = last_restore_decision
        result_obj.freshness_status = freshness_status
        result_obj.last_apply_status = last_apply_status
        
        return result_obj.to_dict()
    
    # ===== Debug Summary Export =====
    
    def export_debug_summary(self) -> Dict[str, Any]:
        """Export operator-readable + machine-readable debug summary.
        
        Includes all observability results for operator review.
        """
        observation = self.observe()
        
        return {
            "debug_summary": {
                "status": observation.get("status", "error"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "details": {
                "capsule_present": observation.get("capsule_present", False),
                "capture_timestamp": observation.get("capture_timestamp"),
                "last_restore_decision": observation.get("last_restore_decision"),
                "freshness_status": observation.get("freshness_status"),
                "last_apply_status": observation.get("last_apply_status"),
                "reason": observation.get("reason"),
            },
        }
    
    # ===== Operator-Facing Debug Queries =====
    
    def get_capsule_status(self) -> Dict[str, Any]:
        """Check whether a capsule is present or absent."""
        observation = self.observe()
        return {
            "status": "present" if observation.get("capsule_present") else "absent",
            "reason": observation.get("reason"),
        }
    
    def get_capture_timestamp(self) -> Dict[str, Any]:
        """Get last capture timestamp if capsule present."""
        observation = self.observe()
        if not observation.get("capsule_present"):
            return {
                "status": "absent",
                "reason": "no_capsule_present",
            }
        return {
            "status": "captured",
            "timestamp": observation.get("capture_timestamp"),
        }
    
    def get_last_restore_decision(self) -> Dict[str, Any]:
        """Get last restore decision (applied/ignored/stale/invalid)."""
        observation = self.observe()
        if not observation.get("capsule_present"):
            return {
                "status": "absent",
                "reason": "no_capsule_present",
            }
        return {
            "status": observation.get("last_restore_decision", "unknown"),
            "reason": observation.get("reason"),
        }
    
    def get_freshness_status(self) -> Dict[str, Any]:
        """Get freshness / acceptance status."""
        observation = self.observe()
        if not observation.get("capsule_present"):
            return {
                "status": "absent",
                "reason": "no_capsule_present",
            }
        return {
            "status": observation.get("freshness_status", "unknown"),
            "reason": observation.get("reason"),
        }
    
    def get_last_apply_status(self) -> Dict[str, Any]:
        """Get whether a capsule was applied, ignored, stale, or invalid."""
        observation = self.observe()
        if not observation.get("capsule_present"):
            return {
                "status": "absent",
                "reason": "no_capsule_present",
            }
        return {
            "status": observation.get("last_apply_status", "unknown"),
            "reason": observation.get("reason"),
        }


# ===== Export Functions for Operator Workflow =====

def export_debug_summary(base_dir: str = None) -> Dict[str, Any]:
    """Export operator-readable debug summary for silent continuity.
    
    v93h: Read-only debug summary for operator review.
    """
    observability = CapsuleObservability(base_dir=base_dir)
    return observability.export_debug_summary()


def get_capsule_status(base_dir: str = None) -> Dict[str, Any]:
    """Check whether a capsule is present or absent.
    
    v93h: Read-only capsule presence check.
    """
    observability = CapsuleObservability(base_dir=base_dir)
    return observability.get_capsule_status()


def get_capture_timestamp(base_dir: str = None) -> Dict[str, Any]:
    """Get last capture timestamp if capsule present.
    
    v93h: Read-only timestamp query.
    """
    observability = CapsuleObservability(base_dir=base_dir)
    return observability.get_capture_timestamp()


def get_last_restore_decision(base_dir: str = None) -> Dict[str, Any]:
    """Get last restore decision (applied/ignored/stale/invalid).
    
    v93h: Read-only decision query.
    """
    observability = CapsuleObservability(base_dir=base_dir)
    return observability.get_last_restore_decision()


def get_freshness_status(base_dir: str = None) -> Dict[str, Any]:
    """Get freshness / acceptance status.
    
    v93h: Read-only freshness query.
    """
    observability = CapsuleObservability(base_dir=base_dir)
    return observability.get_freshness_status()


def get_last_apply_status(base_dir: str = None) -> Dict[str, Any]:
    """Get whether a capsule was applied, ignored, stale, or invalid.
    
    v93h: Read-only apply status query.
    """
    observability = CapsuleObservability(base_dir=base_dir)
    return observability.get_last_apply_status()
