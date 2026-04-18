# test_capability_boundary.py - WESLR v40: Capability / Permission Boundary Layer Tests
# Focused tests for capability boundary layer.
# Additive only, transparent, reversible, non-manipulative, no repo drift.

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.capability_boundary import (
    CapabilityType,
    CapabilityAction,
    CapabilityScope,
    CapabilityPermission,
    CapabilityBoundary,
    get_capability_boundary_registry,
    CapabilityBoundaryEngine,
    integrate_with_deployment_persona,
    integrate_with_safety_contract,
    integrate_with_proof_gate,
    integrate_with_governance_surface,
)


class TestCapabilityTypeEnum(TestCase):
    """Test capability type enum values."""
    
    def test_all_capability_types_present(self):
        """All expected capability types are defined."""
        expected_capabilities = [
            "read_data",
            "read_files",
            "read_memory",
            "analyze",
            "analyze_code",
            "analyze_health",
            "configure",
            "update_config",
            "delete_config",
            "api_call",
            "http_request",
            "database_write",
            "file_write",
            "file_delete",
            "system_command",
            "actuate",
            "execute",
            "autonomous",
            "plan",
            "recommend",
            "forecast",
            "surface",
            "block",
            "gate",
            "audit",
        ]
        
        for cap in expected_capabilities:
            self.assertIn(cap, [c.value for c in CapabilityType])
    
    def test_capabilities_are_strings(self):
        """All capability values are strings."""
        for cap in CapabilityType:
            self.assertIsInstance(cap.value, str)
    
    def test_unique_capability_values(self):
        """All capability values are unique."""
        cap_values = [c.value for c in CapabilityType]
        self.assertEqual(len(cap_values), len(set(cap_values)))


class TestCapabilityActionEnum(TestCase):
    """Test capability action enum values."""
    
    def test_all_actions_present(self):
        """All expected actions are defined."""
        expected_actions = [
            "allow",
            "restrict",
            "prohibit",
            "approval_gated",
            "degraded",
        ]
        
        for action in expected_actions:
            self.assertIn(action, [a.value for a in CapabilityAction])


class TestCapabilityScopeEnum(TestCase):
    """Test capability scope enum values."""
    
    def test_all_scopes_present(self):
        """All expected scopes are defined."""
        expected_scopes = [
            "global",
            "local",
            "external",
            "internal",
            "surface",
            "execution",
        ]
        
        for scope in expected_scopes:
            self.assertIn(scope, [s.value for s in CapabilityScope])


class TestCapabilityPermission(TestCase):
    """Test CapabilityPermission data class."""
    
    def test_permission_creation(self):
        """Permission creation works correctly."""
        permission = CapabilityPermission(
            capability=CapabilityType.API_CALL.value,
            action=CapabilityAction.ALLOW.value,
            scope=CapabilityScope.EXTERNAL.value,
            max_frequency_hz=1.0,
            approval_required=True,
        )
        
        self.assertEqual(permission.capability, CapabilityType.API_CALL.value)
        self.assertEqual(permission.action, CapabilityAction.ALLOW.value)
        self.assertEqual(permission.scope, CapabilityScope.EXTERNAL.value)
        self.assertEqual(permission.max_frequency_hz, 1.0)
        self.assertTrue(permission.approval_required)
    
    def test_is_allowed(self):
        """is_allowed works correctly."""
        permission = CapabilityPermission(
            capability=CapabilityType.READ_DATA.value,
            action=CapabilityAction.ALLOW.value,
        )
        self.assertTrue(permission.is_allowed())
        
        permission.action = CapabilityAction.RESTRICT.value
        self.assertFalse(permission.is_allowed())
        
        permission.action = CapabilityAction.PROHIBIT.value
        self.assertFalse(permission.is_allowed())
    
    def test_is_restricted(self):
        """is_restricted works correctly."""
        permission = CapabilityPermission(
            capability=CapabilityType.READ_DATA.value,
            action=CapabilityAction.RESTRICT.value,
        )
        self.assertTrue(permission.is_restricted())
        
        permission.action = CapabilityAction.ALLOW.value
        self.assertFalse(permission.is_restricted())
    
    def test_is_prohibited(self):
        """is_prohibited works correctly."""
        permission = CapabilityPermission(
            capability=CapabilityType.READ_DATA.value,
            action=CapabilityAction.PROHIBIT.value,
        )
        self.assertTrue(permission.is_prohibited())
        
        permission.action = CapabilityAction.ALLOW.value
        self.assertFalse(permission.is_prohibited())
    
    def test_to_dict(self):
        """Permission to_dict conversion works."""
        permission = CapabilityPermission(
            capability=CapabilityType.API_CALL.value,
            action=CapabilityAction.ALLOW.value,
        )
        
        result = permission.to_dict()
        
        self.assertEqual(result["capability"], CapabilityType.API_CALL.value)
        self.assertEqual(result["action"], CapabilityAction.ALLOW.value)
        self.assertIn("created_at", result)
    
    def test_from_dict(self):
        """Permission from_dict reconstruction works."""
        original = CapabilityPermission(
            capability=CapabilityType.FORECAST.value,
            action=CapabilityAction.ALLOW.value,
            approval_required=True,
        )
        
        data = original.to_dict()
        recreated = CapabilityPermission.from_dict(data)
        
        self.assertEqual(recreated.capability, original.capability)
        self.assertEqual(recreated.action, original.action)
        self.assertEqual(recreated.approval_required, original.approval_required)


