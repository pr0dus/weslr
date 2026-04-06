"""Tests for External Action Safety Contract Layer (v23)

Tests safety_contract.py data models, registry, engine, and integration hooks.
"""

from __future__ import annotations

import unittest

from weslr.safety_contract import (
    ActionType,
    SafetyLevel,
    ApprovalRequirement,
    ExecutionPermission,
    SafetyRequirement,
    SafetyContract,
    get_safety_contract_registry,
    SafetyEngine,
    integrate_with_change_proposal,
    integrate_with_governance_view,
    integrate_with_proposal_realization,
    integrate_with_proof_gate,
)


class TestSafetyContractModels(unittest.TestCase):
    """Test safety contract data models."""

    def test_action_type_enum(self):
        """Test ActionType enum values."""
        self.assertEqual(ActionType.READ_DATA.value, "read_data")
        self.assertEqual(ActionType.READ_FILES.value, "read_files")
        self.assertEqual(ActionType.READ_MEMORY.value, "read_memory")
        self.assertEqual(ActionType.ANALYZE.value, "analyze")
        self.assertEqual(ActionType.CONFIGURE.value, "configure")
        self.assertEqual(ActionType.UPDATE_CONFIG.value, "update_config")
        self.assertEqual(ActionType.API_CALL.value, "api_call")
        self.assertEqual(ActionType.HTTP_REQUEST.value, "http_request")
        self.assertEqual(ActionType.DATABASE_WRITE.value, "database_write")
        self.assertEqual(ActionType.FILE_WRITE.value, "file_write")
        self.assertEqual(ActionType.SYSTEM_COMMAND.value, "system_command")
        self.assertEqual(ActionType.ACTUATE.value, "actuate")
        self.assertEqual(ActionType.EXECUTE.value, "execute")
        self.assertEqual(ActionType.AUTONOMOUS.value, "autonomous")
        self.assertEqual(ActionType.OTHER.value, "other")

    def test_safety_level_enum(self):
        """Test SafetyLevel enum values."""
        self.assertEqual(SafetyLevel.INFORMATIONAL.value, "informational")
        self.assertEqual(SafetyLevel.LOW.value, "low")
        self.assertEqual(SafetyLevel.MEDIUM.value, "medium")
        self.assertEqual(SafetyLevel.HIGH.value, "high")
        self.assertEqual(SafetyLevel.CRITICAL.value, "critical")

    def test_approval_requirement_enum(self):
        """Test ApprovalRequirement enum values."""
        self.assertEqual(ApprovalRequirement.NONE.value, "none")
        self.assertEqual(ApprovalRequirement.REVIEW.value, "review")
        self.assertEqual(ApprovalRequirement.APPROVAL.value, "approval")
        self.assertEqual(ApprovalRequirement.MULTI_STAGED.value, "multi_staged")
        self.assertEqual(ApprovalRequirement.AUDIT_ONLY.value, "audit_only")

    def test_execution_permission_enum(self):
        """Test ExecutionPermission enum values."""
        self.assertEqual(ExecutionPermission.PERMITTED.value, "permitted")
        self.assertEqual(ExecutionPermission.BLOCKED.value, "blocked")
        self.assertEqual(ExecutionPermission.OFFLINE_BLOCKED.value, "offline_blocked")
        self.assertEqual(ExecutionPermission.INSUFFICIENT_EVIDENCE.value, "insufficient_evidence")
        self.assertEqual(ExecutionPermission.DOMAIN_PROHIBITED.value, "domain_prohibited")
        self.assertEqual(ExecutionPermission.PROOF_REQUIRED.value, "proof_required")

    def test_create_safety_requirement(self):
        """Test creating a safety requirement."""
        req = SafetyRequirement(
            action_type=ActionType.SYSTEM_COMMAND.value,
            safety_level=SafetyLevel.HIGH.value,
            approval_requirement=ApprovalRequirement.MULTI_STAGED.value,
            min_evidence_confidence=0.7,
            requires_rollback=True,
            requires_audit=True,
            requires_domain_context=True,
        )
        
        self.assertEqual(req.action_type, ActionType.SYSTEM_COMMAND.value)
        self.assertEqual(req.safety_level, SafetyLevel.HIGH.value)
        self.assertEqual(req.approval_requirement, ApprovalRequirement.MULTI_STAGED.value)
        self.assertEqual(req.min_evidence_confidence, 0.7)
        self.assertTrue(req.requires_rollback)
        self.assertTrue(req.requires_audit)
        self.assertTrue(req.requires_domain_context)

    def test_create_safety_contract(self):
        """Test creating a safety contract."""
        contract = SafetyContract(
            action_type=ActionType.API_CALL.value,
            safety_level=SafetyLevel.MEDIUM.value,
            approval_requirement=ApprovalRequirement.APPROVAL.value,
            min_evidence_confidence=0.6,
        )
        
        self.assertEqual(contract.action_type, ActionType.API_CALL.value)
        self.assertEqual(contract.safety_level, SafetyLevel.MEDIUM.value)
        self.assertEqual(contract.approval_requirement, ApprovalRequirement.APPROVAL.value)
        # SafetyContract created directly is permitted by default (no assessment done)
        self.assertTrue(contract.is_permitted())
        self.assertFalse(contract.is_blocked())
        self.assertEqual(contract.execution_permission, ExecutionPermission.PERMITTED.value)

    def test_safety_contract_to_dict(self):
        """Test safety contract serialization."""
        contract = SafetyContract(
            action_type=ActionType.CONFIGURE.value,
            safety_level=SafetyLevel.LOW.value,
            approval_requirement=ApprovalRequirement.REVIEW.value,
        )
        
        contract_dict = contract.to_dict()
        self.assertEqual(contract_dict["action_type"], ActionType.CONFIGURE.value)
        self.assertEqual(contract_dict["safety_level"], SafetyLevel.LOW.value)
        self.assertEqual(contract_dict["approval_requirement"], ApprovalRequirement.REVIEW.value)

    def test_safety_contract_from_dict(self):
        """Test safety contract deserialization."""
        contract = SafetyContract(
            action_type=ActionType.READ_DATA.value,
            safety_level=SafetyLevel.INFORMATIONAL.value,
            approval_requirement=ApprovalRequirement.NONE.value,
        )
        
        contract_dict = contract.to_dict()
        contract2 = SafetyContract.from_dict(contract_dict)
        
        self.assertEqual(contract.action_type, contract2.action_type)
        self.assertEqual(contract.safety_level, contract2.safety_level)

    def test_safety_contract_add_blocked_reason(self):
        """Test adding blocked reasons."""
        contract = SafetyContract(
            action_type=ActionType.API_CALL.value,
            safety_level=SafetyLevel.MEDIUM.value,
            approval_requirement=ApprovalRequirement.APPROVAL.value,
        )
        
        contract.add_blocked_reason("Network unavailable")
        contract.add_blocked_reason("Insufficient evidence")
        
        self.assertIn("Network unavailable", contract.blocked_reasons)
        self.assertIn("Insufficient evidence", contract.blocked_reasons)

    def test_safety_contract_set_permission(self):
        """Test setting execution permission."""
        contract = SafetyContract(
            action_type=ActionType.SYSTEM_COMMAND.value,
            safety_level=SafetyLevel.HIGH.value,
            approval_requirement=ApprovalRequirement.MULTI_STAGED.value,
        )
        
        contract.set_permission(ExecutionPermission.OFFLINE_BLOCKED.value, "Offline mode")
        
        self.assertEqual(contract.execution_permission, ExecutionPermission.OFFLINE_BLOCKED.value)
        self.assertIn("Offline mode", contract.blocked_reasons)
        self.assertFalse(contract.is_permitted())
        self.assertTrue(contract.is_blocked())


