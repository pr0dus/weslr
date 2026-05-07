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
from ..consolidation_config import load_config, save_config
from ..consolidation_promotion import (
    get_auto_status,
    enable_auto,
    disable_auto,
    decide_promotion,
    auto_promote,
    _AUDIT_PATH,
    PromotionResult,
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

    # ── auto subcommand (V2) ─────────────────────────────────────────────────
    auto_parser = sub.add_parser("auto", help="Consolidation auto-promotion control")
    auto_sub = auto_parser.add_subparsers(dest="auto_subcommand", required=True)

    auto_status_parser = auto_sub.add_parser("status", help="Show auto-promotion status")
    auto_status_parser.add_argument(
        "--base-path", dest="base_path",
        help="Override .weslr base path"
    )
    auto_status_parser.add_argument(
        "--json", action="store_true",
        help="Machine-readable output"
    )

    auto_on_parser = auto_sub.add_parser("on", help="Enable consolidation auto-promotion")
    auto_on_parser.add_argument(
        "--base-path", dest="base_path",
        help="Override .weslr base path"
    )

    auto_off_parser = auto_sub.add_parser("off", help="Disable consolidation auto-promotion")
    auto_off_parser.add_argument(
        "--base-path", dest="base_path",
        help="Override .weslr base path"
    )

    auto_audit_parser = auto_sub.add_parser("audit", help="Show recent audit log entries")
    auto_audit_parser.add_argument(
        "--limit", type=int, default=20,
        help="Number of entries to show (default: 20)"
    )

    # ── promote subcommand (V2) ──────────────────────────────────────────────
    promote_parser = sub.add_parser("promote", help="Promote a consolidation candidate (dry-run or live)")
    promote_parser.add_argument(
        "cluster_id", nargs="?",
        help="Cluster ID to promote (omit for list)"
    )
    promote_parser.add_argument(
        "--dry-run", action="store_true",
        help="Show decision without writing anything"
    )
    promote_parser.add_argument(
        "--approve", action="store_true",
        help="Explicitly approve (overrides auto-disabled for yellow/red)"
    )
    promote_parser.add_argument(
        "--base-path", dest="base_path",
        help="Override .weslr base path"
    )
    promote_parser.add_argument(
        "--json", action="store_true",
        help="Machine-readable output"
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

    # ── auto subcommand ──────────────────────────────────────────────────────
    if args.subcommand == "auto":
        return _handle_auto(args, base)

    # ── promote subcommand ──────────────────────────────────────────────────
    if args.subcommand == "promote":
        return _handle_promote(args, base)

    return 0


# -------------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------------

def _load_cfg(base):
    path = str(base / "consolidation_config.json") if base else None
    return load_config(path)


def _handle_auto(args, base) -> int:
    import json

    cfg = _load_cfg(base)

    if args.auto_subcommand == "status":
        status = get_auto_status(cfg)
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            lines = [
                f"consolidation_auto_enabled={status['consolidation_auto_enabled']}",
                f"green_zone_auto_promotion_enabled={status['green_zone_auto_promotion_enabled']}",
                f"enabled_zones={status['enabled_zones']}",
                f"require_provenance={status['require_provenance']}",
                f"require_audit_log={status['require_audit_log']}",
                f"allowed_green_destinations={status['allowed_green_destinations']}",
            ]
            print("\n".join(lines))
        return 0

    if args.auto_subcommand == "on":
        cfg = enable_auto(cfg)
        print("Consolidation auto-promotion ENABLED")
        return 0

    if args.auto_subcommand == "off":
        cfg = disable_auto(cfg)
        print("Consolidation auto-promotion DISABLED")
        return 0

    if args.auto_subcommand == "audit":
        audit_path = base / "consolidation_audit.jsonl" if base else _AUDIT_PATH
        if not audit_path.exists():
            print(f"No audit log found at {audit_path}")
            return 1
        with open(audit_path, encoding="utf-8") as f:
            entries = [json.loads(l) for l in f if l.strip()]
        print(f"audit_log={audit_path}")
        print(f"entry_count={len(entries)}")
        print()
        for entry in entries[-args.limit:]:
            ts = entry.get("timestamp", "?")
            ev = entry.get("decision", "?")
            cid = entry.get("cluster_id", "?")
            zone = entry.get("zone", "?")
            dest = entry.get("destination", "?")
            blocked = entry.get("blocked_reasons", [])
            reasons_str = f" blocked={blocked}" if blocked else ""
            print(f"  [{ts}] {ev}  zone={zone}  dest={dest}  cluster={cid}{reasons_str}")
        return 0

    return 0


def _read_digest_clusters(base) -> list[dict]:
    """Read clusters from consolidation_digest.jsonl."""
    digest_path = (base / _DIGEST_FILENAME) if base else _ROOT / _DIGEST_FILENAME
    clusters = []
    if digest_path.exists():
        with open(digest_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    import json
                    clusters.append(json.loads(line))
    return clusters


def _handle_promote(args, base) -> int:
    import json

    cfg = _load_cfg(base)
    clusters = _read_digest_clusters(base)

    if not clusters:
        print("No consolidation digest found. Run 'weslr consolidation run' first.")
        return 1

    if not args.cluster_id:
        # List all candidates with their zones
        print(f"{'cluster_id':<40} {'zone':<8} {'auto':<6} {'destination':<30}")
        print("-" * 90)
        for c in clusters:
            decision = decide_promotion(c, cfg)
            auto_mark = "YES" if decision.auto_promote else "no"
            print(f"{c.get('cluster_id','?'):<40} {decision.zone:<8} {auto_mark:<6} {c.get('proposed_destination','?'):<30}")
        return 0

    # Find the target cluster
    target = None
    for c in clusters:
        if c.get("cluster_id") == args.cluster_id:
            target = c
            break

    if not target:
        print(f"Cluster '{args.cluster_id}' not found in consolidation digest.")
        return 1

    decision = decide_promotion(target, cfg)

    if args.dry_run:
        if args.json:
            print(json.dumps(decision.to_dict(), indent=2))
        else:
            print(f"cluster_id:    {decision.cluster_id}")
            print(f"zone:          {decision.zone}")
            print(f"auto_eligible: {decision.auto_eligible}")
            print(f"auto_promote:  {decision.auto_promote}")
            print(f"destination:   {decision.destination}")
            print(f"blocked_reasons: {decision.blocked_reasons}")
            print(f"provenance:    {decision.provenance}")
        return 0

    # Live promotion
    result = auto_promote(target, cfg)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"promoted:      {result.promoted}")
        print(f"decision:      {result.decision}")
        print(f"zone:          {result.zone}")
        print(f"destination:   {result.destination}")
        if result.blocked_reasons:
            print(f"blocked_reasons: {result.blocked_reasons}")
        print(f"record_written: {result.record_written}")
    return 0
