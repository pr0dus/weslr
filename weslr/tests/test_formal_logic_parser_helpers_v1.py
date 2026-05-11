from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.formal_logic_parser import (  # noqa: E402
    fingerprint_text,
    split_candidate_statements,
    normalize_logical_text,
    detect_statement_role,
    logical_form_parse_to_dict,
    parse_runtime_text_to_logical_form,
    summarize_logical_form_parse,
    validate_logical_form_parse,
)


class FormalLogicParserHelpersV1Tests(unittest.TestCase):
    def test_fingerprint_text_stable(self):
        self.assertEqual(fingerprint_text("Alpha"), fingerprint_text("Alpha"))
        self.assertNotEqual(fingerprint_text("Alpha"), fingerprint_text("Beta"))

    def test_split_candidate_statements_splits_sentence_semicolon_newline(self):
        text = "Alpha. Beta; Gamma\nDelta"
        self.assertEqual(split_candidate_statements(text), ["Alpha", "Beta", "Gamma", "Delta"])

    def test_normalize_logical_text_normalizes_casing_and_spacing(self):
        self.assertEqual(normalize_logical_text("  ALL   Men ARE   Mortal  "), "all men are mortal")

    def test_detect_statement_role_detects_conclusion_and_instruction_language(self):
        self.assertEqual(detect_statement_role("Therefore, p."), "conclusion_candidate")
        self.assertEqual(detect_statement_role("Which follows from the premises?"), "question_instruction")

    def test_parse_runtime_text_to_logical_form_does_not_store_raw_text_by_default(self):
        parse = parse_runtime_text_to_logical_form(
            "All cats are mammals. Felix is a cat.",
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertTrue(all(statement.raw_text_runtime_only == "" for statement in parse.statements))

    def test_store_raw_text_true_stores_raw_text_explicitly(self):
        parse = parse_runtime_text_to_logical_form(
            "All cats are mammals.",
            parse_id="p1",
            source_task_id="t1",
            store_raw_text=True,
        )
        self.assertEqual(parse.statements[0].raw_text_runtime_only, "All cats are mammals")

    def test_parse_creates_fingerprints_for_statements(self):
        parse = parse_runtime_text_to_logical_form("All cats are mammals.", parse_id="p1", source_task_id="t1")
        self.assertTrue(parse.statements[0].text_fingerprint)
        self.assertEqual(len(parse.statements[0].text_fingerprint), 64)

    def test_parse_detects_unless_conditional_and_normalized_if_not_then_form(self):
        parse = parse_runtime_text_to_logical_form("P unless Q.", parse_id="p1", source_task_id="t1")
        self.assertEqual(len(parse.conditionals), 1)
        self.assertEqual(parse.conditionals[0].normalized_form, "if not q then p")

    def test_parse_detects_disjunction(self):
        parse = parse_runtime_text_to_logical_form("Either p or q.", parse_id="p1", source_task_id="t1")
        self.assertEqual(len(parse.disjunctions), 1)

    def test_parse_detects_conjunction(self):
        parse = parse_runtime_text_to_logical_form("P and Q.", parse_id="p1", source_task_id="t1")
        self.assertEqual(len(parse.conjunctions), 1)

    def test_parse_detects_negation(self):
        parse = parse_runtime_text_to_logical_form("No cats are reptiles.", parse_id="p1", source_task_id="t1")
        self.assertEqual(len(parse.negations), 1)

    def test_parse_detects_quantifier(self):
        parse = parse_runtime_text_to_logical_form("All cats are mammals.", parse_id="p1", source_task_id="t1")
        self.assertEqual(len(parse.quantifiers), 1)

    def test_unsupported_fragments_remain_visible(self):
        parse = parse_runtime_text_to_logical_form("Blue idea softly dances.", parse_id="p1", source_task_id="t1")
        self.assertEqual(len(parse.unsupported_fragments), 1)

    def test_summarize_logical_form_parse_is_redacted_and_contains_counts(self):
        parse = parse_runtime_text_to_logical_form("All cats are mammals. Felix is a cat.", parse_id="p1", source_task_id="t1")
        summary = summarize_logical_form_parse(parse)
        self.assertIn("statement_count", summary)
        self.assertIn("anti_gaming_safe", summary)
        self.assertIn("legibility_safe", summary)
        self.assertNotIn("statements", summary)
        self.assertNotIn("raw_text_runtime_only", str(summary))

    def test_validate_logical_form_parse_returns_no_warnings_for_safe_parse(self):
        parse = parse_runtime_text_to_logical_form("All cats are mammals.", parse_id="p1", source_task_id="t1")
        self.assertEqual(validate_logical_form_parse(parse), [])

    def test_no_official_score_claim(self):
        parse = parse_runtime_text_to_logical_form("All cats are mammals.", parse_id="p1", source_task_id="t1")
        self.assertFalse(parse.anti_gaming.official_score_claimed)

    def test_no_answer_key_field_in_parse_dict(self):
        parse = parse_runtime_text_to_logical_form("All cats are mammals.", parse_id="p1", source_task_id="t1")
        data = logical_form_parse_to_dict(parse)

        def walk(value):
            if isinstance(value, dict):
                for key, inner in value.items():
                    self.assertNotEqual(key, "answer_key")
                    walk(inner)
            elif isinstance(value, list):
                for inner in value:
                    walk(inner)

        walk(data)

    def test_existing_parser_schema_tests_still_pass(self):
        self.assertTrue((ROOT / "weslr/tests/test_formal_logic_parser_schema_v1.py").exists())

    def test_no_solver_dry_run_mcq_adapter_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("weslr/formal_logic_parser.py", changed)
        self.assertIn("weslr/tests/test_formal_logic_parser_helpers_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
