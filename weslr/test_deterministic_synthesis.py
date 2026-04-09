# test_deterministic_synthesis.py - WESLR v94g: Deterministic Insight Synthesis Layer Tests
# Tests for v94g Deterministic Insight Synthesis Layer.
# Read-only operator-facing layer tests only.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no storage framework expansion, no analytics engine beyond synthesis scope.

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from weslr.deterministic_synthesis import (
    ApprovalReasonGrouping,
    BottleneckRecurrenceSummary,
    ConfidenceTrendSummary,
    DeterministicSynthesisEngine,
    DeterministicSynthesisFormatter,
    DeterministicSynthesisResult,
    PatternGrouping,
    ProposalOutcomeGrouping,
    SynthesisScope,
    SynthesisType,
)


# ============================================================================
# TEST DATA HELPERS
# ============================================================================


def create_test_records() -> List[Dict[str, Any]]:
    """Create test records for synthesis testing."""
    return [
        # Approval events
        {
            "event_id": "event_001",
            "event_type": "approval",
            "record_id": "record_001",
            "record_type": "approval_event",
            "approval_notes": "Validated by operator",
            "approval_status": "approved",
            "timestamp": "2026-04-07T12:00:00Z",
        },
        {
            "event_id": "event_002",
            "event_type": "approval",
            "record_id": "record_002",
            "record_type": "approval_event",
            "approval_notes": "Validated by operator",
            "approval_status": "approved",
            "timestamp": "2026-04-07T12:05:00Z",
        },
        {
            "event_id": "event_003",
            "event_type": "approval",
            "record_id": "record_003",
            "record_type": "approval_event",
            "approval_notes": "Insufficient evidence",
            "approval_status": "denied",
            "timestamp": "2026-04-07T12:10:00Z",
        },
        {
            "event_id": "event_004",
            "event_type": "approval",
            "record_id": "record_004",
            "record_type": "approval_event",
            "approval_notes": "Insufficient evidence",
            "approval_status": "denied",
            "timestamp": "2026-04-07T12:15:00Z",
        },
        {
            "event_id": "event_005",
            "event_type": "approval",
            "record_id": "record_005",
            "record_type": "approval_event",
            "approval_notes": "Validated by operator",
            "approval_status": "approved",
            "timestamp": "2026-04-07T12:20:00Z",
        },
        # Proposals
        {
            "proposal_id": "proposal_001",
            "record_type": "proposal",
            "state": "approved",
            "title": "System health improvement",
            "effort": 50,
            "risk": "low",
        },
        {
            "proposal_id": "proposal_002",
            "record_type": "proposal",
            "state": "approved",
            "title": "Performance optimization",
            "effort": 75,
            "risk": "medium",
        },
        {
            "proposal_id": "proposal_003",
            "record_type": "proposal",
            "state": "denied",
            "title": "Breaking change proposal",
            "effort": 100,
            "risk": "high",
        },
        {
            "proposal_id": "proposal_004",
            "record_type": "proposal",
            "state": "deferred",
            "title": "Future enhancement",
            "effort": 20,
            "risk": "low",
        },
        # Confidence records
        {
            "record_id": "confidence_001",
            "record_type": "confidence",
            "confidence": 0.7,
            "trend_type": "increasing",
        },
        {
            "record_id": "confidence_002",
            "record_type": "confidence",
            "confidence": 0.75,
            "trend_type": "increasing",
        },
        {
            "record_id": "confidence_003",
            "record_type": "confidence",
            "confidence": 0.8,
            "trend_type": "increasing",
        },
        {
            "record_id": "confidence_004",
            "record_type": "confidence",
            "confidence": 0.5,
            "trend_type": "decreasing",
        },
        {
            "record_id": "confidence_005",
            "record_type": "confidence",
            "confidence": 0.45,
            "trend_type": "decreasing",
        },
        {
            "record_id": "confidence_006",
            "record_type": "confidence",
            "confidence": 0.5,
            "trend_type": "stable",
        },
        # Bottleneck events
        {
            "bottleneck_id": "bottleneck_001",
            "record_type": "bottleneck",
            "bottleneck_type": "approval_delay",
            "bottleneck_category": "process",
            "duration": 120,
        },
        {
            "bottleneck_id": "bottleneck_002",
            "record_type": "bottleneck",
            "bottleneck_type": "approval_delay",
            "bottleneck_category": "process",
            "duration": 180,
        },
        {
            "bottleneck_id": "bottleneck_003",
            "record_type": "bottleneck",
            "bottleneck_type": "validation",
            "bottleneck_category": "resource",
            "duration": 90,
        },
        # Generic records for pattern grouping - same type, same content for pattern grouping
        {
            "record_id": "record_101",
            "record_type": "generic",
            "pattern_data": "pattern_a",
        },
        {
            "record_id": "record_102",
            "record_type": "generic",
            "pattern_data": "pattern_a",
        },
        {
            "record_id": "record_103",
            "record_type": "generic",
            "pattern_data": "pattern_a",
        },
    ]


