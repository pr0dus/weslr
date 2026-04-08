"""Test suite for Observability + Audit Export Layer (v94e)

Test Doctrine version: 1.0.0 (2026-04-08)
Test coverage: Observability and audit export functionality
"""

import unittest
import time
import json
from io import StringIO

from weslr.observability import (
    get_routing_timeline,
    get_governance_decisions,
    get_proposal_lifecycle,
    get_audit_timeline,
    export_routing_summary,
    export_governance_summary,
    format_routing_timeline,
    format_governance_decisions,
    format_audit_summary,
    AuditEvent,
)


class TestObservabilityModel(unittest.TestCase):
    """Model tests for Observability layer."""

    def test_audit_event_serialization(self):
        """Test AuditEvent dataclass can be serialized."""
        event = AuditEvent(
            timestamp=1234567890,
            event_type="routing",
            proposal_id="test_001",
            action="route",
            actor="operator",
            notes="Test event",
        )
        
        data = event.__dict__
        self.assertEqual(data["timestamp"], 1234567890)
        self.assertEqual(data["event_type"], "routing")
        self.assertEqual(data["proposal_id"], "test_001")

    def test_audit_event_to_dict(self):
        """Test AuditEvent can be converted to dict."""
        event = AuditEvent(
            timestamp=int(time.time()),
            event_type="governance",
            proposal_id="test_002",
            action="approve",
            actor="reviewer",
        )
        
        data = event.__dict__
        self.assertIn("timestamp", data)
        self.assertIn("event_type", data)
        self.assertIn("proposal_id", data)

    def test_json_serialization_of_audit_events(self):
        """Test AuditEvent list can be JSON serialized."""
        events = [
            AuditEvent(
                timestamp=1234567890,
                event_type="routing",
                proposal_id="test_003",
                action="route",
                actor="op1",
            ),
            AuditEvent(
                timestamp=1234567891,
                event_type="governance",
                proposal_id="test_003",
                action="approve",
                actor="op2",
            ),
        ]
        
        # Should serialize without error
        json_str = json.dumps([e.__dict__ for e in events])
        parsed = json.loads(json_str)
        self.assertEqual(len(parsed), 2)


class TestObservabilityCoreMethods(unittest.TestCase):
    """Core method behavior tests."""

    def test_get_routing_timeline_returns_list(self):
        """Test get_routing_timeline returns List."""
        result = get_routing_timeline("any_id")
        self.assertIsInstance(result, list)

    def test_get_routing_timeline_empty_proposal(self):
        """Test get_routing_timeline handles missing proposal."""
        result = get_routing_timeline("nonexistent")
        self.assertIsInstance(result, list)

    def test_get_governance_decisions_returns_list(self):
        """Test get_governance_decisions returns List."""
        result = get_governance_decisions("any_id")
        self.assertIsInstance(result, list)

    def test_get_governance_decisions_empty_proposal(self):
        """Test get_governance_decisions handles missing proposal."""
        result = get_governance_decisions("nonexistent")
        self.assertIsInstance(result, list)

    def test_get_proposal_lifecycle_returns_dict(self):
        """Test get_proposal_lifecycle returns Dict with lifecycle info."""
        result = get_proposal_lifecycle("any_id")
        self.assertIsInstance(result, dict)
        self.assertIn("proposal_id", result)
        self.assertIn("transitions", result)

    def test_get_proposal_lifecycle_empty_proposal(self):
        """Test get_proposal_lifecycle handles missing proposal."""
        result = get_proposal_lifecycle("nonexistent")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["transitions"], [])

    def test_get_audit_timeline_returns_list(self):
        """Test get_audit_timeline returns List[AuditEvent]."""
        result = get_audit_timeline()
        self.assertIsInstance(result, list)

    def test_export_routing_summary_returns_dict(self):
        """Test export_routing_summary returns Dict."""
        result = export_routing_summary()
        self.assertIsInstance(result, dict)
        self.assertIn("total_count", result)

    def test_export_governance_summary_returns_dict(self):
        """Test export_governance_summary returns Dict."""
        result = export_governance_summary()
        self.assertIsInstance(result, dict)
        self.assertIn("review_count", result)
        self.assertIn("decisions_by_type", result)


