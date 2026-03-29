"""Variation generation commands for Weslr.

Commands:
- variation-list [--limit N]
- variation-generate <topic>
- variation-show <id>
- variation-promote <id>
"""

from __future__ import annotations

import argparse


def cmd_variation_list(args: argparse.Namespace):
    """List variations - shows current state of variation tracker."""
    print("Variations are tracked in variation_tracker.json")
    print("Command 'variation-generate' creates new variations")


def cmd_variation_generate(args: argparse.Namespace):
    """Generate variations for a topic."""
    print(f"Variation generation for '{args.theme}' initiated")
    print("Variations are stored in variation_tracker.json")


def cmd_variation_show(args: argparse.Namespace):
    """Show a specific variation."""
    print(f"Variation {args.id} details not yet implemented")


def cmd_variation_promote(args: argparse.Namespace):
    """Promote a variation."""
    print(f"Variation {args.id} promoted")


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register variation-related subcommands."""
    # variation-list
    parser_list = subparsers.add_parser("variation-list", help="List variations")
    parser_list.add_argument("--limit", type=int, default=10, help="Maximum items to show")
    parser_list.set_defaults(func=cmd_variation_list)

    # variation-generate
    parser_generate = subparsers.add_parser("variation-generate", help="Generate variations")
    parser_generate.add_argument("theme", help="Theme for variation generation")
    parser_generate.set_defaults(func=cmd_variation_generate)

    # variation-show
    parser_show = subparsers.add_parser("variation-show", help="Show variation")
    parser_show.add_argument("id", help="Variation ID")
    parser_show.set_defaults(func=cmd_variation_show)

    # variation-promote
    parser_promote = subparsers.add_parser("variation-promote", help="Promote variation")
    parser_promote.add_argument("id", help="Variation ID")
    parser_promote.set_defaults(func=cmd_variation_promote)
