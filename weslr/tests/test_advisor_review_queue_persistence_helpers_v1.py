from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.advisor_review_queue_persistence import (  # noqa: E402
    append_persistence_event,
    create_empty_persistence_event,
    create_status_update_event,
    load_persistence_events,
    summarize_persistence_events,
    validate_queue_storage_path,
)

REAL_QUEUE_FILE = ROOT / ".weslr" / "advisor_review_queue.jsonl"
ALLOWED_CHANGED = {
    "weslr/advisor_review_queue_persistence.py",
    "weslr/tests/test_advisor_review_queue_persistence_helpers_v1.py",
    "weslr/tests/test_advisor_review_queue_persistence_schema_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/advisor_review_queue.py",
    "weslr/local_scan_advisor_review.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_discovery/review.py",
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/advisor_prompt_templates.py",
    "weslr/llm_advisor_mode.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
    "review_queue.json",
    "export_queue.json",
    ".weslr/advisor_review_queue.jsonl",
}


def valid_event(**overrides):
    event = create_empty_persistence_event(
        event_id="event_001",
        event_type="queue_item_created",
        queue_item_id="queue_item_001",
        redacted_summary="redacted queue item summary",
    )
    for key, value in overrides.items():
        setattr(event, key, value)
    return event


class AdvisorReviewQueuePersistenceHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(append_persistence_event)
        self.assertTrue(load_persistence_events)
        self.assertTrue(summarize_persistence_events)

    def test_02_safe_temp_path_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([], validate_queue_storage_path(Path(tmp) / "queue.jsonl"))

    def test_03_path_traversal_fails(self):
        self.assertIn("path traversal is not allowed", validate_queue_storage_path("../queue.jsonl"))

    def test_04_unsafe_absolute_path_fails_by_default(self):
        errors = validate_queue_storage_path("/etc/weslr/advisor_review_queue.jsonl")
        self.assertIn("absolute paths are not allowed", errors)

    def test_05_append_event_writes_one_jsonl_line_to_temp_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.jsonl"
            result = append_persistence_event(path, valid_event())
            self.assertTrue(result["success"])
            self.assertEqual(1, len(path.read_text(encoding="utf-8").splitlines()))

    def test_06_load_events_reads_appended_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.jsonl"
            append_persistence_event(path, valid_event())
            result = load_persistence_events(path)
            self.assertEqual([], result["validation_errors"])
            self.assertEqual(1, len(result["events"]))
            self.assertEqual("event_001", result["events"][0].event_id)

    def test_07_missing_file_loads_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = load_persistence_events(Path(tmp) / "missing.jsonl")
            self.assertEqual([], result["events"])
            self.assertEqual([], result["validation_errors"])

    def test_08_invalid_event_is_not_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.jsonl"
            result = append_persistence_event(path, valid_event(event_id=""))
            self.assertFalse(result["success"])
            self.assertFalse(path.exists())

    def test_09_status_update_event_is_created_in_memory(self):
        event = create_status_update_event("queue_item_001", "pending_review", "accepted", "approved")
        self.assertEqual("status_update_requested", event.event_type)
        self.assertEqual("queue_item_001", event.queue_item_id)
        self.assertEqual("accepted", event.new_status)

    def test_10_summary_is_redacted_count_only(self):
        summary = summarize_persistence_events([valid_event()])
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual(1, summary["event_count"])

    def test_11_summary_does_not_contain_sensitive_strings(self):
        event = valid_event(redacted_summary="api key token secret raw benchmark answer key private user data")
        summary = summarize_persistence_events([event])
        rendered = json.dumps(summary).lower()
        for forbidden in ["api key", "token", "secret", "raw benchmark", "answer key", "private user data"]:
            self.assertNotIn(forbidden, rendered)

    def test_12_no_external_model_calls(self):
        result = append_persistence_event(Path(tempfile.gettempdir()) / "weslr_model_guard_queue.jsonl", valid_event(event_id="event_model_guard"))
        self.assertFalse(result["external_model_calls_made"])
        (Path(tempfile.gettempdir()) / "weslr_model_guard_queue.jsonl").unlink(missing_ok=True)

    def test_13_no_runtime_config_changes(self):
        summary = summarize_persistence_events([valid_event()])
        self.assertFalse(summary["runtime_changes_made"])

    def test_14_no_answer_selection(self):
        summary = summarize_persistence_events([valid_event()])
        self.assertFalse(summary["answer_selection"])

    def test_15_no_truth_soundness_claim(self):
        summary = summarize_persistence_events([valid_event()])
        self.assertFalse(summary["truth_claim"])

    def test_16_no_official_score(self):
        summary = summarize_persistence_events([valid_event()])
        self.assertFalse(summary["official_score"])

    def test_17_real_advisor_review_queue_jsonl_is_not_created(self):
        self.assertFalse(REAL_QUEUE_FILE.exists())

    def test_18_persistence_schema_tests_still_pass(self):
        subprocess.run(["python3", "weslr/tests/test_advisor_review_queue_persistence_schema_v1.py"], cwd=str(ROOT), check=True)

    def test_19_advisor_review_queue_schema_tests_still_pass(self):
        subprocess.run(["python3", "weslr/tests/test_advisor_review_queue_schema_v1.py"], cwd=str(ROOT), check=True)

    def test_20_release_gate_check_pass(self):
        subprocess.run(["python3", "weslr/tests/release_gate_v1.py"], cwd=str(ROOT), check=True)
        subprocess.run(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT), check=True)

    def test_21_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
