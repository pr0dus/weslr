"""
WESLR Memory Capture Commands

CLI for inspecting and testing memory capture.
Run with: python3 -m weslr.commands.memory_capture_commands <command>
"""

import argparse
import json
import sys
import tempfile
import shutil

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.memory_capture import (
    safe_turn_fingerprint,
    classify_memory_capture_candidates,
    capture_memories_from_turn,
    safe_capture_memories_from_turn,
    MemoryCaptureCandidate,
    MemoryCaptureResult,
)
from weslr.entity_memory import load_entity_memories


def cmd_inspect(args):
    """Classify memory capture candidates from message/response without writing."""
    identity_state = {
        "is_verified": bool(args.verified),
        "identity_status": args.identity_status or "unknown",
        "user_id": args.user_id or None,
    }
    candidates = classify_memory_capture_candidates(
        args.message,
        args.response or "",
        {"project_id": args.project_id},
        identity_state,
        [],
    )
    print(f"Message: {args.message!r}")
    print(f"Response: {args.response!r}")
    print(f"Identity: status={identity_state['identity_status']}, verified={identity_state['is_verified']}, user_id={identity_state['user_id']}")
    print(f"Candidates found: {len(candidates)}")
    for c in candidates:
        print(f"  [{c.capture_type}] {c.entity_type}:{c.entity_id} | {c.summary}")
        print(f"    confidence={c.confidence}, access={c.access_level}, safe={c.safe_to_store}")
        print(f"    evidence={c.evidence}, tags={c.tags}")
    if not candidates:
        print("  (no candidates)")
    if args.json:
        print("\n--- JSON ---")
        print(json.dumps([c.to_dict() for c in candidates], indent=2))


def cmd_capture(args):
    """Capture memories from message/response, writing to temp or specified base path."""
    base = args.base_path or tempfile.mkdtemp(prefix="weslr_mem_capture_")
    print(f"Using base path: {base}")

    identity_meta = {
        "is_verified": bool(args.verified),
        "known_user_status": args.identity_status or "unknown",
        "sender_identity": args.user_id,
    }

    result = safe_capture_memories_from_turn(
        args.message,
        args.response or "",
        {"project_id": args.project_id},
        identity_meta,
        base_path=base if not args.no_write else None,
    )

    print(f"Attempted: {result.attempted}")
    print(f"Captured: {result.captured}")
    print(f"Records created: {result.records_created}")
    print(f"Candidates considered: {result.candidates_considered}")
    print(f"Scope used: {result.scope_used}")
    print(f"Skipped reason: {result.skipped_reason}")

    if result.captured and not args.no_write:
        print(f"\nMemories written to: {base}")
        print(f"Run: python3 -m weslr.commands.memory_capture_commands list --base-path {base} --entity-type project --entity-id {args.project_id or 'weslr'}")


def cmd_list(args):
    """List memories for a given entity scope."""
    td = args.base_path or None
    try:
        memories = load_entity_memories(args.entity_type, args.entity_id, base_path=td)
        print(f"Entity: {args.entity_type}:{args.entity_id}")
        print(f"Memory records: {len(memories)}")
        for m in memories:
            print(f"  [{m.memory_id}] {m.timestamp}")
            print(f"    {m.summary}")
            print(f"    confidence={m.confidence}, access={m.access_level}, verified={m.verified}, provenance={m.provenance}")
            if m.tags:
                print(f"    tags={m.tags}")
    except FileNotFoundError:
        print(f"No memory file found for {args.entity_type}:{args.entity_id}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="WESLR Memory Capture Commands")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_inspect = sub.add_parser("inspect", help="Inspect candidates without writing")
    p_inspect.add_argument("--message", required=True, help="User message")
    p_inspect.add_argument("--response", default="", help="Agent response")
    p_inspect.add_argument("--verified", action="store_true", help="Identity is verified")
    p_inspect.add_argument("--identity-status", default=None, help="e.g. channel_verified, unknown")
    p_inspect.add_argument("--user-id", default=None, help="Sender user ID")
    p_inspect.add_argument("--project-id", default=None, help="Project ID")
    p_inspect.add_argument("--json", action="store_true", help="Also print JSON")

    p_capture = sub.add_parser("capture", help="Capture memories to temp dir or --base-path")
    p_capture.add_argument("--message", required=True, help="User message")
    p_capture.add_argument("--response", default="", help="Agent response")
    p_capture.add_argument("--verified", action="store_true", help="Identity is verified")
    p_capture.add_argument("--identity-status", default=None, help="e.g. channel_verified")
    p_capture.add_argument("--user-id", default=None, help="Sender user ID")
    p_capture.add_argument("--project-id", default=None, help="Project ID")
    p_capture.add_argument("--base-path", default=None, help="Base path for memories")
    p_capture.add_argument("--no-write", action="store_true", help="Inspect only, don't write")

    p_list = sub.add_parser("list", help="List memories for an entity scope")
    p_list.add_argument("--entity-type", required=True, help="e.g. project, person")
    p_list.add_argument("--entity-id", required=True, help="Entity ID")
    p_list.add_argument("--base-path", default=None, help="Base path (required if not using default ~/.weslr)")

    args = parser.parse_args()

    if args.cmd == "inspect":
        cmd_inspect(args)
    elif args.cmd == "capture":
        cmd_capture(args)
    elif args.cmd == "list":
        cmd_list(args)


if __name__ == "__main__":
    main()
