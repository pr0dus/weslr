"""WESLR Capsule Recovery (v93a + v93b + v93c integration)

Deterministic rebuild logic for active work capsule.
Silent reconstruction of minimal working context after /new.

Rules:
- Additive only (no breaking changes)
- Reversible (single file removal)
- Silent/internal only (no user-visible commands)
- Graceful failure (no crash if capsule missing)
- Deterministic rebuild (no confidence logic yet)
- v93b: Snapshot/restore integration with narrow restore boundary
- v93c: Validation and boundary enforcement for restored capsule state

v93b changes:
- Added CapsulePersister class for snapshot/write operations
- Added restore_boundary parameter for narrow restore definition
- Added snapshot_restore hook for integration with operator workflow

v93c changes:
- Added CapsuleValidator class for restore validation
- Added MAX_CAPSULE_AGE_SECONDS to enforce capsule staleness
- Added VALID_RESTORE_PHASES for phase validation
- Added validate_restored_context() method for application boundary
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .active_work_capsule import ActiveWorkCapsule


# Capsule file path (relative to base_dir)
CAPSULE_FILE = "continuity/active_work_capsule.json"


# Restore boundary (narrow and low-risk)
# Only operator workflow checkpoints, no global startup-wide auto-restore
# Restore boundary: operator workflow checkpoint restoration only
RESTORE_BOUNDARY = {
    "operator_workflow_checkpoint": True,
    "global_startup_restore": False,
    "session_continuation_restore": True,
}


class CapsuleRebuilder:
    """Rebuild working context from active work capsule."""
    
    @staticmethod
    def rebuild_from_capsule(capsule: ActiveWorkCapsule) -> Dict[str, Any]:
        """Return minimal working context from valid capsule.
        
        Deterministic rebuild: same capsule always produces same context.
        No external calls, no network, no confidence decay logic yet.
        
        v93e: Changed 'rebuild_timestamp' to 'timestamp' to align with
        CapsuleFreshnessPolicy validation requirements.
        """
        return {
            "current_layer": capsule.layer_name,
            "current_task_id": capsule.task_id,
            "current_phase": capsule.phase,
            "approved_files": set(capsule.approved_files),
            "pending_tests": set(capsule.pending_tests),
            "seal_criteria": capsule.seal_criteria,
            "short_task_summary": capsule.short_task_summary,
            "active_constraints": capsule.active_constraints,
            "timestamp": capsule.timestamp,
        }
    
    @staticmethod
    def load_capsule_file(base_dir: str) -> Optional[ActiveWorkCapsule]:
        """Load capsule from file if it exists."""
        capsule_path = os.path.join(base_dir, CAPSULE_FILE)
        if not os.path.exists(capsule_path):
            return None
        try:
            with open(capsule_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ActiveWorkCapsule.from_dict(data)
        except Exception:
            return None
    
    @staticmethod
    def rebuild_from_file(base_dir: str) -> Dict[str, Any]:
        """Load capsule from file and rebuild context.
        
        Returns dict with status and optionally reconstructed context.
        Gracefully handles missing file or invalid capsule.
        """
        capsule = CapsuleRebuilder.load_capsule_file(base_dir)
        if capsule is None:
            return {"status": "no_capsule"}
        
        if not capsule.is_valid():
            return {"status": "invalid_capsule"}
        
        context = CapsuleRebuilder.rebuild_from_capsule(capsule)
        return {"status": "success", "context": context}


# Top-level helper functions for continuity.py integration


def load_active_work_capsule(base_dir: str = None) -> Optional[ActiveWorkCapsule]:
    """Load latest active work capsule (silently).
    
    Accepts base_dir parameter. Returns None if file missing or invalid.
    No external calls, no user-visible output.
    """
    try:
        from .adapters.openclaw import OpenClawPaths
    except ImportError:
        OpenClawPaths = None
    
    if base_dir is None:
        if OpenClawPaths is not None:
            paths = OpenClawPaths()
            base_dir = paths.base_dir()
        else:
            return None
    
    return CapsuleRebuilder.load_capsule_file(base_dir)


def restore_from_capsule(base_dir: str = None) -> Dict[str, Any]:
    """Restore working context from capsule (silently, internal only).
    
    Returns dict with status and optionally reconstructed context.
    Gracefully handles missing file or invalid capsule.
    No breaking changes to existing continuity logic.
    """
    try:
        from .adapters.openclaw import OpenClawPaths
    except ImportError:
        OpenClawPaths = None
    
    if base_dir is None:
        if OpenClawPaths is not None:
            paths = OpenClawPaths()
            base_dir = paths.base_dir()
        else:
            return {"status": "no_base_dir"}
    
    return CapsuleRebuilder.rebuild_from_file(base_dir)


# v93c: Silent Capsule Rebuild Application Boundary
# Adds validation and conditional application of restored capsule state
# ===== v93c: Silent Capsule Rebuild Application Boundary =====


# Valid phases that can be restored
VALID_RESTORE_PHASES = {"planning", "implementation", "seal"}

# Maximum age of capsule in seconds (24 hours)
MAX_CAPSULE_AGE_SECONDS = 24 * 60 * 60


class CapsuleValidator:
    """Validate capsule state before application.
    
    v93c: Silent Capsule Rebuild Application Boundary.
    Ensures restored capsules are valid, not stale, and within restore boundary.
    """
    
    @staticmethod
    def validate_restored_context(context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate restored context before application.
        
        Returns validation result dict with:
        - status: "valid" | "invalid" | "stale" | "outside_boundary"
        - reason: explanation for validation result
        """
        if not context:
            return {"status": "invalid", "reason": "empty_context"}
        
        # Check required fields
        required = {"current_layer", "current_phase", "timestamp"}
        missing = required - set(context.keys())
        if missing:
            return {"status": "invalid", "reason": f"missing_fields: {missing}"}
        
        # Check phase is valid
        phase = context.get("current_phase")
        if phase not in VALID_RESTORE_PHASES:
            return {"status": "invalid", "reason": f"invalid_phase: {phase}"}
        
        # Check timestamp age (staleness)
        timestamp = context.get("timestamp")
        try:
            from datetime import datetime
            capsule_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            now = datetime.now(capsule_time.tzinfo or capsule_time.utcoffset)
            age_seconds = (now - capsule_time).total_seconds()
            if age_seconds > MAX_CAPSULE_AGE_SECONDS:
                return {"status": "stale", "reason": f"capsule_age: {int(age_seconds)}s > {MAX_CAPSULE_AGE_SECONDS}s"}
        except Exception:
            return {"status": "invalid", "reason": "invalid_timestamp_format"}
        
        # Check restore boundary
        if not RESTORE_BOUNDARY.get("operator_workflow_checkpoint", False):
            return {"status": "outside_boundary", "reason": "restore_boundary_disabled"}
        
        return {"status": "valid", "reason": "all_checks_passed"}


