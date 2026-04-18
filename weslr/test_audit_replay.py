# test_audit_replay.py - WESLR v43: Audit Replay / Decision Forensics Surface Tests
# Focused tests for audit replay layer.
# Additive only, transparent, reversible, non-manipulative, no repo drift.

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.audit_replay import (
    ReplayStatus,
    ForensicCategory,
    ReplayEvent,
    ReplayTrace,
    ForensicReport,
    AuditReplayEngine,
    integrate_with_audit_ledger,
    integrate_with_governance_surface,
    integrate_with_operator_views,
)


class TestReplayStatusEnum(TestCase):
    """Test replay status enum values."""
    
    def test_all_statuses_present(self):
        """All expected statuses are defined."""
        expected_statuses = [
            "active",
            "complete",
            "partial",
            "degraded",
        ]
        
        for status in expected_statuses:
            self.assertIn(status, [s.value for s in ReplayStatus])
    
    def test_statuses_are_strings(self):
        """All status values are strings."""
        for status in ReplayStatus:
            self.assertIsInstance(status.value, str)


class TestForensicCategoryEnum(TestCase):
    """Test forensic category enum values."""
    
    def test_all_categories_present(self):
        """All expected categories are defined."""
        expected_categories = [
            "decision_reconstruction",
            "evidence_chain",
            "approval_history",
            "state_transition",
            "escalation_path",
            "root_cause_analysis",
        ]
        
        for category in expected_categories:
            self.assertIn(category, [c.value for c in ForensicCategory])
    
    def test_categories_are_strings(self):
        """All category values are strings."""
        for category in ForensicCategory:
            self.assertIsInstance(category.value, str)


class TestReplayEvent(TestCase):
    """Test ReplayEvent data class."""
    
    def test_event_creation(self):
        """Event creation works correctly."""
        event = ReplayEvent(
            event_id="event_test_123",
            event_type="proposal_created",
            timestamp="2026-04-06T18:00:00Z",
            source="system",
            actor_id="test_actor",
            affected_object_id="proposal_456",
            context_id="context_789",
        )
        
        self.assertEqual(event.event_id, "event_test_123")
        self.assertEqual(event.event_type, "proposal_created")
        self.assertEqual(event.source, "system")
        self.assertEqual(event.actor_id, "test_actor")
        self.assertEqual(event.affected_object_id, "proposal_456")
        self.assertEqual(event.context_id, "context_789")
    
    def test_event_with_approval(self):
        """Event creation with approval works."""
        event = ReplayEvent(
            event_id="event_approval_123",
            event_type="proposal_approved",
            timestamp="2026-04-06T18:00:00Z",
            source="operator",
            actor_id="operator_1",
            approval_status="approved",
            approval_notes="Approved by operator",
        )
        
        self.assertEqual(event.approval_status, "approved")
        self.assertEqual(event.approval_notes, "Approved by operator")
    
    def test_event_with_state_transition(self):
        """Event creation with state transition works."""
        event = ReplayEvent(
            event_id="event_state_123",
            event_type="state_changed",
            timestamp="2026-04-06T18:00:00Z",
            source="system",
            before_state={"status": "draft"},
            after_state={"status": "approved"},
        )
        
        self.assertEqual(event.before_state, {"status": "draft"})
        self.assertEqual(event.after_state, {"status": "approved"})
    
    def test_to_dict(self):
        """Event to_dict conversion works."""
        event = ReplayEvent(
            event_id="event_test",
            event_type="proposal_created",
            timestamp="2026-04-06T18:00:00Z",
            source="system",
        )
        
        result = event.to_dict()
        
        self.assertEqual(result["event_id"], "event_test")
        self.assertEqual(result["event_type"], "proposal_created")
        self.assertIn("timestamp", result)
        self.assertIn("created_at", result)
    
    def test_from_dict(self):
        """Event from_dict reconstruction works."""
        original = ReplayEvent(
            event_id="event_test",
            event_type="proposal_approved",
            timestamp="2026-04-06T18:00:00Z",
            source="system",
            approval_status="approved",
        )
        
        data = original.to_dict()
        recreated = ReplayEvent.from_dict(data)
        
        self.assertEqual(recreated.event_id, original.event_id)
        self.assertEqual(recreated.event_type, original.event_type)
        self.assertEqual(recreated.approval_status, original.approval_status)


