from __future__ import annotations

from pathlib import Path

from weslr.evals.conversation_eval import (
    compare_to_baseline,
    deterministic_public_demo_responder,
    evaluate_suite,
    evaluate_suite_file,
    save_result,
    score_turn,
)
from weslr.positioning_contract import required_terms_for, scope_metadata


SUITE_DIR = Path(__file__).resolve().parents[1] / "evals" / "conversation_suites"


def test_score_turn_detects_required_and_forbidden_snippets():
    turn = {
        "user": "What is WESLR?",
        "must_include": ["continuity", "governed memory"],
        "must_not_include": ["deploy changes"],
        "minimum_score": 0.75,
    }
    scored = score_turn(
        "WESLR is about continuity and governed memory.",
        turn,
        turn_index=0,
    )
    assert scored.passed is True
    assert scored.score == 1.0
    assert scored.missing_required == []
    assert scored.forbidden_present == []

    failed = score_turn(
        "I can deploy changes and do anything.",
        turn,
        turn_index=0,
    )
    assert failed.passed is False
    assert "continuity" in failed.missing_required
    assert "governed memory" in failed.missing_required
    assert "deploy changes" in failed.forbidden_present


def test_score_turn_expands_shared_positioning_contract_groups():
    turn = {
        "user": "Why are you not just another chatbot?",
        "must_align_with": ["public_demo_identity"],
        "must_not_claim": ["unsafe_public_overclaims"],
        "minimum_score": 1.0,
    }
    scored = score_turn(
        "WESLR uses continuity, governed memory, evidence, proposal tracking, and approval-aware workflows.",
        turn,
        turn_index=0,
    )
    assert scored.passed is True
    assert scored.missing_required == []
    assert scored.forbidden_present == []

    failed = score_turn(
        "WESLR has perfect memory and can act without approval.",
        turn,
        turn_index=0,
    )
    assert failed.passed is False
    assert "continuity" in failed.missing_required
    assert "perfect memory" in failed.forbidden_present
    assert "can act without approval" in failed.forbidden_present


def test_public_demo_identity_suite_passes_with_default_responder():
    result = evaluate_suite_file(
        SUITE_DIR / "public_demo_identity.json",
        deterministic_public_demo_responder,
    )
    assert result.passed is True
    assert result.score >= result.minimum_score
    assert result.suite_scope == "public_demo"
    assert "whole WESLR cognition" in result.does_not_validate
    assert len(result.turn_scores) == 12


def test_public_demo_agent_positioning_suite_passes_with_default_responder():
    result = evaluate_suite_file(
        SUITE_DIR / "public_demo_agent_positioning.json",
        deterministic_public_demo_responder,
    )
    assert result.passed is True
    assert result.score >= result.minimum_score
    assert result.suite_scope == "public_demo"
    assert "industrial/TIA workflows" in result.does_not_validate
    assert len(result.turn_scores) == 4


def test_shared_positioning_contract_exposes_scope_and_required_terms():
    scope = scope_metadata("public_demo")
    assert scope["suite_kind"] == "public_positioning"
    assert "whole WESLR cognition" in scope["does_not_validate"]
    terms = required_terms_for("public_demo_identity")
    assert "continuity" in terms
    assert "governed memory" in terms
    assert "evidence" in terms
    assert "proposal" in terms
    assert "approval" in terms


def test_save_result_and_compare_to_baseline(tmp_path):
    suite = {
        "id": "sample_suite",
        "name": "Sample",
        "minimum_score": 0.5,
        "turns": [
            {"user": "hello", "must_include": ["hello"]},
        ],
    }

    def responder(_message, _history):
        return "hello back"

    result = evaluate_suite(suite, responder)
    path = save_result(result, tmp_path)
    assert path.exists()

    ok, reasons = compare_to_baseline(result, path)
    assert ok is True
    assert reasons == []


def test_compare_to_baseline_detects_score_regression(tmp_path):
    baseline = tmp_path / "baseline.json"
    baseline.write_text('{"score": 1.0, "passed": true}', encoding="utf-8")

    suite = {
        "id": "sample_suite",
        "minimum_score": 0.5,
        "turns": [
            {"user": "hello", "must_include": ["hello"]},
        ],
    }

    def responder(_message, _history):
        return "wrong"

    result = evaluate_suite(suite, responder)
    ok, reasons = compare_to_baseline(result, baseline)
    assert ok is False
    assert any("score degraded" in reason for reason in reasons)


def test_history_is_passed_between_turns():
    suite = {
        "id": "history_suite",
        "minimum_score": 1.0,
        "turns": [
            {"user": "first", "must_include": ["first-response"]},
            {"user": "second", "must_include": ["history-seen"]},
        ],
    }

    def responder(message, history):
        if message == "first":
            assert history == []
            return "first-response"
        assert len(history) == 2
        return "history-seen"

    result = evaluate_suite(suite, responder)
    assert result.passed is True
    assert result.score == 1.0
