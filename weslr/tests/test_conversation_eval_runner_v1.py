from __future__ import annotations

import json
from pathlib import Path

from weslr.evals.conversation_eval import evaluate_suite
from weslr.evals.run_conversation_eval import (
    format_text_report,
    result_summary,
    run_suites,
)


ROOT = Path(__file__).resolve().parents[1]
SUITES = ROOT / "evals" / "conversation_suites"


def test_result_summary_reports_weak_turns():
    suite = {
        "id": "weak_suite",
        "name": "Weak suite",
        "minimum_score": 0.8,
        "turns": [
            {"user": "hello", "must_include": ["expected"]},
        ],
    }
    result = evaluate_suite(suite, lambda _message, _history: "wrong")
    summary = result_summary(result)
    assert summary["passed"] is False
    assert summary["weak_turns"]
    assert summary["weak_turns"][0]["missing_required"] == ["expected"]


def test_result_summary_includes_scope_metadata():
    result = evaluate_suite(
        {
            "id": "scoped_suite",
            "name": "Scoped suite",
            "suite_scope": "public_demo",
            "minimum_score": 1.0,
            "turns": [{"user": "hello", "must_include": ["hello"]}],
        },
        lambda _message, _history: "hello",
    )
    summary = result_summary(result)
    assert summary["suite_scope"] == "public_demo"
    assert summary["suite_kind"] == "public_positioning"
    assert "public first impression" in summary["validates"]
    assert "whole WESLR cognition" in summary["does_not_validate"]


def test_format_text_report_includes_score_scope_and_weak_turn():
    suite = {
        "id": "weak_suite",
        "name": "Weak suite",
        "suite_scope": "public_demo",
        "minimum_score": 0.8,
        "turns": [
            {"user": "hello", "must_include": ["expected"]},
        ],
    }
    result = evaluate_suite(suite, lambda _message, _history: "wrong")
    summary = result_summary(result)
    text = format_text_report(summary, saved_path="out.json")
    assert "Suite: weak_suite" in text
    assert "Scope: public_demo" in text
    assert "Does not validate:" in text
    assert "whole WESLR cognition" in text
    assert "Score:" in text
    assert "Weak turns:" in text
    assert "missing=expected" in text
    assert "Saved: out.json" in text


def test_run_suites_saves_results(tmp_path):
    reports = run_suites(
        [SUITES / "public_demo_identity.json"],
        output_dir=tmp_path,
    )
    assert len(reports) == 1
    report = reports[0]
    assert report["suite_id"] == "public_demo_identity"
    assert report["suite_scope"] == "public_demo"
    assert "whole WESLR cognition" in report["does_not_validate"]
    assert report["passed"] is True
    saved = Path(report["saved_path"])
    assert saved.exists()
    assert saved.name == "public_demo_identity.result.json"


def test_run_suites_detects_baseline_regression(tmp_path):
    suite_path = tmp_path / "local_regression_suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "id": "local_regression_suite",
                "name": "Local regression suite",
                "minimum_score": 0.9,
                "turns": [
                    {
                        "user": "hello",
                        "must_include": ["intentionally-absent-token"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    baseline_dir = tmp_path / "baselines"
    baseline_dir.mkdir()
    (baseline_dir / "local_regression_suite.result.json").write_text(
        '{"score": 1.0, "passed": true}',
        encoding="utf-8",
    )

    reports = run_suites(
        [suite_path],
        output_dir=tmp_path / "results",
        baseline_dir=baseline_dir,
    )
    assert len(reports) == 1
    report = reports[0]
    assert report["baseline_ok"] is False
    assert report["baseline_reasons"]
