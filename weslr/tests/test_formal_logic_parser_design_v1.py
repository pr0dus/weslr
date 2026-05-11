from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC = ROOT / "docs/WESLR_FORMAL_LOGIC_PARSER_V1.md"


class FormalLogicParserDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")

    def test_document_exists(self):
        self.assertTrue(DOC.exists())

    def test_contains_formal_logic_parser_v1(self):
        self.assertIn("FormalLogicParser V1", self.text)

    def test_contains_natural_language_logical_form_extraction(self):
        self.assertIn("natural_language_logical_form_extraction", self.text)

    def test_contains_diagnosis_evidence_terms(self):
        for term in [
            "no_supported_pattern",
            "natural_language_logical_form_extraction",
            "disjunction_elimination_or_cases",
            "unless_conditionals",
        ]:
            self.assertIn(term, self.text)

    def test_contains_parser_output_schema_terms(self):
        for term in [
            "LogicalFormParse",
            "statements",
            "premises",
            "candidate_conclusions",
            "operators",
            "quantifiers",
            "conditionals",
            "negations",
            "disjunctions",
            "conjunctions",
            "parse_confidence",
            "unsupported_fragments",
            "human_translation",
        ]:
            self.assertIn(term, self.text)

    def test_contains_unless_translation(self):
        self.assertIn("P unless Q", self.text)
        self.assertIn("if not Q then P", self.text)

    def test_contains_disjunction_case_analysis(self):
        for term in ["either/or", "disjunction case split", "elimination of impossible cases"]:
            self.assertIn(term, self.text)

    def test_contains_trace_integration(self):
        for term in ["parsed_statement", "logical_form", "parser_warning", "unsupported_fragment"]:
            self.assertIn(term, self.text)

    def test_contains_cognitive_legibility_boundary(self):
        self.assertIn("Cognitive Legibility Boundary", self.text)

    def test_contains_anti_gaming_boundaries(self):
        for term in [
            "answer-key use",
            "item-id use",
            "benchmark-specific phrase rules",
            "raw benchmark storage by default",
            "official-score claims",
            "answer-position bias",
            "private symbolic authority",
        ]:
            self.assertIn(term, self.text)

    def test_contains_future_implementation_phases(self):
        for term in [
            "parser dataclasses only",
            "parser helper functions",
            "parser redacted diagnostics",
            "FormalLogicSolver consumes parser output",
            "dry-run harness reports parser coverage",
            "arbitrator blocks low-confidence parse",
            "optional MCQ adapter opt-in",
        ]:
            self.assertIn(term, self.text)

    def test_rejects_forbidden_phrases(self):
        forbidden = [
            "WESLR has passed MMLU",
            "official MMLU score",
            "leaderboard score",
            "memorize answer keys",
            "answer-key learning",
        ]
        for term in forbidden:
            self.assertNotIn(term, self.text)


if __name__ == "__main__":
    unittest.main()