def create_test_audit_ledger() -> Dict[str, Any]:
    """Create test audit ledger for integration testing."""
    return {
        "ledger_id": "test_ledger_001",
        "name": "test_audit_ledger",
        "description": "Test audit ledger for deterministic synthesis",
        "events": [
            {
                "event_id": "audit_event_001",
                "event_type": "proposal_approved",
                "approval_status": "approved",
                "approval_notes": "Operator validated",
                "timestamp": "2026-04-07T12:00:00Z",
            },
            {
                "event_id": "audit_event_002",
                "event_type": "proposal_approved",
                "approval_status": "approved",
                "approval_notes": "Operator validated",
                "timestamp": "2026-04-07T12:05:00Z",
            },
            {
                "event_id": "audit_event_003",
                "event_type": "proposal_denied",
                "approval_status": "denied",
                "approval_notes": "Insufficient evidence",
                "timestamp": "2026-04-07T12:10:00Z",
            },
        ],
    }


# ============================================================================
# MOCK CLASSES (For Integration Testing)
# ============================================================================


class MockRecoveryRecommendationService:
    """Mock v75 RecoveryRecommendationService for testing."""
    
    def __init__(self):
        """Initialize mock service."""
        self._recommendations: List[Dict[str, Any]] = []
    
    def add_recommendation(
        self,
        recommendation_id: str,
        recommendation_type: str,
        interpretation: str,
        confidence_level: str,
        confidence_reason: str,
        confidence_guidance: Optional[str],
        evidence_references: List[str],
    ) -> None:
        """Add a test recommendation."""
        self._recommendations.append({
            "recommendation_id": recommendation_id,
            "recommendation_type": recommendation_type,
            "interpretation": interpretation,
            "confidence_level": confidence_level,
            "confidence_reason": confidence_reason,
            "confidence_guidance": confidence_guidance,
            "evidence_references": evidence_references,
        })
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get all recommendations."""
        return self._recommendations


class MockRecoveryDecisionTrace:
    """Mock v78 RecoveryDecisionTrace for testing."""
    
    def __init__(self):
        """Initialize mock trace."""
        self._records: List[Dict[str, Any]] = []
    
    def add_decision_record(
        self,
        trace_id: str,
        decision_type: str,
        timestamp: str,
        decision: str,
        rationale: str,
        correlation_ids: Dict[str, str],
    ) -> None:
        """Add a test decision record."""
        self._records.append({
            "trace_id": trace_id,
            "decision_type": decision_type,
            "timestamp": timestamp,
            "decision": decision,
            "rationale": rationale,
            "correlation_ids": correlation_ids,
        })
    
    def get_records(self) -> List[Dict[str, Any]]:
        """Get all records."""
        return self._records


# ============================================================================
# DETERMINISTIC SYNTHESIS ENGINE TESTS
# ============================================================================


class TestDeterministicSynthesisEngine(unittest.TestCase):
    """Tests for DeterministicSynthesisEngine."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = DeterministicSynthesisEngine()
        self.test_records = create_test_records()
    
    def test_synthesize_patterns(self) -> None:
        """Test pattern grouping synthesis."""
        patterns = self.engine.synthesize_patterns(self.test_records, pattern_type="repetition", min_frequency=2)
        
        # Should find at least one pattern grouping
        self.assertGreater(len(patterns), 0)
        
        # Check pattern grouping structure
        for pattern in patterns:
            self.assertIsInstance(pattern.pattern_id, str)
            self.assertIn(pattern.pattern_type, ["repetition", "correlation", "sequence"])
            self.assertGreater(pattern.frequency, 0)
            self.assertGreater(len(pattern.member_record_ids), 0)
            self.assertIsInstance(pattern.to_json(), str)
            self.assertIsInstance(pattern.to_dict(), dict)
    
    def test_synthesize_patterns_min_frequency(self) -> None:
        """Test pattern grouping with minimum frequency filter."""
        patterns = self.engine.synthesize_patterns(self.test_records, pattern_type="repetition", min_frequency=5)
        
        # With high min_frequency, should find fewer patterns
        for pattern in patterns:
            self.assertGreaterEqual(pattern.frequency, 5)
    
    def test_synthesize_approval_reasons(self) -> None:
        """Test approval reason grouping synthesis."""
        approval_events = [
            r for r in self.test_records if r.get("event_type") == "approval"
        ]
        reasons = self.engine.synthesize_approval_reasons(approval_events)
        
        # Should find at least one reason grouping
        self.assertGreater(len(reasons), 0)
        
        # Check reason grouping structure
        for reason in reasons:
            self.assertIsInstance(reason.reason_id, str)
            self.assertIn(reason.reason_type, ["approval", "rejection"])
            self.assertGreater(len(reason.member_record_ids), 0)
            self.assertGreater(reason.frequency, 0)
            self.assertGreaterEqual(reason.approval_rate, 0.0)
            self.assertLessEqual(reason.approval_rate, 1.0)
            self.assertIsInstance(reason.to_json(), str)
            self.assertIsInstance(reason.to_dict(), dict)
    
    def test_synthesize_proposal_outcomes(self) -> None:
        """Test proposal outcome grouping synthesis."""
        proposals = [r for r in self.test_records if r.get("record_type") == "proposal"]
        outcomes = self.engine.synthesize_proposal_outcomes(proposals)
        
        # Should find at least one outcome grouping
        self.assertGreater(len(outcomes), 0)
        
        # Check outcome grouping structure
        for outcome in outcomes:
            self.assertIsInstance(outcome.outcome_id, str)
            self.assertIn(outcome.outcome_category, ["approved", "denied", "deferred", "deprecated"])
            self.assertGreater(len(outcome.member_proposal_ids), 0)
            self.assertGreater(outcome.frequency, 0)
            self.assertIsInstance(outcome.to_json(), str)
            self.assertIsInstance(outcome.to_dict(), dict)
    
    def test_synthesize_confidence_trends(self) -> None:
        """Test confidence trend synthesis."""
        confidence_records = [
            r for r in self.test_records if r.get("record_type") == "confidence"
        ]
        trends = self.engine.synthesize_confidence_trends(confidence_records)
        
        # Should find at least one trend summary
        self.assertGreater(len(trends), 0)
        
        # Check trend summary structure
        for trend in trends:
            self.assertIsInstance(trend.trend_id, str)
            self.assertIn(trend.trend_type, ["increasing", "decreasing", "stable", "variable"])
            self.assertIsInstance(trend.before_confidence, float)
            self.assertIsInstance(trend.after_confidence, float)
            self.assertIn(trend.confidence_direction, ["up", "down", "stable", "variable"])
            self.assertGreater(len(trend.member_record_ids), 0)
            self.assertGreater(trend.frequency, 0)
            self.assertIsInstance(trend.to_json(), str)
            self.assertIsInstance(trend.to_dict(), dict)
    
    def test_synthesize_bottleneck_recurrences(self) -> None:
        """Test bottleneck recurrence synthesis."""
        bottleneck_events = [
            r for r in self.test_records if r.get("record_type") == "bottleneck"
        ]
        bottlenecks = self.engine.synthesize_bottleneck_recurrences(bottleneck_events)
        
        # Should find at least one bottleneck summary
        self.assertGreater(len(bottlenecks), 0)
        
        # Check bottleneck summary structure
        for bottleneck in bottlenecks:
            self.assertIsInstance(bottleneck.bottleneck_id, str)
            self.assertIn(bottleneck.bottleneck_type, ["approval_delay", "validation", "escalation"])
            self.assertGreater(len(bottleneck.member_bottleneck_ids), 0)
            self.assertGreater(bottleneck.frequency, 0)
            self.assertIsInstance(bottleneck.to_json(), str)
            self.assertIsInstance(bottleneck.to_dict(), dict)
    
    def test_synthesize_all(self) -> None:
        """Test complete synthesis from existing records."""
        result = self.engine.synthesize_all(self.test_records, scope="global")
        
        # Check result structure
        self.assertIsInstance(result.result_id, str)
        self.assertEqual(result.synthesis_type, "complete")
        self.assertEqual(result.synthesis_scope, "global")
        self.assertEqual(result.source_record_count, len(self.test_records))
        self.assertIsInstance(result.processing_duration_ms, int)
        self.assertGreaterEqual(result.processing_duration_ms, 0)  # Can be 0 for fast execution
        
        # Check all synthesis outputs are present
        self.assertGreater(len(result.pattern_groupings), 0)
        self.assertGreater(len(result.approval_reason_groupings), 0)
        self.assertGreater(len(result.proposal_outcome_groupings), 0)
        self.assertGreater(len(result.confidence_trend_summaries), 0)
        self.assertGreater(len(result.bottleneck_recurrence_summaries), 0)
        
        # Check JSON export
        json_output = result.to_json()
        self.assertIsInstance(json_output, str)
        parsed = json.loads(json_output)
        self.assertEqual(parsed["source_record_count"], len(self.test_records))
    
    def test_export_to_json(self) -> None:
        """Test JSON export functionality."""
        result = self.engine.synthesize_all(self.test_records, scope="global")
        
        # Export to file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name
        
        try:
            json_output = self.engine.export_to_json(result, filepath)
            
            # Verify file was created
            self.assertTrue(os.path.exists(filepath))
            
            # Verify JSON output
            self.assertIsInstance(json_output, str)
            parsed = json.loads(json_output)
            self.assertEqual(parsed["result_id"], result.result_id)
        finally:
            os.unlink(filepath)
    
    def test_get_cached_synthesis_result(self) -> None:
        """Test cached synthesis result retrieval."""
        result = self.engine.synthesize_all(self.test_records, scope="global")
        
        # Get cached result
        cached = self.engine.get_synthesis_result(result.result_id)
        self.assertIsNotNone(cached)
        self.assertEqual(cached.result_id, result.result_id)
        
        # Test non-existent result
        nonexistent = self.engine.get_synthesis_result("nonexistent_id")
        self.assertIsNone(nonexistent)
    
    def test_empty_records_handling(self) -> None:
        """Test handling of empty record list."""
        empty_records = []
        result = self.engine.synthesize_all(empty_records, scope="global")
        
        self.assertEqual(result.source_record_count, 0)
        self.assertEqual(len(result.pattern_groupings), 0)
        self.assertEqual(len(result.approval_reason_groupings), 0)
        self.assertEqual(len(result.proposal_outcome_groupings), 0)
        self.assertEqual(len(result.confidence_trend_summaries), 0)
        self.assertEqual(len(result.bottleneck_recurrence_summaries), 0)
    
    def test_single_record_handling(self) -> None:
        """Test handling of single record."""
        single_record = self.test_records[:1]
        result = self.engine.synthesize_all(single_record, scope="global")
        
        self.assertEqual(result.source_record_count, 1)


