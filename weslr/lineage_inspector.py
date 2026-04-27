"""Lineage Inspector V1 — Artifact Lineage Inspection Surface.

Smallest safe first slice: read-only inspection of artifact lineage fields.
No graph engine. No traversal. No inference beyond explicit fields.

Design: docs/LINEAGE_AWARE_ARTIFACT_INSPECTION_V1.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

SCHEMA_VERSION = "1.0"


@dataclass
class ArtifactLineageInspection:
    """Structured lineage inspection output for a single artifact.

    Fields:
        artifact_id: ID of the inspected artifact.
        lineage_status: Classification derived from explicit fields only.
            - "root": artifact has no parents (generation=0, self as root)
            - "derived": artifact has parents, root_artifact_id is set
            - "incomplete": parent refs present but root_artifact_id is null
            - "legacy_unknown": artifact predates lineage fields entirely
        parent_artifact_ids: List of direct parent IDs; empty for root.
        root_artifact_id: Topmost ancestor; None if unknown or incomplete.
        generation: Distance from root; None if unknown.
        thread_ids: Thread/session context; empty if none.
        lineage_complete: True when status is root|derived and root is set.
        notes: Human-readable lineage note.
        schema_version: Output schema version for forward compatibility.
    """

    artifact_id: str
    lineage_status: str  # Literal["root", "derived", "incomplete", "legacy_unknown"]
    parent_artifact_ids: list[str] = field(default_factory=list)
    root_artifact_id: Optional[str] = None
    generation: Optional[int] = None
    thread_ids: list[str] = field(default_factory=list)
    lineage_complete: bool = False
    notes: str = ""
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "artifact_id": self.artifact_id,
            "lineage_status": self.lineage_status,
            "parent_artifact_ids": self.parent_artifact_ids,
            "root_artifact_id": self.root_artifact_id,
            "generation": self.generation,
            "thread_ids": self.thread_ids,
            "lineage_complete": self.lineage_complete,
            "notes": self.notes,
            "schema_version": self.schema_version,
        }


def inspect_artifact_lineage(
    artifact: dict,
    thread_ids: Optional[list[str]] = None,
) -> ArtifactLineageInspection:
    """Inspect lineage fields of a single artifact dict.

    Reads explicit lineage fields only. Does not traverse, infer, or mutate.

    Classification rules (in priority order):
        1. legacy_unknown  — "generation" field absent entirely
        2. incomplete       — parent_artifact_ids non-empty but root_artifact_id is null
        3. root             — parent_artifact_ids empty AND generation == 0
        4. derived          — parent_artifact_ids non-empty AND root_artifact_id set

    Args:
        artifact: Artifact dict with lineage fields (parent_artifact_ids,
                  root_artifact_id, generation). May be partial.
        thread_ids: Optional thread/session context list.

    Returns:
        ArtifactLineageInspection with classified status and structured output.
    """
    artifact_id = artifact.get("artifact_id", "unknown")
    parent_ids = artifact.get("parent_artifact_ids") or []
    root_id = artifact.get("root_artifact_id")
    generation = artifact.get("generation")

    # Detect legacy (no generation field at all — field absent, not just None)
    has_generation_field = "generation" in artifact

    if not has_generation_field:
        return ArtifactLineageInspection(
            artifact_id=artifact_id,
            lineage_status="legacy_unknown",
            parent_artifact_ids=[],
            root_artifact_id=None,
            generation=None,
            thread_ids=thread_ids or [],
            lineage_complete=False,
            notes="Artifact predates lineage fields; parent/root/generation unknown.",
        )

    # Read explicit lineage_intent if present
    lineage_intent = artifact.get("lineage_intent")

    # Explicit root intent — return immediately
    if lineage_intent == "root":
        return ArtifactLineageInspection(
            artifact_id=artifact_id,
            lineage_status="root",
            parent_artifact_ids=[],
            root_artifact_id=artifact_id,
            generation=0,
            thread_ids=thread_ids or [],
            lineage_complete=True,
            notes="Explicit root intent.",
        )

    # Detect incomplete: parent refs present but root_artifact_id absent
    # Must run before derived classification
    if parent_ids and root_id is None:
        return ArtifactLineageInspection(
            artifact_id=artifact_id,
            lineage_status="incomplete",
            parent_artifact_ids=list(parent_ids),
            root_artifact_id=None,
            generation=int(generation) if generation is not None else None,
            thread_ids=thread_ids or [],
            lineage_complete=False,
            notes="Parent references present but root_artifact_id is unset; lineage incomplete.",
        )

    # Explicit derived intent — return after incomplete check passes
    if lineage_intent == "derived":
        return ArtifactLineageInspection(
            artifact_id=artifact_id,
            lineage_status="derived",
            parent_artifact_ids=list(parent_ids),
            root_artifact_id=root_id,
            generation=int(generation) if generation is not None else None,
            thread_ids=thread_ids or [],
            lineage_complete=True,
            notes="Explicit derived intent.",
        )

    # Classify root vs derived (no explicit intent — legacy behavior)
    if not parent_ids and generation == 0:
        return ArtifactLineageInspection(
            artifact_id=artifact_id,
            lineage_status="root",
            parent_artifact_ids=[],
            root_artifact_id=artifact_id,
            generation=0,
            thread_ids=thread_ids or [],
            lineage_complete=True,
            notes="Root artifact.",
        )

    # derived (legacy fallback)
    return ArtifactLineageInspection(
        artifact_id=artifact_id,
        lineage_status="derived",
        parent_artifact_ids=list(parent_ids),
        root_artifact_id=root_id,
        generation=int(generation) if generation is not None else None,
        thread_ids=thread_ids or [],
        lineage_complete=True,
        notes="Derived from {} parent{}.".format(
            len(parent_ids), "s" if len(parent_ids) != 1 else ""
        ),
    )


def inspect_artifact_lineage_by_id(
    artifact_id: str,
    artifact_store_module: Optional[object] = None,
) -> Optional[ArtifactLineageInspection]:
    """Inspect artifact lineage by ID using the artifact store.

    Args:
        artifact_id: The artifact ID to look up.
        artifact_store_module: Optional artifact_store module reference.
            If omitted, imports from weslr.artifact_store locally.

    Returns:
        ArtifactLineageInspection or None if artifact not found.
    """
    if artifact_store_module is None:
        from weslr import artifact_store
    else:
        artifact_store = artifact_store_module

    artifact = artifact_store.get_artifact(artifact_id)
    if artifact is None:
        return None

    thread_ids = artifact.get("thread_ids")
    return inspect_artifact_lineage(artifact, thread_ids=thread_ids)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python lineage_inspector.py <artifact-id> [--store <path>]")
        print("       python lineage_inspector.py --inspect-json <json-string>")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "--inspect-json" and len(sys.argv) >= 3:
        try:
            artifact = json.loads(sys.argv[2])
            result = inspect_artifact_lineage(artifact)
            print(json.dumps(result.to_dict(), indent=2))
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            sys.exit(1)

    else:
        artifact_id = cmd
        result = inspect_artifact_lineage_by_id(artifact_id)
        if result is None:
            print("Artifact not found.")
            sys.exit(1)
        else:
            print(json.dumps(result.to_dict(), indent=2))
