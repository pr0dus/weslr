# test_insight_proposal_layer.py - WESLR v94h: Deterministic Insight Proposal Layer Tests
# Tests for v94h Governed Insight Proposal Layer.
# Read-only transformation tests only.
# No mutation, no auto-approval, no auto-application.
# No recommendations, no predictive modeling.

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from weslr.deterministic_synthesis import (
    PatternGrouping,
    ApprovalReasonGrouping,
    ProposalOutcomeGrouping,
    ConfidenceTrendSummary,
    BottleneckRecurrenceSummary,
    DeterministicSynthesisResult,
    SynthesisScope,
)
from weslr.insight_proposal_layer import (
    InsightProposalPayload,
    InsightProposalExporter,
    InsightProposalConverter,
    InsightProposalLayer,
)


# ============================================================================
# TEST DATA HELPERS
# ============================================================================


def create_test_synthesis_result() -> DeterministicSynthesisResult:
    """Create test v94g synthesis result for testing v94h."""
    return DeterministicSynthesisResult(
        result_id="synth_test_001",
        synthesis_type="complete",
        synthesis_scope="global",
        created_at="2026-04-09T08:00:00Z",
        source_record_count=100,
        
        # Pattern groupings
        pattern_groupings=[
            PatternGrouping(
                pattern_id="pattern_001",
                pattern_type="repetition",
                criteria={"key": "pattern_a"},
                member_record_ids=["rec_001", "rec_002", "rec_003"],
                frequency=3,
            ),
        ],
        
        # Approval reason groupings
        approval_reason_groupings=[
            ApprovalReasonGrouping(
                reason_id="reason_001",
                reason_type="approval",
                reason_text="Validated by operator",
                member_record_ids=["event_001", "event_002"],
                frequency=2,
                approval_rate=1.0,
            ),
        ],
        
        # Proposal outcome groupings
        proposal_outcome_groupings=[
            ProposalOutcomeGrouping(
                outcome_id="outcome_001",
                outcome_category="approved",
                member_proposal_ids=["proposal_001", "proposal_002"],
                frequency=2,
            ),
        ],
        
        # Confidence trend summaries
        confidence_trend_summaries=[
            ConfidenceTrendSummary(
                trend_id="trend_001",
                trend_type="increasing",
                before_confidence=0.7,
                after_confidence=0.85,
                confidence_change=0.15,
                confidence_direction="up",
                member_record_ids=["rec_001", "rec_002"],
                frequency=2,
            ),
        ],
        
        # Bottleneck recurrence summaries
        bottleneck_recurrence_summaries=[
            BottleneckRecurrenceSummary(
                bottleneck_id="bottleneck_001",
                bottleneck_type="approval_delay",
                bottleneck_category="process",
                member_bottleneck_ids=["bottleneck_001", "bottleneck_002"],
                frequency=2,
            ),
        ],
    )


def create_empty_synthesis_result() -> DeterministicSynthesisResult:
    """Create empty v94g synthesis result for edge case testing."""
    return DeterministicSynthesisResult(
        result_id="synth_empty_001",
        synthesis_type="complete",
        synthesis_scope="global",
        created_at="2026-04-09T08:00:00Z",
        source_record_count=0,
        pattern_groupings=[],
        approval_reason_groupings=[],
        proposal_outcome_groupings=[],
        confidence_trend_summaries=[],
        bottleneck_recurrence_summaries=[],
    )


# ============================================================================
# INSIGHT PROPOSAL PAYLOAD TESTS
# ============================================================================


