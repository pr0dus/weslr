from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "src"):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from weslr.arc_agi2_public_challenge_solver_candidate_runner import (
    collect_frozen_solver_candidate_hashes_v1,
    run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1,
)


if __name__ == "__main__":
    manifest_path = Path(
        os.environ.get(
            "WESLR_ARC_AGI2_PUBLIC_MANIFEST_PATH",
            ROOT / "config" / "arc_agi2_public_data_approval_manifest.solver_dry_run.local.json",
        )
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
        manifest,
        repo_root=ROOT,
        staging_root=Path("/data/data/com.termux/files/home/weslr-arc-agi2-submission-staging"),
        artifact_root=Path("/data/data/com.termux/files/home/arc-agi2-public-source/solver_candidate_dry_run_v1"),
    )
    print(
        json.dumps(
            {
                "approved_phase": result["approved_phase"],
                "checksum_match": result["checksum_match"],
                "challenge_files_used": result["challenge_files_used"],
                "solution_files_opened": result["solution_files_opened"],
                "task_count": result["task_count"],
                "test_input_count": result["test_input_count"],
                "candidate_artifact_path": result["candidate_artifact_path"],
                "artifact_validation": result["artifact_validation"],
                "hash_guard_result": result["hash_guard_result"],
                "redaction_valid": result["redaction_result"]["valid"],
                "leakage_audit": result["leakage_audit"],
                "official_percentage": result["official_percentage"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