class TestSafetyContractRegistry(unittest.TestCase):
    """Test safety contract registry."""

    def test_get_safety_contract_registry(self):
        """Test that registry returns standard action types."""
        registry = get_safety_contract_registry()
        
        self.assertIn(ActionType.READ_DATA.value, registry)
        self.assertIn(ActionType.READ_FILES.value, registry)
        self.assertIn(ActionType.READ_MEMORY.value, registry)
        self.assertIn(ActionType.ANALYZE.value, registry)
        self.assertIn(ActionType.CONFIGURE.value, registry)
        self.assertIn(ActionType.API_CALL.value, registry)
        self.assertIn(ActionType.HTTP_REQUEST.value, registry)
        self.assertIn(ActionType.FILE_WRITE.value, registry)
        self.assertIn(ActionType.SYSTEM_COMMAND.value, registry)
        self.assertIn(ActionType.AUTONOMOUS.value, registry)

    def test_registry_action_types(self):
        """Test registry action type configurations."""
        registry = get_safety_contract_registry()
        
        # Informational actions should have no approval requirement
        info_req = registry[ActionType.READ_DATA.value]
        self.assertEqual(info_req.approval_requirement, ApprovalRequirement.NONE.value)
        self.assertEqual(info_req.safety_level, SafetyLevel.INFORMATIONAL.value)
        
        # Configuration changes should require review
        config_req = registry[ActionType.CONFIGURE.value]
        self.assertEqual(config_req.approval_requirement, ApprovalRequirement.REVIEW.value)
        self.assertEqual(config_req.safety_level, SafetyLevel.LOW.value)
        self.assertTrue(config_req.requires_rollback)
        self.assertTrue(config_req.requires_audit)
        
        # API calls should require approval
        api_req = registry[ActionType.API_CALL.value]
        self.assertEqual(api_req.approval_requirement, ApprovalRequirement.APPROVAL.value)
        self.assertEqual(api_req.safety_level, SafetyLevel.MEDIUM.value)
        self.assertTrue(api_req.requires_rollback)
        self.assertTrue(api_req.requires_audit)
        
        # System commands should be critical
        sys_req = registry[ActionType.SYSTEM_COMMAND.value]
        self.assertEqual(sys_req.approval_requirement, ApprovalRequirement.MULTI_STAGED.value)
        self.assertEqual(sys_req.safety_level, SafetyLevel.CRITICAL.value)
        self.assertTrue(sys_req.requires_rollback)
        self.assertTrue(sys_req.requires_audit)
        self.assertEqual(len(sys_req.requires_proof), 3)
        self.assertIn("validation", sys_req.requires_proof)
        self.assertIn("rollback_coverage", sys_req.requires_proof)
        self.assertIn("impact_analysis", sys_req.requires_proof)
        
        # Autonomous actions should be critical
        auto_req = registry[ActionType.AUTONOMOUS.value]
        self.assertEqual(auto_req.approval_requirement, ApprovalRequirement.MULTI_STAGED.value)
        self.assertEqual(auto_req.safety_level, SafetyLevel.CRITICAL.value)


