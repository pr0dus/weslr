# test_escalation.py - WESLR v41: Escalation / Human Handoff Layer Tests
# Focused tests for escalation layer.
# Additive only, transparent, reversible, non-manipulative, no repo drift.

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.escalation import (
    EscalationTrigger,
    EscalationReason,
    RequiredHumanRole,
    UrgencyLevel,
    HandoffStatus,
    HandoffPackage,
    EscalationRequest,
    get_escalation_human_roles,
    EscalationEngine,
    integrate_with_capability_boundary,
    integrate_with_safety_contract,
    integrate_with_proof_gate,
    integrate_with_governance_surface,
)


class TestEscalationTriggerEnum(TestCase):
    """Test escalation trigger enum values."""
    
    def test_all_triggers_present(self):
        """All expected triggers are defined."""
        expected_triggers = [
            "blocked_by_capability",
            "restricted_by_capability",
            "requires_approval",
            "high_risk",
            "no_explanation",
            "specialist_required",
            "unreliable_connection",
            "degraded_mode",
            "other",
        ]
        
        for trigger in expected_triggers:
            self.assertIn(trigger, [t.value for t in EscalationTrigger])
    
    def test_triggers_are_strings(self):
        """All trigger values are strings."""
        for trigger in EscalationTrigger:
            self.assertIsInstance(trigger.value, str)


class TestEscalationReasonEnum(TestCase):
    """Test escalation reason enum values."""
    
    def test_all_reasons_present(self):
        """All expected reasons are defined."""
        expected_reasons = [
            "capability_prohibited",
            "capability_restricted",
            "capability_approval_needed",
            "safety_threshold_exceeded",
            "insufficient_evidence",
            "lacks_specialist",
            "network_failure",
            "degraded_operations",
            "unknown",
        ]
        
        for reason in expected_reasons:
            self.assertIn(reason, [r.value for r in EscalationReason])


class TestRequiredHumanRoleEnum(TestCase):
    """Test required human role enum values."""
    
    def test_all_roles_present(self):
        """All expected roles are defined."""
        expected_roles = [
            "operator",
            "administrator",
            "domain_expert",
            "operations_specialist",
            "security_specialist",
            "auditor",
            "emergency_contact",
            "legal_reviewer",
            "customer",
            "technical_support",
        ]
        
        for role in expected_roles:
            self.assertIn(role, [r.value for r in RequiredHumanRole])
    
    def test_unique_roles(self):
        """All role values are unique."""
        role_values = [r.value for r in RequiredHumanRole]
        self.assertEqual(len(role_values), len(set(role_values)))


class TestUrgencyLevelEnum(TestCase):
    """Test urgency level enum values."""
    
    def test_all_urgency_levels_present(self):
        """All expected urgency levels are defined."""
        expected_levels = [
            "low",
            "normal",
            "high",
            "critical",
        ]
        
        for level in expected_levels:
            self.assertIn(level, [u.value for u in UrgencyLevel])


class TestHandoffStatusEnum(TestCase):
    """Test handoff status enum values."""
    
    def test_all_statuses_present(self):
        """All expected statuses are defined."""
        expected_statuses = [
            "pending",
            "awaiting_review",
            "reviewed",
            "approved",
            "denied",
            "escalated",
            "timeout",
            "cancelled",
        ]
        
        for status in expected_statuses:
            self.assertIn(status, [s.value for s in HandoffStatus])


