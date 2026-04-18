# test_audit_ledger.py - WESLR v42: Audit / Traceability Ledger Layer Tests
# Focused tests for audit ledger layer.
# Additive only, transparent, reversible, non-manipulative, no repo drift.

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.audit_ledger import (
    LedgerEventType,
    AuditSource,
    AuditLevel,
    LedgerEvent,
    AuditLedger,
    AuditLedgerEngine,
    integrate_with_proposals,
    integrate_with_proof_gate,
    integrate_with_escalation,
    integrate_with_governance_surface,
)


class TestLedgerEventTypeEnum(TestCase):
    """Test ledger event type enum values."""
    
    def test_all_event_types_present(self):
        """All expected event types are defined."""
        expected_types = [
            "proposal_created",
            "proposal_updated",
            "proposal_approved",
            "proposal_denied",
            "proposal_deferred",
            "proposal_deprecated",
            "proof_requested",
            "proof_satisfied",
            "proof_failed",
            "execution_eligible",
            "execution_blocked",
            "escalation_triggered",
            "escalation_approved",
            "escalation_denied",
            "escalation_escalated",
            "state_changed",
            "context_changed",
            "configuration_changed",
            "system_started",
            "systemstopped",
            "handoff_created",
            "handoff_reviewed",
            "handoff_timed_out",
            "other",
        ]
        
        for event_type in expected_types:
            self.assertIn(event_type, [t.value for t in LedgerEventType])
    
    def test_event_types_are_strings(self):
        """All event type values are strings."""
        for event_type in LedgerEventType:
            self.assertIsInstance(event_type.value, str)


class TestAuditSourceEnum(TestCase):
    """Test audit source enum values."""
    
    def test_all_sources_present(self):
        """All expected sources are defined."""
        expected_sources = [
            "system",
            "operator",
            "administrator",
            "apis_caller",
            "scheduled_task",
            "integration",
        ]
        
        for source in expected_sources:
            self.assertIn(source, [s.value for s in AuditSource])
    
    def test_sources_are_strings(self):
        """All source values are strings."""
        for source in AuditSource:
            self.assertIsInstance(source.value, str)


class TestAuditLevelEnum(TestCase):
    """Test audit level enum values."""
    
    def test_all_levels_present(self):
        """All expected levels are defined."""
        expected_levels = [
            "debug",
            "info",
            "warn",
            "error",
            "critical",
        ]
        
        for level in expected_levels:
            self.assertIn(level, [l.value for l in AuditLevel])


class TestLedgerEvent(TestCase):
    """Test LedgerEvent data class."""
    
    def test_event_creation(self):
        """Event creation works correctly."""
        event = LedgerEvent(
            event_id="event_test_123",
            event_type=LedgerEventType.PROPOSAL_CREATED.value,
            timestamp="2026-04-06T18:00:00Z",
            source=AuditSource.SYSTEM.value,
            actor_id="test_actor",
            affected_object_id="proposal_456",
            context_id="context_789",
        )
        
        self.assertEqual(event.event_id, "event_test_123")
        self.assertEqual(event.event_type, LedgerEventType.PROPOSAL_CREATED.value)
        self.assertEqual(event.source, AuditSource.SYSTEM.value)
        self.assertEqual(event.actor_id, "test_actor")
        self.assertEqual(event.affected_object_id, "proposal_456")
        self.assertEqual(event.context_id, "context_789")
    
    def test_event_with_approval(self):
        """Event creation with approval works."""
        event = LedgerEvent(
            event_id="event_approval_123",
            event_type=LedgerEventType.PROPOSAL_APPROVED.value,
            timestamp="2026-04-06T18:00:00Z",
            source=AuditSource.OPERATOR.value,
            actor_id="operator_1",
            approval_status="approved",
            approval_notes="Approved by operator",
        )
        
        self.assertEqual(event.approval_status, "approved")
        self.assertEqual(event.approval_notes, "Approved by operator")
    
    def test_event_with_state_transition(self):
        """Event creation with state transition works."""
        event = LedgerEvent(
            event_id="event_state_123",
            event_type=LedgerEventType.STATE_CHANGED.value,
            timestamp="2026-04-06T18:00:00Z",
            before_state={"status": "draft"},
            after_state={"status": "approved"},
        )
        
        self.assertEqual(event.before_state, {"status": "draft"})
        self.assertEqual(event.after_state, {"status": "approved"})
    
    def test_to_dict(self):
        """Event to_dict conversion works."""
        event = LedgerEvent(
            event_id="event_test",
            event_type=LedgerEventType.PROPOSAL_CREATED.value,
            timestamp="2026-04-06T18:00:00Z",
        )
        
        result = event.to_dict()
        
        self.assertEqual(result["event_id"], "event_test")
        self.assertEqual(result["event_type"], LedgerEventType.PROPOSAL_CREATED.value)
        self.assertIn("timestamp", result)
        self.assertIn("created_at", result)
    
    def test_from_dict(self):
        """Event from_dict reconstruction works."""
        original = LedgerEvent(
            event_id="event_test",
            event_type=LedgerEventType.PROPOSAL_APPROVED.value,
            timestamp="2026-04-06T18:00:00Z",
            approval_status="approved",
        )
        
        data = original.to_dict()
        recreated = LedgerEvent.from_dict(data)
        
        self.assertEqual(recreated.event_id, original.event_id)
        self.assertEqual(recreated.event_type, original.event_type)
        self.assertEqual(recreated.approval_status, original.approval_status)


