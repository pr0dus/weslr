from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.evals.official_mcq_adapter import (  # noqa: E402
    build_prompt,
    extract_selected_label,
    load_suite,
    run_item,
    run_suite,
)


SUITE_PATH = ROOT / "weslr" / "evals" / "conversation_suites" / "official_mcq_tiny_sample_v0.json"
GENERALIZATION_SUITE_PATH = ROOT / "weslr" / "evals" / "conversation_suites" / "official_mcq_generalization_sample_v1.json"


class OfficialMcqAdapterV0Tests(unittest.TestCase):
    def test_loads_tiny_sample_suite(self):
        suite = load_suite(SUITE_PATH)
        self.assertEqual(suite["suite_id"], "official_mcq_tiny_sample_v0")
        self.assertEqual(len(suite["items"]), 10)

    def test_generalization_sample_also_loads(self):
        suite = load_suite(GENERALIZATION_SUITE_PATH)
        self.assertEqual(suite["suite_id"], "official_mcq_generalization_sample_v1")
        self.assertEqual(len(suite["items"]), 20)

    def test_suite_is_sample_only_and_not_official(self):
        suite = load_suite(SUITE_PATH)
        self.assertTrue(suite["sample_only"])
        self.assertFalse(suite["official_score"])
        self.assertFalse(suite["internal_eval"])

    def test_runs_adapter_on_tiny_suite(self):
        summary = run_suite(SUITE_PATH)
        self.assertEqual(summary.suite_id, "official_mcq_tiny_sample_v0")
        self.assertEqual(summary.total, 10)
        self.assertGreaterEqual(summary.answered_count + summary.no_answer_count, summary.total)

    def test_produces_accuracy_and_failure_modes(self):
        summary = run_suite(SUITE_PATH)
        self.assertIsInstance(summary.accuracy, float)
        self.assertIsInstance(summary.failure_modes, dict)
        self.assertIn("no_answer_selection", set(summary.failure_modes) | {"no_answer_selection"})

    def test_does_not_claim_official_score(self):
        summary = run_suite(SUITE_PATH)
        payload = json.dumps(summary.to_dict())
        self.assertIn('"official_score": false', payload)
        self.assertNotIn("official benchmark score", payload.lower())
        self.assertNotIn("leaderboard", payload.lower())

    def test_handles_no_answer_selection_safely(self):
        suite = load_suite(SUITE_PATH)
        item = suite["items"][0]
        result = run_item(item, suite["sample_only"], suite["official_score"])
        self.assertIn(result.failure_mode, {None, "no_answer_selection"})
        if result.selected_label is None:
            self.assertFalse(result.correct)
            self.assertEqual(result.failure_mode, "no_answer_selection")

    def test_rejects_malformed_choices(self):
        bad_suite = {
            "suite_id": "bad_suite",
            "sample_only": True,
            "official_score": False,
            "items": [
                {
                    "id": "bad_01",
                    "benchmark_family": "mmlu_gpqa_style",
                    "domain": "science",
                    "question": "Bad choices?",
                    "choices": [{"label": "AA", "text": "too long"}],
                    "answer_label": "AA",
                    "required_skill": "test",
                    "explanation_required": True,
                }
            ],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(bad_suite, tmp)
            tmp_path = tmp.name
        try:
            with self.assertRaises(ValueError):
                load_suite(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_output_includes_cognitive_legibility_fields(self):
        summary = run_suite(SUITE_PATH)
        first = summary.results[0].to_dict()
        self.assertIn("explanation", first)
        self.assertTrue("confidence" in first or "uncertainty" in first)
        self.assertIn("failure_mode", first)

    def test_extract_selected_label_supports_explicit_label(self):
        suite = load_suite(SUITE_PATH)
        item = suite["items"][0]
        label = extract_selected_label("Answer: A\nBecause it describes spread-out energy.", item.choices)
        self.assertEqual(label, "A")

    def test_build_prompt_contains_choices(self):
        suite = load_suite(SUITE_PATH)
        prompt = build_prompt(suite["items"][0])
        self.assertIn("Choices:", prompt)
        self.assertIn("A.", prompt)
        self.assertIn("Select the best answer label", prompt)

    def test_temporary_public_subset_style_suite_with_provenance_loads(self):
        public_subset = {
            "suite_id": "public_subset_eval",
            "sample_only": False,
            "internal_eval": True,
            "official_score": False,
            "dataset_name": "ExampleDataset",
            "dataset_version": "2026.1",
            "dataset_source": "already-local public subset",
            "subset_name": "mini-dev",
            "subset_size": 1,
            "source_split": "dev",
            "license_note": "public subset manually placed locally",
            "conversion_schema_version": "public_subset_schema_v1",
            "prompt_format_version": "official_mcq_prompt_v1",
            "adapter_version": "official_mcq_adapter_v0",
            "items": [
                {
                    "id": "item_1",
                    "benchmark_family": "mmlu_gpqa_style",
                    "domain": "science",
                    "question": "Which option best describes entropy?",
                    "choices": [
                        {"label": "A", "text": "Spread out energy or arrangements in a system."},
                        {"label": "B", "text": "A guarantee that order always increases."}
                    ],
                    "answer_label": "A",
                    "required_skill": "science_explanation",
                    "explanation_required": True
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(public_subset, tmp)
            tmp_path = tmp.name
        try:
            suite = load_suite(tmp_path)
            self.assertFalse(suite["sample_only"])
            self.assertTrue(suite["internal_eval"])
            self.assertEqual(suite["metadata"]["dataset_name"], "ExampleDataset")
        finally:
            os.unlink(tmp_path)

    def test_run_summary_includes_provenance_metadata(self):
        summary = run_suite(SUITE_PATH)
        self.assertIn("adapter_version", summary.metadata)
        self.assertIn("date_run", summary.run_provenance)
        self.assertIn("official_score", summary.run_provenance)
        self.assertFalse(summary.run_provenance["official_score"])

    def test_official_score_true_is_rejected(self):
        bad_suite = {
            "suite_id": "bad_suite",
            "sample_only": True,
            "official_score": True,
            "items": [],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(bad_suite, tmp)
            tmp_path = tmp.name
        try:
            with self.assertRaises(ValueError):
                load_suite(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_sample_only_false_without_internal_eval_or_provenance_is_rejected(self):
        bad_suite = {
            "suite_id": "bad_suite",
            "sample_only": False,
            "official_score": False,
            "items": [
                {
                    "id": "item_1",
                    "benchmark_family": "mmlu_gpqa_style",
                    "domain": "science",
                    "question": "Which option best describes entropy?",
                    "choices": [
                        {"label": "A", "text": "Spread out energy or arrangements in a system."},
                        {"label": "B", "text": "A guarantee that order always increases."}
                    ],
                    "answer_label": "A",
                    "required_skill": "science_explanation",
                    "explanation_required": True
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(bad_suite, tmp)
            tmp_path = tmp.name
        try:
            with self.assertRaises(ValueError):
                load_suite(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_cli_json_output_shape(self):
        result = subprocess.run(
            [
                "python3",
                "-m",
                "weslr.evals.official_mcq_adapter",
                "--suite",
                str(SUITE_PATH),
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        for key in [
            "suite_id",
            "sample_only",
            "official_score",
            "internal_eval",
            "metadata",
            "run_provenance",
            "total",
            "accuracy",
            "answered_count",
            "no_answer_count",
            "results",
        ]:
            self.assertIn(key, payload)
        self.assertFalse(payload["official_score"])
        self.assertTrue(payload["sample_only"])


if __name__ == "__main__":
    unittest.main()
