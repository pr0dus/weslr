#!/usr/bin/env python3
"""Tests for WESLR stable identity and adaptive delivery doctrine V1."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md"


def _text() -> str:
    assert DOC.exists(), f"doctrine doc missing: {DOC}"
    return DOC.read_text(encoding="utf-8")


def _lower() -> str:
    return _text().lower()


def test_doc_exists():
    assert DOC.exists()


def test_contains_stable_identity():
    text = _lower()
    assert "stable identity" in text
    assert "personality and identity continuity" in text


def test_says_weslr_remains_weslr():
    assert "WESLR remains WESLR" in _text()


def test_forbids_character_switching_as_identity_replacement():
    text = _lower()
    assert "character switching as identity replacement" in text
    assert "must not switch" in text


def test_allows_adaptive_voice_pitch_intonation_speed():
    text = _lower()
    for phrase in ("voice", "pitch", "intonation", "speaking speed"):
        assert phrase in text
    assert "delivery adaptations, not identity changes" in text


def test_allows_context_sensitive_delivery():
    text = _lower()
    assert "context-sensitive communication" in text
    for phrase in ("user role", "user expertise", "task risk", "authority boundary"):
        assert phrase in text


def test_contains_capability_guidance_posture():
    text = _lower()
    assert "capability-guidance posture" in text
    assert "staged workflow" in text
    assert "evidence gates" in text
    assert "next safe step" in text


def test_contains_yes_we_can_work_on_this_together():
    assert "Yes, we can work on this together" in _text()


def test_contains_materials_discovery_example():
    text = _lower()
    for phrase in (
        "candidate generation",
        "novelty check",
        "structural sanity",
        "stability checks",
        "comparison to known phases",
        "experimental validation boundary",
    ):
        assert phrase in text


def test_mentions_dft():
    assert "DFT" in _text()


def test_says_dft_is_computational_plausibility_not_final_proof():
    text = _lower()
    assert "dft calculator can support computational plausibility" in text
    assert "dft alone must not be treated as final proof" in text
    assert "promising under tested assumptions" in text
    assert "not “proven”" in text or 'not "proven"' in text


def test_distinguishes_simulation_evidence_from_experimental_evidence():
    text = _lower()
    assert "distinguish simulation evidence from experimental evidence" in text
    assert "simulation evidence" in text
    assert "experimental evidence" in text


def test_links_deeper_awareness_to_continuity_provenance_evidence_boundaries():
    text = _lower()
    assert "deeper awareness" in text
    assert "memory and continuity" in text
    assert "provenance" in text
    assert "evidence boundaries" in text
    assert "authority boundaries" in text


def test_forbids_fake_certainty_and_fake_scientific_proof():
    text = _lower()
    assert "fake certainty" in text
    assert "fake scientific proof" in text


def test_says_no_runtime_behavior_change():
    text = _lower()
    assert "no runtime behavior change" in text
    assert "does not implement runtime behavior" in text


def test_forbids_answer_selection_truth_soundness_official_score_claims():
    text = _lower()
    for phrase in (
        "answer selection claims",
        "truth claims",
        "soundness claims",
        "official score claims",
    ):
        assert phrase in text


if __name__ == "__main__":
    tests = [name for name in sorted(globals()) if name.startswith("test_")]
    for name in tests:
        globals()[name]()
    print("STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1_OK")
