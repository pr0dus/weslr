"""Test suite for Capsule Freshness / Acceptance Policy Layer (v93d)

Test Doctrine version: 1.0.0 (2026-04-08)

Test categories:
- Model: Dataclass, constants, serialization
- Behavior: validate_freshness, is_stale, is_invalid, acceptance
- Integration: hooks into continuity, operator workflow
- BackwardCompatibility: v93c restore flows still work
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from weslr.capsule_policy import (
    CapsuleFreshnessPolicy,
    FreshnessResult,
    MAX_CAPSULE_AGE_SECONDS,
    VALID_RESTORE_PHASES,
)


# ===== Model Tests (TestCapsuleFreshnessPolicyModel) =====

class TestCapsuleFreshnessPolicyModel(unittest.TestCase):
    """Dataclass, constants, serialization."""
    
    def test_constants_defined(self):
        """Test constants are defined and reasonable."""
        self.assertEqual(MAX_CAPSULE_AGE_SECONDS, 24 * 60 * 60)
        self.assertEqual(MAX_CAPSULE_AGE_SECONDS, 86400)
        self.assertIn("planning", VALID_RESTORE_PHASES)
        self.assertIn("implementation", VALID_RESTORE_PHASES)
        self.assertIn("seal", VALID_RESTORE_PHASES)
        self.assertEqual(len(VALID_RESTORE_PHASES), 3)
    
    def test_freshness_result_dataclass(self):
        """Test FreshnessResult dataclass fields."""
        result = FreshnessResult.fresh("test reason")
        self.assertEqual(result.status, "fresh")
        self.assertEqual(result.reason, "test reason")
        self.assertIn("T", result.timestamp)  # ISO-8601
        
        result = FreshnessResult.stale(86401)
        self.assertEqual(result.status, "stale")
        self.assertIn("capsule_age", result.reason)
        
        result = FreshnessResult.invalid("test reason")
        self.assertEqual(result.status, "invalid")
        self.assertEqual(result.reason, "test reason")
    
    def test_freshness_result_to_dict(self):
        """Test FreshnessResult to_dict serialization."""
        result = FreshnessResult.fresh("all checks passed")
        d = result.to_dict()
        self.assertEqual(d["status"], "fresh")
        self.assertEqual(d["reason"], "all checks passed")
        self.assertIn("timestamp", d)
    
    def test_freshness_result_factory_methods(self):
        """Test factory methods for different statuses."""
        fresh = FreshnessResult.fresh()
        self.assertEqual(fresh.status, "fresh")
        
        stale = FreshnessResult.stale(86401)
        self.assertEqual(stale.status, "stale")
        self.assertIn("capsule_age", stale.reason)
        
        invalid = FreshnessResult.invalid("missing fields")
        self.assertEqual(invalid.status, "invalid")
        self.assertIn("missing fields", invalid.reason)


# ===== Behavior Tests (TestCapsuleFreshnessPolicyBehavior) =====

class TestCapsuleFreshnessPolicyBehavior(unittest.TestCase):
    """validate_freshness, is_stale, is_invalid, acceptance."""
    
    def setUp(self):
        """Create valid capsule for testing."""
        now = datetime.now(timezone.utc)
        self.valid_capsule = {
            "current_layer": "test_layer",
            "current_phase": "planning",
            "timestamp": now.isoformat(),
        }
        self.stale_capsule = {
            "current_layer": "test_layer",
            "current_phase": "planning",
            "timestamp": (now - timedelta(hours=25)).isoformat(),
        }
    
    def test_validate_freshness_valid(self):
        """Test validate_freshness returns fresh for valid capsule."""
        result = CapsuleFreshnessPolicy.validate_freshness(self.valid_capsule)
        self.assertEqual(result.status, "fresh")
    
    def test_validate_freshness_empty(self):
        """Test validate_freshness returns invalid for empty capsule."""
        result = CapsuleFreshnessPolicy.validate_freshness({})
        self.assertEqual(result.status, "invalid")
        self.assertIn("empty", result.reason.lower())
    
    def test_validate_freshness_missing_fields(self):
        """Test validate_freshness returns invalid for missing fields."""
        capsule = {"current_phase": "planning"}  # missing current_layer, timestamp
        result = CapsuleFreshnessPolicy.validate_freshness(capsule)
        self.assertEqual(result.status, "invalid")
        self.assertIn("missing_fields", result.reason)
    
    def test_validate_freshness_invalid_phase(self):
        """Test validate_freshness returns invalid for invalid phase."""
        capsule = {
            "current_layer": "test",
            "current_phase": "invalid_phase",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        result = CapsuleFreshnessPolicy.validate_freshness(capsule)
        self.assertEqual(result.status, "invalid")
        self.assertIn("invalid_phase", result.reason)
    
    def test_validate_freshness_invalid_timestamp(self):
        """Test validate_freshness returns invalid for bad timestamp."""
        capsule = {
            "current_layer": "test",
            "current_phase": "planning",
            "timestamp": "not-a-timestamp",
        }
        result = CapsuleFreshnessPolicy.validate_freshness(capsule)
        self.assertEqual(result.status, "invalid")
        self.assertIn("timestamp", result.reason)
    
    def test_validate_freshness_stale(self):
        """Test validate_freshness returns stale for old capsule."""
        capsule = {
            "current_layer": "test",
            "current_phase": "planning",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
        }
        result = CapsuleFreshnessPolicy.validate_freshness(capsule)
        self.assertEqual(result.status, "stale")
    
    def test_is_stale_true(self):
        """Test is_stale returns True for stale capsule."""
        capsule = {
            "current_layer": "test",
            "current_phase": "planning",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
        }
        self.assertTrue(CapsuleFreshnessPolicy.is_stale(capsule))
    
    def test_is_stale_false(self):
        """Test is_stale returns False for fresh capsule."""
        self.assertFalse(CapsuleFreshnessPolicy.is_stale(self.valid_capsule))
    
    def test_is_invalid_true(self):
        """Test is_invalid returns True for invalid capsule."""
        capsule = {"current_phase": "invalid"}  # missing fields
        self.assertTrue(CapsuleFreshnessPolicy.is_invalid(capsule))
    
    def test_is_invalid_false(self):
        """Test is_invalid returns False for valid capsule."""
        self.assertFalse(CapsuleFreshnessPolicy.is_invalid(self.valid_capsule))
    
    def test_should_reject_fully_stale(self):
        """Test should_reject_fully returns True for stale capsule."""
        capsule = {
            "current_layer": "test",
            "current_phase": "planning",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
        }
        self.assertTrue(CapsuleFreshnessPolicy.should_reject_fully(capsule))
    
    def test_should_reject_fully_invalid(self):
        """Test should_reject_fully returns True for invalid capsule."""
        capsule = {"current_phase": "invalid"}  # missing fields
        self.assertTrue(CapsuleFreshnessPolicy.should_reject_fully(capsule))
    
    def test_should_reject_fully_false(self):
        """Test should_reject_fully returns False for valid capsule."""
        self.assertFalse(CapsuleFreshnessPolicy.should_reject_fully(self.valid_capsule))
    
    def test_get_rejection_reason_stale(self):
        """Test get_rejection_reason returns reason for stale capsule."""
        capsule = {
            "current_layer": "test",
            "current_phase": "planning",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
        }
        reason = CapsuleFreshnessPolicy.get_rejection_reason(capsule)
        self.assertIn("capsule_age", reason.lower())
    
    def test_get_rejection_reason_invalid(self):
        """Test get_rejection_reason returns reason for invalid capsule."""
        capsule = {"current_phase": "invalid"}
        reason = CapsuleFreshnessPolicy.get_rejection_reason(capsule)
        self.assertIn("missing_fields", reason.lower())


# ===== Integration Tests (TestCapsuleFreshnessPolicyIntegration) =====

class TestCapsuleFreshnessPolicyIntegration(unittest.TestCase):
    """Hooks into continuity, operator workflow."""
    
    def test_policy_integration_with_validation_boundary(self):
        """Test policy integrates with existing validation boundary."""
        from weslr.capsule_recovery import CapsuleValidator
        
        # Create capsule that passes v93c validation
        now = datetime.now(timezone.utc)
        capsule = {
            "current_layer": "test_layer",
            "current_phase": "planning",
            "timestamp": now.isoformat(),
        }
        
        # Should pass v93c validation
        v93c_result = CapsuleValidator.validate_restored_context(capsule)
        self.assertEqual(v93c_result["status"], "valid")
        
        # Should pass v93d freshness policy
        v93d_result = CapsuleFreshnessPolicy.validate_freshness(capsule)
        self.assertEqual(v93d_result.status, "fresh")
    
    def test_stale_capsule_rejected_by_both_layers(self):
        """Test stale capsule rejected by both v93c and v93d."""
        from weslr.capsule_recovery import CapsuleValidator
        
        # Create stale capsule
        capsule = {
            "current_layer": "test_layer",
            "current_phase": "planning",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
        }
        
        # v93c should flag as stale
        v93c_result = CapsuleValidator.validate_restored_context(capsule)
        self.assertEqual(v93c_result["status"], "stale")
        
        # v93d should also flag as stale
        v93d_result = CapsuleFreshnessPolicy.validate_freshness(capsule)
        self.assertEqual(v93d_result.status, "stale")


# ===== Backward Compatibility Tests (TestCapsuleFreshnessPolicyBackwardCompatibility) =====

class TestCapsuleFreshnessPolicyBackwardCompatibility(unittest.TestCase):
    """v93c restore flows still work."""
    
    def test_v93c_restore_flow_without_policy(self):
        """Test v93c restore flows work without policy integration."""
        from weslr.capsule_recovery import CapsuleValidator, restore_from_capsule
        
        # Create valid capsule
        now = datetime.now(timezone.utc)
        capsule = {
            "current_layer": "test_layer",
            "current_phase": "planning",
            "timestamp": now.isoformat(),
        }
        
        # v93c validation should still work
        result = CapsuleValidator.validate_restored_context(capsule)
        self.assertEqual(result["status"], "valid")
    
    def test_restore_from_capsule_integration(self):
        """Test restore_from_capsule integrates with existing continuity."""
        from weslr.capsule_recovery import restore_from_capsule
        
        # Test returns expected structure
        result = restore_from_capsule()
        self.assertIn("status", result)
    
    def test_v93d_additive_only(self):
        """Test v93d is additive only (no breaking changes)."""
        # Existing v93c flows should still work
        from weslr.capsule_recovery import CapsuleValidator
        
        capsule = {
            "current_layer": "test",
            "current_phase": "planning",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # v93c should still return valid
        result = CapsuleValidator.validate_restored_context(capsule)
        self.assertEqual(result["status"], "valid")
        
        # v93d should also accept it
        result = CapsuleFreshnessPolicy.validate_freshness(capsule)
        self.assertEqual(result.status, "fresh")


if __name__ == "__main__":
    unittest.main()