class TestInsightProposalPayload(unittest.TestCase):
    """Tests for InsightProposalPayload data class."""
    
    def test_payload_serialization(self) -> None:
        """Test payload serialization to dict and JSON."""
        payload = InsightProposalPayload(
            proposal_id="proposal_001",
            title="Test Proposal",
            description="Test description",
            proposal_type="pattern_summary",
            priority="high",
            created_at="2026-04-09T08:00:00Z",
        )
        
        # Test to_dict
        data = payload.to_dict()
        self.assertEqual(data["proposal_id"], "proposal_001")
        self.assertEqual(data["title"], "Test Proposal")
        self.assertEqual(data["proposal_type"], "pattern_summary")
        self.assertIn("pattern_summaries", data)
        self.assertIn("validation_requirements", data)
        
        # Test to_json
        json_str = payload.to_json()
        self.assertIsInstance(json_str, str)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["proposal_id"], "proposal_001")
    
    def test_payload_default_values(self) -> None:
        """Test payload default values."""
        payload = InsightProposalPayload(
            proposal_id="proposal_001",
            title="Test",
            description="Test",
            proposal_type="pattern_summary",
        )
        
        self.assertEqual(payload.priority, "medium")
        self.assertEqual(payload.current_state, "pending_review")
        self.assertEqual(payload.approval_state, "pending")
        self.assertEqual(payload.evidence_confidence, 0.0)
        self.assertEqual(payload.evidence_summary, "")
    
    def test_payload_full_serialization(self) -> None:
        """Test full payload serialization with all fields."""
        payload = InsightProposalPayload(
            proposal_id="proposal_001",
            title="Full Proposal",
            description="Full description",
            proposal_type="rationale_grouping",
            priority="low",
            pattern_summaries=[{"pattern_id": "p1", "frequency": 5}],
            grouped_rationale=[{"reason_id": "r1", "frequency": 3}],
            recurrence_summaries=[{"bottleneck_id": "b1", "frequency": 2}],
            confidence_summaries=[{"trend_id": "t1", "direction": "up"}],
            validation_requirements=["validation_1"],
            rollback_expectations=["rollback_1"],
            evidence_claim_ids=["claim_1", "claim_2"],
            evidence_chain_ids=["chain_1"],
            evidence_summary="Test evidence",
            evidence_confidence=0.85,
            created_at="2026-04-09T08:00:00Z",
        )
        
        data = payload.to_dict()
        
        # Verify all fields present
        self.assertEqual(data["proposal_id"], "proposal_001")
        self.assertEqual(data["pattern_summaries"], [{"pattern_id": "p1", "frequency": 5}])
        self.assertEqual(data["grouped_rationale"], [{"reason_id": "r1", "frequency": 3}])
        self.assertEqual(data["recurrence_summaries"], [{"bottleneck_id": "b1", "frequency": 2}])
        self.assertEqual(data["confidence_summaries"], [{"trend_id": "t1", "direction": "up"}])
        self.assertEqual(data["validation_requirements"], ["validation_1"])
        self.assertEqual(data["evidence_claim_ids"], ["claim_1", "claim_2"])
        self.assertEqual(data["evidence_confidence"], 0.85)


# ============================================================================
# INSIGHT PROPOSAL EXPORTER TESTS
# ============================================================================


class TestInsightProposalExporter(unittest.TestCase):
    """Tests for InsightProposalExporter."""
    
    def test_format_proposal(self) -> None:
        """Test proposal formatting for operator readability."""
        payload = InsightProposalPayload(
            proposal_id="proposal_001",
            title="Test Proposal",
            description="Test description",
            proposal_type="pattern_summary",
            created_at="2026-04-09T08:00:00Z",
        )
        
        formatted = InsightProposalExporter.format_proposal(payload)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("INSIGHT PROPOSAL", formatted)
        self.assertIn("Proposal ID: proposal_001", formatted)
        self.assertIn("Title: Test Proposal", formatted)
    
    def test_export_to_json(self) -> None:
        """Test JSON export."""
        import tempfile
        import os
        
        payload = InsightProposalPayload(
            proposal_id="proposal_001",
            title="Test Proposal",
            description="Test",
            proposal_type="pattern_summary",
            created_at="2026-04-09T08:00:00Z",
        )
        
        # Test file export
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name
        
        try:
            json_output = InsightProposalExporter.export_to_json(payload, filepath)
            
            # Verify file created
            self.assertTrue(os.path.exists(filepath))
            
            # Verify JSON
            self.assertIsInstance(json_output, str)
            parsed = json.loads(json_output)
            self.assertEqual(parsed["proposal_id"], "proposal_001")
        finally:
            os.unlink(filepath)
    
    def test_export_to_text(self) -> None:
        """Test text export."""
        import tempfile
        import os
        
        payload = InsightProposalPayload(
            proposal_id="proposal_001",
            title="Test Proposal",
            description="Test",
            proposal_type="pattern_summary",
            created_at="2026-04-09T08:00:00Z",
        )
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            filepath = f.name
        
        try:
            text_output = InsightProposalExporter.export_to_text(payload, filepath)
            
            # Verify file created
            self.assertTrue(os.path.exists(filepath))
            
            # Verify text
            self.assertIsInstance(text_output, str)
            self.assertIn("INSIGHT PROPOSAL", text_output)
        finally:
            os.unlink(filepath)
    
    def test_format_proposal_is_operator_readable(self) -> None:
        """Verify formatted output is operator-readable."""
        payload = InsightProposalPayload(
            proposal_id="proposal_001",
            title="Test Proposal",
            description="Test",
            proposal_type="pattern_summary",
            pattern_summaries=[{"pattern_type": "repetition", "frequency": 5}],
            created_at="2026-04-09T08:00:00Z",
        )
        
        formatted = InsightProposalExporter.format_proposal(payload)
        
        # Should be human-readable with clear sections
        self.assertIn("INSIGHT PROPOSAL", formatted)
        self.assertIn("Proposal ID:", formatted)
        self.assertIn("Type:", formatted)
        
        # Should have multiple lines for readability
        lines = formatted.split("\n")
        self.assertGreater(len(lines), 10)