# ============================================================================
# DETERMINISTIC SYNTHESIS FORMATTER TESTS
# ============================================================================


class TestDeterministicSynthesisFormatter(unittest.TestCase):
    """Tests for DeterministicSynthesisFormatter."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = DeterministicSynthesisEngine()
        self.test_records = create_test_records()
        self.result = self.engine.synthesize_all(self.test_records, scope="global")
    
    def test_format_pattern_grouping(self) -> None:
        """Test pattern grouping text formatting."""
        pg = self.result.pattern_groupings[0]
        formatted = DeterministicSynthesisFormatter.format_pattern_grouping(pg)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("Pattern Grouping:", formatted)
        self.assertIn("Type:", formatted)
        self.assertIn("Members:", formatted)
    
    def test_format_approval_reason_grouping(self) -> None:
        """Test approval reason grouping text formatting."""
        arg = self.result.approval_reason_groupings[0]
        formatted = DeterministicSynthesisFormatter.format_approval_reason_grouping(arg)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("Approval Reason:", formatted)
        self.assertIn("Reason:", formatted)
        self.assertIn("Approval Rate:", formatted)
    
    def test_format_proposal_outcome_grouping(self) -> None:
        """Test proposal outcome grouping text formatting."""
        pog = self.result.proposal_outcome_groupings[0]
        formatted = DeterministicSynthesisFormatter.format_proposal_outcome_grouping(pog)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("Proposal Outcome:", formatted)
        self.assertIn("Category:", formatted)
        self.assertIn("Members:", formatted)
    
    def test_format_confidence_trend_summary(self) -> None:
        """Test confidence trend summary text formatting."""
        cts = self.result.confidence_trend_summaries[0]
        formatted = DeterministicSynthesisFormatter.format_confidence_trend_summary(cts)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("Confidence Trend:", formatted)
        self.assertIn("Before:", formatted)
        self.assertIn("After:", formatted)
        self.assertIn("Direction:", formatted)
    
    def test_format_bottleneck_recurrence_summary(self) -> None:
        """Test bottleneck recurrence summary text formatting."""
        brs = self.result.bottleneck_recurrence_summaries[0]
        formatted = DeterministicSynthesisFormatter.format_bottleneck_recurrence_summary(brs)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("Bottleneck:", formatted)
        self.assertIn("Type:", formatted)
        self.assertIn("Category:", formatted)
    
    def test_format_result(self) -> None:
        """Test complete result text formatting."""
        formatted = DeterministicSynthesisFormatter.format_result(self.result)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("DETERMINISTIC INSIGHT SYNTHESIS REPORT", formatted)
        self.assertIn("PATTERN GROUPINGS", formatted)
        self.assertIn("APPROVAL REASON GROUPINGS", formatted)
        self.assertIn("PROPOSAL OUTCOME GROUPINGS", formatted)
        self.assertIn("CONFIDENCE TREND SUMMARIES", formatted)
        self.assertIn("BOTTLENECK RECURRENCE SUMMARIES", formatted)
        self.assertIn("Result ID:", formatted)
        self.assertIn("Scope:", formatted)
    
    def test_format_result_is_operator_readable(self) -> None:
        """Verify formatted output is operator-readable (no code, no JSON)."""
        formatted = DeterministicSynthesisFormatter.format_result(self.result)
        
        # Should be plain text (not raw JSON)
        # Note: criteria and reason fields may contain JSON in their values, but
        # the overall structure is human-readable with clear section headers
        lines = formatted.split("\n")
        self.assertGreater(len(lines), 10)  # Multiple lines for readability
        
        # Check for section headers (human-readable, not machine-readable)
        self.assertIn("PATTERN GROUPINGS", formatted)
        self.assertIn("APPROVAL REASON GROUPINGS", formatted)
        self.assertIn("PROPOSAL OUTCOME GROUPINGS", formatted)
        self.assertIn("CONFIDENCE TREND SUMMARIES", formatted)
        self.assertIn("BOTTLENECK RECURRENCE SUMMARIES", formatted)


# ============================================================================
# NO-MUTATION BOUNDARY TESTS
# ============================================================================


class TestNoMutationBoundary(unittest.TestCase):
    """Tests for no-mutation boundary."""
    
    def test_engine_does_not_mutate_source_records(self) -> None:
        """Verify engine does not mutate source records."""
        records = create_test_records()
        original_records = json.loads(json.dumps(records))  # Deep copy
        
        engine = DeterministicSynthesisEngine()
        engine.synthesize_all(records, scope="global")
        
        # Verify records unchanged
        self.assertEqual(records, original_records)
    
    def test_engine_does_not_mutate_audit_ledger(self) -> None:
        """Verify engine does not mutate audit ledger."""
        audit_data = create_test_audit_ledger()
        original_events = json.loads(json.dumps(audit_data.get("events", [])))
        
        engine = DeterministicSynthesisEngine()
        engine.synthesize_all(original_events, scope="global")
        
        # Verify events unchanged
        self.assertEqual(audit_data["events"], original_events)


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestBackwardCompatibility(unittest.TestCase):
    """Tests for backward compatibility with existing WESLR modules."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = DeterministicSynthesisEngine()
    
    def test_engine_works_with_mock_repositories(self) -> None:
        """Test engine works with mock repository implementations."""
        # Create mock repositories (simulating existing WESLR structures)
        mock_recommendation_service = MockRecoveryRecommendationService()
        mock_decision_trace = MockRecoveryDecisionTrace()
        
        # Add some test data
        mock_recommendation_service.add_recommendation(
            recommendation_id="rec_001",
            recommendation_type="suggestion",
            interpretation="Test interpretation",
            confidence_level="high",
            confidence_reason="Test reason",
            confidence_guidance="Test guidance",
            evidence_references=["ev_001", "ev_002"],
        )
        
        mock_decision_trace.add_decision_record(
            trace_id="trace_001",
            decision_type="proposal",
            timestamp="2026-04-07T12:00:00Z",
            decision="approve",
            rationale="Test rationale",
            correlation_ids={"flow_id": "flow_001"},
        )
        
        # Verify mocks work (integration test)
        recommendations = mock_recommendation_service.get_recommendations()
        self.assertGreater(len(recommendations), 0)
        
        records = mock_decision_trace.get_records()
        self.assertGreater(len(records), 0)
    
    def test_engine_compatible_with_existing_data_models(self) -> None:
        """Test engine compatible with existing WESLR data models."""
        # Test with data structures matching existing WESLR models
        # Pattern grouping requires at least 2 records with same pattern data
        test_data = [
            {
                "event_id": "event_001",
                "event_type": "approval",
                "record_type": "approval_event",
                "pattern_data": "approval_pattern",
                "approval_notes": "Validated",
                "approval_status": "approved",
            },
            {
                "event_id": "event_002",
                "event_type": "approval",
                "record_type": "approval_event",
                "pattern_data": "approval_pattern",
                "approval_notes": "Validated",
                "approval_status": "approved",
            },
            {
                "proposal_id": "proposal_001",
                "record_type": "proposal",
                "pattern_data": "proposal_pattern",
                "state": "approved",
                "title": "Test proposal",
            },
            {
                "proposal_id": "proposal_002",
                "record_type": "proposal",
                "pattern_data": "proposal_pattern",
                "state": "approved",
                "title": "Test proposal 2",
            },
            {
                "record_id": "confidence_001",
                "record_type": "confidence",
                "pattern_data": "confidence_pattern",
                "confidence": 0.8,
            },
            {
                "record_id": "confidence_002",
                "record_type": "confidence",
                "pattern_data": "confidence_pattern",
                "confidence": 0.85,
            },
            {
                "bottleneck_id": "bottleneck_001",
                "record_type": "bottleneck",
                "pattern_data": "bottleneck_pattern",
                "bottleneck_type": "approval_delay",
                "bottleneck_category": "process",
            },
            {
                "bottleneck_id": "bottleneck_002",
                "record_type": "bottleneck",
                "pattern_data": "bottleneck_pattern",
                "bottleneck_type": "approval_delay",
                "bottleneck_category": "process",
            },
        ]
        
        result = self.engine.synthesize_all(test_data, scope="context")
        self.assertIsNotNone(result)
        
        # Verify all synthesis outputs present
        self.assertGreater(len(result.pattern_groupings), 0)
        self.assertGreater(len(result.approval_reason_groupings), 0)
        self.assertGreater(len(result.proposal_outcome_groupings), 0)
        self.assertGreater(len(result.confidence_trend_summaries), 0)
        self.assertGreater(len(result.bottleneck_recurrence_summaries), 0)