class TestAuditLedger(TestCase):
    """Test AuditLedger data class."""
    
    def test_ledger_creation(self):
        """Ledger creation works correctly."""
        ledger = AuditLedger(
            ledger_id="test_ledger_123",
            name="Test Ledger",
            description="Test description",
        )
        
        self.assertEqual(ledger.ledger_id, "test_ledger_123")
        self.assertEqual(ledger.name, "Test Ledger")
        self.assertEqual(ledger.description, "Test description")
        self.assertEqual(len(ledger.events), 0)
    
    def test_add_event(self):
        """Ledger add_event works correctly."""
        ledger = AuditLedger(
            ledger_id="test_ledger",
            name="Test Ledger",
        )
        
        event = {
            "event_id": "event_1",
            "event_type": LedgerEventType.PROPOSAL_CREATED.value,
        }
        
        ledger.add_event(event)
        
        self.assertEqual(len(ledger.events), 1)
        self.assertEqual(ledger.events[0], event)
    
    def test_get_events_by_type(self):
        """Ledger get_events_by_type works correctly."""
        ledger = AuditLedger(
            ledger_id="test_ledger",
            name="Test Ledger",
        )
        
        ledger.add_event({
            "event_id": "event_1",
            "event_type": LedgerEventType.PROPOSAL_CREATED.value,
        })
        ledger.add_event({
            "event_id": "event_2",
            "event_type": LedgerEventType.PROPOSAL_APPROVED.value,
        })
        ledger.add_event({
            "event_id": "event_3",
            "event_type": LedgerEventType.PROPOSAL_CREATED.value,
        })
        
        created_events = ledger.get_events_by_type(LedgerEventType.PROPOSAL_CREATED.value)
        
        self.assertEqual(len(created_events), 2)
    
    def test_get_events_by_object(self):
        """Ledger get_events_by_object works correctly."""
        ledger = AuditLedger(
            ledger_id="test_ledger",
            name="Test Ledger",
        )
        
        ledger.add_event({
            "event_id": "event_1",
            "event_type": LedgerEventType.PROPOSAL_CREATED.value,
            "affected_object_id": "proposal_456",
        })
        ledger.add_event({
            "event_id": "event_2",
            "event_type": LedgerEventType.PROPOSAL_APPROVED.value,
            "affected_object_id": "proposal_456",
        })
        ledger.add_event({
            "event_id": "event_3",
            "event_type": LedgerEventType.PROPOSAL_CREATED.value,
            "affected_object_id": "proposal_789",
        })
        
        proposal_events = ledger.get_events_by_object("proposal_456")
        
        self.assertEqual(len(proposal_events), 2)
    
    def test_get_trace_summary(self):
        """Ledger get_trace_summary works correctly."""
        ledger = AuditLedger(
            ledger_id="test_ledger",
            name="Test Ledger",
        )
        
        ledger.add_event({
            "event_id": "event_1",
            "event_type": LedgerEventType.PROPOSAL_CREATED.value,
            "affected_object_id": "proposal_456",
        })
        ledger.add_event({
            "event_id": "event_2",
            "event_type": LedgerEventType.PROPOSAL_APPROVED.value,
            "affected_object_id": "proposal_456",
            "approval_status": "approved",
        })
        
        summary = ledger.get_trace_summary("proposal_456")
        
        self.assertEqual(summary["object_id"], "proposal_456")
        self.assertEqual(summary["event_count"], 2)
        self.assertEqual(summary["approval_count"], 1)
    
    def test_to_dict(self):
        """Ledger to_dict conversion works."""
        ledger = AuditLedger(
            ledger_id="test_ledger",
            name="Test Ledger",
        )
        
        result = ledger.to_dict()
        
        self.assertEqual(result["ledger_id"], "test_ledger")
        self.assertEqual(result["name"], "Test Ledger")
        self.assertEqual(result["event_count"], 0)
        self.assertIn("events", result)
        self.assertIn("created_at", result)
    
    def test_from_dict(self):
        """Ledger from_dict reconstruction works."""
        original = AuditLedger(
            ledger_id="test_ledger",
            name="Test Ledger",
        )
        
        data = original.to_dict()
        recreated = AuditLedger.from_dict(data)
        
        self.assertEqual(recreated.ledger_id, original.ledger_id)
        self.assertEqual(recreated.name, original.name)