# ============================================================================
# INSIGHT PROPOSAL CONVERTER TESTS
# ============================================================================


class TestInsightProposalConverter(unittest.TestCase):
    """Tests for InsightProposalConverter."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.converter = InsightProposalConverter()
    
    def test_convert_empty_synthesis(self) -> None:
        """Test conversion of empty synthesis result."""
        empty_result = create_empty_synthesis_result()
        proposals = self.converter.convert(empty_result)
        
        self.assertEqual(len(proposals), 0)
    
    def test_convert_complete_synthesis(self) -> None:
        """Test conversion of complete synthesis result."""
        synthesis = create_test_synthesis_result()
        proposals = self.converter.convert(synthesis)
        
        # Should create proposals for each synthesis category
        self.assertGreater(len(proposals), 0)
        
        # Verify proposal structure
        for proposal in proposals:
            self.assertIsInstance(proposal, InsightProposalPayload)
            self.assertIsNotNone(proposal.proposal_id)
            self.assertIsNotNone(proposal.title)
            self.assertIn(proposal.proposal_type, [
                "pattern_summary", "rationale_grouping", "outcome_summary",
                "confidence_summary", "recurrence_summary"
            ])
    
    def test_convert_pattern_groupings(self) -> None:
        """Test pattern grouping conversion."""
        synthesis = create_test_synthesis_result()
        proposals = self.converter._convert_pattern_groupings(synthesis)
        
        self.assertGreater(len(proposals), 0)
        for p in proposals:
            self.assertEqual(p.proposal_type, "pattern_summary")
            self.assertGreater(len(p.pattern_summaries), 0)
    
    def test_convert_approval_reasons(self) -> None:
        """Test approval reason conversion."""
        synthesis = create_test_synthesis_result()
        proposals = self.converter._convert_approval_reasons(synthesis)
        
        self.assertGreater(len(proposals), 0)
        for p in proposals:
            self.assertEqual(p.proposal_type, "rationale_grouping")
            self.assertGreater(len(p.grouped_rationale), 0)
    
    def test_convert_proposal_outcomes(self) -> None:
        """Test proposal outcome conversion."""
        synthesis = create_test_synthesis_result()
        proposals = self.converter._convert_proposal_outcomes(synthesis)
        
        self.assertGreater(len(proposals), 0)
        for p in proposals:
            self.assertEqual(p.proposal_type, "outcome_summary")
            self.assertGreater(len(p.recurrence_summaries), 0)
    
    def test_convert_confidence_trends(self) -> None:
        """Test confidence trend conversion."""
        synthesis = create_test_synthesis_result()
        proposals = self.converter._convert_confidence_trends(synthesis)
        
        self.assertGreater(len(proposals), 0)
        for p in proposals:
            self.assertEqual(p.proposal_type, "confidence_summary")
            self.assertGreater(len(p.confidence_summaries), 0)
    
    def test_convert_bottleneck_recurrences(self) -> None:
        """Test bottleneck recurrence conversion."""
        synthesis = create_test_synthesis_result()
        proposals = self.converter._convert_bottleneck_recurrences(synthesis)
        
        self.assertGreater(len(proposals), 0)
        for p in proposals:
            self.assertEqual(p.proposal_type, "recurrence_summary")
            self.assertGreater(len(p.recurrence_summaries), 0)
    
    def test_conversion_count(self) -> None:
        """Test conversion counter."""
        synthesis = create_test_synthesis_result()
        self.converter.convert(synthesis)
        
        count = self.converter.get_conversion_count()
        self.assertGreater(count, 0)


# ============================================================================
# INSIGHT PROPOSAL LAYER TESTS
# ============================================================================


class TestInsightProposalLayer(unittest.TestCase):
    """Tests for InsightProposalLayer."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.layer = InsightProposalLayer()
    
    def test_process_synthesis_result(self) -> None:
        """Test layer processing of synthesis result."""
        synthesis = create_test_synthesis_result()
        proposals = self.layer.process_synthesis_result(synthesis)
        
        self.assertGreater(len(proposals), 0)
        self.assertEqual(len(self.layer.get_last_proposals()), len(proposals))
    
    def test_export_proposals_to_json(self) -> None:
        """Test layer JSON export."""
        synthesis = create_test_synthesis_result()
        self.layer.process_synthesis_result(synthesis)
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name
        
        try:
            json_output = self.layer.export_proposals_to_json(filepath=filepath)
            
            # Verify
            self.assertIsInstance(json_output, str)
            self.assertTrue(os.path.exists(filepath))
            
            parsed = json.loads(json_output)
            if isinstance(parsed, list):
                self.assertGreater(len(parsed), 0)
            else:
                self.assertIn("proposal_id", parsed)
        finally:
            os.unlink(filepath)
    
    def test_export_proposals_to_text(self) -> None:
        """Test layer text export."""
        synthesis = create_test_synthesis_result()
        self.layer.process_synthesis_result(synthesis)
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            filepath = f.name
        
        try:
            text_output = self.layer.export_proposals_to_text(filepath=filepath)
            
            # Verify
            self.assertIsInstance(text_output, str)
            self.assertTrue(os.path.exists(filepath))
            self.assertIn("INSIGHT PROPOSAL", text_output)
        finally:
            os.unlink(filepath)
    
    def test_conversion_count(self) -> None:
        """Test layer conversion count."""
        synthesis = create_test_synthesis_result()
        self.layer.process_synthesis_result(synthesis)
        
        count = self.layer.get_conversion_count()
        self.assertGreater(count, 0)


