"""Tests for ARC-AGI-2 run event log V1."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from weslr.arc_run_event_log_v1 import (
    FORBIDDEN_METADATA_KEYS_V1,
    ArcRunEventLogV1,
    make_run_id,
)


class TestEventLogBasics:
    def test_writes_valid_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp, write_text_log=False, write_summary=False)
            log.start_run()
            log.emit("INFO", "evaluation", "task_solved", "Task solved", {"task_id": "t1"})
            log.finish_run()
            log.close()
            events = [json.loads(line) for line in Path(tmp, "events.jsonl").read_text().splitlines() if line.strip()]
            assert len(events) == 3
            assert events[0]["event_type"] == "run_started"
            assert events[1]["event_type"] == "task_solved"
            assert events[2]["event_type"] == "run_finished"

    def test_writes_readable_text_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp, write_jsonl=False, write_summary=False)
            log.start_run()
            log.emit("INFO", "evaluation", "task_solved", "Task solved", {"task_id": "t1"})
            log.finish_run()
            log.close()
            text = Path(tmp, "run.log").read_text()
            assert "INFO" in text
            assert "task_solved" in text
            assert "Task solved" in text

    def test_writes_summary_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp, write_text_log=False, write_jsonl=False)
            log.start_run()
            log.emit("INFO", "evaluation", "task_solved", "Task solved")
            log.finish_run({"solved": 1})
            log.close()
            summary = json.loads(Path(tmp, "summary.json").read_text())
            assert summary["run_id"] == "test-run"
            assert summary["event_count"] == 3
            assert summary["summary"]["solved"] == 1

    def test_preserves_event_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp, write_text_log=False, write_summary=False)
            log.start_run()
            log.emit("INFO", "evaluation", "task_solved", "first", {"order": 1})
            log.emit("INFO", "evaluation", "task_unsolved", "second", {"order": 2})
            log.finish_run()
            log.close()
            events = [json.loads(line) for line in Path(tmp, "events.jsonl").read_text().splitlines() if line.strip()]
            assert events[1]["metadata"]["order"] == 1
            assert events[2]["metadata"]["order"] == 2

    def test_supports_deterministic_run_id(self):
        rid = make_run_id("test")
        assert rid.startswith("test-")

    def test_does_not_require_log_path_inside_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp)
            log.start_run()
            log.finish_run()
            log.close()
            assert Path(tmp, "events.jsonl").exists()


class TestMetadataSafety:
    def test_rejects_unsafe_metadata_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp, write_text_log=False, write_summary=False)
            log.start_run()
            for bad_key in FORBIDDEN_METADATA_KEYS_V1:
                with pytest.raises(ValueError, match="Forbidden metadata key"):
                    log.emit("INFO", "evaluation", "task_solved", "bad", {bad_key: "value"})
            log.finish_run()
            log.close()

    def test_rejects_non_json_safe_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp, write_text_log=False, write_summary=False)
            log.start_run()
            with pytest.raises(ValueError, match="Non-JSON-safe"):
                log.emit("INFO", "evaluation", "task_solved", "bad", {"key": object()})
            log.finish_run()
            log.close()

    def test_allows_safe_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp, write_text_log=False, write_summary=False)
            log.start_run()
            log.emit("INFO", "evaluation", "task_solved", "ok", {
                "task_id": "t1",
                "family_label": "crop",
                "split": "dev",
                "shape": [3, 3],
                "count": 5,
                "solved": True,
            })
            log.finish_run()
            log.close()
            events = [json.loads(line) for line in Path(tmp, "events.jsonl").read_text().splitlines() if line.strip()]
            assert events[1]["metadata"]["task_id"] == "t1"


class TestLevelValidation:
    def test_rejects_unknown_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp, write_text_log=False, write_summary=False)
            log.start_run()
            with pytest.raises(ValueError, match="Unknown level"):
                log.emit("INVALID", "evaluation", "task_solved", "bad")
            log.finish_run()
            log.close()

    def test_accepts_all_allowed_levels(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp, write_text_log=False, write_summary=False)
            log.start_run()
            for level in ("DEBUG", "INFO", "WARNING", "ERROR", "SUMMARY"):
                log.emit(level, "evaluation", "task_solved", f"test {level}")
            log.finish_run()
            log.close()
            events = [json.loads(line) for line in Path(tmp, "events.jsonl").read_text().splitlines() if line.strip()]
            assert len(events) == 7  # start + 5 + finish


class TestPhaseValidation:
    def test_rejects_unknown_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp, write_text_log=False, write_summary=False)
            log.start_run()
            with pytest.raises(ValueError, match="Unknown phase"):
                log.emit("INFO", "invalid_phase", "task_solved", "bad")
            log.finish_run()
            log.close()


class TestEventTypeValidation:
    def test_rejects_unknown_event_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = ArcRunEventLogV1("test-run", tmp, write_text_log=False, write_summary=False)
            log.start_run()
            with pytest.raises(ValueError, match="Unknown event_type"):
                log.emit("INFO", "evaluation", "invalid_type", "bad")
            log.finish_run()
            log.close()