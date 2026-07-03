from __future__ import annotations

import json

import pytest

from weslr.arc_official_public_data_adapter import build_arc_official_public_dummy_approval_manifest_v1
from weslr.arc_official_public_data_harness import build_arc_official_public_dummy_surface_report_v1, run_arc_official_public_dummy_no_data_harness_v1


FORBIDDEN_TOKENS = (
    "reference_output",
    "expected_output",
    "reference_grid",
    "latent_rule",
    "answer_descriptor",
    "raw_task_json",
)


def test_harness_runs_dummy_no_data_fixture_only() -> None:
    result = run_arc_official_public_dummy_no_data_harness_v1()
    summary = result["summary"]
    assert result["synthetic_only"] is True
    assert result["official_data_touched"] is False
    assert result["public_data_touched"] is False
    assert result["network_touched"] is False
    assert summary["task_count"] == 2
    assert summary["exact_two_output_compliance"] is True
    assert summary["official_percentage"] == 0
    assert summary["official_percentage_remains_none_zero"] is True
    assert summary["official_public_data_untouched"] is True
    assert summary["aggregate_score"] == 2
    assert all(item["task_score"] == 1 for item in result["task_results"])


def test_harness_rejects_invalid_manifest() -> None:
    manifest = build_arc_official_public_dummy_approval_manifest_v1()
    manifest["owner_approved"] = False
    with pytest.raises(ValueError):
        run_arc_official_public_dummy_no_data_harness_v1(manifest=manifest)


def test_harness_report_is_metadata_only() -> None:
    result = run_arc_official_public_dummy_no_data_harness_v1()
    report = build_arc_official_public_dummy_surface_report_v1(result=result, start_head="abc", end_head="abc")
    assert "official_public_parse_scorer_surface_dummy_ready" in report
    assert "dummy_no_data_fixture_v1" in report
    assert all(token not in report.lower() for token in FORBIDDEN_TOKENS)
    assert json.dumps(result["summary"], ensure_ascii=False).find("reference_output") == -1
