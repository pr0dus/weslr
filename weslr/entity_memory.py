"""
WESLR Entity Memory Namespaces

Bounded entity-scoped memory for persons, families, companies, institutions,
teams, departments, and projects.

Design principles:
- Memory is scoped to an entity, not only to a user.
- A person can belong to many entities simultaneously.
- Membership/role must be explicit and evidence-scored.
- Access depends on verified identity + verified role, not just profile existence.
- Personal, shared, institutional, and project memory are kept separate.
- No LLM. No raw memory dumps. Bounded summaries only.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_WESLR_HOME = "/data/data/com.termux/files/home/.weslr"
MEMORY_DIR = "memory"
ENTITIES_DIR = "entities"
RELATIONSHIPS_SUBDIR = "_relationships"
RELATIONSHIPS_FILE = "relationships.jsonl"
MEMORY_FILE = "memory.jsonl"
RELATIONSHIPS_VERSION = 1
MEMORY_RECORD_VERSION = 1

# Entity types
class EntityType(str, Enum):
    PERSON = "person"
    FAMILY = "family"
    HOUSEHOLD = "household"
    COMPANY = "company"
    INSTITUTION = "institution"
    TEAM = "team"
    DEPARTMENT = "department"
    PROJECT = "project"
    SYSTEM = "system"
    UNKNOWN = "unknown"


# Access levels
class AccessLevel(str, Enum):
    PRIVATE = "private"          # only the owning person
    SHARED = "shared"           # group/institutional members
    REPRESENTATIVE = "representative"  # verified rep with specific scope
    PUBLIC = "public"           # anyone
    OPERATOR_ONLY = "operator_only"   # operator only
    ROLE_RESTRICTED = "role_restricted"  # role-dependent access


# Relationship types
class RelationshipType(str, Enum):
    MEMBER_OF = "member_of"
    WORKS_FOR = "works_for"
    OWNS = "owns"
    LEADS = "leads"
    REPRESENTS = "represents"
    MANAGES = "manages"
    BELONGS_TO_HOUSEHOLD = "belongs_to_household"
    PART_OF_FAMILY = "part_of_family"
    CONTRIBUTES_TO_PROJECT = "contributes_to_project"
    OWNS_PROJECT = "owns_project"
    DEPARTMENT_OF = "department_of"
    TEAM_OF = "team_of"
    AFFILIATED_WITH = "affiliated_with"
    VERIFIED_REPRESENTATIVE_OF = "verified_representative_of"
    UNKNOWN = "unknown"


# Role types
class RoleType(str, Enum):
    OWNER = "owner"
    CEO = "ceo"
    OPERATOR = "operator"
    ADMIN = "admin"
    MEMBER = "member"
    EMPLOYEE = "employee"
    REPRESENTATIVE = "representative"
    CONTRACTOR = "contractor"
    ADVISOR = "advisor"
    VIEWER = "viewer"
    GUARDIAN = "guardian"
    PARENT = "parent"
    CHILD = "child"
    SPOUSE = "spouse"
    SIBLING = "sibling"
    HOUSEHOLD_MEMBER = "household_member"
    PROJECT_OWNER = "project_owner"
    PROJECT_CONTRIBUTOR = "project_contributor"
    UNKNOWN = "unknown"


# ── ID generation ──────────────────────────────────────────────────────────

def make_entity_id(name: str, entity_type: str) -> str:
    """
    Generate a stable entity_id from a name and type.
    Lowercase, hyphenated, max 40 chars.
    """
    base = f"{entity_type}_{name}"
    return base.lower().replace(" ", "-").replace("_", "-")[:40]


def person_memory_id(user_id: str) -> str:
    return make_entity_id(user_id, EntityType.PERSON.value)


# ── Namespace paths ────────────────────────────────────────────────────────

def entity_memory_base(base_path: Optional[str] = None) -> str:
    if base_path:
        return base_path
    return os.path.join(DEFAULT_WESLR_HOME, MEMORY_DIR, ENTITIES_DIR)


def entity_memory_path(
    entity_type: str,
    entity_id: str,
    base_path: Optional[str] = None,
) -> str:
    """Return path to entity's memory.jsonl file."""
    base = entity_memory_base(base_path)
    return os.path.join(base, entity_type, entity_id, MEMORY_FILE)


