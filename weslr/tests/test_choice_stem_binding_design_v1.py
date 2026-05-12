from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_CHOICE_STEM_BINDING_DESIGN_V1.md"


class ChoiceStemBindingDesignV1Tests(unittest.TestCase):
    def _doc(self) -> str:
        return DOC.read_text(encoding="utf-8")

    def test_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_required_status_and_title(self):
        text = self._doc()
        for needle in [
            "WESLR Choice-Stem Binding Design V1",
            "design_only",
            "execution_allowed = false",
            "official_score_claimed = false",
        ]:
            self.assertIn(needle, text)

    def test_binding_model_and_types(self):
        text = self._doc()
        for needle in [
            "ChoiceStemBindingCandidate",
            "choice_completes_question_predicate",
            "choice_supplies_subject",
            "choice_supplies_object",
            "choice_supplies_conclusion",
            "choice_is_full_claim",
            "choice_is_fragment_unknown",
            "unsupported_binding",
        ]:
            self.assertIn(needle, text)

    def test_anti_gaming_boundaries(self):
        text = self._doc().lower()
        for needle in [
            "no answer keys",
            "no item ids as authority",
            "no item-id authority",
            "no benchmark-specific wording patches",
            "no answer selection",
        ]:
            self.assertIn(needle, text)

    def test_runtime_distinction_and_future_audit(self):
        text = self._doc()
        self.assertIn("not `/chat` integration", text)
        self.assertIn("runtime integration audit", text)

    def test_operator_decision_options(self):
        text = self._doc()
        for needle in [
            "APPROVE_CHOICE_STEM_BINDING_SCHEMA_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(needle, text)

    def test_no_forbidden_implementation_files_changed(self):
        forbidden = {
            "weslr/formal_logic_parser.py",
            "weslr/logical_form_normalizer.py",
            "weslr/logic_teaching_spine.py",
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