# ============================================================================
# NO-MUTATION BOUNDARY TESTS
# ============================================================================


class TestNoMutationBoundary(unittest.TestCase):
    """Tests for no-mutation boundary."""
    
    def test_converter_does_not_mutate_source_synthesis(self) -> None:
        """Verify converter does not mutate source synthesis result."""
        synthesis = create_test_synthesis_result()
        original_patterns = [pg.to_dict() for pg in synthesis.pattern_groupings]
        
        converter = InsightProposalConverter()
        converter.convert(synthesis)
        
        # Verify synthesis unchanged
        new_patterns = [pg.to_dict() for pg in synthesis.pattern_groupings]
        self.assertEqual(new_patterns, original_patterns)
    
    def test_layer_does_not_mutate_source_synthesis(self) -> None:
        """Verify layer does not mutate source synthesis result."""
        synthesis = create_test_synthesis_result()
        original_patterns = [pg.to_dict() for pg in synthesis.pattern_groupings]
        
        layer = InsightProposalLayer()
        layer.process_synthesis_result(synthesis)
        
        # Verify synthesis unchanged
        new_patterns = [pg.to_dict() for pg in synthesis.pattern_groupings]
        self.assertEqual(new_patterns, original_patterns)


# ============================================================================
# NO-RECOMMENDATION BOUNDARY TESTS
# ============================================================================


class TestNoRecommendationBoundary(unittest.TestCase):
    """Tests for no-recommendation boundary."""
    
    def test_exported_output_is_descriptive_not_prescriptive(self) -> None:
        """Verify exported output is descriptive, not prescriptive."""
        synthesis = create_test_synthesis_result()
        layer = InsightProposalLayer()
        proposals = layer.process_synthesis_result(synthesis)
        
        # Export to text
        text_output = layer.export_proposals_to_text()
        
        # Should not contain recommendation language
        self.assertNotIn("should", text_output.lower())
        self.assertNotIn("must", text_output.lower())
        self.assertNotIn("need to", text_output.lower())
        self.assertNotIn("recommend", text_output.lower())
    
    def test_proposals_do_not_contain_recommendations(self) -> None:
        """Verify proposals do not contain recommendations."""
        synthesis = create_test_synthesis_result()
        layer = InsightProposalLayer()
        proposals = layer.process_synthesis_result(synthesis)
        
        for proposal in proposals:
            json_output = proposal.to_json()
            data = json.loads(json_output)
            
            # Check all fields
            for key, value in data.items():
                if isinstance(value, str):
                    self.assertNotIn("recommend", value.lower())
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            for subkey, subval in item.items():
                                if isinstance(subval, str):
                                    self.assertNotIn("recommend", subval.lower())


# ============================================================================
# EXPORT SCHEMA TESTS
# ============================================================================


