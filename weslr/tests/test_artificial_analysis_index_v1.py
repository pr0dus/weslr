"""
WESLR Artificial Analysis Index V1 — Tests

Tests for aai_pass1 attention classification and summary building.
No JSONL files are modified. No runtime behavior changed.

Run:
    python3 -m pytest weslr/tests/test_artificial_analysis_index_v1.py -v
"""

import json
import os
import pathlib
import tempfile
from unittest import TestCase, main

from weslr.artificial_analysis_index import (
    classify_attention_item,
    build_attention_summary,
    _AUTHORITY,
    _AUTOMATIC_CHANGE,
    _LEVEL_LABELS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_temp_jsonl(lines: list[dict]) -> str:
    """Create a temp JSONL file and return path."""
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")
    return path


def make_temp_jsonl_raw(lines: list[str]) -> str:
    """Create a temp JSONL file with raw strings (some malformed)."""
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as f:
        for line in lines:
            f.write(line + "\n")
    return path


# ---------------------------------------------------------------------------
# Test classify_attention_item
# ---------------------------------------------------------------------------

class TestClassifyAttentionItem(TestCase):

    def test_authority_always_attention_only(self):
        """authority field must always be 'attention_only'."""
        test_cases = [
            {"record_type": "contract_observation_v1", "timestamp": "2026-05-01T00:00:00Z"},
            {"record_type": "public_signal_v1", "session_id_hash": "abc123"},
            {"record_type": "contract_insufficiency_v1", "detected_at": "2026-05-01T00:00:00Z", "proposal_ready": True},
            {"record_type": "contract_proposal_review_v1", "proposal_id": "CP-20260501-001"},
        ]
        for rec in test_cases:
            result = classify_attention_item(rec)
            self.assertEqual(result["authority"], _AUTHORITY)

    def test_automatic_change_always_false(self):
        """automatic_change is always False in all results."""
        test_cases = [
            {"record_type": "contract_observation_v1", "timestamp": "2026-05-01T00:00:00Z"},
            {"record_type": "public_signal_v1", "session_id_hash": "abc123"},
            {"record_type": "contract_insufficiency_v1", "detected_at": "2026-05-01T00:00:00Z", "proposal_ready": True},
            {"record_type": "contract_proposal_review_v1", "proposal_id": "CP-20260501-001"},
        ]
        for rec in test_cases:
            result = classify_attention_item(rec)
            self.assertIs(result["automatic_change"] if "automatic_change" in result else _AUTOMATIC_CHANGE, False)

    def test_contract_observation_level_0(self):
        """Contract observation records are level 0 (suppress)."""
        record = {
            "record_type": "contract_observation_v1",
            "response_contract": "conversational_entry",
            "interaction_frame": "entry",
            "turn_type": "greeting",
            "reply_shape": "conversational_entry",
            "signal_type": None,
            "response_path": "unknown",
            "source": "website_public",
            "safe_to_record": True,
            "raw_prompt_stored": False,
            "pii_stored": False,
            "behavior_change_allowed": False,
            "value_inference_allowed": False,
            "timestamp": "2026-05-01T00:00:00Z",
            "session_id_hash": "abc123",
        }
        result = classify_attention_item(record)
        self.assertEqual(result["attention_level"], 0)
        self.assertEqual(result["classification"], "suppress")
        self.assertEqual(result["source"], "contract_observation")

    def test_contract_observation_escalates_if_safety_violation(self):
        """Contract observation with raw_prompt_stored=True escalates to level 3."""
        record = {
            "record_type": "contract_observation_v1",
            "timestamp": "2026-05-01T00:00:00Z",
            "raw_prompt_stored": True,
        }
        result = classify_attention_item(record)
        self.assertEqual(result["attention_level"], 3)
        self.assertEqual(result["classification"], "ask")
        self.assertTrue(result["requires_operator_action"])

    def test_public_signal_level_1(self):
        """Public signal records are level 1 (track)."""
        record = {
            "record_type": "public_signal_v1",
            "session_id_hash": "abc123",
            "signal_type": "S4",
            "response_path": "fallback_safe",
            "topic_normalized": None,
            "timestamp": "2026-05-01T00:00:00Z",
            "source": "website_public",
            "safe_to_record": True,
            "raw_prompt_stored": False,
            "pii_stored": False,
            "behavior_change_allowed": False,
            "value_inference_allowed": False,
        }
        result = classify_attention_item(record)
        self.assertEqual(result["attention_level"], 1)
        self.assertEqual(result["classification"], "track")
        self.assertEqual(result["source"], "public_signal")

    def test_insufficiency_proposal_ready_level_2(self):
        """Insufficiency record with proposal_ready=True is level 2 (summary)."""
        record = {
            "record_type": "contract_insufficiency_v1",
            "pattern_type": "weak_entry_repetition",
            "contract": "conversational_entry",
            "response_path": "fallback_safe",
            "occurrence_count": 5,
            "detected_at": "2026-05-01T00:00:00Z",
            "proposal_ready": True,
            "stable_across_checks": 3,
            "insufficiency_confirmed": True,
        }
        result = classify_attention_item(record)
        self.assertEqual(result["attention_level"], 2)
        self.assertEqual(result["classification"], "summary")
        self.assertEqual(result["source"], "contract_insufficiency")

    def test_insufficiency_not_proposal_ready_level_1(self):
        """Insufficiency record with proposal_ready=False is level 1 (track)."""
        record = {
            "record_type": "contract_insufficiency_v1",
            "pattern_type": "weak_entry_repetition",
            "contract": "conversational_entry",
            "detected_at": "2026-05-01T00:00:00Z",
            "proposal_ready": False,
            "stable_across_checks": 1,
        }
        result = classify_attention_item(record)
        self.assertEqual(result["attention_level"], 1)
        self.assertEqual(result["classification"], "track")

    def test_proposal_review_pending_level_3(self):
        """Pending contract proposal review records are level 3 (ask)."""
        record = {
            "record_type": "contract_proposal_review_v1",
            "proposal_id": "CP-20260501-001",
            "pattern_type": "weak_entry_repetition",
            "contract": "conversational_entry",
            "response_path": "unknown",
            "generated_at": "2026-05-01T00:00:00Z",
            "operator_action_requested": "review_contract_outcome",
            "automatic_change": False,
            "proposal_status": "pending_review",
        }
        result = classify_attention_item(record)
        self.assertEqual(result["attention_level"], 3)
        self.assertEqual(result["classification"], "ask")
        self.assertEqual(result["source"], "contract_proposal_review")
        self.assertTrue(result["requires_operator_action"])

    def test_no_level_4_in_normal_data(self):
        """Normal Pass 1 data should have no level 4 records."""
        normal_records = [
            {"record_type": "contract_observation_v1", "timestamp": "2026-05-01T00:00:00Z",
             "raw_prompt_stored": False, "pii_stored": False, "behavior_change_allowed": False},
            {"record_type": "public_signal_v1", "session_id_hash": "abc123"},
            {"record_type": "contract_insufficiency_v1", "detected_at": "2026-05-01T00:00:00Z",
             "proposal_ready": False, "stable_across_checks": 1},
            {"record_type": "contract_proposal_review_v1", "proposal_id": "CP-20260501-001",
             "proposal_status": "pending_review"},
        ]
        for rec in normal_records:
            result = classify_attention_item(rec)
            self.assertNotEqual(result["attention_level"], 4,
                                f"Unexpected level 4 for normal record: {rec}")

    def test_malformed_record_suppress(self):
        """Malformed record (not a dict) returns level 0 suppress."""
        result = classify_attention_item(None)
        self.assertEqual(result["attention_level"], 0)
        self.assertEqual(result["classification"], "suppress")

    def test_empty_dict_level_1(self):
        """Empty dict (no record_type) returns level 1 (track) — treated as unknown type."""
        result = classify_attention_item({})
        self.assertEqual(result["attention_level"], 1)
        self.assertEqual(result["classification"], "track")

    def test_unknown_record_type_level_1(self):
        """Unknown record type returns level 1 (track)."""
        result = classify_attention_item({"record_type": "unknown_type"})
        self.assertEqual(result["attention_level"], 1)
        self.assertEqual(result["classification"], "track")

    def test_classify_returns_required_fields(self):
        """Every classification result has all required fields."""
        record = {"record_type": "contract_observation_v1", "timestamp": "2026-05-01T00:00:00Z",
                  "raw_prompt_stored": False, "pii_stored": False, "behavior_change_allowed": False}
        result = classify_attention_item(record)
        for field in ("attention_level", "classification", "reason", "source",
                      "record_id", "requires_operator_action", "authority"):
            self.assertIn(field, result)

    def test_level_labels_match_levels(self):
        """Level label mapping is consistent."""
        for lvl, label in _LEVEL_LABELS.items():
            self.assertIn(label, ("suppress", "track", "summary", "ask", "interrupt"))


# ---------------------------------------------------------------------------
# Test build_attention_summary
# ---------------------------------------------------------------------------

class TestBuildAttentionSummary(TestCase):

    def test_missing_public_signals_returns_safe_summary(self):
        """Missing public_signals.jsonl returns empty levels, no crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = build_attention_summary(
                public_signals_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                contract_observations_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                insufficiency_log_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                proposal_review_log_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
            )
            self.assertEqual(summary["record_type"], "aai_attention_summary_v1")
            self.assertEqual(summary["authority"], "attention_only")
            self.assertFalse(summary["automatic_change"])
            self.assertIn("operator_message", summary)
            self.assertIn("levels", summary)
            self.assertIn("counts", summary)
            self.assertEqual(summary["counts"]["total"], 0)

    def test_malformed_lines_skipped(self):
        """Malformed JSONL lines are skipped, valid lines are processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(pathlib.Path(tmpdir) / "test.jsonl")
            with open(path, "w") as f:
                f.write('{"record_type": "public_signal_v1", "session_id_hash": "abc"}\n')
                f.write("NOT VALID JSON\n")
                f.write('{"record_type": "public_signal_v1", "session_id_hash": "def"}\n')
                f.write('{"incomplete\n')
                f.write('{"record_type": "public_signal_v1", "session_id_hash": "ghi"}\n')

            summary = build_attention_summary(
                public_signals_path=path,
                contract_observations_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                insufficiency_log_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                proposal_review_log_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
            )
            # 3 valid lines should be classified
            self.assertEqual(summary["counts"]["1"], 3)

    def test_contract_observations_all_level_0(self):
        """All contract_observation records in real data are level 0."""
        summary = build_attention_summary()
        level_0_records = summary["levels"]["0"]
        for rec in level_0_records:
            if rec["source"] == "contract_observation":
                self.assertEqual(rec["attention_level"], 0)

    def test_public_signals_all_level_1(self):
        """All public_signal records in real data are level 1."""
        summary = build_attention_summary()
        level_1_records = summary["levels"]["1"]
        public_signals = [r for r in level_1_records if r["source"] == "public_signal"]
        for rec in public_signals:
            self.assertEqual(rec["attention_level"], 1)

    def test_proposal_ready_insufficiency_level_2(self):
        """proposal_ready=True insufficiency records classified level 2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(pathlib.Path(tmpdir) / "insufficient.jsonl")
            with open(path, "w") as f:
                f.write(json.dumps({
                    "record_type": "contract_insufficiency_v1",
                    "pattern_type": "weak_entry_repetition",
                    "contract": "conversational_entry",
                    "detected_at": "2026-05-01T00:00:00Z",
                    "proposal_ready": True,
                    "stable_across_checks": 3,
                }) + "\n")

            summary = build_attention_summary(
                public_signals_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                contract_observations_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                insufficiency_log_path=path,
                proposal_review_log_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
            )
            self.assertEqual(summary["counts"]["2"], 1)
            self.assertEqual(summary["levels"]["2"][0]["attention_level"], 2)
            self.assertEqual(summary["levels"]["2"][0]["classification"], "summary")

    def test_pending_review_level_3(self):
        """pending_review proposal records classified level 3."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(pathlib.Path(tmpdir) / "reviews.jsonl")
            with open(path, "w") as f:
                f.write(json.dumps({
                    "record_type": "contract_proposal_review_v1",
                    "proposal_id": "CP-20260501-001",
                    "pattern_type": "weak_entry_repetition",
                    "contract": "conversational_entry",
                    "generated_at": "2026-05-01T00:00:00Z",
                    "proposal_status": "pending_review",
                    "automatic_change": False,
                }) + "\n")

            summary = build_attention_summary(
                public_signals_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                contract_observations_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                insufficiency_log_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                proposal_review_log_path=path,
            )
            self.assertEqual(summary["counts"]["3"], 1)
            self.assertEqual(summary["levels"]["3"][0]["attention_level"], 3)
            self.assertEqual(summary["levels"]["3"][0]["classification"], "ask")
            self.assertTrue(summary["levels"]["3"][0]["requires_operator_action"])

    def test_no_level_4_in_normal_data_summary(self):
        """build_attention_summary on real data produces zero level 4 items."""
        summary = build_attention_summary()
        self.assertEqual(summary["counts"]["4"], 0)

    def test_automatic_change_false_in_summary(self):
        """automatic_change in summary is always False."""
        summary = build_attention_summary()
        self.assertFalse(summary["automatic_change"])

    def test_authority_attention_only_in_summary(self):
        """authority in summary is always 'attention_only'."""
        summary = build_attention_summary()
        self.assertEqual(summary["authority"], "attention_only")

    def test_operator_message_present(self):
        """operator_message field is always present."""
        summary = build_attention_summary()
        self.assertIn("operator_message", summary)
        self.assertIsInstance(summary["operator_message"], str)
        self.assertGreater(len(summary["operator_message"]), 0)

    def test_operator_message_no_immediate_action_when_no_3_or_4(self):
        """When no level 3 or 4 items, message says no immediate action needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Empty sources
            summary = build_attention_summary(
                public_signals_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                contract_observations_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                insufficiency_log_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                proposal_review_log_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
            )
            self.assertIn("no immediate operator action required", summary["operator_message"].lower())

    def test_operator_message_mentions_pending_when_level_3(self):
        """When level 3 items exist, message mentions pending review."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(pathlib.Path(tmpdir) / "reviews.jsonl")
            with open(path, "w") as f:
                f.write(json.dumps({
                    "record_type": "contract_proposal_review_v1",
                    "proposal_id": "CP-20260501-001",
                    "pattern_type": "weak_entry_repetition",
                    "contract": "conversational_entry",
                    "generated_at": "2026-05-01T00:00:00Z",
                    "proposal_status": "pending_review",
                    "automatic_change": False,
                }) + "\n")

            summary = build_attention_summary(
                public_signals_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                contract_observations_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                insufficiency_log_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                proposal_review_log_path=path,
            )
            self.assertIn("review", summary["operator_message"].lower())

    def test_sources_read_listed(self):
        """sources_read field lists all source paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = build_attention_summary(
                public_signals_path="/custom/path/public_signals.jsonl",
                contract_observations_path="/custom/path/contract_observations.jsonl",
                insufficiency_log_path="/custom/path/contract_insufficiency_log.jsonl",
                proposal_review_log_path="/custom/path/contract_proposal_review_log.jsonl",
            )
            self.assertEqual(len(summary["sources_read"]), 4)
            for src in summary["sources_read"]:
                self.assertIn("custom/path", src)

    def test_counts_total_equals_sum_of_levels(self):
        """counts['total'] equals sum of all level counts."""
        summary = build_attention_summary()
        total = summary["counts"]["total"]
        level_sum = sum(summary["counts"][str(i)] for i in range(5))
        self.assertEqual(total, level_sum)

    def test_no_jsonl_files_modified(self):
        """build_attention_summary does not modify any JSONL files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a small test file
            test_file = pathlib.Path(tmpdir) / "public_signals.jsonl"
            original_content = '{"record_type": "public_signal_v1", "session_id_hash": "abc"}\n'
            test_file.write_text(original_content)

            # Run summary
            summary = build_attention_summary(
                public_signals_path=str(test_file),
                contract_observations_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                insufficiency_log_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
                proposal_review_log_path=str(pathlib.Path(tmpdir) / "nonexistent.jsonl"),
            )

            # Verify file unchanged
            self.assertEqual(test_file.read_text(), original_content)

    def test_real_data_produces_consistent_structure(self):
        """Real data build_attention_summary returns all required top-level keys."""
        summary = build_attention_summary()
        for key in ("record_type", "generated_at", "authority", "automatic_change",
                    "levels", "operator_message", "counts", "sources_read"):
            self.assertIn(key, summary)

    def test_levels_keys_0_through_4(self):
        """levels dict has keys '0' through '4'."""
        summary = build_attention_summary()
        for i in range(5):
            self.assertIn(str(i), summary["levels"])


# ---------------------------------------------------------------------------
# Test no state changes
# ---------------------------------------------------------------------------

class TestNoStateChanges(TestCase):

    def test_proposal_status_not_changed(self):
        """classify_attention_item never changes proposal_status."""
        record = {
            "record_type": "contract_proposal_review_v1",
            "proposal_id": "CP-20260501-001",
            "proposal_status": "pending_review",
        }
        result = classify_attention_item(record)
        self.assertEqual(result.get("proposal_status", None), None)
        # The classifier doesn't add proposal_status

    def test_build_summary_does_not_append_to_files(self):
        """build_attention_summary appends nothing to any JSONL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sources = {
                "public_signals_path": str(pathlib.Path(tmpdir) / "public_signals.jsonl"),
                "contract_observations_path": str(pathlib.Path(tmpdir) / "contract_obs.jsonl"),
                "insufficiency_log_path": str(pathlib.Path(tmpdir) / "insuf.jsonl"),
                "proposal_review_log_path": str(pathlib.Path(tmpdir) / "reviews.jsonl"),
            }
            # Create files with content
            for path in sources.values():
                pathlib.Path(path).write_text('{"record_type": "public_signal_v1", "session_id_hash": "x"}\n')

            before_sizes = {p: pathlib.Path(p).stat().st_size for p in sources.values()}

            build_attention_summary(**sources)

            after_sizes = {p: pathlib.Path(p).stat().st_size for p in sources.values()}
            for p in sources.values():
                self.assertEqual(before_sizes[p], after_sizes[p],
                                 f"File {p} was modified by build_attention_summary")


if __name__ == "__main__":
    main()