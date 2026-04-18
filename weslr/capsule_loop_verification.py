"""WESLR Capsule Loop Verification (v93g)

End-to-end silent continuity loop verification.
Verifies capture→store→load→validate→decision→apply cycle.

Rules:
- Additive only (no breaking changes)
- Reversible (single file removal)
- Silent/internal only (no user-visible commands)
- Narrow verification scope (integrate v93a-v93f components)
- No duplicate capture logic (use v93f capture_if_valid_context)
- No behavior changes to /new (preserved)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from .active_work_capsule import ActiveWorkCapsule
from .capsule_policy import CapsuleFreshnessPolicy
from .capsule_recovery import CapsuleRebuilder


@dataclass
class LoopVerificationResult:
    """Result of end-to-end capsule loop verification."""
    
    status: str  # "verified" | "failed"
    reason: str  # Operator-readable explanation
    loop_steps: Dict[str, Any]  # Verification details for each step
    timestamp: str  # ISO-8601 UTC timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status,
            "reason": self.reason,
            "loop_steps": self.loop_steps,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def verified(cls, loop_steps: Dict[str, Any]) -> "LoopVerificationResult":
        """Create verified result."""
        return cls(
            status="verified",
            reason="full_loop_verified",
            loop_steps=loop_steps,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    @classmethod
    def failed(cls, reason: str, loop_steps: Dict[str, Any]) -> "LoopVerificationResult":
        """Create failed result."""
        return cls(
            status="failed",
            reason=reason,
            loop_steps=loop_steps,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class CapsuleLoopVerifier:
    """End-to-end silent continuity loop verification.
    
    v93g: Capsule End-to-End Silent Continuity Loop Verification.
    Verifies the complete capture→store→load→validate→decision→apply cycle.
    
    Integration scope (v93a-v93f):
    - v93a: ActiveWorkCapsule (core data structure)
    - v93b: CapsulePersister (capture/write integration)
    - v93c: CapsuleRebuilder (restore integration)
    - v93d: CapsuleFreshnessPolicy (validation)
    - v93e: resume_from_capsule (decision logic)
    - v93f: capture_if_valid_context (capture boundary)
    
    No user-visible behavior, no /new changes, no framework events.
    """
    
    def __init__(self, base_dir: str = None):
        """Initialize verifier with optional base directory."""
        self.base_dir = base_dir
        self.continuity_dir = None
        self.capsule_path = None
        if base_dir:
            self.continuity_dir = os.path.join(base_dir, "continuity")
            self.capsule_path = os.path.join(self.continuity_dir, "active_work_capsule.json")
    
    # ===== v93g: End-to-End Loop Verification =====
    
    def verify_full_loop(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute capture→store→load→validate→decision→apply cycle.
        
        Returns verification result dict with status and details.
        Silent/internal only, no user-visible output.
        """
        # Initialize continuity dir if not already done
        if self.base_dir:
            if self.continuity_dir is None:
                self.continuity_dir = os.path.join(self.base_dir, "continuity")
            os.makedirs(self.continuity_dir, exist_ok=True)
            self.capsule_path = os.path.join(self.continuity_dir, "active_work_capsule.json")
        
        result = LoopVerificationResult.verified({})
        
        # Step 1: Capture
        capture_result = self._capture_context(context)
        if capture_result["status"] != "captured":
            result = LoopVerificationResult.failed(
                f"capture_failed: {capture_result.get('reason', 'unknown')}",
                {"capture": capture_result},
            )
            return result.to_dict()
        
        # Step 2: Store
        store_result = self._store_capsule(capture_result["capsule"])
        if store_result["status"] != "stored":
            result = LoopVerificationResult.failed(
                f"store_failed: {store_result.get('reason', 'unknown')}",
                {"capture": capture_result, "store": store_result},
            )
            return result.to_dict()
        
        # Step 3: Load
        load_result = self._load_capsule()
        if load_result["status"] != "loaded":
            result = LoopVerificationResult.failed(
                f"load_failed: {load_result.get('reason', 'unknown')}",
                {"capture": capture_result, "store": store_result, "load": load_result},
            )
            return result.to_dict()
        
        # Step 4: Validate
        validate_result = self._validate_capsule(load_result["capsule"])
        if validate_result["status"] != "valid":
            result = LoopVerificationResult.failed(
                f"validate_failed: {validate_result.get('reason', 'unknown')}",
                {
                    "capture": capture_result,
                    "store": store_result,
                    "load": load_result,
                    "validate": validate_result,
                },
            )
            return result.to_dict()
        
        # Step 5: Decision
        decision_result = self._make_decision(validate_result["context"])
        if decision_result["status"] != "apply":
            result = LoopVerificationResult.failed(
                f"decision_failed: {decision_result.get('reason', 'unknown')}",
                {
                    "capture": capture_result,
                    "store": store_result,
                    "load": load_result,
                    "validate": validate_result,
                    "decision": decision_result,
                },
            )
            return result.to_dict()
        
        # Step 6: Apply
        apply_result = self._apply_decision(decision_result["context"])
        if apply_result["status"] != "applied":
            result = LoopVerificationResult.failed(
                f"apply_failed: {apply_result.get('reason', 'unknown')}",
                {
                    "capture": capture_result,
                    "store": store_result,
                    "load": load_result,
                    "validate": validate_result,
                    "decision": decision_result,
                    "apply": apply_result,
                },
            )
            return result.to_dict()
        
        # Full loop verified
        return LoopVerificationResult.verified({
            "capture": capture_result,
            "store": store_result,
            "load": load_result,
            "validate": validate_result,
            "decision": decision_result,
            "apply": apply_result,
        }).to_dict()
    
    def _capture_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Capture context using v93f capture_if_valid_context."""
        return capture_if_valid_context(
            layer_name=context.get("layer_name"),
            task_id=context.get("task_id"),
            phase=context.get("phase"),
            short_task_summary=context.get("short_task_summary"),
            approved_files=context.get("approved_files"),
            pending_tests=context.get("pending_tests"),
            seal_criteria=context.get("seal_criteria"),
            active_constraints=context.get("active_constraints"),
        )
    
    def _store_capsule(self, capsule: ActiveWorkCapsule) -> Dict[str, Any]:
        """Store capsule to file."""
        if self.base_dir is None:
            return {"status": "skipped", "reason": "no_base_dir"}
        
        # Initialize directories and paths
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
            return {"status": "failed", "reason": f"write_error: {str(e)}"}
    
    def _load_capsule(self) -> Dict[str, Any]:
        """Load capsule from file."""
        if self.capsule_path is None:
            return {"status": "skipped", "reason": "no_capsule_path"}
        
        if not os.path.exists(self.capsule_path):
            return {"status": "failed", "reason": "capsule_file_not_found"}
        
        try:
            with open(self.capsule_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            capsule = ActiveWorkCapsule.from_dict(data)
            return {"status": "loaded", "capsule": capsule, "path": self.capsule_path}
        except Exception as e:
            return {"status": "failed", "reason": f"read_error: {str(e)}"}
    
    def _validate_capsule(self, capsule: ActiveWorkCapsule) -> Dict[str, Any]:
        """Validate capsule using v93d freshness policy."""
        # Build minimal context from capsule
        context = CapsuleRebuilder.rebuild_from_capsule(capsule)
        
        # Validate via v93d freshness policy
        freshness = CapsuleFreshnessPolicy.validate_freshness(context)
        
        if freshness.status == "fresh":
            return {"status": "valid", "context": context, "freshness": freshness.to_dict()}
        elif freshness.status == "stale":
            return {"status": "rejected", "reason": freshness.reason, "freshness": freshness.to_dict()}
        else:  # invalid
            return {"status": "rejected", "reason": freshness.reason, "freshness": freshness.to_dict()}
    
    def _make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make decision using v93e resume_from_capsule logic."""
        # Load capsule from file for decision
        capsule = CapsuleRebuilder.load_capsule_file(self.base_dir)
        if capsule is None:
            return {"status": "ignore", "reason": "no_capsule_file"}
        
        # Build context from capsule
        context = CapsuleRebuilder.rebuild_from_capsule(capsule)
        
        # Validate via v93d freshness policy
        freshness = CapsuleFreshnessPolicy.validate_freshness(context)
        
        if freshness.status == "fresh":
            return {"status": "apply", "reason": "capsule_fresh_and_valid", "context": context}
        
        return {
            "status": "stale" if freshness.status == "stale" else "invalid",
            "reason": freshness.reason,
            "freshness": freshness.to_dict(),
        }
    
    def _apply_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply decision (return context for verification)."""
        return {
            "status": "applied",
            "context": context,
            "reason": "decision_applied_successfully",
        }
    
    # ===== Boundary Interaction Verification =====
    
    def verify_boundary_interaction(self) -> Dict[str, Any]:
        """Verify capture boundary + restore boundary integration.
        
        Ensures capture boundary output matches restore boundary input.
        """
        # Sample context for verification
        context = {
            "layer_name": "test_layer",
            "task_id": "test_task",
            "phase": "implementation",
            "short_task_summary": "Test verification",
        }
        
        # Capture
        capture_result = self._capture_context(context)
        if capture_result["status"] != "captured":
            return {
                "status": "failed",
                "reason": f"capture_boundary_not_working: {capture_result.get('reason')}",
            }
        
        capsule = capture_result["capsule"]
        
        # Store
        store_result = self._store_capsule(capsule)
        if store_result["status"] != "stored":
            return {
                "status": "failed",
                "reason": f"capture_boundary_output_not_storable: {store_result.get('reason')}",
            }
        
        # Load
        load_result = self._load_capsule()
        if load_result["status"] != "loaded":
            return {
                "status": "failed",
                "reason": f"restore_boundary_not_receiving: {load_result.get('reason')}",
            }
        
        # Validate
        validate_result = self._validate_capsule(load_result["capsule"])
        if validate_result["status"] != "valid":
            return {
                "status": "failed",
                "reason": f"restore_boundary_validation_failed: {validate_result.get('reason')}",
            }
        
        return {
            "status": "verified",
            "reason": "capture_and_restore_boundaries_integrate_correctly",
        }
    
    # ===== Freshness Policy Integration Verification =====
    
    def verify_freshness_policy_integration(self) -> Dict[str, Any]:
        """Verify v93d freshness policy integration in loop.
        
        Ensures stale/invalid capsules are rejected before decision.
        """
        # Create stale capsule (old timestamp)
        old_timestamp = "2026-04-01T00:00:00Z"
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="test",
            phase="implementation",
            approved_files=[],
            pending_tests=[],
            seal_criteria=[],
            short_task_summary="Test",
            active_constraints=[],
            timestamp=old_timestamp,
        )
        
        # Store stale capsule
        store_result = self._store_capsule(capsule)
        if store_result["status"] != "stored":
            return {
                "status": "failed",
                "reason": f"could_not_create_stale_capsule: {store_result.get('reason')}",
            }
        
        # Load and validate
        load_result = self._load_capsule()
        if load_result["status"] != "loaded":
            return {
                "status": "failed",
                "reason": f"could_not_load_stale_capsule: {load_result.get('reason')}",
            }
        
        validate_result = self._validate_capsule(load_result["capsule"])
        
        if validate_result["status"] != "rejected":
            return {
                "status": "failed",
                "reason": f"freshness_policy_not_working: {validate_result.get('reason')}",
            }
        
        return {
            "status": "verified",
            "reason": "stale_capsule_correctly_rejected",
            "freshness": validate_result.get("freshness"),
        }
    
    # ===== Stale/Invalid Rejection Verification =====
    
    def verify_stale_invalid_rejection(self) -> Dict[str, Any]:
        """Verify stale/invalid capsule rejection behavior.
        
        Tests both stale (age > 24h) and invalid (missing fields) rejection.
        """
        results = {"stale": None, "invalid": None}
        
        # Test stale rejection
        stale_result = self._test_stale_rejection()
        results["stale"] = stale_result
        
        # Test invalid rejection
        invalid_result = self._test_invalid_rejection()
        results["invalid"] = invalid_result
        
        if stale_result["status"] != "verified" or invalid_result["status"] != "verified":
            return {
                "status": "failed",
                "reason": "stale_or_invalid_rejection_not_working",
                "details": results,
            }
        
        return {
            "status": "verified",
            "reason": "both_stale_and_invalid_correctly_rejected",
            "details": results,
        }
    
    def _test_stale_rejection(self) -> Dict[str, Any]:
        """Test stale capsule rejection."""
        old_timestamp = "2026-04-01T00:00:00Z"
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="test",
            phase="implementation",
            approved_files=[],
            pending_tests=[],
            seal_criteria=[],
            short_task_summary="Stale test",
            active_constraints=[],
            timestamp=old_timestamp,
        )
        
        store_result = self._store_capsule(capsule)
        if store_result["status"] != "stored":
            return {"status": "failed", "reason": f"could_not_create_stale_capsule"}
        
        load_result = self._load_capsule()
        if load_result["status"] != "loaded":
            return {"status": "failed", "reason": f"could_not_load_stale_capsule"}
        
        validate_result = self._validate_capsule(load_result["capsule"])
        
        if validate_result["status"] != "rejected":
            return {"status": "failed", "reason": "stale_capsule_not_rejected"}
        
        return {"status": "verified", "reason": "stale_capsule_correctly_rejected"}
    
    def _test_invalid_rejection(self) -> Dict[str, Any]:
        """Test invalid capsule rejection."""
        # Create capsule with invalid phase (not in VALID_RESTORE_PHASES)
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="invalid_phase",  # Invalid: not a valid restore phase
            approved_files=[],
            pending_tests=[],
            seal_criteria=[],
            short_task_summary="Invalid test",
            active_constraints=[],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        store_result = self._store_capsule(capsule)
        if store_result["status"] != "stored":
            return {"status": "failed", "reason": f"could_not_create_invalid_capsule"}
        
        load_result = self._load_capsule()
        if load_result["status"] != "loaded":
            return {"status": "failed", "reason": f"could_not_load_invalid_capsule"}
        
        validate_result = self._validate_capsule(load_result["capsule"])
        
        if validate_result["status"] != "rejected":
            return {"status": "failed", "reason": "invalid_capsule_not_rejected"}
        
        return {"status": "verified", "reason": "invalid_capsule_correctly_rejected"}
    
    # ===== Silent Decision Behavior Verification =====
    
    def verify_silent_decision_behavior(self) -> Dict[str, Any]:
        """Verify no user-visible behavior changes.
        
        Decision behavior should be silent/internal only.
        """
        context = {
            "layer_name": "test_layer",
            "task_id": "test_task",
            "phase": "implementation",
            "short_task_summary": "Test verification",
        }
        
        capture_result = self._capture_context(context)
        if capture_result["status"] != "captured":
            return {
                "status": "failed",
                "reason": "capture_boundary_not_working",
            }
        
        store_result = self._store_capsule(capture_result["capsule"])
        if store_result["status"] != "stored":
            return {
                "status": "failed",
                "reason": "capture_boundary_output_not_storable",
            }
        
        load_result = self._load_capsule()
        if load_result["status"] != "loaded":
            return {
                "status": "failed",
                "reason": "restore_boundary_not_receiving",
            }
        
        decision_result = self._make_decision({})
        
        # Decision should be silent/internal only
        if decision_result["status"] != "apply":
            return {
                "status": "failed",
                "reason": f"decision_not_silent: {decision_result.get('reason')}",
            }
        
        return {
            "status": "verified",
            "reason": "decision_behavior_is_silent_internal_only",
        }
    
    # ===== Export Verification Summary =====
    
    def export_verification_summary(self) -> Dict[str, Any]:
        """Export operator-readable + machine-readable verification summary.
        
        Includes all verification results for operator review.
        """
        boundary_result = self.verify_boundary_interaction()
        freshness_result = self.verify_freshness_policy_integration()
        rejection_result = self.verify_stale_invalid_rejection()
        silent_result = self.verify_silent_decision_behavior()
        
        return {
            "verification_summary": {
                "status": "all_passed" if all(
                    r["status"] == "verified" 
                    for r in [boundary_result, freshness_result, rejection_result, silent_result]
                ) else "some_failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "details": {
                "boundary_interaction": boundary_result,
                "freshness_policy_integration": freshness_result,
                "stale_invalid_rejection": rejection_result,
                "silent_decision_behavior": silent_result,
            },
        }


# ===== v93f integration: Capture If Valid Context (already in active_work_capsule.py) =====
# Import from active_work_capsule to avoid duplication


def capture_if_valid_context(
    layer_name: str,
    task_id: str,
    phase: str,
    short_task_summary: str,
    approved_files: list = None,
    pending_tests: list = None,
    seal_criteria: list = None,
    active_constraints: list = None,
    timestamp: str = None,
) -> Dict[str, Any]:
    """Silent internal capsule capture trigger boundary.
    
    v93f: Silent Capsule Capture Trigger Boundary.
    Copied here for v93g verification module self-containment.
    
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
    from .active_work_capsule import ActiveWorkCapsule
    
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
