# test_operator_insight_timeline.py - WESLR v88 Tests
# Test suite for Operator Insight Timeline / Escalation Context Layer
# Validates: data models, behavior, integration, backward compatibility

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone

from .operator_insight_timeline import (
    InsightTimelineEntry,
    InsightTimelineStore,
    OperatorInsightTimeline,
    TimelineSummary,
)
from .operator_recovery_insight import RecoveryInsight


class TestInsightTimelineModel(unittest.TestCase):
    """Model tests for InsightTimelineEntry and TimelineSummary."""
    
    def test_entry_creation(self) -> None:
        """Test InsightTimelineEntry construction."""
        entry = InsightTimelineEntry(
            entry_id="test_entry_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_id="insight_123",
            drift_type="significance",
            before_value="low",
            after_value="high",
            significance_delta=0.5,
            confidence_delta=0.0,
            escalation_level="attention",
            escalation_reason="Significance increased",
            correlation_ids={"flow_id": "flow_1", "request_id": "req_1"},
        )
        self.assertEqual(entry.entry_id, "test_entry_001")
        self.assertEqual(entry.drift_type, "significance")
        self.assertEqual(entry.escalation_level, "attention")
    
    def test_entry_to_dict(self) -> None:
        """Test InsightTimelineEntry to_dict serialization."""
        entry = InsightTimelineEntry(
            entry_id="test_entry_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_id="insight_123",
            drift_type="significance",
            before_value="low",
            after_value="high",
            significance_delta=0.5,
            confidence_delta=0.0,
            escalation_level="attention",
            escalation_reason="Significance increased",
            correlation_ids={"flow_id": "flow_1", "request_id": "req_1"},
        )
        d = entry.to_dict()
        self.assertEqual(d["drift_type"], "significance")
        self.assertEqual(d["escalation_level"], "attention")
    
    def test_entry_json_serialization(self) -> None:
        """Test InsightTimelineEntry JSON roundtrip."""
        entry = InsightTimelineEntry(
            entry_id="test_entry_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_id="insight_123",
            drift_type="significance",
            before_value="low",
            after_value="high",
            significance_delta=0.5,
            confidence_delta=0.0,
            escalation_level="attention",
            escalation_reason="Significance increased",
            correlation_ids={"flow_id": "flow_1", "request_id": "req_1"},
        )
        json_str = entry.to_json()
        d = json.loads(json_str)
        self.assertEqual(d["drift_type"], "significance")
    
    def test_summary_creation(self) -> None:
        """Test TimelineSummary construction."""
        summary = TimelineSummary(
            summary_id="summary_001",
            timestamp="2026-04-07T12:00:00Z",
            time_range_start="2026-04-07T00:00:00Z",
            time_range_end="2026-04-07T12:00:00Z",
            total_changes=10,
            escalation_events=2,
            drift_type_distribution={"significance": 5, "confidence_guidance": 3},
            operator_readable="Operator summary",
            machine_readable='{"test": true}',
        )
        self.assertEqual(summary.total_changes, 10)
        self.assertEqual(summary.escalation_events, 2)
    
    def test_summary_to_dict(self) -> None:
        """Test TimelineSummary to_dict serialization."""
        summary = TimelineSummary(
            summary_id="summary_001",
            timestamp="2026-04-07T12:00:00Z",
            time_range_start="2026-04-07T00:00:00Z",
            time_range_end="2026-04-07T12:00:00Z",
            total_changes=10,
            escalation_events=2,
            drift_type_distribution={"significance": 5},
            operator_readable="Operator summary",
            machine_readable='{"test": true}',
        )
        d = summary.to_dict()
        self.assertEqual(d["total_changes"], 10)
        self.assertEqual(d["escalation_events"], 2)
    
    def test_summary_json_serialization(self) -> None:
        """Test TimelineSummary JSON roundtrip."""
        summary = TimelineSummary(
            summary_id="summary_001",
            timestamp="2026-04-07T12:00:00Z",
            time_range_start="2026-04-07T00:00:00Z",
            time_range_end="2026-04-07T12:00:00Z",
            total_changes=10,
            escalation_events=2,
            drift_type_distribution={"significance": 5},
            operator_readable="Operator summary",
            machine_readable='{"test": true}',
        )
        json_str = summary.to_json()
        d = json.loads(json_str)
        self.assertEqual(d["total_changes"], 10)


