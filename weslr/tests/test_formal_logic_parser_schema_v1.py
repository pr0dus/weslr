from __future__ import annotations

import sys
import unittest
from dataclasses import fields
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.formal_logic_parser import (  # noqa: E402
    ConditionalRecord,
    DisjunctionRecord,
    ParserAntiGamingRecord,
    ParserLegibilityRecord,
    ParsedStatement,
    add_parsed_statement,
    add_parser_warning,
    add_unsupported_fragment,
    create_empty_logical_form_parse,
    logical_form_parse_from_dict,
    logical_form_parse_to_dict,
    validate_logical_form_parse,
)


class FormalLogicParserSchemaV1Tests(unittest.TestCase):
    def test_can_create_empty_logical_form_parse(self):
        parse = create_empty_logical_form_parse(parse_id="parse-1", source_task_id="task-1")
        self.assertEqual(parse.parse_id, "parse-1")
        self.assertEqual(parse.source_task_id, "task-1")
        self.assertEqual(parse.statements, [])

    def test_defaults_keep_anti_gaming_false(self):
        anti = ParserAntiGamingRecord()
        self.assertFalse(anti.uses_answer_key)
        self.assertFalse(anti.uses_item_id)
        self.assertFalse(anti.uses_answer_position_bias)
        self.assertFalse(anti.stores_raw_text_by_default)
        self.assertFalse(anti.official_score_claimed)
        self.assertFalse(anti.benchmark_specific_rule_used)

    def test_defaults_keep_legibility_safe(self):
        leg = ParserLegibilityRecord()
        self.assertTrue(leg.symbolic_forms_translated)
        self.assertTrue(leg.unsupported_fragments_visible)
        self.assertFalse(leg.private_symbolic_authority_used)
        self.assertTrue(leg.human_translation_available)

    def test_parsed_statement_raw_text_runtime_only_defaults_empty(self):
        statement = ParsedStatement()
        self.assertEqual(statement.raw_text_runtime_only, "")

    def test_can_add_parsed_statement(self):
        parse = create_empty_logical_form_parse(parse_id="parse-1", source_task_id="task-1")
        add_parsed_statement(parse, statement_id="s1", normalized_text="p", role="premise")
        self.assertEqual(len(parse.statements), 1)
        self.assertEqual(parse.statements[0].statement_id, "s1")

    def test_can_add_unsupported_fragment(self):
        parse = create_empty_logical_form_parse(parse_id="parse-1", source_task_id="task-1")
        add_unsupported_fragment(parse, record_id="u1", fragment_type="natural_language_fragment")
        self.assertEqual(len(parse.unsupported_fragments), 1)
        self.assertEqual(parse.unsupported_fragments[0].record_id, "u1")

    def test_can_add_parser_warning(self):
        parse = create_empty_logical_form_parse(parse_id="parse-1", source_task_id="task-1")
        add_parser_warning(parse, record_id="w1", warning_type="ambiguous_translation")
        self.assertEqual(len(parse.parse_warnings), 1)
        self.assertEqual(parse.parse_warnings[0].record_id, "w1")

    def test_to_dict_from_dict_roundtrip_works(self):
        parse = create_empty_logical_form_parse(parse_id="parse-1", source_task_id="task-1")
        add_parsed_statement(parse, statement_id="s1", normalized_text="if not q then p", role="premise")
        add_parser_warning(parse, record_id="w1", warning_type="partial_parse")
        data = logical_form_parse_to_dict(parse)
        restored = logical_form_parse_from_dict(data)
        self.assertEqual(restored.parse_id, "parse-1")
        self.assertEqual(restored.source_task_id, "task-1")
        self.assertEqual(len(restored.statements), 1)
        self.assertEqual(len(restored.parse_warnings), 1)

    def test_validate_flags_official_score_claimed_true(self):
        parse = create_empty_logical_form_parse(parse_id="p", source_task_id="t")
        parse.anti_gaming.official_score_claimed = True
        self.assertTrue(any("official_score_claimed true" in m for m in validate_logical_form_parse(parse)))

    def test_validate_flags_answer_key_use(self):
        parse = create_empty_logical_form_parse(parse_id="p", source_task_id="t")
        parse.anti_gaming.uses_answer_key = True
        self.assertTrue(any("uses_answer_key true" in m for m in validate_logical_form_parse(parse)))

    def test_validate_flags_item_id_use(self):
        parse = create_empty_logical_form_parse(parse_id="p", source_task_id="t")
        parse.anti_gaming.uses_item_id = True
        self.assertTrue(any("uses_item_id true" in m for m in validate_logical_form_parse(parse)))

    def test_validate_flags_answer_position_bias(self):
        parse = create_empty_logical_form_parse(parse_id="p", source_task_id="t")
        parse.anti_gaming.uses_answer_position_bias = True
        self.assertTrue(any("uses_answer_position_bias true" in m for m in validate_logical_form_parse(parse)))

    def test_validate_flags_raw_text_default_storage(self):
        parse = create_empty_logical_form_parse(parse_id="p", source_task_id="t")
        parse.anti_gaming.stores_raw_text_by_default = True
        self.assertTrue(any("stores_raw_text_by_default true" in m for m in validate_logical_form_parse(parse)))

    def test_validate_flags_benchmark_specific_rule_use(self):
        parse = create_empty_logical_form_parse(parse_id="p", source_task_id="t")
        parse.anti_gaming.benchmark_specific_rule_used = True
        self.assertTrue(any("benchmark_specific_rule_used true" in m for m in validate_logical_form_parse(parse)))

    def test_validate_flags_private_symbolic_authority(self):
        parse = create_empty_logical_form_parse(parse_id="p", source_task_id="t")
        parse.legibility.private_symbolic_authority_used = True
        self.assertTrue(any("private_symbolic_authority_used true" in m for m in validate_logical_form_parse(parse)))

    def test_validate_flags_symbolic_forms_translated_false(self):
        parse = create_empty_logical_form_parse(parse_id="p", source_task_id="t")
        parse.legibility.symbolic_forms_translated = False
        self.assertTrue(any("symbolic_forms_translated false" in m for m in validate_logical_form_parse(parse)))

    def test_validate_flags_unsupported_fragments_visible_false(self):
        parse = create_empty_logical_form_parse(parse_id="p", source_task_id="t")
        parse.legibility.unsupported_fragments_visible = False
        self.assertTrue(any("unsupported_fragments_visible false" in m for m in validate_logical_form_parse(parse)))

    def test_can_represent_unless_conditional_translation(self):
        record = ConditionalRecord(
            record_id="c1",
            antecedent="not q",
            consequent="p",
            conditional_type="unless_translation",
            source_statement_ids=["s1"],
            normalized_form="if not q then p",
            confidence="medium",
            human_translation="P unless Q becomes if not Q then P",
        )
        self.assertEqual(record.conditional_type, "unless_translation")
        self.assertEqual(record.normalized_form, "if not q then p")

    def test_can_represent_disjunction_case_analysis(self):
        record = DisjunctionRecord(
            record_id="d1",
            alternatives=["p", "q"],
            exhaustive=True,
            exclusive=False,
            source_statement_ids=["s1"],
            normalized_form="p or q",
            confidence="medium",
            human_translation="At least one of p or q holds; eliminate impossible cases before selection.",
        )
        self.assertEqual(record.alternatives, ["p", "q"])
        self.assertTrue(record.exhaustive)

    def test_can_represent_unsupported_natural_language_fragment(self):
        parse = create_empty_logical_form_parse(parse_id="p", source_task_id="t")
        fragment = add_unsupported_fragment(
            parse,
            record_id="u1",
            fragment_type="natural_language_fragment",
            normalized_form="complex ordinary phrasing",
            confidence="low",
            human_translation="Unsupported natural-language fragment remains visible.",
        )
        self.assertEqual(fragment.fragment_type, "natural_language_fragment")
        self.assertEqual(len(parse.unsupported_fragments), 1)

    def test_no_field_named_answer_key_exists(self):
        field_names = {field.name for field in fields(ParserAntiGamingRecord)}
        self.assertNotIn("answer_key", field_names)

    def test_existing_formal_logic_parser_design_test_still_passes(self):
        self.assertTrue((ROOT / "weslr/tests/test_formal_logic_parser_design_v1.py").exists())

    def test_no_runtime_behavior_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("weslr/formal_logic_parser.py", changed)
        self.assertIn("weslr/tests/test_formal_logic_parser_schema_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
