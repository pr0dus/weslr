#!/usr/bin/env python3
"""
WESLR Review Interface V1 — Tests

Covers:
- missing log returns empty list
- malformed lines skipped
- pending_review records loaded
- non-pending records ignored or separated
- lookup by proposal_id
- summary count by pattern_type/contract
- no writes to any file
- no behavior change fields
- no raw prompt/PII exposure
"""

import importlib
import json
import pathlib
import sys
import tempfile
import shutil
import unittest

_workspace = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_workspace))
sys.path.insert(0, str(_workspace / "weslr"))


def _reload():
    for mod in ("weslr.review_interface",):
        try:
            importlib.reload(importlib.import_module(mod))
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Record builders
# ---------------------------------------------------------------------------

def _make_review(
    proposal_id="CP-20260501-001",
    pattern_type="weak_entry_repetition",
    contract="conversational_entry",
    response_path="fallback_safe",
    proposal_status="pending_review",
    stable_across_checks=3,
    occurrence_count=5,
    with_forbidden_field=False,
    with_pii_field=False,
):
    rec = {
        "record_type": "contract_proposal_review_v1",
        "proposal_id": proposal_id,
        "generated_at": "2026-05-01T07:22:11Z",
        "pattern_type": pattern_type,
        "contract": contract,
        "response_path": response_path,
        "evidence_summary": {
            "occurrence_count": occurrence_count,
            "signal_types_seen": [None] * occurrence_count,
            "frame_distribution": {"entry": occurrence_count},
            "stable_across_checks": stable_across_checks,
            "window_size": 50,
        },
        "operator_action_requested": "review_contract_outcome",
        "automatic_change": False,
        "proposal_status": proposal_status,
    }
    if with_forbidden_field:
        rec["raw_prompt"] = "should not be exposed"
    if with_pii_field:
        rec["email"] = "user@example.com"
    return rec


# ---------------------------------------------------------------------------
# Test: missing log returns empty list
# ---------------------------------------------------------------------------

class TestMissingLog(unittest.TestCase):
    """Missing proposal log returns empty list — no crash."""

    def setUp(self):
        _reload()
        from weslr.review_interface import load_pending_contract_reviews
        self.fn = load_pending_contract_reviews

    def test_missing_log_returns_empty_list(self):
        """Missing log file returns empty list, no exception."""
        tmpdir = tempfile.mkdtemp()
        try:
            result = self.fn(log_path=str(pathlib.Path(tmpdir) / "missing.jsonl"))
            self.assertEqual(result, [])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test: malformed lines skipped
# ---------------------------------------------------------------------------

class TestMalformedLinesSkipped(unittest.TestCase):
    """Unreadable JSON lines are skipped silently."""

    def setUp(self):
        _reload()
        from weslr.review_interface import load_pending_contract_reviews
        self.fn = load_pending_contract_reviews

    def test_malformed_json_skipped(self):
        """Malformed JSON lines are skipped — valid lines still loaded."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            with open(log, "w") as f:
                f.write('{"record_type": "contract_proposal_review_v1", "proposal_id": "CP-20260501-001", "proposal_status": "pending_review", "pattern_type": "weak_entry_repetition", "contract": "conversational_entry"}\n')
                f.write("not valid json line\n")
                f.write('{"record_type": "contract_proposal_review_v1", "proposal_id": "CP-20260501-002", "proposal_status": "pending_review", "pattern_type": "fallback_repetition", "contract": "fallback_safe"}\n')

            result = self.fn(log_path=str(log))
            self.assertEqual(len(result), 2)
            ids = [r["proposal_id"] for r in result]
            self.assertIn("CP-20260501-001", ids)
            self.assertIn("CP-20260501-002", ids)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_empty_lines_skipped(self):
        """Empty lines are skipped silently."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            with open(log, "w") as f:
                f.write('{"record_type": "contract_proposal_review_v1", "proposal_id": "CP-20260501-001", "proposal_status": "pending_review", "pattern_type": "weak_entry_repetition", "contract": "conversational_entry"}\n')
                f.write("\n")
                f.write("   \n")
                f.write('{"record_type": "contract_proposal_review_v1", "proposal_id": "CP-20260501-002", "proposal_status": "pending_review", "pattern_type": "fallback_repetition", "contract": "fallback_safe"}\n')

            result = self.fn(log_path=str(log))
            self.assertEqual(len(result), 2)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test: pending_review records loaded
# ---------------------------------------------------------------------------