def relationships_path(base_path: Optional[str] = None) -> str:
    """Return path to relationships.jsonl file."""
    base = entity_memory_base(base_path)
    return os.path.join(base, RELATIONSHIPS_SUBDIR, RELATIONSHIPS_FILE)


# ── Memory record ───────────────────────────────────────────────────────────

@dataclass
class MemoryRecord:
    """One memory record in an entity's memory log."""
    memory_id: str = ""
    timestamp: str = ""
    entity_type: str = ""
    entity_id: str = ""
    scope: str = ""
    access_level: str = AccessLevel.PRIVATE.value
    source: str = ""
    summary: str = ""
    details: Optional[str] = None
    tags: list = field(default_factory=list)
    confidence: float = 0.5
    verified: bool = False
    created_by: str = ""
    related_person_ids: list = field(default_factory=list)
    related_group_ids: list = field(default_factory=list)
    related_entity_ids: list = field(default_factory=list)
    project_ids: list = field(default_factory=list)
    provenance: str = ""
    retention_policy: str = "default"
    memory_version: int = MEMORY_RECORD_VERSION

    def to_dict(self) -> dict:
        d = asdict(self)
        d["access_level"] = self.access_level
        return d

    @staticmethod
    def from_dict(d: dict) -> "MemoryRecord":
        # Strip unknown fields gracefully
        known = {
            k: v for k, v in d.items()
            if k in (
                "memory_id", "timestamp", "entity_type", "entity_id", "scope",
                "access_level", "source", "summary", "details", "tags",
                "confidence", "verified", "created_by", "related_person_ids",
                "related_group_ids", "related_entity_ids", "project_ids",
                "provenance", "retention_policy", "memory_version",
            )
        }
        return MemoryRecord(**known)


def create_memory_record(
    entity_type: str,
    entity_id: str,
    summary: str,
    scope: str = "default",
    access_level: str = AccessLevel.PRIVATE.value,
    source: str = "operator",
    details: Optional[str] = None,
    tags: Optional[list] = None,
    confidence: float = 0.5,
    verified: bool = False,
    created_by: str = "operator",
    related_person_ids: Optional[list] = None,
    related_group_ids: Optional[list] = None,
    related_entity_ids: Optional[list] = None,
    project_ids: Optional[list] = None,
    provenance: str = "explicit",
    retention_policy: str = "default",
) -> MemoryRecord:
    """Create a new memory record with generated ID and timestamp."""
    now = datetime.now(timezone.utc).isoformat()
    return MemoryRecord(
        memory_id=uuid.uuid4().hex[:16],
        timestamp=now,
        entity_type=entity_type,
        entity_id=entity_id,
        scope=scope,
        access_level=access_level,
        source=source,
        summary=summary,
        details=details,
        tags=tags or [],
        confidence=confidence,
        verified=verified,
        created_by=created_by,
        related_person_ids=related_person_ids or [],
        related_group_ids=related_group_ids or [],
        related_entity_ids=related_entity_ids or [],
        project_ids=project_ids or [],
        provenance=provenance,
        retention_policy=retention_policy,
    )


# ── Memory write / read ─────────────────────────────────────────────────────

def append_entity_memory(
    record: MemoryRecord,
    base_path: Optional[str] = None,
) -> None:
    """Append a memory record to an entity's memory.jsonl file."""
    path = entity_memory_path(
        record.entity_type,
        record.entity_id,
        base_path=base_path,
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record.to_dict()) + "\n")


