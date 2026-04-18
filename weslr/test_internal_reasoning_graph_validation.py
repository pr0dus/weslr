"""Tests for Internal Reasoning Graph Validation Engine

Test Doctrine v1
Test Doctrine version: 1.0.0 (2026-04-08)
"""

from __future__ import annotations

import time
import unittest

from weslr.internal_reasoning_graph.validation import (
    ProposalValidationEngine,
    ValidationCheckType,
    ValidationIssue,
    ValidationSeverity,
    ValidationResult,
    ValidationStatus,
)


class MockNode:
    """Mock node for testing."""
    def __init__(self, node_id, node_type="proposal", metadata=None, status="active", edges=None):
        self.id = node_id
        self.name = "Test Proposal"
        self.description = "Test proposal description"
        self.node_type = node_type
        self.metadata = metadata or {}
        self.status = status
        self.updated_at = int(time.time())
        self.edges = edges or []


class TestValidationEngineModel(unittest.TestCase):
    """Model tests for Validation Engine."""
    
    def test_validation_issue_serialization(self):
        """Test ValidationIssue serialization/deserialization."""
        issue = ValidationIssue(
            check_type=ValidationCheckType.FORMAT,
            severity=ValidationSeverity.ERROR,
            message="Missing required field",
            field="id",
            expected="non-empty string",
            actual=None,
        )
        
        serialized = issue.to_dict()
        self.assertEqual(serialized["check_type"], "format")
        self.assertEqual(serialized["severity"], "error")
        self.assertEqual(serialized["message"], "Missing required field")
        self.assertEqual(serialized["field"], "id")
        
        # Test from_dict
        restored = ValidationIssue.from_dict(serialized)
        self.assertEqual(restored.check_type, ValidationCheckType.FORMAT)
        self.assertEqual(restored.severity, ValidationSeverity.ERROR)
    
    def test_validation_result_serialization(self):
        """Test ValidationResult serialization/deserialization."""
        issues = [
            ValidationIssue(
                check_type=ValidationCheckType.FORMAT,
                severity=ValidationSeverity.ERROR,
                message="Missing required field",
            ),
        ]
        
        result = ValidationResult(
            status=ValidationStatus.INVALID.value,
            issues=issues,
            checked_at=1234567890,
        )
        
        serialized = result.to_dict()
        self.assertEqual(serialized["status"], "invalid")
        self.assertEqual(len(serialized["issues"]), 1)
        self.assertEqual(serialized["checked_at"], 1234567890)
        
        # Test from_dict
        restored = ValidationResult.from_dict(serialized)
        self.assertEqual(restored.status, "invalid")
        self.assertEqual(restored.checked_at, 1234567890)
    
    def test_validation_result_properties(self):
        """Test ValidationResult is_valid and is_invalid properties."""
        valid_result = ValidationResult(
            status=ValidationStatus.VALID.value,
            issues=[],
        )
        invalid_result = ValidationResult(
            status=ValidationStatus.INVALID.value,
            issues=[ValidationIssue(
                check_type=ValidationCheckType.FORMAT,
                severity=ValidationSeverity.ERROR,
                message="Error",
            )],
        )
        
        self.assertTrue(valid_result.is_valid)
        self.assertFalse(valid_result.is_invalid)
        self.assertFalse(invalid_result.is_valid)
        self.assertTrue(invalid_result.is_invalid)


