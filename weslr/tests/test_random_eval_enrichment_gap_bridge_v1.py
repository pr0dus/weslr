from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from weslr.evals import enrichment_gap_bridge as bridge  # noqa: E402
from weslr.internal_reasoning_graph.store import InternalReasoningGraphStore  # noqa: E402


class RandomEvalEnrichmentGapBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.graph_dir = Path(self.tempdir.name) / "irg"
        self.store = InternalReasoningGraphStore(graph_dir=self.graph_dir)
        self.weak_result = {
            "prompt": "What should you do when you are not sure?",
            "category": "ambiguity_uncertainty",
            "path": "fallback_safe",
            "response_text": "I'm not able to process that request.",
            "fallback_safe": True,
            "repeated_response": False,
            "generic_fallback_phrase": True,
            "score": 0.22,
            "notes": ["fallback", "generic_fallback", "weak_uncertainty_handling"],
        }

    def tearDown(self):
        self.tempdir.cleanup()

    def test_failure_mode_classification_for_fallback_result(self):
        self.assertEqual(bridge.classify_failure_mode(self.weak_result), "weak_uncertainty_handling")

    def test_category_maps_to_missing_skill(self):
        self.assertEqual(
            bridge.map_category_to_missing_skill("ambiguity_uncertainty"),
            "uncertainty_reasoning",
        )

    def test_missing_skill_maps_to_target_substrate(self):
        self.assertEqual(
            bridge.map_missing_skill_to_target_substrate("human_context_reasoning"),
            "meaning_obligation_and_entity_memory",
        )
        self.assertEqual(
            bridge.map_missing_skill_to_target_substrate("uncertainty_reasoning"),
            "evidence_substrate_and_eval_scorecard",
        )

    def test_gap_kwargs_include_legibility_summary_and_fingerprint_without_raw_prompt(self):
        kwargs = bridge.build_gap_record_kwargs(self.weak_result)
        self.assertIn("operator review required", kwargs["legibility_summary"].lower())
        self.assertIn("no automatic execution", kwargs["legibility_summary"].lower())
        self.assertEqual(len(kwargs["prompt_fingerprint"]), 64)
        self.assertNotIn("source_prompt", kwargs)
        self.assertEqual(kwargs["failure_mode"], "weak_uncertainty_handling")

    def test_create_records_from_small_eval_summary_into_temp_graph_store(self):
        summary = {"results": [self.weak_result]}
        created = bridge.create_gap_records_from_eval_summary(summary, self.store)
        self.assertEqual(len(created), 1)
        gap = created[0]
        self.assertEqual(gap.metadata["source_eval"], "random_ordinary_intelligence_prep_v1")
        self.assertEqual(gap.metadata["category"], "ambiguity_uncertainty")
        self.assertTrue(gap.metadata["operator_review_required"])
        self.assertFalse(gap.metadata["execution_allowed"])

    def test_records_can_be_summarized_without_sensitive_prompt(self):
        created = bridge.create_gap_records_from_eval_summary({"results": [self.weak_result]}, self.store)
        summary = self.store.summarize_enrichment_gap_record(created[0].id, include_sensitive=False)
        self.assertNotIn("source_prompt", summary)
        self.assertEqual(summary["source_eval"], "random_ordinary_intelligence_prep_v1")
        self.assertTrue(summary["source_prompt_fingerprint"])

    def test_link_true_creates_graph_relationships(self):
        created = bridge.create_gap_records_from_eval_summary(
            {"results": [self.weak_result]},
            self.store,
            link=True,
        )
        gap = created[0]
        summary = self.store.summarize_enrichment_gap_record(gap.id)
        graph_links = summary["graph_links"]
        self.assertTrue(graph_links["missing_skill_node_id"])
        self.assertTrue(graph_links["target_substrate_node_id"])
        self.assertTrue(graph_links["proposed_enrichment_node_id"])
        self.assertTrue(graph_links["tests_required_node_id"])
        self.assertTrue(graph_links["operator_review_node_id"])

    def test_dry_run_cli_does_not_write_project_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                before = set(os.listdir(tmpdir))
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = bridge.main(["--seed", "42", "--count", "5", "--threshold", "0.65", "--dry-run"])
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(old_cwd)
        self.assertEqual(rc, 0)
        self.assertEqual(before, after)
        self.assertIn("dry-run", buf.getvalue().lower())

    def test_max_records_cap_is_respected(self):
        summary = {"results": [dict(self.weak_result, prompt=f"weak prompt {idx}") for idx in range(5)]}
        created = bridge.create_gap_records_from_eval_summary(summary, self.store, max_records=2)
        self.assertEqual(len(created), 2)

    def test_eval_layer_remains_measurement_source_only(self):
        created = bridge.create_gap_records_from_eval_summary({"results": [self.weak_result]}, self.store, link=True)
        gap = created[0]
        self.assertEqual(gap.metadata["source_eval"], "random_ordinary_intelligence_prep_v1")
        self.assertIsNone(self.store.find_node_by_name("random_ordinary_intelligence_prep_v1"))
        self.assertEqual(gap.metadata["target_substrate"], "evidence_substrate_and_eval_scorecard")


if __name__ == "__main__":
    unittest.main()