def load_entity_memories(
    entity_type: str,
    entity_id: str,
    base_path: Optional[str] = None,
    limit: int = 50,
    access_level: Optional[str] = None,
) -> list[MemoryRecord]:
    """
    Load memory records for an entity, newest first.
    Optionally filter by access_level.
    """
    path = entity_memory_path(entity_type, entity_id, base_path=base_path)
    if not os.path.isfile(path):
        return []

    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                rec = MemoryRecord.from_dict(d)
                if access_level and rec.access_level != access_level:
                    continue
                records.append(rec)
            except Exception:
                continue

    # Newest first, respect limit
    records.sort(key=lambda r: r.timestamp, reverse=True)
    return records[:limit]


# ── Summarize ────────────────────────────────────────────────────────────────

def summarize_memory_records(records: list[MemoryRecord]) -> dict:
    """
    Produce a bounded structured summary from a list of memory records.
    No raw dump. Tags, topics, counts, confidence bands.
    """
    if not records:
        return {
            "count": 0,
            "scope": "none",
            "summaries": [],
            "tags": [],
            "topics": [],
            "confidence_bands": {"high": 0, "medium": 0, "low": 0},
        }

    high_conf = sum(1 for r in records if r.confidence >= 0.75)
    medium_conf = sum(1 for r in records if 0.4 <= r.confidence < 0.75)
    low_conf = sum(1 for r in records if r.confidence < 0.4)

    all_tags: list[str] = []
    all_summaries: list[str] = []
    for r in records:
        if r.summary:
            all_summaries.append(r.summary)
        if r.tags:
            all_tags.extend(r.tags)

    # Deduplicate and limit tags
    unique_tags = list(dict.fromkeys(all_tags))[:20]

    return {
        "count": len(records),
        "scope": records[0].entity_type if records else "unknown",
        "summaries": all_summaries[:10],
        "tags": unique_tags,
        "topics": list(dict.fromkeys(
            t for t in unique_tags if len(t) < 30
        ))[:10],
        "confidence_bands": {
            "high": high_conf,
            "medium": medium_conf,
            "low": low_conf,
        },
        "verified_count": sum(1 for r in records if r.verified),
    }


def format_memory_response(
    summary: dict,
    scope_label: str,
    person_name: Optional[str] = None,
) -> str:
    """
    Format a bounded memory response string.
    No raw dumps. No file references. Scoped to the entity.
    """
    count = summary.get("count", 0)
    if count == 0:
        return f"I have no stored memories for {scope_label} yet."

    tags = summary.get("tags", [])
    topics = summary.get("topics", [])
    verified = summary.get("verified_count", 0)

    parts = []
    if person_name:
        parts.append(f"From {person_name}'s {scope_label} memory:")

    if tags:
        parts.append(f"I recall: {', '.join(tags[:5])}")

    if topics and len(topics) > len(tags[:5]):
        remaining = [t for t in topics if t not in tags[:5]]
        if remaining:
            parts.append(f"Topics covered: {', '.join(remaining[:5])}")

    parts.append(f"[{count} memory record{'s' if count != 1 else ''}, "
                 f"{verified} verified]")

    return " ".join(parts)


# ── Relationship ────────────────────────────────────────────────────────────

@dataclass
class EntityRelationship:
    """Link between a person and an entity, with role and evidence."""
    relationship_id: str = ""
    person_id: str = ""
    entity_type: str = ""
    entity_id: str = ""
    entity_display_name: str = ""
    role: str = RoleType.UNKNOWN.value
    relationship_type: str = RelationshipType.UNKNOWN.value
    strength: str = "medium"   # strong / medium / weak
    verified: bool = False
    confidence: float = 0.0
    source: str = ""
    created_at: str = ""
    updated_at: str = ""
    evidence: list = field(default_factory=list)
    limitations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "EntityRelationship":
        known = {
            k: v for k, v in d.items()
            if k in (
                "relationship_id", "person_id", "entity_type", "entity_id",
                "entity_display_name", "role", "relationship_type", "strength",
                "verified", "confidence", "source", "created_at", "updated_at",
                "evidence", "limitations",
            )
        }
        return EntityRelationship(**known)