class TestAuditLedgerEngine(TestCase):
    """Test AuditLedgerEngine class."""
    
    def test_engine_initialization(self):
        """Engine initialization works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            self.assertEqual(len(engine.ledgers), 0)
    
    def test_create_ledger(self):
        """Engine create_ledger works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            ledger = engine.create_ledger(
                ledger_id="test_ledger",
                name="Test Ledger",
                description="Test description",
            )
            
            self.assertIsNotNone(ledger)
            self.assertEqual(ledger.ledger_id, "test_ledger")
            self.assertEqual(ledger.name, "Test Ledger")
    
    def test_get_ledger(self):
        """Engine get_ledger works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            ledger = engine.create_ledger(ledger_id="test_ledger")
            retrieved = engine.get_ledger("test_ledger")
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.ledger_id, ledger.ledger_id)
    
    def test_record_proposal_created(self):
        """Engine record_proposal_created works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            event = engine.record_proposal_created(
                proposal_id="proposal_123",
                title="Test Proposal",
                description="Test description",
                context_id="context_456",
            )
            
            self.assertIsNotNone(event)
            self.assertEqual(event.event_type, LedgerEventType.PROPOSAL_CREATED.value)
    
    def test_record_proposal_approved(self):
        """Engine record_proposal_approved works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            event = engine.record_proposal_approved(
                proposal_id="proposal_123",
                approved_by="operator_1",
                notes="Approved by operator",
            )
            
            self.assertIsNotNone(event)
            self.assertEqual(event.event_type, LedgerEventType.PROPOSAL_APPROVED.value)
            self.assertEqual(event.approval_status, "approved")
    
    def test_record_proposal_denied(self):
        """Engine record_proposal_denied works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            event = engine.record_proposal_denied(
                proposal_id="proposal_123",
                denied_by="operator_1",
                notes="Denied by operator",
            )
            
            self.assertIsNotNone(event)
            self.assertEqual(event.event_type, LedgerEventType.PROPOSAL_DENIED.value)
            self.assertEqual(event.approval_status, "denied")
    
    def test_record_proof_requested(self):
        """Engine record_proof_requested works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            event = engine.record_proof_requested(
                proposal_id="proposal_123",
                proof_type="risk_assessment",
                requested_by="system",
            )
            
            self.assertIsNotNone(event)
            self.assertEqual(event.event_type, LedgerEventType.PROOF_REQUESTED.value)
    
    def test_record_escalation_triggered(self):
        """Engine record_escalation_triggered works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            event = engine.record_escalation_triggered(
                escalation_id="escalation_123",
                trigger="blocked_by_capability",
                reason="Capability prohibited",
                required_role="operator",
            )
            
            self.assertIsNotNone(event)
            self.assertEqual(event.event_type, LedgerEventType.ESCALATION_TRIGGERED.value)
    
    def test_record_escalation_approved(self):
        """Engine record_escalation_approved works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            event = engine.record_escalation_approved(
                escalation_id="escalation_123",
                approved_by="operator_1",
                notes="Approved",
            )
            
            self.assertIsNotNone(event)
            self.assertEqual(event.event_type, LedgerEventType.ESCALATION_APPROVED.value)
    
    def test_record_escalation_denied(self):
        """Engine record_escalation_denied works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            event = engine.record_escalation_denied(
                escalation_id="escalation_123",
                denied_by="operator_1",
                notes="Denied",
            )
            
            self.assertIsNotNone(event)
            self.assertEqual(event.event_type, LedgerEventType.ESCALATION_DENIED.value)
    
    def test_get_default_ledger(self):
        """Engine get_default_ledger creates default if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            ledger = engine.get_default_ledger()
            
            self.assertIsNotNone(ledger)
            self.assertEqual(ledger.ledger_id, "default")
    
    def test_get_trace_summary(self):
        """Engine get_trace_summary works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            engine.record_proposal_created(
                proposal_id="proposal_123",
                title="Test Proposal",
                description="Test description",
            )
            engine.record_proposal_approved(
                proposal_id="proposal_123",
                approved_by="operator_1",
            )
            
            summary = engine.get_trace_summary("proposal_123")
            
            self.assertEqual(summary["object_id"], "proposal_123")
            self.assertEqual(summary["event_count"], 2)
            self.assertEqual(summary["approval_count"], 1)
    
    def test_to_dict(self):
        """Engine to_dict conversion works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            engine.create_ledger(ledger_id="test_ledger")
            
            result = engine.to_dict()
            
            self.assertEqual(result["ledger_count"], 1)
            self.assertIn("ledgers", result)


class TestIntegrationHooks(TestCase):
    """Test integration hook functions."""
    
    def test_integrate_with_proposals(self):
        """integrate_with_proposals adds ledger context."""
        proposal_dict = {"proposal_id": "test_proposal"}
        
        result = integrate_with_proposals(proposal_dict)
        
        self.assertIn("audit_ledger_context", result)
        self.assertIsNone(result["audit_ledger_context"])
    
    def test_integrate_with_proposals_with_engine(self):
        """integrate_with_proposals works with ledger engine."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            engine.record_proposal_created(
                proposal_id="integration_proposal",
                title="Test Proposal",
                description="Test description",
            )
            
            proposal_dict = {"proposal_id": "integration_proposal"}
            
            result = integrate_with_proposals(
                proposal_dict,
                ledger_engine=engine,
                proposal_id="integration_proposal",
            )
            
            self.assertIn("audit_ledger_context", result)
            self.assertIsNotNone(result["audit_ledger_context"])
            self.assertEqual(result["audit_ledger_context"]["event_count"], 1)
    
    def test_integrate_with_proof_gate(self):
        """integrate_with_proof_gate adds ledger context."""
        proof_dict = {"proof_type": "validation"}
        
        result = integrate_with_proof_gate(proof_dict)
        
        self.assertIn("audit_ledger_context", result)
        self.assertIsNone(result["audit_ledger_context"])
    
    def test_integrate_with_escalation(self):
        """integrate_with_escalation adds ledger context."""
        escalation_dict = {"escalation_id": "test_escalation"}
        
        result = integrate_with_escalation(escalation_dict)
        
        self.assertIn("audit_ledger_context", result)
        self.assertIsNone(result["audit_ledger_context"])
    
    def test_integrate_with_governance_surface(self):
        """integrate_with_governance_surface adds ledger context."""
        governance_dict = {"governance_id": "test_governance"}
        
        result = integrate_with_governance_surface(governance_dict)
        
        self.assertIn("audit_ledger_context", result)
        self.assertIsNone(result["audit_ledger_context"])


