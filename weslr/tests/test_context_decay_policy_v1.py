"""
WESLR Context Decay Policy V1 — Tests

Run:
    python3 weslr/tests/test_context_decay_policy_v1.py

Verdict label: WESLR_CONTEXT_DECAY_POLICY_V1_DEFINED
"""

import unittest
from weslr.context_decay_policy import (
    classify_context_decay,
    ContextDecayResult,
)


class TestContextDecayPolicy(unittest.TestCase):

    # ------------------------------------------------------------------------
    # Fresh / aging / stale / archival classification
    # ------------------------------------------------------------------------
    def test_fresh_under_7_days(self):
        result = classify_context_decay(last_seen_days=0, access_count=0, source_type="other")
        self.assertEqual(result.status, "fresh")

    def test_fresh_at_7_days(self):
        result = classify_context_decay(last_seen_days=7, access_count=0, source_type="other")
        self.assertEqual(result.status, "fresh")

    def test_aging_8_days(self):
        result = classify_context_decay(last_seen_days=8, access_count=0, source_type="other")
        self.assertEqual(result.status, "aging")

    def test_aging_at_30_days(self):
        result = classify_context_decay(last_seen_days=30, access_count=0, source_type="other")
        self.assertEqual(result.status, "aging")

    def test_stale_31_days(self):
        result = classify_context_decay(last_seen_days=31, access_count=0, source_type="other")
        self.assertEqual(result.status, "stale")

    def test_stale_at_90_days(self):
        result = classify_context_decay(last_seen_days=90, access_count=0, source_type="other")
        self.assertEqual(result.status, "stale")

    def test_archival_91_days(self):
        result = classify_context_decay(last_seen_days=91, access_count=0, source_type="other")
        self.assertEqual(result.status, "archival")

    def test_archival_365_days(self):
        result = classify_context_decay(last_seen_days=365, access_count=0, source_type="other")
        self.assertEqual(result.status, "archival")

    # ------------------------------------------------------------------------
    # Access count reduces effective age
    # ------------------------------------------------------------------------
    def test_access_count_reduces_score(self):
        """High access count reduces decay score."""
        r_lo = classify_context_decay(last_seen_days=5, access_count=0, source_type="other")
        r_hi = classify_context_decay(last_seen_days=5, access_count=5, source_type="other")
        self.assertLess(r_hi.decay_score, r_lo.decay_score)

    def test_no_access_count_no_reduction(self):
        """0 access → no reduction"""
        result = classify_context_decay(last_seen_days=70, access_count=0, source_type="other")
        self.assertEqual(result.status, "stale")

    def test_low_access_count_no_reduction(self):
        """access=4 (<5) → no reduction"""
        result = classify_context_decay(last_seen_days=70, access_count=4, source_type="other")
        self.assertEqual(result.status, "stale")

    def test_high_access_reduces_archival_score(self):
        """High access at 200 days: status moves stale, score drops vs no access."""
        r_lo = classify_context_decay(last_seen_days=200, access_count=0, source_type="evidence")
        r_hi = classify_context_decay(last_seen_days=200, access_count=5, source_type="evidence")
        # Score with high access must be lower
        self.assertLess(r_hi.decay_score, r_lo.decay_score)
        # Without access: 200 days → archival (score = 1.0 capped)
        self.assertEqual(r_lo.status, "archival")
        self.assertEqual(r_lo.decay_score, 1.0)
        # With access: 200-120=80 → stale (score < 1.0)
        self.assertEqual(r_hi.status, "stale")
        self.assertLess(r_hi.decay_score, 1.0)

    # ------------------------------------------------------------------------
    # Source type constraints
    # ------------------------------------------------------------------------
    def test_governance_never_archive_candidate(self):
        """governance source → never archive_candidate"""
        result = classify_context_decay(last_seen_days=365, access_count=0, source_type="governance")
        self.assertNotEqual(result.recommended_action, "archive_candidate")

    def test_proposal_never_archive_candidate(self):
        """proposal source → never archive_candidate"""
        result = classify_context_decay(last_seen_days=365, access_count=0, source_type="proposal")
        self.assertNotEqual(result.recommended_action, "archive_candidate")

    def test_evidence_can_be_archive_candidate(self):
        """evidence at 120 days → archive_candidate"""
        result = classify_context_decay(last_seen_days=120, access_count=0, source_type="evidence")
        self.assertEqual(result.recommended_action, "archive_candidate")

    def test_signal_can_be_archive_candidate(self):
        """signal at 120 days → archive_candidate"""
        result = classify_context_decay(last_seen_days=120, access_count=0, source_type="signal")
        self.assertEqual(result.recommended_action, "archive_candidate")

    # ------------------------------------------------------------------------
    # Public mode behavior
    # ------------------------------------------------------------------------
    def test_public_mode_suppresses_archive_candidate(self):
        """public_demo_readonly → deprioritize, never archive_candidate"""
        result = classify_context_decay(
            last_seen_days=120, access_count=0,
            source_type="evidence", mode="public_demo_readonly"
        )
        self.assertEqual(result.recommended_action, "deprioritize")

    def test_public_mode_returns_classification(self):
        """public mode still returns status"""
        result = classify_context_decay(
            last_seen_days=5, access_count=0,
            source_type="other", mode="public_demo_readonly"
        )
        self.assertEqual(result.status, "fresh")

    def test_public_mode_stale_deprioritize(self):
        """public mode stale → deprioritize"""
        result = classify_context_decay(
            last_seen_days=60, access_count=0,
            source_type="memory", mode="public_demo_readonly"
        )
        self.assertEqual(result.recommended_action, "deprioritize")

    def test_public_mode_archival_deprioritize(self):
        """public mode archival → deprioritize (never archive_candidate)"""
        result = classify_context_decay(
            last_seen_days=365, access_count=0,
            source_type="other", mode="public_demo_readonly"
        )
        self.assertEqual(result.recommended_action, "deprioritize")

    # ------------------------------------------------------------------------
    # Destructive action — ALWAYS False (core invariant)
    # ------------------------------------------------------------------------
    def test_destructive_action_allowed_always_false_fresh(self):
        for stype in ["governance", "proposal", "evidence", "signal", "other"]:
            result = classify_context_decay(last_seen_days=0, access_count=0, source_type=stype)
            self.assertFalse(result.destructive_action_allowed)

    def test_destructive_action_allowed_always_false_archival(self):
        for stype in ["governance", "proposal", "evidence", "signal", "other"]:
            result = classify_context_decay(last_seen_days=365, access_count=0, source_type=stype)
            self.assertFalse(result.destructive_action_allowed)

    def test_destructive_action_allowed_never_true(self):
        """Even when archive_candidate is recommended"""
        result = classify_context_decay(last_seen_days=365, access_count=0, source_type="evidence")
        self.assertFalse(result.destructive_action_allowed)
        self.assertEqual(result.recommended_action, "archive_candidate")

    # ------------------------------------------------------------------------
    # Decay score bounds
    # ------------------------------------------------------------------------
    def test_decay_score_bounded(self):
        for days in [0, 7, 30, 90, 180, 365]:
            result = classify_context_decay(last_seen_days=days, access_count=0, source_type="other")
            self.assertGreaterEqual(result.decay_score, 0.0)
            self.assertLessEqual(result.decay_score, 1.0)

    def test_decay_score_increases_with_age(self):
        """Score at 90 days > score at 7 days"""
        r7 = classify_context_decay(last_seen_days=7, access_count=0, source_type="other")
        r90 = classify_context_decay(last_seen_days=90, access_count=0, source_type="other")
        self.assertGreater(r90.decay_score, r7.decay_score)

    # ------------------------------------------------------------------------
    # Recommended actions
    # ------------------------------------------------------------------------
    def test_fresh_recommends_keep(self):
        result = classify_context_decay(last_seen_days=2, access_count=0, source_type="other")
        self.assertEqual(result.recommended_action, "keep")

    def test_aging_recommends_deprioritize(self):
        result = classify_context_decay(last_seen_days=20, access_count=0, source_type="other")
        self.assertEqual(result.recommended_action, "deprioritize")

    def test_stale_recommends_deprioritize(self):
        result = classify_context_decay(last_seen_days=60, access_count=0, source_type="other")
        self.assertEqual(result.recommended_action, "deprioritize")

    def test_archival_governance_deprioritize(self):
        """Archival governance → deprioritize (never archive_candidate)"""
        result = classify_context_decay(last_seen_days=365, access_count=0, source_type="governance")
        self.assertEqual(result.recommended_action, "deprioritize")

    # ------------------------------------------------------------------------
    # Graceful handling of bad inputs
    # ------------------------------------------------------------------------
    def test_none_last_seen_days(self):
        result = classify_context_decay(last_seen_days=None, access_count=0, source_type="other")
        self.assertEqual(result.status, "fresh")

    def test_negative_last_seen_days(self):
        result = classify_context_decay(last_seen_days=-10, access_count=0, source_type="other")
        self.assertEqual(result.status, "fresh")

    def test_none_access_count(self):
        result = classify_context_decay(last_seen_days=60, access_count=None, source_type="other")
        self.assertEqual(result.status, "stale")

    def test_unknown_source_type_archives(self):
        """Unknown source type → treated as non-protected"""
        result = classify_context_decay(last_seen_days=365, access_count=0, source_type="unknown_type")
        self.assertEqual(result.recommended_action, "archive_candidate")

    # ------------------------------------------------------------------------
    # Result immutability
    # ------------------------------------------------------------------------
    def test_result_is_frozen(self):
        result = classify_context_decay(last_seen_days=30, access_count=0, source_type="other")
        with self.assertRaises(Exception):
            result.status = "fresh"


if __name__ == "__main__":
    print("=" * 60)
    print("WESLR_CONTEXT_DECAY_POLICY_V1_DEFINED")
    print("=" * 60)
    unittest.main(verbosity=2)
