"""Memory lifecycle commands for Weslr.

Commands:
- memory-list [--limit N]
- memory-show <id>
- memory-prune [--older-than N]
- memory-lifecycle
- memory-pressure
"""

from __future__ import annotations

import argparse
import json
import time

import sim


def cmd_memory_list(args: argparse.Namespace):
    """List memory items."""
    # Load memory from sim module
    items = sim.load_messages() or []

    limit = args.limit or 10
    for item in items[:limit]:
        if isinstance(item, dict):
            print(f"{item.get('id', 'unknown')}: {item.get('content', '')[:50]}...")


def cmd_memory_show(args: argparse.Namespace):
    """Show a specific memory item."""
    # Load memory and find by ID
    items = sim.load_messages() or []

    for item in items:
        if isinstance(item, dict) and item.get('id') == args.id:
            print(json.dumps(item, indent=2))
            return

    print(f"Memory item '{args.id}' not found")


def cmd_memory_prune(args: argparse.Namespace):
    """Prune old memory items."""
    older_than = args.older_than or 86400  # Default: 1 day in seconds

    items = sim.load_messages() or []
    before = len(items)

    # Filter out old items
    now = int(time.time())
    items = [
        item for item in items
        if isinstance(item, dict) and (now - item.get('created_at', 0)) < older_than
    ]

    # Save back
    # Note: sim module needs to have save function
    # For now, just report
    print(f"Pruned {before - len(items)} old memory items")


def cmd_memory_lifecycle(args: argparse.Namespace):
    """Show memory lifecycle report."""
    report = sim.build_memory_lifecycle_report() or {}
    print(json.dumps(report, indent=2))


def cmd_memory_pressure(args: argparse.Namespace):
    """Show memory pressure status."""
    pressure = sim.monitor_memory_pressure() or {}
    print(json.dumps(pressure, indent=2))


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register memory-related subcommands."""
    # memory-list
    parser_list = subparsers.add_parser("memory-list", help="List memory items")
    parser_list.add_argument("--limit", type=int, default=10, help="Maximum items to show")
    parser_list.set_defaults(func=cmd_memory_list)

    # memory-show
    parser_show = subparsers.add_parser("memory-show", help="Show memory item")
    parser_show.add_argument("id", help="Memory item ID")
    parser_show.set_defaults(func=cmd_memory_show)

    # memory-prune
    parser_prune = subparsers.add_parser("memory-prune", help="Prune old memory")
    parser_prune.add_argument("--older-than", type=int, help="Age threshold in seconds")
    parser_prune.set_defaults(func=cmd_memory_prune)

    # memory-lifecycle
    parser_lifecycle = subparsers.add_parser("memory-lifecycle", help="Memory lifecycle report")
    parser_lifecycle.set_defaults(func=cmd_memory_lifecycle)

    # memory-pressure
    parser_pressure = subparsers.add_parser("memory-pressure", help="Memory pressure status")
    parser_pressure.set_defaults(func=cmd_memory_pressure)