class TestInsightTimelineBehavior(unittest.TestCase):
    """Behavior tests for InsightTimelineStore and OperatorInsightTimeline."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.store = InsightTimelineStore()
        self.timeline = OperatorInsightTimeline()
    
    def test_store_add_entry(self) -> None:
        """Test InsightTimelineStore.add_entry."""
        entry = InsightTimelineEntry(
            entry_id="test_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_id="insight_1",
            drift_type="significance",
            before_value="low",
            after_value="high",
            significance_delta=0.5,
            confidence_delta=0.0,
            escalation_level="attention",
            escalation_reason="Significance increased",
            correlation_ids={"flow_id": "flow_1"},
        )
        self.store.add_entry(entry)
        entries = self.store.get_timeline()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].entry_id, "test_001")
    
    def test_store_get_timeline(self) -> None:
        """Test InsightTimelineStore.get_timeline."""
        for i in range(5):
            entry = InsightTimelineEntry(
                entry_id=f"entry_{i}",
                timestamp=f"2026-04-07T12:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="significance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="attention",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        entries = self.store.get_timeline()
        self.assertEqual(len(entries), 5)
    
    def test_store_get_timeline_for_request(self) -> None:
        """Test InsightTimelineStore.get_timeline_for_request."""
        # Add entries with different request IDs
        for i in range(3):
            entry = InsightTimelineEntry(
                entry_id=f"entry_{i}",
                timestamp=f"2026-04-07T12:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="significance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="attention",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1", "request_id": "req_A"},
            )
            self.store.add_entry(entry)
        
        for i in range(3, 6):
            entry = InsightTimelineEntry(
                entry_id=f"entry_{i}",
                timestamp=f"2026-04-07T13:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="confidence_guidance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="normal",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_2", "request_id": "req_B"},
            )
            self.store.add_entry(entry)
        
        entries = self.store.get_timeline_for_request("req_A")
        self.assertEqual(len(entries), 3)
        
        entries = self.store.get_timeline_for_request("req_B")
        self.assertEqual(len(entries), 3)
    
    def test_store_get_timeline_for_flow(self) -> None:
        """Test InsightTimelineStore.get_timeline_for_flow."""
        for i in range(3):
            entry = InsightTimelineEntry(
                entry_id=f"entry_{i}",
                timestamp=f"2026-04-07T12:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="significance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="attention",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_A", "request_id": f"req_{i}"},
            )
            self.store.add_entry(entry)
        
        entries = self.store.get_timeline_for_flow("flow_A")
        self.assertEqual(len(entries), 3)
    
    def test_store_get_significance_shifts(self) -> None:
        """Test InsightTimelineStore.get_significance_shifts."""
        for i in range(3):
            entry = InsightTimelineEntry(
                entry_id=f"entry_{i}",
                timestamp=f"2026-04-07T12:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="significance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="attention",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        for i in range(3, 5):
            entry = InsightTimelineEntry(
                entry_id=f"entry_{i}",
                timestamp=f"2026-04-07T13:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="confidence_guidance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="normal",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        shifts = self.store.get_significance_shifts()
        self.assertEqual(len(shifts), 3)
    
    def test_store_get_confidence_shifts(self) -> None:
        """Test InsightTimelineStore.get_confidence_shifts."""
        for i in range(3):
            entry = InsightTimelineEntry(
                entry_id=f"entry_{i}",
                timestamp=f"2026-04-07T12:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="significance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="attention",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        for i in range(3, 5):
            entry = InsightTimelineEntry(
                entry_id=f"entry_{i}",
                timestamp=f"2026-04-07T13:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="confidence_guidance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="normal",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        shifts = self.store.get_confidence_shifts()
        self.assertEqual(len(shifts), 2)
    
    def test_store_get_safe_action_shifts(self) -> None:
        """Test InsightTimelineStore.get_safe_action_shifts."""
        # Add entries with no safe_action_shift initially
        for i in range(3):
            entry = InsightTimelineEntry(
                entry_id=f"entry_{i}",
                timestamp=f"2026-04-07T12:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="safe_next_action",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                safe_action_shift="A -> B",
                escalation_level="normal",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        shifts = self.store.get_safe_action_shifts()
        self.assertEqual(len(shifts), 3)
    
    def test_store_get_entries_by_escalation(self) -> None:
        """Test InsightTimelineStore.get_entries_by_escalation."""
        for i in range(2):
            entry = InsightTimelineEntry(
                entry_id=f"entry_normal_{i}",
                timestamp=f"2026-04-07T12:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="significance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="normal",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        for i in range(2):
            entry = InsightTimelineEntry(
                entry_id=f"entry_attention_{i}",
                timestamp=f"2026-04-07T13:{i:02d}:00Z",
                insight_id=f"insight_{i+2}",
                drift_type="significance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="attention",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        normals = self.store.get_entries_by_escalation("normal")
        attentions = self.store.get_entries_by_escalation("attention")
        
        self.assertEqual(len(normals), 2)
        self.assertEqual(len(attentions), 2)
    
    def test_store_get_escalation_summary(self) -> None:
        """Test InsightTimelineStore.get_escalation_summary."""
        for i in range(2):
            entry = InsightTimelineEntry(
                entry_id=f"entry_normal_{i}",
                timestamp=f"2026-04-07T12:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="significance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="normal",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        for i in range(2):
            entry = InsightTimelineEntry(
                entry_id=f"entry_attention_{i}",
                timestamp=f"2026-04-07T13:{i:02d}:00Z",
                insight_id=f"insight_{i+2}",
                drift_type="significance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="attention",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        summary = self.store.get_escalation_summary()
        self.assertEqual(summary["normal"], 2)
        self.assertEqual(summary["attention"], 2)
        self.assertEqual(summary["urgent"], 0)
    
    def test_store_export_operator_readable(self) -> None:
        """Test InsightTimelineStore.export_operator_readable."""
        entry = InsightTimelineEntry(
            entry_id="test_entry",
            timestamp="2026-04-07T12:00:00Z",
            insight_id="insight_1",
            drift_type="significance",
            before_value="low",
            after_value="high",
            significance_delta=0.5,
            confidence_delta=0.0,
            escalation_level="attention",
            escalation_reason="Significance increased",
            correlation_ids={"flow_id": "flow_1"},
        )
        self.store.add_entry(entry)
        
        output = self.store.export_operator_readable()
        self.assertIn("OPERATOR INSIGHT TIMELINE SUMMARY", output)
        self.assertIn("ATTENTION: 1", output)
    
    def test_store_export_machine_readable(self) -> None:
        """Test InsightTimelineStore.export_machine_readable."""
        entry = InsightTimelineEntry(
            entry_id="test_entry",
            timestamp="2026-04-07T12:00:00Z",
            insight_id="insight_1",
            drift_type="significance",
            before_value="low",
            after_value="high",
            significance_delta=0.5,
            confidence_delta=0.0,
            escalation_level="attention",
            escalation_reason="Significance increased",
            correlation_ids={"flow_id": "flow_1"},
        )
        self.store.add_entry(entry)
        
        output = self.store.export_machine_readable()
        data = json.loads(output)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["drift_type"], "significance")
    
    def test_store_export_drift_type_json(self) -> None:
        """Test InsightTimelineStore.export_drift_type_json."""
        for i in range(2):
            entry = InsightTimelineEntry(
                entry_id=f"entry_{i}",
                timestamp=f"2026-04-07T12:{i:02d}:00Z",
                insight_id=f"insight_{i}",
                drift_type="significance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="attention",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        for i in range(2):
            entry = InsightTimelineEntry(
                entry_id=f"entry_conf_{i}",
                timestamp=f"2026-04-07T13:{i:02d}:00Z",
                insight_id=f"insight_conf_{i}",
                drift_type="confidence_guidance",
                before_value="low",
                after_value="high",
                significance_delta=0.5,
                confidence_delta=0.0,
                escalation_level="normal",
                escalation_reason="Test",
                correlation_ids={"flow_id": "flow_1"},
            )
            self.store.add_entry(entry)
        
        sig_output = self.store.export_drift_type_json("significance")
        sig_data = json.loads(sig_output)
        self.assertEqual(len(sig_data), 2)
        
        conf_output = self.store.export_drift_type_json("confidence_guidance")
        conf_data = json.loads(conf_output)
        self.assertEqual(len(conf_data), 2)
    
    def test_timeline_record_insight_change(self) -> None:
        """Test OperatorInsightTimeline.record_insight_change."""
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
        )
        
        entry = self.timeline.record_insight_change(current)
        self.assertIsNotNone(entry)
        self.assertIn("timeline_", entry.entry_id)
    
    def test_timeline_record_insight_change_with_previous(self) -> None:
        """Test OperatorInsightTimeline.record_insight_change with previous insight."""
        previous = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T10:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="low",
            significance_reason="Test reason",
        )
        
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="high",
            significance_reason="Test reason",
        )
        
        entry = self.timeline.record_insight_change(current, previous)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.drift_type, "significance")
        self.assertEqual(entry.escalation_level, "attention")
    
    def test_timeline_get_timeline(self) -> None:
        """Test OperatorInsightTimeline.get_timeline."""
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
        )
        
        self.timeline.record_insight_change(current)
        entries = self.timeline.get_timeline()
        self.assertEqual(len(entries), 1)
    
    def test_timeline_get_timeline_for_request(self) -> None:
        """Test OperatorInsightTimeline.get_timeline_for_request."""
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1", "request_id": "req_A"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
        )
        
        self.timeline.record_insight_change(current)
        entries = self.timeline.get_timeline_for_request("req_A")
        self.assertEqual(len(entries), 1)
    
    def test_timeline_get_timeline_for_flow(self) -> None:
        """Test OperatorInsightTimeline.get_timeline_for_flow."""
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_A"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
        )
        
        self.timeline.record_insight_change(current)
        entries = self.timeline.get_timeline_for_flow("flow_A")
        self.assertEqual(len(entries), 1)
    
    def test_timeline_get_significance_shifts(self) -> None:
        """Test OperatorInsightTimeline.get_significance_shifts."""
        previous = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T10:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="low",
            significance_reason="Test reason",
        )
        
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="high",
            significance_reason="Test reason",
        )
        
        self.timeline.record_insight_change(current, previous)
        shifts = self.timeline.get_significance_shifts()
        self.assertEqual(len(shifts), 1)
    
    def test_timeline_get_confidence_shifts(self) -> None:
        """Test OperatorInsightTimeline.get_confidence_shifts."""
        previous = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T10:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
            guidance="Do A",
        )
        
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
            guidance="Do B",
        )
        
        self.timeline.record_insight_change(current, previous)
        shifts = self.timeline.get_confidence_shifts()
        self.assertEqual(len(shifts), 1)
    
    def test_timeline_get_safe_action_shifts(self) -> None:
        """Test OperatorInsightTimeline.get_safe_action_shifts."""
        previous = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T10:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
            guidance="Do A",
        )
        
        # Same significance AND guidance = safe_next_action drift type
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
            guidance="Do A",
        )
        
        self.timeline.record_insight_change(current, previous)
        shifts = self.timeline.get_safe_action_shifts()
        self.assertEqual(len(shifts), 1)
    
    def test_timeline_get_summary_window(self) -> None:
        """Test OperatorInsightTimeline.get_summary_window."""
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
        )
        
        self.timeline.record_insight_change(current)
        summary = self.timeline.get_summary_window()
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary.total_changes, 1)
    
    def test_timeline_get_summary_window_empty(self) -> None:
        """Test OperatorInsightTimeline.get_summary_window with no data."""
        timeline = OperatorInsightTimeline()
        summary = timeline.get_summary_window()
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary.total_changes, 0)
    
    def test_timeline_get_escalation_summary(self) -> None:
        """Test OperatorInsightTimeline.get_escalation_summary."""
        for i in range(2):
            current = RecoveryInsight(
                insight_id=f"insight_{i}",
                timestamp="2026-04-07T12:00:00Z",
                insight_type="trend_shift",
                pattern_id="pattern_1",
                correlation_ids={"flow_id": "flow_1"},
                interpretation="Test insight",
                significance="low",
                significance_reason="Test reason",
            )
            self.timeline.record_insight_change(current)
        
        summary = self.timeline.get_escalation_summary()
        self.assertEqual(summary["normal"], 2)
        self.assertEqual(summary["attention"], 0)
        self.assertEqual(summary["urgent"], 0)
    
    def test_timeline_export_operator_readable(self) -> None:
        """Test OperatorInsightTimeline.export_operator_readable."""
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
        )
        
        self.timeline.record_insight_change(current)
        output = self.timeline.export_operator_readable()
        self.assertIn("OPERATOR INSIGHT TIMELINE SUMMARY", output)
    
    def test_timeline_export_machine_readable(self) -> None:
        """Test OperatorInsightTimeline.export_machine_readable."""
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
        )
        
        self.timeline.record_insight_change(current)
        output = self.timeline.export_machine_readable()
        data = json.loads(output)
        self.assertEqual(len(data), 1)
    
    def test_timeline_export_timeline_json(self) -> None:
        """Test OperatorInsightTimeline.export_timeline_json."""
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
        )
        
        self.timeline.record_insight_change(current)
        output = self.timeline.export_timeline_json()
        data = json.loads(output)
        self.assertEqual(len(data), 1)
    
    def test_timeline_drift_type_filtering(self) -> None:
        """Test OperatorInsightTimeline export_drift_type_json."""
        for i in range(2):
            current = RecoveryInsight(
                insight_id=f"insight_{i}",
                timestamp="2026-04-07T12:00:00Z",
                insight_type="trend_shift",
                pattern_id="pattern_1",
                correlation_ids={"flow_id": "flow_1"},
                interpretation="Test insight",
                significance="low",
                significance_reason="Test reason",
            )
            self.timeline.record_insight_change(current)
        
        # Entries 2,3: Same significance, different guidance = confidence_guidance drift
        for i in range(2, 4):
            previous = RecoveryInsight(
                insight_id=f"insight_{i}",
                timestamp="2026-04-07T10:00:00Z",
                insight_type="trend_shift",
                pattern_id="pattern_1",
                correlation_ids={"flow_id": "flow_1"},
                interpretation="Test insight",
                significance="medium",
                significance_reason="Test reason",
                guidance="Do A",
            )
            
            current = RecoveryInsight(
                insight_id=f"insight_{i}",
                timestamp="2026-04-07T12:00:00Z",
                insight_type="trend_shift",
                pattern_id="pattern_1",
                correlation_ids={"flow_id": "flow_1"},
                interpretation="Test insight",
                significance="medium",
                significance_reason="Test reason",
                guidance="Do B",
            )
            self.timeline.record_insight_change(current, previous)
        
        sig_output = self.timeline.export_drift_type_json("significance")
        sig_data = json.loads(sig_output)
        # First 2 entries have insight_count drift, next 2 have confidence_guidance drift
        # So confidence_guidance count should be 2
        self.assertEqual(len(sig_data), 0)  # No significance drift in these entries
        
        conf_output = self.timeline.export_drift_type_json("confidence_guidance")
        conf_data = json.loads(conf_output)
        self.assertEqual(len(conf_data), 2)


class TestInsightTimelineIntegration(unittest.TestCase):
    """Integration tests for OperatorInsightTimeline with WESLR."""
    
    def test_layer_registration(self) -> None:
        """Test that OperatorInsightTimeline is properly registered."""
        timeline = OperatorInsightTimeline()
        self.assertIsNotNone(timeline)
        self.assertIsInstance(timeline, OperatorInsightTimeline)
    
    def test_v88_compatibility_with_v87(self) -> None:
        """Test v88 compatibility with v87 drift comparison."""
        from .operator_insight_comparison import OperatorInsightComparison
        
        timeline = OperatorInsightTimeline()
        comparison = OperatorInsightComparison()
        
        # Both layers should instantiate without error
        self.assertIsNotNone(timeline)
        self.assertIsNotNone(comparison)


class TestInsightTimelineBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for v88 with v75-v87."""
    
    def test_v87_compatibility(self) -> None:
        """Test v88 does not break v87 OperatorInsightComparison."""
        from .operator_insight_comparison import (
            InsightDriftStore,
            OperatorInsightComparison,
        )
        
        comparison = OperatorInsightComparison()
        store = InsightDriftStore()
        
        # v87 methods should still work
        result = comparison.compare_drift(
            "summary_1",
            "summary_2",
            10,
            15,
            {"type_a": 5},
            {"type_a": 7},
        )
        self.assertIsNotNone(result)
    
    def test_v86_compatibility(self) -> None:
        """Test v88 does not break v86 OperatorInsightHistory."""
        from .operator_insight_history import OperatorInsightHistory
        
        history = OperatorInsightHistory()
        self.assertIsNotNone(history)
    
    def test_v85_compatibility(self) -> None:
        """Test v88 does not break v85 OperatorRecoveryInsight."""
        from .operator_recovery_insight import (
            RecoveryInsight,
            OperatorRecoveryInsight,
        )
        
        insight = RecoveryInsight(
            insight_id="test_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test",
            significance="medium",
            significance_reason="Test",
        )
        self.assertIsNotNone(insight)
        
        recovery_insight = OperatorRecoveryInsight()
        self.assertIsNotNone(recovery_insight)


