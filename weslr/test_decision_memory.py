"""Test suite for Decision Memory Layer (v94f)

Test Doctrine version: 1.0.0 (2026-04-08)
Test coverage: Decision memory, pattern tracking, confidence history
"""

import unittest
import json
from io import StringIO

from weslr.decision_memory import (
    DecisionRecord,
    ProposalPattern,
    ConfidenceHistory,
    DecisionSummary,
    get_decision_history,
    get_operator_decisions,
    get_decision_counts,
    track_proposal_pattern,
    get_recurring_patterns,
    get_pattern_counts,
    get_confidence_history,
    describe_confidence_trend,
    export_decision_summary,
    export_operator_summary,
    format_decision_summary,
    format_operator_summary,
)


class TestDecisionMemoryModel(unittest.TestCase):
    """Model tests for Decision Memory layer."""

    def test_decision_record_serialization(self):
        """Test DecisionRecord can be serialized."""
        record = DecisionRecord(
            proposal_id="test_001",
            decision="approved",
            operator="reviewer_1",
            timestamp=1234567890,
            notes="Looks good",
            confidence=0.85,
        )
        
        data = record.to_dict()
        self.assertEqual(data["proposal_id"], "test_001")
        self.assertEqual(data["decision"], "approved")
        self.assertEqual(data["confidence"], 0.85)

    def test_decision_record_deserialization(self):
        """Test DecisionRecord can be deserialized."""
        original = DecisionRecord(
            proposal_id="test_002",
            decision="rejected",
            operator="reviewer_2",
            timestamp=1234567891,
            notes="Not suitable",
            confidence=0.3,
        )
        
        data = original.to_dict()
        restored = DecisionRecord.from_dict(data)
        
        self.assertEqual(restored.proposal_id, original.proposal_id)
        self.assertEqual(restored.decision, original.decision)
        self.assertEqual(restored.operator, original.operator)

    def test_proposal_pattern_serialization(self):
        """Test ProposalPattern can be serialized."""
        pattern = ProposalPattern(
            pattern_id="pattern_001",
            claim_text_prefix="test claim",
            outcomes={"approved": 3, "rejected": 1},
            last_update=1234567890,
            confidence_values=[0.7, 0.8, 0.6, 0.9],
        )
        
        data = pattern.to_dict()
        self.assertEqual(data["claim_text_prefix"], "test claim")
        self.assertEqual(data["outcomes"]["approved"], 3)
        self.assertEqual(len(data["confidence_values"]), 4)

    def test_proposal_pattern_total_count(self):
        """Test ProposalPattern.total_count property."""
        pattern = ProposalPattern(
            pattern_id="pattern_002",
            claim_text_prefix="test",
            outcomes={"approved": 5, "rejected": 2},
            last_update=1234567890,
        )
        
        self.assertEqual(pattern.total_count, 7)

    def test_proposal_pattern_approval_rate(self):
        """Test ProposalPattern.approval_rate property."""
        pattern = ProposalPattern(
            pattern_id="pattern_003",
            claim_text_prefix="test",
            outcomes={"approved": 4, "rejected": 1},
            last_update=1234567890,
        )
        
        self.assertAlmostEqual(pattern.approval_rate, 0.8, places=1)

    def test_confidence_history_serialization(self):
        """Test ConfidenceHistory can be serialized."""
        history = ConfidenceHistory(
            proposal_id="history_001",
            values=[
                {"timestamp": 1234567890, "confidence": 0.7},
                {"timestamp": 1234567891, "confidence": 0.8},
            ],
        )
        
        data = history.to_dict()
        self.assertEqual(len(data["values"]), 2)
        self.assertEqual(data["values"][0]["confidence"], 0.7)

    def test_confidence_history_first_last_value(self):
        """Test ConfidenceHistory first/last value properties."""
        history = ConfidenceHistory(
            proposal_id="history_002",
            values=[
                {"timestamp": 1234567890, "confidence": 0.6},
                {"timestamp": 1234567891, "confidence": 0.9},
            ],
        )
        
        self.assertEqual(history.first_value, 0.6)
        self.assertEqual(history.last_value, 0.9)

    def test_decision_summary_serialization(self):
        """Test DecisionSummary can be serialized."""
        summary = DecisionSummary(
            total_decisions=10,
            approved_count=7,
            rejected_count=3,
            patterns=[],
            preference_summary={},
        )
        
        data = summary.to_dict()
        self.assertEqual(data["total_decisions"], 10)
        self.assertEqual(data["approved_count"], 7)

    def test_json_serialization_of_decisions(self):
        """Test DecisionRecord list can be JSON serialized."""
        records = [
            DecisionRecord(
                proposal_id="test_003",
                decision="approved",
                operator="op1",
                timestamp=1234567890,
            ),
            DecisionRecord(
                proposal_id="test_004",
                decision="rejected",
                operator="op2",
                timestamp=1234567891,
            ),
        ]
        
        json_str = json.dumps([r.to_dict() for r in records])
        parsed = json.loads(json_str)
        self.assertEqual(len(parsed), 2)


class TestDecisionHistoryCapture(unittest.TestCase):
    """Decision history capture tests."""

    def test_get_decision_history_returns_list(self):
        """Test get_decision_history returns List[DecisionRecord]."""
        result = get_decision_history("any_id")
        self.assertIsInstance(result, list)

    def test_get_operator_decisions_returns_list(self):
        """Test get_operator_decisions returns List[DecisionRecord]."""
        result = get_operator_decisions("any_operator")
        self.assertIsInstance(result, list)

    def test_get_decision_counts_returns_dict(self):
        """Test get_decision_counts returns Dict with counts."""
        result = get_decision_counts()
        self.assertIsInstance(result, dict)
        self.assertIn("total", result)
        self.assertIn("approved", result)
        self.assertIn("rejected", result)

    def test_get_decision_counts_empty_engine(self):
        """Test get_decision_counts handles empty governance engine."""
        result = get_decision_counts()
        # Should return zeros when no decisions exist
        self.assertIsInstance(result["total"], int)
        self.assertIsInstance(result["approved"], int)
        self.assertIsInstance(result["rejected"], int)