class TestHandoffPackage(TestCase):
    """Test HandoffPackage data class."""
    
    def test_package_creation(self):
        """Package creation works correctly."""
        package = HandoffPackage(
            package_id="test-package-123",
            context_id="test-context-456",
            capability="execute",
            action="system_command",
            reason="System command requires approval",
            risk_level=0.8,
            confidence=0.3,
            recommended_action="Review by operations specialist",
        )
        
        self.assertEqual(package.package_id, "test-package-123")
        self.assertEqual(package.context_id, "test-context-456")
        self.assertEqual(package.capability, "execute")
        self.assertEqual(package.risk_level, 0.8)
        self.assertEqual(package.confidence, 0.3)
        self.assertEqual(package.recommended_action, "Review by operations specialist")
    
    def test_package_with_options(self):
        """Package creation with options works."""
        package = HandoffPackage(
            package_id="test-package-789",
            context_id="test-context-012",
            options=["approve", "deny", "modify"],
            alternative_actions=["defer", "fallback"],
        )
        
        self.assertEqual(len(package.options), 3)
        self.assertIn("approve", package.options)
        self.assertEqual(len(package.alternative_actions), 2)
    
    def test_to_dict(self):
        """Package to_dict conversion works."""
        package = HandoffPackage(
            package_id="test-package",
            context_id="test-context",
            risk_level=0.5,
        )
        
        result = package.to_dict()
        
        self.assertEqual(result["package_id"], "test-package")
        self.assertEqual(result["context_id"], "test-context")
        self.assertEqual(result["risk_level"], 0.5)
        self.assertIn("created_at", result)
    
    def test_from_dict(self):
        """Package from_dict reconstruction works."""
        original = HandoffPackage(
            package_id="test-package",
            context_id="test-context",
            risk_level=0.7,
            confidence=0.2,
        )
        
        data = original.to_dict()
        recreated = HandoffPackage.from_dict(data)
        
        self.assertEqual(recreated.package_id, original.package_id)
        self.assertEqual(recreated.context_id, original.context_id)
        self.assertEqual(recreated.risk_level, original.risk_level)


class TestEscalationRequest(TestCase):
    """Test EscalationRequest data class."""
    
    def test_request_creation(self):
        """Request creation works correctly."""
        request = EscalationRequest(
            escalation_id="test-escalation-123",
            trigger=EscalationTrigger.BLOCKED_BY_CAPABILITY.value,
            reason=EscalationReason.CAPABILITY_PROHIBITED.value,
            required_role=RequiredHumanRole.OPERATIONS_SPECIALIST.value,
            urgency=UrgencyLevel.HIGH.value,
            context_id="test-context",
        )
        
        self.assertEqual(request.escalation_id, "test-escalation-123")
        self.assertEqual(request.trigger, EscalationTrigger.BLOCKED_BY_CAPABILITY.value)
        self.assertEqual(request.required_role, RequiredHumanRole.OPERATIONS_SPECIALIST.value)
        self.assertEqual(request.urgency, UrgencyLevel.HIGH.value)
        self.assertEqual(request.context_id, "test-context")
    
    def test_request_update(self):
        """Request update refreshes timestamp."""
        request = EscalationRequest(
            escalation_id="test-escalation",
            trigger=EscalationTrigger.BLOCKED_BY_CAPABILITY.value,
            reason=EscalationReason.CAPABILITY_PROHIBITED.value,
        )
        
        original_timestamp = request.updated_at
        updated = request.update(risk_level=0.8)
        
        # Note: EscalationRequest doesn't have risk_level as a direct attribute
        # It stores it in handoff_package, but that's optional
        self.assertEqual(updated.trigger, EscalationTrigger.BLOCKED_BY_CAPABILITY.value)
        self.assertNotEqual(updated.updated_at, original_timestamp)
    
    def test_set_status(self):
        """Request set_status works correctly."""
        request = EscalationRequest(
            escalation_id="test-escalation",
            trigger=EscalationTrigger.BLOCKED_BY_CAPABILITY.value,
            reason=EscalationReason.CAPABILITY_PROHIBITED.value,
        )
        
        original_timestamp = request.updated_at
        updated = request.set_status(HandoffStatus.APPROVED.value)
        
        self.assertEqual(updated.status, HandoffStatus.APPROVED.value)
        self.assertNotEqual(updated.updated_at, original_timestamp)
    
    def test_to_dict(self):
        """Request to_dict conversion works."""
        request = EscalationRequest(
            escalation_id="test-escalation",
            trigger=EscalationTrigger.REQUIRES_APPROVAL.value,
            reason=EscalationReason.CAPABILITY_APPROVAL_NEEDED.value,
            timeout_ms=120000,
        )
        
        result = request.to_dict()
        
        self.assertEqual(result["escalation_id"], "test-escalation")
        self.assertEqual(result["trigger"], EscalationTrigger.REQUIRES_APPROVAL.value)
        self.assertEqual(result["timeout_ms"], 120000)
        self.assertIn("created_at", result)
        self.assertIn("updated_at", result)
    
    def test_from_dict(self):
        """Request from_dict reconstruction works."""
        original = EscalationRequest(
            escalation_id="test-escalation",
            trigger=EscalationTrigger.HIGH_RISK.value,
            reason=EscalationReason.SAFETY_THRESHOLD_EXCEEDED.value,
            required_role=RequiredHumanRole.SECURITY_SPECIALIST.value,
        )
        
        data = original.to_dict()
        recreated = EscalationRequest.from_dict(data)
        
        self.assertEqual(recreated.escalation_id, original.escalation_id)
        self.assertEqual(recreated.trigger, original.trigger)
        self.assertEqual(recreated.required_role, original.required_role)


