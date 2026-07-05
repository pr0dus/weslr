"""Tests for ARC-AGI-2 synthetic run log analyzer V1."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from weslr.arc_synthetic_run_log_analyzer_v1 import (
    adversarial_summary,
    analyze_events,
    check_expected_output_leakage,
    check_missing_events,
    check_raw_grid_leakage,
    check_summary_consistency,
    check_task_count_mismatch,
    check_unsafe_metadata,
    count_by_level,
    count_by_phase,
    count_by_type,
    count_exceptions,
    count_fallback,
    count_malformed,
    count_solved_unsolved,
    load_events,
    load_summary,
    split_summaries,
    top_failure_categories,
    top_fallback_families,
)


def _make_event(event_type: str, phase: str = "evaluation", level: str = "INFO",
                metadata: dict | None = None, message: str = "") -> dict:
    return {
        "run_id": "test",
        "timestamp_utc": "2026-07-05T19:00:00.000Z",
        "elapsed_sec": 0.0,
        "level": level,
        "phase": phase,
        "event_type": event_type,
        "message": message,
        "metadata": metadata or {},
    }


class TestCounts:
    def test_counts_by_level(self):
        events = [
            _make_event("run_started", level="INFO"),
            _make_event("task_solved", level="INFO"),
            _make_event("exception", level="ERROR"),
        ]
        counts = count_by_level(events)
        assert counts["INFO"] == 2
        assert counts["ERROR"] == 1

    def test_counts_by_phase(self):
        events = [
            _make_event("run_started", phase="run_start"),
            _make_event("task_solved", phase="evaluation"),
            _make_event("run_finished", phase="run_end"),
        ]
        counts = count_by_phase(events)
        assert counts["run_start"] == 1
        assert counts["evaluation"] == 1

    def test_counts_by_type(self):
        events = [
            _make_event("run_started"),
            _make_event("task_solved"),
            _make_event("task_unsolved"),
            _make_event("run_finished"),
        ]
        counts = count_by_type(events)
        assert counts["run_started"] == 1
        assert counts["task_solved"] == 1
        assert counts["task_unsolved"] == 1


class TestSummaries:
    def test_split_summaries(self):
        events = [
            _make_event("split_summary", metadata={"split_name": "dev", "solved": 5}),
            _make_event("split_summary", metadata={"split_name": "heldout", "solved": 10}),
        ]
        summaries = split_summaries(events)
        assert summaries["dev"]["solved"] == 5
        assert summaries["heldout"]["solved"] == 10

    def test_solved_unsolved(self):
        events = [
            _make_event("task_solved"),
            _make_event("task_solved"),
            _make_event("task_unsolved"),
        ]
        counts = count_solved_unsolved(events)
        assert counts["solved"] == 2
        assert counts["unsolved"] == 1

    def test_fallback(self):
        events = [
            _make_event("fallback_used"),
            _make_event("fallback_used"),
        ]
        counts = count_fallback(events)
        assert counts["fallback_used"] == 2

    def test_malformed(self):
        events = [
            _make_event("malformed_output"),
        ]
        assert count_malformed(events) == 1

    def test_exceptions(self):
        events = [
            _make_event("exception", metadata={"task_id": "t1"}),
            _make_event("exception", metadata={"task_id": "t2"}),
        ]
        excs = count_exceptions(events)
        assert len(excs) == 2

    def test_adversarial_summary(self):
        events = [
            _make_event("adversarial_rejection", metadata={"rejected": True}),
            _make_event("adversarial_rejection", metadata={"rejected": True}),
            _make_event("adversarial_rejection", metadata={"rejected": False}),
        ]
        adv = adversarial_summary(events)
        assert adv["adversarial_rejection_pass"] == 2
        assert adv["adversarial_rejection_fail"] == 1

    def test_top_fallback_families(self):
        events = [
            _make_event("fallback_used", metadata={"family_label": "crop"}),
            _make_event("fallback_used", metadata={"family_label": "crop"}),
            _make_event("fallback_used", metadata={"family_label": "recolor"}),
        ]
        top = top_fallback_families(events)
        assert top[0] == ("crop", 2)

    def test_top_failure_categories(self):
        events = [
            _make_event("task_unsolved", metadata={"failure_category": "wrong_family"}),
            _make_event("task_unsolved", metadata={"failure_category": "wrong_family"}),
            _make_event("task_unsolved", metadata={"failure_category": "fallback_only"}),
        ]
        top = top_failure_categories(events)
        assert top[0][0] == "wrong_family"


class TestMissingEvents:
    def test_detects_missing_run_summary(self):
        events = [
            _make_event("run_started"),
            _make_event("run_finished"),
        ]
        issues = check_missing_events(events)
        assert "Missing run_summary event" in issues

    def test_detects_missing_run_started(self):
        events = [
            _make_event("run_finished"),
        ]
        issues = check_missing_events(events)
        assert "Missing run_started event" in issues

    def test_detects_missing_run_finished(self):
        events = [
            _make_event("run_started"),
        ]
        issues = check_missing_events(events)
        assert "Missing run_finished event" in issues

    def test_valid_log_passes(self):
        events = [
            _make_event("run_started"),
            _make_event("run_summary"),
            _make_event("run_finished"),
        ]
        issues = check_missing_events(events)
        assert issues == []


class TestTaskCountMismatch:
    def test_detects_mismatch(self):
        events = [
            _make_event("task_started"),
            _make_event("task_started"),
            _make_event("task_solved"),
        ]
        issues = check_task_count_mismatch(events)
        assert len(issues) > 0

    def test_matches_when_correct(self):
        events = [
            _make_event("task_started"),
            _make_event("task_solved"),
        ]
        issues = check_task_count_mismatch(events)
        assert issues == []


class TestUnsafeMetadata:
    def test_detects_raw_grid(self):
        events = [
            _make_event("task_solved", metadata={"raw_grid": [[0, 1], [1, 0]]}),
        ]
        issues = check_unsafe_metadata(events)
        assert len(issues) > 0

    def test_detects_expected_output(self):
        events = [
            _make_event("task_solved", metadata={"expected_output": [[0, 1], [1, 0]]}),
        ]
        issues = check_unsafe_metadata(events)
        assert len(issues) > 0

    def test_clean_metadata_passes(self):
        events = [
            _make_event("task_solved", metadata={"task_id": "t1", "family_label": "crop"}),
        ]
        issues = check_unsafe_metadata(events)
        assert issues == []


class TestExpectedOutputLeakage:
    def test_detects_leakage_in_solver_execution(self):
        events = [
            _make_event("solver_packet_created", phase="solver_execution",
                        metadata={"expected_output_shape": [3, 3]}),
        ]
        issues = check_expected_output_leakage(events)
        assert len(issues) > 0

    def test_clean_solver_execution_passes(self):
        events = [
            _make_event("solver_packet_created", phase="solver_execution",
                        metadata={"task_id": "t1", "shape": [3, 3]}),
        ]
        issues = check_expected_output_leakage(events)
        assert issues == []


class TestRawGridLeakage:
    def test_detects_grid_data_in_metadata(self):
        events = [
            _make_event("task_solved", metadata={"train": [[0, 1], [1, 0]]}),
        ]
        issues = check_raw_grid_leakage(events)
        assert len(issues) > 0

    def test_clean_metadata_passes(self):
        events = [
            _make_event("task_solved", metadata={"task_id": "t1"}),
        ]
        issues = check_raw_grid_leakage(events)
        assert issues == []


class TestSummaryConsistency:
    def test_detects_event_count_mismatch(self):
        events = [_make_event("run_started"), _make_event("run_finished")]
        summary = {"event_count": 5, "summary": {"solved": 1}}
        issues = check_summary_consistency(events, summary)
        assert len(issues) > 0

    def test_matches_when_correct(self):
        events = [_make_event("run_started"), _make_event("run_finished")]
        summary = {"event_count": 2, "summary": {}}
        issues = check_summary_consistency(events, summary)
        assert issues == []


class TestFullAnalysis:
    def test_analyzes_good_log(self):
        events = [
            _make_event("run_started", phase="run_start"),
            _make_event("task_started", phase="solver_execution", metadata={"task_id": "t1"}),
            _make_event("task_solved", phase="evaluation", metadata={"task_id": "t1"}),
            _make_event("run_summary", phase="run_summary"),
            _make_event("run_finished", phase="run_end"),
        ]
        analysis = analyze_events(events)
        assert analysis["event_count"] == 5
        assert analysis["leakage_audit_pass"] is True
        assert analysis["missing_events"] == []

    def test_detects_leakage_in_full_analysis(self):
        events = [
            _make_event("run_started", phase="run_start"),
            _make_event("task_solved", phase="evaluation", metadata={"raw_grid": [[0]]}),
            _make_event("run_finished", phase="run_end"),
        ]
        analysis = analyze_events(events)
        assert analysis["leakage_audit_pass"] is False
        assert len(analysis["unsafe_metadata"]) > 0

    def test_summarizes_exceptions(self):
        events = [
            _make_event("exception", metadata={"task_id": "t1", "exception_type": "ValueError"}),
        ]
        analysis = analyze_events(events)
        assert analysis["exception_count"] == 1
        assert len(analysis["exceptions"]) == 1

    def test_summarizes_fallback_families(self):
        events = [
            _make_event("fallback_used", metadata={"family_label": "crop"}),
            _make_event("fallback_used", metadata={"family_label": "crop"}),
        ]
        analysis = analyze_events(events)
        assert analysis["top_fallback_families"][0] == ("crop", 2)

    def test_validates_adversarial(self):
        events = [
            _make_event("adversarial_rejection", metadata={"rejected": True}),
            _make_event("adversarial_rejection", metadata={"rejected": False}),
        ]
        analysis = analyze_events(events)
        assert analysis["adversarial"]["adversarial_rejection_pass"] == 1
        assert analysis["adversarial"]["adversarial_rejection_fail"] == 1


class TestLoadFunctions:
    def test_load_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "events.jsonl")
            path.write_text('{"event_type": "run_started"}\n{"event_type": "run_finished"}\n')
            events = load_events(str(path))
            assert len(events) == 2

    def test_load_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "summary.json")
            path.write_text('{"run_id": "test", "event_count": 5}')
            summary = load_summary(str(path))
            assert summary["run_id"] == "test"