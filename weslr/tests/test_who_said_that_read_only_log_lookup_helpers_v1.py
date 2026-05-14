from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.voice_source_attribution_log import (  # noqa: E402
    create_empty_voice_attribution_log_event,
    voice_attribution_log_event_to_dict,
)
from weslr.who_said_that_log_lookup import (  # noqa: E402
    WhoSaidThatLogLookupResult,
    create_empty_who_said_that_log_lookup_path_policy,
    create_empty_who_said_that_log_lookup_request,
    load_voice_attribution_log_events_read_only,
    resolve_who_said_that_from_lookup_result,
    select_voice_attribution_log_events,
    summarize_who_said_that_log_lookup_diagnostics,
    validate_who_said_that_log_lookup_result,
    validate_who_said_that_lookup_path,
)

ALLOWED_CHANGED_FILES = {
    "weslr/who_said_that_log_lookup.py",
    "weslr/tests/test_who_said_that_read_only_log_lookup_helpers_v1.py",
    "weslr/tests/test_who_said_that_read_only_log_lookup_schema_v1.py",
}


def request(**overrides):
    data = {"request_id": "req_lookup", "query_id": "query_lookup"}
    data.update(overrides)
    return create_empty_who_said_that_log_lookup_request(**data)


def event(event_id="event_a", utterance_id="utt_a", created_at="2026-05-13T21:00:00+00:00", **overrides):
    data = {
        "event_type": "post_speak_attribution_confirmed",
        "source_subsystem": "voice_gateway",
        "speech_emitted": True,
        "speech_success": True,
        "authority_level": "observed_event",
        "truth_class": "observed",
        "trace_refs": ["verified:trace-a"],
        "created_at": created_at,
        "redacted_summary": "redacted voice attribution event",
        "attribution_record_snapshot": {
            "source_module": "voice_surface",
            "generated_by": "weslr",
            "trigger_type": "voice_event",
            "confidence": "medium",
            "operator_review_required": True,
        },
    }
    data.update(overrides)
    return create_empty_voice_attribution_log_event(event_id=event_id, utterance_id=utterance_id, **data)


def write_jsonl(path: Path, events):
    with path.open("w", encoding="utf-8") as handle:
        for item in events:
            handle.write(json.dumps(voice_attribution_log_event_to_dict(item), sort_keys=True) + "\n")


