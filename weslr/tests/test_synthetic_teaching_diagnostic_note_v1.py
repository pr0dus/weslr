from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_SYNTHETIC_TEACHING_DIAGNOSTIC_NOTE_V1.md"

FORBIDDEN_CHANGED = {
    "weslr/logic_teaching_spine.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}
ALLOWED_CHANGED = {
    "docs/WESLR_SYNTHETIC_TEACHING_DIAGNOSTIC_NOTE_V1.md",
    "weslr/tests/test_synthetic_teaching_diagnostic_note_v1.py",
}


class SyntheticTeachingDiagnosticNoteV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def git_changed_files(self) -> set[str]:
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only && git ls-files --others --exclude-standard"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}

    def test_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_status_markers_present(self):
        self.assertIn("documentation_only", self.text)
        self.assertIn("execution_allowed = false", self.text)
        self.assertIn("official_score_claimed = false", self.text)

    def test_partial_diagnostic_mentions_six_manual_steps(self):
        self.assertIn("6 manually constructed proof steps", self.text)

    def test_full_diagnostic_mentions_loader(self):
        self.assertIn("load_synthetic_logic_curriculum_v1()", self.text)

    def test_full_diagnostic_mentions_fourteen_fixtures_families(self):
        self.assertIn("14 fixtures/families", self.text)
        self.assertIn("all 14 synthetic curriculum families", self.text)

    def test_mentions_seventy_teaching_explanations(self):
        self.assertIn("70 teaching explanations", self.text)

    def test_mentions_unsupported_gap_count(self):
        self.assertIn("unsupported gap count remains high: 100", self.lower)

    def test_mentions_fallacy_explanation_count(self):
        self.assertIn("fallacy explanation count is 0", self.lower)

    def test_forbids_answer_selection(self):
        self.assertIn("no answer selection", self.lower)

    def test_forbids_truth_soundness_claim(self):
        self.assertIn("no truth/soundness claim", self.lower)

    def test_forbids_official_score(self):
        self.assertIn("no official score", self.lower)

    def test_says_synthetic_offline_only(self):
        self.assertIn("synthetic/offline only", self.lower)

    def test_no_forbidden_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