class TestReplayTrace(TestCase):
    """Test ReplayTrace data class."""
    
    def test_trace_creation(self):
        """Trace creation works correctly."""
        trace = ReplayTrace(
            trace_id="trace_test_123",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
            category=ForensicCategory.DECISION_RECONSTRUCTION.value,
        )
        
        self.assertEqual(trace.trace_id, "trace_test_123")
        self.assertEqual(trace.affected_object_id, "proposal_456")
        self.assertEqual(trace.affected_object_type, "proposal")
        self.assertEqual(trace.category, ForensicCategory.DECISION_RECONSTRUCTION.value)
        self.assertEqual(len(trace.events), 0)
    
    def test_add_event(self):
        """Trace add_event works correctly."""
        trace = ReplayTrace(
            trace_id="trace_test",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
        )
        
        event = {
            "event_id": "event_1",
            "event_type": "proposal_created",
        }
        
        trace.add_event(event)
        
        self.assertEqual(len(trace.events), 1)
        self.assertEqual(trace.events[0], event)
    
    def test_get_events_by_actor(self):
        """Trace get_events_by_actor works correctly."""
        trace = ReplayTrace(
            trace_id="trace_test",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
        )
        
        trace.add_event({
            "event_id": "event_1",
            "event_type": "proposal_created",
            "actor_id": "operator_1",
        })
        trace.add_event({
            "event_id": "event_2",
            "event_type": "proposal_approved",
            "actor_id": "operator_1",
        })
        trace.add_event({
            "event_id": "event_3",
            "event_type": "proposal_created",
            "actor_id": "operator_2",
        })
        
        operator1_events = trace.get_events_by_actor("operator_1")
        
        self.assertEqual(len(operator1_events), 2)
    
    def test_get_events_by_type(self):
        """Trace get_events_by_type works correctly."""
        trace = ReplayTrace(
            trace_id="trace_test",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
        )
        
        trace.add_event({
            "event_id": "event_1",
            "event_type": "proposal_created",
        })
        trace.add_event({
            "event_id": "event_2",
            "event_type": "proposal_approved",
        })
        trace.add_event({
            "event_id": "event_3",
            "event_type": "proposal_created",
        })
        
        created_events = trace.get_events_by_type("proposal_created")
        
        self.assertEqual(len(created_events), 2)
    
    def test_get_approval_events(self):
        """Trace get_approval_events works correctly."""
        trace = ReplayTrace(
            trace_id="trace_test",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
        )
        
        trace.add_event({
            "event_id": "event_1",
            "event_type": "proposal_approved",
            "approval_status": "approved",
        })
        trace.add_event({
            "event_id": "event_2",
            "event_type": "proposal_denied",
            "approval_status": "denied",
        })
        trace.add_event({
            "event_id": "event_3",
            "event_type": "proposal_created",
        })
        
        approval_events = trace.get_approval_events()
        
        self.assertEqual(len(approval_events), 2)
    
    def test_generate_forensic_summary(self):
        """Trace generate_forensic_summary works correctly."""
        trace = ReplayTrace(
            trace_id="trace_test",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
        )
        
        trace.add_event({
            "event_id": "event_1",
            "event_type": "proposal_created",
        })
        trace.add_event({
            "event_id": "event_2",
            "event_type": "proposal_approved",
            "approval_status": "approved",
            "actor_id": "operator_1",
        })
        
        summary = trace.generate_forensic_summary()
        
        self.assertIsNotNone(summary)
        self.assertIn("Events:", summary)
        self.assertIn("Approvals:", summary)
        self.assertIn("Actors:", summary)
    
    def test_to_dict(self):
        """Trace to_dict conversion works."""
        trace = ReplayTrace(
            trace_id="trace_test",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
        )
        
        result = trace.to_dict()
        
        self.assertEqual(result["trace_id"], "trace_test")
        self.assertEqual(result["affected_object_id"], "proposal_456")
        self.assertEqual(result["event_count"], 0)
        self.assertIn("events", result)
        self.assertIn("created_at", result)
    
    def test_from_dict(self):
        """Trace from_dict reconstruction works."""
        original = ReplayTrace(
            trace_id="trace_test",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
        )
        
        data = original.to_dict()
        recreated = ReplayTrace.from_dict(data)
        
        self.assertEqual(recreated.trace_id, original.trace_id)
        self.assertEqual(recreated.affected_object_id, original.affected_object_id)