class TestCapabilityBoundary(TestCase):
    """Test CapabilityBoundary data class."""
    
    def test_boundary_creation(self):
        """Boundary creation works correctly."""
        boundary = CapabilityBoundary(
            boundary_id="test_boundary",
            role="test_role",
            allowed_capabilities=[{"capability": "read_data", "action": "allow"}],
            prohibited_capabilities=[{"capability": "execute", "action": "prohibit"}],
            max_concurrent_capabilities=3,
        )
        
        self.assertEqual(boundary.boundary_id, "test_boundary")
        self.assertEqual(boundary.role, "test_role")
        self.assertEqual(len(boundary.allowed_capabilities), 1)
        self.assertEqual(len(boundary.prohibited_capabilities), 1)
        self.assertEqual(boundary.max_concurrent_capabilities, 3)
    
    def test_boundary_update(self):
        """Boundary update refreshes timestamp."""
        boundary = CapabilityBoundary(
            boundary_id="test_boundary",
            role="test_role",
            max_concurrent_capabilities=3,
        )
        
        original_timestamp = boundary.updated_at
        updated = boundary.update(max_concurrent_capabilities=5)
        
        self.assertEqual(updated.max_concurrent_capabilities, 5)
        self.assertNotEqual(updated.updated_at, original_timestamp)
    
    def test_to_dict(self):
        """Boundary to_dict conversion works."""
        boundary = CapabilityBoundary(
            boundary_id="test_boundary",
            role="test_role",
            allowed_capabilities=[{"capability": "read_data", "action": "allow"}],
        )
        
        result = boundary.to_dict()
        
        self.assertEqual(result["boundary_id"], "test_boundary")
        self.assertEqual(result["role"], "test_role")
        self.assertEqual(len(result["allowed_capabilities"]), 1)
        self.assertIn("created_at", result)
        self.assertIn("updated_at", result)
    
    def test_from_dict(self):
        """Boundary from_dict reconstruction works."""
        original = CapabilityBoundary(
            boundary_id="test_boundary",
            role="test_role",
            max_concurrent_capabilities=4,
            max_frequency_per_minute=30,
        )
        
        data = original.to_dict()
        recreated = CapabilityBoundary.from_dict(data)
        
        self.assertEqual(recreated.boundary_id, original.boundary_id)
        self.assertEqual(recreated.role, original.role)
        self.assertEqual(recreated.max_concurrent_capabilities, original.max_concurrent_capabilities)


