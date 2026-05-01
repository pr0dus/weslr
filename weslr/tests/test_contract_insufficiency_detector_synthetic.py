"""
WESLR Contract Insufficiency Detector V1 — Synthetic Fixture Validation

Strict rules:
- Do NOT write to weslr/contract_observations.jsonl
- Do NOT modify public_signals.jsonl
- Do NOT trigger /chat behavior changes
- Do NOT create proposals
- Do NOT use LLM
- Use only synthetic test fixture

Cases:
1. no detection under threshold (window < 10)
2. weak_entry_repetition detected (>= 3 occurrences, null/S4 only, entry frame)
3. fallback_repetition detected
4. mixed S1/S2 signal prevents detection
5. window < 10 records prevents detection
6. stable_across_checks reaches 3 (consecutive detections)
7. proposal_ready becomes true only after stability threshold
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
FIXTURE_PATH = _workspace / "weslr/tests/fixtures/synthetic_contract_observations.jsonl"


def _reload():
    for mod in ("weslr.contract_insufficiency_detector",):
        try:
            importlib.reload(importlib.import_module(mod))
        except Exception:
            pass


def _make_record(**kw):
    defaults = dict(
        record_type="contract_observation_v1",
        response_contract="conversational_entry",
        interaction_frame="entry",
        turn_type="greeting",
        reply_shape="conversational_entry",
        signal_type=None,
        response_path="fallback_safe",
        source="website_public",
        safe_to_record=True,
        raw_prompt_stored=False,
        pii_stored=False,
        behavior_change_allowed=False,
        value_inference_allowed=False,
        timestamp="2026-04-30T18:00:00Z",
        session_id_hash="aabbcc",
    )
    defaults.update(kw)
    return defaults


class TestCase1WindowTooSmall(unittest.TestCase):
    """Case 1 + Case 5: window < 10 prevents detection."""

    def setUp(self):
        _reload()
        from weslr.contract_insufficiency_detector import detect_insufficiency
        self.detect = detect_insufficiency

    def test_window_too_small_returns_no_result(self):
        """Window < 10 records: detector must return insufficiency_found=false."""
        tmpdir = tempfile.mkdtemp()
        obs = pathlib.Path(tmpdir) / "obs.jsonl"
        log = pathlib.Path(tmpdir) / "log.jsonl"
        try:
            # Write 9 records (below min_records=10)
            records = [_make_record(session_id_hash=f"h{i}") for i in range(9)]
            with open(obs, "w") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")

            result = self.detect(str(obs), insufficiency_log_path=str(log), window_size=50, min_records=10)
            self.assertFalse(result["insufficiency_found"])
            self.assertEqual(result["window_records"], 9)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestCase2WeakEntryRepetition(unittest.TestCase):
    """Case 2: weak_entry_repetition detected."""

    def setUp(self):
        _reload()
        from weslr.contract_insufficiency_detector import detect_insufficiency
        self.detect = detect_insufficiency

    def test_weak_entry_repetition_detected(self):
        """>= 3 same contract + entry frame + null/S4 signals + same path = detected."""
        tmpdir = tempfile.mkdtemp()
        obs = pathlib.Path(tmpdir) / "obs.jsonl"
        log = pathlib.Path(tmpdir) / "log.jsonl"
        try:
            records = [
                _make_record(
                    response_contract="conversational_entry",
                    interaction_frame="entry",
                    signal_type=None,
                    response_path="fallback_safe",
                    session_id_hash=f"h{i}",
                    timestamp=f"2026-04-30T18:00:{i:02d}Z",
                )
                for i in range(10)
            ]
            with open(obs, "w") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")

            result = self.detect(str(obs), insufficiency_log_path=str(log), window_size=50, min_records=10)
            self.assertTrue(result["insufficiency_found"])
            self.assertIn("conversational_entry", result["contracts_checked"])
            pattern = result["proposal_ready_patterns"][0]
            self.assertEqual(pattern["pattern_type"], "weak_entry_repetition")
            self.assertEqual(pattern["contract"], "conversational_entry")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestCase3FallbackRepetition(unittest.TestCase):
    """Case 3: fallback_repetition detected."""

    def setUp(self):
        _reload()
        from weslr.contract_insufficiency_detector import detect_insufficiency
        self.detect = detect_insufficiency

    def test_fallback_repetition_detected(self):
        """fallback_safe contract + unknown frame + null/S4 = fallback_repetition."""
        tmpdir = tempfile.mkdtemp()
        obs = pathlib.Path(tmpdir) / "obs.jsonl"
        log = pathlib.Path(tmpdir) / "log.jsonl"
        try:
            records = [
                _make_record(
                    response_contract="fallback_safe",
                    interaction_frame="unknown",
                    signal_type=None,
                    response_path="fallback_safe",
                    session_id_hash=f"h{i}",
                    timestamp=f"2026-04-30T18:00:{i:02d}Z",
                )
                for i in range(10)
            ]
            with open(obs, "w") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")

            result = self.detect(str(obs), insufficiency_log_path=str(log), window_size=50, min_records=10)
            self.assertTrue(result["insufficiency_found"])
            pattern = result["proposal_ready_patterns"][0]
            self.assertEqual(pattern["pattern_type"], "fallback_repetition")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestCase4MixedS1S2PreventsDetection(unittest.TestCase):
    """Case 4: mixed S1/S2 signals block detection even with weak frames."""

    def setUp(self):
        _reload()
        from weslr.contract_insufficiency_detector import detect_insufficiency
        self.detect = detect_insufficiency

    def test_s1_signal_blocks_detection(self):
        """S1 signal mixed in → IC3 fails → no detection."""
        tmpdir = tempfile.mkdtemp()
        obs = pathlib.Path(tmpdir) / "obs.jsonl"
        log = pathlib.Path(tmpdir) / "log.jsonl"
        try:
            records = [
                _make_record(
                    response_contract="conversational_entry",
                    interaction_frame="entry",
                    signal_type="S1",  # S1 should unblock the pattern
                    response_path="fallback_safe",
                    session_id_hash=f"h{i}",
                    timestamp=f"2026-04-30T18:00:{i:02d}Z",
                )
                for i in range(10)
            ]
            with open(obs, "w") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")

            result = self.detect(str(obs), insufficiency_log_path=str(log), window_size=50, min_records=10)
            self.assertFalse(result["insufficiency_found"])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_s2_signal_blocks_detection(self):
        """S2 signal mixed in → IC3 fails → no detection."""
        tmpdir = tempfile.mkdtemp()
        obs = pathlib.Path(tmpdir) / "obs.jsonl"
        log = pathlib.Path(tmpdir) / "log.jsonl"
        try:
            records = [
                _make_record(
                    response_contract="conversational_entry",
                    interaction_frame="entry",
                    signal_type="S2",
                    response_path="fallback_safe",
                    session_id_hash=f"h{i}",
                    timestamp=f"2026-04-30T18:00:{i:02d}Z",
                )
                for i in range(10)
            ]
            with open(obs, "w") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")

            result = self.detect(str(obs), insufficiency_log_path=str(log), window_size=50, min_records=10)
            self.assertFalse(result["insufficiency_found"])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestCase6StabilityReachesThreshold(unittest.TestCase):
    """Case 6 + Case 7: stability tracker reaches 3 → proposal_ready=true."""

    def setUp(self):
        _reload()
        from weslr.contract_insufficiency_detector import (
            detect_insufficiency,
            check_stability,
            _STABILITY_COUNTS,
            _STABLE_PATTERNS,
        )
        self.detect = detect_insufficiency
        self.check_stability = check_stability
        # Reset stability state between tests
        _STABILITY_COUNTS.clear()
        _STABLE_PATTERNS.clear()

    def test_stability_increments_across_checks(self):
        """check_stability increments consecutive_checks on each call."""
        evidence = _make_record(
            response_contract="conversational_entry",
            interaction_frame="entry",
            signal_type=None,
            response_path="fallback_safe",
        )

        # Check 1
        r1 = self.check_stability("weak_entry_repetition", "conversational_entry", evidence)
        self.assertEqual(r1["consecutive_checks"], 1)
        self.assertFalse(r1["stable"])
        self.assertFalse(r1["proposal_ready"])

        # Check 2
        r2 = self.check_stability("weak_entry_repetition", "conversational_entry", evidence)
        self.assertEqual(r2["consecutive_checks"], 2)
        self.assertFalse(r2["stable"])
        self.assertFalse(r2["proposal_ready"])

    def test_stability_reaches_threshold_at_3(self):
        """Check 3: consecutive_checks=3 → stable=true, proposal_ready=true."""
        evidence = _make_record(
            response_contract="conversational_entry",
            interaction_frame="entry",
            signal_type=None,
            response_path="fallback_safe",
        )

        self.check_stability("weak_entry_repetition", "conversational_entry", evidence)
        self.check_stability("weak_entry_repetition", "conversational_entry", evidence)
        r3 = self.check_stability("weak_entry_repetition", "conversational_entry", evidence)

        self.assertEqual(r3["consecutive_checks"], 3)
        self.assertTrue(r3["stable"])
        self.assertTrue(r3["proposal_ready"])
        self.assertEqual(r3["min_checks_required"], 3)

    def test_proposal_ready_only_after_stability_threshold(self):
        """proposal_ready=true ONLY after consecutive_checks >= 3."""
        evidence = _make_record(
            response_contract="conversational_entry",
            interaction_frame="entry",
            signal_type=None,
            response_path="fallback_safe",
        )

        r1 = self.check_stability("weak_entry_repetition", "conversational_entry", evidence)
        self.assertFalse(r1["proposal_ready"])

        r2 = self.check_stability("weak_entry_repetition", "conversational_entry", evidence)
        self.assertFalse(r2["proposal_ready"])

        r3 = self.check_stability("weak_entry_repetition", "conversational_entry", evidence)
        self.assertTrue(r3["proposal_ready"])


class TestRealObservationsFileUntouched(unittest.TestCase):
    """Confirm real contract_observations.jsonl is never modified."""

    def test_real_file_not_created_by_detector(self):
        """Running detector does not create weslr/contract_observations.jsonl."""
        real_path = _workspace / "weslr/contract_observations.jsonl"
        existed_before = real_path.exists()
        content_before = real_path.read_text() if existed_before else None

        _reload()
        from weslr.contract_insufficiency_detector import detect_insufficiency
        tmpdir = tempfile.mkdtemp()
        obs = pathlib.Path(tmpdir) / "obs.jsonl"
        log = pathlib.Path(tmpdir) / "log.jsonl"
        try:
            # Run detector against temp fixture
            records = [_make_record(session_id_hash=f"h{i}") for i in range(10)]
            with open(obs, "w") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")
            detect_insufficiency(str(obs), insufficiency_log_path=str(log), window_size=50, min_records=10)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        existed_after = real_path.exists()
        content_after = real_path.read_text() if existed_after else None
        # Key invariant: file content must not change regardless of before state
        if content_before is not None:
            self.assertEqual(content_before, content_after, "contract_observations.jsonl content was modified!")
        else:
            self.assertFalse(existed_after, "contract_observations.jsonl was created by detector!")


class TestDeterministicOutput(unittest.TestCase):
    """Case 15: deterministic output for same input."""

    def setUp(self):
        _reload()
        from weslr.contract_insufficiency_detector import detect_insufficiency
        self.detect = detect_insufficiency

    def test_deterministic_same_input_same_output(self):
        """Two runs with identical records produce identical output."""
        tmpdir = tempfile.mkdtemp()
        obs = pathlib.Path(tmpdir) / "obs.jsonl"
        log = pathlib.Path(tmpdir) / "log.jsonl"
        try:
            records = [
                _make_record(
                    response_contract="conversational_entry",
                    interaction_frame="entry",
                    signal_type=None,
                    response_path="fallback_safe",
                    session_id_hash=f"h{i}",
                )
                for i in range(12)
            ]
            with open(obs, "w") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")

            result1 = self.detect(str(obs), insufficiency_log_path=str(log), window_size=50, min_records=10)
            result2 = self.detect(str(obs), insufficiency_log_path=str(log), window_size=50, min_records=10)

            # Remove timestamp-dependent fields for comparison
            r1 = {k: v for k, v in result1.items() if k != "checked_at"}
            r2 = {k: v for k, v in result2.items() if k != "checked_at"}
            self.assertEqual(r1, r2)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestNoProductionTruthModified(unittest.TestCase):
    """Confirm production truth JSONL files are never written by detector."""

    def setUp(self):
        _reload()
        from weslr.contract_insufficiency_detector import detect_insufficiency
        self.detect = detect_insufficiency

    PRODUCTION_FILES = [
        "proposal_trace.jsonl",
        "implementation_plans.jsonl",
        "diagnostic_records.jsonl",
        "state_checkpoint.json",
        "public_signals.jsonl",
    ]

    def test_production_files_unmodified(self):
        """Running detector must not touch any production truth files."""
        production_paths = [_workspace / "weslr" / f for f in self.PRODUCTION_FILES]
        before = {str(p): p.exists() for p in production_paths}
        for p in production_paths:
            if p.exists():
                with open(p) as f:
                    before[str(p)] = f.read()

        _reload()
        tmpdir = tempfile.mkdtemp()
        obs = pathlib.Path(tmpdir) / "obs.jsonl"
        log = pathlib.Path(tmpdir) / "log.jsonl"
        try:
            records = [_make_record(session_id_hash=f"h{i}") for i in range(12)]
            with open(obs, "w") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")
            self.detect(str(obs), insufficiency_log_path=str(log), window_size=50, min_records=10)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        for p in production_paths:
            if p.exists():
                with open(p) as f:
                    after = f.read()
                self.assertEqual(before[str(p)], after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