class TestForensicReport(TestCase):
    """Test ForensicReport data class."""
    
    def test_report_creation(self):
        """Report creation works correctly."""
        report = ForensicReport(
            report_id="report_test_123",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
            status="draft",
        )
        
        self.assertEqual(report.report_id, "report_test_123")
        self.assertEqual(report.affected_object_id, "proposal_456")
        self.assertEqual(report.affected_object_type, "proposal")
        self.assertEqual(report.status, "draft")
        self.assertEqual(len(report.traces), 0)
    
    def test_to_dict(self):
        """Report to_dict conversion works."""
        report = ForensicReport(
            report_id="report_test",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
        )
        
        result = report.to_dict()
        
        self.assertEqual(result["report_id"], "report_test")
        self.assertEqual(result["affected_object_id"], "proposal_456")
        self.assertEqual(result["trace_count"], 0)
        self.assertIn("traces", result)
        self.assertIn("created_at", result)
    
    def test_from_dict(self):
        """Report from_dict reconstruction works."""
        original = ForensicReport(
            report_id="report_test",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
        )
        
        data = original.to_dict()
        recreated = ForensicReport.from_dict(data)
        
        self.assertEqual(recreated.report_id, original.report_id)
        self.assertEqual(recreated.affected_object_id, original.affected_object_id)


class TestAuditReplayEngine(TestCase):
    """Test AuditReplayEngine class."""
    
    def test_engine_initialization(self):
        """Engine initialization works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            self.assertEqual(len(engine.traces), 0)
            self.assertEqual(len(engine.reports), 0)
    
    def test_create_trace(self):
        """Engine create_trace works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            trace = engine.create_trace(
                trace_id="trace_test",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
            )
            
            self.assertIsNotNone(trace)
            self.assertEqual(trace.trace_id, "trace_test")
            self.assertEqual(trace.affected_object_id, "proposal_456")
    
    def test_get_trace(self):
        """Engine get_trace works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            trace = engine.create_trace(
                trace_id="trace_test",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
            )
            retrieved = engine.get_trace("trace_test")
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.trace_id, trace.trace_id)
    
    def test_create_trace_from_events(self):
        """Engine create_trace_from_events works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            events = [
                {
                    "event_id": "event_1",
                    "event_type": "proposal_created",
                },
                {
                    "event_id": "event_2",
                    "event_type": "proposal_approved",
                },
            ]
            
            trace = engine.create_trace_from_events(
                trace_id="trace_test",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
                events=events,
            )
            
            self.assertIsNotNone(trace)
            self.assertEqual(len(trace.events), 2)
    
    def test_create_report(self):
        """Engine create_report works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            trace1 = engine.create_trace(
                trace_id="trace_1",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
            )
            trace2 = engine.create_trace(
                trace_id="trace_2",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
            )
            
            report = engine.create_report(
                report_id="report_test",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
                traces=["trace_1", "trace_2"],
            )
            
            self.assertIsNotNone(report)
            self.assertEqual(len(report.traces), 2)
    
    def test_get_report(self):
        """Engine get_report works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            report = engine.create_report(
                report_id="report_test",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
                traces=[],
            )
            retrieved = engine.get_report("report_test")
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.report_id, report.report_id)
    
    def test_get_trace_summary(self):
        """Engine get_trace_summary works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            trace = engine.create_trace(
                trace_id="trace_proposal_456",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
            )
            trace.add_event({
                "event_id": "event_1",
                "event_type": "proposal_created",
            })
            trace.add_event({
                "event_id": "event_2",
                "event_type": "proposal_approved",
                "actor_id": "operator_1",
            })
            
            summary = engine.get_trace_summary("proposal_456")
            
            self.assertIsNotNone(summary)
            self.assertTrue(summary["trace_exists"])
            self.assertEqual(summary["event_count"], 2)
    
    def test_get_trace_summary_not_found(self):
        """Engine get_trace_summary handles missing object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            summary = engine.get_trace_summary("nonexistent_object")
            
            self.assertIsNotNone(summary)
            self.assertFalse(summary["trace_exists"])
            self.assertEqual(summary["event_count"], 0)
    
    def test_to_dict(self):
        """Engine to_dict conversion works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            engine.create_trace(
                trace_id="trace_test",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
            )
            
            result = engine.to_dict()
            
            self.assertEqual(result["trace_count"], 1)
            self.assertEqual(result["report_count"], 0)
            self.assertIn("traces", result)
            self.assertIn("reports", result)


class TestIntegrationHooks(TestCase):
    """Test integration hook functions."""
    
    def test_integrate_with_audit_ledger(self):
        """integrate_with_audit_ledger adds replay context."""
        audit_dict = {"audit_id": "test_audit"}
        
        result = integrate_with_audit_ledger(audit_dict)
        
        self.assertIn("audit_replay_context", result)
        self.assertIsNone(result["audit_replay_context"])
    
    def test_integrate_with_audit_ledger_with_engine(self):
        """integrate_with_audit_ledger works with replay engine."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            engine.create_trace(
                trace_id="trace_test",
                affected_object_id="integration_object",
                affected_object_type="proposal",
            )
            trace = engine.get_trace("trace_test")
            if trace:
                trace.add_event({
                    "event_id": "event_1",
                    "event_type": "proposal_created",
                })
            
            audit_dict = {"audit_id": "test_audit"}
            
            result = integrate_with_audit_ledger(
                audit_dict,
                replay_engine=engine,
                object_id="integration_object",
            )
            
            self.assertIn("audit_replay_context", result)
            self.assertIsNotNone(result["audit_replay_context"])
            self.assertTrue(result["audit_replay_context"]["trace_exists"])
    
    def test_integrate_with_governance_surface(self):
        """integrate_with_governance_surface adds replay context."""
        governance_dict = {"governance_id": "test_governance"}
        
        result = integrate_with_governance_surface(governance_dict)
        
        self.assertIn("audit_replay_context", result)
        self.assertIsNone(result["audit_replay_context"])
    
    def test_integrate_with_operator_views(self):
        """integrate_with_operator_views adds replay context."""
        operator_dict = {"operator_id": "test_operator"}
        
        result = integrate_with_operator_views(operator_dict)
        
        self.assertIn("audit_replay_context", result)
        self.assertIsNone(result["audit_replay_context"])


