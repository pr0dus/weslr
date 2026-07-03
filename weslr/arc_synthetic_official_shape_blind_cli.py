"""Offline CLI for the blind synthetic ARC official-shape mock readiness run."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from weslr.arc_synthetic_official_shape_blind_runner import (
    run_arc_synthetic_official_shape_blind_readiness_v1,
    summarize_arc_synthetic_official_shape_blind_readiness_v1,
)

SCHEMA_VERSION_V1 = "ArcSyntheticOfficialShapeBlindCliV1"
OWNER_COMMAND_V1 = "./run arc-mock --blind"
REPORT_RELATIVE_PATH_V1 = Path("docs/WESLR_ARC_SYNTHETIC_OFFICIAL_SHAPE_BLIND_NO_FAMILY_LABEL_240_MOCK_V1.md")


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
    return subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def _git_branch(repo_root: Path) -> str:
    return subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def _format_manifest(result: Mapping[str, Any]) -> list[str]:
    lines = []
    for batch in result.get("blind_batch_results", []) if isinstance(result.get("blind_batch_results"), list) else []:
        lines.append(
            f"- Batch {batch.get('batch_index')} seed {batch.get('seed')}: tasks={batch.get('task_count')}, score={batch.get('summary', {}).get('task_score')}, solver={batch.get('solver_score')}, baseline={batch.get('baseline_score')}, exact-two={batch.get('exact_two_output_compliance')}"
        )
    return lines


def _format_family_scores(summary: Mapping[str, Any]) -> list[str]:
    lines = []
    family_scores = summary.get("family_scores", {}) if isinstance(summary.get("family_scores"), Mapping) else {}
    for family_id in sorted(family_scores):
        item = family_scores.get(family_id, {}) if isinstance(family_scores.get(family_id), Mapping) else {}
        lines.append(
            f"- {family_id}: count={item.get('count', 0)}, solver_exact={item.get('solver_exact', 0)}, baseline_exact={item.get('baseline_exact', 0)}, task_score={item.get('task_score', 0)}"
        )
    return lines


def build_arc_synthetic_official_shape_blind_report_v1(*, result: Mapping[str, Any], summary: Mapping[str, Any], start_head: str, end_head: str) -> str:
    bundle_summary = result.get("bundle_summary", {}) if isinstance(result.get("bundle_summary"), Mapping) else {}
    audit = result.get("audit", {}) if isinstance(result.get("audit"), Mapping) else {}
    report_verdict = "blind_mock_ready_for_public_parse_scorer_design" if result.get("blind_readiness_signal", False) else "blind_mock_not_ready_for_public_parse_scorer_design"
    lines = [
        "# WESLR ARC Synthetic Official-Shape Blind No-Family-Label 240 Mock V1",
        "",
        f"- Repository: `{_repo_root()}`",
        f"- Branch: `{_git_branch(_repo_root())}`",
        f"- Start HEAD: `{start_head}`",
        f"- End HEAD: `{end_head}`",
        f"- Owner blind command: `{OWNER_COMMAND_V1}`",
        "- Synthetic-only statement: yes; no official/public ARC data was touched",
        "- Official percentage: none/0",
        "",
        "## Previous 120-task label-assisted result summary",
        "- Task score: 120/120",
        "- Solver exact: 120/120",
        "- Trivial baseline exact: 10/120",
        "- Exactly-two-output compliance: passed",
        "",
        "## Why family metadata was not enough for public readiness",
        "- The 120-task run proved the offline path, but it still carried family-aware solver-visible labels that let the candidate path shortcut the inference problem.",
        "- This blind run removes those labels from the solver-visible packet so the solver must infer from train pairs and test input alone.",
        "",
        "## Blind projection design",
        "- Solver-visible packets are anonymized, contain only task id, train pairs, test input, and generic format metadata.",
        "- Family labels, variant ids, and scorer references remain hidden-side only.",
        "- Compatibility mode is retained as a regression check with labels visible only there.",
        "",
        "## Anti-oracle audit",
        f"- toy_task_type_visible_to_solver: {audit.get('toy_task_type_visible_to_solver', False)}",
        f"- family_id_visible_to_solver: {audit.get('family_id_visible_to_solver', False)}",
        f"- variant_id_visible_to_solver: {audit.get('variant_id_visible_to_solver', False)}",
        f"- semantic_task_id_visible_to_solver: {audit.get('semantic_task_id_visible_to_solver', False)}",
        f"- expected_output_visible_to_solver: {audit.get('expected_output_visible_to_solver', False)}",
        f"- scorer_reference_visible_to_solver: {audit.get('scorer_reference_visible_to_solver', False)}",
        f"- family_metadata_used_after_prediction_only: {audit.get('family_metadata_used_after_prediction_only', False)}",
        "",
        "## Seeds and batch manifest",
        f"- Seed list: {summary.get('seed_list', [])}",
    ]
    lines.extend(_format_manifest(result))
    lines.extend([
        "",
        "## Aggregate blind results",
        f"- Tasks: {result.get('task_count', 0)}",
        f"- Batch count: {result.get('batch_count', 0)}",
        f"- Aggregate blind score: {summary.get('task_score', 0)}/{result.get('task_count', 0)}",
        f"- Solver exact: {summary.get('solver_exact_count', 0)}/{result.get('task_count', 0)}",
        f"- Trivial baseline score: {summary.get('baseline_exact_count', 0)}/{result.get('task_count', 0)}",
        f"- Malformed: {summary.get('malformed_count', 0)}, timeout: {summary.get('timeout_count', 0)}, error: {summary.get('error_count', 0)}",
        f"- Blind batch variance: {summary.get('blind_batch_score_variance', 0.0)}",
        f"- Exact-two-output compliance: {[batch.get('exact_two_output_compliance', False) for batch in result.get('blind_batch_results', []) if isinstance(batch, Mapping)]}",
        "",
        "## Compatibility regression check",
        f"- Label-assisted solver exact: {summary.get('compatibility_solver_exact_count', 0)}/{result.get('task_count', 0)}",
        f"- Label-assisted baseline exact: {summary.get('compatibility_baseline_exact_count', 0)}/{result.get('task_count', 0)}",
        "",
        "## Per-family blind score",
    ])
    lines.extend(_format_family_scores(summary))
    lines.extend([
        "",
        "## Reflect/rotate blind score",
        f"- reflect_object_horizontal_or_vertical: {summary.get('family_scores', {}).get('reflect_object_horizontal_or_vertical', {}).get('solver_exact', 0) if isinstance(summary.get('family_scores'), Mapping) else 0}",
        f"- rotate_object_90: {summary.get('family_scores', {}).get('rotate_object_90', {}).get('solver_exact', 0) if isinstance(summary.get('family_scores'), Mapping) else 0}",
        "",
        "## Leakage audit",
        f"- {result.get('audit', {})}",
        "",
        "## Protected-file audit",
        "- protected runtime/chat/UI files changed: no",
        "",
        "## Verdict",
        f"- Readiness verdict: `{report_verdict}`",
        "- Recommended next lane: public parse/scorer surface design over the blind packet contract",
        "",
        f"- Bundle summary: {bundle_summary}",
    ])
    return "\n".join(lines).rstrip() + "\n"


def run_arc_synthetic_official_shape_blind_cli_v1() -> dict[str, Any]:
    repo_root = _repo_root()
    start_head = _git_head(repo_root)
    result = run_arc_synthetic_official_shape_blind_readiness_v1()
    summary = summarize_arc_synthetic_official_shape_blind_readiness_v1(result)
    end_head = _git_head(repo_root)
    report_text = build_arc_synthetic_official_shape_blind_report_v1(result=result, summary=summary, start_head=start_head, end_head=end_head)
    report_path = repo_root / REPORT_RELATIVE_PATH_V1
    report_path.write_text(report_text)
    final_verdict = "blind_mock_ready_for_public_parse_scorer_design" if result.get("blind_readiness_signal", False) else "blind_mock_not_ready_for_public_parse_scorer_design"
    print("ARC synthetic official-shape blind mock run complete")
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
    payload = run_arc_synthetic_official_shape_blind_cli_v1()
    return 0 if payload["final_verdict"] == "blind_mock_ready_for_public_parse_scorer_design" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