class TestCapabilityBoundaryRegistry(TestCase):
    """Test get_capability_boundary_registry function."""
    
    def test_registry_contains_all_roles(self):
        """Registry contains all predefined roles."""
        registry = get_capability_boundary_registry()
        
        expected_roles = [
            "home_family",
            "education",
            "hospitals_medicine",
            "science_research",
            "industry",
            "aerospace_long_mission",
        ]
        
        for role in expected_roles:
            self.assertIn(role, registry)
    
    def test_registry_boundaries_have_expected_properties(self):
        """Registry boundaries have expected properties."""
        registry = get_capability_boundary_registry()
        
        # Test home_family boundary
        home_boundary = registry["home_family"]
        self.assertEqual(home_boundary.max_concurrent_capabilities, 3)
        self.assertEqual(home_boundary.max_frequency_per_minute, 30)
        self.assertEqual(len(home_boundary.prohibited_capabilities), 4)
        
        # Test hospitals_medicine boundary
        hospital_boundary = registry["hospitals_medicine"]
        self.assertEqual(hospital_boundary.max_concurrent_capabilities, 1)
        self.assertEqual(hospital_boundary.max_frequency_per_minute, 10)
        self.assertEqual(len(hospital_boundary.prohibited_capabilities), 7)
        
        # Test aerospace boundary
        aerospace_boundary = registry["aerospace_long_mission"]
        self.assertEqual(aerospace_boundary.max_concurrent_capabilities, 3)
        self.assertEqual(aerospace_boundary.max_frequency_per_minute, 30)
        self.assertEqual(len(aerospace_boundary.prohibited_capabilities), 1)
    
    def test_home_family_allowed_capabilities(self):
        """Home family boundary has expected allowed capabilities."""
        registry = get_capability_boundary_registry()
        boundary = registry["home_family"]
        
        allowed_caps = [c["capability"] for c in boundary.allowed_capabilities]
        self.assertIn("read_data", allowed_caps)
        self.assertIn("read_memory", allowed_caps)
        self.assertIn("analyze", allowed_caps)


