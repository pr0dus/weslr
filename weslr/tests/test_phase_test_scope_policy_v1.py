#!/usr/bin/env python3
"""Tests for WESLR phase test scope policy V1."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_DOC = ROOT / "docs" / "WESLR_PHASE_TEST_SCOPE_POLICY_V1.md"

ALLOWED_CHANGED = {
    "docs/WESLR_PHASE_TEST_SCOPE_POLICY_V1.md",
    "weslr/tests/test_phase_test_scope_policy_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/pending_messages_queue.py",
    "openclaw.json",
    ".openclaw/config.json",
}

REQUIRED_POLICY_PHRASES = {
    "Phase-specific changed-file assertions are valid only during that phase's final validation.",
    "They should not be used as permanent regression tests that fail future approved files.",
    "Future durable tests should validate behavior, schemas, safety flags, boundaries, and forbidden side effects.",
    "Scope checks for \"allowed changed files\" belong in operator workflow, release gate staged-scope checks, or temporary phase validation.",
    "the AI audit schema/helper tests failed because they expected previous-step changed files while a new approved inventory phase was staged.",
    "This was a process/test-scope issue, not an implementation failure.",
}


class PhaseTestScopePolicyV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_policy_doc_exists(self):
        self.assertTrue(POLICY_DOC.exists())

    def test_02_required_policy_phrases_present(self):
        text = POLICY_DOC.read_text(encoding="utf-8")
        for phrase in REQUIRED_POLICY_PHRASES:
            self.assertIn(phrase, text)

    def test_03_policy_distinguishes_durable_tests_from_phase_scope(self):
        text = POLICY_DOC.read_text(encoding="utf-8").lower()
        self.assertIn("durable tests", text)
        self.assertIn("temporary phase validation", text)
        self.assertIn("release gate staged-scope checks", text)

    def test_04_policy_preserves_safety_boundary_terms(self):
        text = POLICY_DOC.read_text(encoding="utf-8").lower()
        for term in (
            "protected test item",
            "answer-key",
            "official or clinical score claims",
            "benchmark tuning",
            "runtime/chat/voice behavior changes",
            "redacted/count-only summaries",
        ):
            self.assertIn(term, text)

    def test_05_only_policy_files_changed(self):
        changed = self.git_changed_files()
        self.assertTrue(changed.issubset(ALLOWED_CHANGED), sorted(changed - ALLOWED_CHANGED))
        self.assertFalse(changed & FORBIDDEN_CHANGED, sorted(changed & FORBIDDEN_CHANGED))


if __name__ == "__main__":
    unittest.main(verbosity=2)
