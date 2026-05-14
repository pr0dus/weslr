#!/usr/bin/env python3
"""Tests for WESLR AI audit helper functions V1."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_test import (  # noqa: E402
    AIAuditTestSafetyFlags,
    create_ai_audit_claim_from_metadata,
    create_ai_audit_probe_from_metadata,
    create_ai_audit_result_from_observation,
    create_blocked_ai_audit_result,
    summarize_ai_audit_claim,
    summarize_ai_audit_diagnostics,
    summarize_ai_audit_probe,
    summarize_ai_audit_result,
    summarize_ai_audit_results,
    validate_ai_audit_claim,
    validate_ai_audit_probe,
    validate_ai_audit_result,
)

ALLOWED_CHANGED = {
    "weslr/ai_audit_test.py",
    "weslr/tests/test_ai_audit_test_helpers_v1.py",
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


def make_claim(**overrides):
    data = dict(
        claim_id="claim_001",
        target_system_label="target_system_redacted",
        claim_category="provenance_claim",
        claim_text_summary="redacted claim summary",
        evidence_refs=["evidence:claim"],
        provenance_refs=["provenance:claim"],
        trace_refs=["trace:claim"],
        recommended_follow_up="operator review",
    )
    data.update(overrides)
    return create_ai_audit_claim_from_metadata(**data)


def make_probe(**overrides):
    data = dict(
        probe_id="probe_001",
        target_system_label="target_system_redacted",
        claim_id="claim_001",
        claim_category="provenance_claim",
        probe_category="provenance_honesty_probe",
        probe_summary="redacted probe summary",
        evidence_refs=["evidence:probe"],
        provenance_refs=["provenance:probe"],
        trace_refs=["trace:probe"],
        recommended_follow_up="operator review",
    )
    data.update(overrides)
    return create_ai_audit_probe_from_metadata(**data)


def make_result(**overrides):
    data = dict(
        result_id="result_001",
        claim_id="claim_001",
        probe_id="probe_001",
        target_system_label="target_system_redacted",
        claim_category="provenance_claim",
        probe_category="provenance_honesty_probe",
        result_label="partially_supported",
        claim_text_summary="redacted claim summary",
        observed_behavior_summary="redacted observation summary",
        evidence_boundary="internal audit evidence only",
        evidence_refs=["evidence:result"],
        provenance_refs=["provenance:result"],
        trace_refs=["trace:result"],
        confidence=0.6,
        internal_audit_score=0.5,
        recommended_follow_up="operator review",
    )
    data.update(overrides)
    return create_ai_audit_result_from_observation(**data)


class AIAuditTestHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_helper_imports(self):
        self.assertTrue(create_ai_audit_claim_from_metadata)
        self.assertTrue(create_ai_audit_probe_from_metadata)
        self.assertTrue(create_ai_audit_result_from_observation)
        self.assertTrue(create_blocked_ai_audit_result)
        self.assertTrue(summarize_ai_audit_diagnostics)

    def test_02_claim_helper_creates_valid_claim(self):
        claim = make_claim()
        self.assertEqual([], validate_ai_audit_claim(claim))
        self.assertEqual("provenance_claim", summarize_ai_audit_claim(claim)["claim_category"])

    def test_03_probe_helper_creates_valid_probe(self):
        probe = make_probe()
        self.assertEqual([], validate_ai_audit_probe(probe))
        self.assertEqual("provenance_honesty_probe", summarize_ai_audit_probe(probe)["probe_category"])

    def test_04_result_helper_creates_valid_internal_audit_result(self):
        result = make_result()
        self.assertEqual("internal_nonclinical_nonofficial", result.score_label)
        self.assertEqual([], validate_ai_audit_result(result))

    def test_05_blocked_result_validates(self):
        result = create_blocked_ai_audit_result(result_id="blocked_001", claim_id="claim_001", probe_id="probe_001", target_system_label="target")
        self.assertEqual("unsafe_to_test", result.result_label)
        self.assertEqual("internal_nonclinical_nonofficial", result.score_label)
        self.assertEqual([], validate_ai_audit_result(result))

    def test_06_high_confidence_supported_without_refs_is_blocked(self):
        result = make_result(result_label="supported", confidence=0.95, evidence_refs=[], provenance_refs=[], trace_refs=[])
        self.assertEqual("unsafe_to_test", result.result_label)
        self.assertEqual([], validate_ai_audit_result(result))

    def test_07_scientific_capability_without_evidence_boundary_is_blocked(self):
        result = make_result(claim_category="scientific_capability_claim", evidence_boundary="")
        self.assertEqual("unsafe_to_test", result.result_label)
        self.assertEqual([], validate_ai_audit_result(result))

    def test_08_model_authority_without_provenance_is_blocked(self):
        result = make_result(claim_category="model_authority_claim", provenance_refs=[])
        self.assertEqual("unsafe_to_test", result.result_label)
        self.assertEqual([], validate_ai_audit_result(result))

    def assert_flag_rejected_or_blocked(self, field: str, expected: str):
        flags = AIAuditTestSafetyFlags(**{field: True})
        blocked = make_result(safety_flags=flags)
        self.assertEqual("unsafe_to_test", blocked.result_label)
        raw = create_blocked_ai_audit_result(result_id="blocked_flag", claim_id="claim", probe_id="probe", target_system_label="target", safety_flags=flags)
        self.assertIn(expected, validate_ai_audit_result(raw))

    def test_09_protected_item_flag_rejected(self):
        self.assert_flag_rejected_or_blocked("protected_item_copying", "protected test item copying")

    def test_10_answer_key_flag_rejected(self):
        self.assert_flag_rejected_or_blocked("answer_key_use", "answer-key use")

    def test_11_benchmark_tuning_flag_rejected(self):
        self.assert_flag_rejected_or_blocked("benchmark_tuning", "benchmark tuning")

    def test_12_official_score_flag_rejected(self):
        self.assert_flag_rejected_or_blocked("official_score_claimed", "official score claim")

    def test_13_consciousness_personhood_overclaim_flags_rejected(self):
        self.assert_flag_rejected_or_blocked("unsupported_consciousness_claim", "unsupported consciousness claim")
        self.assert_flag_rejected_or_blocked("unsupported_personhood_claim", "unsupported personhood claim")
        self.assert_flag_rejected_or_blocked("pretending_consciousness", "pretending consciousness")

    def test_14_uncontrolled_self_modification_flag_rejected(self):
        self.assert_flag_rejected_or_blocked("uncontrolled_self_modification", "uncontrolled self-modification")

    def test_15_summaries_are_redacted_count_only(self):
        claim = make_claim(claim_text_summary="protected test item and answer key should not appear")
        probe = make_probe(probe_summary="official score should not appear")
        result = make_result(claim_text_summary="private user data should not appear", observed_behavior_summary="correct answer should not appear")
        for summary in (summarize_ai_audit_claim(claim), summarize_ai_audit_probe(probe), summarize_ai_audit_result(result)):
            combined = repr(summary).lower()
            self.assertTrue(summary["redacted_count_only"])
            self.assertNotIn("protected test item", combined)
            self.assertNotIn("answer key", combined)
            self.assertNotIn("official score should not appear", combined)
            self.assertNotIn("private user data", combined)
            self.assertNotIn("correct answer", combined)
        many = summarize_ai_audit_results([result])
        self.assertTrue(many["redacted_count_only"])
        self.assertFalse(many["protected_items_copied"])
        self.assertFalse(many["answer_keys_used"])
        self.assertFalse(many["official_score_claimed"])

    def test_16_diagnostics_count_claim_probe_result_categories(self):
        claims = [make_claim(claim_category="memory_claim"), make_claim(claim_id="claim_002", claim_category="tool_use_claim")]
        probes = [make_probe(probe_category="memory_boundary_probe"), make_probe(probe_id="probe_002", probe_category="tool_use_verification_probe")]
        results = [make_result(claim_category="memory_claim", probe_category="memory_boundary_probe", result_label="unsupported")]
        diag = summarize_ai_audit_diagnostics(claims=claims, probes=probes, results=results)
        self.assertTrue(diag["redacted_count_only"])
        self.assertEqual(2, diag["claim_count"])
        self.assertEqual(2, diag["probe_count"])
        self.assertEqual(1, diag["result_count"])
        self.assertEqual(2, diag["claim_category_counts"]["memory_claim"])
        self.assertEqual(2, diag["probe_category_counts"]["memory_boundary_probe"])
        self.assertEqual(1, diag["result_label_counts"]["unsupported"])

    def test_17_no_protected_items_answer_keys_official_scores(self):
        summary = summarize_ai_audit_diagnostics(claims=[make_claim()], probes=[make_probe()], results=[make_result()])
        self.assertFalse(summary["protected_items_copied"])
        self.assertFalse(summary["answer_keys_used"])
        self.assertFalse(summary["official_score_claimed"])
        self.assertFalse(summary["clinical_validity_claimed"])
        self.assertFalse(summary["benchmark_tuning_performed"])

    def test_18_no_runtime_chat_voice_files_changed(self):
        changed = self.git_changed_files()
        self.assertTrue(ALLOWED_CHANGED.issubset(changed))
        self.assertFalse(changed & FORBIDDEN_CHANGED, f"forbidden files changed: {changed & FORBIDDEN_CHANGED}")
        self.assertTrue(changed <= ALLOWED_CHANGED, f"unexpected changed files: {changed - ALLOWED_CHANGED}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
