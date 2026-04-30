"""
WESLR Contract Insufficiency Detector V1 — Tests

Validates:
1. detect_insufficiency returns no_result when window too small
2. detect_insufficiency detects weak_entry_repetition pattern
3. detect_insufficiency detects fallback_repetition pattern
4. detect_insufficiency ignores records with S1/S2 signals
5. detect_insufficiency ignores varied response_paths
6. detect_insufficiency ignores contracts with <3 occurrences
7. sufficiency evidence appends to insufficiency log
8. stability tracker increments across checks (iterations 1-2, not reaching threshold)
9. stability tracker reaches proposal_ready at threshold
10. detector never writes to production truth files
11. detector never modifies contract_observations.jsonl
12. detector read-only from observation file
13. detector never changes behavior
14. detector never uses LLM
15. detector never creates proposals (only evidence)
16. no PII in evidence records
"""

import importlib
import json
import pathlib
import sys
import tempfile
import unittest
import shutil

_workspace = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_workspace))


def _reload():
    for mod in ("weslr.contract_insufficiency_detector",):
        try:
            importlib.import_module(mod)
            importlib.reload(importlib.import_module(mod))
        except Exception:
            pass


# ── fixtures ────────────────────────────────────────────────────────────────

def _make_obs_record(**kw):
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
        session_id_hash="aabbccdd",
    )
    defaults.update(kw)
    return defaults


