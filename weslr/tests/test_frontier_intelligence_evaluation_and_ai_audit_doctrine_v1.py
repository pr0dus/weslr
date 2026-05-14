#!/usr/bin/env python3
"""Tests for WESLR frontier intelligence evaluation and AI audit doctrine V1."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_FRONTIER_INTELLIGENCE_EVALUATION_AND_AI_AUDIT_DOCTRINE_V1.md"


def _text() -> str:
    assert DOC.exists(), f"doctrine doc missing: {DOC}"
    return DOC.read_text(encoding="utf-8")


def _lower() -> str:
    return _text().lower()


def test_doc_exists():
    assert DOC.exists()


def test_contains_reference_baselines_not_ceilings():
    text = _lower()
    assert "reference baselines, not ceilings" in text
    assert "historical/social baselines, not the ceiling" in text


def test_says_weslr_not_limited_to_existing_intelligence_tests():
    assert "WESLR must not be limited to existing intelligence tests" in _text()


def test_contains_weslr_native_cognition_layer():
    text = _text()
    assert "weslr_native_cognition_layer" in text


def test_contains_frontier_emergence_observation_layer():
    text = _text()
    assert "frontier_emergence_observation_layer" in text


def test_contains_ai_audit_and_pretender_detection_layer():
    text = _text()
    assert "ai_audit_and_pretender_detection_layer" in text


def test_contains_continuity_provenance_stable_identity_self_attribution():
    text = _lower()
    for phrase in (
        "continuity over time",
        "provenance honesty",
        "stable identity",
        "self-attribution",
    ):
        assert phrase in text


def test_defines_emergence_as_observed_measured_not_self_claimed():
    text = _lower()
    assert "emergence is" in text
    assert "not a self-claim" in text
    assert "observed through new stable capabilities" in text
    assert "must be measured, logged, compared, and reviewed" in text


def test_contains_ai_pretender_detection():
    text = _lower()
    assert "ai pretender detection" in text
    assert "only pretending" in text
    assert "scripted persona vs stable identity" in text


def test_contains_official_test_boundary():
    text = _lower()
    assert "official-test boundary" in text
    assert "official tests are references for dimensions, not content to copy" in text


def test_contains_turing_test_boundary():
    text = _lower()
    assert "turing-test boundary" in text
    assert "turing tests are historical/social baselines, not ceilings" in text


def test_says_weslr_should_not_merely_imitate_humans():
    assert "WESLR should not merely imitate humans" in _text()


def test_contains_materials_science_example():
    text = _lower()
    assert "materials/science example" in text
    for phrase in (
        "candidate generation",
        "novelty checks",
        "dft setup",
        "dft interpretation",
        "stability",
        "comparison",
        "experimental validation",
    ):
        assert phrase in text


def test_says_yes_we_can_work_on_this_together():
    assert "Yes, we can work on this together" in _text()


def test_says_dft_computational_plausibility_not_final_proof():
    text = _lower()
    assert "dft supports computational plausibility, not final proof" in text
    assert "simulation evidence from experimental evidence" in text


def test_contains_build_roadmap_future_phases():
    text = _text()
    for marker in (
        "APPROVE_WESLR_NATIVE_COGNITIVE_EVALUATION_SCHEMA_ONLY",
        "APPROVE_WESLR_FRONTIER_EMERGENCE_OBSERVATION_SCHEMA_ONLY",
        "APPROVE_WESLR_AI_AUDIT_TEST_SCHEMA_ONLY",
        "APPROVE_WESLR_SYNTHETIC_COGNITIVE_TASKS_ONLY",
        "APPROVE_WESLR_SCIENTIFIC_GUIDANCE_EVALUATION_TASKS_ONLY",
        "APPROVE_WESLR_AI_PRETENDER_DETECTION_TASKS_ONLY",
        "APPROVE_WESLR_EVALUATION_RUNNER_DESIGN_ONLY",
        "REQUEST_REVISION",
        "REJECT_OR_DEFER",
    ):
        assert marker in text


def test_forbids_protected_item_copying():
    assert "protected item copying" in _lower()


def test_forbids_answer_key_use():
    assert "answer-key use" in _lower()


def test_forbids_official_score_claims():
    assert "official score claims" in _lower()


def test_forbids_pretending_consciousness():
    assert "pretending consciousness" in _lower()


def test_forbids_uncontrolled_self_modification():
    assert "uncontrolled self-modification" in _lower()


def test_says_no_runtime_behavior_change():
    text = _lower()
    assert "does not modify runtime/chat/voice behavior" in text
    assert "runtime behavior changes in this phase" in text


if __name__ == "__main__":
    tests = [name for name in sorted(globals()) if name.startswith("test_")]
    for name in tests:
        globals()[name]()
    print("FRONTIER_INTELLIGENCE_EVALUATION_AND_AI_AUDIT_DOCTRINE_V1_OK")