class TestEscalationHumanRoles(TestCase):
    """Test get_escalation_human_roles function."""
    
    def test_registry_contains_all_roles(self):
        """Registry contains all predefined roles."""
        registry = get_escalation_human_roles()
        
        expected_roles = [
            RequiredHumanRole.OPERATOR.value,
            RequiredHumanRole.ADMINISTRATOR.value,
            RequiredHumanRole.DOMAIN_EXPERT.value,
            RequiredHumanRole.OPERATIONS_SPECIALIST.value,
            RequiredHumanRole.SECURITY_SPECIALIST.value,
            RequiredHumanRole.AUDITOR.value,
            RequiredHumanRole.EMERGENCY_CONTACT.value,
            RequiredHumanRole.LEGAL_REVIEWER.value,
            RequiredHumanRole.CUSTOMER.value,
            RequiredHumanRole.TECHNICAL_SUPPORT.value,
        ]
        
        for role in expected_roles:
            self.assertIn(role, registry)
    
    def test_registry_roles_have_expected_properties(self):
        """Registry roles have expected properties."""
        registry = get_escalation_human_roles()
        
        # Test operator role
        operator = registry[RequiredHumanRole.OPERATOR.value]
        self.assertEqual(operator["response_time_hours"], 24)
        self.assertIn("approval", operator["capabilities"])
        
        # Test emergency contact role
        emergency = registry[RequiredHumanRole.EMERGENCY_CONTACT.value]
        self.assertEqual(emergency["response_time_hours"], 1)
        self.assertIn("emergency_action", emergency["capabilities"])
        
        # Test legal reviewer role
        legal = registry[RequiredHumanRole.LEGAL_REVIEWER.value]
        self.assertEqual(legal["response_time_hours"], 168)
        self.assertIn("legal_review", legal["capabilities"])