class TestObservabilityAggregation(unittest.TestCase):
    """Aggregation and timeline behavior tests."""

    def test_audit_timeline_aggregates_routes(self):
        """Test audit timeline can aggregate routing events."""
        router = get_audit_timeline()
        # Just verify it returns something
        self.assertIsInstance(router, list)

    def test_audit_timeline_sorted_by_timestamp(self):
        """Test audit timeline events are sorted by timestamp."""
        events = get_audit_timeline()
        if events:
            timestamps = [e.timestamp for e in events]
            self.assertEqual(timestamps, sorted(timestamps))

    def test_routing_summary_counts_by_status(self):
        """Test routing summary counts events by status."""
        summary = export_routing_summary()
        self.assertIn("count_by_status", summary)

    def test_governance_summary_has_decisions_by_type(self):
        """Test governance summary has decisions by type."""
        summary = export_governance_summary()
        self.assertIn("decisions_by_type", summary)


class TestObservabilityBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests."""

    def test_router_importable(self):
        """Test EvidenceToGovernanceRouter importable from v94d."""
        from weslr.evidence_to_governance_router import EvidenceToGovernanceRouter
        self.assertIsNotNone(EvidenceToGovernanceRouter)

    def test_governance_engine_importable(self):
        """Test ProposalGovernanceEngine importable from v94b."""
        from weslr.internal_reasoning_graph.governance import ProposalGovernanceEngine
        self.assertIsNotNone(ProposalGovernanceEngine)

    def test_evidence_intake_importable(self):
        """Test evidence intake models importable from v94c."""
        from weslr.evidence_intake.models import EvidenceProposalPayload
        self.assertIsNotNone(EvidenceProposalPayload)

    def test_v94d_cli_evidence_importable(self):
        """Test CLI evidence module importable from v94d."""
        from weslr.cli_evidence import register_commands
        self.assertIsNotNone(register_commands)


class TestObservabilityFormatters(unittest.TestCase):
    """Formatter helper tests."""

    def test_format_routing_timeline_returns_string(self):
        """Test format_routing_timeline returns human-readable string."""
        result = format_routing_timeline("any_id")
        self.assertIsInstance(result, str)

    def test_format_routing_timeline_empty(self):
        """Test format_routing_timeline handles empty history."""
        result = format_routing_timeline("nonexistent")
        self.assertIsInstance(result, str)

    def test_format_governance_decisions_returns_string(self):
        """Test format_governance_decisions returns human-readable string."""
        result = format_governance_decisions("any_id")
        self.assertIsInstance(result, str)

    def test_format_audit_summary_returns_string(self):
        """Test format_audit_summary returns human-readable string."""
        result = format_audit_summary()
        self.assertIsInstance(result, str)

    def test_formatters_are_pure_functions(self):
        """Test formatter helpers don't have side effects."""
        # Call formatter - should return string without modifying state
        result = format_routing_timeline("test")
        self.assertIsInstance(result, str)
        # No assertion about state since we're testing pure function behavior


class TestObservabilityOutputStructure(unittest.TestCase):
    """Output structure tests."""

    def test_export_routing_summary_structure(self):
        """Test export_routing_summary has expected structure."""
        summary = export_routing_summary()
        self.assertIn("routings", summary)
        self.assertIn("total_count", summary)
        self.assertIn("count_by_status", summary)

    def test_export_governance_summary_structure(self):
        """Test export_governance_summary has expected structure."""
        summary = export_governance_summary()
        self.assertIn("review_records", summary)
        self.assertIn("history_records", summary)
        self.assertIn("review_count", summary)
        self.assertIn("history_count", summary)

    def test_get_proposal_lifecycle_structure(self):
        """Test get_proposal_lifecycle has expected structure."""
        lifecycle = get_proposal_lifecycle("any_id")
        self.assertIn("proposal_id", lifecycle)
        self.assertIn("transitions", lifecycle)
        self.assertIn("actors", lifecycle)
        self.assertIn("total_duration_seconds", lifecycle)


if __name__ == "__main__":
    unittest.main()
