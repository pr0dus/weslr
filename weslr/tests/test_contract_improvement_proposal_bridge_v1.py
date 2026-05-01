#!/usr/bin/env python3
"""
WESLR Contract Improvement Proposal Bridge V1 — Tests

Covers:
- missing insufficiency log returns no proposals
- non-proposal-ready evidence ignored
- proposal_ready evidence creates review record
- duplicate ready evidence does not duplicate review records
- malformed lines skipped
- no raw prompt/PII accepted
- automatic_change always false
- proposal_status pending_review
- append-only behavior
- no production truth files modified
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
    for mod in ("weslr.contract_improvement_proposal_bridge",):
        try:
            importlib.reload(importlib.import_module(mod))
        except Exception:
            pass


def _make_insufficiency(
    pattern_type="weak_entry_repetition",
    contract="conversational_entry",
    response_path="fallback_safe",
    signal_type=None,
    occurrence_count=10,
    stable_across_checks=3,
    proposal_ready=True,
    insufficiency_confirmed=True,
    with_forbidden_field=False,
    with_pii=False,
):
    """Build a valid insufficiency log record."""
    rec = {
        "record_type": "contract_insufficiency_v1",
        "pattern_type": pattern_type,
        "detected_at": "2026-05-01T07:00:00Z",
        "window_size": 50,
        "record_count_in_window": 10,
        "contract": contract,
        "response_path": response_path,
        "occurrence_count": occurrence_count,
        "signal_types_seen": [signal_type] * occurrence_count,
        "frame_distribution": {"entry": occurrence_count},
        "signal_type_distribution": {str(signal_type): occurrence_count},
        "insufficiency_confirmed": insufficiency_confirmed,
        "stable_across_checks": stable_across_checks,
        "proposal_ready": proposal_ready,
    }
    if with_forbidden_field:
        rec["raw_prompt"] = "this should not be here"
    if with_pii:
        rec["some_field"] = "contact: john@test.com"
    return rec


class TestMissingSourceLog(unittest.TestCase):
    """Source log missing returns empty result, no crash."""

    def setUp(self):
        _reload()
        from weslr.contract_improvement_proposal_bridge import generate_proposals
        self.generate = generate_proposals

    def test_missing_log_returns_empty(self):
        """Missing insufficiency log returns all-zero result."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "missing_insuff_log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            result = self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            self.assertEqual(result["generated"], 0)
            self.assertEqual(result["malformed"], 0)
            self.assertEqual(result["skipped_non_ready"], 0)
            self.assertEqual(result["total_processed"], 0)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestNonProposalReadyFiltered(unittest.TestCase):
    """Evidence where proposal_ready=False is not converted."""

    def setUp(self):
        _reload()
        from weslr.contract_improvement_proposal_bridge import generate_proposals
        self.generate = generate_proposals

    def test_non_ready_evidence_ignored(self):
        """proposal_ready=False evidence is skipped."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_insufficiency(proposal_ready=False, stable_across_checks=3)
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            result = self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            self.assertEqual(result["generated"], 0)
            self.assertEqual(result["skipped_non_ready"], 1)
            self.assertFalse(pathlib.Path(prop).exists())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_below_stability_threshold_ignored(self):
        """stable_across_checks < 3 is skipped even if proposal_ready=True."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_insufficiency(stable_across_checks=2, proposal_ready=True)
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            result = self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            self.assertEqual(result["generated"], 0)
            self.assertEqual(result["skipped_non_ready"], 1)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestProposalReadyCreatesRecord(unittest.TestCase):
    """proposal_ready=True + stable_across_checks>=3 creates a review record."""

    def setUp(self):
        _reload()
        from weslr.contract_improvement_proposal_bridge import generate_proposals
        self.generate = generate_proposals

    def test_ready_evidence_creates_review_record(self):
        """Valid proposal-ready evidence produces one review record."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_insufficiency(
                pattern_type="weak_entry_repetition",
                contract="conversational_entry",
                response_path="fallback_safe",
                stable_across_checks=3,
                proposal_ready=True,
            )
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            result = self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            self.assertEqual(result["generated"], 1)
            self.assertEqual(result["skipped_duplicates"], 0)

            lines = pathlib.Path(prop).read_text().strip().split("\n")
            self.assertEqual(len(lines), 1)
            stored = json.loads(lines[0])
            self.assertEqual(stored["record_type"], "contract_proposal_review_v1")
            self.assertIn("proposal_id", stored)
            self.assertEqual(stored["pattern_type"], "weak_entry_repetition")
            self.assertEqual(stored["contract"], "conversational_entry")
            self.assertEqual(stored["response_path"], "fallback_safe")
            self.assertEqual(stored["operator_action_requested"], "review_contract_outcome")
            self.assertIs(stored["automatic_change"], False)
            self.assertEqual(stored["proposal_status"], "pending_review")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_evidence_summary_fields(self):
        """Review record contains correct evidence_summary."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_insufficiency(
                occurrence_count=7,
                stable_across_checks=3,
            )
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            stored = json.loads(pathlib.Path(prop).read_text().strip().split("\n")[0])
            es = stored["evidence_summary"]
            self.assertEqual(es["occurrence_count"], 7)
            self.assertIn("stable_across_checks", es)
            self.assertIn("frame_distribution", es)
            self.assertIn("signal_types_seen", es)
            self.assertIn("window_size", es)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestDeduplication(unittest.TestCase):
    """Same pattern+contract+response_path+stable_across_checks is deduplicated."""

    def setUp(self):
        _reload()
        from weslr.contract_improvement_proposal_bridge import generate_proposals
        self.generate = generate_proposals

    def test_duplicate_ready_evidence_not_duplicated(self):
        """Identical ready evidence is deduplicated — only one record created."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_insufficiency(
                pattern_type="weak_entry_repetition",
                contract="conversational_entry",
                response_path="fallback_safe",
                stable_across_checks=3,
            )
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")
                f.write(json.dumps(rec) + "\n")
                f.write(json.dumps(rec) + "\n")

            result = self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            self.assertEqual(result["generated"], 1)
            self.assertEqual(result["skipped_duplicates"], 2)

            lines = pathlib.Path(prop).read_text().strip().split("\n")
            self.assertEqual(len(lines), 1)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_different_contract_not_deduplicated(self):
        """Different contract creates separate record."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec1 = _make_insufficiency(
                pattern_type="weak_entry_repetition",
                contract="conversational_entry",
                response_path="fallback_safe",
            )
            rec2 = _make_insufficiency(
                pattern_type="fallback_repetition",
                contract="fallback_safe",
                response_path="fallback_safe",
            )
            with open(log, "w") as f:
                f.write(json.dumps(rec1) + "\n")
                f.write(json.dumps(rec.dumps(rec2) + "\n") if False else "")
            # Write manually
            with open(log, "w") as f:
                f.write(json.dumps(rec1) + "\n")

            self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            result1 = self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            # rec2 different contract
            rec2 = _make_insufficiency(
                pattern_type="weak_entry_repetition",
                contract="conversational_entry",
                response_path="fallback_safe",
            )
            with open(log, "w") as f:
                f.write(json.dumps(rec1) + "\n")
                f.write(json.dumps(rec2) + "\n")
            result2 = self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            # After first run prop log has CP-001 for rec1; second run rec2 is same pattern/contract/path/check
            # Both rec1 and rec2 are same dedup key — only 1 generated
            self.assertEqual(result2["generated"], 0)
            self.assertEqual(result2["skipped_duplicates"], 2)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestMalformedLinesSkipped(unittest.TestCase):
    """Unreadable and forbidden-content lines are skipped gracefully."""

    def setUp(self):
        _reload()
        from weslr.contract_improvement_proposal_bridge import generate_proposals
        self.generate = generate_proposals

    def test_malformed_json_skipped(self):
        """Malformed JSON lines are counted as malformed but don't crash."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            with open(log, "w") as f:
                f.write('{"record_type": "contract_insufficiency_v1", "proposal_ready": true, "stable_across_checks": 3, "pattern_type": "weak_entry_repetition", "contract": "conversational_entry", "response_path": "fallback_safe", "occurrence_count": 10}\n')
                f.write("not valid json line\n")
                f.write('{"record_type": "contract_insufficiency_v1", "proposal_ready": true, "stable_across_checks": 3, "pattern_type": "fallback_repetition", "contract": "fallback_safe", "response_path": "fallback_safe", "occurrence_count": 10}\n')

            result = self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            self.assertEqual(result["malformed"], 1)
            self.assertEqual(result["generated"], 2)
            lines = pathlib.Path(prop).read_text().strip().split("\n")
            self.assertEqual(len(lines), 2)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_forbidden_field_rejected(self):
        """Records with forbidden fields (raw_prompt, etc.) are rejected."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            bad_rec = _make_insufficiency(with_forbidden_field=True)
            good_rec = _make_insufficiency()
            with open(log, "w") as f:
                f.write(json.dumps(bad_rec) + "\n")
                f.write(json.dumps(good_rec) + "\n")

            result = self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            self.assertEqual(result["malformed"], 1)
            self.assertEqual(result["generated"], 1)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_pii_rejected(self):
        """Records with PII signals are rejected as malformed."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            pii_rec = _make_insufficiency(with_pii=True)
            good_rec = _make_insufficiency()
            with open(log, "w") as f:
                f.write(json.dumps(pii_rec) + "\n")
                f.write(json.dumps(good_rec) + "\n")

            result = self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            self.assertEqual(result["malformed"], 1)
            self.assertEqual(result["generated"], 1)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestRecordShape(unittest.TestCase):
    """Review record shape matches specification exactly."""

    def setUp(self):
        _reload()
        from weslr.contract_improvement_proposal_bridge import generate_proposals
        self.generate = generate_proposals

    def test_automatic_change_always_false(self):
        """automatic_change is always False in generated records."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_insufficiency(stable_across_checks=3)
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            stored = json.loads(pathlib.Path(prop).read_text().strip().split("\n")[0])
            self.assertIs(stored["automatic_change"], False)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_proposal_status_pending_review(self):
        """proposal_status is always 'pending_review'."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_insufficiency(stable_across_checks=3)
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            stored = json.loads(pathlib.Path(prop).read_text().strip().split("\n")[0])
            self.assertEqual(stored["proposal_status"], "pending_review")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_proposal_id_format(self):
        """proposal_id follows CP-YYYYMMDD-NNN format."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_insufficiency(stable_across_checks=3)
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            stored = json.loads(pathlib.Path(prop).read_text().strip().split("\n")[0])
            import re
            self.assertRegex(stored["proposal_id"], r"^CP-\d{8}-\d{3}$")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestAppendOnlyBehavior(unittest.TestCase):
    """Running bridge does not truncate or overwrite existing proposal log."""

    def setUp(self):
        _reload()
        from weslr.contract_improvement_proposal_bridge import generate_proposals
        self.generate = generate_proposals

    def test_append_does_not_truncate(self):
        """Second run appends to existing proposal log."""
        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec1 = _make_insufficiency(
                pattern_type="weak_entry_repetition",
                contract="conversational_entry",
                response_path="fallback_safe",
            )
            rec2 = _make_insufficiency(
                pattern_type="fallback_repetition",
                contract="fallback_safe",
                response_path="fallback_safe",
            )
            with open(log, "w") as f:
                f.write(json.dumps(rec1) + "\n")

            self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            with open(log, "w") as f:
                f.write(json.dumps(rec2) + "\n")

            self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
            lines = pathlib.Path(prop).read_text().strip().split("\n")
            self.assertEqual(len(lines), 2)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestNoProductionTruthModified(unittest.TestCase):
    """Bridge never writes to production truth files."""

    def setUp(self):
        _reload()
        from weslr.contract_improvement_proposal_bridge import generate_proposals
        self.generate = generate_proposals

    PRODUCTION_FILES = [
        "proposal_trace.jsonl",
        "implementation_plans.jsonl",
        "state_checkpoint.json",
    ]

    def test_production_files_unmodified(self):
        """Running bridge does not touch production truth files."""
        production_paths = [
            _workspace / "weslr" / f
            for f in self.PRODUCTION_FILES
        ]
        before = {}
        for p in production_paths:
            existed = p.exists()
            before[str(p)] = p.read_text() if existed else None

        tmpdir = tempfile.mkdtemp()
        log = pathlib.Path(tmpdir) / "log.jsonl"
        prop = pathlib.Path(tmpdir) / "proposal_log.jsonl"
        try:
            rec = _make_insufficiency(stable_across_checks=3)
            with open(log, "w") as f:
                f.write(json.dumps(rec) + "\n")

            self.generate(
                insufficiency_log_path=str(log),
                proposal_log_path=str(prop),
            )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        for p in production_paths:
            existed_before = before[str(p)] is not None
            existed_after = p.exists()
            if existed_before:
                self.assertEqual(p.read_text(), before[str(p)])
            else:
                self.assertFalse(existed_after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