class TestValidationEngineBehavior(unittest.TestCase):
    """Behavior tests for Validation Engine."""
    
    def setUp(self):
        self.engine = ProposalValidationEngine()
    
    def test_validate_proposal_format(self):
        """Test validating proposal format."""
        node = MockNode("proposal-1", metadata={"proposed_by": "operator-1"})
        node.metadata["required_governance"] = "operator_review"
        
        result = self.engine.validate_proposal(node, actor="system")
        
        self.assertEqual(result.status, ValidationStatus.VALID.value)
    
    def test_validate_proposal_missing_required_field(self):
        """Test validation fails when required field missing."""
        node = MockNode("proposal-1", metadata={})
        node.metadata["required_governance"] = "operator_review"
        
        # Set invalid node_type
        node.node_type = "invalid_type"
        
        result = self.engine.validate_proposal(node, actor="system")
        
        self.assertEqual(result.status, ValidationStatus.INVALID.value)
        
        # Check for format error
        format_issues = [i for i in result.issues if i.check_type == ValidationCheckType.FORMAT]
        self.assertGreater(len(format_issues), 0)
    
    def test_validate_proposal_scope_csharp(self):
        """Test validation fails for C# references."""
        node = MockNode("proposal-1", metadata={"proposed_by": "operator-1"})
        node.description = "This is C# code"
        
        result = self.engine.validate_proposal(node, actor="system")
        
        # C# reference should trigger scope error
        scope_issues = [i for i in result.issues if i.check_type == ValidationCheckType.SCOPE]
        csharp_issues = [i for i in scope_issues if "c#" in i.message.lower() or "c_sharp" in i.message.lower()]
        self.assertGreater(len(csharp_issues), 0)
    
    def test_validate_proposal_scope_tia(self):
        """Test validation fails for TIA references."""
        node = MockNode("proposal-1", metadata={"proposed_by": "operator-1"})
        node.description = "This is TIA integration"
        
        result = self.engine.validate_proposal(node, actor="system")
        
        # TIA reference should trigger scope error
        scope_issues = [i for i in result.issues if i.check_type == ValidationCheckType.SCOPE]
        tia_issues = [i for i in scope_issues if "tia" in i.message.lower()]
        self.assertGreater(len(tia_issues), 0)
    
    def test_validate_proposal_additive_deprecation(self):
        """Test validation warns for deprecation."""
        node = MockNode("proposal-1", metadata={"proposed_by": "operator-1"})
        node.status = "deprecated"
        
        result = self.engine.validate_proposal(node, actor="system")
        
        # Deprecation should trigger additive warning
        additive_issues = [i for i in result.issues if i.check_type == ValidationCheckType.ADDITIVE]
        self.assertGreater(len(additive_issues), 0)
    
    def test_validate_proposal_backward_compatibility_breaking_change(self):
        """Test validation errors for breaking change."""
        node = MockNode("proposal-1", metadata={"proposed_by": "operator-1"})
        node.metadata["breaking_change"] = True
        
        result = self.engine.validate_proposal(node, actor="system")
        
        # Breaking change should trigger backward compatibility error
        bc_issues = [i for i in result.issues if i.check_type == ValidationCheckType.BACKWARD_COMPATIBILITY]
        breaking_issues = [i for i in bc_issues if "breaking" in i.message.lower()]
        self.assertGreater(len(breaking_issues), 0)
    
    def test_get_validation_status(self):
        """Test getting validation status - read-only query."""
        node = MockNode("proposal-1", metadata={"proposed_by": "operator-1"})
        
        self.engine.validate_proposal(node, actor="system")
        
        status = self.engine.get_validation_status("proposal-1")
        self.assertEqual(status, ValidationStatus.VALID.value)
    
    def test_get_validation_issues(self):
        """Test getting validation issues - read-only query."""
        node = MockNode("proposal-1", node_type="invalid_type")
        
        self.engine.validate_proposal(node, actor="system")
        
        issues = self.engine.get_validation_issues("proposal-1")
        self.assertGreater(len(issues), 0)
    
    def test_export_validation_summary(self):
        """Test exporting validation summary - operator-readable + machine-readable."""
        node = MockNode("proposal-1", metadata={"proposed_by": "operator-1"})
        
        self.engine.validate_proposal(node, actor="system")
        
        summary = self.engine.export_validation_summary("proposal-1")
        
        self.assertIn("proposal_id", summary)
        self.assertIn("status", summary)
        self.assertIn("checked_at", summary)
        self.assertIn("issues", summary)
    
    def test_export_all_validations(self):
        """Test exporting all validations - operator-readable + machine-readable."""
        node1 = MockNode("proposal-1", metadata={"proposed_by": "operator-1"})
        node2 = MockNode("proposal-2", node_type="invalid_type")
        
        self.engine.validate_proposal(node1, actor="system")
        self.engine.validate_proposal(node2, actor="system")
        
        summary = self.engine.export_all_validations()
        
        self.assertIn("validations", summary)
        self.assertIn("total_count", summary)
        self.assertIn("valid_count", summary)
        self.assertIn("invalid_count", summary)
        self.assertEqual(summary["total_count"], 2)