class TestEscalationEngine(TestCase):
    """Test EscalationEngine class."""
    
    def test_engine_initialization(self):
        """Engine initialization works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            self.assertEqual(len(engine.escalations), 0)
            self.assertEqual(len(engine.handoffs), 0)
    
    def test_create_handoff(self):
        """Engine create_handoff works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            package = engine.create_handoff(
                context_id="test-context",
                capability="execute",
                action="system_command",
                reason="System command requires approval",
            )
            
            self.assertIsNotNone(package)
            self.assertIn("test-context", package.context_id)
            self.assertEqual(package.capability, "execute")
    
    def test_create_handoff_with_options(self):
        """Engine create_handoff with options works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            package = engine.create_handoff(
                context_id="test-context",
                capability="actuate",
                action="actuate",
                reason="Actuation requires approval",
                options=["approve", "deny"],
                alternative_actions=["defer", "fallback"],
                recommended_action="Deny and consult operations",
            )
            
            self.assertEqual(len(package.options), 2)
            self.assertIn("approve", package.options)
            self.assertEqual(len(package.alternative_actions), 2)
            self.assertEqual(package.recommended_action, "Deny and consult operations")
    
    def test_create_escalation(self):
        """Engine create_escalation works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            escalation = engine.create_escalation(
                trigger=EscalationTrigger.REQUIRES_APPROVAL.value,
                reason=EscalationReason.CAPABILITY_APPROVAL_NEEDED.value,
                required_role=RequiredHumanRole.ADMINISTRATOR.value,
                urgency=UrgencyLevel.HIGH.value,
                context_id="test-context",
            )
            
            self.assertIsNotNone(escalation)
            self.assertEqual(escalation.trigger, EscalationTrigger.REQUIRES_APPROVAL.value)
            self.assertEqual(escalation.required_role, RequiredHumanRole.ADMINISTRATOR.value)
    
    def test_create_escalation_with_handoff(self):
        """Engine create_escalation with handoff package works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            handoff = engine.create_handoff(
                context_id="test-context",
                capability="execute",
                action="system_command",
                reason="System command blocked",
            )
            
            escalation = engine.create_escalation(
                trigger=EscalationTrigger.BLOCKED_BY_CAPABILITY.value,
                reason=EscalationReason.CAPABILITY_PROHIBITED.value,
                handoff_package_id=handoff.package_id,
            )
            
            self.assertIsNotNone(escalation.handoff_package)
            self.assertEqual(escalation.handoff_package["package_id"], handoff.package_id)
    
    def test_get_escalation(self):
        """Engine get_escalation works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            escalation = engine.create_escalation(
                trigger=EscalationTrigger.REQUIRES_APPROVAL.value,
                reason=EscalationReason.CAPABILITY_APPROVAL_NEEDED.value,
            )
            
            retrieved = engine.get_escalation(escalation.escalation_id)
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.escalation_id, escalation.escalation_id)
    
    def test_get_handoff(self):
        """Engine get_handoff works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            handoff = engine.create_handoff(
                context_id="test-context",
                capability="execute",
                action="system_command",
                reason="System command requires approval",
            )
            
            retrieved = engine.get_handoff(handoff.package_id)
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.package_id, handoff.package_id)
    
    def test_create_escalation_from_capability_check(self):
        """Engine create_escalation_from_capability_check works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            capability_check = {
                "permitted": False,
                "reason": "Capability prohibited: execute",
                "capability": "execute",
            }
            
            escalation = engine.create_escalation_from_capability_check(
                capability_check,
                context_id="test-context",
            )
            
            self.assertIsNotNone(escalation)
            self.assertEqual(escalation.trigger, EscalationTrigger.BLOCKED_BY_CAPABILITY.value)
            self.assertEqual(escalation.reason, EscalationReason.CAPABILITY_PROHIBITED.value)
    
    def test_create_escalation_from_capability_check_permitted(self):
        """Engine create_escalation_from_capability_check returns None for permitted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            capability_check = {
                "permitted": True,
                "reason": "Capability allowed",
            }
            
            escalation = engine.create_escalation_from_capability_check(
                capability_check,
                context_id="test-context",
            )
            
            self.assertIsNone(escalation)
    
    def test_create_escalation_from_capability_check_restricted(self):
        """Engine create_escalation_from_capability_check handles restricted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            capability_check = {
                "permitted": False,
                "reason": "Capability restricted: api_call",
                "capability": "api_call",
            }
            
            escalation = engine.create_escalation_from_capability_check(
                capability_check,
                context_id="test-context",
            )
            
            self.assertIsNotNone(escalation)
            self.assertEqual(escalation.trigger, EscalationTrigger.RESTRICTED_BY_CAPABILITY.value)
            self.assertEqual(escalation.reason, EscalationReason.CAPABILITY_RESTRICTED.value)
    
    def test_create_escalation_from_capability_check_approval_needed(self):
        """Engine create_escalation_from_capability_check handles approval needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            capability_check = {
                "permitted": False,
                "reason": "Capability requires approval: autonomous",
                "capability": "autonomous",
                "requires_approval": True,
            }
            
            escalation = engine.create_escalation_from_capability_check(
                capability_check,
                context_id="test-context",
            )
            
            self.assertIsNotNone(escalation)
            self.assertEqual(escalation.trigger, EscalationTrigger.REQUIRES_APPROVAL.value)
            self.assertEqual(escalation.reason, EscalationReason.CAPABILITY_APPROVAL_NEEDED.value)
    
    def test_approve_escalation(self):
        """Engine approve_escalation works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            handoff = engine.create_handoff(
                context_id="test-context",
                capability="execute",
                action="system_command",
                reason="System command requires approval",
            )
            
            escalation = engine.create_escalation(
                trigger=EscalationTrigger.REQUIRES_APPROVAL.value,
                reason=EscalationReason.CAPABILITY_APPROVAL_NEEDED.value,
                handoff_package_id=handoff.package_id,
            )
            
            approved = engine.approve_escalation(
                escalation.escalation_id,
                approved_by="test_operator",
                notes="Approved by operator after review",
            )
            
            self.assertEqual(approved.status, HandoffStatus.APPROVED.value)
            self.assertIn("approved_notes", approved.handoff_package)
    
    def test_deny_escalation(self):
        """Engine deny_escalation works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            handoff = engine.create_handoff(
                context_id="test-context",
                capability="execute",
                action="system_command",
                reason="System command requires approval",
            )
            
            escalation = engine.create_escalation(
                trigger=EscalationTrigger.REQUIRES_APPROVAL.value,
                reason=EscalationReason.CAPABILITY_APPROVAL_NEEDED.value,
                handoff_package_id=handoff.package_id,
            )
            
            denied = engine.deny_escalation(
                escalation.escalation_id,
                denied_by="test_operator",
                notes="Denied due to safety concerns",
            )
            
            self.assertEqual(denied.status, HandoffStatus.DENIED.value)
            self.assertIn("denied_notes", denied.handoff_package)
    
    def test_get_pending_escalations(self):
        """Engine get_pending_escalations works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            # Create pending escalation
            pending = engine.create_escalation(
                trigger=EscalationTrigger.REQUIRES_APPROVAL.value,
                reason=EscalationReason.CAPABILITY_APPROVAL_NEEDED.value,
            )
            
            # Create approved escalation
            approved = engine.create_escalation(
                trigger=EscalationTrigger.REQUIRES_APPROVAL.value,
                reason=EscalationReason.CAPABILITY_APPROVAL_NEEDED.value,
            )
            engine.approve_escalation(approved.escalation_id, "test_operator")
            
            pending_list = engine.get_pending_escalations()
            
            self.assertEqual(len(pending_list), 1)
            self.assertEqual(pending_list[0].escalation_id, pending.escalation_id)
    
    def test_to_dict(self):
        """Engine to_dict conversion works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            escalation = engine.create_escalation(
                trigger=EscalationTrigger.REQUIRES_APPROVAL.value,
                reason=EscalationReason.CAPABILITY_APPROVAL_NEEDED.value,
            )
            
            result = engine.to_dict()
            
            self.assertEqual(result["escalation_count"], 1)
            self.assertEqual(result["handoff_count"], 0)
            self.assertEqual(result["pending_count"], 1)
            self.assertIn("escalations", result)
            self.assertIn("handoffs", result)


class TestIntegrationHooks(TestCase):
    """Test integration hook functions."""
    
    def test_integrate_with_capability_boundary(self):
        """integrate_with_capability_boundary adds escalation context."""
        capability_dict = {"permitted": False, "reason": "test"}
        
        result = integrate_with_capability_boundary(capability_dict)
        
        self.assertIn("escalation_context", result)
        self.assertIsNone(result["escalation_context"])
    
    def test_integrate_with_capability_boundary_with_engine(self):
        """integrate_with_capability_boundary works with escalation engine."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            engine.create_escalation(
                trigger=EscalationTrigger.REQUIRES_APPROVAL.value,
                reason=EscalationReason.CAPABILITY_APPROVAL_NEEDED.value,
            )
            
            capability_dict = {"permitted": False}
            
            result = integrate_with_capability_boundary(
                capability_dict,
                escalation_engine=engine,
                context_id="test-context",
            )
            
            self.assertIn("escalation_context", result)
            self.assertIsNotNone(result["escalation_context"])
            self.assertTrue(result["escalation_context"]["requires_review"])
    
    def test_integrate_with_safety_contract(self):
        """integrate_with_safety_contract adds escalation context."""
        safety_dict = {"safety_level": "high"}
        
        result = integrate_with_safety_contract(safety_dict)
        
        self.assertIn("escalation_context", result)
        self.assertIsNone(result["escalation_context"])
    
    def test_integrate_with_safety_contract_with_engine(self):
        """integrate_with_safety_contract works with escalation engine."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            engine.create_escalation(
                trigger=EscalationTrigger.HIGH_RISK.value,
                reason=EscalationReason.SAFETY_THRESHOLD_EXCEEDED.value,
            )
            
            safety_dict = {"safety_level": "high"}
            
            result = integrate_with_safety_contract(
                safety_dict,
                escalation_engine=engine,
                context_id="test-context",
            )
            
            self.assertIn("escalation_context", result)
            self.assertIsNotNone(result["escalation_context"])
            self.assertTrue(result["escalation_context"]["requires_human_review"])
    
    def test_integrate_with_proof_gate(self):
        """integrate_with_proof_gate adds escalation context."""
        proof_dict = {"execution_eligible": False}
        
        result = integrate_with_proof_gate(proof_dict)
        
        self.assertIn("escalation_context", result)
        self.assertIsNone(result["escalation_context"])
    
    def test_integrate_with_governance_surface(self):
        """integrate_with_governance_surface adds escalation context."""
        governance_dict = {"approval_required": False}
        
        result = integrate_with_governance_surface(governance_dict)
        
        self.assertIn("escalation_context", result)
        self.assertIsNone(result["escalation_context"])


class TestEscalationFlow(TestCase):
    """Test complete escalation flow."""
    
    def test_complete_escalation_flow(self):
        """Complete escalation flow works end-to-end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            # Step 1: Check capability and get result
            capability_check = {
                "permitted": False,
                "reason": "Capability prohibited: execute",
                "capability": "execute",
            }
            
            # Step 2: Create escalation from capability check
            escalation = engine.create_escalation_from_capability_check(
                capability_check,
                context_id="test-context",
            )
            
            self.assertIsNotNone(escalation)
            self.assertEqual(escalation.status, HandoffStatus.PENDING.value)
            
            # Step 3: Get pending escalations
            pending = engine.get_pending_escalations()
            self.assertEqual(len(pending), 1)
            
            # Step 4: Approve escalation
            approved = engine.approve_escalation(
                escalation.escalation_id,
                approved_by="test_operator",
                notes="Approved after safety review",
            )
            
            self.assertEqual(approved.status, HandoffStatus.APPROVED.value)
    
    def test_escalation_denial_flow(self):
        """Escalation denial flow works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            capability_check = {
                "permitted": False,
                "reason": "Capability restricted: api_call",
                "capability": "api_call",
            }
            
            escalation = engine.create_escalation_from_capability_check(
                capability_check,
                context_id="test-context",
            )
            
            # Deny escalation
            denied = engine.deny_escalation(
                escalation.escalation_id,
                denied_by="test_operator",
                notes="Deny: API calls restricted in this context",
            )
            
            self.assertEqual(denied.status, HandoffStatus.DENIED.value)


class TestBackwardCompatibility(TestCase):
    """Test backward compatibility with existing code."""
    
    def test_existing_code_works_without_escalation_context(self):
        """Existing code works when escalation context not provided."""
        # Integration hooks should work without escalation engine
        capability_result = integrate_with_capability_boundary({"test": "data"})
        self.assertEqual(capability_result["test"], "data")
        
        safety_result = integrate_with_safety_contract({"test": "data"})
        self.assertEqual(safety_result["test"], "data")
        
        proof_result = integrate_with_proof_gate({"test": "data"})
        self.assertEqual(proof_result["test"], "data")
    
    def test_engine_without_context(self):
        """Engine works without context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            # Create escalation without context
            escalation = engine.create_escalation(
                trigger=EscalationTrigger.OTHER.value,
                reason=EscalationReason.UNKNOWN.value,
            )
            
            self.assertIsNotNone(escalation)
            self.assertIsNone(escalation.context_id)
    
    def test_handoff_without_package(self):
        """Engine create_escalation without handoff package works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            
            escalation = engine.create_escalation(
                trigger=EscalationTrigger.HIGH_RISK.value,
                reason=EscalationReason.SAFETY_THRESHOLD_EXCEEDED.value,
            )
            
            self.assertIsNotNone(escalation)
            self.assertIsNone(escalation.handoff_package)


class TestSerialization(TestCase):
    """Test serialization and deserialization."""
    
    def test_handoff_serialization(self):
        """Handoff package serialization round-trip works."""
        original = HandoffPackage(
            package_id="serial-test",
            context_id="test-context",
            capability="execute",
            risk_level=0.8,
        )
        
        data = original.to_dict()
        recreated = HandoffPackage.from_dict(data)
        
        self.assertEqual(original.package_id, recreated.package_id)
        self.assertEqual(original.context_id, recreated.context_id)
        self.assertEqual(original.capability, recreated.capability)
    
    def test_escalation_serialization(self):
        """Escalation request serialization round-trip works."""
        original = EscalationRequest(
            escalation_id="serial-test",
            trigger=EscalationTrigger.REQUIRES_APPROVAL.value,
            reason=EscalationReason.CAPABILITY_APPROVAL_NEEDED.value,
            timeout_ms=120000,
        )
        
        data = original.to_dict()
        recreated = EscalationRequest.from_dict(data)
        
        self.assertEqual(original.escalation_id, recreated.escalation_id)
        self.assertEqual(original.trigger, recreated.trigger)
        self.assertEqual(original.timeout_ms, recreated.timeout_ms)


class TestIntegrationWithExistingLayers(TestCase):
    """Test integration with existing WESLR layers."""
    
    def test_integration_with_safety_contract(self):
        """Integration with safety contract works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            engine.create_escalation(
                trigger=EscalationTrigger.HIGH_RISK.value,
                reason=EscalationReason.SAFETY_THRESHOLD_EXCEEDED.value,
            )
            
            # Simulate safety contract usage pattern
            safety_dict = {
                "safety_level": "high",
                "action_type": "execute",
            }
            
            result = integrate_with_safety_contract(
                safety_dict,
                escalation_engine=engine,
                context_id="safety-test",
            )
            
            self.assertIn("escalation_context", result)
            self.assertIsNotNone(result["escalation_context"])
    
    def test_integration_with_governance_surface(self):
        """Integration with governance surface works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = EscalationEngine(storage_path=tmpdir)
            engine.create_escalation(
                trigger=EscalationTrigger.REQUIRES_APPROVAL.value,
                reason=EscalationReason.CAPABILITY_APPROVAL_NEEDED.value,
            )
            
            governance_dict = {
                "approval_required": False,
            }
            
            result = integrate_with_governance_surface(
                governance_dict,
                escalation_engine=engine,
                context_id="governance-test",
            )
            
            self.assertIn("escalation_context", result)
            self.assertIsNotNone(result["escalation_context"])


if __name__ == "__main__":
    import unittest
    unittest.main()
