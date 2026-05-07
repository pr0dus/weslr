"""
WESLR Entity Memory CLI

Usage:
    python3 -m weslr.commands.entity_memory_commands <command> [options]

Commands:
    add         Add a memory record to an entity scope
    list        List memory records for an entity scope
    namespaces  List all entity memory namespaces present
    summarize   Summarize memories for an entity scope
    relate      Create a person-to-entity relationship
    relationships  List relationships for a person or entity
    scopes      Show memory scopes for a given identity status

All commands support:
    --base-path <memory_base_path>    default: ~/.weslr/memory
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.entity_memory import (
    append_entity_memory,
    create_memory_record,
    create_relationship,
    entity_memory_path,
    format_memory_response,
    list_entity_memory_namespaces,
    load_entity_memories,
    load_relationships,
    make_entity_id,
    person_memory_id,
    resolve_memory_scopes,
    resolve_person_memberships,
    save_relationship,
    summarize_memory_records,
    AccessLevel,
    EntityType,
    RelationshipType,
    RoleType,
)
from weslr.user_profile import load_user_profile


def _base_path(args):
    p = getattr(args, "base_path", None)
    if p:
        return p
    return None  # uses default in entity_memory.py


def cmd_add(args):
    entity_type = getattr(args, "entity_type", None)
    entity_id = getattr(args, "entity_id", None)
    summary = getattr(args, "summary", None)

    if not entity_type or not entity_id or not summary:
        print("Error: --entity-type, --entity-id, and --summary are required")
        sys.exit(1)

    record = create_memory_record(
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        source=getattr(args, "source", "operator") or "operator",
        access_level=getattr(args, "access_level", None) or AccessLevel.PRIVATE.value,
        tags=getattr(args, "tags", []) or [],
        confidence=float(getattr(args, "confidence", 0.5)),
        verified=bool(getattr(args, "verified", False)),
    )
    append_entity_memory(record, base_path=_base_path(args))
    print(f"Memory record added: {record.memory_id} for {entity_type}/{entity_id}")
    print(f"  summary: {summary[:80]}")


def cmd_list(args):
    entity_type = getattr(args, "entity_type", None)
    entity_id = getattr(args, "entity_id", None)

    if not entity_type or not entity_id:
        print("Error: --entity-type and --entity-id are required")
        sys.exit(1)

    limit = int(getattr(args, "limit", 20) or 20)
    records = load_entity_memories(entity_type, entity_id, base_path=_base_path(args), limit=limit)

    if not records:
        print(f"No memories found for {entity_type}/{entity_id}")
        return

    print(f"=== {entity_type}/{entity_id} — {len(records)} records ===")
    for r in records:
        verified = "✓" if r.verified else "✗"
        print(f"  [{verified}] {r.timestamp[:10]} | {r.summary[:70]}")


def cmd_namespaces(args):
    namespaces = list_entity_memory_namespaces(base_path=_base_path(args))

    if not namespaces:
        print("No entity memory namespaces found.")
        return

    print(f"=== Entity Memory Namespaces ({len(namespaces)}) ===")
    for ns in namespaces:
        print(f"  {ns['entity_type']}/{ns['entity_id']}: {ns['record_count']} records")


def cmd_summarize(args):
    entity_type = getattr(args, "entity_type", None)
    entity_id = getattr(args, "entity_id", None)

    if not entity_type or not entity_id:
        print("Error: --entity-type and --entity-id are required")
        sys.exit(1)

    records = load_entity_memories(entity_type, entity_id, base_path=_base_path(args), limit=50)
    summary = summarize_memory_records(records)

    if not records:
        print(f"No memories found for {entity_type}/{entity_id}")
        return

    resp = format_memory_response(summary, f"{entity_type} {entity_id}")
    print(resp)
    print(f"\nDetails: {summary['count']} records, {summary['verified_count']} verified")
    print(f"Tags: {', '.join(summary['tags'][:10])}")


def cmd_relate(args):
    person_id = getattr(args, "person_id", None)
    entity_type = getattr(args, "entity_type", None)
    entity_id = getattr(args, "entity_id", None)
    role = getattr(args, "role", None)
    relationship_type = getattr(args, "relationship_type", None)

    if not all([person_id, entity_type, entity_id, role, relationship_type]):
        print("Error: --person-id, --entity-type, --entity-id, --role, --relationship-type are required")
        sys.exit(1)

    rel = create_relationship(
        person_id=person_id,
        entity_type=entity_type,
        entity_id=entity_id,
        role=role,
        relationship_type=relationship_type,
        entity_display_name=getattr(args, "display_name", None) or entity_id,
        strength=getattr(args, "strength", "medium") or "medium",
        verified=bool(getattr(args, "verified", False)),
        confidence=float(getattr(args, "confidence", 0.4)),
    )
    save_relationship(rel, base_path=_base_path(args))
    print(f"Relationship created: {rel.relationship_id}")
    print(f"  {person_id} —[{role}]→ {entity_type}/{entity_id}")
    print(f"  verified={rel.verified}, confidence={rel.confidence:.2f}")


def cmd_relationships(args):
    person_id = getattr(args, "person_id", None)
    entity_id = getattr(args, "entity_id", None)

    rels = load_relationships(person_id=person_id, entity_id=entity_id, base_path=_base_path(args))

    if not rels:
        print("No relationships found.")
        return

    print(f"=== Relationships ({len(rels)}) ===")
    for r in rels:
        verified = "✓" if r.verified else "✗"
        print(f"  [{verified}] {r.person_id} —[{r.role}]→ {r.entity_type}/{r.entity_display_name}")
        print(f"           relationship_type={r.relationship_type}, conf={r.confidence:.2f}")


def cmd_scopes(args):
    identity_status = getattr(args, "identity_status", "onboarded_unverified")
    user_id = getattr(args, "user_id", "test_user")
    primary_projects = getattr(args, "primary_projects", "") or ""

    projects = [p.strip() for p in primary_projects.split(",") if p.strip()] if primary_projects else []

    rels = resolve_person_memberships(user_id, base_path=_base_path(args))
    scopes = resolve_memory_scopes(
        identity_status=identity_status,
        user_id=user_id,
        primary_projects=projects,
        memberships=rels,
    )

    print(f"=== Memory scopes for identity_status={identity_status}, user_id={user_id} ===")
    for name, meta in scopes.items():
        print(f"  {name}: {meta['entity_type']}/{meta['entity_id']} [{meta['access_level']}]")


def main():
    parser = argparse.ArgumentParser(description="WESLR Entity Memory CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add memory record to an entity")
    p_add.add_argument("--entity-type", required=True)
    p_add.add_argument("--entity-id", required=True)
    p_add.add_argument("--summary", required=True)
    p_add.add_argument("--source", default="operator")
    p_add.add_argument("--access-level", default=None)
    p_add.add_argument("--tags", nargs="*", default=[])
    p_add.add_argument("--confidence", default="0.5")
    p_add.add_argument("--verified", action="store_true")
    p_add.add_argument("--base-path", default=None)

    p_list = sub.add_parser("list", help="List memory records for an entity")
    p_list.add_argument("--entity-type", required=True)
    p_list.add_argument("--entity-id", required=True)
    p_list.add_argument("--limit", default="20")
    p_list.add_argument("--base-path", default=None)

    p_ns = sub.add_parser("namespaces", help="List all entity memory namespaces")
    p_ns.add_argument("--base-path", default=None)

    p_sum = sub.add_parser("summarize", help="Summarize memories for an entity")
    p_sum.add_argument("--entity-type", required=True)
    p_sum.add_argument("--entity-id", required=True)
    p_sum.add_argument("--base-path", default=None)

    p_rel = sub.add_parser("relate", help="Create a person-to-entity relationship")
    p_rel.add_argument("--person-id", required=True)
    p_rel.add_argument("--entity-type", required=True)
    p_rel.add_argument("--entity-id", required=True)
    p_rel.add_argument("--role", required=True)
    p_rel.add_argument("--relationship-type", required=True)
    p_rel.add_argument("--display-name", default=None)
    p_rel.add_argument("--strength", default="medium")
    p_rel.add_argument("--verified", action="store_true")
    p_rel.add_argument("--confidence", default="0.4")
    p_rel.add_argument("--base-path", default=None)

    p_rels = sub.add_parser("relationships", help="List relationships")
    p_rels.add_argument("--person-id", default=None)
    p_rels.add_argument("--entity-id", default=None)
    p_rels.add_argument("--base-path", default=None)

    p_scopes = sub.add_parser("scopes", help="Show memory scopes for identity status")
    p_scopes.add_argument("--identity-status", default="onboarded_unverified")
    p_scopes.add_argument("--user-id", default="test_user")
    p_scopes.add_argument("--primary-projects", default="")
    p_scopes.add_argument("--base-path", default=None)

    args = parser.parse_args()
    dispatch = {
        "add": cmd_add,
        "list": cmd_list,
        "namespaces": cmd_namespaces,
        "summarize": cmd_summarize,
        "relate": cmd_relate,
        "relationships": cmd_relationships,
        "scopes": cmd_scopes,
    }
    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
