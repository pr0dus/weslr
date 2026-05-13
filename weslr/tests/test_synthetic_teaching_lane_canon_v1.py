from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_SYNTHETIC_TEACHING_LANE_CANON_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_SYNTHETIC_TEACHING_LANE_CANON_V1.md",
    "weslr/tests/test_synthetic_teaching_lane_canon_v1.py",
}
FORBIDDEN_PHASE_2_CHANGED = {
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "weslr/logic_teaching_spine.py",
    "weslr/tests/test_teaching_explanation_style_helpers_v1.py",
    "weslr/tests/test_teaching_explanation_helpers_v1.py",
}


class SyntheticTeachingLaneCanonV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc_text = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
        cls.doc_lower = cls.doc_text.lower()

    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], text=True).splitlines()
        return set(changed + staged + untracked)

    def test_doc_exists(self):
        self.assertTrue(DOC_PATH.exists())

    def test_title_and_status_terms_present(self):
        self.assertIn("Synthetic Teaching Lane Canon V1", self.doc_text)
        self.assertIn("canon_note", self.doc_text)
        self.assertIn("execution_allowed = false", self.doc_text)
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_lane_milestone_present(self):
        self.assertIn("synthetic curriculum → proof step → teaching explanation", self.doc_text)

    def test_metrics_present(self):
        self.assertIn("fixtures: 14", self.doc_text)
        self.assertIn("proof steps: 14", self.doc_text)
        self.assertIn("teaching explanations: 70", self.doc_text)
        self.assertIn("forbidden phrase count: 0", self.doc_text)

    def test_all_five_modes_present_with_exact_beginner_spelling(self):
        for mode in ["beginner", "technical", "academic", "spock", "operator_audit"]:
            self.assertIn(mode, self.doc_text)
        self.assertNotIn("beginer", self.doc_text)

    def test_safety_boundaries_present(self):
        for phrase in [
            "no answer selection",
            "no truth/soundness claim",
            "no official score",
            "no answer-key use",
            "no item-ID authority",
            "no benchmark-specific tuning",
            "no runtime integration",
            "no benchmark text",
        ]:
            self.assertIn(phrase.lower(), self.doc_lower)

    def test_scope_boundaries_present(self):
        for phrase in [
            "synthetic/offline only",
            "internal lane only",
            "not public/runtime ready",
            "not benchmark scoring",
            "not a final proof engine",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_why_this_matters_present(self):
        self.assertIn(
            "controlled teaching-style explanations from governed proof artifacts without relying on an LLM as runtime authority",
            self.doc_text,
        )

    def test_caveats_present(self):
        for phrase in [
            "synthetic only",
            "unsupported gaps still exist",
            "runtime integration requires separate audit",
            "public teaching behavior requires separate safety gates",
            "future work needed for real user-facing logic tutoring",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_recommended_next_phases_present(self):
        for phase in [
            "APPROVE_SYNTHETIC_TEACHING_LANE_READINESS_REVIEW_ONLY",
            "APPROVE_LLM_ADVISOR_MODE_DESIGN_ONLY",
            "APPROVE_UNSUPPORTED_GAP_FOLLOWUP_DESIGN_ONLY",
            "KEEP_SYNTHETIC_TEACHING_INTERNAL_ONLY",
        ]:
            self.assertIn(phase, self.doc_text)

    def test_no_forbidden_implementation_files_changed_in_phase_2(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_PHASE_2_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
