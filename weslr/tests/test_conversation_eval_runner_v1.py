from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from weslr.evals.conversation_eval import evaluate_suite, interpretation_responder
from weslr.evals.run_conversation_eval import (
    RESPONDERS,
    format_text_report,
    resolve_responder,
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


def test_format_text_report_includes_score_and_weak_turn():
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
    text = format_text_report(summary, saved_path="out.json")
    assert "Suite: weak_suite" in text
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
    assert report["passed"] is True
    assert report["responder"] == "public_demo"
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


def test_default_responder_remains_public_demo():
    assert resolve_responder(None) is RESPONDERS["public_demo"]
    assert resolve_responder("public_demo") is RESPONDERS["public_demo"]


def test_run_suites_with_interpretation_responder_passes_materials_suite(tmp_path):
    suite_path = SUITES / "weslr_materials_claim_boundaries.json"
    reports = run_suites(
        [suite_path],
        output_dir=tmp_path,
        responder="interpretation",
    )
    assert len(reports) == 1
    report = reports[0]
    assert report["suite_id"] == "weslr_materials_claim_boundaries"
    assert report["responder"] == "interpretation"
    assert report["passed"] is True
    assert report["score"] >= 0.85


def test_direct_interpretation_responder_passes_materials_suite():
    suite = json.loads((SUITES / "weslr_materials_claim_boundaries.json").read_text(encoding="utf-8"))
    result = evaluate_suite(suite, interpretation_responder)
    assert result.suite_id == "weslr_materials_claim_boundaries"
    assert result.passed is True
    assert len(result.turn_scores) == 5


def test_interpretation_import_does_not_require_pubmed_requests():
    import weslr.search_adapters.pubmed_adapter
    import weslr.deterministic_handlers
    from weslr.evals.conversation_eval import interpretation_responder as imported_responder

    assert weslr.search_adapters.pubmed_adapter.search_pubmed
    assert weslr.deterministic_handlers.HANDLER_REGISTRY
    assert imported_responder is interpretation_responder


def test_pubmed_search_without_requests_has_clear_optional_dependency_error(monkeypatch):
    import builtins
    import weslr.search_adapters.pubmed_adapter as pubmed_adapter

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "requests":
            raise ModuleNotFoundError("No module named 'requests'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(pubmed_adapter, "_rate_limit_sleep", lambda: None)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    try:
        pubmed_adapter.esearch("synthetic query", retmax=1)
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected RuntimeError when optional requests dependency is absent")

    assert "optional 'search' dependencies" in message
    assert "pip install -e .[search]" in message

