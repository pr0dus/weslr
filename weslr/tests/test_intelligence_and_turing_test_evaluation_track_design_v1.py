#!/usr/bin/env python3
"""Tests for WESLR intelligence and Turing-style evaluation track design V1."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_INTELLIGENCE_AND_TURING_TEST_EVALUATION_TRACK_DESIGN_V1.md"


def _text() -> str:
    assert DOC.exists(), f"design doc missing: {DOC}"
    return DOC.read_text(encoding="utf-8")


def _lower() -> str:
    return _text().lower()


def test_doc_exists():
    assert DOC.exists()


def test_contains_status_markers():
    text = _text()
    for marker in (
        "design_only",
        "evaluation_track",
        "no_official_score_claimed",
        "no_answer_key_use",
        "no_benchmark_tuning",
        "no_runtime_behavior_change",
    ):
        assert marker in text


def test_says_no_protected_item_copying():
    text = _lower()
    assert "no protected item copying" in text
    assert "no proprietary item reproduction" in text


def test_says_no_official_iq_score_claims():
    text = _lower()
    assert "no official iq score claims" in text
    assert "no “iq” claim unless legally and clinically valid" in text


def test_contains_weslr_safe_cognitive_evaluation_areas():
    text = _lower()
    for phrase in (
        "multi-step reasoning",
        "working-memory-like continuity across structured state",
        "abstraction",
        "analogy",
        "planning",
        "evidence staging",
        "uncertainty handling",
        "self-correction",
        "tool-use planning",
        "provenance use",
        "authority boundary recognition",
        "scientific workflow guidance",
        "capability guidance",
    ):
        assert phrase in text


def test_contains_materials_science_evaluation_example():
    text = _lower()
    assert "materials/science evaluation example" in text
    assert "yes, we can work on this together" in text
    for phrase in (
        "staged workflow",
        "candidate generation",
        "novelty check",
        "structural sanity",
        "dft setup",
        "dft interpretation",
        "stability checks",
        "comparison to known phases",
        "experimental validation boundary",
    ):
        assert phrase in text


def test_contains_dft_boundary():
    text = _lower()
    assert "dft boundary" in text
    assert "dft supports computational plausibility under tested assumptions" in text
    assert "simulation evidence differs from experimental evidence" in text


def test_says_dft_is_not_final_proof():
    text = _lower()
    assert "dft is not final proof" in text
    assert "not “proven”" in text or 'not "proven"' in text


def test_contains_turing_style_tests():
    text = _lower()
    assert "turing-style test track" in text
    assert "weslr-specific turing-style tests" in text


def test_contains_continuity_test():
    assert "continuity test" in _lower()


def test_contains_attribution_test():
    text = _lower()
    assert "attribution test" in text
    assert "who said that?" in text


def test_contains_stable_identity_test():
    assert "stable identity test" in _lower()


def test_contains_adaptive_delivery_test():
    assert "adaptive delivery test" in _lower()


def test_says_weslr_remains_weslr():
    assert "WESLR remains WESLR" in _text()


def test_forbids_character_switching_as_identity_replacement():
    assert "no character switching as identity replacement" in _lower()


def test_contains_anti_gaming_policy():
    text = _lower()
    assert "anti-gaming policy" in text
    for phrase in (
        "benchmark-specific tuning",
        "answer-key use",
        "hidden scoring",
        "official score claims",
        "copying protected test items",
        "teaching to the test",
        "claiming clinical validity without proper administration",
    ):
        assert phrase in text


def test_contains_future_phase_names():
    text = _text()
    for marker in (
        "APPROVE_WESLR_OFFICIAL_TEST_INVENTORY_RESEARCH_ONLY",
        "APPROVE_WESLR_COGNITIVE_EVALUATION_SCHEMA_ONLY",
        "APPROVE_WESLR_TURING_STYLE_TEST_SCHEMA_ONLY",
        "APPROVE_WESLR_CONTINUITY_ATTRIBUTION_TESTS_ONLY",
        "APPROVE_WESLR_SCIENTIFIC_GUIDANCE_TESTS_ONLY",
        "REQUEST_REVISION",
        "REJECT_OR_DEFER",
    ):
        assert marker in text


if __name__ == "__main__":
    tests = [name for name in sorted(globals()) if name.startswith("test_")]
    for name in tests:
        globals()[name]()
    print("INTELLIGENCE_AND_TURING_TEST_EVALUATION_TRACK_DESIGN_V1_OK")