class TestAuditFlow(TestCase):
    """Test complete audit flow."""
    
    def test_complete_proposal_audit_flow(self):
        """Complete proposal audit flow works end-to-end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            # Create proposal
            engine.record_proposal_created(
                proposal_id="proposal_123",
                title="Test Proposal",
                description="Test description",
            )
            
            # Approve proposal
            engine.record_proposal_approved(
                proposal_id="proposal_123",
                approved_by="operator_1",
                notes="Approved by operator",
            )
            
            # Get trace summary
            summary = engine.get_trace_summary("proposal_123")
            
            self.assertEqual(summary["event_count"], 2)
            self.assertEqual(summary["approval_count"], 1)
    
    def test_complete_escalation_audit_flow(self):
        """Complete escalation audit flow works end-to-end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            # Trigger escalation
            engine.record_escalation_triggered(
                escalation_id="escalation_123",
                trigger="blocked_by_capability",
                reason="Capability prohibited",
                required_role="operator",
            )
            
            # Approve escalation
            engine.record_escalation_approved(
                escalation_id="escalation_123",
                approved_by="operator_1",
                notes="Approved after review",
            )
            
            # Get trace summary
            summary = engine.get_trace_summary("escalation_123")
            
            self.assertEqual(summary["event_count"], 2)
            self.assertEqual(summary["approval_count"], 1)