def create_relationship(
    person_id: str,
    entity_type: str,
    entity_id: str,
    role: str,
    relationship_type: str,
    entity_display_name: str = "",
    strength: str = "medium",
    verified: bool = False,
    confidence: float = 0.0,
    source: str = "explicit_operator",
    evidence: Optional[list] = None,
    limitations: Optional[list] = None,
) -> EntityRelationship:
    """Create a new relationship record."""
    now = datetime.now(timezone.utc).isoformat()
    return EntityRelationship(
        relationship_id=uuid.uuid4().hex[:16],
        person_id=person_id,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_display_name=entity_display_name or entity_id,
        role=role,
        relationship_type=relationship_type,
        strength=strength,
        verified=verified,
        confidence=confidence,
        source=source,
        created_at=now,
        updated_at=now,
        evidence=evidence or [],
        limitations=limitations or [],
    )


def save_relationship(
    relationship: EntityRelationship,
    base_path: Optional[str] = None,
) -> None:
    """Append a relationship record to the relationships file."""
    path = relationships_path(base_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(relationship.to_dict()) + "\n")


def load_relationships(
    person_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    base_path: Optional[str] = None,
) -> list[EntityRelationship]:
    """
    Load relationships, optionally filtered by person_id or entity_id.
    """
    path = relationships_path(base_path)
    if not os.path.isfile(path):
        return []

    results = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                rel = EntityRelationship.from_dict(d)
                if person_id and rel.person_id != person_id:
                    continue
                if entity_id and rel.entity_id != entity_id:
                    continue
                results.append(rel)
            except Exception:
                continue

    results.sort(key=lambda r: r.updated_at, reverse=True)
    return results


def resolve_person_memberships(
    person_id: str,
    base_path: Optional[str] = None,
) -> list[EntityRelationship]:
    """Get all entity memberships for a person."""
    return load_relationships(person_id=person_id, base_path=base_path)


# ── Access control ─────────────────────────────────────────────────────────

def can_access_memory_scope(
    identity_status: str,
    access_level: str,
    requested_scope: Optional[str] = None,
    role_evidence: Optional[list[EntityRelationship]] = None,
) -> tuple[bool, str]:
    """
    Check whether the current identity can access memory at a given access level.

    Returns (allowed, reason).

    Rules:
    - PRIVATE: requires channel_verified and matching person_id
    - SHARED: requires verified relationship to the entity
    - REPRESENTATIVE: requires verified rep role
    - OPERATOR_ONLY: requires operator role
    - ROLE_RESTRICTED: requires verified role in role_evidence
    - PUBLIC: always allowed (no identity required)
    """
    if access_level == AccessLevel.PUBLIC.value:
        return (True, "public access")

    if identity_status == "unknown":
        return (False, "identity not established — cannot access scoped memory")

    if access_level == AccessLevel.OPERATOR_ONLY.value:
        if identity_status not in ("channel_verified", "device_verified", "test_verified"):
            return (False, "operator-only memory requires verified channel")
        return (True, "operator access granted")

    if access_level == AccessLevel.PRIVATE.value:
        # PRIVATE always requires channel_verified
        if identity_status != "channel_verified":
            return (False, "private memory requires verified channel")
        return (True, "private memory access granted")

    if access_level in (AccessLevel.SHARED.value, AccessLevel.REPRESENTATIVE.value, AccessLevel.ROLE_RESTRICTED.value):
        if not role_evidence:
            return (False, f"{access_level} memory requires verified role evidence")
        # Must have at least one verified relationship of the right type
        verified_rels = [r for r in role_evidence if r.verified]
        if not verified_rels:
            return (False, f"{access_level} memory requires verified relationship")
        return (True, "role-scoped memory access granted")

    # Fallback: reject
    return (False, f"unknown access level: {access_level}")


