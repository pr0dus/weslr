from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "src"):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from weslr.arc_agi2_public_local_score_checker import run_arc_agi2_public_local_score_check_no_submission_v1


if __name__ == "__main__":
    manifest_path = Path(
        os.environ.get(
            "WESLR_ARC_AGI2_PUBLIC_MANIFEST_PATH",
            ROOT / "config" / "arc_agi2_public_data_approval_manifest.local_score_check.local.json",
        )
    )
    artifact_path = Path(
        os.environ.get(
            "WESLR_ARC_AGI2_PUBLIC_CANDIDATE_ARTIFACT_PATH",
            "/data/data/com.termux/files/home/arc-agi2-public-source/solver_candidate_dry_run_v1/solver_candidates_no_scoring.json",
        )
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result = run_arc_agi2_public_local_score_check_no_submission_v1(
        manifest,
        repo_root=ROOT,
        staging_root=Path("/data/data/com.termux/files/home/weslr-arc-agi2-submission-staging"),
        artifact_path=artifact_path,
    )
    print(
        json.dumps(
            {
                "approved_phase": result["approved_phase"],
                "checksum_match": result["checksum_match"],
                "candidate_artifact_path": result["candidate_artifact_path"],
                "candidate_artifact_hash_before": result["candidate_artifact_hash_before"],
                "candidate_artifact_hash_after": result["candidate_artifact_hash_after"],
                "candidate_artifact_unchanged": result["candidate_artifact_unchanged"],
                "solution_files_parsed": result["solution_files_parsed"],
                "exactly_two_output_valid": result["exactly_two_output_valid"],
                "total_tasks_scored": result["total_tasks_scored"],
                "correct_count": result["correct_count"],
                "incorrect_count": result["incorrect_count"],
                "malformed_candidate_count": result["malformed_candidate_count"],
                "missing_candidate_count": result["missing_candidate_count"],
                "local_public_exact_match_rate_non_official": result["local_public_exact_match_rate_non_official"],
                "hash_guard_result": result["hash_guard_result"],
                "redaction_valid": result["redaction_result"]["valid"],
                "leakage_audit": result["leakage_audit"],
                "official_percentage": result["official_percentage"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
