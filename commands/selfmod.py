"""Self-modification commands for Weslr.

Commands:
- selfmod-list [--limit N]
- selfmod-show <id>
- selfmod-apply <id>
- selfmod-rollback <id>
- selfmod-status
"""

from __future__ import annotations

import argparse
import json

from self_modifier import build_proposal_report
from self_mod_applier import apply_modification, rollback
from self_mod_dashboard import get_dashboard_status


def cmd_selfmod_list(args: argparse.Namespace):
    """List self-modification proposals."""
    proposals = build_proposal_report() or []

    limit = args.limit or 10
    for i, proposal in enumerate(proposals[:limit]):
        print(f"Proposal {i+1}: {proposal.get('title', 'unnamed')}")
        print(f"  Type: {proposal.get('type', 'unknown')}")
        print(f"  Status: {proposal.get('status', 'pending')}")
        print()


def cmd_selfmod_show(args: argparse.Namespace):
    """Show a specific self-modification proposal."""
    proposals = build_proposal_report() or []

    for proposal in proposals:
        if str(proposal.get('id', '')).endswith(args.id):
            print(json.dumps(proposal, indent=2))
            return
        if proposal.get('title', '').lower() == args.id.lower():
            print(json.dumps(proposal, indent=2))
            return

    print(f"Self-modification proposal '{args.id}' not found")


def cmd_selfmod_apply(args: argparse.Namespace):
    """Apply a self-modification."""
    result = apply_modification(args.id)
    print(f"Applied modification: {result}")


def cmd_selfmod_rollback(args: argparse.Namespace):
    """Rollback a self-modification."""
    result = rollback(args.id)
    print(f"Rolled back modification: {result}")


def cmd_selfmod_status(args: argparse.Namespace):
    """Show self-modification status."""
    status = get_dashboard_status() or {}
    print(json.dumps(status, indent=2))


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register selfmod-related subcommands."""
    # selfmod-list
    parser_list = subparsers.add_parser("selfmod-list", help="List self-modification proposals")
    parser_list.add_argument("--limit", type=int, default=10, help="Maximum items to show")
    parser_list.set_defaults(func=cmd_selfmod_list)

    # selfmod-show
    parser_show = subparsers.add_parser("selfmod-show", help="Show self-modification proposal")
    parser_show.add_argument("id", help="Proposal ID or title")
    parser_show.set_defaults(func=cmd_selfmod_show)

    # selfmod-apply
    parser_apply = subparsers.add_parser("selfmod-apply", help="Apply self-modification")
    parser_apply.add_argument("id", help="Proposal ID")
    parser_apply.set_defaults(func=cmd_selfmod_apply)

    # selfmod-rollback
    parser_rollback = subparsers.add_parser("selfmod-rollback", help="Rollback self-modification")
    parser_rollback.add_argument("id", help="Proposal ID")
    parser_rollback.set_defaults(func=cmd_selfmod_rollback)

    # selfmod-status
    parser_status = subparsers.add_parser("selfmod-status", help="Self-modification status")
    parser_status.set_defaults(func=cmd_selfmod_status)