class CapsulePersister:
    """Snapshot/write and read/restore hooks for v93b integration.
    
    Adds narrow restore boundary support while preserving v93a behavior.
    """
    
    @staticmethod
    def write_snapshot(capsule: ActiveWorkCapsule, base_dir: str) -> Dict[str, Any]:
        """Write active work capsule to continuity storage (snapshot).
        
        Narrow restore boundary: only operator workflow checkpoints.
        No global startup-wide auto-restore.
        """
        if not RESTORE_BOUNDARY["operator_workflow_checkpoint"]:
            return {"status": "not_in_restore_boundary"}
        
        capsule_path = os.path.join(base_dir, CAPSULE_FILE)
        continuity_dir = os.path.dirname(capsule_path)
        os.makedirs(continuity_dir, exist_ok=True)
        
        try:
            with open(capsule_path, "w", encoding="utf-8") as f:
                json.dump(capsule.to_dict(), f, indent=2, sort_keys=True)
            return {"status": "success", "path": capsule_path}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def read_restore_point(base_dir: str) -> Dict[str, Any]:
        """Read latest active work capsule from continuity storage.
        
        Narrow restore boundary: only operator workflow checkpoints.
        Returns status dict without triggering restore.
        """
        if not RESTORE_BOUNDARY["operator_workflow_checkpoint"]:
            return {"status": "not_in_restore_boundary"}
        
        result = CapsuleRebuilder.rebuild_from_file(base_dir)
        return result
    
    @staticmethod
    def snapshot_restore(base_dir: str = None) -> Dict[str, Any]:
        """Perform snapshot restore from continuity storage (silently).
        
        Returns dict with status and optionally reconstructed context.
        Narrow restore boundary applied - no global startup-wide restore.
        """
        if not RESTORE_BOUNDARY["operator_workflow_checkpoint"]:
            return {"status": "not_in_restore_boundary"}
        
        if base_dir is None:
            try:
                from .adapters.openclaw import OpenClawPaths
            except ImportError:
                OpenClawPaths = None
            
            if OpenClawPaths is not None:
                paths = OpenClawPaths()
                base_dir = paths.base_dir()
            else:
                return {"status": "no_base_dir"}
        
        return CapsuleRebuilder.rebuild_from_file(base_dir)
