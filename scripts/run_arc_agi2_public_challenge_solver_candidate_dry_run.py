from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "src"):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from weslr.arc_agi2_public_challenge_solver_candidate_runner import (
    DEFAULT_ARTIFACT_DIRNAME_V2,
    TARGET_ALL_PUBLIC_CHALLENGES_NO_SCORE_V1,
    TARGET_KAGGLE_TEST_SUBMISSION_SHAPE_V1,
    TARGET_PUBLIC_SCOREABLE_V1,
    run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1,
)

TARGET_CHOICES = [
    TARGET_PUBLIC_SCOREABLE_V1,
    TARGET_KAGGLE_TEST_SUBMISSION_SHAPE_V1,
    TARGET_ALL_PUBLIC_CHALLENGES_NO_SCORE_V1,
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ARC-AGI-2 public challenge solver-candidate dry run.")
    parser.add_argument("--target", choices=TARGET_CHOICES, default=TARGET_PUBLIC_SCOREABLE_V1)
    parser.add_argument(
        "--manifest-path",
        default=ROOT / "config" / "arc_agi2_public_data_approval_manifest.solver_dry_run.local.json",
    )
    parser.add_argument(
        "--artifact-root",
        default=Path("/data/data/com.termux/files/home/arc-agi2-public-source") / DEFAULT_ARTIFACT_DIRNAME_V2,
    )
    parser.add_argument(
        "--repo-root",
        default=ROOT,
    )
    parser.add_argument(
        "--staging-root",
        default=Path("/data/data/com.termux/files/home/weslr-arc-agi2-submission-staging"),
    )
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest_path).read_text(encoding="utf-8"))
    result = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
        manifest,
        repo_root=args.repo_root,
        staging_root=args.staging_root,
        artifact_root=args.artifact_root,
        target_mode=args.target,
    )
    print(
        json.dumps(
            {
                "target_mode": result["target_mode"],
                "approved_phase": result["approved_phase"],
                "checksum_match": result["checksum_match"],
                "challenge_files_used": result["challenge_files_used"],
                "solution_files_opened": result["solution_files_opened"],
                "task_count": result["task_count"],
                "test_input_count": result["test_input_count"],
                "artifact_task_key_mode": result["artifact_task_key_mode"],
                "candidate_artifact_path": result["candidate_artifact_path"],
                "artifact_validation": result["artifact_validation"],
                "sample_submission_alignment": result["sample_submission_alignment"],
                "hash_guard_result": result["hash_guard_result"],
                "redaction_valid": result["redaction_result"]["valid"],
                "leakage_audit": result["leakage_audit"],
                "official_percentage": result["official_percentage"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