class TestCapabilityBoundaryEngine(TestCase):
    """Test CapabilityBoundaryEngine class."""
    
    def test_engine_initialization(self):
        """Engine initialization loads boundaries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            
            self.assertGreater(len(engine.boundaries), 0)
            self.assertEqual(len(engine.active_boundaries), 0)
    
    def test_get_boundary(self):
        """Engine get_boundary works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            
            boundary = engine.get_boundary("home_family")
            self.assertIsNotNone(boundary)
            self.assertEqual(boundary.role, "home_family")
    
    def test_get_default_boundary(self):
        """Engine get_default_boundary works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            
            boundary = engine.get_default_boundary()
            
            self.assertIsNotNone(boundary)
            self.assertEqual(boundary.role, "home_family")
    
    def test_set_active_boundary(self):
        """Engine set_active_boundary works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            
            role = engine.set_active_boundary("test-context", "education")
            
            self.assertEqual(role, "education")
            self.assertEqual(engine.active_boundaries["test-context"], "education")
    
    def test_set_active_boundary_fallback(self):
        """Engine set_active_boundary falls back to home_family for unknown role."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            
            role = engine.set_active_boundary("test-context", "unknown_role")
            
            self.assertEqual(role, "home_family")
    
    def test_check_capability_allowed(self):
        """Engine check_capability works for allowed capabilities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            engine.set_active_boundary("test-context", "home_family")
            
            result = engine.check_capability("read_data", "allow", "test-context")
            
            self.assertTrue(result["permitted"])
            self.assertIn("allowed", result["reason"].lower())
    
    def test_check_capability_prohibited(self):
        """Engine check_capability works for prohibited capabilities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            engine.set_active_boundary("test-context", "home_family")
            
            result = engine.check_capability("execute", "allow", "test-context")
            
            self.assertFalse(result["permitted"])
            self.assertIn("prohibited", result["reason"].lower())
    
    def test_check_capability_approval_gated(self):
        """Engine check_capability works for approval-gated capabilities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            engine.set_active_boundary("test-context", "home_family")
            
            result = engine.check_capability("autonomous", "allow", "test-context")
            
            self.assertFalse(result["permitted"])
            self.assertIn("requires approval", result["reason"].lower())
            self.assertTrue(result.get("requires_approval", False))
    
    def test_check_capability_not_explicitly_permitted(self):
        """Engine check_capability returns not permitted for unlisted capability."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            engine.set_active_boundary("test-context", "home_family")
            
            result = engine.check_capability("unknown_capability", "allow", "test-context")
            
            self.assertFalse(result["permitted"])
            self.assertIn("not explicitly permitted", result["reason"].lower())
    
    def test_get_degraded_boundary(self):
        """Engine get_degraded_boundary creates degraded mode boundary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            
            base_boundary = engine.get_boundary("home_family")
            degraded_boundary = engine.get_degraded_boundary(base_boundary)
            
            self.assertNotEqual(degraded_boundary.boundary_id, base_boundary.boundary_id)
            self.assertIn("degraded", degraded_boundary.boundary_id)
            self.assertLess(degraded_boundary.max_concurrent_capabilities, base_boundary.max_concurrent_capabilities)
            self.assertLess(degraded_boundary.max_frequency_per_minute, base_boundary.max_frequency_per_minute)
    
    def test_to_dict(self):
        """Engine to_dict conversion works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            engine.set_active_boundary("test-context", "education")
            
            result = engine.to_dict()
            
            self.assertGreater(result["boundary_count"], 0)
            self.assertEqual(result["active_boundary_count"], 1)
            self.assertIn("boundaries", result)
            self.assertIn("active_boundaries", result)


class TestIntegrationHooks(TestCase):
    """Test integration hook functions."""
    
    def test_integrate_with_deployment_persona(self):
        """integrate_with_deployment_persona adds boundary context."""
        persona_dict = {"recommendation": "test"}
        
        result = integrate_with_deployment_persona(persona_dict)
        
        self.assertIn("capability_boundary_context", result)
        self.assertIsNone(result["capability_boundary_context"])
    
    def test_integrate_with_deployment_persona_with_engine(self):
        """integrate_with_deployment_persona works with boundary engine."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            engine.set_active_boundary("integration-test", "science_research")
            
            persona_dict = {"recommendation": "test"}
            
            result = integrate_with_deployment_persona(
                persona_dict,
                boundary_engine=engine,
                context_id="integration-test",
            )
            
            self.assertIn("capability_boundary_context", result)
            self.assertIsNotNone(result["capability_boundary_context"])
            self.assertEqual(result["capability_boundary_context"]["boundary_id"], "science_research_v40")
    
    def test_integrate_with_safety_contract(self):
        """integrate_with_safety_contract adds boundary context."""
        safety_dict = {"safety_level": "low"}
        
        result = integrate_with_safety_contract(safety_dict)
        
        self.assertIn("capability_boundary_context", result)
        self.assertIsNone(result["capability_boundary_context"])
    
    def test_integrate_with_safety_contract_with_engine(self):
        """integrate_with_safety_contract works with boundary engine."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            engine.set_active_boundary("safety-test", "hospitals_medicine")
            
            safety_dict = {"safety_level": "critical"}
            
            result = integrate_with_safety_contract(
                safety_dict,
                boundary_engine=engine,
                context_id="safety-test",
            )
            
            self.assertIn("capability_boundary_context", result)
            self.assertIsNotNone(result["capability_boundary_context"])
            self.assertEqual(result["capability_boundary_context"]["boundary_id"], "hospitals_medicine_v40")
    
    def test_integrate_with_proof_gate(self):
        """integrate_with_proof_gate adds boundary context."""
        proof_dict = {"execution_eligible": False}
        
        result = integrate_with_proof_gate(proof_dict)
        
        self.assertIn("capability_boundary_context", result)
        self.assertIsNone(result["capability_boundary_context"])
    
    def test_integrate_with_governance_surface(self):
        """integrate_with_governance_surface adds boundary context."""
        governance_dict = {"approval_required": False}
        
        result = integrate_with_governance_surface(governance_dict)
        
        self.assertIn("capability_boundary_context", result)
        self.assertIsNone(result["capability_boundary_context"])


class TestRoleBasedCapabilities(TestCase):
    """Test role-based capability boundaries."""
    
    def test_hospitals_medicine_has_highly_restricted_capabilities(self):
        """Hospitals/medicine role has highly restricted capabilities."""
        registry = get_capability_boundary_registry()
        boundary = registry["hospitals_medicine"]
        
        # Should have very few allowed capabilities
        self.assertLessEqual(len(boundary.allowed_capabilities), 5)
        
        # Should have many prohibited capabilities
        self.assertGreaterEqual(len(boundary.prohibited_capabilities), 5)
        
        # Should have maximum caution
        self.assertEqual(boundary.max_concurrent_capabilities, 1)
    
    def test_science_research_has_expanded_capabilities(self):
        """Science/research role has expanded capabilities."""
        registry = get_capability_boundary_registry()
        boundary = registry["science_research"]
        
        # Should have more allowed capabilities
        self.assertGreater(len(boundary.allowed_capabilities), 5)
        
        # Should have fewer prohibited capabilities
        self.assertLess(len(boundary.prohibited_capabilities), 3)
        
        # Should have high frequency limit
        self.assertEqual(boundary.max_frequency_per_minute, 120)
    
    def test_aerospace_boundary_autonomous_approval(self):
        """Aerospace boundary requires approval for autonomous actions."""
        registry = get_capability_boundary_registry()
        boundary = registry["aerospace_long_mission"]
        
        # Autonomous is approval-gated, not prohibited
        autonomous_approval_gated = any(
            c["capability"] == "autonomous" and c["action"] == "approval_gated"
            for c in boundary.approval_gated_capabilities
        )
        self.assertTrue(autonomous_approval_gated)
        
        # Execute is prohibited
        execute_prohibited = any(
            c["capability"] == "execute" and c["action"] == "prohibit"
            for c in boundary.prohibited_capabilities
        )
        self.assertTrue(execute_prohibited)
    
    def test_education_boundary_allows_code_analysis(self):
        """Education boundary allows code analysis."""
        registry = get_capability_boundary_registry()
        boundary = registry["education"]
        
        allowed_caps = [c["capability"] for c in boundary.allowed_capabilities]
        self.assertIn("analyze_code", allowed_caps)
    
    def test_industry_boundary_has_approval_gated_actuate(self):
        """Industry boundary has approval-gated actuate capability."""
        registry = get_capability_boundary_registry()
        boundary = registry["industry"]
        
        approval_gated_caps = [c["capability"] for c in boundary.approval_gated_capabilities]
        self.assertIn("actuate", approval_gated_caps)


class TestBackwardCompatibility(TestCase):
    """Test backward compatibility with existing code."""
    
    def test_existing_code_works_without_boundary_context(self):
        """Existing code works when boundary context not provided."""
        # Integration hooks should work without boundary engine
        persona_result = integrate_with_deployment_persona({"test": "data"})
        self.assertEqual(persona_result["test"], "data")
        
        safety_result = integrate_with_safety_contract({"test": "data"})
        self.assertEqual(safety_result["test"], "data")
        
        proof_result = integrate_with_proof_gate({"test": "data"})
        self.assertEqual(proof_result["test"], "data")
    
    def test_engine_without_context(self):
        """Engine works without active boundary (uses defaults)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            
            # No context set - should use defaults
            boundary = engine.get_active_boundary("nonexistent")
            
            self.assertIsNotNone(boundary)
            self.assertEqual(boundary.role, "home_family")
    
    def test_missing_role_fallback(self):
        """Engine handles missing role gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = CapabilityBoundaryEngine(storage_path=tmpdir)
            
            # Set to non-existent role
            engine.set_active_boundary("test", "nonexistent_role")
            
            boundary = engine.get_active_boundary("test")
            
            # Should fall back to home_family
            self.assertIsNotNone(boundary)
            self.assertEqual(boundary.role, "home_family")


class TestSerialization(TestCase):
    """Test serialization and deserialization."""
    
    def test_permission_serialization(self):
        """Permission serialization round-trip works."""
        original = CapabilityPermission(
            capability="read_data",
            action="allow",
            approval_required=True,
        )
        
        data = original.to_dict()
        recreated = CapabilityPermission.from_dict(data)
        
        self.assertEqual(original.capability, recreated.capability)
        self.assertEqual(original.action, recreated.action)
        self.assertEqual(original.approval_required, recreated.approval_required)
    
    def test_boundary_serialization(self):
        """Boundary serialization round-trip works."""
        original = CapabilityBoundary(
            boundary_id="serial-test",
            role="test_role",
            max_concurrent_capabilities=5,
        )
        
        data = original.to_dict()
        recreated = CapabilityBoundary.from_dict(data)
        
        self.assertEqual(original.boundary_id, recreated.boundary_id)
        self.assertEqual(original.role, recreated.role)
        self.assertEqual(original.max_concurrent_capabilities, recreated.max_concurrent_capabilities)


if __name__ == "__main__":
    import unittest
    unittest.main()
