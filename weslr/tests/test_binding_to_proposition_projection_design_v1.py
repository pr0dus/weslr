from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_BINDING_TO_PROPOSITION_PROJECTION_DESIGN_V1.md"


class BindingToPropositionProjectionDesignV1Tests(unittest.TestCase):
    def _doc(self) -> str:
        return DOC.read_text(encoding="utf-8")

    def test_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_required_title_and_status(self):
        text = self._doc()
        for needle in [
            "Binding-to-Proposition Projection Design V1",
            "design_only",
            "execution_allowed = false",
            "official_score_claimed = false",
        ]:
            self.assertIn(needle, text)

    def test_projection_rules_present(self):
        text = self._doc()
        self.assertIn("ChoiceStemBindingCandidate → PropositionCandidate", text)
        self.assertIn("PredicateCandidate → PropositionCandidate", text)
        self.assertIn("projection-ready", text)

    def test_all_binding_types_present(self):
        text = self._doc()
        for needle in [
            "choice_completes_question_predicate",
            "choice_supplies_subject",
            "choice_supplies_object",
            "choice_supplies_conclusion",
            "choice_is_full_claim",
            "choice_is_fragment_unknown",
            "unsupported_binding",
        ]:
            self.assertIn(needle, text)

    def test_anti_gaming_boundaries_present(self):
        text = self._doc().lower()
        for needle in [
            "no answer-key use",
            "no answer keys",
            "no item ids as authority",
            "no benchmark-specific tuning",
            "no answer selection",
            "no official score claim",
        ]:
            self.assertIn(needle, text)

    def test_no_runtime_integration(self):
        text = self._doc().lower()
        self.assertIn("no runtime integration", text)

    def test_operator_decision_options_present(self):
        text = self._doc()
        for needle in [
            "APPROVE_BINDING_TO_PROPOSITION_HELPERS_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(needle, text)

    def test_no_forbidden_implementation_files_changed(self):
        forbidden = {
            "weslr/choice_stem_binding.py",
            "weslr/logic_teaching_spine.py",
            "weslr/logical_form_normalizer.py",
            "weslr/formal_logic_parser.py",
            "weslr/formal_logic_solver.py",
            "weslr/evals/official_mcq_adapter.py",
        }
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        self.assertFalse(changed & forbidden, f"Forbidden files changed: {sorted(changed & forbidden)}")


if __name__ == "__main__":
    unittest.main()
