"""WESLR Capsule Recovery (v93a)

Deterministic rebuild logic for active work capsule.
Silent reconstruction of minimal working context after /new.

Rules:
- Additive only (no breaking changes)
- Reversible (single file removal)
- Silent/internal only (no user-visible commands)
- Graceful failure (no crash if capsule missing)
- Deterministic rebuild (no confidence logic yet)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .active_work_capsule import ActiveWorkCapsule


# Capsule file path (relative to base_dir)
CAPSULE_FILE = "continuity/active_work_capsule.json"


class CapsuleRebuilder:
    """Rebuild working context from active work capsule."""
    
    @staticmethod
    def rebuild_from_capsule(capsule: ActiveWorkCapsule) -> Dict[str, Any]:
        """Return minimal working context from valid capsule.
        
        Deterministic rebuild: same capsule always produces same context.
        No external calls, no network, no confidence decay logic yet.
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
            "rebuild_timestamp": capsule.timestamp,
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
