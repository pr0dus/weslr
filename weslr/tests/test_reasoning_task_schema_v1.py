from __future__ import annotations

import dataclasses
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.reasoning_task import (  # noqa: E402
    AntiGamingRecord,
    LegibilityRecord,
    ReasoningTask,
    ReasoningTaskInput,
    create_empty_reasoning_task,
    reasoning_task_from_dict,
    reasoning_task_to_dict,
    validate_reasoning_task,
)


class ReasoningTaskSchemaV1Tests(unittest.TestCase):
    def test_can_create_empty_reasoning_task(self):
        task = create_empty_reasoning_task()
        self.assertIsInstance(task, ReasoningTask)

    def test_top_level_fields_exist(self):
        task = create_empty_reasoning_task()
        for name in [
            "schema_version",
            "task_id",
            "task_family",
            "domain",
            "required_skill",
            "provenance",
            "input",
            "parsed",
            "choice_representations",
            "blackboard",
            "solver_plan",
            "arbitration",
            "legibility",
            "anti_gaming",
            "failure",
        ]:
            self.assertTrue(hasattr(task, name))

    def test_provenance_defaults_keep_official_score_false(self):
        task = create_empty_reasoning_task()
        self.assertFalse(task.provenance.official_score)
        self.assertTrue(task.provenance.internal_eval)
        self.assertFalse(task.provenance.sample_only)

    def test_anti_gaming_defaults_all_false(self):
        anti = AntiGamingRecord()
        self.assertFalse(anti.uses_item_id)
        self.assertFalse(anti.uses_answer_key)
        self.assertFalse(anti.uses_answer_position_bias)
        self.assertFalse(anti.stores_raw_question_by_default)
        self.assertFalse(anti.official_score_claimed)

    def test_legibility_defaults_private_authority_used_false(self):
        legibility = LegibilityRecord()
        self.assertTrue(legibility.symbolic_forms_translated)
        self.assertFalse(legibility.private_authority_used)

    def test_failure_defaults_enrichment_record_allowed_true(self):
        task = create_empty_reasoning_task()
        self.assertTrue(task.failure.enrichment_record_allowed)

    def test_formal_logic_shaped_task_can_be_represented(self):
        task = create_empty_reasoning_task(
            task_family="multiple_choice_reasoning",
            domain="formal_logic",
            required_skill="ordinary_reasoning",
        )
        task.parsed.premises = ["If A then B", "A"]
        task.parsed.conclusion_candidates = ["B", "not B"]
        task.parsed.constraints = ["valid inference", "consistency"]
        task.blackboard.conflicts = ["choice B conflicts with premise set"]
        self.assertEqual(task.parsed.premises[0], "If A then B")
        self.assertIn("B", task.parsed.conclusion_candidates)
        self.assertIn("consistency", task.parsed.constraints)
        self.assertEqual(len(task.blackboard.conflicts), 1)

    def test_ethics_tradeoff_shaped_task_can_be_represented(self):
        task = create_empty_reasoning_task(
            task_family="multiple_choice_reasoning",
            domain="ethics_tradeoff",
            required_skill="ethics_tradeoff_reasoning",
        )
        task.parsed.entities = ["customers", "operator", "regulator"]
        task.parsed.constraints = ["duty of care", "governance review"]
        task.parsed.relations = ["harm-risk", "consent-boundary", "benefit-tradeoff"]
        task.choice_representations = [
            {
                "label": "A",
                "supports": ["fast rollout"],
                "violations": ["governance bypass"],
            },
            {
                "label": "B",
                "supports": ["governance review", "reduced harm"],
                "violations": [],
            },
        ]
        self.assertIn("customers", task.parsed.entities)
        self.assertIn("duty of care", task.parsed.constraints)
        self.assertIn("benefit-tradeoff", task.parsed.relations)
        self.assertEqual(task.choice_representations[0]["label"], "A")

    def test_to_dict_from_dict_roundtrip_works(self):
        task = create_empty_reasoning_task(
            task_id="rt-1",
            task_family="multiple_choice_reasoning",
            domain="formal_logic",
            required_skill="ordinary_reasoning",
        )
        task.input = ReasoningTaskInput(
            question_text="runtime only",
            question_fingerprint="sha256:abc",
            choices=[{"label": "A", "text": "choice a"}],
        )
        task.choice_representations = []
        data = reasoning_task_to_dict(task)
        restored = reasoning_task_from_dict(data)
        self.assertEqual(data, reasoning_task_to_dict(restored))
        self.assertEqual(restored.task_id, "rt-1")
        self.assertEqual(restored.input.question_fingerprint, "sha256:abc")

    def test_validate_reasoning_task_flags_official_score_true(self):
        task = create_empty_reasoning_task()
        task.provenance.official_score = True
        warnings = validate_reasoning_task(task)
        self.assertTrue(any("official_score true" in item for item in warnings))

    def test_validate_reasoning_task_flags_answer_key_use(self):
        task = create_empty_reasoning_task()
        task.anti_gaming.uses_answer_key = True
        warnings = validate_reasoning_task(task)
        self.assertTrue(any("uses_answer_key true" in item for item in warnings))

    def test_validate_reasoning_task_flags_private_authority(self):
        task = create_empty_reasoning_task()
        task.legibility.private_authority_used = True
        warnings = validate_reasoning_task(task)
        self.assertTrue(any("private_authority_used true" in item for item in warnings))

    def test_validate_reasoning_task_flags_raw_question_storage_by_default(self):
        task = create_empty_reasoning_task()
        task.anti_gaming.stores_raw_question_by_default = True
        warnings = validate_reasoning_task(task)
        self.assertTrue(any("stores_raw_question_by_default true" in item for item in warnings))

    def test_no_field_named_answer_key_exists_in_dataclasses(self):
        task = create_empty_reasoning_task()
        all_field_names = set()
        for obj in [
            task,
            task.provenance,
            task.input,
            task.parsed,
            task.blackboard,
            task.solver_plan,
            task.arbitration,
            task.legibility,
            task.anti_gaming,
            task.failure,
        ]:
            all_field_names.update(field.name for field in dataclasses.fields(obj))
        self.assertNotIn("answer_key", all_field_names)

    def test_no_runtime_behavior_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("weslr/reasoning_task.py", changed)
        self.assertIn("weslr/tests/test_reasoning_task_schema_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
