# commands/thread.py — Thread Tracker CLI commands

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr import thread_tracker


def cmd_thread_list(args) -> None:
    """List threads, optionally filtered by state."""
    state = args.state if hasattr(args, "state") else None
    limit = getattr(args, "limit", 50)
    threads = thread_tracker.list_threads(state=state, limit=limit)
    if not threads:
        print("No threads found.")
        return
    for t in threads:
        item_count = len(t.get("items", []))
        print(f"[{t['id']}] {t['name']} | state={t['state']} | items={item_count} | updated={t['updated_at']}")


def cmd_thread_create(args) -> None:
    """Create a new thread."""
    thread = thread_tracker.create_thread(args.name)
    if thread is None:
        print("Error: thread limit reached (100). Prune dormant threads first.", file=sys.stderr)
        sys.exit(1)
    print(f"Created thread [{thread['id']}] {thread['name']}")


def cmd_thread_show(args) -> None:
    """Show full details of a thread."""
    thread = thread_tracker.get_thread(args.thread_id)
    if thread is None:
        print(f"Thread [{args.thread_id}] not found.", file=sys.stderr)
        sys.exit(1)
    print(f"Thread: [{thread['id']}] {thread['name']}")
    print(f"  State:    {thread['state']}")
    print(f"  Created:  {thread['created_at']}")
    print(f"  Updated:  {thread['updated_at']}")
    print(f"  Tags:     {', '.join(thread.get('tags', []) or ['(none)'])}")
    print(f"  Items:    {len(thread.get('items', []))}")
    for item in thread.get("items", []):
        note_suffix = f" | note: {item['note']}" if item.get("note") else ""
        print(
            f"    - [{item['item_type']}] {item['item_id']} "
            f"({item['link_type']}, by {item['added_by']} at {item['added_at']}){note_suffix}"
        )


def cmd_thread_add_item(args) -> None:
    """Add an item to a thread."""
    ok = thread_tracker.add_item(
        thread_id=args.thread_id,
        item_type=args.item_type,
        item_id=args.item_id,
        link_type=args.link_type,
        added_by=args.added_by,
    )
    if not ok:
        print(
            f"Error: could not add item to thread [{args.thread_id}]. "
            f"Check that the thread exists and item_type={args.item_type} is valid.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Added [{args.item_type}] {args.item_id} to thread [{args.thread_id}]")


def cmd_thread_set_state(args) -> None:
    """Set the state of a thread."""
    ok = thread_tracker.set_state(args.thread_id, args.new_state)
    if not ok:
        print(
            f"Error: could not set state to '{args.new_state}'. "
            f"Check that the thread exists and state is one of: active, unresolved, resolved, dormant.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Thread [{args.thread_id}] state set to {args.new_state}")


def register_commands(parser) -> None:
    """Register thread commands with the CLI parser."""
    thread_parser = parser.add_parser("thread", help="Thread Tracker operations")
    sub = thread_parser.add_subparsers(dest="thread_cmd", metavar="CMD")

    # thread list
    p = sub.add_parser("list", help="List threads")
    p.add_argument("--state", choices=["active", "unresolved", "resolved", "dormant"], help="Filter by state")
    p.add_argument("--limit", type=int, default=50, help="Max threads to return")
    p.set_defaults(func=cmd_thread_list)

    # thread create
    p = sub.add_parser("create", help="Create a new thread")
    p.add_argument("name", help="Thread name")
    p.set_defaults(func=cmd_thread_create)

    # thread show
    p = sub.add_parser("show", help="Show thread details")
    p.add_argument("thread_id", help="Thread ID (e.g., thr-xxxx)")
    p.set_defaults(func=cmd_thread_show)

    # thread add-item
    p = sub.add_parser("add-item", help="Add an item to a thread")
    p.add_argument("thread_id", help="Thread ID")
    p.add_argument("item_type", choices=["artifact", "question", "suggestion", "resolution", "note"], help="Item type")
    p.add_argument("item_id", help="Item ID or content")
    p.add_argument("link_type", choices=["explicit", "inferred"], help="Link type")
    p.add_argument("added_by", help="Authority (e.g., operator, integration:artifact_inquiry)")
    p.set_defaults(func=cmd_thread_add_item)

    # thread set-state
    p = sub.add_parser("set-state", help="Set thread state")
    p.add_argument("thread_id", help="Thread ID")
    p.add_argument("new_state", choices=["active", "unresolved", "resolved", "dormant"], help="New state")
    p.set_defaults(func=cmd_thread_set_state)

    def dispatch(args) -> None:
        if args.thread_cmd is None:
            thread_parser.print_help()
            return
        args.func(args)

    thread_parser.set_defaults(func=dispatch)
