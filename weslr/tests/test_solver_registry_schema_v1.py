from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.solver_registry import (  # noqa: E402
    SolverCapability,
    SolverDescriptor,
    SolverSafetyProfile,
    create_empty_solver_registry,
    get_solver,
    list_candidate_solvers,
    register_solver,
    validate_solver_descriptor,
)


class SolverRegistrySchemaV1Tests(unittest.TestCase):
    def test_can_create_empty_registry(self):
        registry = create_empty_solver_registry()
        self.assertEqual(registry.schema_version, "1.0")
        self.assertTrue(len(registry.solvers) >= 8)

    def test_safe_defaults_are_safe(self):
        safety = SolverSafetyProfile()
        self.assertFalse(safety.uses_item_id)
        self.assertFalse(safety.uses_answer_key)
        self.assertFalse(safety.stores_raw_question_by_default)
        self.assertFalse(safety.official_score_claimed)
        self.assertFalse(safety.private_authority_used)
        self.assertFalse(safety.opaque_output_allowed)
        self.assertTrue(safety.requires_human_legible_explanation)

    def test_can_register_solver_descriptor(self):
        registry = create_empty_solver_registry()
        descriptor = SolverDescriptor(
            solver_id="test_solver",
            solver_family="test_family",
            description="test",
            supported_task_types=["structured_reasoning"],
            supported_domains=["formal_logic"],
            supported_skills=["ordinary_reasoning"],
        )
        register_solver(registry, descriptor)
        self.assertIsNotNone(get_solver(registry, "test_solver"))

    def test_can_retrieve_solver_by_id(self):
        registry = create_empty_solver_registry()
        solver = get_solver(registry, "formal_logic_solver")
        self.assertIsNotNone(solver)
        self.assertEqual(solver.solver_id, "formal_logic_solver")

    def test_candidate_solver_lookup_by_task_domain_skill_works(self):
        registry = create_empty_solver_registry()
        candidates = list_candidate_solvers(
            registry,
            task_type="multiple_choice_reasoning",
            domain="formal_logic",
            required_skill="ordinary_reasoning",
        )
        ids = {solver.solver_id for solver in candidates}
        self.assertIn("formal_logic_solver", ids)
        self.assertNotIn("science_mechanism_solver", ids)

    def test_validation_flags_answer_key_use(self):
        descriptor = SolverDescriptor(solver_id="bad")
        descriptor.safety_profile.uses_answer_key = True
        warnings = validate_solver_descriptor(descriptor)
        self.assertTrue(any("uses_answer_key true" in item for item in warnings))

    def test_validation_flags_item_id_use(self):
        descriptor = SolverDescriptor(solver_id="bad")
        descriptor.safety_profile.uses_item_id = True
        warnings = validate_solver_descriptor(descriptor)
        self.assertTrue(any("uses_item_id true" in item for item in warnings))

    def test_validation_flags_official_score_claim(self):
        descriptor = SolverDescriptor(solver_id="bad")
        descriptor.safety_profile.official_score_claimed = True
        warnings = validate_solver_descriptor(descriptor)
        self.assertTrue(any("official_score_claimed true" in item for item in warnings))

    def test_validation_flags_private_authority(self):
        descriptor = SolverDescriptor(solver_id="bad")
        descriptor.safety_profile.private_authority_used = True
        warnings = validate_solver_descriptor(descriptor)
        self.assertTrue(any("private_authority_used true" in item for item in warnings))

    def test_validation_flags_opaque_output(self):
        descriptor = SolverDescriptor(solver_id="bad")
        descriptor.safety_profile.opaque_output_allowed = True
        warnings = validate_solver_descriptor(descriptor)
        self.assertTrue(any("opaque_output_allowed true" in item for item in warnings))

    def test_validation_flags_enabled_solver_with_no_supported_skills(self):
        descriptor = SolverDescriptor(
            solver_id="bad",
            enabled=True,
            supported_task_types=["structured_reasoning"],
            supported_skills=[],
        )
        warnings = validate_solver_descriptor(descriptor)
        self.assertTrue(any("enabled solver with no supported skills" in item for item in warnings))

    def test_validation_flags_answer_selecting_solver_without_legibility(self):
        descriptor = SolverDescriptor(
            solver_id="bad",
            legibility_required=False,
            capabilities=[SolverCapability(can_select_answer=True)],
        )
        warnings = validate_solver_descriptor(descriptor)
        self.assertTrue(any("without legibility_required" in item for item in warnings))

    def test_predefined_descriptors_exist(self):
        registry = create_empty_solver_registry()
        ids = {solver.solver_id for solver in registry.solvers}
        for required in [
            "formal_logic_solver",
            "ethics_tradeoff_solver",
            "science_mechanism_solver",
            "semantic_language_solver",
            "math_reasoning_solver",
            "evidence_retrieval_solver",
            "analogy_abstraction_solver",
            "uncertainty_calibration_solver",
        ]:
            self.assertIn(required, ids)

    def test_predefined_descriptors_are_disabled_by_default(self):
        registry = create_empty_solver_registry()
        for solver in registry.solvers:
            self.assertFalse(solver.enabled)

    def test_predefined_descriptors_include_formal_logic_and_ethics_tradeoff(self):
        registry = create_empty_solver_registry()
        formal = get_solver(registry, "formal_logic_solver")
        ethics = get_solver(registry, "ethics_tradeoff_solver")
        self.assertIn("formal_logic", formal.supported_domains)
        self.assertIn("ethics_tradeoff", ethics.supported_domains)

    def test_no_runtime_behavior_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("weslr/solver_registry.py", changed)
        self.assertIn("weslr/tests/test_solver_registry_schema_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
