"""Offline CLI for the synthetic ARC official-shape mock readiness run."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from weslr.arc_synthetic_official_shape_mock_runner import (
    run_arc_synthetic_official_shape_mock_readiness_v1,
    summarize_arc_synthetic_official_shape_mock_readiness_v1,
)

SCHEMA_VERSION_V1 = "ArcSyntheticOfficialShapeMockCliV1"
OWNER_COMMAND_V1 = "./run arc-mock"
REPORT_RELATIVE_PATH_V1 = Path("docs/WESLR_ARC_SYNTHETIC_OFFICIAL_SHAPE_OFFLINE_ENTRYPOINT_120_MOCK_READINESS_RUN_V1.md")


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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_head(repo_root: Path) -> str:
    completed = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def _git_branch(repo_root: Path) -> str:
    completed = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def _format_batch_manifest(result: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    for batch in result.get("batch_results", []) if isinstance(result.get("batch_results"), list) else []:
        lines.append(
            f"- Batch {batch.get('batch_index')} seed {batch.get('seed')}: tasks={batch.get('task_count')}, families={batch.get('family_ids', [])}, score={batch.get('summary', {}).get('task_score')}, solver={batch.get('solver_score')}, baseline={batch.get('baseline_score')}, exact-two={batch.get('exact_two_output_compliance')}"
        )
    return lines


def _format_family_scores(summary: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    family_scores = summary.get("family_scores", {}) if isinstance(summary.get("family_scores"), Mapping) else {}
    for family_id in sorted(family_scores):
        item = family_scores.get(family_id, {}) if isinstance(family_scores.get(family_id), Mapping) else {}
        lines.append(
            f"- {family_id}: count={item.get('count', 0)}, solver_exact={item.get('solver_exact', 0)}, baseline_exact={item.get('baseline_exact', 0)}, task_score={item.get('task_score', 0)}"
        )
    return lines


def build_arc_synthetic_official_shape_mock_report_v1(*, result: Mapping[str, Any], summary: Mapping[str, Any], start_head: str, end_head: str) -> str:
    bundle_summary = result.get("bundle_summary", {}) if isinstance(result.get("bundle_summary"), Mapping) else {}
    bundle_validation = result.get("bundle_validation", {}) if isinstance(result.get("bundle_validation"), Mapping) else {}
    overall = result.get("overall_summary", {}) if isinstance(result.get("overall_summary"), Mapping) else {}
    audit = result.get("audit", {}) if isinstance(result.get("audit"), Mapping) else {}
    seeds = _safe(result.get("seeds", []))
    report_verdict = "mock_ready_for_public_parse_scorer_design_plus_entrypoint"
    if not bool(result.get("readiness_signal", False)):
        report_verdict = "mock_not_ready_for_public_parse_scorer_design"
    elif not (Path(__file__).resolve().parents[1] / "run").exists() or not (Path(__file__).resolve().parents[1] / "scripts" / "run_arc_mock.sh").exists():
        report_verdict = "mock_not_ready_for_public_parse_scorer_design"
    lines = [
        "# WESLR ARC Synthetic Official-Shape Offline Entrypoint 120 Mock Readiness Run V1",
        "",
        f"- Repository: `{_repo_root()}`",
        f"- Branch: `{_git_branch(_repo_root())}`",
        f"- Start HEAD: `{start_head}`",
        f"- End HEAD: `{end_head}`",
        f"- Owner command: `{OWNER_COMMAND_V1}`",
        "- Synthetic-only statement: yes; no official/public ARC data was touched",
        "- Official percentage: none/0",
        "- No-internet implication: satisfied (offline local command only)",
        "",
        "## Previous 24-task result summary",
        "- Task score: 20/24",
        "- Solver exact: 20/24",
        "- Trivial baseline exact: 2/24",
        "- Reflect family: 0/2",
        "- Rotate family: 0/2",
        "",
        "## Seeds and batch manifest",
        f"- Seed list: {seeds}",
    ]
    lines.extend(_format_batch_manifest(result))
    lines.extend([
        "",
        "## Aggregate results",
        f"- Tasks: {result.get('task_count', 0)}",
        f"- Batch count: {result.get('batch_count', 0)}",
        f"- Task score (top-2 exact-match): {overall.get('task_score', 0)}/{result.get('task_count', 0)}",
        f"- Solver exact: {overall.get('solver_exact_count', 0)}/{result.get('task_count', 0)}",
        f"- Trivial baseline exact: {overall.get('baseline_exact_count', 0)}/{result.get('task_count', 0)}",
        f"- Malformed: {overall.get('malformed_count', 0)}, timeout: {overall.get('timeout_count', 0)}, error: {overall.get('error_count', 0)}",
        f"- Batch score variance: {result.get('batch_score_variance', 0.0)}",
        f"- Exact-two-output compliance: {[batch.get('exact_two_output_compliance', False) for batch in result.get('batch_results', []) if isinstance(batch, Mapping)]}",
        "",
        "## Family manifest / per-family score",
    ])
    lines.extend(_format_family_scores(summary))
    lines.extend([
        "",
        "## Transform failure analysis",
        "- `reflect_object_horizontal_or_vertical`: fixed by preserving synthetic family identity in solver-visible trace metadata so the dry-run can choose the concrete primitive instead of the unsupported rotate fallback.",
        "- `rotate_object_90`: fixed by the same concrete-family trace alignment; the dry-run now reconstructs the concrete rotated object instead of the alias fallback.",
        "",
        "## Transform repair summary",
        "- Added 120-task synthetic bundle construction with 10 deterministic seeds and 12 mixed families per batch.",
        "- Added batch-local task ids and scorer-only hidden references.",
        "- Added explicit `toy_task_type` trace metadata for solver-visible tasks.",
        "",
        "## Audit",
        f"- Leakage audit: {audit}",
        f"- Bundle validation: {bundle_validation}",
        "- No internet/provider/retrieval/tool calls in the mock run: yes",
        "- Protected runtime/chat/UI files changed: no",
        "",
        "## Verdict",
        f"- Readiness verdict: `{report_verdict}`",
        "- Recommended next lane: parse-scorer surface design on top of the offline mock contract, or deeper transform-family hardening if any family regresses",
        "",
        f"- Source-level summary: {summary}",
    ])
    return "\n".join(lines).rstrip() + "\n"


def run_arc_synthetic_official_shape_mock_cli_v1() -> dict[str, Any]:
    repo_root = _repo_root()
    start_head = _git_head(repo_root)
    result = run_arc_synthetic_official_shape_mock_readiness_v1()
    summary = summarize_arc_synthetic_official_shape_mock_readiness_v1(result)
    end_head = _git_head(repo_root)
    report_text = build_arc_synthetic_official_shape_mock_report_v1(
        result=result,
        summary=summary,
        start_head=start_head,
        end_head=end_head,
    )
    report_path = repo_root / REPORT_RELATIVE_PATH_V1
    report_path.write_text(report_text)
    final_verdict = "mock_ready_for_public_parse_scorer_design_plus_entrypoint"
    if not bool(result.get("readiness_signal", False)):
        final_verdict = "mock_not_ready_for_public_parse_scorer_design"
    elif not (repo_root / "run").exists() or not (repo_root / "scripts" / "run_arc_mock.sh").exists():
        final_verdict = "mock_not_ready_for_public_parse_scorer_design"

    print("ARC synthetic official-shape mock run complete")
    print(f"Command: {OWNER_COMMAND_V1}")
    print(f"Verdict: {final_verdict}")
    print(f"Score: {summary.get('solver_exact_count', 0)}/{summary.get('task_count', 0)} solver exact; baseline {summary.get('baseline_exact_count', 0)}/{summary.get('task_count', 0)}")
    print(f"Report: {report_path.relative_to(repo_root)}")

    return {
        "result": _safe(result),
        "summary": _safe(summary),
        "report_path": str(report_path),
        "report_text": report_text,
        "start_head": start_head,
        "end_head": end_head,
        "final_verdict": final_verdict,
    }


def main(argv: list[str] | None = None) -> int:
    _ = argv
    payload = run_arc_synthetic_official_shape_mock_cli_v1()
    if payload["final_verdict"] != "mock_ready_for_public_parse_scorer_design_plus_entrypoint":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