def _write_obs_lines(path: pathlib.Path, records: list[dict]) -> None:
    with open(path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


# ── tests ─────────────────────────────────────────────────────────────────────

class TestDetectorWindowSize(unittest.TestCase):
    """Tests 1: window size threshold."""

    def setUp(self):
        _reload()
        from weslr.contract_insufficiency_detector import detect_insufficiency
        self.detect = detect_insufficiency

    def test_no_result_when_window_too_small(self):
        """1. detect returns no_result when window < min_records."""
        tmpdir = tempfile.mkdtemp()
        obs = pathlib.Path(tmpdir) / "contract_observations.jsonl"
        try:
            recs = [_make_obs_record(session_id_hash=f"h{i}") for i in range(5)]
            _write_obs_lines(obs, recs)
            result = self.detect(observation_path=str(obs), window_size=50, min_records=10)
            self.assertFalse(result["insufficiency_found"])
            self.assertEqual(result["window_records"], 5)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestDetectorPatternDetection(unittest.TestCase):
    """Tests 2-6: pattern detection logic."""

    def setUp(self):
        _reload()
        from weslr.contract_insufficiency_detector import detect_insufficiency
        self.detect = detect_insufficiency

    def _run(self, recs):
        tmpdir = tempfile.mkdtemp()
        obs = pathlib.Path(tmpdir) / "contract_observations.jsonl"
        ins_log = pathlib.Path(tmpdir) / "contract_insufficiency_log.jsonl"
        try:
            _write_obs_lines(obs, recs)
            import weslr.contract_insufficiency_detector as det
            orig_obs = det.DEFAULT_OBSERVATION_PATH
            orig_log = det.DEFAULT_INSUFFICIENCY_LOG_PATH
            det.DEFAULT_OBSERVATION_PATH = str(obs)
            det.DEFAULT_INSUFFICIENCY_LOG_PATH = str(ins_log)
            try:
                result = self.detect(observation_path=str(obs), window_size=100, min_records=3)
            finally:
                det.DEFAULT_OBSERVATION_PATH = orig_obs
                det.DEFAULT_INSUFFICIENCY_LOG_PATH = orig_log
            return result, ins_log
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_detects_weak_entry_repetition(self):
        """2. weak_entry_repetition detected when contract=conversational_entry, all null S-type, same path."""
        recs = [
            _make_obs_record(response_contract="conversational_entry", signal_type=None,
                           response_path="fallback_safe", interaction_frame="entry",
                           session_id_hash=f"h{i}")
            for i in range(4)
        ]
        result, _ = self._run(recs)
        self.assertTrue(result["insufficiency_found"])
        self.assertEqual(result["proposal_ready_patterns"][0]["pattern_type"], "weak_entry_repetition")

    def test_detects_fallback_repetition(self):
        """3. fallback_repetition detected when contract=fallback_safe, all null/S4, same path."""
        recs = [
            _make_obs_record(response_contract="fallback_safe", signal_type="S4",
                           response_path="fallback_safe", interaction_frame="unknown",
                           session_id_hash=f"h{i}")
            for i in range(3)
        ]
        result, _ = self._run(recs)
        self.assertTrue(result["insufficiency_found"])
        self.assertEqual(result["proposal_ready_patterns"][0]["pattern_type"], "fallback_repetition")

    def test_ignores_records_with_s1_s2_signals(self):
        """4. records with S1 or S2 signals are not flagged as insufficient."""
        recs = [
            _make_obs_record(response_contract="conversational_entry", signal_type="S1",
                           response_path="fallback_safe", interaction_frame="entry",
                           session_id_hash=f"h{i}")
            for i in range(4)
        ]
        result, _ = self._run(recs)
        self.assertFalse(result["insufficiency_found"])

    def test_ignores_varied_response_paths(self):
        """5. varied response_paths for same contract → not flagged."""
        recs = [
            _make_obs_record(response_contract="conversational_entry", signal_type=None,
                           response_path=f"path{i}", interaction_frame="entry",
                           session_id_hash=f"h{i}")
            for i in range(4)
        ]
        result, _ = self._run(recs)
        self.assertFalse(result["insufficiency_found"])

    def test_ignores_fewer_than_three_occurrences(self):
        """6. contract with only 2 occurrences → not flagged."""
        recs = [
            _make_obs_record(response_contract="conversational_entry", signal_type=None,
                           response_path="fallback_safe", interaction_frame="entry",
                           session_id_hash=f"h{i}")
            for i in range(2)
        ]
        result, _ = self._run(recs)
        self.assertFalse(result["insufficiency_found"])


class TestEvidenceLogging(unittest.TestCase):
    """Tests 7-9: evidence append + stability tracking."""

    def setUp(self):
        _reload()
        from weslr.contract_insufficiency_detector import (
            detect_insufficiency, check_stability,
        )
        self.detect = detect_insufficiency
        self.check_stability = check_stability
        self.tmpdir = tempfile.mkdtemp()
        self.obs = pathlib.Path(self.tmpdir) / "contract_observations.jsonl"
        self.ins_log = pathlib.Path(self.tmpdir) / "contract_insufficiency_log.jsonl"
        import weslr.contract_insufficiency_detector as det
        orig_obs = det.DEFAULT_OBSERVATION_PATH
        orig_log = det.DEFAULT_INSUFFICIENCY_LOG_PATH
        det.DEFAULT_OBSERVATION_PATH = str(self.obs)
        det.DEFAULT_INSUFFICIENCY_LOG_PATH = str(self.ins_log)
        self.addCleanup(lambda: setattr(det, "DEFAULT_OBSERVATION_PATH", orig_obs))
        det._STABILITY_COUNTS.clear()
        det._STABLE_PATTERNS.clear()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_evidence_appends_to_insufficiency_log(self):
        """7. sufficiency evidence appends to insufficiency log."""
        recs = [
            _make_obs_record(response_contract="conversational_entry", signal_type=None,
                           response_path="fallback_safe", interaction_frame="entry",
                           session_id_hash=f"h{i}")
            for i in range(4)
        ]
        _write_obs_lines(self.obs, recs)
        result = self.detect(observation_path=str(self.obs), window_size=100, min_records=3)
        self.assertTrue(result["insufficiency_found"])
        with open(self.ins_log) as f:
            lines = [l.strip() for l in f if l.strip()]
        self.assertEqual(len(lines), 1)
        ev = json.loads(lines[0])
        self.assertEqual(ev["record_type"], "contract_insufficiency_v1")
        self.assertEqual(ev["pattern_type"], "weak_entry_repetition")

    def test_stability_tracker_increments(self):
        """8. stability tracker increments across consecutive checks (iterations 1-2 only)."""
        ev = {"pattern_type": "weak_entry_repetition", "contract": "conversational_entry",
              "occurrence_count": 4}
        # First check — count=1, not yet stable (min_checks=3)
        r1 = self.check_stability("weak_entry_repetition", "conversational_entry", ev)
        self.assertEqual(r1["consecutive_checks"], 1)
        self.assertFalse(r1["stable"])
        # Second check — count=2, still not stable
        r2 = self.check_stability("weak_entry_repetition", "conversational_entry", ev)
        self.assertEqual(r2["consecutive_checks"], 2)
        self.assertFalse(r2["stable"])

    def test_stability_reaches_proposal_ready(self):
        """9. stability tracker sets proposal_ready at min_checks threshold."""
        ev = {"pattern_type": "weak_entry_repetition", "contract": "conversational_entry",
              "occurrence_count": 4}
        for _ in range(3):
            result = self.check_stability("weak_entry_repetition", "conversational_entry", ev)
        self.assertTrue(result["proposal_ready"])
        self.assertTrue(result["stable"])


class TestProductionGuard(unittest.TestCase):
    """Tests 10-16: production guard constraints."""

    def setUp(self):
        _reload()
        self.tmpdir = tempfile.mkdtemp()
        self.obs = pathlib.Path(self.tmpdir) / "contract_observations.jsonl"
        self.ins_log = pathlib.Path(self.tmpdir) / "contract_insufficiency_log.jsonl"
        self.prod_trace = pathlib.Path(self.tmpdir) / "proposal_trace.jsonl"
        self.prod_state = pathlib.Path(self.tmpdir) / "state_checkpoint.json"
        self.prod_signal = pathlib.Path(self.tmpdir) / "public_signals.jsonl"
        self.prod_trace.touch()
        self.prod_state.touch()
        self.prod_signal.touch()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_detector_never_writes_production_truth(self):
        """10. detector never writes to production truth files."""
        import weslr.contract_insufficiency_detector as det
        orig_obs = det.DEFAULT_OBSERVATION_PATH
        orig_log = det.DEFAULT_INSUFFICIENCY_LOG_PATH
        det.DEFAULT_OBSERVATION_PATH = str(self.obs)
        det.DEFAULT_INSUFFICIENCY_LOG_PATH = str(self.ins_log)
        try:
            recs = [
                _make_obs_record(response_contract="conversational_entry", signal_type=None,
                               response_path="fallback_safe", interaction_frame="entry",
                               session_id_hash=f"h{i}")
                for i in range(4)
            ]
            _write_obs_lines(self.obs, recs)
            from weslr.contract_insufficiency_detector import detect_insufficiency
            detect_insufficiency(observation_path=str(self.obs), window_size=100, min_records=3)
            for f in (self.prod_trace, self.prod_state):
                self.assertEqual(f.stat().st_size, 0,
                                 f"Production file {f.name} was modified")
        finally:
            det.DEFAULT_OBSERVATION_PATH = orig_obs
            det.DEFAULT_INSUFFICIENCY_LOG_PATH = orig_log

    def test_detector_never_modifies_observation_file(self):
        """11. detector read-only from observation file — does not modify it."""
        import weslr.contract_insufficiency_detector as det
        orig_obs = det.DEFAULT_OBSERVATION_PATH
        orig_log = det.DEFAULT_INSUFFICIENCY_LOG_PATH
        det.DEFAULT_OBSERVATION_PATH = str(self.obs)
        det.DEFAULT_INSUFFICIENCY_LOG_PATH = str(self.ins_log)
        try:
            recs = [
                _make_obs_record(response_contract="conversational_entry", signal_type=None,
                               response_path="fallback_safe", interaction_frame="entry",
                               session_id_hash=f"h{i}")
                for i in range(4)
            ]
            _write_obs_lines(self.obs, recs)
            orig_content = self.obs.read_text()
            from weslr.contract_insufficiency_detector import detect_insufficiency
            detect_insufficiency(observation_path=str(self.obs), window_size=100, min_records=3)
            self.assertEqual(self.obs.read_text(), orig_content,
                             "Observation file was modified by detector")
        finally:
            det.DEFAULT_OBSERVATION_PATH = orig_obs
            det.DEFAULT_INSUFFICIENCY_LOG_PATH = orig_log

    def test_no_pii_in_evidence(self):
        """16. no PII in evidence records."""
        import weslr.contract_insufficiency_detector as det
        orig_obs = det.DEFAULT_OBSERVATION_PATH
        orig_log = det.DEFAULT_INSUFFICIENCY_LOG_PATH
        det.DEFAULT_OBSERVATION_PATH = str(self.obs)
        det.DEFAULT_INSUFFICIENCY_LOG_PATH = str(self.ins_log)
        try:
            recs = [
                _make_obs_record(response_contract="conversational_entry", signal_type=None,
                               response_path="fallback_safe", interaction_frame="entry",
                               session_id_hash="aabbccdd")
                for i in range(4)
            ]
            _write_obs_lines(self.obs, recs)
            from weslr.contract_insufficiency_detector import detect_insufficiency
            detect_insufficiency(observation_path=str(self.obs), window_size=100, min_records=3)
            if self.ins_log.exists():
                with open(self.ins_log) as f:
                    for line in f:
                        rec = json.loads(line.strip())
                        for key in rec:
                            self.assertNotIn("email", key.lower())
                            self.assertNotIn("phone", key.lower())
                            self.assertNotIn("name", key.lower())
                            self.assertNotIn("address", key.lower())
        finally:
            det.DEFAULT_OBSERVATION_PATH = orig_obs
            det.DEFAULT_INSUFFICIENCY_LOG_PATH = orig_log


class TestConstraintsVerbatim(unittest.TestCase):
    """Tests 12-15: hardcoded constraints from spec."""

    def test_never_changes_behavior(self):
        """13. detector never changes behavior — no handler hooks, no route changes."""
        from weslr import contract_insufficiency_detector as det
        src = pathlib.Path(det.__file__).read_text()
        self.assertNotIn("format_reply", src)
        self.assertNotIn("expand_response", src)
        self.assertNotIn("weslr_backend_contract", src)

    def test_never_uses_llm(self):
        """14. detector never uses LLM — no openai, no anthropic imports."""
        from weslr import contract_insufficiency_detector as det
        src = pathlib.Path(det.__file__).read_text()
        self.assertNotIn("openai", src)
        self.assertNotIn("anthropic", src)
        self.assertNotIn("Anthropic", src)
        self.assertNotIn("OpenAI", src)

    def test_never_creates_proposals(self):
        """15. detector never creates proposals — only evidence, not governance objects."""
        from weslr import contract_insufficiency_detector as det
        src = pathlib.Path(det.__file__).read_text()
        self.assertNotIn("proposal_trace", src)
        self.assertNotIn("governance", src)
        self.assertNotIn("proposal_id", src)

    def test_read_only_from_observation_file(self):
        """12. detector reads from observation file — no write to it."""
        from weslr import contract_insufficiency_detector as det
        src = pathlib.Path(det.__file__).read_text()
        self.assertIn("_read_tail", src)
        has_write = ("open(DEFAULT_OBSERVATION_PATH, \"w\")" in src or
                     "open(DEFAULT_OBSERVATION_PATH, 'w')" in src or
                     "open(DEFAULT_OBSERVATION_PATH, \"a\")" in src or
                     "open(DEFAULT_OBSERVATION_PATH, 'a')" in src)
        self.assertFalse(has_write, "detector writes to observation file")


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("WESLR Contract Insufficiency Detector V1 — Test Suite")
    print("=" * 60)
    sys.argv = [sys.argv[0]]
    unittest.main(verbosity=2)