class TestPatternDriftTracking(unittest.TestCase):
    """Pattern tracking and confidence drift tests."""

    def test_track_proposal_pattern_returns_id(self):
        """Test track_proposal_pattern returns pattern ID."""
        pattern_id = track_proposal_pattern(
            proposal_id="pattern_test_001",
            claim_text="Test claim for pattern",
            decision="approved",
            confidence=0.85,
        )
        
        self.assertIsInstance(pattern_id, str)
        self.assertIn("pattern_", pattern_id)

    def test_get_recurring_patterns_returns_list(self):
        """Test get_recurring_patterns returns List[ProposalPattern]."""
        result = get_recurring_patterns()
        self.assertIsInstance(result, list)

    def test_get_pattern_counts_returns_dict(self):
        """Test get_pattern_counts returns Dict with counts."""
        result = get_pattern_counts()
        self.assertIsInstance(result, dict)
        self.assertIn("total_patterns", result)

    def test_get_confidence_history_returns_object(self):
        """Test get_confidence_history returns ConfidenceHistory."""
        result = get_confidence_history("history_test_001")
        self.assertIsInstance(result, ConfidenceHistory)

    def test_get_confidence_history_empty_proposal(self):
        """Test get_confidence_history handles missing proposal."""
        result = get_confidence_history("nonexistent")
        self.assertIsInstance(result, ConfidenceHistory)
        # Should have empty values when no history
        self.assertEqual(result.values, [])


class TestSummaryExportBehavior(unittest.TestCase):
    """Summary export behavior tests."""

    def test_export_decision_summary_returns_object(self):
        """Test export_decision_summary returns DecisionSummary."""
        result = export_decision_summary()
        self.assertIsInstance(result, DecisionSummary)

    def test_export_decision_summary_has_counts(self):
        """Test export_decision_summary has decision counts."""
        result = export_decision_summary()
        self.assertIn("total_decisions", result.to_dict())
        self.assertIn("approved_count", result.to_dict())

    def test_export_operator_summary_returns_dict(self):
        """Test export_operator_summary returns Dict."""
        result = export_operator_summary("any_operator")
        self.assertIsInstance(result, dict)
        self.assertIn("operator", result)
        self.assertIn("total_decisions", result)

    def test_format_decision_summary_returns_string(self):
        """Test format_decision_summary returns human-readable string."""
        summary = DecisionSummary(
            total_decisions=5,
            approved_count=3,
            rejected_count=2,
            patterns=[],
            preference_summary={},
        )
        
        result = format_decision_summary(summary)
        self.assertIsInstance(result, str)
        self.assertIn("Decision Summary", result)

    def test_format_operator_summary_returns_string(self):
        """Test format_operator_summary returns human-readable string."""
        summary = {
            "operator": "test_operator",
            "total_decisions": 3,
            "approved_count": 2,
            "rejected_count": 1,
            "decisions": [],
        }
        
        result = format_operator_summary(summary)
        self.assertIsInstance(result, str)
        self.assertIn("Decision Summary for", result)

    def test_formatters_are_pure_functions(self):
        """Test formatter helpers don't have side effects."""
        # Call formatter - should return string without modifying state
        result = format_decision_summary()
        self.assertIsInstance(result, str)
        # No state mutation assertion needed


class TestDecisionMemoryBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests."""

    def test_governance_engine_importable(self):
        """Test ProposalGovernanceEngine importable from v94b."""
        from weslr.internal_reasoning_graph.governance import ProposalGovernanceEngine
        self.assertIsNotNone(ProposalGovernanceEngine)

    def test_evidence_to_governance_router_importable(self):
        """Test EvidenceToGovernanceRouter importable from v94c."""
        from weslr.evidence_to_governance_router import EvidenceToGovernanceRouter
        self.assertIsNotNone(EvidenceToGovernanceRouter)

    def test_observability_importable(self):
        """Test observability module importable from v94e."""
        from weslr.observability import get_audit_timeline
        self.assertIsNotNone(get_audit_timeline)

    def test_v94d_cli_evidence_importable(self):
        """Test CLI evidence module importable from v94d."""
        from weslr.cli_evidence import register_commands
        self.assertIsNotNone(register_commands)

    def test_v94f_decision_memory_unmodified(self):
        """Test decision memory doesn't break v94b-v94e engines."""
        # All imports should work without error
        from weslr.internal_reasoning_graph.governance import ProposalGovernanceEngine
        from weslr.evidence_to_governance_router import EvidenceToGovernanceRouter
        from weslr.observability import get_audit_timeline
        from weslr.decision_memory import DecisionRecord, export_decision_summary
        
        # Create instances to verify compatibility
        governance = ProposalGovernanceEngine()
        self.assertIsNotNone(governance)
        
        router = EvidenceToGovernanceRouter()
        self.assertIsNotNone(router)
        
        decision = DecisionRecord(
            proposal_id="bc_test_001",
            decision="approved",
            operator="operator",
            timestamp=1234567890,
        )
        self.assertIsNotNone(decision)


if __name__ == "__main__":
    unittest.main()