class WhoSaidThatReadOnlyLogLookupHelpersV1Tests(unittest.TestCase):
    def test_01_module_imports(self):
        self.assertTrue(load_voice_attribution_log_events_read_only)
        self.assertTrue(select_voice_attribution_log_events)
        self.assertTrue(resolve_who_said_that_from_lookup_result)

    def test_02_explicit_safe_temp_path_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "voice_source_attribution.jsonl"
            self.assertEqual([], validate_who_said_that_lookup_path(path, create_empty_who_said_that_log_lookup_path_policy()))

    def test_03_path_traversal_fails(self):
        errors = validate_who_said_that_lookup_path("../voice_source_attribution.jsonl", create_empty_who_said_that_log_lookup_path_policy())
        self.assertIn("path traversal rejected", errors)

    def test_04_unsafe_absolute_path_fails_by_default(self):
        errors = validate_who_said_that_lookup_path("/etc/passwd", create_empty_who_said_that_log_lookup_path_policy())
        self.assertIn("absolute path rejected", errors)

    def test_05_missing_explicit_file_returns_empty_missing_log_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.jsonl"
            result = load_voice_attribution_log_events_read_only(path, request())
            self.assertTrue(result.missing_log)
            self.assertEqual(0, result.records_found)
            self.assertEqual(0, result.selected_event_count)

    def test_06_missing_explicit_file_does_not_create_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.jsonl"
            load_voice_attribution_log_events_read_only(path, request())
            self.assertFalse(path.exists())

    def test_07_valid_jsonl_event_loads_from_temp_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            write_jsonl(path, [event()])
            result = load_voice_attribution_log_events_read_only(path, request())
            self.assertEqual(1, result.records_found)
            self.assertEqual(1, result.selected_event_count)

    def test_08_invalid_jsonl_line_reported_not_trusted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            path.write_text("not-json\n", encoding="utf-8")
            result = load_voice_attribution_log_events_read_only(path, request())
            self.assertEqual(0, result.records_found)
            self.assertTrue(result.warnings)

    def test_09_most_recent_selects_latest_event(self):
        old = event(event_id="old", created_at="2026-05-13T20:00:00+00:00")
        new = event(event_id="new", created_at="2026-05-13T21:00:00+00:00")
        selected = select_voice_attribution_log_events([old, new], request(max_events=1))
        self.assertEqual("new", selected[0].event_id)

    def test_10_by_utterance_id_selects_matching_event(self):
        selected = select_voice_attribution_log_events([event(utterance_id="utt_a"), event(utterance_id="utt_b")], request(lookup_mode="by_utterance_id", requested_utterance_id="utt_b"))
        self.assertEqual(["utt_b"], [item.utterance_id for item in selected])

    def test_11_by_trace_ref_selects_matching_event(self):
        selected = select_voice_attribution_log_events([event(event_id="a"), event(event_id="b", trace_refs=["verified:trace-b"])], request(lookup_mode="by_trace_ref", requested_trace_ref="verified:trace-b"))
        self.assertEqual(["b"], [item.event_id for item in selected])

    def test_12_by_time_window_selects_matching_events(self):
        selected = select_voice_attribution_log_events([
            event(event_id="before", created_at="2026-05-13T19:00:00+00:00"),
            event(event_id="inside", created_at="2026-05-13T20:30:00+00:00"),
        ], request(lookup_mode="by_time_window", time_window_start="2026-05-13T20:00:00+00:00", time_window_end="2026-05-13T21:00:00+00:00"))
        self.assertEqual(["inside"], [item.event_id for item in selected])

    def test_13_manual_review_only_does_not_overclaim(self):
        selected = select_voice_attribution_log_events([event()], request(lookup_mode="manual_review_only", manual_review_only=True))
        self.assertEqual([], selected)

    def test_14_selected_snapshots_are_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            write_jsonl(path, [event()])
            result = load_voice_attribution_log_events_read_only(path, request())
            self.assertNotIn("raw_spoken_text", json.dumps(result.selected_event_snapshots))
            self.assertNotIn("transcript", json.dumps(result.selected_event_snapshots).lower())

    def test_15_raw_spoken_text_in_event_rejected_or_redacted(self):
        bad = event(spoken_text_stored=True)
        selected = select_voice_attribution_log_events([bad], request())
        self.assertEqual([], selected)

    def test_16_result_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            write_jsonl(path, [event()])
            result = load_voice_attribution_log_events_read_only(path, request())
            self.assertEqual([], validate_who_said_that_log_lookup_result(result))

    def test_17_resolver_returns_missing_attribution_when_no_records(self):
        result = WhoSaidThatLogLookupResult(result_id="res", request_id="req_lookup", lookup_mode="most_recent", missing_log=True, attribution_missing=True)
        answer = resolve_who_said_that_from_lookup_result(request(), result)
        self.assertFalse(answer.attribution_found)

    def test_18_resolver_returns_safe_answer_when_record_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            write_jsonl(path, [event()])
            result = load_voice_attribution_log_events_read_only(path, request())
            answer = resolve_who_said_that_from_lookup_result(request(), result)
            self.assertTrue(answer.attribution_found)
            self.assertEqual("voice_gateway", answer.source_subsystem)

    def test_19_no_default_weslr_log_read_occurs_implicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            explicit = Path(tmp) / "missing.jsonl"
            result = load_voice_attribution_log_events_read_only(explicit, request())
            self.assertTrue(result.missing_log)
            self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_20_no_log_file_created_under_weslr(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_21_no_log_writes_performed(self):
        self.assertFalse(load_voice_attribution_log_events_read_only(Path(tempfile.gettempdir()) / "missing-weslr-test.jsonl", request()).log_write_performed)

    def test_22_no_queue_writes_performed(self):
        self.assertFalse(load_voice_attribution_log_events_read_only(Path(tempfile.gettempdir()) / "missing-weslr-test.jsonl", request()).queue_write_performed)

    def test_23_no_registry_persistence(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_24_no_runtime_config_changes(self):
        summary = summarize_who_said_that_log_lookup_diagnostics([])
        self.assertFalse(summary["runtime_changes_performed"])

    def test_25_no_external_model_calls(self):
        summary = summarize_who_said_that_log_lookup_diagnostics([])
        self.assertFalse(summary["external_model_calls_performed"])

    def test_26_no_answer_selection(self):
        summary = summarize_who_said_that_log_lookup_diagnostics([])
        self.assertFalse(summary["answer_selection"])

    def test_27_no_truth_soundness_claim(self):
        summary = summarize_who_said_that_log_lookup_diagnostics([])
        self.assertFalse(summary["truth_claim"])

    def test_28_no_official_score(self):
        summary = summarize_who_said_that_log_lookup_diagnostics([])
        self.assertFalse(summary["official_score"])

    def test_29_diagnostics_summary_redacted_count_only(self):
        summary = summarize_who_said_that_log_lookup_diagnostics([WhoSaidThatLogLookupResult(result_id="res", request_id="req", records_found=2, selected_event_count=1)])
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual(1, summary["lookup_request_count"])
        self.assertEqual(2, summary["records_found_total"])

    def test_30_diagnostics_summary_does_not_contain_sensitive_text(self):
        summary_text = json.dumps(summarize_who_said_that_log_lookup_diagnostics([])).lower()
        for forbidden in ["api key", "token", "secret", "raw spoken", "raw benchmark", "answer key", "private user data"]:
            self.assertNotIn(forbidden, summary_text)

    def test_31_schema_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_who_said_that_read_only_log_lookup_schema_v1.py"], cwd=str(ROOT))

    def test_32_parserless_resolver_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_who_said_that_parserless_resolver_helpers_v1.py"], cwd=str(ROOT))

    def test_33_release_gate_check_pass(self):
        if os.environ.get("WESLR_NESTED_RELEASE_CHECK") == "1":
            self.skipTest("nested release check already in progress")
        env = dict(os.environ)
        env["WESLR_NESTED_RELEASE_CHECK"] = "1"
        subprocess.check_call([sys.executable, "weslr/tests/release_gate_v1.py"], cwd=str(ROOT), env=env)
        subprocess.check_call(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT), env=env)

    def test_34_scope_changed_files_only_allowed(self):
        result = subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True, text=True, capture_output=True)
        changed = set()
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            changed.add(path)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
