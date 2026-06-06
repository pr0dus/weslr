#!/usr/bin/env python3
"""Focused tests for WESLR cognitive research engine boundary helpers v1."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.cognitive_research_engine_boundaries import (  # noqa: E402
    allowed_cognitive_research_boundary_engine_names_v1,
    build_cognitive_research_engine_boundary_registry_v1,
    build_initial_cognitive_research_engine_boundary_examples_v1,
    get_cognitive_research_engine_boundary_v1,
    summarize_cognitive_research_engine_boundary_registry_v1,
    summarize_cognitive_research_engine_boundary_v1,
    to_cognitive_research_engine_boundary_json_safe_v1,
    validate_cognitive_research_engine_boundary_registry_v1,
    validate_cognitive_research_engine_boundary_v1,
)

EXPECTED_ORDER = (
    "RAW_SIGNAL_CARTOGRAPHER",
    "UNINTELLIGIBLE_OUTPUT_ANALYZER",
    "SIGNAL_VS_NOISE_ENGINE",
    "ALGORITHM_EMERGENCE_ENGINE",
    "MUTABLE_AXIOM_MATH_ENGINE",
)


class CognitiveResearchEngineBoundaryHelpersV1Tests(unittest.TestCase):
    def test_01_allowed_engine_names(self):
        self.assertEqual(allowed_cognitive_research_boundary_engine_names_v1(), EXPECTED_ORDER)

    def test_02_registry_contains_all_engines_in_order(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        self.assertEqual(tuple(registry.keys()), EXPECTED_ORDER)
        self.assertEqual(set(registry.keys()), set(EXPECTED_ORDER))

    def test_03_each_engine_has_distinct_identity_and_kernel(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        identities = {registry[name]["engine_identity"] for name in EXPECTED_ORDER}
        kernels = {registry[name]["cognitive_kernel"] for name in EXPECTED_ORDER}
        self.assertEqual(len(identities), len(EXPECTED_ORDER))
        self.assertEqual(len(kernels), len(EXPECTED_ORDER))

    def test_04_each_engine_has_primitives_grammar_outputs(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        for name in EXPECTED_ORDER:
            with self.subTest(name=name):
                boundary = registry[name]
                self.assertGreater(len(boundary["primitive_space"]), 0)
                self.assertGreater(len(boundary["transformation_grammar"]), 0)
                self.assertGreater(len(boundary["output_categories"]), 0)

    def test_05_safe_and_forbidden_inputs_are_populated(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        for name in EXPECTED_ORDER:
            with self.subTest(name=name):
                boundary = registry[name]
                self.assertGreater(len(boundary["safe_input_categories"]), 0)
                self.assertGreater(len(boundary["forbidden_input_categories"]), 0)

    def test_06_denied_authority_is_enforced(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        for name in EXPECTED_ORDER:
            with self.subTest(name=name):
                boundary = registry[name]
                denied = boundary["denied_authority"]
                self.assertTrue(all(value is False for value in denied.values()))
                self.assertTrue(validate_cognitive_research_engine_boundary_v1(boundary)["valid"])

    def test_07_public_claim_restrictions_are_enforced(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        for name in EXPECTED_ORDER:
            with self.subTest(name=name):
                boundary = registry[name]
                restrictions = boundary["public_claim_restrictions"]
                self.assertTrue(all(value is True for value in restrictions.values()))

    def test_08_cognitive_research_run_is_envelope_only(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        for name in EXPECTED_ORDER:
            with self.subTest(name=name):
                relationship = registry[name]["relationship_to_cognitive_research_run_v1"]
                self.assertTrue(relationship["envelope_only"])
                self.assertTrue(relationship["not_engine_kernel"])
                self.assertTrue(relationship["not_runtime_authority"])
                self.assertTrue(relationship["not_proof_authority"])
                self.assertTrue(relationship["not_public_claim_authority"])

    def test_09_validate_registry_passes(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        validation = validate_cognitive_research_engine_boundary_registry_v1(registry)
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["engine_count"], 5)

    def test_10_unknown_engine_fails_closed(self):
        with self.assertRaises(KeyError):
            get_cognitive_research_engine_boundary_v1("NOT_AN_ENGINE")
        validation = validate_cognitive_research_engine_boundary_v1({"engine_name": "NOT_AN_ENGINE"})
        self.assertFalse(validation["valid"])

    def test_11_missing_fields_fail_closed(self):
        boundary = get_cognitive_research_engine_boundary_v1("RAW_SIGNAL_CARTOGRAPHER")
        boundary.pop("primitive_space")
        validation = validate_cognitive_research_engine_boundary_v1(boundary)
        self.assertFalse(validation["valid"])
        self.assertGreater(validation["violation_count"], 0)

    def test_12_empty_primitive_space_fails_closed(self):
        boundary = get_cognitive_research_engine_boundary_v1("SIGNAL_VS_NOISE_ENGINE")
        boundary["primitive_space"] = []
        validation = validate_cognitive_research_engine_boundary_v1(boundary)
        self.assertFalse(validation["valid"])

    def test_13_empty_forbidden_input_categories_fails_closed(self):
        boundary = get_cognitive_research_engine_boundary_v1("UNINTELLIGIBLE_OUTPUT_ANALYZER")
        boundary["forbidden_input_categories"] = []
        validation = validate_cognitive_research_engine_boundary_v1(boundary)
        self.assertFalse(validation["valid"])

    def test_14_empty_output_categories_fails_closed(self):
        boundary = get_cognitive_research_engine_boundary_v1("ALGORITHM_EMERGENCE_ENGINE")
        boundary["output_categories"] = []
        validation = validate_cognitive_research_engine_boundary_v1(boundary)
        self.assertFalse(validation["valid"])

    def test_15_missing_anti_flattening_rule_fails_closed(self):
        boundary = get_cognitive_research_engine_boundary_v1("MUTABLE_AXIOM_MATH_ENGINE")
        boundary["anti_flattening_rule"] = ""
        validation = validate_cognitive_research_engine_boundary_v1(boundary)
        self.assertFalse(validation["valid"])

    def test_16_forbidden_authority_true_fails_closed(self):
        boundary = get_cognitive_research_engine_boundary_v1("RAW_SIGNAL_CARTOGRAPHER")
        boundary["denied_authority"]["runtime_authority"] = True
        validation = validate_cognitive_research_engine_boundary_v1(boundary)
        self.assertFalse(validation["valid"])

    def test_17_public_claim_restriction_false_fails_closed(self):
        boundary = get_cognitive_research_engine_boundary_v1("RAW_SIGNAL_CARTOGRAPHER")
        boundary["public_claim_restrictions"]["proof_claims_blocked"] = False
        validation = validate_cognitive_research_engine_boundary_v1(boundary)
        self.assertFalse(validation["valid"])

    def test_18_cognitive_research_run_not_kernel_violation_fails_closed(self):
        boundary = get_cognitive_research_engine_boundary_v1("RAW_SIGNAL_CARTOGRAPHER")
        boundary["relationship_to_cognitive_research_run_v1"]["not_engine_kernel"] = False
        validation = validate_cognitive_research_engine_boundary_v1(boundary)
        self.assertFalse(validation["valid"])

    def test_19_flattening_markers_fail_closed(self):
        boundary = get_cognitive_research_engine_boundary_v1("ALGORITHM_EMERGENCE_ENGINE")
        boundary["cognitive_kernel"] = "acts like a generic assistant"
        validation = validate_cognitive_research_engine_boundary_v1(boundary)
        self.assertFalse(validation["valid"])

    def test_20_relationship_graph_order_is_correct(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        self.assertIsNone(registry["RAW_SIGNAL_CARTOGRAPHER"]["prior_engine_name"])
        self.assertEqual(registry["RAW_SIGNAL_CARTOGRAPHER"]["next_engine_name"], "UNINTELLIGIBLE_OUTPUT_ANALYZER")
        self.assertEqual(registry["UNINTELLIGIBLE_OUTPUT_ANALYZER"]["prior_engine_name"], "RAW_SIGNAL_CARTOGRAPHER")
        self.assertEqual(registry["UNINTELLIGIBLE_OUTPUT_ANALYZER"]["next_engine_name"], "SIGNAL_VS_NOISE_ENGINE")
        self.assertEqual(registry["SIGNAL_VS_NOISE_ENGINE"]["prior_engine_name"], "UNINTELLIGIBLE_OUTPUT_ANALYZER")
        self.assertEqual(registry["SIGNAL_VS_NOISE_ENGINE"]["next_engine_name"], "ALGORITHM_EMERGENCE_ENGINE")
        self.assertEqual(registry["ALGORITHM_EMERGENCE_ENGINE"]["prior_engine_name"], "SIGNAL_VS_NOISE_ENGINE")
        self.assertEqual(registry["ALGORITHM_EMERGENCE_ENGINE"]["next_engine_name"], "MUTABLE_AXIOM_MATH_ENGINE")
        self.assertEqual(registry["MUTABLE_AXIOM_MATH_ENGINE"]["prior_engine_name"], "ALGORITHM_EMERGENCE_ENGINE")
        self.assertIsNone(registry["MUTABLE_AXIOM_MATH_ENGINE"]["next_engine_name"])

    def test_21_json_safe_conversion_works(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        safe = to_cognitive_research_engine_boundary_json_safe_v1(registry)
        json.dumps(safe)
        self.assertIsInstance(safe, dict)
        self.assertIsInstance(safe["RAW_SIGNAL_CARTOGRAPHER"]["primitive_space"], list)

    def test_22_summaries_are_bounded_and_safe(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        summary = summarize_cognitive_research_engine_boundary_v1(registry["RAW_SIGNAL_CARTOGRAPHER"])
        registry_summary = summarize_cognitive_research_engine_boundary_registry_v1(registry)
        self.assertLess(len(summary), 800)
        self.assertLess(len(registry_summary), 500)
        self.assertNotIn("secret", summary.lower())
        self.assertNotIn("secret", registry_summary.lower())

    def test_23_examples_are_synthetic_and_non_private(self):
        examples = build_initial_cognitive_research_engine_boundary_examples_v1()
        self.assertEqual(len(examples), 5)
        for example in examples:
            with self.subTest(engine=example["engine_name"]):
                self.assertTrue(any(str(ref).startswith("synthetic:") for ref in example["input_metadata_refs"]))
                text = json.dumps(example).lower()
                self.assertNotIn("secret reasoning", text)
                self.assertNotIn("hidden prompt", text)
                self.assertNotIn("token=", text)

    def test_24_helper_source_has_no_forbidden_imports(self):
        source = Path(ROOT / "weslr" / "cognitive_research_engine_boundaries.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        lowered = " ".join(imports).lower()
        for forbidden in ("subprocess", "socket", "urllib", "requests", "asyncio", "http.client"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, lowered)

    def test_25_protected_files_unchanged(self):
        protected = ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"]
        for rel in protected:
            with self.subTest(rel=rel):
                subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], check=True)


if __name__ == "__main__":
    unittest.main()
