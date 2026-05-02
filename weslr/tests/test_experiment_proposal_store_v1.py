"""
WESLR Experiment Proposal Store V1 — Unit Tests

Tests the experiment_proposal_schema, experiment_proposal_store,
and their integration. Uses temp files for all JSONL operations.
"""

import itertools
import json
import os
import pathlib
import tempfile
import unittest

from weslr.experiment_proposal_schema import (
    build_experiment_proposal,
    generate_experiment_proposal_id,
    validate_experiment_proposal,
)
from weslr.experiment_proposal_store import (
    append_experiment_proposal,
    append_if_new,
    get_default_experiment_proposal_path,
    load_experiment_proposals,
    proposal_dedup_key,
    proposal_exists,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_valid_proposal(**overrides) -> dict:
    """Return a minimal valid proposal with optional field overrides."""
    base = build_experiment_proposal(
        type="search_insight",
        title="Test proposal",
        description="A test search insight proposal.",
        params={"query": "test", "depth": "normal"},
        confidence=0.75,
        confidence_reasons=["test reason 1", "test reason 2"],
        source="user_timeline",
        source_refs=["test_ref"],
        timeline_id="tl_test",
        related_capability="evidence.search",
        risk_level="low",
        requires_operator_approval=True,
    )
    for k, v in overrides.items():
        base[k] = v
    return base


# ---------------------------------------------------------------------------
# ID generation tests
# ---------------------------------------------------------------------------

class TestProposalIdGeneration(unittest.TestCase):
    def test_id_format(self):
        pid = generate_experiment_proposal_id()
        self.assertRegex(pid, r"^EXP-\d{8}-\d{3}$")

    def test_id_date_from_now(self):
        import time
        now = time.time()
        pid = generate_experiment_proposal_id(now=now)
        date_part = pid.split("-")[1]
        expected = time.strftime("%Y%m%d", time.localtime(now))
        self.assertEqual(date_part, expected)

    def test_id_increments_with_existing(self):
        now = 1200096000.0  # fixed timestamp → 2008-01-12 UTC
        existing = [
            {"proposal_id": "EXP-20080112-001"},
            {"proposal_id": "EXP-20080112-002"},
        ]
        pid = generate_experiment_proposal_id(existing_records=existing, now=now)
        self.assertEqual(pid, "EXP-20080112-003")

    def test_id_skips_other_date(self):
        now = 1200096000.0
        existing = [
            {"proposal_id": "EXP-20080111-999"},
            {"proposal_id": "EXP-20080112-001"},
        ]
        pid = generate_experiment_proposal_id(existing_records=existing, now=now)
        self.assertEqual(pid, "EXP-20080112-002")

    def test_id_skips_malformed(self):
        now = 1200096000.0
        existing = [
            {"proposal_id": "malformed"},
            {"proposal_id": "EXP-20080112-001"},
        ]
        pid = generate_experiment_proposal_id(existing_records=existing, now=now)
        self.assertEqual(pid, "EXP-20080112-002")

    def test_id_starts_at_001_when_empty(self):
        pid = generate_experiment_proposal_id(existing_records=[], now=1200096000.0)
        self.assertEqual(pid, "EXP-20080112-001")


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------

class TestSchemaValidation(unittest.TestCase):
    def test_valid_proposal_passes(self):
        p = _make_valid_proposal()
        valid, errors = validate_experiment_proposal(p)
        self.assertTrue(valid)
        self.assertEqual(errors, [])

    def test_missing_proposal_id_fails(self):
        p = _make_valid_proposal()
        del p["proposal_id"]
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("proposal_id" in e for e in errors))

    def test_missing_record_type_fails(self):
        p = _make_valid_proposal()
        del p["record_type"]
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("record_type" in e for e in errors))

    def test_wrong_record_type_fails(self):
        p = _make_valid_proposal(record_type="wrong_type")
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("record_type" in e for e in errors))

    def test_invalid_type_fails(self):
        p = _make_valid_proposal(type="invalid_type")
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("type must be one of" in e for e in errors))

    def test_invalid_status_fails(self):
        p = _make_valid_proposal(execution_status="invalid_status")
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("execution_status must be one of" in e for e in errors))

    def test_invalid_risk_level_fails(self):
        p = _make_valid_proposal(risk_level="invalid_risk")
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("risk_level must be one of" in e for e in errors))

    def test_confidence_out_of_range_fails(self):
        p = _make_valid_proposal(confidence=1.5)
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("between 0.0 and 1.0" in e for e in errors))

    def test_missing_confidence_reasons_fails(self):
        p = _make_valid_proposal()
        del p["confidence_reasons"]
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("confidence_reasons" in e for e in errors))

    def test_forbidden_raw_prompt_fails(self):
        p = _make_valid_proposal(raw_prompt="some prompt")
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("forbidden field 'raw_prompt'" in e for e in errors))

    def test_forbidden_transcript_fails(self):
        p = _make_valid_proposal(transcript="full conversation here")
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("forbidden field 'transcript'" in e for e in errors))

    def test_forbidden_password_fails(self):
        p = _make_valid_proposal(password="secret123")
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("forbidden field 'password'" in e for e in errors))

    def test_automatic_execution_not_false_fails(self):
        p = _make_valid_proposal(automatic_execution=True)
        valid, errors = validate_experiment_proposal(p)
        self.assertFalse(valid)
        self.assertTrue(any("automatic_execution must be False" in e for e in errors))


