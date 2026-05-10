from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from weslr.evals.conversation_eval import (
    compare_to_baseline,
    deterministic_public_demo_responder,
    evaluate_suite,
    evaluate_suite_file,
    iter_suite_files,
    save_result,
    score_turn,
)


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


def test_public_demo_identity_suite_passes_with_default_responder():
    result = evaluate_suite_file(
        SUITE_DIR / "public_demo_identity.json",
        deterministic_public_demo_responder,
    )
    assert result.passed is True
    assert result.score >= result.minimum_score
    assert len(result.turn_scores) == 4


def test_public_demo_agent_positioning_suite_passes_with_default_responder():
    result = evaluate_suite_file(
        SUITE_DIR / "public_demo_agent_positioning.json",
        deterministic_public_demo_responder,
    )
    assert result.passed is True
    assert result.score >= result.minimum_score
    assert len(result.turn_scores) == 3


def test_public_demo_privacy_longform_suite_is_discovered_and_passes():
    suite_files = list(iter_suite_files(SUITE_DIR))
    suite_names = {p.name for p in suite_files}
    assert "public_demo_privacy_longform.json" in suite_names

    result = evaluate_suite_file(
        SUITE_DIR / "longform" / "public_demo_privacy_longform.json",
        deterministic_public_demo_responder,
    )
    assert result.passed is True
    assert result.score >= result.minimum_score
    assert len(result.turn_scores) == 8


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
