"""Opportunity management commands for Weslr.

Commands:
- opportunity-list [--limit N]
- opportunity-transition <id>
- opportunity-reject <id>
- opportunity-cluster
- opportunity-revisit <id>
"""

from __future__ import annotations

import argparse
import json

import sim


def cmd_opportunity_list(args: argparse.Namespace):
    """List opportunities."""
    items = sim.load_projects() or []

    limit = args.limit or 10
    for i, item in enumerate(items[:limit]):
        if isinstance(item, dict):
            print(f"Opportunity {i+1}: {item.get('title', 'unnamed')}")
            print(f"  ID: {item.get('id', 'unknown')}")
            print(f"  Status: {item.get('status', 'unknown')}")
            print()


def cmd_opportunity_transition(args: argparse.Namespace):
    """Transition an opportunity."""
    result = sim.apply_pack_outcome(args.id, "transition")
    print(f"Transitioned opportunity: {result}")


def cmd_opportunity_reject(args: argparse.Namespace):
    """Reject an opportunity."""
    result = sim.apply_pack_outcome(args.id, "reject")
    print(f"Rejected opportunity: {result}")


def cmd_opportunity_cluster(args: argparse.Namespace):
    """Cluster opportunities."""
    clusters = sim.category_action() or {}
    print(json.dumps(clusters, indent=2))


def cmd_opportunity_revisit(args: argparse.Namespace):
    """Mark an opportunity for revisit."""
    result = sim.browse_queue(args.id, "revisit")
    print(f"Marked opportunity for revisit: {result}")


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register opportunity-related subcommands."""
    # opportunity-list
    parser_list = subparsers.add_parser("opportunity-list", help="List opportunities")
    parser_list.add_argument("--limit", type=int, default=10, help="Maximum items to show")
    parser_list.set_defaults(func=cmd_opportunity_list)

    # opportunity-transition
    parser_transition = subparsers.add_parser("opportunity-transition", help="Transition opportunity")
    parser_transition.add_argument("id", help="Opportunity ID")
    parser_transition.set_defaults(func=cmd_opportunity_transition)

    # opportunity-reject
    parser_reject = subparsers.add_parser("opportunity-reject", help="Reject opportunity")
    parser_reject.add_argument("id", help="Opportunity ID")
    parser_reject.set_defaults(func=cmd_opportunity_reject)

    # opportunity-cluster
    parser_cluster = subparsers.add_parser("opportunity-cluster", help="Cluster opportunities")
    parser_cluster.set_defaults(func=cmd_opportunity_cluster)

    # opportunity-revisit
    parser_revisit = subparsers.add_parser("opportunity-revisit", help="Mark opportunity for revisit")
    parser_revisit.add_argument("id", help="Opportunity ID")
    parser_revisit.set_defaults(func=cmd_opportunity_revisit)
