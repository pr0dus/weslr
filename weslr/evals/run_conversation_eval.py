"""Conversation Eval Report Runner V1.

Thin CLI/report layer over `weslr.evals.conversation_eval`.

Usage:
  python -m weslr.evals.run_conversation_eval
  python -m weslr.evals.run_conversation_eval --suite weslr/evals/conversation_suites/public_demo_identity.json
  python -m weslr.evals.run_conversation_eval --json
  python -m weslr.evals.run_conversation_eval --output .weslr/eval_results
  python -m weslr.evals.run_conversation_eval --baseline-dir weslr/evals/baselines

This runner does not create a new evaluation system. It uses the existing
Conversation Evaluation Suite V1 engine.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from weslr.evals.conversation_eval import (
    SuiteResult,
    compare_to_baseline,
    deterministic_public_demo_responder,
    evaluate_suite_file,
    iter_suite_files,
    save_result,
)

DEFAULT_SUITE_DIR = Path(__file__).resolve().parent / "conversation_suites"
DEFAULT_OUTPUT_DIR = Path(".weslr") / "eval_results" / "conversation"


def _baseline_path_for(result: SuiteResult, baseline_dir: str | Path | None) -> Path | None:
    if not baseline_dir:
        return None
    return Path(baseline_dir) / f"{result.suite_id}.result.json"


def _weak_turns(result: SuiteResult) -> list[dict]:
    weak: list[dict] = []
    for turn in result.turn_scores:
        if not turn.passed or turn.missing_required or turn.forbidden_present:
            weak.append(
                {
                    "turn_index": turn.turn_index,
                    "user": turn.user,
                    "score": turn.score,
                    "passed": turn.passed,
                    "missing_required": turn.missing_required,
                    "forbidden_present": turn.forbidden_present,
                    "notes": turn.notes,
                }
            )
    return weak


def result_summary(result: SuiteResult, baseline_dir: str | Path | None = None) -> dict:
    baseline_path = _baseline_path_for(result, baseline_dir)
    baseline_ok = True
    baseline_reasons: list[str] = []
    if baseline_path is not None:
        baseline_ok, baseline_reasons = compare_to_baseline(result, baseline_path)
    return {
        "suite_id": result.suite_id,
        "suite_name": result.suite_name,
        "suite_scope": result.suite_scope,
        "suite_kind": result.suite_kind,
        "validates": result.validates,
        "does_not_validate": result.does_not_validate,
        "score": round(result.score, 6),
        "minimum_score": result.minimum_score,
        "passed": result.passed,
        "baseline_ok": baseline_ok,
        "baseline_reasons": baseline_reasons,
        "weak_turns": _weak_turns(result),
    }


def format_text_report(summary: dict, saved_path: str | None = None) -> str:
    status = "PASS" if summary["passed"] else "FAIL"
    baseline_status = "PASS" if summary["baseline_ok"] else "FAIL"
    lines = [
        f"Suite: {summary['suite_id']}",
        f"Name: {summary['suite_name']}",
        f"Scope: {summary.get('suite_scope', 'unspecified')}",
        f"Kind: {summary.get('suite_kind', 'unspecified')}",
        f"Score: {summary['score']:.3f} / 1.000",
        f"Minimum: {summary['minimum_score']:.3f}",
        f"Result: {status}",
        f"Baseline: {baseline_status}",
    ]
    if summary.get("validates"):
        lines.append("Validates:")
        for item in summary["validates"]:
            lines.append(f"  - {item}")
    if summary.get("does_not_validate"):
        lines.append("Does not validate:")
        for item in summary["does_not_validate"]:
            lines.append(f"  - {item}")
    if saved_path:
        lines.append(f"Saved: {saved_path}")
    if summary["baseline_reasons"]:
        lines.append("Baseline notes:")
        for reason in summary["baseline_reasons"]:
            lines.append(f"  - {reason}")
    if summary["weak_turns"]:
        lines.append("Weak turns:")
        for turn in summary["weak_turns"]:
            lines.append(f"  - Turn {turn['turn_index']}: {turn['user']}")
            lines.append(f"    score={turn['score']:.3f} passed={turn['passed']}")
            if turn["missing_required"]:
                lines.append(f"    missing={', '.join(turn['missing_required'])}")
            if turn["forbidden_present"]:
                lines.append(f"    forbidden={', '.join(turn['forbidden_present'])}")
            if turn["notes"]:
                lines.append(f"    notes={', '.join(turn['notes'])}")
    else:
        lines.append("Weak turns: none")
    return "\n".join(lines)


def run_suites(
    suite_paths: Iterable[Path],
    output_dir: str | Path | None = DEFAULT_OUTPUT_DIR,
    baseline_dir: str | Path | None = None,
) -> list[dict]:
    reports: list[dict] = []
    for suite_path in suite_paths:
        result = evaluate_suite_file(suite_path, deterministic_public_demo_responder)
        saved_path: Path | None = None
        if output_dir:
            saved_path = save_result(result, output_dir)
        summary = result_summary(result, baseline_dir=baseline_dir)
        summary["suite_path"] = str(suite_path)
        summary["saved_path"] = str(saved_path) if saved_path else None
        reports.append(summary)
    return reports


def _collect_suite_paths(args: argparse.Namespace) -> list[Path]:
    if args.suite:
        return [Path(args.suite)]
    suite_dir = Path(args.suite_dir)
    return list(iter_suite_files(suite_dir))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run WESLR conversation evaluation suites")
    parser.add_argument("--suite", help="Run one suite JSON file")
    parser.add_argument("--suite-dir", default=str(DEFAULT_SUITE_DIR), help="Directory containing suite JSON files")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR), help="Directory for saved result JSON files; use empty string to disable")
    parser.add_argument("--baseline-dir", help="Directory containing baseline result JSON files")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    suite_paths = _collect_suite_paths(args)
    output_dir = args.output if args.output else None
    reports = run_suites(suite_paths, output_dir=output_dir, baseline_dir=args.baseline_dir)

    passed = all(r["passed"] and r["baseline_ok"] for r in reports)

    if args.json:
        print(json.dumps({"passed": passed, "suites": reports}, indent=2, ensure_ascii=False))
    else:
        if not reports:
            print("No conversation suites found.")
        for idx, report in enumerate(reports):
            if idx:
                print("\n" + "-" * 72 + "\n")
            print(format_text_report(report, saved_path=report.get("saved_path")))
        print("\nOverall: " + ("PASS" if passed else "FAIL"))

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
