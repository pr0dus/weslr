#!/usr/bin/env python3
"""Weslr CLI - Capability Discovery commands.

Commands:
- list: List capability suggestions with filters
- create: Create a new capability suggestion
- deny: Deny a suggestion for N hours (default 24h)
- accept: Accept a suggestion
- archive: Archive a suggestion
- search: Search suggestions by text
- stats: Show capability discovery statistics
- show: Show a single suggestion by ID
- snooze: Snooze a suggestion for N hours (default 1h)

## Operator Usage

Basic workflow:
1. Create suggestions: capability create --title "..." --type <type> --summary "..." --why "..." --improvement "..."
2. List suggestions: capability list [--status <status>] [--type <type>]
3. Search: capability search --query "term"
4. Review single: capability show --id <id>
5. Status transitions: deny, snooze, accept, archive

Examples:
  # Create a new suggestion
  weslr capability create --title "Mobile app" --type native_mobile --summary "Need native mobile" --why "Users need mobile access" --improvement "iOS/Android apps"
  
  # List all suggestions
  weslr capability list
  
  # Deny for 24 hours
  weslr capability deny --id <id>
  
  # Snooze for 1 hour
  weslr capability snooze --id <id>
  
  # Accept for implementation
  weslr capability accept --id <id>
  
  # Archive as irrelevant
  weslr capability archive --id <id>
  
  # Search for keywords
  weslr capability search --query "mobile"
  
  # View statistics
  weslr capability stats
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add workspace to path
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR))

from weslr.capability_discovery import api, data_model, store


def register_commands(subparsers):
    """Register capability discovery subcommands."""
    parser = subparsers.add_parser("capability", help="Capability discovery commands")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # list command
    list_parser = subparsers.add_parser("list", help="List capability suggestions")
    list_parser.add_argument("--status", choices=["new", "suggested", "accepted", "denied", "snoozed", "archived"], help="Filter by status")
    list_parser.add_argument("--type", choices=[t.value for t in data_model.CapabilityType], help="Filter by capability type")
    list_parser.add_argument("--limit", type=int, default=20, help="Limit results")
    list_parser.add_argument("--offset", type=int, default=0, help="Offset for pagination")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.set_defaults(func=cmd_list)

    # create command
    create_parser = subparsers.add_parser("create", help="Create a new capability suggestion")
    create_parser.add_argument("--title", required=True, help="Title of the suggestion")
    create_parser.add_argument("--type", required=True, choices=[t.value for t in data_model.CapabilityType], help="Capability type")
    create_parser.add_argument("--summary", required=True, help="Brief summary")
    create_parser.add_argument("--why", required=True, help="Why this matters")
    create_parser.add_argument("--improvement", required=True, help="Improvement area")
    create_parser.add_argument("--confidence", type=float, default=0.5, help="Confidence score (0-1)")
    create_parser.add_argument("--tags", nargs="*", default=[], help="Tags for filtering")
    create_parser.set_defaults(func=cmd_create)

    # deny command
    deny_parser = subparsers.add_parser("deny", help="Deny a suggestion")
    deny_parser.add_argument("--id", required=True, help="Suggestion ID")
    deny_parser.add_argument("--hours", type=int, default=24, help="Deny for N hours (default 24h)")
    deny_parser.add_argument("--json", action="store_true", help="Output as JSON")
    deny_parser.set_defaults(func=cmd_deny)

    # accept command
    accept_parser = subparsers.add_parser("accept", help="Accept a suggestion")
    accept_parser.add_argument("--id", required=True, help="Suggestion ID")
    accept_parser.add_argument("--json", action="store_true", help="Output as JSON")
    accept_parser.set_defaults(func=cmd_accept)

    # archive command
    archive_parser = subparsers.add_parser("archive", help="Archive a suggestion")
    archive_parser.add_argument("--id", required=True, help="Suggestion ID")
    archive_parser.add_argument("--json", action="store_true", help="Output as JSON")
    archive_parser.set_defaults(func=cmd_archive)

    # show command
    show_parser = subparsers.add_parser("show", help="Show a single suggestion by ID")
    show_parser.add_argument("--id", required=True, help="Suggestion ID")
    show_parser.add_argument("--json", action="store_true", help="Output as JSON")
    show_parser.set_defaults(func=cmd_show)

    # snooze command
    snooze_parser = subparsers.add_parser("snooze", help="Snooze a suggestion")
    snooze_parser.add_argument("--id", required=True, help="Suggestion ID")
    snooze_parser.add_argument("--hours", type=int, default=1, help="Snooze for N hours (default 1h)")
    snooze_parser.add_argument("--json", action="store_true", help="Output as JSON")
    snooze_parser.set_defaults(func=cmd_snooze)

    # search command
    search_parser = subparsers.add_parser("search", help="Search suggestions")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--limit", type=int, default=20, help="Limit results")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")
    search_parser.set_defaults(func=cmd_search)

    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show capability discovery statistics")
    stats_parser.add_argument("--json", action="store_true", help="Output as JSON")
    stats_parser.set_defaults(func=cmd_stats)


def cmd_list(args):
    """Handle 'capability list' command."""
    status = data_model.SuggestionStatus(args.status) if args.status else None
    capability_type = data_model.CapabilityType(args.type) if args.type else None

    suggestions = api.list_suggestions(
        status=status,
        capability_type=capability_type,
        limit=args.limit,
        offset=args.offset,
    )

    if args.json:
        output = [s.to_dict() for s in suggestions]
        print(json.dumps(output, indent=2))
    else:
        if not suggestions:
            print("No suggestions found.")
            return
        for s in suggestions:
            print(f"[{s.id[:8]}] {s.title} ({s.status.value}) - {s.capability_type.value}")
            if s.summary:
                print(f"    {s.summary}")
            print()


def cmd_create(args):
    """Handle 'capability create' command."""
    provenance = []
    suggestion = api.create_suggestion(
        title=args.title,
        capability_type=data_model.CapabilityType(args.type),
        summary=args.summary,
        why_it_matters=args.why,
        improvement_area=args.improvement,
        provenance=provenance,
        confidence=args.confidence,
        tags=args.tags,
    )
    print(f"Created suggestion: {suggestion.id[:8]}")
    print(f"Title: {suggestion.title}")
    print(f"Status: {suggestion.status.value}")


def cmd_deny(args):
    """Handle 'capability deny' command."""
    suggestion = api.deny_suggestion(suggestion_id=args.id, hours=args.hours)
    if args.json:
        print(json.dumps(suggestion.to_dict(), indent=2))
    else:
        print(f"Denied: {suggestion.id[:8]} - {suggestion.title}")
        print(f"Status: {suggestion.status.value}")
        print(f"Denied until: {suggestion.denied_until}")


def cmd_accept(args):
    """Handle 'capability accept' command."""
    suggestion = api.accept_suggestion(suggestion_id=args.id)
    if args.json:
        print(json.dumps(suggestion.to_dict(), indent=2))
    else:
        print(f"Accepted: {suggestion.id[:8]} - {suggestion.title}")
        print(f"Status: {suggestion.status.value}")


def cmd_archive(args):
    """Handle 'capability archive' command."""
    suggestion = api.archive_suggestion(suggestion_id=args.id)
    if args.json:
        print(json.dumps(suggestion.to_dict(), indent=2))
    else:
        print(f"Archived: {suggestion.id[:8]} - {suggestion.title}")
        print(f"Status: {suggestion.status.value}")


def cmd_show(args):
    """Handle 'capability show' command."""
    suggestion = api.get_suggestion(suggestion_id=args.id)
    if not suggestion:
        print(f"Suggestion not found: {args.id}")
        return
    if args.json:
        print(json.dumps(suggestion.to_dict(), indent=2))
    else:
        print(f"ID: {suggestion.id}")
        print(f"Title: {suggestion.title}")
        print(f"Type: {suggestion.capability_type.value}")
        print(f"Status: {suggestion.status.value}")
        print(f"Summary: {suggestion.summary}")
        print(f"Why it matters: {suggestion.why_it_matters}")
        print(f"Improvement area: {suggestion.improvement_area}")
        print(f"Confidence: {suggestion.confidence}")
        print(f"Created: {suggestion.created_at}")
        print(f"Last seen: {suggestion.last_seen_at}")
        if suggestion.denied_until:
            print(f"Denied until: {suggestion.denied_until}")
        if suggestion.snoozed_until:
            print(f"Snoozed until: {suggestion.snoozed_until}")


def cmd_snooze(args):
    """Handle 'capability snooze' command."""
    suggestion = api.update_status(suggestion_id=args.id, new_status=data_model.SuggestionStatus.SNOOZED)
    # Set snooze until
    suggestion.snoozed_until = api.time.strftime(
        "%Y-%m-%dT%H:%M:%SZ",
        api.time.gmtime(api.time.time() + args.hours * 3600)
    )
    api.get_store().update_suggestion(suggestion)
    # Emit snoozed governance override signal (fail-open)
    try:
        import sys
        sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
        from weslr.drift_emitter import emit_snoozed_signal
        emit_snoozed_signal(proposal_id=str(suggestion.id), human="operator")
    except Exception:
        pass
    if args.json:
        print(json.dumps(suggestion.to_dict(), indent=2))
    else:
        print(f"Snoozed: {suggestion.id[:8]} - {suggestion.title}")
        print(f"Status: {suggestion.status.value}")
        print(f"Snoozed until: {suggestion.snoozed_until}")


def cmd_search(args):
    """Handle 'capability search' command."""
    suggestions = api.search_suggestions(query=args.query, limit=args.limit)
    if args.json:
        output = [s.to_dict() for s in suggestions]
        print(json.dumps(output, indent=2))
    else:
        if not suggestions:
            print("No suggestions found.")
            return
        for s in suggestions:
            print(f"[{s.id[:8]}] {s.title} ({s.status.value}) - {s.capability_type.value}")
            if s.summary:
                print(f"    {s.summary}")
            print()


def cmd_stats(args):
    """Handle 'capability stats' command."""
    total = api.count_suggestions()
    by_status = {status: api.count_suggestions(status) for status in data_model.SuggestionStatus}
    
    stats = {
        "total": total,
        "by_status": {s.value: c for s, c in by_status.items()},
    }

    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print(f"Total suggestions: {total}")
        print("\nBy status:")
        for status, count in by_status.items():
            if count > 0:
                print(f"  {status}: {count}")


def main():
    """Main entry point for capability commands."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Capability discovery CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Register commands
    register_commands(subparsers)
    
    # Parse args
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Dispatch to command handlers
    if args.command == "list":
        cmd_list(args)
    elif args.command == "create":
        cmd_create(args)
    elif args.command == "deny":
        cmd_deny(args)
    elif args.command == "accept":
        cmd_accept(args)
    elif args.command == "archive":
        cmd_archive(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "snooze":
        cmd_snooze(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

