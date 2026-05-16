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
    build_internal_evaluation_case_review_card_v1,
    build_internal_evaluation_corpus_review_cards_v1,
    build_internal_evaluation_corpus_status_bundle_v1,
    build_internal_evaluation_corpus_v1,
    build_internal_evaluation_safe_example_cases_v1,
    create_internal_evaluation_case_v1,
    render_internal_evaluation_corpus_markdown_v1,
    render_internal_evaluation_corpus_review_cards_markdown_v1,
    render_internal_evaluation_corpus_status_bundle_markdown_v1,
    summarize_internal_evaluation_corpus_review_cards_v1,
    summarize_internal_evaluation_corpus_status_bundle_v1,
    summarize_internal_evaluation_corpus_v1,
    to_internal_evaluation_corpus_json_safe_v1,
    to_internal_evaluation_corpus_review_cards_json_safe_v1,
    to_internal_evaluation_corpus_status_bundle_json_safe_v1,
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

    def test_37_review_card_builds_for_one_valid_case(self):
        card = build_internal_evaluation_case_review_card_v1(valid_case())
        self.assertEqual("internal_evaluation_case_review_card_v1", card["card_type"])
        self.assertEqual("problem_decomposition", card["category"])
        self.assertEqual("weslr_internal_evaluation_case_v1", card["schema_version"])
        self.assertTrue(card["validation_status"]["valid"])
        self.assertEqual("dry_review_ready", card["readiness_label"])
        self.assertFalse(card["runner_created"])
        self.assertFalse(card["scoring_created"])
        self.assertFalse(card["model_calls"])
        self.assertFalse(card["advisor_calls"])
        self.assertFalse(card["safe_to_execute"])

    def test_38_review_card_redacts_raw_prompt_and_includes_counts(self):
        case = valid_case(input_prompt="Synthetic prompt: unique raw prompt text for card redaction.")
        card = build_internal_evaluation_case_review_card_v1(case)
        rendered = str(card).lower()
        self.assertNotIn("unique raw prompt text", rendered)
        self.assertNotIn("input_prompt", card)
        self.assertEqual(2, card["expected_property_count"])
        self.assertEqual(2, card["forbidden_property_count"])
        self.assertEqual(3, card["safety_boundary_count"])
        self.assertIn("raw_text_stored", card["metadata_expectation_keys"])
        joined_notes = " ".join(card["review_notes"]).lower()
        self.assertIn("property expectations", joined_notes)
        self.assertIn("without execution", joined_notes)
        self.assertNotIn("unique raw prompt text", joined_notes)

    def test_39_review_card_includes_safe_flags(self):
        card = build_internal_evaluation_case_review_card_v1(valid_case())
        flags = card["safe_flags"]
        self.assertTrue(flags["restricted_content_free"])
        self.assertTrue(flags["keyed_solution_free"])
        self.assertTrue(flags["concealed_instruction_free"])
        self.assertTrue(flags["raw_private_text_free"])
        self.assertFalse(flags["model_call_required"])
        self.assertFalse(flags["tool_execution_required"])
        self.assertFalse(flags["live_web_required"])
        self.assertTrue(flags["not_official_score"])
        self.assertTrue(flags["no_public_authority_claim"])
        self.assertTrue(flags["non_certifying"])
        self.assertNotIn("non_public_authority_claim", flags)
        self.assertFalse(flags["runtime_wiring_expected"])

    def test_40_review_card_marks_invalid_case_review_only(self):
        case = valid_case(answer_key=True, requires_model_call=True)
        card = build_internal_evaluation_case_review_card_v1(case)
        self.assertFalse(card["validation_status"]["valid"])
        self.assertEqual("needs_operator_review", card["readiness_label"])
        self.assertFalse(card["safe_to_execute"])
        self.assertFalse(card["runner_created"])
        self.assertFalse(card["scoring_created"])
        self.assertFalse(card["model_calls"])
        self.assertFalse(card["advisor_calls"])
        self.assertFalse(card["safe_flags"]["keyed_solution_free"])
        self.assertTrue(card["safe_flags"]["model_call_required"])
        self.assertIn("requires review", " ".join(card["review_notes"]).lower())

    def test_41_review_overview_builds_for_all_safe_examples(self):
        review = build_internal_evaluation_corpus_review_cards_v1(build_internal_evaluation_safe_example_cases_v1())
        self.assertEqual("internal_evaluation_corpus_review_cards_v1", review["schema_version"])
        self.assertEqual(len(ALLOWED_INTERNAL_EVALUATION_CATEGORIES), review["card_count"])
        self.assertEqual(0, review["invalid_card_count"])
        self.assertEqual("dry_review_ready", review["readiness_label"])
        self.assertFalse(review["writes_performed"])
        self.assertFalse(review["runner_created"])
        self.assertFalse(review["scoring_created"])

    def test_42_review_overview_covers_all_categories(self):
        review = build_internal_evaluation_corpus_review_cards_v1(build_internal_evaluation_safe_example_cases_v1())
        self.assertEqual(ALLOWED_INTERNAL_EVALUATION_CATEGORIES, set(review["categories_covered"]))

    def test_43_review_summary_is_count_only_redacted(self):
        review = build_internal_evaluation_corpus_review_cards_v1(build_internal_evaluation_safe_example_cases_v1())
        summary = summarize_internal_evaluation_corpus_review_cards_v1(review)
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual(len(ALLOWED_INTERNAL_EVALUATION_CATEGORIES), summary["total_cards"])
        self.assertEqual(0, summary["invalid_cards"])
        self.assertEqual({"dry_review_ready": len(ALLOWED_INTERNAL_EVALUATION_CATEGORIES)}, summary["readiness_labels"])
        self.assertNotIn("input_prompt", summary)
        self.assertFalse(summary["writes_performed"])
        self.assertFalse(summary["runner_created"])
        self.assertFalse(summary["scoring_created"])

    def test_44_review_markdown_hides_raw_prompt_and_forbidden_terms(self):
        case = valid_case(input_prompt="Synthetic prompt: markdown-only raw prompt should not appear.")
        case["case_id"] = "case_with_answer_key_hidden_prompt_raw_private_text"
        review = build_internal_evaluation_corpus_review_cards_v1([case])
        rendered = render_internal_evaluation_corpus_review_cards_markdown_v1(review).lower()
        self.assertIn("dry review only: true", rendered)
        self.assertIn("readiness label:", rendered)
        self.assertIn("safe flags:", rendered)
        self.assertIn("no_public_authority_claim=true", rendered)
        self.assertIn("non_certifying=true", rendered)
        self.assertIn("model calls: false", rendered)
        self.assertIn("advisor calls: false", rendered)
        self.assertNotIn("non_public_authority_claim", str(review["cards"][0]["safe_flags"]))
        self.assertNotIn("markdown-only raw prompt", rendered)
        self.assertNotIn("input_prompt", rendered)
        self.assertNotIn("answer_key", rendered)
        self.assertNotIn("answer key", rendered)
        self.assertNotIn("hidden_prompt", rendered)
        self.assertNotIn("hidden prompt", rendered)
        self.assertNotIn("protected_test_item", rendered)
        self.assertNotIn("protected material", rendered)
        self.assertNotIn("raw_private_text", rendered)
        self.assertNotIn("official score", rendered)
        self.assertNotIn("certification", rendered)

    def test_45_review_json_safe_copy_is_deep_copy(self):
        review = build_internal_evaluation_corpus_review_cards_v1([valid_case()])
        exported = to_internal_evaluation_corpus_review_cards_json_safe_v1(review)
        exported["cards"][0]["case_id"] = "mutated"
        self.assertNotEqual(exported["cards"][0]["case_id"], review["cards"][0]["case_id"])

    def test_46_review_cards_create_no_weslr_writes_or_execution_surfaces(self):
        before = set((ROOT / ".weslr").rglob("*")) if (ROOT / ".weslr").exists() else set()
        review = build_internal_evaluation_corpus_review_cards_v1(build_internal_evaluation_safe_example_cases_v1())
        after = set((ROOT / ".weslr").rglob("*")) if (ROOT / ".weslr").exists() else set()
        self.assertEqual(before, after)
        self.assertFalse(review["writes_performed"])
        self.assertFalse(review["runner_created"])
        self.assertFalse(review["scoring_created"])
        self.assertFalse(review["model_calls"])
        self.assertFalse(review["advisor_calls"])
        self.assertFalse(review["safe_to_execute"])

    def test_47_invalid_review_stays_non_executable_and_non_authoritative(self):
        case = valid_case(requires_tool_execution=True)
        review = build_internal_evaluation_corpus_review_cards_v1([case])
        summary = summarize_internal_evaluation_corpus_review_cards_v1(review)
        card = review["cards"][0]
        self.assertEqual(1, review["invalid_card_count"])
        self.assertEqual(1, summary["invalid_cards"])
        self.assertEqual(1, summary["safety_flag_summary"]["tool_execution_required_cases"])
        self.assertFalse(card["safe_to_execute"])
        self.assertFalse(card["runner_created"])
        self.assertFalse(card["scoring_created"])

    def test_48_safe_examples_remain_valid_after_card_generation(self):
        examples = build_internal_evaluation_safe_example_cases_v1()
        build_internal_evaluation_corpus_review_cards_v1(examples)
        validations = [validate_internal_evaluation_case_v1(case) for case in examples]
        self.assertTrue(all(item["valid"] for item in validations), validations)


    def test_49_status_bundle_default_builds_safe_json_without_execution(self):
        before = set((ROOT / ".weslr").rglob("*")) if (ROOT / ".weslr").exists() else set()
        bundle = build_internal_evaluation_corpus_status_bundle_v1()
        after = set((ROOT / ".weslr").rglob("*")) if (ROOT / ".weslr").exists() else set()
        self.assertEqual(before, after)
        self.assertEqual("internal_evaluation_corpus_status_bundle_v1", bundle["bundle_type"])
        self.assertEqual("status_bundle_ready", bundle["readiness_label"])
        self.assertEqual(len(ALLOWED_INTERNAL_EVALUATION_CATEGORIES), bundle["case_count"])
        self.assertFalse(bundle["runner_created"])
        self.assertFalse(bundle["scoring_created"])
        self.assertFalse(bundle["model_calls"])
        self.assertFalse(bundle["advisor_calls"])
        self.assertFalse(bundle["safe_to_execute"])
        exported = to_internal_evaluation_corpus_status_bundle_json_safe_v1(bundle)
        self.assertEqual(bundle, exported)

    def test_50_status_bundle_category_coverage_and_invalid_counts(self):
        bundle = build_internal_evaluation_corpus_status_bundle_v1()
        self.assertEqual(ALLOWED_INTERNAL_EVALUATION_CATEGORIES, set(bundle["categories_covered"]))
        self.assertEqual(len(ALLOWED_INTERNAL_EVALUATION_CATEGORIES), bundle["category_count"])
        self.assertEqual([], bundle["missing_categories"])
        self.assertEqual(0, bundle["invalid_case_count"])
        self.assertEqual(0, bundle["invalid_card_count"])
        self.assertEqual(0, bundle["duplicate_case_id_count"])

    def test_51_status_bundle_invalid_input_needs_operator_review(self):
        bundle = build_internal_evaluation_corpus_status_bundle_v1([valid_case(answer_key=True)])
        self.assertEqual("needs_operator_review", bundle["readiness_label"])
        self.assertGreater(bundle["invalid_case_count"], 0)
        self.assertGreater(bundle["invalid_card_count"], 0)
        self.assertFalse(bundle["safe_to_execute"])

    def test_52_status_bundle_allowed_and_blocked_next_steps(self):
        bundle = build_internal_evaluation_corpus_status_bundle_v1()
        allowed = set(bundle["allowed_next_steps"])
        blocked = set(bundle["blocked_next_steps"])
        self.assertEqual(
            {
                "document_helper_canon",
                "review_status_bundle",
                "design_redacted_advisor_review_adapter",
                "add_more_safe_synthetic_cases",
                "refine_case_taxonomy",
            },
            allowed,
        )
        for action in {
            "create_runner",
            "create_scoring_engine",
            "run_official_benchmark",
            "claim_official_score",
            "call_advisor_llm",
            "call_external_model",
            "ingest_protected_items",
            "store_answer_keys",
            "probe_hidden_prompts",
            "write_weslr_state",
            "runtime_chat_replacement",
        }:
            self.assertIn(action, blocked)
        self.assertTrue(all("runner" not in step and "score" not in step and "call_external_model" not in step for step in allowed))

    def test_53_status_bundle_safety_posture_flags(self):
        posture = build_internal_evaluation_corpus_status_bundle_v1()["safety_posture"]
        self.assertTrue(posture["no_runner"])
        self.assertTrue(posture["no_scoring"])
        self.assertTrue(posture["no_model_calls"])
        self.assertTrue(posture["no_advisor_calls"])
        self.assertTrue(posture["no_protected_items"])
        self.assertTrue(posture["no_answer_keys"])
        self.assertTrue(posture["no_hidden_prompts"])
        self.assertTrue(posture["no_raw_private_text"])
        self.assertTrue(posture["not_official_score"])
        self.assertTrue(posture["non_certifying"])

    def test_54_status_bundle_summary_is_count_only_redacted(self):
        summary = summarize_internal_evaluation_corpus_status_bundle_v1(build_internal_evaluation_corpus_status_bundle_v1())
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual("status_bundle_ready", summary["readiness_label"])
        self.assertEqual(len(ALLOWED_INTERNAL_EVALUATION_CATEGORIES), summary["case_count"])
        self.assertNotIn("input_prompt", summary)
        rendered = str(summary).lower()
        self.assertNotIn("answer key", rendered)
        self.assertNotIn("hidden prompt", rendered)
        self.assertNotIn("protected content", rendered)
        self.assertNotIn("official score", rendered)
        self.assertFalse(summary["scoring_created"])
        self.assertFalse(summary["model_calls"])

    def test_55_status_bundle_markdown_is_safe_and_non_certifying(self):
        rendered = render_internal_evaluation_corpus_status_bundle_markdown_v1(build_internal_evaluation_corpus_status_bundle_v1()).lower()
        self.assertIn("readiness label: status_bundle_ready", rendered)
        self.assertIn("## safety posture", rendered)
        self.assertIn("## allowed next steps", rendered)
        self.assertIn("## blocked next steps", rendered)
        self.assertIn("no_model_calls: true", rendered)
        self.assertIn("non_certifying: true", rendered)
        self.assertIn("create_runner", rendered)
        self.assertNotIn("input_prompt", rendered)
        self.assertNotIn("synthetic prompt:", rendered)
        self.assertNotIn("answer key", rendered)
        self.assertNotIn("hidden prompt", rendered)
        self.assertNotIn("protected material", rendered)
        self.assertNotIn("official score", rendered)
        self.assertNotIn("iq score", rendered)
        self.assertNotIn("certification", rendered)

    def test_56_status_bundle_json_safe_copy_is_deep_copy(self):
        bundle = build_internal_evaluation_corpus_status_bundle_v1()
        exported = to_internal_evaluation_corpus_status_bundle_json_safe_v1(bundle)
        exported["categories_covered"].append("mutated")
        exported["safety_posture"]["no_runner"] = False
        self.assertNotEqual(exported["categories_covered"], bundle["categories_covered"])
        self.assertTrue(bundle["safety_posture"]["no_runner"])


if __name__ == "__main__":
    unittest.main()