class TestBackwardCompatibility(TestCase):
    """Test backward compatibility with existing code."""
    
    def test_existing_code_works_without_audit_context(self):
        """Existing code works when audit context not provided."""
        # Integration hooks should work without ledger engine
        proposal_result = integrate_with_proposals({"test": "data"})
        self.assertEqual(proposal_result["test"], "data")
        
        proof_result = integrate_with_proof_gate({"test": "data"})
        self.assertEqual(proof_result["test"], "data")
        
        escalation_result = integrate_with_escalation({"test": "data"})
        self.assertEqual(escalation_result["test"], "data")
    
    def test_engine_without_context(self):
        """Engine works without context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            # Create ledger without context
            ledger = engine.create_ledger(
                ledger_id="no_context_ledger",
                name="No Context Ledger",
            )
            
            self.assertIsNotNone(ledger)
    
    def test_record_event_without_optional_fields(self):
        """Engine record methods work without optional fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            
            event = engine.record_proposal_created(
                proposal_id="proposal_minimal",
                title="Minimal Proposal",
                description="Test description",
            )
            
            self.assertIsNotNone(event)
            self.assertIsNone(event.actor_id)


class TestSerialization(TestCase):
    """Test serialization and deserialization."""
    
    def test_event_serialization(self):
        """Event serialization round-trip works."""
        original = LedgerEvent(
            event_id="serial_test",
            event_type=LedgerEventType.PROPOSAL_CREATED.value,
            timestamp="2026-04-06T18:00:00Z",
            approval_status="approved",
        )
        
        data = original.to_dict()
        recreated = LedgerEvent.from_dict(data)
        
        self.assertEqual(original.event_id, recreated.event_id)
        self.assertEqual(original.event_type, recreated.event_type)
        self.assertEqual(original.approval_status, recreated.approval_status)
    
    def test_ledger_serialization(self):
        """Ledger serialization round-trip works."""
        original = AuditLedger(
            ledger_id="serial_test",
            name="Test Ledger",
        )
        
        data = original.to_dict()
        recreated = AuditLedger.from_dict(data)
        
        self.assertEqual(original.ledger_id, recreated.ledger_id)
        self.assertEqual(original.name, recreated.name)


class TestIntegrationWithExistingLayers(TestCase):
    """Test integration with existing WESLR layers."""
    
    def test_integration_with_proposals(self):
        """Integration with proposals works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            engine.record_proposal_created(
                proposal_id="proposal_test",
                title="Test Proposal",
                description="Test description",
            )
            
            # Simulate proposal usage pattern
            proposal_dict = {
                "proposal_id": "proposal_test",
                "title": "Test Proposal",
            }
            
            result = integrate_with_proposals(
                proposal_dict,
                ledger_engine=engine,
                proposal_id="proposal_test",
            )
            
            self.assertIn("audit_ledger_context", result)
            self.assertIsNotNone(result["audit_ledger_context"])
    
    def test_integration_with_escalation(self):
        """Integration with escalation works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditLedgerEngine(storage_path=tmpdir)
            engine.record_escalation_triggered(
                escalation_id="escalation_test",
                trigger="blocked_by_capability",
                reason="Capability prohibited",
                required_role="operator",
            )
            
            escalation_dict = {
                "escalation_id": "escalation_test",
                "trigger": "blocked_by_capability",
            }
            
            result = integrate_with_escalation(
                escalation_dict,
                ledger_engine=engine,
                escalation_id="escalation_test",
            )
            
            self.assertIn("audit_ledger_context", result)
            self.assertIsNotNone(result["audit_ledger_context"])


if __name__ == "__main__":
    import unittest
    unittest.main()
