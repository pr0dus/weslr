from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.evals import official_mcq_gap_bridge as bridge  # noqa: E402
from weslr.internal_reasoning_graph.store import InternalReasoningGraphStore  # noqa: E402


class OfficialMcqGapBridgeV1Tests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.graph_dir = Path(self.tempdir.name) / "irg"
        self.result_path = Path(self.tempdir.name) / "official_mcq_result.json"
        self.payload = {
            "suite_id": "official_mcq_internal_eval_demo",
            "sample_only": False,
            "internal_eval": True,
            "official_score": False,
            "metadata": {
                "suite_id": "official_mcq_internal_eval_demo",
                "dataset_name": "SyntheticMMLU",
                "dataset_version": "v0-synthetic",
                "subset_name": "demo5",
            },
            "results": [
                {
                    "id": "item_weak_1",
                    "domain": "science",
                    "benchmark_family": "mmlu_gpqa_style",
                    "required_skill": "science_explanation",
                    "question": "SYNTHETIC_PLACEHOLDER_QUESTION_1",
                    "selected_label": None,
                    "answer_label": "A",
                    "correct": False,
                    "confidence": 0.2,
                    "uncertainty": "high",
                    "failure_mode": "no_answer_selection",
                    "explanation": "No confident answer.",
                    "response_path": "fallback_safe",
                    "official_score": False,
                    "sample_only": False,
                },
                {
                    "id": "item_strong_1",
                    "domain": "language_semantics",
                    "benchmark_family": "mmlu_gpqa_style",
                    "required_skill": "semantic_explanation",
                    "question": "SYNTHETIC_PLACEHOLDER_QUESTION_2",
                    "selected_label": "B",
                    "answer_label": "B",
                    "correct": True,
                    "confidence": 0.92,
                    "uncertainty": "low",
                    "failure_mode": None,
                    "explanation": "Strong explanation.",
                    "response_path": "semantic_route",
                    "official_score": False,
                    "sample_only": False,
                },
                {
                    "id": "item_weak_2",
                    "domain": "governance_evidence",
                    "benchmark_family": "mmlu_gpqa_style",
                    "required_skill": "weslr_routing_and_governance_reasoning",
                    "question": "SYNTHETIC_PLACEHOLDER_QUESTION_3",
                    "selected_label": "C",
                    "answer_label": "A",
                    "correct": False,
                    "confidence": 0.48,
                    "uncertainty": "medium",
                    "failure_mode": "incorrect_answer",
                    "explanation": "Wrong answer selected.",
                    "response_path": "governance_route",
                    "official_score": False,
                    "sample_only": False,
                },
            ],
        }
        self.result_path.write_text(json.dumps(self.payload), encoding="utf-8")
        self.store = InternalReasoningGraphStore(graph_dir=self.graph_dir)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_loads_sample_style_mcq_result(self):
        sample_payload = dict(self.payload)
        sample_payload["sample_only"] = True
        sample_payload["internal_eval"] = False
        sample_path = Path(self.tempdir.name) / "sample_mcq_result.json"
        sample_path.write_text(json.dumps(sample_payload), encoding="utf-8")
        loaded = bridge.load_mcq_result(sample_path)
        self.assertTrue(loaded["sample_only"])
        self.assertFalse(loaded["official_score"])

    def test_rejects_official_score_true(self):
        bad = dict(self.payload)
        bad["official_score"] = True
        bad_path = Path(self.tempdir.name) / "bad_official.json"
        bad_path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(ValueError):
            bridge.load_mcq_result(bad_path)

    def test_identifies_incorrect_no_answer_high_uncertainty_as_weak(self):
        self.assertTrue(bridge.is_weak_mcq_result(self.payload["results"][0]))
        self.assertTrue(bridge.is_weak_mcq_result(self.payload["results"][2]))

    def test_correct_high_confidence_item_is_not_weak(self):
        self.assertFalse(bridge.is_weak_mcq_result(self.payload["results"][1]))

    def test_required_skill_maps_to_missing_skill(self):
        self.assertEqual(
            bridge.map_required_skill_to_missing_skill("science_explanation"),
            "science_mechanism_explanation",
        )
        self.assertEqual(
            bridge.map_required_skill_to_missing_skill("semantic_explanation"),
            "semantic_explanation",
        )
        self.assertEqual(
            bridge.map_required_skill_to_missing_skill("unknown_skill"),
            "unknown_benchmark_skill_gap",
        )

    def test_missing_skill_maps_to_target_substrate(self):
        self.assertEqual(
            bridge.map_missing_skill_to_target_substrate("science_mechanism_explanation"),
            "concept_graph_and_evidence_substrate",
        )
        self.assertEqual(
            bridge.map_missing_skill_to_target_substrate("semantic_explanation"),
            "meaning_obligation_and_capability_taxonomy",
        )
        self.assertEqual(
            bridge.map_missing_skill_to_target_substrate("ordinary_reasoning"),
            "internal_reasoning_graph_and_eval_scorecard",
        )
        self.assertEqual(
            bridge.map_missing_skill_to_target_substrate("ethics_tradeoff_reasoning"),
            "internal_reasoning_graph_and_governance_surface",
        )

    def test_gap_kwargs_do_not_include_raw_question_by_default(self):
        kwargs = bridge.build_gap_kwargs_from_mcq_result(self.payload["results"][0], self.payload["metadata"])
        self.assertNotIn("source_prompt", kwargs)
        self.assertNotIn("SYNTHETIC_PLACEHOLDER_QUESTION_1", json.dumps(kwargs))

    def test_gap_kwargs_do_not_include_answer_label_by_default(self):
        kwargs = bridge.build_gap_kwargs_from_mcq_result(self.payload["results"][0], self.payload["metadata"])
        self.assertNotIn("answer_label", kwargs)
        self.assertNotIn("selected_label", kwargs)

    def test_gap_kwargs_include_question_fingerprint(self):
        kwargs = bridge.build_gap_kwargs_from_mcq_result(self.payload["results"][0], self.payload["metadata"])
        self.assertEqual(len(kwargs["prompt_fingerprint"]), 64)
        self.assertIn("question_fingerprint", "\n".join(kwargs["evidence_refs"]))

    def test_creates_enrichment_gap_records_in_temp_graph_store(self):
        created = bridge.create_gap_records_from_mcq_result_file(self.result_path, self.store)
        self.assertEqual(len(created), 2)
        self.assertEqual(self.store.get_enrichment_gap_records()[0].metadata["source_eval"], bridge.SOURCE_EVAL)

    def test_created_records_require_operator_review_and_execution_allowed_false(self):
        created = bridge.create_gap_records_from_mcq_result_file(self.result_path, self.store)
        for gap in created:
            self.assertTrue(gap.metadata["operator_review_required"])
            self.assertFalse(gap.metadata["execution_allowed"])
            self.assertTrue(gap.metadata["read_only"])

    def test_link_true_creates_graph_relationships_if_supported(self):
        created = bridge.create_gap_records_from_mcq_result_file(self.result_path, self.store, link=True)
        summary = self.store.summarize_enrichment_gap_record(created[0].id)
        self.assertTrue(summary["graph_links"]["missing_skill_node_id"])
        self.assertTrue(summary["graph_links"]["target_substrate_node_id"])

    def test_cli_dry_run_writes_nothing(self):
        empty_graph_dir = Path(self.tempdir.name) / "dry_graph"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = bridge.main(["--result", str(self.result_path), "--dry-run", "--json"])
        self.assertEqual(rc, 0)
        self.assertFalse(empty_graph_dir.exists())
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(payload["would_create"], 2)

    def test_cli_with_temp_graph_dir_writes_only_to_temp_graph_dir(self):
        temp_graph_dir = Path(self.tempdir.name) / "write_graph"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = bridge.main([
                "--result", str(self.result_path),
                "--graph-dir", str(temp_graph_dir),
                "--json",
            ])
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["mode"], "write")
        self.assertTrue(temp_graph_dir.exists())
        self.assertTrue((temp_graph_dir / "nodes").exists())
        self.assertFalse((ROOT / "weslr" / "internal_reasoning_graph" / "internal_reasoning_graph" / "nodes").exists() and temp_graph_dir != (ROOT / "weslr" / "internal_reasoning_graph" / "internal_reasoning_graph"))

    def test_proposed_enrichment_is_general_not_item_specific_answer_memorization(self):
        kwargs = bridge.build_gap_kwargs_from_mcq_result(self.payload["results"][2], self.payload["metadata"])
        text = kwargs["proposed_enrichment"].lower()
        self.assertNotIn("option a", text)
        self.assertNotIn("answer_label", text)
        self.assertNotIn("choose option", text)
        self.assertIn("not benchmark gaming", text)

    def test_include_sensitive_true_stores_question_only_when_requested(self):
        kwargs = bridge.build_gap_kwargs_from_mcq_result(
            self.payload["results"][0],
            self.payload["metadata"],
            include_sensitive=True,
        )
        self.assertEqual(kwargs["source_prompt"], "SYNTHETIC_PLACEHOLDER_QUESTION_1")
        self.assertNotIn("answer_label", kwargs)

    def test_max_records_cap_is_respected(self):
        created = bridge.create_gap_records_from_mcq_result_file(self.result_path, self.store, max_records=1)
        self.assertEqual(len(created), 1)


if __name__ == "__main__":
    unittest.main()
