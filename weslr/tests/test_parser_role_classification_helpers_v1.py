#!/usr/bin/env python3
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
)


class ParserRoleClassificationHelpersV1Tests(unittest.TestCase):
    def test_quantified_placeholder_claims_are_premises(self):
        self.assertEqual(classify_question_fragment("All A are B.", position=1, total=2), "premise")
        self.assertEqual(classify_question_fragment("No A are B.", position=1, total=2), "premise")
        self.assertEqual(classify_question_fragment("Some A are B.", position=1, total=2), "premise")

    def test_conditional_and_conjunctive_placeholder_claims_are_premises(self):
        self.assertEqual(classify_question_fragment("If A then B.", position=1, total=2), "premise")
        self.assertEqual(classify_question_fragment("A is B and C is D.", position=1, total=2), "premise")

    def test_instruction_placeholders_are_question_instructions(self):
        self.assertEqual(
            classify_question_fragment("Which of the following must be true?", position=2, total=2),
            "question_instruction",
        )
        self.assertEqual(
            classify_question_fragment("What follows from the statements above?", position=2, total=2),
            "question_instruction",
        )

    def test_based_on_statement_is_not_premise(self):
        self.assertIn(
            classify_question_fragment("Based on the statements above.", position=2, total=2),
            {"question_instruction", "background"},
        )
        self.assertNotEqual(
            classify_question_fragment("Based on the statements above.", position=2, total=2),
            "premise",
        )

    def test_context_shells_are_background(self):
        self.assertEqual(classify_question_fragment("Consider the following statements.", position=1, total=2), "background")
        self.assertEqual(classify_question_fragment("Given the following scenario.", position=1, total=2), "background")

    def test_ambiguous_short_fragment_is_not_premise(self):
        self.assertNotEqual(classify_question_fragment("A.", position=1, total=1), "premise")
        self.assertIn(classify_question_fragment("A.", position=1, total=1), {"background", "unsupported_fragment"})

    def test_choice_claims_stay_candidate_side_in_mcq_structure(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "All A are B. Which of the following must be true?",
            [{"label": "A", "text": "A is B."}],
            parse_id="p1",
            source_task_id="t1",
        )
        choice_statements = [statement for statement in parse.statements if statement.statement_id.startswith("choice_")]
        self.assertEqual([statement.role for statement in choice_statements], ["choice_claim"])
        self.assertFalse(any(statement.statement_id in parse.premises for statement in choice_statements))

    def test_no_answer_key_or_item_id_authority_or_benchmark_tuning(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "All A are B. Which of the following must be true?",
            [{"label": "A", "text": "A is B.", "answer_key": "A", "answer_label": "A", "item_id": "secret"}],
            parse_id="p1",
            source_task_id="t1",
        )
        data = logical_form_parse_to_dict(parse)
        serialized = str(data).lower()
        self.assertNotIn("answer_label", serialized)
        self.assertNotIn("secret", serialized)
        self.assertFalse(parse.anti_gaming.uses_answer_key)
        self.assertFalse(parse.anti_gaming.uses_item_id)
        self.assertFalse(parse.anti_gaming.benchmark_specific_rule_used)
        self.assertFalse(parse.anti_gaming.official_score_claimed)

    def test_existing_parser_schema_and_helper_tests_exist(self):
        self.assertTrue((ROOT / "weslr/tests/test_formal_logic_parser_helpers_v1.py").exists())
        self.assertTrue((ROOT / "weslr/tests/test_formal_logic_parser_mcq_structure_v1.py").exists())
        self.assertTrue((ROOT / "weslr/tests/test_formal_logic_parser_schema_v1.py").exists())


if __name__ == "__main__":
    unittest.main()