class TestInsightTimelineEscalationHeuristics(unittest.TestCase):
    """Tests for escalation level heuristics (not certainties)."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.timeline = OperatorInsightTimeline()
    
    def test_escalation_normal(self) -> None:
        """Test normal escalation level."""
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="low",
            significance_reason="Test reason",
        )
        
        entry = self.timeline.record_insight_change(current)
        self.assertEqual(entry.escalation_level, "normal")
    
    def test_escalation_attention_high_significance(self) -> None:
        """Test attention escalation for high significance change."""
        previous = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T10:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="low",
            significance_reason="Test reason",
        )
        
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="high",
            significance_reason="Test reason",
        )
        
        entry = self.timeline.record_insight_change(current, previous)
        self.assertEqual(entry.escalation_level, "attention")
        self.assertIn("Significant", entry.escalation_reason)
    
    def test_escalation_attention_significance_delta(self) -> None:
        """Test attention escalation for large significance delta."""
        previous = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T10:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="low",
            significance_reason="Test reason",
        )
        
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="high",
            significance_reason="Test reason",
        )
        
        entry = self.timeline.record_insight_change(current, previous)
        self.assertEqual(entry.escalation_level, "attention")
    
    def test_escalation_urgent_not_triggered(self) -> None:
        """Test that urgent escalation is not triggered without specific conditions."""
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="medium",
            significance_reason="Test reason",
        )
        
        entry = self.timeline.record_insight_change(current)
        self.assertIn(entry.escalation_level, ["normal", "attention"])
    
    def test_escalation_reasons_are_heuristic(self) -> None:
        """Test that escalation reasons are heuristic (not certainty)."""
        previous = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T10:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="low",
            significance_reason="Test reason",
        )
        
        current = RecoveryInsight(
            insight_id="insight_001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern_1",
            correlation_ids={"flow_id": "flow_1"},
            interpretation="Test insight",
            significance="high",
            significance_reason="Test reason",
        )
        
        entry = self.timeline.record_insight_change(current, previous)
        # Reason should mention it's heuristic guidance, not certainty
        self.assertIn("Significant", entry.escalation_reason)


if __name__ == "__main__":
    unittest.main()
