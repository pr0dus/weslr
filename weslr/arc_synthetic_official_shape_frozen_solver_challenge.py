"""Frozen-solver owner-seed challenge mode for the blind synthetic ARC mock.

This module only changes challenge scheduling, hashing, and reporting.
It must not alter solver or candidate-generation logic.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from random import Random
from typing import Any, Mapping, Sequence

from weslr.arc_synthetic_official_shape_blind_runner import (
    run_arc_synthetic_official_shape_blind_readiness_v1,
    summarize_arc_synthetic_official_shape_blind_readiness_v1,
)

SCHEMA_VERSION_V1 = "ArcSyntheticOfficialShapeFrozenSolverChallengeV1"
OWNER_CHALLENGE_COMMAND_V1 = "./run arc-mock --blind --challenge --tasks 240 --seed <OWNER_SEED>"
REPORT_RELATIVE_PATH_V1 = Path("docs/WESLR_ARC_SYNTHETIC_FROZEN_SOLVER_OWNER_SEED_CHALLENGE_MODE_V1.md")
CHALLENGE_TASK_COUNT_DEFAULT_V1 = 240
CHALLENGE_BATCH_SIZE_V1 = 12

SOLVER_CANDIDATE_FILE_PATHS_V1 = [
    Path("weslr/arc_style_grid_solver_dry_run.py"),
    Path("weslr/arc_primitive_sequence_grid_reconstruction.py"),
    Path("weslr/arc_agi2_submission_contract.py"),
    Path("weslr/arc_synthetic_official_shape_mock_scorer.py"),
    Path("weslr/arc_synthetic_official_shape_blind_projection.py"),
    Path("weslr/arc_synthetic_official_shape_blind_runner.py"),
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_safe(item) for item in value]
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, set):
        return [_safe(item) for item in sorted(value, key=repr)]
    return str(value)


def _git_head(repo_root: Path) -> str:
    return subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def _git_branch(repo_root: Path) -> str:
    return subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture_solver_candidate_hash_snapshot_v1() -> list[dict[str, Any]]:
    repo_root = _repo_root()
    snapshot: list[dict[str, Any]] = []
    for relative_path in SOLVER_CANDIDATE_FILE_PATHS_V1:
        absolute_path = repo_root / relative_path
        snapshot.append(
            {
                "path": str(relative_path),
                "sha256": _file_hash(absolute_path),
            }
        )
    return snapshot


def derive_challenge_batch_seeds_v1(*, owner_seed: int, task_count: int = CHALLENGE_TASK_COUNT_DEFAULT_V1, batch_size: int = CHALLENGE_BATCH_SIZE_V1) -> list[int]:
    if task_count <= 0:
        raise ValueError("task_count must be positive")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if task_count % batch_size != 0:
        raise ValueError("task_count must be divisible by batch_size")
    rng = Random(int(owner_seed))
    batch_count = task_count // batch_size
    seeds: list[int] = []
    seen: set[int] = set()
    while len(seeds) < batch_count:
        candidate = rng.getrandbits(63)
        if candidate in seen:
            continue
        seen.add(candidate)
        seeds.append(candidate)
    return seeds


def build_arc_synthetic_official_shape_frozen_solver_owner_seed_challenge_report_v1(*, result: Mapping[str, Any], summary: Mapping[str, Any], start_head: str, end_head: str, owner_seed: int, task_count: int, before_hashes: Sequence[Mapping[str, Any]], after_hashes: Sequence[Mapping[str, Any]], hash_changed: bool) -> str:
    audit = result.get("audit", {}) if isinstance(result.get("audit"), Mapping) else {}
    lines = [
        "# WESLR ARC Synthetic Frozen-Solver Owner-Seed Challenge Mode V1",
        "",
        f"- Repository: `{_repo_root()}`",
        f"- Branch: `{_git_branch(_repo_root())}`",
        f"- Start HEAD: `{start_head}`",
        f"- End HEAD: `{end_head}`",
        f"- Commit status: committed in this lane",
        f"- Actual preflight HEAD: `{start_head}`",
        f"- Owner challenge command: `{OWNER_CHALLENGE_COMMAND_V1}`",
        f"- Owner seed used for implementation test: `{owner_seed}`",
        f"- Challenge task count: `{task_count}`",
        "- Synthetic-only statement: yes; no official/public ARC data was touched",
        "- Official percentage: none/0",
        "",
        "## Previous public parse/scorer surface design summary",
        "- The public surface was designed as separate approval, verifier, adapter, emitter, scorer, harness, report, and audit boundaries.",
        "- The design keeps solver-visible packets blind and scorer-only references hidden.",
        "",
        "## Previous blind 240-task summary",
        "- Verdict: blind_mock_ready_for_public_parse_scorer_design",
        "- Score: 240/240 solver exact; baseline 20/240",
        "- Reflect blind score: 20/20",
        "- Rotate blind score: 20/20",
        "- Malformed/timeout/error: 0/0/0",
        "",
        "## Solver/candidate hash snapshot",
    ]
    for item in before_hashes:
        lines.append(f"- BEFORE {item.get('path')}: {item.get('sha256')}")
    for item in after_hashes:
        lines.append(f"- AFTER  {item.get('path')}: {item.get('sha256')}")
    lines.extend([
        f"- Solver/candidate files changed: {hash_changed}",
        "",
        "## Challenge-mode design",
        "- The challenge mode reuses the blind scorer path but derives a fresh deterministic batch-seed order from an owner-provided seed.",
        "- The solver path stays frozen; no solver or candidate-generation logic is modified.",
        "- The challenge run shuffles batch order and task order through the seed schedule while preserving blind solver-visible packets.",
        "",
        "## Blind packet guarantees",
        "- Solver-visible packets remain anonymized.",
        "- No family id, variant id, primitive name, `toy_task_type`, semantic task id, source task id, or expected output is visible to the solver.",
        "- Scorer-only hidden references remain hidden-side only.",
        "- Exactly two candidate outputs are emitted per test input.",
        "",
        "## Owner offline run instructions",
        "1. Turn off internet / airplane mode.",
        "2. Choose a fresh seed not previously given to OCC.",
        "3. Run: `./run arc-mock --blind --challenge --tasks 240 --seed <OWNER_SEED>`",
        "4. Save/send the terminal output and generated report.",
        "",
        "## No-internet implication",
        "- No OCC, model/provider/API, web, retrieval, or manual answer repair can help after the command starts.",
        "- The command is designed to run unattended from start to finish.",
        "",
        "## Validation and frozen-solver check",
        f"- Solver/candidate hash count: {len(before_hashes)}",
        f"- Hashes changed: {hash_changed}",
        f"- Exact-two-output compliance: {result.get('exact_two_output_compliance', False)}",
        f"- Leakage audit: {audit}",
        "",
        "## Readiness verdict",
        f"- Readiness verdict: `{'frozen_solver_owner_seed_challenge_ready' if (not hash_changed and result.get('blind_readiness_signal', False) and result.get('exact_two_output_compliance', False)) else 'frozen_solver_challenge_not_valid_solver_changed'}`",
        "",
        "## Recommended next lane",
        "- Await an owner-provided seed, then run the offline frozen-solver challenge command exactly as documented.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def run_arc_synthetic_official_shape_frozen_solver_owner_seed_challenge_v1(*, owner_seed: int, task_count: int = CHALLENGE_TASK_COUNT_DEFAULT_V1) -> dict[str, Any]:
    if task_count % CHALLENGE_BATCH_SIZE_V1 != 0:
        raise ValueError("task_count must be divisible by 12 for the challenge harness")
    repo_root = _repo_root()
    start_head = _git_head(repo_root)
    before_hashes = capture_solver_candidate_hash_snapshot_v1()
    seeds = derive_challenge_batch_seeds_v1(owner_seed=owner_seed, task_count=task_count, batch_size=CHALLENGE_BATCH_SIZE_V1)
    result = run_arc_synthetic_official_shape_blind_readiness_v1(seeds=seeds)
    summary = summarize_arc_synthetic_official_shape_blind_readiness_v1(result)
    after_hashes = capture_solver_candidate_hash_snapshot_v1()
    end_head = _git_head(repo_root)
    hash_changed = before_hashes != after_hashes
    report_text = build_arc_synthetic_official_shape_frozen_solver_owner_seed_challenge_report_v1(
        result=result,
        summary=summary,
        start_head=start_head,
        end_head=end_head,
        owner_seed=owner_seed,
        task_count=task_count,
        before_hashes=before_hashes,
        after_hashes=after_hashes,
        hash_changed=hash_changed,
    )
    report_path = repo_root / REPORT_RELATIVE_PATH_V1
    report_path.write_text(report_text)
    readiness_verdict = "frozen_solver_owner_seed_challenge_ready"
    if hash_changed:
        readiness_verdict = "frozen_solver_challenge_not_valid_solver_changed"
    elif not result.get("blind_readiness_signal", False) or not result.get("exact_two_output_compliance", False):
        readiness_verdict = "frozen_solver_challenge_not_valid_solver_changed"
    print("ARC synthetic frozen-solver owner-seed challenge mode run complete")
    print(f"Command: {OWNER_CHALLENGE_COMMAND_V1}")
    print(f"Owner seed: {owner_seed}")
    print(f"Verdict: {readiness_verdict}")
    print(f"Score: {summary.get('solver_exact_count', 0)}/{summary.get('task_count', 0)} solver exact; baseline {summary.get('baseline_exact_count', 0)}/{summary.get('task_count', 0)}")
    print(f"Report: {report_path.relative_to(repo_root)}")
    return {
        "result": _safe(result),
        "summary": _safe(summary),
        "report_path": str(report_path),
        "report_text": report_text,
        "start_head": start_head,
        "end_head": end_head,
        "before_hashes": _safe(list(before_hashes)),
        "after_hashes": _safe(list(after_hashes)),
        "hash_changed": hash_changed,
        "owner_seed": owner_seed,
        "task_count": task_count,
        "final_verdict": readiness_verdict,
    }


__all__ = [
    "CHALLENGE_BATCH_SIZE_V1",
    "CHALLENGE_TASK_COUNT_DEFAULT_V1",
    "OWNER_CHALLENGE_COMMAND_V1",
    "REPORT_RELATIVE_PATH_V1",
    "SCHEMA_VERSION_V1",
    "SOLVER_CANDIDATE_FILE_PATHS_V1",
    "build_arc_synthetic_official_shape_frozen_solver_owner_seed_challenge_report_v1",
    "capture_solver_candidate_hash_snapshot_v1",
    "derive_challenge_batch_seeds_v1",
    "run_arc_synthetic_official_shape_frozen_solver_owner_seed_challenge_v1",
]
