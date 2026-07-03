from __future__ import annotations

import subprocess
from pathlib import Path

from weslr.arc_synthetic_official_shape_frozen_solver_challenge import (
    OWNER_CHALLENGE_COMMAND_V1,
    REPORT_RELATIVE_PATH_V1,
    capture_solver_candidate_hash_snapshot_v1,
    run_arc_synthetic_official_shape_frozen_solver_owner_seed_challenge_v1,
)


def test_frozen_solver_owner_seed_challenge_keeps_solver_hashes_unchanged() -> None:
    before = capture_solver_candidate_hash_snapshot_v1()
    payload = run_arc_synthetic_official_shape_frozen_solver_owner_seed_challenge_v1(owner_seed=123456789, task_count=240)
    after = capture_solver_candidate_hash_snapshot_v1()

    assert before == after
    assert payload["hash_changed"] is False
    assert payload["final_verdict"] == "frozen_solver_owner_seed_challenge_ready"
    assert payload["summary"]["task_count"] == 240
    assert payload["summary"]["solver_exact_count"] == 240
    assert payload["summary"]["baseline_exact_count"] == 20
    assert payload["result"]["exact_two_output_compliance"] is True
    assert payload["result"]["blind_readiness_signal"] is True
    assert payload["owner_seed"] == 123456789
    assert payload["task_count"] == 240

    report_path = Path(payload["report_path"])
    assert report_path.exists()
    report_text = report_path.read_text()
    assert OWNER_CHALLENGE_COMMAND_V1 in report_text
    assert str(REPORT_RELATIVE_PATH_V1) in str(report_path)
    assert "frozen_solver_owner_seed_challenge_ready" in report_text
    assert "Solver/candidate files changed: False" in report_text


def test_arc_mock_blind_challenge_command_runs_offline_entrypoint() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        ["./run", "arc-mock", "--blind", "--challenge", "--tasks", "240", "--seed", "123456789"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    stdout = completed.stdout
    assert "Verdict: frozen_solver_owner_seed_challenge_ready" in stdout
    assert "Command: ./run arc-mock --blind --challenge --tasks 240 --seed <OWNER_SEED>" in stdout or "Command: ./run arc-mock --blind --challenge --tasks 240 --seed 123456789" in stdout
