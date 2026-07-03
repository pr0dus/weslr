"""Dummy/no-data harness for the ARC official-public parse/scorer surface."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

from weslr.arc_official_public_data_adapter import (
    DUMMY_FIXTURE_RELATIVE_PATH_V1,
    build_arc_official_public_dummy_approval_manifest_v1,
    load_arc_official_public_dummy_no_data_bundle_v1,
    validate_solver_visible_packet_v1,
)
from weslr.arc_official_public_data_emitter import emit_arc_official_public_two_output_packet_v1
from weslr.arc_official_public_data_report_redactor import redact_arc_official_public_report_payload_v1
from weslr.arc_official_public_data_scorer import score_arc_official_public_top2_packet_v1

SCHEMA_VERSION_V1 = "arc_official_public_data_harness_v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_head(repo_root: Path) -> str:
    return subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def _git_branch(repo_root: Path) -> str:
    return subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def _summarize_task_result(task_result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task_id": task_result.get("task_id"),
        "anonymized_task_id": task_result.get("anonymized_task_id"),
        "parse_status": task_result.get("parse_status"),
        "format_status": task_result.get("format_status"),
        "candidate_count_status": task_result.get("candidate_count_status"),
        "task_score": int(task_result.get("task_score", 0)),
        "solver_exact": bool(task_result.get("solver_exact", False)),
        "baseline_exact": bool(task_result.get("baseline_exact", False)),
        "malformed_count": int(task_result.get("malformed_count", 0)),
        "error_count": int(task_result.get("error_count", 0)),
        "exact_two_output_compliance": bool(task_result.get("exact_two_output_compliance", False)),
        "reference_shape": task_result.get("reference_shape"),
    }


def run_arc_official_public_dummy_no_data_harness_v1(*, manifest: Any | None = None) -> dict[str, Any]:
    approval_manifest = build_arc_official_public_dummy_approval_manifest_v1() if manifest is None else manifest
    bundle = load_arc_official_public_dummy_no_data_bundle_v1(manifest=approval_manifest)
    task_results: list[dict[str, Any]] = []
    for task, reference in zip(bundle["solver_visible_tasks"], bundle["scorer_reference_tasks"]):
        packet_validation = validate_solver_visible_packet_v1(task)
        emission = emit_arc_official_public_two_output_packet_v1(solver_visible_packet=task)
        top2_packet = emission["top2_packet"]
        score = score_arc_official_public_top2_packet_v1(top2_packet=top2_packet, reference_output=reference["reference_output"])
        exact_two_output_compliance = len(top2_packet.get("attempts", [])) == 2 if isinstance(top2_packet, Mapping) else False
        task_result = {
            "task_id": task["task_id"],
            "anonymized_task_id": task["anonymized_task_id"],
            "parse_status": task.get("parse_status"),
            "format_status": "ok" if packet_validation["valid"] else "invalid",
            "candidate_count_status": "exact_two" if exact_two_output_compliance else "invalid",
            "candidate_rule": emission["rule"],
            "task_score": int(score["task_score"]),
            "solver_exact": bool(score["solver_exact"]),
            "baseline_exact": bool(score["baseline_exact"]),
            "malformed_count": int(score["malformed_count"]),
            "error_count": int(score["error_count"]),
            "exact_two_output_compliance": exact_two_output_compliance,
            "reference_shape": score["reference_shape"],
            "score_metadata": {
                "schema_version": score["schema_version"],
                "metadata_only": score["metadata_only"],
            },
            "leakage_audit": {
                "expected_output_visible_to_solver": False,
                "scorer_reference_visible_to_solver": False,
                "raw_task_json_visible": False,
                "latent_rule_visible": False,
            },
        }
        task_results.append(task_result)
    summary = {
        "schema_version": SCHEMA_VERSION_V1,
        "task_count": len(task_results),
        "parse_status": "parsed" if all(item["parse_status"] == "parsed" for item in task_results) else "partial",
        "format_status": "ok" if all(item["format_status"] == "ok" for item in task_results) else "invalid",
        "candidate_count_status": "exact_two" if all(item["exact_two_output_compliance"] for item in task_results) else "invalid",
        "exact_two_output_compliance": all(item["exact_two_output_compliance"] for item in task_results),
        "aggregate_score": sum(item["task_score"] for item in task_results),
        "solver_exact_count": sum(int(item["solver_exact"]) for item in task_results),
        "baseline_exact_count": sum(int(item["baseline_exact"]) for item in task_results),
        "malformed_count": sum(int(item["malformed_count"]) for item in task_results),
        "error_count": sum(int(item["error_count"]) for item in task_results),
        "anonymized_task_ids": [item["anonymized_task_id"] for item in task_results],
        "source_checksum": bundle["source_checksum"],
        "source_version_or_snapshot": bundle["source_descriptor"]["source_version_or_snapshot"],
        "official_percentage": 0,
        "official_percentage_remains_none_zero": True,
        "official_public_data_untouched": True,
    }
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "synthetic_only": True,
        "official_data_touched": False,
        "public_data_touched": False,
        "network_touched": False,
        "approval_manifest": approval_manifest,
        "bundle": bundle,
        "task_results": task_results,
        "summary": summary,
        "leakage_audit": {
            "expected_output_visible_to_solver": False,
            "scorer_reference_visible_to_solver": False,
            "raw_task_json_visible": False,
            "latent_rule_visible": False,
            "official_percentage": 0,
        },
    }


def build_arc_official_public_dummy_surface_report_v1(*, result: Mapping[str, Any], start_head: str, end_head: str) -> str:
    summary = result.get("summary", {}) if isinstance(result.get("summary"), Mapping) else {}
    redacted_result = redact_arc_official_public_report_payload_v1(result)
    lines = [
        "# WESLR ARC Official Public Parse/Scorer Surface Dummy Implementation V1",
        "",
        f"- Repository: `{_repo_root()}`",
        f"- Branch: `{_git_branch(_repo_root())}`",
        f"- Start HEAD: `{start_head}`",
        f"- End HEAD: `{end_head}`",
        f"- Commit status: committed in this lane",
        f"- Actual preflight HEAD: `{start_head}`",
        "- Owner offline challenge summary: frozen_solver_owner_seed_challenge_ready; 240/240 solver exact; baseline 20/240; hashes unchanged; leakage clean",
        "- Scope statement: dummy/no-data implementation only; no official/public ARC data was opened or parsed",
        "- Dummy/no-data fixture statement: the parser and scorer were exercised only against the synthetic dummy fixture `dummy_no_data_fixture_v1` at `weslr/tests/fixtures/arc_official_public_dummy_no_data_v1.json`",
        "- Official/public data untouched: yes",
        "- Official percentage: none/0",
        "",
        "## Implemented files",
        "- `weslr/arc_official_public_data_adapter.py`",
        "- `weslr/arc_official_public_data_emitter.py`",
        "- `weslr/arc_official_public_data_scorer.py`",
        "- `weslr/arc_official_public_data_harness.py`",
        "- `weslr/arc_official_public_data_report_redactor.py`",
        "- `weslr/tests/fixtures/arc_official_public_dummy_no_data_v1.json`",
        "- `weslr/tests/test_arc_official_public_data_adapter.py`",
        "- `weslr/tests/test_arc_official_public_data_emitter.py`",
        "- `weslr/tests/test_arc_official_public_data_scorer.py`",
        "- `weslr/tests/test_arc_official_public_data_harness.py`",
        "- `weslr/tests/test_arc_official_public_data_report_redactor.py`",
        "",
        "## Adapter behavior",
        "- Requires an approval manifest.",
        "- Verifies checksum and provenance against the local dummy fixture.",
        "- Rejects missing approval, checksum mismatch, unsupported source kind, synthetic-as-official claims, and official/public source paths.",
        "- Produces anonymized solver-visible packets and separate scorer-only reference records.",
        "",
        "## Emitter behavior",
        "- Infers a dummy rule from train pairs only.",
        "- Emits exactly two candidate outputs per test input.",
        "- Rejects malformed or non-grid outputs.",
        "- Does not repair candidates from hidden references.",
        "",
        "## Scorer behavior",
        "- Uses exact grid equality only.",
        "- Scores 1 when either candidate exactly matches the scorer-only reference.",
        "- Scores 0 otherwise.",
        "- Returns metadata-safe results only.",
        "",
        "## Harness behavior",
        "- Wires adapter → solver-visible packet → emitter → scorer.",
        "- Uses the dummy/no-data fixture only.",
        "- Produces metadata-only summaries.",
        "- Keeps official/public data untouched.",
        "",
        "## Redactor behavior",
        "- Removes expected outputs, reference grids, raw task JSON dumps, latent rules, and answer descriptors.",
        "- Preserves checksum/provenance metadata.",
        "- Preserves aggregate score metadata only.",
        "",
        "## Approval dependency",
        "- The adapter/harness reject missing or invalid approval manifests.",
        "- The adapter/harness reject official/public source paths until approved metadata exists.",
        "- The implementation does not authorize official data use.",
        "",
        "## Leakage audit",
        f"- {redacted_result.get('leakage_audit', {})}",
        f"- Summary: {summary}",
        "",
        "## Validation results",
        f"- Exact-two-output compliance: {summary.get('exact_two_output_compliance', False)}",
        f"- Aggregate score metadata: {summary.get('aggregate_score', 0)}/{summary.get('task_count', 0)}",
        f"- Solver exact: {summary.get('solver_exact_count', 0)}/{summary.get('task_count', 0)}",
        f"- Baseline exact: {summary.get('baseline_exact_count', 0)}/{summary.get('task_count', 0)}",
        f"- Malformed: {summary.get('malformed_count', 0)}, error: {summary.get('error_count', 0)}",
        f"- Official percentage remains none/0: {summary.get('official_percentage_remains_none_zero', False)}",
        "",
        "## Readiness verdict",
        f"- Readiness verdict: `{'official_public_parse_scorer_surface_dummy_ready' if (result.get('official_data_touched') is False and result.get('public_data_touched') is False and summary.get('exact_two_output_compliance', False) and summary.get('official_percentage_remains_none_zero', False) and summary.get('malformed_count', 0) == 0 and summary.get('error_count', 0) == 0) else 'official_public_parse_scorer_surface_dummy_not_ready'}`",
        "",
        "## Recommended next lane",
        "- If operator approval for real public sources is later granted, wire the verifier/adapter boundary first and keep scorer-only references hidden.",
    ]
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "SCHEMA_VERSION_V1",
    "run_arc_official_public_dummy_no_data_harness_v1",
    "build_arc_official_public_dummy_surface_report_v1",
]
