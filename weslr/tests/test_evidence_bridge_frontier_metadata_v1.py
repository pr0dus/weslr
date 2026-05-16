#!/usr/bin/env python3
"""Focused tests for evidence bridge Frontier metadata adapter helpers V1."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.evidence_bridge_frontier_metadata import (  # noqa: E402
    build_frontier_evidence_bridge_alignment_v1,
    build_output_provenance_for_evidence_bridge_v1,
    render_frontier_evidence_bridge_alignment_markdown_v1,
    summarize_frontier_evidence_bridge_alignment_v1,
    to_frontier_evidence_bridge_metadata_json_safe_v1,
    validate_frontier_evidence_bridge_alignment_v1,
    validate_output_provenance_for_evidence_bridge_v1,
)


class EvidenceBridgeFrontierMetadataV1Tests(unittest.TestCase):
    def sample_evidence_metadata(self):
        return {
            "evidence_used": True,
            "authority": "external_evidence_unverified",
            "truth_status": "unverified",
            "automatic_truth_write": False,
            "source_count": 2,
            "source_urls": ["https://example.invalid/a", "https://example.invalid/b"],
            "search_attempted": True,
            "classification": {
                "record_type": "evidence_need_classification_v1",
                "evidence_needed": True,
                "need_type": "lookup_request",
                "confidence": 0.88,
                "reason": "Matched lookup_request pattern",
                "authority": "classification_only",
                "automatic_search_allowed": False,
                "message": "raw prompt should not be copied",
                "raw_source_text": "raw source should not be copied",
            },
        }

    def test_01_basic_mapping_preserves_safe_bridge_metadata(self):
        alignment = build_frontier_evidence_bridge_alignment_v1(
            self.sample_evidence_metadata(),
            superseded_fallback_or_generic_answer=True,
        )
        self.assertEqual("frontier_evidence_bridge_metadata_alignment_v1", alignment["alignment_type"])
        self.assertEqual("evidence_chat_bridge", alignment["source_bridge"])
        self.assertTrue(alignment["evidence_used"])
        self.assertEqual("external_evidence_unverified", alignment["authority"])
        self.assertEqual("unverified", alignment["truth_status"])
        self.assertFalse(alignment["automatic_truth_write"])
        self.assertEqual(2, alignment["source_count"])
        self.assertTrue(alignment["source_urls_present"])
        self.assertNotIn("source_urls", alignment)
        self.assertTrue(alignment["superseded_fallback_or_generic_answer"])
        self.assertTrue(validate_frontier_evidence_bridge_alignment_v1(alignment)["valid"])

    def test_02_safe_false_posture_is_fixed(self):
        alignment = build_frontier_evidence_bridge_alignment_v1(self.sample_evidence_metadata())
        for key in [
            "model_calls",
            "advisor_calls",
            "memory_writes",
            "truth_writes",
            "raw_text_stored",
            "safe_to_wire_runtime",
        ]:
            self.assertFalse(alignment[key], key)

    def test_03_classification_summary_is_safe_allowlist_only(self):
        alignment = build_frontier_evidence_bridge_alignment_v1(self.sample_evidence_metadata())
        summary = alignment["classification_summary"]
        self.assertTrue(summary["evidence_needed"])
        self.assertEqual("lookup_request", summary["need_type"])
        self.assertEqual(0.88, summary["confidence"])
        encoded = json.dumps(summary, sort_keys=True).lower()
        self.assertNotIn("raw prompt", encoded)
        self.assertNotIn("raw source", encoded)
        self.assertNotIn("message", summary)
        self.assertNotIn("raw_source_text", summary)

    def test_04_validation_rejects_forbidden_alignment_fields_and_flags(self):
        base = build_frontier_evidence_bridge_alignment_v1(self.sample_evidence_metadata())
        forbidden_cases = [
            ("source_urls", ["https://example.invalid/raw"]),
            ("raw_source_text", "raw source text"),
            ("safe_to_wire_runtime", True),
            ("model_calls", True),
            ("advisor_calls", True),
            ("automatic_truth_write", True),
            ("truth_writes", True),
            ("registry_write", True),
            ("official_iq_score", "claimed"),
            ("certification_claim", "claimed"),
            ("answer_key", "rejected example"),
            ("hidden_prompt", "rejected example"),
            ("protected_material", "rejected example"),
        ]
        for key, value in forbidden_cases:
            unsafe = copy.deepcopy(base)
            unsafe[key] = value
            validation = validate_frontier_evidence_bridge_alignment_v1(unsafe)
            self.assertFalse(validation["valid"], key)
            self.assertGreater(validation["violation_count"], 0, key)

    def test_05_validation_rejects_forbidden_wording_in_strings(self):
        base = build_frontier_evidence_bridge_alignment_v1(self.sample_evidence_metadata())
        for marker in [
            "official IQ claim",
            "official score claim",
            "answer key claim",
            "hidden prompt claim",
            "protected material claim",
            "runtime wiring authorized claim",
        ]:
            unsafe = copy.deepcopy(base)
            unsafe["classification_summary"]["reason"] = marker
            self.assertFalse(validate_frontier_evidence_bridge_alignment_v1(unsafe)["valid"], marker)

    def test_06_output_provenance_helper_is_metadata_only(self):
        alignment = build_frontier_evidence_bridge_alignment_v1(self.sample_evidence_metadata())
        provenance = build_output_provenance_for_evidence_bridge_v1(alignment)
        self.assertEqual("evidence_chat_bridge", provenance["generated_by"])
        self.assertEqual("unknown", provenance["authority_level"])
        self.assertEqual("unverified", provenance["truth_class"])
        self.assertEqual("user_message", provenance["trigger_type"])
        for key in [
            "llm_assisted",
            "advisor_assisted",
            "memory_write_performed",
            "queue_write_performed",
            "runtime_action_performed",
        ]:
            self.assertFalse(provenance[key], key)
        self.assertTrue(validate_output_provenance_for_evidence_bridge_v1(provenance)["valid"])

    def test_07_output_provenance_validator_rejects_assistance_writes_and_authority(self):
        provenance = build_output_provenance_for_evidence_bridge_v1(self.sample_evidence_metadata())
        for key in [
            "llm_assisted",
            "advisor_assisted",
            "memory_write_performed",
            "queue_write_performed",
            "runtime_action_performed",
        ]:
            unsafe = copy.deepcopy(provenance)
            unsafe[key] = True
            self.assertFalse(validate_output_provenance_for_evidence_bridge_v1(unsafe)["valid"], key)

        unsafe = copy.deepcopy(provenance)
        unsafe["authority_level"] = "system_fact"
        self.assertFalse(validate_output_provenance_for_evidence_bridge_v1(unsafe)["valid"])

        unsafe = copy.deepcopy(provenance)
        unsafe["registry_write"] = True
        self.assertFalse(validate_output_provenance_for_evidence_bridge_v1(unsafe)["valid"])

    def test_08_json_safe_copy_is_deep_and_isolated(self):
        original = {"nested": {"items": [1, 2, {"value": "safe"}]}}
        copied = to_frontier_evidence_bridge_metadata_json_safe_v1(original)
        copied["nested"]["items"][2]["value"] = "changed"
        self.assertEqual("safe", original["nested"]["items"][2]["value"])

    def test_09_summary_and_markdown_are_redacted_and_count_only(self):
        alignment = build_frontier_evidence_bridge_alignment_v1(self.sample_evidence_metadata())
        summary = summarize_frontier_evidence_bridge_alignment_v1(alignment)
        rendered = render_frontier_evidence_bridge_alignment_markdown_v1(alignment)
        encoded = json.dumps(summary, sort_keys=True).lower() + "\n" + rendered.lower()
        self.assertEqual(2, summary["source_count"])
        self.assertTrue(summary["source_urls_present"])
        self.assertIn("unverified", encoded)
        self.assertIn("non-authoritative", encoded)
        self.assertIn("no-write=true", encoded)
        self.assertNotIn("https://example.invalid", encoded)
        self.assertNotIn("raw source", encoded)
        self.assertNotIn("hidden prompt", encoded)
        self.assertNotIn("answer key", encoded)
        self.assertNotIn("protected material", encoded)

    def test_10_architecture_preservation_static_guardrails(self):
        module_source = (ROOT / "weslr" / "evidence_bridge_frontier_metadata.py").read_text()
        forbidden_runtime_markers = [
            "search_searxng(",
            "maybe_answer_with_evidence(",
            "run_evidence_pipeline(",
            "is_searxng_enabled(",
            "generate_chat(",
            "open(",
            ".write(",
            "mkdir(",
            "chat_responder",
        ]
        for marker in forbidden_runtime_markers:
            self.assertNotIn(marker, module_source, marker)


if __name__ == "__main__":
    unittest.main()