# ── Memory scope resolution ─────────────────────────────────────────────────

def resolve_memory_scopes(
    identity_status: str,
    user_id: str,
    primary_projects: Optional[list[str]] = None,
    memberships: Optional[list[EntityRelationship]] = None,
) -> dict[str, dict]:
    """
    Resolve all memory scopes available to the current identity.
    Returns dict of scope_name -> scope_metadata.

    Scopes considered:
    - personal: own person memory (channel_verified only)
    - project_<name>: each project in primary_projects
    - family_<id>, company_<id>, etc.: from verified memberships
    """
    scopes: dict[str, dict] = {}

    # Personal scope: channel_verified only
    if identity_status == "channel_verified":
        scopes["personal"] = {
            "entity_type": EntityType.PERSON.value,
            "entity_id": person_memory_id(user_id),
            "access_level": AccessLevel.PRIVATE.value,
            "scope_label": "personal",
        }

    # Project scopes: operator_only by default
    for project_id in (primary_projects or []):
        scopes[f"project_{project_id}"] = {
            "entity_type": EntityType.PROJECT.value,
            "entity_id": make_entity_id(project_id, EntityType.PROJECT.value),
            "access_level": AccessLevel.OPERATOR_ONLY.value,
            "scope_label": f"project {project_id}",
        }

    # Entity scopes from verified memberships
    for rel in (memberships or []):
        if not rel.verified:
            continue
        scopes[f"{rel.entity_type}_{rel.entity_id}"] = {
            "entity_type": rel.entity_type,
            "entity_id": rel.entity_id,
            "access_level": AccessLevel.SHARED.value,
            "scope_label": f"{rel.entity_type} {rel.entity_display_name}",
            "role": rel.role,
        }

    return scopes


def load_scoped_memories(
    scopes: dict[str, dict],
    base_path: Optional[str] = None,
    limit_per_scope: int = 10,
) -> dict[str, dict]:
    """
    Load memories for all resolved scopes.
    Returns scope_name -> {summary, records_count, access_ok}.
    """
    results = {}
    for scope_name, scope_meta in scopes.items():
        entity_type = scope_meta["entity_type"]
        entity_id = scope_meta["entity_id"]
        access_level = scope_meta["access_level"]

        # Skip operator-only if not verified channel
        # (already filtered in resolve_memory_scopes)
        records = load_entity_memories(
            entity_type,
            entity_id,
            base_path=base_path,
            limit=limit_per_scope,
        )
        summary = summarize_memory_records(records)
        results[scope_name] = {
            "summary": summary,
            "records_count": len(records),
            "access_ok": True,
            "scope_label": scope_meta.get("scope_label", scope_name),
        }

    return results


# ── Namespace listing ───────────────────────────────────────────────────────

def list_entity_memory_namespaces(
    base_path: Optional[str] = None,
) -> list[dict]:
    """
    List all entity memory namespaces present.
    Returns list of {entity_type, entity_id, record_count}.
    """
    base = entity_memory_base(base_path)
    result = []
    if not os.path.isdir(base):
        return result

    for entity_type in os.listdir(base):
        type_dir = os.path.join(base, entity_type)
        if not os.path.isdir(type_dir):
            continue
        for entity_id in os.listdir(type_dir):
            entity_dir = os.path.join(type_dir, entity_id)
            if not os.path.isdir(entity_dir):
                continue
            memory_file = os.path.join(entity_dir, MEMORY_FILE)
            count = 0
            if os.path.isfile(memory_file):
                with open(memory_file) as f:
                    count = sum(1 for line in f if line.strip())
            result.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "record_count": count,
            })

    result.sort(key=lambda x: (x["entity_type"], x["entity_id"]))
    return result