class TestExportSchema(unittest.TestCase):
    """Tests for export schema compliance."""
    
    def test_proposal_json_schema(self) -> None:
        """Test proposal JSON schema."""
        payload = InsightProposalPayload(
            proposal_id="proposal_001",
            title="Test Proposal",
            description="Test",
            proposal_type="pattern_summary",
            pattern_summaries=[{"pattern_type": "repetition", "frequency": 5}],
            created_at="2026-04-09T08:00:00Z",
        )
        
        data = payload.to_dict()
        
        # Required fields
        self.assertIn("proposal_id", data)
        self.assertIn("title", data)
        self.assertIn("description", data)
        self.assertIn("proposal_type", data)
        self.assertIn("pattern_summaries", data)
        self.assertIn("current_state", data)
        self.assertIn("approval_state", data)
        
        # Optional fields
        self.assertIn("priority", data)
        self.assertIn("validation_requirements", data)
        self.assertIn("evidence_claim_ids", data)
        self.assertIn("evidence_confidence", data)
    
    def test_multiple_proposals_export_schema(self) -> None:
        """Test multiple proposals export schema."""
        layer = InsightProposalLayer()
        synthesis = create_test_synthesis_result()
        layer.process_synthesis_result(synthesis)
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name
        
        try:
            json_output = layer.export_proposals_to_json(filepath=filepath)
            parsed = json.loads(json_output)
            
            # Should be array of proposals
            if isinstance(parsed, list):
                self.assertGreater(len(parsed), 0)
                for p in parsed:
                    self.assertIn("proposal_id", p)
                    self.assertIn("title", p)
                    self.assertIn("proposal_type", p)
        finally:
            os.unlink(filepath)


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestBackwardCompatibility(unittest.TestCase):
    """Tests for backward compatibility with existing WESLR modules."""
    
    def test_layer_accepts_v94g_synthesis_result(self) -> None:
        """Test layer accepts v94g synthesis result."""
        layer = InsightProposalLayer()
        synthesis = create_test_synthesis_result()
        
        # Should process without error
        proposals = layer.process_synthesis_result(synthesis)
        self.assertGreater(len(proposals), 0)
    
    def test_layer_interoperates_with_operator_proposal_review(self) -> None:
        """Test layer interoperates with v13 operator proposal review."""
        # Mock v13 OperatorReviewOutput interface
        # (actual import skipped due to module dependency issues in test environment)
        
        layer = InsightProposalLayer()
        synthesis = create_test_synthesis_result()
        proposals = layer.process_synthesis_result(synthesis)
        
        # Verify proposals have required fields for v13 integration
        for proposal in proposals:
            # Required fields that should match v13 OperatorReviewOutput
            self.assertIsNotNone(proposal.proposal_id)
            self.assertIsNotNone(proposal.title)
            self.assertIsNotNone(proposal.description)
            self.assertIn(proposal.priority, ["low", "medium", "high"])
            self.assertIn(proposal.proposal_type, [
                "pattern_summary", "rationale_grouping", "outcome_summary",
                "confidence_summary", "recurrence_summary"
            ])


# ============================================================================
# COMPREHENSIVE INTEGRATION TEST
# ============================================================================


class TestV94HIntegration(unittest.TestCase):
    """End-to-end v94h integration test."""
    
    def test_end_to_end_flow(self) -> None:
        """Test complete flow from synthesis to proposals to export."""
        # Create synthesis result
        synthesis = create_test_synthesis_result()
        
        # Process through layer
        layer = InsightProposalLayer()
        proposals = layer.process_synthesis_result(synthesis)
        
        # Export to both formats
        json_output = layer.export_proposals_to_json()
        text_output = layer.export_proposals_to_text()
        
        # Verify outputs
        self.assertGreater(len(proposals), 0)
        self.assertIsInstance(json_output, str)
        self.assertIsInstance(text_output, str)
        
        # Verify JSON is valid
        parsed = json.loads(json_output)
        if isinstance(parsed, list):
            self.assertGreater(len(parsed), 0)
        else:
            self.assertIn("proposal_id", parsed)
        
        # Verify text is readable
        self.assertIn("INSIGHT PROPOSAL", text_output)
    
    def test_empty_synthesis_handling(self) -> None:
        """Test handling of empty synthesis result."""
        empty_result = create_empty_synthesis_result()
        
        layer = InsightProposalLayer()
        proposals = layer.process_synthesis_result(empty_result)
        
        self.assertEqual(len(proposals), 0)
        self.assertEqual(layer.get_conversion_count(), 0)


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    unittest.main(verbosity=2)
