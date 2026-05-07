"""
WESLR Consolidation Loop — CLI Commands

Manual execution only. No daemon scheduling.
"""

import argparse
import pathlib
import sys

from ..consolidation_loop import (
    run_consolidation_digest,
    build_text_summary,
    _DIGEST_FILENAME,
    _ROOT,
)


def handle_consolidation(argv: list[str] | None = None) -> int:
    """Main entry point for `weslr consolidation` CLI."""
    parser = argparse.ArgumentParser(
        prog="weslr consolidation",
        description="WESLR Consolidation Loop — V1 Read-Only Digest",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    sub.add_parser("help", help="Show this help message")

    run_parser = sub.add_parser("run", help="Run consolidation digest")
    run_parser.add_argument(
        "--hours", type=int, default=24,
        help="Look back window in hours (default: 24)"
    )
    run_parser.add_argument(
        "--base-path", dest="base_path",
        help="Override .weslr base path"
    )
    run_parser.add_argument(
        "--json", action="store_true",
        help="Output machine-readable JSON summary"
    )

    status_parser = sub.add_parser("status", help="Show last digest output path and record count")
    status_parser.add_argument(
        "--base-path", dest="base_path",
        help="Override .weslr base path"
    )

    args = parser.parse_args(argv)

    if args.subcommand == "help":
        parser.print_help()
        return 0

    base = pathlib.Path(args.base_path) if args.base_path else None
    base_str = str(base) if base else None

    if args.subcommand == "run":
        result = run_consolidation_digest(root=base_str, hours=args.hours)

        if args.json:
            import json as _json
            print(_json.dumps({
                "traces_collected": result.traces_collected,
                "clusters_found": result.clusters_found,
                "candidates_written": result.candidates_written,
                "output": str(pathlib.Path(result.output_path) / result.output_file),
                "promotion_performed": False,
            }))
        else:
            print(build_text_summary(result))
        return 0

    if args.subcommand == "status":
        digest_path = (base or _ROOT) / _DIGEST_FILENAME
        if not digest_path.exists():
            print(f"No consolidation digest found at {digest_path}")
            print("Run 'weslr consolidation run' first.")
            return 1
        with open(digest_path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        print(f"consolidation_digest={digest_path}")
        print(f"record_count={len(lines)}")
        return 0

    return 0