class TestSafetyEngine(unittest.TestCase):
    """Test safety engine."""

    def test_assess_informational_action(self):
        """Test assessing an informational action."""
        engine = SafetyEngine()
        contract = engine.assess(ActionType.READ_DATA.value)
        
        self.assertEqual(contract.action_type, ActionType.READ_DATA.value)
        self.assertEqual(contract.safety_level, SafetyLevel.INFORMATIONAL.value)
        self.assertEqual(contract.approval_requirement, ApprovalRequirement.NONE.value)
        self.assertTrue(contract.is_permitted())
        self.assertEqual(contract.execution_permission, ExecutionPermission.PERMITTED.value)

    def test_assess_api_call(self):
        """Test assessing an API call action."""
        engine = SafetyEngine()
        contract = engine.assess(ActionType.API_CALL.value, evidence_confidence=0.7, domain_context="home")
        
        self.assertEqual(contract.action_type, ActionType.API_CALL.value)
        self.assertEqual(contract.safety_level, SafetyLevel.MEDIUM.value)
        self.assertEqual(contract.approval_requirement, ApprovalRequirement.APPROVAL.value)
        self.assertTrue(contract.is_permitted())
        self.assertEqual(contract.execution_permission, ExecutionPermission.PERMITTED.value)

    def test_assess_insufficient_evidence(self):
        """Test assessing with insufficient evidence."""
        engine = SafetyEngine()
        contract = engine.assess(ActionType.API_CALL.value, evidence_confidence=0.3, domain_context="home")
        
        self.assertFalse(contract.is_permitted())
        self.assertEqual(contract.execution_permission, ExecutionPermission.INSUFFICIENT_EVIDENCE.value)
        self.assertIn("Evidence confidence", " ".join(contract.blocked_reasons))

    def test_assess_offline_mode(self):
        """Test assessing in offline mode."""
        engine = SafetyEngine()
        contract = engine.assess(ActionType.API_CALL.value, evidence_confidence=0.7, domain_context="home", is_offline=True)
        
        self.assertFalse(contract.is_permitted())
        self.assertEqual(contract.execution_permission, ExecutionPermission.OFFLINE_BLOCKED.value)
        self.assertIn("External action blocked", " ".join(contract.blocked_reasons))

    def test_assess_system_command(self):
        """Test assessing a system command."""
        engine = SafetyEngine()
        contract = engine.assess(ActionType.SYSTEM_COMMAND.value, evidence_confidence=0.85)
        
        self.assertEqual(contract.action_type, ActionType.SYSTEM_COMMAND.value)
        self.assertEqual(contract.safety_level, SafetyLevel.CRITICAL.value)
        self.assertEqual(contract.approval_requirement, ApprovalRequirement.MULTI_STAGED.value)
        self.assertTrue(contract.requires_rollback)
        self.assertTrue(contract.requires_audit)
        self.assertEqual(contract.min_evidence_confidence, 0.85)

    def test_get_contract_summary(self):
        """Test getting contract summary."""
        engine = SafetyEngine()
        # API_CALL requires domain_context, so provide it for permitted status
        contract = engine.assess(ActionType.API_CALL.value, evidence_confidence=0.7, domain_context="home")
        
        summary = engine.get_contract_summary(contract)
        
        self.assertEqual(summary["action_type"], ActionType.API_CALL.value)
        self.assertEqual(summary["safety_level"], SafetyLevel.MEDIUM.value)
        self.assertEqual(summary["approval_requirement"], ApprovalRequirement.APPROVAL.value)
        self.assertEqual(summary["evidence_required"], 0.6)
        self.assertTrue(summary["requires_rollback"])
        self.assertTrue(summary["requires_audit"])
        self.assertEqual(summary["execution_permission"], ExecutionPermission.PERMITTED.value)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for proposals, governance, and proof gates."""

    def test_integrate_with_change_proposal_adds_safety_fields(self):
        """Test that integration adds safety fields to change proposal."""
        proposal_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
        }
        
        result = integrate_with_change_proposal(proposal_dict)
        
        self.assertIn("action_type", result)
        self.assertIn("safety_contract", result)
        self.assertIn("safety_contract_summary", result)
        self.assertIsNone(result["action_type"])
        self.assertIsNone(result["safety_contract"])
        self.assertIsNone(result["safety_contract_summary"])

    def test_integrate_with_change_proposal_preserves_existing(self):
        """Test that integration preserves existing safety fields."""
        proposal_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
            "action_type": "api_call",
            "safety_contract": {"action_type": "api_call"},
        }
        
        result = integrate_with_change_proposal(proposal_dict)
        
        self.assertEqual(result["action_type"], "api_call")
        self.assertEqual(result["safety_contract"], {"action_type": "api_call"})

    def test_integrate_with_governance_view_adds_safety_fields(self):
        """Test that integration adds safety fields to governance view."""
        governance_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertIn("action_type", result)
        self.assertIn("safety_contract", result)
        self.assertIn("safety_status", result)
        self.assertIn("safety_blocked", result)
        self.assertIsNone(result["action_type"])
        self.assertIsNone(result["safety_contract"])
        self.assertIsNone(result["safety_status"])
        self.assertFalse(result["safety_blocked"])

    def test_integrate_with_governance_view_preserves_existing(self):
        """Test that integration preserves existing safety fields."""
        governance_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
            "action_type": "system_command",
            "safety_contract": {"action_type": "system_command"},
            "safety_blocked": True,
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertEqual(result["action_type"], "system_command")
        self.assertEqual(result["safety_contract"], {"action_type": "system_command"})
        self.assertTrue(result["safety_blocked"])

    def test_integrate_with_proposal_realization_adds_safety_fields(self):
        """Test that integration adds safety fields to proposal realization."""
        realization_dict = {
            "plan_id": "plan-001",
            "proposal_id": "prop-001",
        }
        
        result = integrate_with_proposal_realization(realization_dict)
        
        self.assertIn("action_type", result)
        self.assertIn("safety_contract", result)
        self.assertIn("safety_approved", result)
        self.assertIn("safety_blocked_reasons", result)
        self.assertIsNone(result["action_type"])
        self.assertIsNone(result["safety_contract"])
        self.assertFalse(result["safety_approved"])
        self.assertEqual(result["safety_blocked_reasons"], [])

    def test_integrate_with_proposal_realization_preserves_existing(self):
        """Test that integration preserves existing safety fields."""
        realization_dict = {
            "plan_id": "plan-001",
            "proposal_id": "prop-001",
            "action_type": "http_request",
            "safety_approved": True,
        }
        
        result = integrate_with_proposal_realization(realization_dict)
        
        self.assertEqual(result["action_type"], "http_request")
        self.assertTrue(result["safety_approved"])

    def test_integrate_with_proof_gate_adds_safety_fields(self):
        """Test that integration adds safety fields to proof gate."""
        proof_dict = {
            "plan_id": "plan-001",
            "proposal_id": "prop-001",
        }
        
        result = integrate_with_proof_gate(proof_dict)
        
        self.assertIn("safety_approved", result)
        self.assertIn("safety_blocked", result)
        self.assertIn("safety_blocked_reasons", result)
        self.assertFalse(result["safety_approved"])
        self.assertFalse(result["safety_blocked"])
        self.assertEqual(result["safety_blocked_reasons"], [])

    def test_integrate_with_proof_gate_preserves_existing(self):
        """Test that integration preserves existing safety fields."""
        proof_dict = {
            "plan_id": "plan-001",
            "proposal_id": "prop-001",
            "safety_approved": True,
            "safety_blocked": True,
        }
        
        result = integrate_with_proof_gate(proof_dict)
        
        self.assertTrue(result["safety_approved"])
        self.assertTrue(result["safety_blocked"])


if __name__ == "__main__":
    unittest.main()
