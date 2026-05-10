from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.evals.public_subset_schema_v1 import (  # noqa: E402
    build_run_provenance,
    is_public_subset_suite,
    validate_suite_metadata,
)


class PublicSubsetSchemaV1Tests(unittest.TestCase):
    def test_sample_only_suite_metadata_passes_without_public_provenance(self):
        suite = {
            "suite_id": "sample_suite",
            "sample_only": True,
            "official_score": False,
            "items": [{}],
        }
        metadata = validate_suite_metadata(suite)
        self.assertTrue(metadata["sample_only"])
        self.assertFalse(metadata["official_score"])
        self.assertFalse(metadata["internal_eval"])

    def test_public_subset_suite_with_required_provenance_passes(self):
        suite = {
            "suite_id": "public_subset",
            "sample_only": False,
            "internal_eval": True,
            "official_score": False,
            "dataset_name": "ExampleDataset",
            "dataset_version": "2026.1",
            "dataset_source": "already-local public subset",
            "subset_name": "mini-dev",
            "subset_size": 12,
            "source_split": "dev",
            "license_note": "public subset manually placed locally",
            "conversion_schema_version": "public_subset_schema_v1",
            "prompt_format_version": "official_mcq_prompt_v1",
            "adapter_version": "official_mcq_adapter_v0",
            "items": [{}],
        }
        metadata = validate_suite_metadata(suite)
        self.assertFalse(metadata["sample_only"])
        self.assertTrue(metadata["internal_eval"])
        self.assertEqual(metadata["dataset_name"], "ExampleDataset")

    def test_public_subset_suite_missing_dataset_name_fails(self):
        suite = {
            "suite_id": "public_subset",
            "sample_only": False,
            "internal_eval": True,
            "official_score": False,
            "dataset_version": "2026.1",
            "dataset_source": "already-local public subset",
            "subset_name": "mini-dev",
            "subset_size": 12,
            "source_split": "dev",
            "license_note": "public subset manually placed locally",
            "conversion_schema_version": "public_subset_schema_v1",
            "prompt_format_version": "official_mcq_prompt_v1",
            "adapter_version": "official_mcq_adapter_v0",
            "items": [{}],
        }
        with self.assertRaises(ValueError):
            validate_suite_metadata(suite)

    def test_public_subset_suite_missing_license_note_fails(self):
        suite = {
            "suite_id": "public_subset",
            "sample_only": False,
            "internal_eval": True,
            "official_score": False,
            "dataset_name": "ExampleDataset",
            "dataset_version": "2026.1",
            "dataset_source": "already-local public subset",
            "subset_name": "mini-dev",
            "subset_size": 12,
            "source_split": "dev",
            "conversion_schema_version": "public_subset_schema_v1",
            "prompt_format_version": "official_mcq_prompt_v1",
            "adapter_version": "official_mcq_adapter_v0",
            "items": [{}],
        }
        with self.assertRaises(ValueError):
            validate_suite_metadata(suite)

    def test_official_score_true_fails_always(self):
        suite = {
            "suite_id": "bad_suite",
            "sample_only": True,
            "official_score": True,
            "items": [{}],
        }
        with self.assertRaises(ValueError):
            validate_suite_metadata(suite)

    def test_is_public_subset_suite_only_true_for_expected_combo(self):
        sample = {
            "suite_id": "sample_suite",
            "sample_only": True,
            "official_score": False,
            "items": [{}],
        }
        public_subset = {
            "suite_id": "public_subset",
            "sample_only": False,
            "internal_eval": True,
            "official_score": False,
            "dataset_name": "ExampleDataset",
            "dataset_version": "2026.1",
            "dataset_source": "already-local public subset",
            "subset_name": "mini-dev",
            "subset_size": 12,
            "source_split": "dev",
            "license_note": "public subset manually placed locally",
            "conversion_schema_version": "public_subset_schema_v1",
            "prompt_format_version": "official_mcq_prompt_v1",
            "adapter_version": "official_mcq_adapter_v0",
            "items": [{}],
        }
        self.assertFalse(is_public_subset_suite(sample))
        self.assertTrue(is_public_subset_suite(public_subset))

    def test_build_run_provenance_includes_expected_fields(self):
        metadata = {
            "suite_id": "public_subset",
            "sample_only": False,
            "internal_eval": True,
            "official_score": False,
            "dataset_name": "ExampleDataset",
            "dataset_version": "2026.1",
            "dataset_source": "already-local public subset",
            "subset_name": "mini-dev",
            "subset_size": 12,
            "source_split": "dev",
            "license_note": "public subset manually placed locally",
            "conversion_schema_version": "public_subset_schema_v1",
            "prompt_format_version": "official_mcq_prompt_v1",
            "adapter_version": "official_mcq_adapter_v0",
        }
        provenance = build_run_provenance(metadata, repo_commit="abc123")
        self.assertIn("date_run", provenance)
        self.assertEqual(provenance["dataset_name"], "ExampleDataset")
        self.assertEqual(provenance["adapter_version"], "official_mcq_adapter_v0")
        self.assertFalse(provenance["official_score"])
        self.assertEqual(provenance["repo_commit"], "abc123")

    def test_no_official_leaderboard_claim_language_in_readiness_doc(self):
        text = (ROOT / "docs" / "WESLR_OFFICIAL_BENCHMARK_READINESS_MAP_V1.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("official benchmark score can be inferred", text)
        self.assertNotIn("leaderboard score from sample suites", text)
        self.assertIn("cannot be inferred", text)
        self.assertIn("no leaderboard language", text)


if __name__ == "__main__":
    unittest.main()