class TestForensicFlow(TestCase):
    """Test complete forensic analysis flow."""
    
    def test_complete_forensic_trace_flow(self):
        """Complete forensic trace flow works end-to-end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            # Create trace
            trace = engine.create_trace(
                trace_id="trace_proposal_456",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
            )
            
            # Add events
            trace.add_event({
                "event_id": "event_1",
                "event_type": "proposal_created",
            })
            trace.add_event({
                "event_id": "event_2",
                "event_type": "proposal_approved",
                "actor_id": "operator_1",
                "approval_status": "approved",
            })
            
            # Generate summary
            summary = trace.generate_forensic_summary()
            
            self.assertIsNotNone(summary)
            self.assertIn("Events:", summary)
            self.assertIn("Actors:", summary)
    
    def test_complete_forensic_report_flow(self):
        """Complete forensic report flow works end-to-end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            # Create traces
            trace1 = engine.create_trace(
                trace_id="trace_proposal_456",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
            )
            trace1.add_event({
                "event_id": "event_1",
                "event_type": "proposal_created",
            })
            
            trace2 = engine.create_trace(
                trace_id="trace_proposal_456_escalation",
                affected_object_id="proposal_456",
                affected_object_type="escalation",
            )
            trace2.add_event({
                "event_id": "event_2",
                "event_type": "escalation_triggered",
            })
            
            # Create report
            report = engine.create_report(
                report_id="report_proposal_456",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
                traces=["trace_proposal_456", "trace_proposal_456_escalation"],
            )
            
            self.assertIsNotNone(report)
            self.assertEqual(len(report.traces), 2)


