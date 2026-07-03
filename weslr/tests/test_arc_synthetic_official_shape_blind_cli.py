from __future__ import annotations

import subprocess
from pathlib import Path

from weslr.arc_synthetic_official_shape_blind_cli import OWNER_COMMAND_V1, REPORT_RELATIVE_PATH_V1


FORBIDDEN_TOKENS = (
    "family_id",
    "variant_id",
    "toy_task_type",
    "primitive",
    "reflect",
    "rotate",
    "expected_output",
    "source_task_id",
)


def test_arc_mock_blind_cli_writes_report_and_keeps_stdout_clean() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        ["./run", "arc-mock", "--blind"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    report_path = repo_root / REPORT_RELATIVE_PATH_V1
    report_text = report_path.read_text()
    stdout = completed.stdout.lower()

    assert "Verdict: blind_mock_ready_for_public_parse_scorer_design" in completed.stdout
    assert OWNER_COMMAND_V1 in report_text
    assert "blind_mock_ready_for_public_parse_scorer_design" in report_text
    assert "toy_task_type_visible_to_solver: False" in report_text
    assert "family_id_visible_to_solver: False" in report_text
    assert "variant_id_visible_to_solver: False" in report_text
    assert "semantic_task_id_visible_to_solver: False" in report_text
    assert "expected_output_visible_to_solver: False" in report_text
    assert str(REPORT_RELATIVE_PATH_V1) in str(report_path)
    assert all(token not in stdout for token in FORBIDDEN_TOKENS)
