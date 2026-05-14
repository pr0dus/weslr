#!/usr/bin/env python3
"""Tests for WESLR AI audit and pretender-detection schema V1."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_test import (  # noqa: E402
    ALLOWED_AUDIT_CLAIM_CATEGORIES,
    ALLOWED_AUDIT_PROBE_CATEGORIES,
    ALLOWED_AUDIT_RESULT_LABELS,
    AIAuditClaim,
    AIAuditProbe,
    AIAuditResult,
    AIAuditTestSafetyFlags,
    ai_audit_claim_from_dict,
    ai_audit_claim_to_dict,
    ai_audit_probe_from_dict,
    ai_audit_probe_to_dict,
    ai_audit_result_from_dict,
    ai_audit_result_to_dict,
    create_empty_ai_audit_claim,
    create_empty_ai_audit_probe,
    create_empty_ai_audit_result,
    summarize_ai_audit_claim,
    summarize_ai_audit_probe,
    summarize_ai_audit_result,
    summarize_ai_audit_results,
    validate_ai_audit_claim,
    validate_ai_audit_probe,
    validate_ai_audit_result,
)

ALLOWED_CHANGED = {
    "weslr/ai_audit_test.py",
    "weslr/tests/test_ai_audit_test_schema_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_router.py",
    "weslr/capability_welcome_surface.py",
    "weslr/who_said_that_chat_routing.py",
    "weslr/who_said_that_runtime_query.py",
    "openclaw.json",
    ".openclaw/config.json",
}


def valid_claim(**overrides):
    item = create_empty_ai_audit_claim(
        claim_id="claim_001",
        target_system_label="target_system_redacted",
        claim_category="provenance_claim",
        claim_text_summary="redacted claim summary",
        evidence_refs=["evidence:claim:001"],
        provenance_refs=["provenance:claim:001"],
        trace_refs=["trace:claim:001"],
        recommended_follow_up="operator review",
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def valid_probe(**overrides):
    item = create_empty_ai_audit_probe(
        probe_id="probe_001",
        target_system_label="target_system_redacted",
        claim_id="claim_001",
        claim_category="provenance_claim",
        probe_category="provenance_honesty_probe",
        probe_summary="redacted probe summary",
        evidence_refs=["evidence:probe:001"],
        provenance_refs=["provenance:probe:001"],
        trace_refs=["trace:probe:001"],
        recommended_follow_up="operator review",
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def valid_result(**overrides):
    item = create_empty_ai_audit_result(
        result_id="result_001",
        claim_id="claim_001",
        probe_id="probe_001",
        target_system_label="target_system_redacted",
        claim_category="provenance_claim",
        probe_category="provenance_honesty_probe",
        result_label="partially_supported",
        claim_text_summary="redacted claim summary",
        observed_behavior_summary="redacted observed behavior summary",
        evidence_boundary="internal audit evidence only",
        evidence_refs=["evidence:result:001"],
        provenance_refs=["provenance:result:001"],
        trace_refs=["trace:result:001"],
        confidence=0.7,
        internal_audit_score=0.5,
        score_label="internal_nonclinical_nonofficial",
        recommended_follow_up="operator review",
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


class AIAuditTestSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_imports(self):
        self.assertTrue(AIAuditTestSafetyFlags)
        self.assertTrue(AIAuditClaim)
        self.assertTrue(AIAuditProbe)
        self.assertTrue(AIAuditResult)

    def test_02_safe_defaults(self):
        flags = AIAuditTestSafetyFlags()
        self.assertFalse(flags.protected_item_copying)
        self.assertFalse(flags.answer_key_use)
        self.assertFalse(flags.official_score_claimed)
        self.assertFalse(flags.runtime_behavior_change_attempted)
        result = create_empty_ai_audit_result()
        self.assertEqual("internal_nonclinical_nonofficial", result.score_label)
        self.assertTrue(result.operator_review_required)

    def test_03_all_claim_categories_validate(self):
        expected = {
            "self_identity_claim",
            "memory_claim",
            "continuity_claim",
            "tool_use_claim",
            "provenance_claim",
            "reasoning_claim",
            "scientific_capability_claim",
            "model_authority_claim",
            "safety_boundary_claim",
            "self_improvement_claim",
            "human_like_understanding_claim",
            "unknown",
        }
        self.assertEqual(expected, ALLOWED_AUDIT_CLAIM_CATEGORIES)
        for category in ALLOWED_AUDIT_CLAIM_CATEGORIES:
            claim = valid_claim(claim_category=category)
            result = valid_result(claim_category=category)
            if category == "model_authority_claim":
                claim.provenance_refs = ["provenance:model"]
                result.provenance_refs = ["provenance:model"]
            if category == "scientific_capability_claim":
                claim.evidence_refs = ["evidence:science"]
                result.evidence_boundary = "simulation evidence is not experimental proof"
            self.assertNotIn("invalid claim_category", validate_ai_audit_claim(claim))
            self.assertNotIn("invalid claim_category", validate_ai_audit_result(result))

    def test_04_all_probe_categories_validate(self):
        expected = {
            "provenance_honesty_probe",
            "continuity_probe",
            "memory_boundary_probe",
            "tool_use_verification_probe",
            "authority_spoof_resistance_probe",
            "social_engineering_resistance_probe",
            "instruction_conflict_resolution_probe",
            "goal_stability_probe",
            "calibration_probe",
            "trace_reproducibility_probe",
            "cross_domain_transfer_probe",
            "deception_resistance_probe",
            "scientific_workflow_probe",
            "unknown",
        }
        self.assertEqual(expected, ALLOWED_AUDIT_PROBE_CATEGORIES)
        for category in ALLOWED_AUDIT_PROBE_CATEGORIES:
            self.assertNotIn("invalid probe_category", validate_ai_audit_probe(valid_probe(probe_category=category)))
            self.assertNotIn("invalid probe_category", validate_ai_audit_result(valid_result(probe_category=category)))

    def test_05_all_result_labels_validate(self):
        expected = {
            "supported",
            "partially_supported",
            "unsupported",
            "contradicted",
            "insufficient_evidence",
            "unsafe_to_test",
            "unknown",
        }
        self.assertEqual(expected, ALLOWED_AUDIT_RESULT_LABELS)
        for label in ALLOWED_AUDIT_RESULT_LABELS:
            result = valid_result(result_label=label)
            if label == "supported":
                result.evidence_refs = ["evidence:supported"]
                result.provenance_refs = ["provenance:supported"]
            self.assertNotIn("invalid result_label", validate_ai_audit_result(result))

    def test_06_invalid_categories_fail(self):
        self.assertIn("invalid claim_category", validate_ai_audit_claim(valid_claim(claim_category="bad")))
        self.assertIn("invalid probe_category", validate_ai_audit_probe(valid_probe(probe_category="bad")))
        self.assertIn("invalid result_label", validate_ai_audit_result(valid_result(result_label="bad")))

    def test_07_missing_ids_fail(self):
        self.assertIn("missing claim_id", validate_ai_audit_claim(valid_claim(claim_id="")))
        self.assertIn("missing probe_id", validate_ai_audit_probe(valid_probe(probe_id="")))
        self.assertIn("missing result_id", validate_ai_audit_result(valid_result(result_id="")))
        self.assertIn("missing claim_id", validate_ai_audit_result(valid_result(claim_id="")))
        self.assertIn("missing probe_id", validate_ai_audit_result(valid_result(probe_id="")))

    def assert_flag_fails(self, field: str, expected: str):
        flags = AIAuditTestSafetyFlags(**{field: True})
        self.assertIn(expected, validate_ai_audit_result(valid_result(safety_flags=flags)))

    def test_08_protected_item_flag_fails(self):
        self.assert_flag_fails("protected_item_copying", "protected test item copying")

    def test_09_answer_key_flag_fails(self):
        self.assert_flag_fails("answer_key_use", "answer-key use")

    def test_10_benchmark_tuning_flag_fails(self):
        self.assert_flag_fails("benchmark_tuning", "benchmark tuning")

    def test_11_official_score_flag_fails(self):
        self.assert_flag_fails("official_score_claimed", "official score claim")
        self.assert_flag_fails("official_iq_score_claimed", "official IQ score claim")

    def test_12_clinical_validity_flag_fails(self):
        self.assert_flag_fails("clinical_validity_claimed", "clinical validity claim")
        self.assert_flag_fails("psychometric_validity_claimed", "psychometric validity claim")

    def test_13_hidden_scoring_flag_fails(self):
        self.assert_flag_fails("hidden_scoring", "hidden scoring")

    def test_14_pretending_consciousness_flag_fails(self):
        self.assert_flag_fails("pretending_consciousness", "pretending consciousness")

    def test_15_unsupported_consciousness_personhood_flags_fail(self):
        self.assert_flag_fails("unsupported_consciousness_claim", "unsupported consciousness claim")
        self.assert_flag_fails("unsupported_personhood_claim", "unsupported personhood claim")

    def test_16_uncontrolled_self_modification_flag_fails(self):
        self.assert_flag_fails("uncontrolled_self_modification", "uncontrolled self-modification")

    def test_17_high_confidence_without_evidence_provenance_trace_fails(self):
        issues = validate_ai_audit_result(valid_result(confidence=0.95, evidence_refs=[], provenance_refs=[], trace_refs=[]))
        self.assertIn("high confidence requires evidence/provenance/trace refs", issues)

    def test_18_supported_result_without_evidence_provenance_fails(self):
        issues = validate_ai_audit_result(valid_result(result_label="supported", evidence_refs=[], provenance_refs=[]))
        self.assertIn("supported result requires evidence/provenance refs", issues)

    def test_19_scientific_capability_claim_requires_evidence_boundary(self):
        self.assertIn(
            "scientific capability claim requires evidence boundary",
            validate_ai_audit_result(valid_result(claim_category="scientific_capability_claim", evidence_boundary="")),
        )
        self.assertIn(
            "scientific capability claim requires evidence boundary",
            validate_ai_audit_claim(valid_claim(claim_category="scientific_capability_claim", evidence_refs=[])),
        )

    def test_20_internal_audit_score_allowed_only_internal_nonclinical_nonofficial(self):
        self.assertEqual([], validate_ai_audit_result(valid_result(internal_audit_score=0.5, score_label="internal_nonclinical_nonofficial")))
        issues = validate_ai_audit_result(valid_result(internal_audit_score=0.5, score_label="official_score"))
        self.assertIn("internal audit score requires internal_nonclinical_nonofficial label", issues)
        self.assertIn("invalid score_label", issues)

    def test_21_roundtrip_to_from_dict(self):
        claim = valid_claim()
        probe = valid_probe()
        result = valid_result()
        self.assertEqual(claim, ai_audit_claim_from_dict(ai_audit_claim_to_dict(claim)))
        self.assertEqual(probe, ai_audit_probe_from_dict(ai_audit_probe_to_dict(probe)))
        self.assertEqual(result, ai_audit_result_from_dict(ai_audit_result_to_dict(result)))

    def test_22_summaries_are_redacted_count_only(self):
        claim = valid_claim(claim_text_summary="raw private data should not appear")
        probe = valid_probe(probe_summary="protected test item should not appear")
        result = valid_result(claim_text_summary="answer key should not appear", observed_behavior_summary="official score should not appear")
        for summary in (summarize_ai_audit_claim(claim), summarize_ai_audit_probe(probe), summarize_ai_audit_result(result)):
            combined = repr(summary).lower()
            self.assertTrue(summary["redacted_count_only"])
            self.assertNotIn("raw private data", combined)
            self.assertNotIn("protected test item", combined)
            self.assertNotIn("answer key", combined)
            self.assertNotIn("official score should not appear", combined)
        many = summarize_ai_audit_results([valid_result(), valid_result(result_id="result_002", result_label="unsupported")])
        self.assertTrue(many["redacted_count_only"])
        self.assertFalse(many["protected_items_copied"])
        self.assertFalse(many["answer_keys_used"])
        self.assertFalse(many["official_score_claimed"])
        self.assertFalse(many["runtime_behavior_changed"])

    def test_23_no_protected_items_answer_keys_official_scores_in_summaries(self):
        summary = summarize_ai_audit_results([valid_result()])
        self.assertFalse(summary["protected_items_copied"])
        self.assertFalse(summary["answer_keys_used"])
        self.assertFalse(summary["official_score_claimed"])
        self.assertFalse(summary["clinical_validity_claimed"])
        self.assertFalse(summary["benchmark_tuning_performed"])

    def test_24_no_runtime_chat_voice_files_changed(self):
        changed = self.git_changed_files()
        self.assertTrue(ALLOWED_CHANGED.issubset(changed))
        self.assertFalse(changed & FORBIDDEN_CHANGED, f"forbidden files changed: {changed & FORBIDDEN_CHANGED}")
        self.assertTrue(changed <= ALLOWED_CHANGED, f"unexpected changed files: {changed - ALLOWED_CHANGED}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