class TestPendingRecordsLoaded(unittest.TestCase):
    """Only records with proposal_status == pending_review are returned."""

    def setUp(self):
        _reload()
        from weslr.review_interface import load_pending_contract_reviews
        self.fn = load_pending_contract_reviews

    def test_pending_review_loaded(self):
        """proposal_status=pending_review is returned."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_review(proposal_id="CP-20260501-P001", proposal_status="pending_review")
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            result = self.fn(log_path=str(log))
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["proposal_id"], "CP-20260501-P001")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test: non-pending records ignored
# ---------------------------------------------------------------------------

class TestNonPendingRecordsIgnored(unittest.TestCase):
    """Records with non-pending statuses are excluded from pending list."""

    def setUp(self):
        _reload()
        from weslr.review_interface import load_pending_contract_reviews
        self.fn = load_pending_contract_reviews

    def test_approved_ignored(self):
        """proposal_status=approved is not in pending list."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            pending = _make_review(proposal_id="CP-20260501-PEND", proposal_status="pending_review")
            approved = _make_review(proposal_id="CP-20260501-APP", proposal_status="approved")
            with open(log, "w") as f:
                f.write(json.dumps(pending) + "\n")
                f.write(json.dumps(approved) + "\n")

            result = self.fn(log_path=str(log))
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["proposal_id"], "CP-20260501-PEND")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_rejected_ignored(self):
        """proposal_status=rejected is not in pending list."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            pending = _make_review(proposal_id="CP-20260501-PEND", proposal_status="pending_review")
            rejected = _make_review(proposal_id="CP-20260501-REJ", proposal_status="rejected")
            deferred = _make_review(proposal_id="CP-20260501-DEF", proposal_status="deferred")
            with open(log, "w") as f:
                f.write(json.dumps(pending) + "\n")
                f.write(json.dumps(rejected) + "\n")
                f.write(json.dumps(deferred) + "\n")

            result = self.fn(log_path=str(log))
            self.assertEqual(len(result), 1)
            ids = [r["proposal_id"] for r in result]
            self.assertNotIn("CP-20260501-REJ", ids)
            self.assertNotIn("CP-20260501-DEF", ids)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test: lookup by proposal_id
# ---------------------------------------------------------------------------

class TestLookupByProposalId(unittest.TestCase):
    """get_contract_review_by_id returns the matching record or None."""

    def setUp(self):
        _reload()
        from weslr.review_interface import get_contract_review_by_id
        self.fn = get_contract_review_by_id

    def test_lookup_found(self):
        """Existing proposal_id returns the record."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec1 = _make_review(proposal_id="CP-20260501-FIND", proposal_status="pending_review")
            rec2 = _make_review(proposal_id="CP-20260501-OTHER", proposal_status="pending_review")
            with open(log, "w") as f:
                f.write(json.dumps(rec1) + "\n")
                f.write(json.dumps(rec2) + "\n")

            result = self.fn("CP-20260501-FIND", log_path=str(log))
            self.assertIsNotNone(result)
            self.assertEqual(result["proposal_id"], "CP-20260501-FIND")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_lookup_not_found(self):
        """Non-existent proposal_id returns None."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_review(proposal_id="CP-20260501-REAL", proposal_status="pending_review")
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            result = self.fn("CP-20260501-NOTREAL", log_path=str(log))
            self.assertIsNone(result)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_lookup_empty_id_returns_none(self):
        """Empty or invalid proposal_id returns None — no crash."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            result = self.fn("", log_path=str(log))
            self.assertIsNone(result)
            result2 = self.fn(None, log_path=str(log))
            self.assertIsNone(result2)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test: summary count by pattern_type/contract
# ---------------------------------------------------------------------------

class TestSummaryCounts(unittest.TestCase):
    """summarize_pending_reviews returns correct counts."""

    def setUp(self):
        _reload()
        from weslr.review_interface import summarize_pending_reviews
        self.fn = summarize_pending_reviews

    def test_summary_total_pending(self):
        """summary.total_pending equals number of pending records."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            with open(log, "w") as f:
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-001", pattern_type="weak_entry_repetition", contract="conversational_entry")) + "\n")
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-002", pattern_type="weak_entry_repetition", contract="conversational_entry")) + "\n")
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-003", pattern_type="fallback_repetition", contract="fallback_safe")) + "\n")

            summary = self.fn(log_path=str(log))
            self.assertEqual(summary["total_pending"], 3)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_summary_by_pattern_type(self):
        """summary.by_pattern_type aggregates correctly."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            with open(log, "w") as f:
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-001", pattern_type="weak_entry_repetition")) + "\n")
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-002", pattern_type="weak_entry_repetition")) + "\n")
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-003", pattern_type="fallback_repetition")) + "\n")

            summary = self.fn(log_path=str(log))
            self.assertEqual(summary["by_pattern_type"]["weak_entry_repetition"], 2)
            self.assertEqual(summary["by_pattern_type"]["fallback_repetition"], 1)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_summary_by_contract(self):
        """summary.by_contract aggregates correctly."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            with open(log, "w") as f:
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-001", contract="conversational_entry")) + "\n")
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-002", contract="conversational_entry")) + "\n")
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-003", contract="fallback_safe")) + "\n")

            summary = self.fn(log_path=str(log))
            self.assertEqual(summary["by_contract"]["conversational_entry"], 2)
            self.assertEqual(summary["by_contract"]["fallback_safe"], 1)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_summary_by_response_path(self):
        """summary.by_response_path aggregates correctly."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            with open(log, "w") as f:
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-001", response_path="task_help_query")) + "\n")
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-002", response_path="task_help_query")) + "\n")
                f.write(json.dumps(_make_review(proposal_id="CP-20260501-003", response_path="fallback_safe")) + "\n")

            summary = self.fn(log_path=str(log))
            self.assertEqual(summary["by_response_path"]["task_help_query"], 2)
            self.assertEqual(summary["by_response_path"]["fallback_safe"], 1)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test: no writes to any file
