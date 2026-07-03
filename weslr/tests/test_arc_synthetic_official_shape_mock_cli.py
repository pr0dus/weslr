from __future__ import annotations

from pathlib import Path

from weslr.arc_synthetic_official_shape_mock_cli import OWNER_COMMAND_V1, REPORT_RELATIVE_PATH_V1, run_arc_synthetic_official_shape_mock_cli_v1


def test_arc_mock_cli_writes_report_and_reports_entrypoint_verdict() -> None:
    payload = run_arc_synthetic_official_shape_mock_cli_v1()
    report_path = Path(payload["report_path"])
    assert payload["final_verdict"] == "mock_ready_for_public_parse_scorer_design_plus_entrypoint"
    assert payload["summary"]["task_count"] == 120
    assert report_path.exists()
    report_text = report_path.read_text()
    assert OWNER_COMMAND_V1 in report_text
    assert "mock_ready_for_public_parse_scorer_design_plus_entrypoint" in report_text or "mock_ready_for_public_parse_scorer_design" in report_text
    assert str(REPORT_RELATIVE_PATH_V1) in payload["report_path"]
