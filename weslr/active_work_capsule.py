"""WESLR Active Work Capsule (v93a)

Silent implementation continuity for operator workflow.
Captures current layer/task state for deterministic rebuild after /new.

Rules:
- Additive only (no breaking changes)
- Reversible (single file removal)
- Silent/internal only (no user-visible commands)
- Deterministic rebuild (no confidence decay logic yet)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ActiveWorkCapsule:
    """Minimal implementation continuity state for v93a.
    
    Captures the essential fields needed to rebuild working context
    after /new or provider failure, without user-visible commands.
    """
    
    layer_name: str                     # e.g., "recovery_recommendation_export"
    task_id: str                        # e.g., "v92_planning"
    phase: str                          # "planning" | "implementation" | "seal"
    approved_files: List[str]           # files approved for implementation
    pending_tests: List[str]            # test files pending creation
    seal_criteria: List[str]            # criteria that must pass before seal
    short_task_summary: str             # Brief description (<100 chars)
    active_constraints: List[str]       # constraints active for this task
    timestamp: str                      # ISO-8601 UTC timestamp
    
    def is_valid(self) -> bool:
        """Check if capsule has all required fields."""
        required = [
            "layer_name",
            "task_id",
            "phase",
            "approved_files",
            "pending_tests",
            "seal_criteria",
            "short_task_summary",
            "active_constraints",
            "timestamp",
        ]
        for field_name in required:
            value = getattr(self, field_name, None)
            if value is None:
                return False
            if isinstance(value, list) and len(value) == 0:
                return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert capsule to dictionary for serialization."""
        return {
            "layer_name": self.layer_name,
            "task_id": self.task_id,
            "phase": self.phase,
            "approved_files": self.approved_files,
            "pending_tests": self.pending_tests,
            "seal_criteria": self.seal_criteria,
            "short_task_summary": self.short_task_summary,
            "active_constraints": self.active_constraints,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActiveWorkCapsule":
        """Create capsule from dictionary."""
        return cls(
            layer_name=data["layer_name"],
            task_id=data["task_id"],
            phase=data["phase"],
            approved_files=data["approved_files"],
            pending_tests=data["pending_tests"],
            seal_criteria=data["seal_criteria"],
            short_task_summary=data["short_task_summary"],
            active_constraints=data["active_constraints"],
            timestamp=data["timestamp"],
        )
    
    def to_json(self) -> str:
        """Convert capsule to compact JSON."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
    
    @classmethod
    def from_json(cls, json_str: str) -> "ActiveWorkCapsule":
        """Create capsule from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class CapsuleSerializer:
    """Serialization helper for ActiveWorkCapsule."""
    
    @staticmethod
    def serialize(capsule: ActiveWorkCapsule) -> str:
        """Serialize capsule to JSON string."""
        return capsule.to_json()
    
    @staticmethod
    def deserialize(json_str: str) -> ActiveWorkCapsule:
        """Deserialize JSON string to capsule."""
        return ActiveWorkCapsule.from_json(json_str)


def create_capsule(
    layer_name: str,
    task_id: str,
    phase: str,
    approved_files: List[str],
    pending_tests: List[str],
    seal_criteria: List[str],
    short_task_summary: str,
    active_constraints: List[str],
) -> ActiveWorkCapsule:
    """Factory function to create active work capsule with current timestamp."""
    return ActiveWorkCapsule(
        layer_name=layer_name,
        task_id=task_id,
        phase=phase,
        approved_files=approved_files,
        pending_tests=pending_tests,
        seal_criteria=seal_criteria,
        short_task_summary=short_task_summary,
        active_constraints=active_constraints,
        timestamp=None,  # Will be set by caller
    )


# ===== v93b: Integration Hooks =====


def create_snapshot_capsule(
    layer_name: str,
    task_id: str,
    phase: str,
    approved_files: List[str],
    pending_tests: List[str],
    seal_criteria: List[str],
    short_task_summary: str,
    active_constraints: List[str],
    timestamp: str = None,
) -> ActiveWorkCapsule:
    """Factory function to create snapshot-ready capsule with timestamp.
    
    v93b integration: creates capsule ready for persistence.
    Narrow restore boundary: only operator workflow checkpoints.
    """
    capsule = ActiveWorkCapsule(
        layer_name=layer_name,
        task_id=task_id,
        phase=phase,
        approved_files=approved_files,
        pending_tests=pending_tests,
        seal_criteria=seal_criteria,
        short_task_summary=short_task_summary,
        active_constraints=active_constraints,
        timestamp=timestamp or "2026-04-08T00:00:00Z",
    )
    return capsule


# ===== v93f: Silent Internal Capture Trigger Boundary =====


def capture_if_valid_context(
    layer_name: str,
    task_id: str,
    phase: str,
    short_task_summary: str,
    approved_files: List[str] = None,
    pending_tests: List[str] = None,
    seal_criteria: List[str] = None,
    active_constraints: List[str] = None,
    timestamp: str = None,
) -> Dict[str, Any]:
    """Silent internal capsule capture trigger boundary.
    
    v93f: Silent Capsule Capture Trigger Boundary.
    
    Internal trigger only - no user-visible commands or flags.
    Capture occurs when validated active work context has:
    - Required fields present (layer_name, task_id, phase, short_task_summary)
    - Structurally valid context
    - Capture-worthy phase (implementation or seal)
    
    Minimal capture: only required fields needed, constraints used only if present.
    Silent/internal only - no user-facing output, no framework-style events.
    
    Returns:
        Dict with keys:
        - status: "captured" | "skipped"
        - reason: Human-readable explanation (internal only)
        - capsule: (optional) ActiveWorkCapsule if captured
    """
    # Validation: check minimum required fields are present and valid
    required = {
        "layer_name": layer_name,
        "task_id": task_id,
        "phase": phase,
        "short_task_summary": short_task_summary,
    }
    
    # Check required fields are non-empty strings
    for key, value in required.items():
        if value is None:
            return {
                "status": "skipped",
                "reason": f"missing_required_field: {key}",
            }
        if isinstance(value, str) and not value.strip():
            return {
                "status": "skipped",
                "reason": f"empty_required_field: {key}",
            }
    
    # Check phase is capture-worthy
    if phase not in {"implementation", "seal"}:
        return {
            "status": "skipped",
            "reason": f"phase_not_captureworthy: {phase}",
        }
    
    # Context passes all checks - build the capsule
    capsule = ActiveWorkCapsule(
        layer_name=layer_name,
        task_id=task_id,
        phase=phase,
        approved_files=approved_files or [],
        pending_tests=pending_tests or [],
        seal_criteria=seal_criteria or [],
        short_task_summary=short_task_summary,
        active_constraints=active_constraints or [],
        timestamp=timestamp or "2026-04-08T00:00:00Z",
    )
    
    return {
        "status": "captured",
        "reason": "valid_context_reached",
        "capsule": capsule,
    }