# ---------------------------------------------------------------------------

class TestNoWrites(unittest.TestCase):
    """Read interface never writes to any file."""

    def setUp(self):
        _reload()
        from weslr.review_interface import (
            load_pending_contract_reviews,
            get_contract_review_by_id,
            summarize_pending_reviews,
        )
        self.fns = {
            "load": load_pending_contract_reviews,
            "get": get_contract_review_by_id,
            "summary": summarize_pending_reviews,
        }

    def _touch(self, path: pathlib.Path):
        path.write_text("before\n")

    def test_load_does_not_write(self):
        """load_pending_contract_reviews never modifies the log file."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        log.write_text(
            json.dumps(_make_review(proposal_id="CP-20260501-001"))
            + "\n"
        )

        try:
            before = log.read_text()
            self.fns["load"](log_path=str(log))
            after = log.read_text()
            self.assertEqual(before, after)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_get_does_not_write(self):
        """get_contract_review_by_id never modifies the log file."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        log.write_text(
            json.dumps(_make_review(proposal_id="CP-20260501-001"))
            + "\n"
        )

        try:
            before = log.read_text()
            self.fns["get"]("CP-20260501-001", log_path=str(log))
            after = log.read_text()
            self.assertEqual(before, after)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_summary_does_not_write(self):
        """summarize_pending_reviews never modifies the log file."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        log.write_text(
            json.dumps(_make_review(proposal_id="CP-20260501-001"))
            + "\n"
        )

        try:
            before = log.read_text()
            self.fns["summary"](log_path=str(log))
            after = log.read_text()
            self.assertEqual(before, after)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test: no behavior change fields
# ---------------------------------------------------------------------------

class TestNoBehaviorChangeFields(unittest.TestCase):
    """Loaded records never contain behavior-change fields."""

    def setUp(self):
        _reload()
        from weslr.review_interface import load_pending_contract_reviews
        self.fn = load_pending_contract_reviews

    def test_automatic_change_not_present(self):
        """Loaded records do not carry automatic_change (not a behavior-change field)."""
        # Note: automatic_change IS in the schema but value must be False
        # This test verifies it's in the record and is False
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            with open(log, "w") as f:
                f.write(json.dumps(_make_review()) + "\n")

            result = self.fn(log_path=str(log))
            self.assertEqual(len(result), 1)
            self.assertIn("automatic_change", result[0])
            self.assertIs(result[0]["automatic_change"], False)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test: no raw prompt/PII exposure
# ---------------------------------------------------------------------------

class TestNoRawPromptOrPII(unittest.TestCase):
    """Forbidden fields are stripped from all returned records."""

    def setUp(self):
        _reload()
        from weslr.review_interface import load_pending_contract_reviews
        self.fn = load_pending_contract_reviews

    def test_raw_prompt_stripped(self):
        """Records with raw_prompt are stripped of that field."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_review(with_forbidden_field=True)
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            result = self.fn(log_path=str(log))
            self.assertEqual(len(result), 1)
            self.assertNotIn("raw_prompt", result[0])
            self.assertNotIn("prompt", result[0])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_pii_field_stripped(self):
        """Records with email/phone/ip/address are stripped of those fields."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_review(with_pii_field=True)
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            result = self.fn(log_path=str(log))
            self.assertEqual(len(result), 1)
            self.assertNotIn("email", result[0])
            self.assertNotIn("phone", result[0])
            self.assertNotIn("ip", result[0])
            self.assertNotIn("address", result[0])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_forbidden_fields_not_in_get(self):
        """get_contract_review_by_id also strips forbidden fields."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_review(with_forbidden_field=True)
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            _reload()
            from weslr.review_interface import get_contract_review_by_id
            result = get_contract_review_by_id("CP-20260501-001", log_path=str(log))
            self.assertNotIn("raw_prompt", result)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_forbidden_fields_not_in_summary(self):
        """summarize_pending_reviews also strips forbidden fields."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_review(with_forbidden_field=True)
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            _reload()
            from weslr.review_interface import summarize_pending_reviews
            summary = summarize_pending_reviews(log_path=str(log))
            for rec_out in summary["records"]:
                self.assertNotIn("raw_prompt", rec_out)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
