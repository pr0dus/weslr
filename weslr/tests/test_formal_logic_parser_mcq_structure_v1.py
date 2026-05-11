from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.formal_logic_parser import (  # noqa: E402
    classify_question_fragment,
    logical_form_parse_to_dict,
    parse_mcq_runtime_text_to_logical_form,
    safe_choice_identifier,
    summarize_logical_form_parse,
)


class FormalLogicParserMcqStructureV1Tests(unittest.TestCase):
    def test_parse_mcq_runtime_text_to_logical_form_exists(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Which of the following must be true?",
            [{"label": "A", "text": "All cats are mammals"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertEqual(parse.parse_id, "p1")

    def test_does_not_store_raw_question_or_choice_text_by_default(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Which of the following must be true?",
            [{"label": "A", "text": "All cats are mammals"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertTrue(all(statement.raw_text_runtime_only == "" for statement in parse.statements))

    def test_store_raw_text_true_stores_raw_text_explicitly(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Which of the following must be true?",
            [{"label": "A", "text": "All cats are mammals"}],
            parse_id="p1",
            source_task_id="t1",
            store_raw_text=True,
        )
        self.assertEqual(parse.statements[0].raw_text_runtime_only, "Which of the following must be true?")
        self.assertEqual(parse.statements[1].raw_text_runtime_only, "All cats are mammals")

    def test_question_instruction_detected(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Which of the following must be true?",
            [{"label": "A", "text": "All cats are mammals"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertEqual(parse.statements[0].role, "question_instruction")

    def test_classify_question_fragment_marks_based_on_statements_as_instruction(self):
        self.assertEqual(classify_question_fragment("Based on the statements above", position=2, total=2), "question_instruction")

    def test_parse_adds_question_body_premises(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Felix is a cat. All cats are mammals. Which of the following must be true?",
            [{"label": "A", "text": "Felix is a mammal"}, {"label": "B", "text": "Felix is a reptile"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertEqual(parse.premises, ["stmt_q1", "stmt_q2"])
        self.assertEqual(parse.statements[0].role, "premise")
        self.assertEqual(parse.statements[1].role, "premise")
        self.assertEqual(parse.statements[2].role, "question_instruction")

    def test_relation_sentence_without_explicit_logic_operator_becomes_premise(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Alpha supports Beta. Which statement follows?",
            [{"label": "A", "text": "Alpha supports Beta"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertEqual(parse.statements[0].role, "premise")
        self.assertEqual(parse.premises, ["stmt_q1"])

    def test_choice_texts_become_choice_claim(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Question?",
            [{"label": "A", "text": "All cats are mammals"}, {"label": "B", "text": "No cats are reptiles"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertEqual(parse.statements[1].role, "choice_claim")
        self.assertEqual(parse.statements[2].role, "choice_claim")
        self.assertNotIn(parse.statements[1].statement_id, parse.premises)
        self.assertNotIn(parse.statements[2].statement_id, parse.premises)

    def test_choice_claims_added_to_candidate_conclusions(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Question?",
            [{"label": "A", "text": "All cats are mammals"}, {"label": "B", "text": "No cats are reptiles"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertEqual(len(parse.candidate_conclusions), 2)

    def test_visible_choice_label_becomes_safe_candidate_statement_id(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Question?",
            [{"label": "A", "text": "All cats are mammals"}, {"label": "B", "text": "No cats are reptiles"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertEqual(parse.statements[1].statement_id, "choice_A")
        self.assertEqual(parse.statements[2].statement_id, "choice_B")

    def test_safe_choice_identifier_ignores_answer_label_correct_answer_and_answer_key(self):
        choice = {"label": "A", "answer_label": "Z", "correct_answer": "B", "answer_key": "C", "text": "Claim"}
        self.assertEqual(safe_choice_identifier(choice, 1), "choice_A")

    def test_unsafe_or_missing_choice_label_falls_back_to_index(self):
        self.assertEqual(safe_choice_identifier({"label": "A/B", "text": "Claim"}, 2), "choice_2")
        self.assertEqual(safe_choice_identifier({"text": "Claim"}, 3), "choice_3")

    def test_candidate_conclusions_use_safe_candidate_ids(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Question?",
            [{"label": "A", "text": "All cats are mammals"}, {"label": "@bad", "text": "No cats are reptiles"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertEqual(parse.candidate_conclusions, ["choice_A", "choice_2"])

    def test_summary_includes_choice_claim_count(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Question?",
            [{"label": "A", "text": "All cats are mammals"}],
            parse_id="p1",
            source_task_id="t1",
        )
        summary = summarize_logical_form_parse(parse)
        self.assertEqual(summary["choice_claim_count"], 1)

    def test_summary_includes_question_instruction_count(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Which of the following must be true?",
            [{"label": "A", "text": "All cats are mammals"}],
            parse_id="p1",
            source_task_id="t1",
        )
        summary = summarize_logical_form_parse(parse)
        self.assertEqual(summary["question_instruction_count"], 1)

    def test_summary_premise_count_increases_on_synthetic_mcq(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Felix is a cat. All cats are mammals. Which of the following must be true?",
            [{"label": "A", "text": "Felix is a mammal"}],
            parse_id="p1",
            source_task_id="t1",
        )
        summary = summarize_logical_form_parse(parse)
        self.assertGreaterEqual(summary["premise_count"], 2)

    def test_question_instruction_not_counted_as_unsupported_just_because_no_operator(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Which one is best supported?",
            [{"label": "A", "text": "All cats are mammals"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertEqual(len([u for u in parse.unsupported_fragments if "stmt_q1" in u.source_statement_ids]), 0)

    def test_premise_not_counted_as_unsupported_just_because_it_lacks_if_then(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Felix is furry. Which of the following must be true?",
            [{"label": "A", "text": "Felix is furry"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertEqual(parse.premises, ["stmt_q1"])
        self.assertEqual(len([u for u in parse.unsupported_fragments if "stmt_q1" in u.source_statement_ids]), 0)

    def test_choice_claim_not_counted_as_unsupported_just_because_no_operator(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Question?",
            [{"label": "A", "text": "Felix is furry"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertEqual(len([u for u in parse.unsupported_fragments if "choice_A" in u.source_statement_ids]), 0)

    def test_quantifier_negation_disjunction_detection_still_works_inside_choices(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Question?",
            [
                {"label": "A", "text": "All cats are mammals"},
                {"label": "B", "text": "No cats are reptiles"},
                {"label": "C", "text": "Either p or q"},
            ],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertGreaterEqual(len(parse.quantifiers), 2)
        self.assertGreaterEqual(len(parse.negations), 1)
        self.assertGreaterEqual(len(parse.disjunctions), 1)

    def test_no_answer_label_copied_if_present_in_input(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Question?",
            [{"label": "A", "text": "All cats are mammals", "answer_label": "Z"}],
            parse_id="p1",
            source_task_id="t1",
        )
        data = logical_form_parse_to_dict(parse)
        self.assertNotIn("answer_label", str(data))

    def test_no_answer_key_field_exists_in_parse_dict(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Question?",
            [{"label": "A", "text": "All cats are mammals", "answer_key": "B"}],
            parse_id="p1",
            source_task_id="t1",
        )
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

    def test_official_score_claimed_remains_false(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Question?",
            [{"label": "A", "text": "All cats are mammals"}],
            parse_id="p1",
            source_task_id="t1",
        )
        self.assertFalse(parse.anti_gaming.official_score_claimed)

    def test_existing_parser_tests_still_pass(self):
        self.assertTrue((ROOT / "weslr/tests/test_formal_logic_parser_schema_v1.py").exists())
        self.assertTrue((ROOT / "weslr/tests/test_formal_logic_parser_helpers_v1.py").exists())
        self.assertTrue((ROOT / "weslr/tests/test_formal_logic_parser_design_v1.py").exists())

    def test_no_solver_dry_run_mcq_adapter_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("weslr/formal_logic_parser.py", changed)
        self.assertIn("weslr/tests/test_formal_logic_parser_mcq_structure_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
