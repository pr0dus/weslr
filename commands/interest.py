"""
Interest Tracker CLI commands.

Supports:
  interest create <name> [tag,tag,...]
  interest list [--tag TAG] [--status STATUS]
  interest show <id_or_name>
  interest add-occurrence <id> <type> <item_id> [reason]
"""

from __future__ import annotations

import argparse
from weslr.interest_tracker import create_interest, get_interest, list_interests, add_occurrence


def cmd_interest_create(args: argparse.Namespace) -> None:
    """Create a new interest."""
    name = args.name
    tags = []
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    try:
        interest = create_interest(name, tags)
        print(f"Created: [{interest['id']}] {interest['display_name']}")
        print(f"  normalized name: {interest['name']}")
        print(f"  tags: {', '.join(interest['tags']) or '(none)'}")
    except ValueError as e:
        print(f"Error: {e}")


def cmd_interest_list(args: argparse.Namespace) -> None:
    """List all tracked interests."""
    interests = list_interests(status=args.status, tag=args.tag)
    if not interests:
        if args.tag:
            print(f"No interests with tag '{args.tag}'.")
        else:
            print("No interests tracked.")
        return

    for interest in interests:
        print(f"[{interest['id']}] {interest['display_name']} — {interest['name']}")
        print(f"  tags: {', '.join(interest['tags']) or '(none)'} | "
              f"occurrences: {interest['occurrence_count']} | "
              f"created: {interest['created_at']}")


def cmd_interest_show(args: argparse.Namespace) -> None:
    """Show details for a specific interest."""
    identifier = args.identifier
    interest = get_interest(identifier)
    if not interest:
        print(f"Interest not found: {identifier}")
        return
    print(f"[{interest['id']}] {interest['display_name']}")
    print(f"  normalized name: {interest['name']}")
    print(f"  status: {interest['status']}")
    print(f"  tags: {', '.join(interest['tags']) or '(none)'}")
    print(f"  occurrence_count: {interest['occurrence_count']}")
    print(f"  created_at: {interest['created_at']}")
    print(f"  last_seen_at: {interest['last_seen_at']}")
    print(f"  occurrences: {len(interest.get('occurrences', []))} entries")
    for occ in interest.get("occurrences", []):
        print(f"    [{occ['type']}] {occ['item_id']} — {occ['triggered_at']}")
        if occ.get("reason"):
            print(f"      reason: {occ['reason']}")


def cmd_interest_add_occurrence(args: argparse.Namespace) -> None:
    """Add a manual occurrence to an existing interest."""
    interest_id = args.interest_id
    occ_type = args.type
    item_id = args.item_id
    reason = args.reason or ""
    try:
        interest = add_occurrence(interest_id, occ_type, item_id, reason)
        print(f"Added: [{interest['id']}] {interest['display_name']} — "
              f"occurrence_count now {interest['occurrence_count']}")
    except ValueError as e:
        print(f"Error: {e}")


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register interest tracker subcommands."""
    parser_interest = subparsers.add_parser(
        "interest", help="Interest Tracker commands"
    )
    sub = parser_interest.add_subparsers(dest="interest_cmd", help="Interest subcommands")

    # interest create
    create = sub.add_parser("create", help="Create a new interest")
    create.add_argument("name", help="Interest name (e.g., 'confidence calibration')")
    create.add_argument("tags", nargs="?", default="",
                        help="Comma-separated tags (e.g., 'governance,quality')")
    create.set_defaults(func=cmd_interest_create)

    # interest list
    list_cmd = sub.add_parser("list", help="List all tracked interests")
    list_cmd.add_argument("--tag", dest="tag", default=None, help="Filter by tag")
    list_cmd.add_argument("--status", dest="status", default=None, help="Filter by status")
    list_cmd.set_defaults(func=cmd_interest_list)

    # interest show
    show = sub.add_parser("show", help="Show interest details")
    show.add_argument("identifier", help="Interest ID or normalized name")
    show.set_defaults(func=cmd_interest_show)

    # interest add-occurrence
    add_occ = sub.add_parser("add-occurrence", help="Add a manual occurrence to an interest")
    add_occ.add_argument("interest_id", help="Interest ID")
    add_occ.add_argument("type", help="Occurrence type: artifact, question, or proposal")
    add_occ.add_argument("item_id", help="Item identifier (artifact id, question id, etc.)")
    add_occ.add_argument("reason", nargs="?", default="", help="Optional reason for this occurrence")
    add_occ.set_defaults(func=cmd_interest_add_occurrence)