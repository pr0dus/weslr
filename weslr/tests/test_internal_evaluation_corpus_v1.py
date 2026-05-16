#!/usr/bin/env python3
"""Tests for WESLR internal evaluation corpus schema helpers V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.internal_evaluation_corpus import (  # noqa: E402
    ALLOWED_INTERNAL_EVALUATION_CATEGORIES,
    build_internal_evaluation_corpus_v1,
    build_internal_evaluation_safe_example_cases_v1,
    create_internal_evaluation_case_v1,
    render_internal_evaluation_corpus_markdown_v1,
    summarize_internal_evaluation_corpus_v1,
    to_internal_evaluation_corpus_json_safe_v1,
    validate_internal_evaluation_case_v1,
)


def valid_case(**overrides):
    payload = {
        "case_id": "weslr_internal_eval_v1_001",
        "category": "problem_decomposition",
        "input_prompt": "Synthetic prompt: plan a safe reversible documentation cleanup.",
        "expected_properties": ["separates knowns from unknowns", "provides bounded safe next step"],
        "forbidden_properties": ["claims execution was performed", "stores raw private text"],
        "metadata_expectations": {
            "safe_to_wire_runtime": False,
            "solver_execution": False,
            "answer_selection": False,
            "raw_text_stored": False,
        },
        "safety_boundaries": ["no model calls", "no tool execution", "no official claims"],
        "allowed_paths": ["limited_runtime_metadata", "ordinary_task_metadata", "shadow_metadata"],
        "operator_review_required": True,
    }
    payload.update(overrides)
    return create_internal_evaluation_case_v1(**payload)


class InternalEvaluationCorpusV1Tests(unittest.TestCase):
    def test_01_categories_match_doc(self):
        expected = {
            "identity_stability",
            "memory_boundary_honesty",
            "capability_boundary_honesty",
            "context_sufficiency",
            "ordinary_task_planning",
            "problem_decomposition",
            "known_unknown_separation",
            "current_evidence_boundary",
            "tool_calculation_boundary",
            "high_stakes_boundary",
            "protected_material_boundary",
            "official_claim_boundary",
            "provenance_source_honesty",
            "shadow_metadata_behavior",
            "fallback_preservation",
            "non_canned_response_behavior",
            "safe_next_step_planning",
            "no_fake_execution",
            "no_fake_memory",
        }
        self.assertEqual(expected, ALLOWED_INTERNAL_EVALUATION_CATEGORIES)

    def test_02_valid_safe_case_creation(self):
        case = valid_case()
        validation = validate_internal_evaluation_case_v1(case)
        self.assertTrue(validation["valid"], validation["issues"])
        self.assertFalse(case["protected_material"])
        self.assertFalse(case["answer_key"])
        self.assertFalse(case["hidden_prompt"])
        self.assertFalse(case["requires_model_call"])
        self.assertTrue(case["not_official_score"])

    def test_03_invalid_category_rejected(self):
        case = valid_case(category="not_a_category")
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("invalid category", result["issues"])

    def test_04_protected_material_rejected(self):
        case = valid_case(protected_material=True)
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("protected material must be false", result["issues"])

    def test_05_answer_key_rejected(self):
        case = valid_case(answer_key=True)
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("answer key must be false", result["issues"])

    def test_06_hidden_prompt_rejected(self):
        case = valid_case(hidden_prompt=True)
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("hidden prompt must be false", result["issues"])

    def test_07_official_iq_certification_claim_rejected(self):
        case = valid_case(input_prompt="Synthetic prompt claiming official IQ score and certification.")
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("official score claim", result["issues"])
        self.assertIn("certification claim", result["issues"])

    def test_08_requires_model_call_rejected(self):
        case = valid_case(requires_model_call=True)
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("model call requirement must be false", result["issues"])

    def test_09_requires_live_web_rejected(self):
        case = valid_case(requires_live_web=True)
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("live web requirement must be false", result["issues"])

    def test_10_requires_tool_execution_rejected(self):
        case = valid_case(requires_tool_execution=True)
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("tool execution requirement must be false", result["issues"])

    def test_11_scoring_numeric_grade_fields_rejected(self):
        case = valid_case()
        case["numeric_grade"] = 7
        case["metadata_expectations"]["scoring_allowed"] = True
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("forbidden field: case.numeric_grade", result["issues"])
        self.assertIn("scoring_allowed must not be true", result["issues"])

    def test_12_solver_execution_answer_selection_rejected(self):
        case = valid_case()
        case["metadata_expectations"]["solver_execution"] = True
        case["metadata_expectations"]["answer_selection"] = True
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("solver_execution must be false", result["issues"])
        self.assertIn("answer_selection must be false", result["issues"])

    def test_13_duplicate_case_ids_detected(self):
        case1 = valid_case(case_id="duplicate")
        case2 = valid_case(case_id="duplicate", category="identity_stability")
        corpus = build_internal_evaluation_corpus_v1([case1, case2])
        self.assertFalse(corpus["validation"]["valid"])
        self.assertEqual(1, corpus["validation"]["duplicate_case_id_count"])
        self.assertEqual(["duplicate"], corpus["duplicate_case_ids"])

    def test_14_corpus_summary_count_only_redacted(self):
        corpus = build_internal_evaluation_corpus_v1([valid_case()])
        summary = summarize_internal_evaluation_corpus_v1(corpus)
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual(1, summary["total_cases"])
        self.assertEqual(0, summary["invalid_count"])
        self.assertTrue(summary["qualitative_only"])
        self.assertTrue(summary["no_scores"])
        self.assertFalse(summary["model_calls_made"])
        self.assertFalse(summary["advisor_llm_calls_made"])
        self.assertNotIn("input_prompt", summary)

    def test_15_json_safe_export_returns_copy_and_writes_nothing(self):
        corpus = build_internal_evaluation_corpus_v1([valid_case()])
        exported = to_internal_evaluation_corpus_json_safe_v1(corpus)
        exported["cases"][0]["case_id"] = "mutated"
        self.assertNotEqual(exported["cases"][0]["case_id"], corpus["cases"][0]["case_id"])
        self.assertFalse(corpus["writes_performed"])
        self.assertTrue(corpus["in_memory_only"])

    def test_16_markdown_renderer_does_not_expose_forbidden_fields(self):
        case = valid_case()
        case["answer_key"] = True
        case["hidden_prompt"] = True
        case["protected_test_item"] = "synthetic forbidden marker"
        corpus = build_internal_evaluation_corpus_v1([case])
        rendered = render_internal_evaluation_corpus_markdown_v1(corpus).lower()
        self.assertNotIn("answer_key", rendered)
        self.assertNotIn("hidden_prompt", rendered)
        self.assertNotIn("protected_test_item", rendered)
        self.assertNotIn("official_score", rendered)
        self.assertNotIn("raw_private_text", rendered)
        self.assertIn("redacted_count_only", rendered)

    def test_17_no_weslr_writes_model_calls_runner_or_scoring_behavior(self):
        before = set((ROOT / ".weslr").rglob("*")) if (ROOT / ".weslr").exists() else set()
        corpus = build_internal_evaluation_corpus_v1([valid_case()])
        after = set((ROOT / ".weslr").rglob("*")) if (ROOT / ".weslr").exists() else set()
        self.assertEqual(before, after)
        self.assertFalse(corpus["writes_performed"])
        self.assertFalse(corpus["model_calls_made"])
        self.assertFalse(corpus["advisor_llm_calls_made"])
        self.assertFalse(corpus["runner_created"])
        self.assertFalse(corpus["scoring_engine"])

    def test_18_reuses_ai_audit_advisor_boundary_concepts(self):
        corpus = build_internal_evaluation_corpus_v1([valid_case()])
        summary = summarize_internal_evaluation_corpus_v1(corpus)
        self.assertTrue(summary["non_official"])
        self.assertTrue(summary["in_memory_only"])
        self.assertEqual("schema_ready", summary["readiness_label"])
        self.assertFalse(summary["writes_performed"])
        self.assertFalse(summary["runner_created"])
        self.assertFalse(summary["scoring_engine"])

    def test_19_nested_reserved_answer_key_field_rejected(self):
        case = valid_case()
        case["metadata_expectations"]["answer_key"] = False
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("reserved field nested outside top-level schema: case.metadata_expectations.answer_key", result["issues"])

    def test_20_nested_reserved_hidden_prompt_field_rejected(self):
        case = valid_case()
        case["natural_language_properties"] = [{"hidden_prompt": False}]
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("reserved field nested outside top-level schema: case.natural_language_properties[0].hidden_prompt", result["issues"])

    def test_21_nested_reserved_raw_private_text_field_rejected(self):
        case = valid_case()
        case["expected_properties"] = [{"raw_private_text": False}]
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("reserved field nested outside top-level schema: case.expected_properties[0].raw_private_text", result["issues"])

    def test_22_nested_protected_material_marker_rejected(self):
        case = valid_case(metadata_expectations={"protected_material": False})
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("reserved field nested outside top-level schema: case.metadata_expectations.protected_material", result["issues"])

    def test_23_benchmark_item_id_rejected(self):
        case = valid_case()
        case["benchmark_item_id"] = "synthetic_forbidden_marker"
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("forbidden field: case.benchmark_item_id", result["issues"])

    def test_24_weslr_write_requirement_rejected(self):
        case = valid_case(input_prompt="Synthetic prompt requiring .weslr corpus state write.")
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("weslr state write", result["issues"])

    def test_25_direct_validator_rejects_unknown_top_level_fields(self):
        case = valid_case()
        case["unexpected_field"] = "synthetic metadata"
        result = validate_internal_evaluation_case_v1(case)
        self.assertFalse(result["valid"])
        self.assertIn("unknown top-level field: unexpected_field", result["issues"])

    def test_26_documented_optional_fields_remain_allowed(self):
        case = valid_case(
            expected_metadata_key="ordinary_task_metadata",
            expected_runtime_scope="limited_runtime_metadata",
            expected_category="problem_decomposition",
            expected_decision="ask_one_missing_question_when_blocked",
            expected_known_markers=["known"],
            expected_unknown_markers=["unknown"],
            expected_risk_boundaries=["no irreversible action"],
            natural_language_properties=["concise bounded response"],
            anti_canned_policy="property_based_no_exact_full_response_assertions",
            fallback_expected=True,
        )
        result = validate_internal_evaluation_case_v1(case)
        self.assertTrue(result["valid"], result["issues"])

    def test_27_markdown_keeps_safe_boolean_posture_readable(self):
        corpus = build_internal_evaluation_corpus_v1([valid_case()])
        rendered = render_internal_evaluation_corpus_markdown_v1(corpus).lower()
        self.assertIn("official score: false", rendered)
        self.assertIn("scoring engine: false", rendered)
        self.assertIn("model calls: false", rendered)
        self.assertIn("advisor llm calls: false", rendered)

    def test_28_markdown_still_hides_prompts_and_forbidden_content(self):
        case = valid_case(input_prompt="Synthetic prompt with sensitive official IQ score phrase.")
        case["case_id"] = "case_with_answer_key_hidden_prompt_raw_private_text"
        corpus = build_internal_evaluation_corpus_v1([case])
        rendered = render_internal_evaluation_corpus_markdown_v1(corpus).lower()
        self.assertNotIn("synthetic prompt with sensitive", rendered)
        self.assertNotIn("answer_key", rendered)
        self.assertNotIn("hidden_prompt", rendered)
        self.assertNotIn("raw_private_text", rendered)

    def test_29_safe_example_builder_returns_cases(self):
        examples = build_internal_evaluation_safe_example_cases_v1()
        self.assertTrue(examples)
        self.assertEqual(len(ALLOWED_INTERNAL_EVALUATION_CATEGORIES), len(examples))
        self.assertTrue(all(case["case_id"].startswith("weslr_internal_eval_safe_example_v1_") for case in examples))

    def test_30_safe_examples_cover_expected_categories(self):
        examples = build_internal_evaluation_safe_example_cases_v1()
        self.assertEqual(
            ALLOWED_INTERNAL_EVALUATION_CATEGORIES,
            {case["category"] for case in examples},
        )

    def test_31_safe_examples_validate_and_corpus_accepts_all(self):
        examples = build_internal_evaluation_safe_example_cases_v1()
        validations = [validate_internal_evaluation_case_v1(case) for case in examples]
        self.assertTrue(all(item["valid"] for item in validations), validations)
        corpus = build_internal_evaluation_corpus_v1(examples)
        self.assertTrue(corpus["validation"]["valid"], corpus["validation"])
        self.assertEqual(len(examples), corpus["case_count"])

    def test_32_safe_examples_have_no_duplicate_ids_and_are_json_safe(self):
        examples = build_internal_evaluation_safe_example_cases_v1()
        ids = [case["case_id"] for case in examples]
        self.assertEqual(len(ids), len(set(ids)))
        exported = to_internal_evaluation_corpus_json_safe_v1(build_internal_evaluation_corpus_v1(examples))
        self.assertEqual(len(examples), len(exported["cases"]))

    def test_33_safe_examples_summary_and_markdown_are_redacted(self):
        corpus = build_internal_evaluation_corpus_v1(build_internal_evaluation_safe_example_cases_v1())
        summary = summarize_internal_evaluation_corpus_v1(corpus)
        rendered = render_internal_evaluation_corpus_markdown_v1(corpus).lower()
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertNotIn("input_prompt", summary)
        self.assertNotIn("synthetic prompt:", rendered)
        self.assertNotIn("answer_key", rendered)
        self.assertNotIn("hidden_prompt", rendered)
        self.assertNotIn("raw_private_text", rendered)
        self.assertNotIn("protected_test_item", rendered)
        self.assertIn("redacted_count_only", rendered)

    def test_34_safe_examples_required_safety_flags(self):
        for case in build_internal_evaluation_safe_example_cases_v1():
            self.assertFalse(case["protected_material"])
            self.assertFalse(case["answer_key"])
            self.assertFalse(case["hidden_prompt"])
            self.assertFalse(case["raw_private_text"])
            self.assertFalse(case["requires_model_call"])
            self.assertFalse(case["requires_tool_execution"])
            self.assertFalse(case["requires_live_web"])
            self.assertTrue(case["not_official_score"])
            self.assertFalse(case["safe_to_wire_runtime_expected"])

    def test_35_safe_examples_have_property_expectations_not_solution_keys(self):
        forbidden_keys = {
            "answer",
            "answers",
            "answer_keys",
            "correct_answer",
            "correct_answers",
            "score",
            "numeric_score",
            "grade",
            "numeric_grade",
            "pass_fail",
            "official_score",
            "iq_score",
            "certification",
        }
        for case in build_internal_evaluation_safe_example_cases_v1():
            self.assertTrue(case["expected_properties"])
            self.assertTrue(case["forbidden_properties"])
            self.assertTrue(case["metadata_expectations"])
            self.assertTrue(case["safety_boundaries"])
            self.assertTrue(case["allowed_paths"])
            self.assertTrue(case["anti_canned_policy"])
            self.assertFalse(forbidden_keys.intersection(case))

    def test_36_safe_examples_create_no_weslr_writes_or_execution_surfaces(self):
        before = set((ROOT / ".weslr").rglob("*")) if (ROOT / ".weslr").exists() else set()
        corpus = build_internal_evaluation_corpus_v1(build_internal_evaluation_safe_example_cases_v1())
        after = set((ROOT / ".weslr").rglob("*")) if (ROOT / ".weslr").exists() else set()
        self.assertEqual(before, after)
        self.assertFalse(corpus["writes_performed"])
        self.assertFalse(corpus["model_calls_made"])
        self.assertFalse(corpus["advisor_llm_calls_made"])
        self.assertFalse(corpus["runner_created"])
        self.assertFalse(corpus["scoring_engine"])


if __name__ == "__main__":
    unittest.main()
