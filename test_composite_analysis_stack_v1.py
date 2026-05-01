"""
Tests for WESLR Composite Analysis Stack V1.

Scope: read-only analysis, no /chat integration, no Ollama, no JSONL writes.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure weslr module is importable
import sys
sys.path.insert(0, str(Path(__file__).parent))

from weslr.composite_analysis_stack import (
    classify_structure,
    compute_similarity_score,
    estimate_confidence,
    governance_boundary,
    analyze_item,
    build_composite_summary,
)


class TestClassifyStructure(unittest.TestCase):

    def test_public_signal_v1(self):
        item = {"record_type": "public_signal_v1", "message": "hello"}
        result = classify_structure(item)
        self.assertEqual(result["structural_class"], "operational_signal")
        self.assertEqual(result["source_family"], "signal")
        self.assertEqual(result["authority"], "analysis_only")

    def test_contract_observation_v1(self):
        item = {"record_type": "contract_observation_v1", "response_contract": "conversational_entry"}
        result = classify_structure(item)
        self.assertEqual(result["structural_class"], "observation_signal")
        self.assertEqual(result["source_family"], "contract")

    def test_contract_insufficiency_v1(self):
        item = {"record_type": "contract_insufficiency_v1", "pattern_type": "weak_entry_repetition"}
        result = classify_structure(item)
        self.assertEqual(result["structural_class"], "insufficiency_evidence")
        self.assertEqual(result["source_family"], "contract")

    def test_contract_proposal_review_v1(self):
        item = {"record_type": "contract_proposal_review_v1", "proposal_status": "pending_review"}
        result = classify_structure(item)
        self.assertEqual(result["structural_class"], "review_candidate")
        self.assertEqual(result["source_family"], "contract")

    def test_unknown_record_type(self):
        item = {"record_type": "unknown", "data": "test"}
        result = classify_structure(item)
        self.assertEqual(result["structural_class"], "unknown_signal")
        self.assertEqual(result["source_family"], "unknown")

    def test_missing_record_type(self):
        item = {"message": "hello"}
        result = classify_structure(item)
        self.assertEqual(result["structural_class"], "unknown_signal")
        self.assertEqual(result["authority"], "analysis_only")


class TestComputeSimilarityScore(unittest.TestCase):

    def test_same_record_type(self):
        item = {"record_type": "contract_proposal_review_v1", "response_contract": "structured_explanation"}
        ref = {"record_type": "contract_proposal_review_v1", "response_contract": "structured_explanation"}
        result = compute_similarity_score(item, ref)
        self.assertGreater(result["score"], 0.0)
        self.assertIn("record_type", result["matched_fields"])

    def test_different_record_type(self):
        item = {"record_type": "public_signal_v1", "response_contract": "conversational_entry"}
        ref = {"record_type": "contract_observation_v1", "response_contract": "conversational_entry"}
        result = compute_similarity_score(item, ref)
        self.assertIn("response_contract", result["matched_fields"])
        self.assertNotIn("record_type", result["matched_fields"])

    def test_no_reference_returns_baseline(self):
        item = {
            "record_type": "contract_insufficiency_v1",
            "pattern_type": "weak_entry_repetition",
            "response_contract": "guided_help",
        }
        result = compute_similarity_score(item, None)
        self.assertGreater(result["score"], 0.0)
        self.assertIn("record_type", result["matched_fields"])
        self.assertIn("pattern_type", result["matched_fields"])
        self.assertIn("response_contract", result["matched_fields"])

    def test_empty_item_no_reference(self):
        item = {}
        result = compute_similarity_score(item, None)
        self.assertEqual(result["score"], 0.0)


class TestEstimateConfidence(unittest.TestCase):

    def test_proposal_ready_true_raises_confidence(self):
        item = {
            "record_type": "contract_insufficiency_v1",
            "proposal_ready": True,
            "stable_across_checks": 3,
            "pattern_type": "weak_entry_repetition",
            "response_contract": "structured_explanation",
            "response_path": "system_answer",
            "source": "test",
        }
        result = estimate_confidence(item)
        # proposal_ready gives 0.25, stable>=3 gives 0.20, known type 0.20, high field completeness 0.15
        # Total 0.80 → band should be high
        self.assertIn(result["confidence_band"], ["medium", "high"])
        self.assertIn("proposal_ready_true", result["reasons"])

    def test_stable_across_checks_3_plus_raises_confidence(self):
        item = {
            "record_type": "contract_proposal_review_v1",
            "stable_across_checks": 5,
            "proposal_ready": True,
            "pattern_type": "weak_entry_repetition",
            "response_contract": "guided_help",
            "response_path": "fallback_safe",
            "proposal_status": "pending_review",
        }
        result = estimate_confidence(item)
        self.assertIn(result["confidence_band"], ["medium", "high"])

    def test_missing_record_type_lowers_confidence(self):
        item = {"message": "hello"}
        result = estimate_confidence(item)
        self.assertEqual(result["confidence_band"], "low")
        self.assertIn("missing_or_unknown_record_type", result["reasons"])

    def test_has_validation_errors_lowers_confidence(self):
        item = {
            "record_type": "public_signal_v1",
            "validation_errors": ["field_missing"],
        }
        result = estimate_confidence(item)
        self.assertIn("has_validation_errors", result["reasons"])

    def test_unknown_record_type_is_malformed(self):
        item = {"record_type": "unknown", "data": "x"}
        result = estimate_confidence(item)
        self.assertIn("malformed_record", result["reasons"])

    def test_high_field_completeness(self):
        item = {
            "record_type": "contract_observation_v1",
            "response_contract": "structured_explanation",
            "response_path": "system_answer",
            "pattern_type": "task_help_degradation",
            "turn_index": 1,
            "source": "test",
        }
        result = estimate_confidence(item)
        self.assertIn("high_field_completeness", result["reasons"])


class TestGovernanceBoundary(unittest.TestCase):

    def test_allowed_actions_include_analyze(self):
        result = governance_boundary()
        self.assertIn("analyze", result["allowed_actions"])
        self.assertIn("summarize", result["allowed_actions"])
        self.assertIn("rank", result["allowed_actions"])

    def test_forbidden_actions_include_approve(self):
        result = governance_boundary()
        self.assertIn("approve", result["forbidden_actions"])
        self.assertIn("modify_contract", result["forbidden_actions"])
        self.assertIn("write_truth", result["forbidden_actions"])
        self.assertIn("trigger_external_action", result["forbidden_actions"])
        self.assertIn("write_memory", result["forbidden_actions"])

    def test_operator_required_for_writes(self):
        result = governance_boundary()
        self.assertIn("approve_proposal", result["operator_required_for"])
        self.assertIn("write_to_any_log", result["operator_required_for"])
        self.assertIn("trigger_deployment", result["operator_required_for"])

    def test_authority_is_analysis_only(self):
        result = governance_boundary()
        self.assertEqual(result["authority"], "analysis_only")


class TestAnalyzeItem(unittest.TestCase):

    def test_returns_analysis_only_authority(self):
        item = {"record_type": "public_signal_v1", "message": "hello"}
        result = analyze_item(item)
        self.assertEqual(result["authority"], "analysis_only")
        self.assertFalse(result["automatic_change"])

    def test_contains_structure_classification(self):
        item = {"record_type": "contract_observation_v1", "response_contract": "conversational_entry"}
        result = analyze_item(item)
        self.assertIn("structure", result)
        self.assertEqual(result["structure"]["structural_class"], "observation_signal")

    def test_contains_confidence_estimation(self):
        item = {"record_type": "contract_proposal_review_v1", "proposal_ready": True}
        result = analyze_item(item)
        self.assertIn("confidence", result)
        self.assertIn("confidence_band", result["confidence"])

    def test_contains_governance_boundary(self):
        item = {"record_type": "public_signal_v1"}
        result = analyze_item(item)
        self.assertIn("governance", result)
        self.assertIn("forbidden_actions", result["governance"])

    def test_automatic_change_always_false(self):
        for record_type in ["public_signal_v1", "contract_observation_v1",
                            "contract_insufficiency_v1", "contract_proposal_review_v1"]:
            item = {"record_type": record_type}
            result = analyze_item(item)
            self.assertFalse(result["automatic_change"])


class TestBuildCompositeSummary(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory for mock JSONL files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Patch the file paths to use temp directory
        self.patches = [
            patch("weslr.composite_analysis_stack._PUBLIC_SIGNALS_FILE",
                  self.temp_path / "public_signals.jsonl"),
            patch("weslr.composite_analysis_stack._CONTRACT_OBSERVATIONS_FILE",
                  self.temp_path / "contract_observations.jsonl"),
            patch("weslr.composite_analysis_stack._CONTRACT_INSUFFICIENCY_FILE",
                  self.temp_path / "contract_insufficiency_log.jsonl"),
            patch("weslr.composite_analysis_stack._CONTRACT_PROPOSAL_REVIEW_FILE",
                  self.temp_path / "contract_proposal_review_log.jsonl"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.temp_dir.cleanup()

    def _write_jsonl(self, filename, records):
        path = self.temp_path / filename
        with open(path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def test_reads_empty_files_safely(self):
        # No files written — all sources return []
        result = build_composite_summary()
        self.assertEqual(result["authority"], "analysis_only")
        self.assertFalse(result["automatic_change"])
        self.assertEqual(result["source_counts"]["public_signals"], 0)
        self.assertEqual(result["source_counts"]["contract_observations"], 0)

    def test_reads_populated_files(self):
        self._write_jsonl("public_signals.jsonl", [
            {"record_type": "public_signal_v1", "message": "hello"},
            {"record_type": "public_signal_v1", "message": "world"},
        ])
        self._write_jsonl("contract_observations.jsonl", [
            {"record_type": "contract_observation_v1", "response_contract": "conversational_entry"},
        ])
        result = build_composite_summary()
        self.assertEqual(result["source_counts"]["public_signals"], 2)
        self.assertEqual(result["source_counts"]["contract_observations"], 1)

    def test_malformed_lines_skipped(self):
        self._write_jsonl("public_signals.jsonl", [
            {"record_type": "public_signal_v1", "message": "valid"},
            {"record_type": "public_signal_v1", "message": "also valid"},
        ])
        result = build_composite_summary()
        # Should skip the string, empty line, and continue
        self.assertEqual(result["source_counts"]["public_signals"], 2)

    def test_high_confidence_items_captured(self):
        self._write_jsonl("contract_proposal_review_log.jsonl", [
            {
                "record_type": "contract_proposal_review_v1",
                "proposal_ready": True,
                "stable_across_checks": 5,
                "pattern_type": "weak_entry_repetition",
                "proposal_status": "pending_review",
                "response_contract": "structured_explanation",
                "response_path": "system_answer",
                "attention_level": 2,
                "source": "test",
            }
        ])
        result = build_composite_summary()
        self.assertGreater(len(result["high_confidence_items"]), 0)

    def test_operator_relevant_items_captured(self):
        self._write_jsonl("contract_insufficiency_log.jsonl", [
            {
                "record_type": "contract_insufficiency_v1",
                "proposal_ready": True,
                "pattern_type": "fallback_repetition",
            }
        ])
        result = build_composite_summary()
        self.assertGreater(len(result["operator_relevant_items"]), 0)

    def test_recommended_next_step_present(self):
        result = build_composite_summary()
        self.assertIn("recommended_next_step", result)
        self.assertIsInstance(result["recommended_next_step"], str)


class TestNoExternalIntegrations(unittest.TestCase):

    def test_no_ollama_import(self):
        """Verify no Ollama formatter is imported or called in actual code."""
        import weslr.composite_analysis_stack as cas
        source = open(cas.__file__).read()
        lines = [l for l in source.split('\n') if not l.strip().startswith('#')]
        code_only = '\n'.join(lines)
        # Strip module docstring (first triple-quoted block)
        import re
        code_only = re.sub(r'^\s*""".*?"""', '', code_only, flags=re.DOTALL)
        self.assertNotIn('import ollama', code_only)
        self.assertNotIn('from ollama', code_only)
        self.assertNotIn('local_ollama_formatter', code_only)
        self.assertNotIn('format_with_ollama', code_only)

    def test_no_chat_integration(self):
        """Verify no /chat endpoint or responder is referenced in actual code."""
        import weslr.composite_analysis_stack as cas
        source = open(cas.__file__).read()
        lines = [l for l in source.split('\n') if not l.strip().startswith('#')]
        code_only = '\n'.join(lines)
        import re
        code_only = re.sub(r'^\s*""".*?"""', '', code_only, flags=re.DOTALL)
        self.assertNotIn('chat_responder', code_only)
        self.assertNotIn('handle_chat', code_only)
        self.assertNotIn('"chat_responder"', code_only)
        self.assertNotIn('"handle_chat"', code_only)

    def test_no_jsonl_write_operations(self):
        """Verify no open() calls use 'w' mode on JSONL files."""
        import weslr.composite_analysis_stack as cas
        source = open(cas.__file__).read()
        # Check no write mode on jsonl files
        lines = source.split("\n")
        for line in lines:
            if ".jsonl" in line and "open(" in line:
                self.assertNotIn("'w'", line)
                self.assertNotIn('"w"', line)


if __name__ == "__main__":
    unittest.main()