# ---------------------------------------------------------------------------
# Type-specific rule tests
# ---------------------------------------------------------------------------

class TestPhysicalActionRules(unittest.TestCase):
    def test_physical_action_forces_approval(self):
        p = _make_valid_proposal(type="physical_action")
        valid, errors = validate_experiment_proposal(p)
        self.assertTrue(valid)
        self.assertEqual(p["requires_operator_approval"], True)
        self.assertEqual(p["operator_approval_required"], True)
        self.assertEqual(p["automatic_execution"], False)

    def test_physical_action_build_forces_approval(self):
        p = build_experiment_proposal(
            type="physical_action",
            title="Test physical",
            description="A physical action test.",
            params={},
            confidence=0.5,
            confidence_reasons=["test"],
            source="manual",
            source_refs=[],
            risk_level="high",
            requires_operator_approval=False,  # should be overridden
        )
        self.assertEqual(p["type"], "physical_action")
        self.assertEqual(p["requires_operator_approval"], True)
        self.assertEqual(p["operator_approval_required"], True)
        self.assertEqual(p["automatic_execution"], False)


class TestSelfImprovementRules(unittest.TestCase):
    def test_self_improvement_forces_approval(self):
        p = _make_valid_proposal(type="self_improvement_suggestion")
        valid, errors = validate_experiment_proposal(p)
        self.assertTrue(valid)
        self.assertEqual(p["requires_operator_approval"], True)
        self.assertEqual(p["operator_approval_required"], True)

    def test_self_improvement_build_forces_approval(self):
        p = build_experiment_proposal(
            type="self_improvement_suggestion",
            title="Test self-improvement",
            description="A self-improvement test.",
            params={},
            confidence=0.5,
            confidence_reasons=["test"],
            source="contract_insufficiency",
            source_refs=[],
            risk_level="low",
            requires_operator_approval=False,  # should be overridden
        )
        self.assertEqual(p["requires_operator_approval"], True)
        self.assertEqual(p["operator_approval_required"], True)


# ---------------------------------------------------------------------------
# Store tests
# ---------------------------------------------------------------------------

class TestExperimentProposalStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = os.path.join(self.tmpdir, "proposals.jsonl")

    def tearDown(self):
        for f in os.listdir(self.tmpdir):
            os.unlink(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def test_load_missing_file_returns_empty(self):
        result = load_experiment_proposals(path="/nonexistent/file.jsonl")
        self.assertEqual(result, [])

    def test_load_filters_by_status(self):
        p1 = _make_valid_proposal(execution_status="pending")
        p2 = _make_valid_proposal(execution_status="approved")
        append_experiment_proposal(p1, path=self.tmpfile)
        append_experiment_proposal(p2, path=self.tmpfile)
        pending = load_experiment_proposals(path=self.tmpfile, status="pending")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["execution_status"], "pending")

    def test_load_filters_by_type(self):
        p1 = _make_valid_proposal(type="search_insight")
        p2 = _make_valid_proposal(type="simulation_run")
        append_experiment_proposal(p1, path=self.tmpfile)
        append_experiment_proposal(p2, path=self.tmpfile)
        si = load_experiment_proposals(path=self.tmpfile, type_filter="search_insight")
        self.assertEqual(len(si), 1)
        self.assertEqual(si[0]["type"], "search_insight")

    def test_append_writes_one_line(self):
        p = _make_valid_proposal()
        before = os.path.getsize(self.tmpfile) if os.path.exists(self.tmpfile) else 0
        result = append_experiment_proposal(p, path=self.tmpfile)
        after = os.path.getsize(self.tmpfile)
        self.assertEqual(result["status"], "appended")
        self.assertEqual(result["proposal_id"], p["proposal_id"])
        # one new line
        self.assertGreater(after, before)

    def test_append_only_never_mutates_old_lines(self):
        p1 = _make_valid_proposal(title="First")
        append_experiment_proposal(p1, path=self.tmpfile)
        with open(self.tmpfile) as f:
            line1 = f.read()
        p2 = _make_valid_proposal(title="Second")
        append_experiment_proposal(p2, path=self.tmpfile)
        with open(self.tmpfile) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("First", lines[0])
        self.assertIn("Second", lines[1])

    def test_malformed_line_ignored(self):
        with open(self.tmpfile, "w") as f:
            f.write('{"record_type": "broken"\n')
            f.write(json.dumps(_make_valid_proposal()) + "\n")
        result = load_experiment_proposals(path=self.tmpfile)
        self.assertEqual(len(result), 1)

    def test_dedup_key_identifies_duplicates(self):
        p1 = _make_valid_proposal(title="Exact same title")
        p2 = _make_valid_proposal(title="Exact same title")
        self.assertEqual(proposal_dedup_key(p1), proposal_dedup_key(p2))

    def test_dedup_key_different_on_title(self):
        p1 = _make_valid_proposal(title="Title A")
        p2 = _make_valid_proposal(title="Title B")
        self.assertNotEqual(proposal_dedup_key(p1), proposal_dedup_key(p2))

    def test_proposal_exists_false_for_empty(self):
        p = _make_valid_proposal()
        self.assertFalse(proposal_exists(p, path=self.tmpfile))

    def test_proposal_exists_true_after_append(self):
        p = _make_valid_proposal()
        append_experiment_proposal(p, path=self.tmpfile)
        self.assertTrue(proposal_exists(p, path=self.tmpfile))

    def test_append_if_new_skips_duplicate(self):
        p = _make_valid_proposal()
        r1 = append_if_new(p, path=self.tmpfile)
        self.assertEqual(r1["status"], "appended")
        r2 = append_if_new(p, path=self.tmpfile)
        self.assertEqual(r2["status"], "skipped_duplicate")

    def test_append_if_new_appends_non_duplicate(self):
        p1 = _make_valid_proposal(title="Title A")
        p2 = _make_valid_proposal(title="Title B")
        r1 = append_if_new(p1, path=self.tmpfile)
        r2 = append_if_new(p2, path=self.tmpfile)
        self.assertEqual(r1["status"], "appended")
        self.assertEqual(r2["status"], "appended")

    def test_validation_fails_on_invalid_record(self):
        p = _make_valid_proposal()
        del p["confidence"]
        with self.assertRaises(ValueError) as ctx:
            append_experiment_proposal(p, path=self.tmpfile)
        self.assertIn("validation failed", str(ctx.exception))


# ---------------------------------------------------------------------------
# Safety tests
# ---------------------------------------------------------------------------

class TestSafety(unittest.TestCase):
    def test_no_ollama_imports_in_schema(self):
        with open("weslr/experiment_proposal_schema.py") as f:
            content = f.read()
        self.assertNotIn("import ollama", content.lower())
        self.assertNotIn("from ollama", content.lower())
        self.assertNotIn("import openai", content.lower())

    def test_no_ollama_imports_in_store(self):
        with open("weslr/experiment_proposal_store.py") as f:
            content = f.read()
        self.assertNotIn("import ollama", content.lower())
        self.assertNotIn("from ollama", content.lower())
        self.assertNotIn("import openai", content.lower())

    def test_no_governance_jsonl_writes_in_store(self):
        """Store should only write to experiment_proposals.jsonl, not governance logs."""
        with open("weslr/experiment_proposal_store.py") as f:
            content = f.read()
        governance_files = [
            "contract_observations.jsonl",
            "contract_insufficiency_log.jsonl",
            "contract_proposal_review_log.jsonl",
            "public_signals.jsonl",
            "proposal_trace.jsonl",
            "implementation_plans.jsonl",
            "operator_feedback_log.jsonl",
        ]
        for fname in governance_files:
            self.assertNotIn(fname, content)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