class TestBackwardCompatibility(TestCase):
    """Test backward compatibility with existing code."""
    
    def test_existing_code_works_without_replay_context(self):
        """Existing code works when replay context not provided."""
        # Integration hooks should work without replay engine
        audit_result = integrate_with_audit_ledger({"test": "data"})
        self.assertEqual(audit_result["test"], "data")
        
        governance_result = integrate_with_governance_surface({"test": "data"})
        self.assertEqual(governance_result["test"], "data")
        
        operator_result = integrate_with_operator_views({"test": "data"})
        self.assertEqual(operator_result["test"], "data")
    
    def test_engine_without_context(self):
        """Engine works without context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            # Create trace without context
            trace = engine.create_trace(
                trace_id="no_context_trace",
                affected_object_id="object_1",
                affected_object_type="proposal",
            )
            
            self.assertIsNotNone(trace)
    
    def test_trace_without_optional_fields(self):
        """Trace creation works without optional fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            trace = engine.create_trace(
                trace_id="minimal_trace",
                affected_object_id="object_1",
                affected_object_type="proposal",
            )
            
            self.assertIsNotNone(trace)
            # Default category is decision_reconstruction
            self.assertEqual(trace.category, "decision_reconstruction")
            self.assertIsNone(trace.forensic_summary)


class TestSerialization(TestCase):
    """Test serialization and deserialization."""
    
    def test_event_serialization(self):
        """Event serialization round-trip works."""
        original = ReplayEvent(
            event_id="serial_test",
            event_type="proposal_created",
            timestamp="2026-04-06T18:00:00Z",
            source="system",
            approval_status="approved",
        )
        
        data = original.to_dict()
        recreated = ReplayEvent.from_dict(data)
        
        self.assertEqual(original.event_id, recreated.event_id)
        self.assertEqual(original.event_type, recreated.event_type)
        self.assertEqual(original.approval_status, recreated.approval_status)
    
    def test_trace_serialization(self):
        """Trace serialization round-trip works."""
        original = ReplayTrace(
            trace_id="serial_test",
            affected_object_id="object_1",
            affected_object_type="proposal",
        )
        
        data = original.to_dict()
        recreated = ReplayTrace.from_dict(data)
        
        self.assertEqual(original.trace_id, recreated.trace_id)
        self.assertEqual(original.affected_object_id, recreated.affected_object_id)
    
    def test_report_serialization(self):
        """Report serialization round-trip works."""
        original = ForensicReport(
            report_id="serial_test",
            affected_object_id="object_1",
            affected_object_type="proposal",
        )
        
        data = original.to_dict()
        recreated = ForensicReport.from_dict(data)
        
        self.assertEqual(original.report_id, recreated.report_id)
        self.assertEqual(original.affected_object_id, recreated.affected_object_id)


class TestIntegrationWithExistingLayers(TestCase):
    """Test integration with existing WESLR layers."""
    
    def test_integration_with_audit_ledger(self):
        """Integration with audit ledger works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            engine.create_trace(
                trace_id="trace_test",
                affected_object_id="audit_object",
                affected_object_type="proposal",
            )
            trace = engine.get_trace("trace_test")
            if trace:
                trace.add_event({
                    "event_id": "event_1",
                    "event_type": "proposal_created",
                })
            
            audit_dict = {
                "audit_id": "audit_test",
                "object_id": "audit_object",
            }
            
            result = integrate_with_audit_ledger(
                audit_dict,
                replay_engine=engine,
                object_id="audit_object",
            )
            
            self.assertIn("audit_replay_context", result)
            self.assertIsNotNone(result["audit_replay_context"])
    
    def test_integration_with_governance_surface(self):
        """Integration with governance surface works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AuditReplayEngine(storage_path=tmpdir)
            
            trace = engine.create_trace(
                trace_id="trace_context_123",
                affected_object_id="object_1",
                affected_object_type="proposal",
            )
            trace.add_event({
                "event_id": "event_1",
                "event_type": "proposal_created",
                "context_id": "context_123",
            })
            
            governance_dict = {
                "governance_id": "governance_test",
                "context_id": "context_123",
            }
            
            result = integrate_with_governance_surface(
                governance_dict,
                replay_engine=engine,
                context_id="context_123",
            )
            
            self.assertIn("audit_replay_context", result)
            self.assertIsNotNone(result["audit_replay_context"])


if __name__ == "__main__":
    import unittest
    unittest.main()