class TestValidationEngineIntegration(unittest.TestCase):
    """Integration tests for Validation Engine."""
    
    def test_full_validation_lifecycle(self):
        """Test full validation lifecycle."""
        engine = ProposalValidationEngine()
        
        node = MockNode("proposal-1", metadata={"proposed_by": "operator-1"})
        
        # Validate
        result = engine.validate_proposal(node, actor="system")
        
        # Check status
        status = engine.get_validation_status("proposal-1")
        self.assertEqual(status, result.status)
        
        # Export
        summary = engine.export_validation_summary("proposal-1")
        self.assertEqual(summary["status"], result.status)
    
    def test_validation_state_reset(self):
        """Test validation state can be reset."""
        engine = ProposalValidationEngine()
        
        node1 = MockNode("proposal-1", metadata={"proposed_by": "operator-1"})
        node2 = MockNode("proposal-2", metadata={"proposed_by": "operator-2"})
        
        # Validate both
        engine.validate_proposal(node1, actor="system")
        engine.validate_proposal(node2, actor="system")
        
        # Check both exist
        self.assertEqual(len(engine._validation_results), 2)
        
        # Reset one
        engine.reset_validation("proposal-1")
        self.assertNotIn("proposal-1", engine._validation_results)
        
        # Reset all
        engine.reset_all()
        self.assertEqual(len(engine._validation_results), 0)


class TestValidationEngineBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for Validation Engine."""
    
    def test_old_result_serialization(self):
        """Test old result serialization format still works."""
        # Old format (missing checked_at)
        old_data = {
            "status": "valid",
            "issues": [],
        }
        
        restored = ValidationResult.from_dict(old_data)
        self.assertEqual(restored.status, "valid")
        self.assertEqual(len(restored.issues), 0)
    
    def test_issue_serialization_with_all_fields(self):
        """Test issue serialization with all fields."""
        issue = ValidationIssue(
            check_type=ValidationCheckType.SCOPE,
            severity=ValidationSeverity.WARNING,
            message="Scope issue",
            details={"field": "test"},
            field="test_field",
            expected="expected_value",
            actual="actual_value",
        )
        
        serialized = issue.to_dict()
        restored = ValidationIssue.from_dict(serialized)
        
        self.assertEqual(restored.check_type, ValidationCheckType.SCOPE)
        self.assertEqual(restored.details, {"field": "test"})
        self.assertEqual(restored.field, "test_field")


class TestValidationEngineBoundaryConditions(unittest.TestCase):
    """Boundary condition tests for Validation Engine."""
    
    def test_validate_proposal_with_no_metadata(self):
        """Test validation with minimal node."""
        node = MockNode("proposal-1")
        node.node_type = "proposal"
        
        result = self.engine = ProposalValidationEngine().validate_proposal(node, actor="system")
        
        # Should have at least format issues
        format_issues = [i for i in result.issues if i.check_type == ValidationCheckType.FORMAT]
        # proposal node type should trigger an issue since it's not in allowed list
        self.assertEqual(result.status, ValidationStatus.INVALID.value)
    
    def test_validate_proposal_with_valid_metadata(self):
        """Test validation with complete metadata."""
        node = MockNode("proposal-1")
        node.node_type = "proposal"
        node.metadata = {
            "proposed_by": "operator-1",
            "required_governance": "operator_review",
        }
        
        engine = ProposalValidationEngine()
        result = engine.validate_proposal(node, actor="system")
        
        # Should be valid
        self.assertEqual(result.status, ValidationStatus.VALID.value)
    
    def test_mark_validation_states(self):
        """Test marking validation states."""
        engine = ProposalValidationEngine()
        
        # Mark as pending
        engine.mark_pending("proposal-1")
        self.assertEqual(engine.get_validation_status("proposal-1"), ValidationStatus.PENDING.value)
        
        # Mark as valid
        engine.mark_valid("proposal-1")
        self.assertEqual(engine.get_validation_status("proposal-1"), ValidationStatus.VALID.value)
        
        # Mark as invalid
        engine.mark_invalid("proposal-1", [ValidationIssue(
            check_type=ValidationCheckType.FORMAT,
            severity=ValidationSeverity.ERROR,
            message="Error",
        )])
        self.assertEqual(engine.get_validation_status("proposal-1"), ValidationStatus.INVALID.value)


if __name__ == "__main__":
    unittest.main()
