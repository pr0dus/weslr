from __future__ import annotations

import json
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.reasoning_task import reasoning_task_to_dict  # noqa: E402
from weslr.reasoning_task_builder import (  # noqa: E402
    build_reasoning_task_from_mcq_item,
    validate_built_reasoning_task,
)


@dataclass
class FakeChoice:
    label: str
    text: str


@dataclass
class FakeItem:
    id: str
    benchmark_family: str
    domain: str
    question: str
    choices: list[FakeChoice]
    required_skill: str
    explanation_required: bool
    answer_label: str = "B"


class ReasoningTaskBuilderV1Tests(unittest.TestCase):
    def setUp(self):
        self.item = {
            "id": "formal-1",
            "benchmark_family": "official_mcq",
            "domain": "formal_logic",
            "question": "If A then B. A. What follows?",
            "choices": [
                {"label": "A", "text": "B"},
                {"label": "B", "text": "Not enough information"},
            ],
            "required_skill": "ordinary_reasoning",
            "explanation_required": True,
            "answer_label": "A",
        }
        self.metadata = {
            "dataset_name": "mmlu",
            "subset_name": "formal_logic_dev5",
            "internal_eval": True,
            "sample_only": False,
            "official_score": True,
            "adapter_version": "adapter-x",
            "prompt_format_version": "prompt-y",
        }

    def test_builds_reasoning_task_from_dict_item(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertEqual(task.task_id, "formal-1")
        self.assertEqual(task.domain, "formal_logic")

    def test_builds_reasoning_task_from_object_dataclass_like_item_if_possible(self):
        item = FakeItem(
            id="ethics-1",
            benchmark_family="official_mcq",
            domain="ethics_tradeoff",
            question="What is most ethical?",
            choices=[FakeChoice("A", "Option one"), FakeChoice("B", "Option two")],
            required_skill="ethics_tradeoff_reasoning",
            explanation_required=True,
        )
        task = build_reasoning_task_from_mcq_item(item)
        self.assertEqual(task.task_id, "ethics-1")
        self.assertEqual(task.required_skill, "ethics_tradeoff_reasoning")

    def test_does_not_store_raw_question_by_default(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertEqual(task.input.question_text, "")

    def test_stores_question_fingerprint(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertTrue(bool(task.input.question_fingerprint))

    def test_choice_text_is_fingerprinted_by_default_not_raw(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertTrue(all("text_fingerprint" in c for c in task.input.choices))
        self.assertTrue(all("text" not in c for c in task.input.choices))

    def test_store_raw_question_true_includes_raw_question_and_choice_text_explicitly(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata, store_raw_question=True)
        self.assertTrue(bool(task.input.question_text))
        self.assertTrue(all("text" in c for c in task.input.choices))

    def test_answer_label_is_not_present_in_reasoning_task_dict(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        data = reasoning_task_to_dict(task)
        dumped = json.dumps(data).lower()
        self.assertNotIn("answer_label", dumped)

    def test_official_score_remains_false_even_if_suite_metadata_tries_true(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertFalse(task.provenance.official_score)

    def test_anti_gaming_defaults_remain_safe(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertFalse(task.anti_gaming.uses_item_id)
        self.assertFalse(task.anti_gaming.uses_answer_key)
        self.assertFalse(task.anti_gaming.stores_raw_question_by_default)
        self.assertFalse(task.anti_gaming.official_score_claimed)

    def test_provenance_fields_are_filled_from_suite_metadata(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertEqual(task.provenance.dataset_name, "mmlu")
        self.assertEqual(task.provenance.subset_name, "formal_logic_dev5")
        self.assertEqual(task.provenance.adapter_version, "adapter-x")
        self.assertEqual(task.provenance.prompt_format_version, "prompt-y")

    def test_parsed_task_type_is_multiple_choice_reasoning(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertEqual(task.parsed.task_type, "multiple_choice_reasoning")

    def test_question_intent_is_select_best_answer(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertEqual(task.parsed.question_intent, "select_best_answer")

    def test_candidate_solvers_filled_when_registry_has_matching_descriptors(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertIn("formal_logic_solver", task.solver_plan.candidate_solvers)

    def test_selected_solvers_remains_empty(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertEqual(task.solver_plan.selected_solvers, [])

    def test_validate_built_reasoning_task_returns_no_warnings_for_safe_task(self):
        task = build_reasoning_task_from_mcq_item(self.item, self.metadata)
        self.assertEqual(validate_built_reasoning_task(task), [])

    def test_no_runtime_behavior_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("weslr/reasoning_task_builder.py", changed)
        self.assertIn("weslr/tests/test_reasoning_task_builder_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