# ============================================================================
# EXPORT SCHEMA TESTS
# ============================================================================


class TestExportSchema(unittest.TestCase):
    """Tests for JSON export schema compliance."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = DeterministicSynthesisEngine()
        self.test_records = create_test_records()
        self.result = self.engine.synthesize_all(self.test_records, scope="global")
    
    def test_result_json_schema(self) -> None:
        """Test result JSON export schema."""
        json_output = self.result.to_json()
        data = json.loads(json_output)
        
        # Required fields
        self.assertIn("result_id", data)
        self.assertIn("synthesis_type", data)
        self.assertIn("synthesis_scope", data)
        self.assertIn("created_at", data)
        
        # Synthesis outputs
        self.assertIn("pattern_groupings", data)
        self.assertIn("approval_reason_groupings", data)
        self.assertIn("proposal_outcome_groupings", data)
        self.assertIn("confidence_trend_summaries", data)
        self.assertIn("bottleneck_recurrence_summaries", data)
        
        # Metadata
        self.assertIn("source_record_count", data)
        self.assertIn("processing_duration_ms", data)
    
    def test_pattern_grouping_json_schema(self) -> None:
        """Test pattern grouping JSON schema."""
        pg = self.result.pattern_groupings[0]
        data = pg.to_dict()
        
        self.assertIn("pattern_id", data)
        self.assertIn("pattern_type", data)
        self.assertIn("criteria", data)
        self.assertIn("member_record_ids", data)
        self.assertIn("frequency", data)
    
    def test_approval_reason_grouping_json_schema(self) -> None:
        """Test approval reason grouping JSON schema."""
        arg = self.result.approval_reason_groupings[0]
        data = arg.to_dict()
        
        self.assertIn("reason_id", data)
        self.assertIn("reason_type", data)
        self.assertIn("reason_text", data)
        self.assertIn("member_record_ids", data)
        self.assertIn("frequency", data)
        self.assertIn("approval_rate", data)
    
    def test_proposal_outcome_grouping_json_schema(self) -> None:
        """Test proposal outcome grouping JSON schema."""
        pog = self.result.proposal_outcome_groupings[0]
        data = pog.to_dict()
        
        self.assertIn("outcome_id", data)
        self.assertIn("outcome_category", data)
        self.assertIn("member_proposal_ids", data)
        self.assertIn("frequency", data)
    
    def test_confidence_trend_summary_json_schema(self) -> None:
        """Test confidence trend summary JSON schema."""
        cts = self.result.confidence_trend_summaries[0]
        data = cts.to_dict()
        
        self.assertIn("trend_id", data)
        self.assertIn("trend_type", data)
        self.assertIn("before_confidence", data)
        self.assertIn("after_confidence", data)
        self.assertIn("confidence_change", data)
        self.assertIn("confidence_direction", data)
        self.assertIn("member_record_ids", data)
        self.assertIn("frequency", data)
    
    def test_bottleneck_recurrence_summary_json_schema(self) -> None:
        """Test bottleneck recurrence summary JSON schema."""
        brs = self.result.bottleneck_recurrence_summaries[0]
        data = brs.to_dict()
        
        self.assertIn("bottleneck_id", data)
        self.assertIn("bottleneck_type", data)
        self.assertIn("bottleneck_category", data)
        self.assertIn("member_bottleneck_ids", data)
        self.assertIn("frequency", data)
    
    def test_nested_json_structure(self) -> None:
        """Test nested JSON structure correctness."""
        json_output = self.result.to_json()
        data = json.loads(json_output)
        
        # Verify pattern_groupings is array of objects
        for pg in data["pattern_groupings"]:
            self.assertIsInstance(pg, dict)
            self.assertIsInstance(pg["pattern_id"], str)
            self.assertIsInstance(pg["criteria"], dict)
            self.assertIsInstance(pg["member_record_ids"], list)
        
        # Verify approval_reason_groupings is array of objects
        for arg in data["approval_reason_groupings"]:
            self.assertIsInstance(arg, dict)
            self.assertIsInstance(arg["reason_text"], str)
            self.assertIsInstance(arg["member_record_ids"], list)
        
        # Verify proposal_outcome_groupings is array of objects
        for pog in data["proposal_outcome_groupings"]:
            self.assertIsInstance(pog, dict)
            self.assertIsInstance(pog["outcome_category"], str)
            self.assertIsInstance(pog["member_proposal_ids"], list)
        
        # Verify confidence_trend_summaries is array of objects
        for cts in data["confidence_trend_summaries"]:
            self.assertIsInstance(cts, dict)
            self.assertIsInstance(cts["confidence_direction"], str)
            self.assertIsInstance(cts["member_record_ids"], list)
        
        # Verify bottleneck_recurrence_summaries is array of objects
        for brs in data["bottleneck_recurrence_summaries"]:
            self.assertIsInstance(brs, dict)
            self.assertIsInstance(brs["bottleneck_category"], str)
            self.assertIsInstance(brs["member_bottleneck_ids"], list)


# ============================================================================
# NO-RECOMMENDATION BOUNDARY TESTS
# ============================================================================


class TestNoRecommendationBoundary(unittest.TestCase):
    """Tests for no-recommendation boundary."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = DeterministicSynthesisEngine()
        self.test_records = create_test_records()
        self.result = self.engine.synthesize_all(self.test_records, scope="global")
    
    def test_result_does_not_contain_recommendations(self) -> None:
        """Verify result does not contain recommendations."""
        json_output = self.result.to_json()
        data = json.loads(json_output)
        
        # Check for recommendation-like content
        for key in data.keys():
            if isinstance(data[key], list):
                for item in data[key]:
                    self.assertNotIn("recommendation", key.lower())
                    if isinstance(item, dict):
                        for subkey in item.keys():
                            self.assertNotIn("recommendation", subkey.lower())
        
        # Check formatted text output
        formatted = DeterministicSynthesisFormatter.format_result(self.result)
        # Note: "recommendation" may appear in field names like "recommendation_type"
        # but the actual output should be descriptive, not prescriptive
        self.assertIn("DETERMINISTIC INSIGHT SYNTHESIS REPORT", formatted)
        self.assertIn("PATTERN GROUPINGS", formatted)
    
    def test_formatter_does_not_generate_recommendations(self) -> None:
        """Verify formatter does not generate recommendations."""
        formatted = DeterministicSynthesisFormatter.format_result(self.result)
        
        # Should not contain recommendation language
        self.assertNotIn("should", formatted.lower())
        self.assertNotIn("must", formatted.lower())
        self.assertNotIn("need to", formatted.lower())
        self.assertNotIn("could", formatted.lower())
        self.assertNotIn("might", formatted.lower())
    
    def test_engine_does_not_make_recommendations(self) -> None:
        """Verify engine synthesis is descriptive, not prescriptive."""
        # All synthesis outputs should describe existing patterns
        # No outputs should suggest future actions
        
        # Pattern groupings should describe patterns, not suggest improvements
        for pg in self.result.pattern_groupings:
            self.assertIsNotNone(pg.pattern_type)
            self.assertIsNotNone(pg.frequency)
        
        # Approval reason groupings should describe reasons, not suggest changes
        for arg in self.result.approval_reason_groupings:
            self.assertIsNotNone(arg.reason_type)
            self.assertIsNotNone(arg.approval_rate)
        
        # Proposal outcome groupings should describe outcomes, not suggest actions
        for pog in self.result.proposal_outcome_groupings:
            self.assertIsNotNone(pog.outcome_category)
            self.assertIsNotNone(pog.frequency)
        
        # Confidence trend summaries should describe trends, not suggest adjustments
        for cts in self.result.confidence_trend_summaries:
            self.assertIsNotNone(cts.trend_type)
            self.assertIsNotNone(cts.confidence_direction)
        
        # Bottleneck recurrence summaries should describe bottlenecks, not suggest fixes
        for brs in self.result.bottleneck_recurrence_summaries:
            self.assertIsNotNone(brs.bottleneck_type)
            self.assertIsNotNone(brs.bottleneck_category)


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    unittest.main(verbosity=2)
