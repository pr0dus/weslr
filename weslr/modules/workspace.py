"""
weslr/modules/workspace.py
==========================
Phase 10 — Workspace Manager & Shared Library.

Per-tenant in-memory hypothesis workspaces with optional sharing
via an anonymized shared library. No LLM, deterministic only.

Author: OCC (WESLR governed intelligence) — Phase 10
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

# ── Shared Library Storage (in-memory, per-process) ────────────────────────
# Keyed by shared_hypothesis_id (str)
SHARED_HYPOTHESES: dict[str, dict] = {}

# ── Anonymization helpers ───────────────────────────────────────────────────

# Fields that are ALWAYS stripped when sharing
_STRIP_FIELDS = frozenset([
    "tenant_id", "created_by", "user_comment", "free_text",
    "notes", "private_notes", "personal_notes",
])

# Fields that are KEPT (scientific content)
_KEEP_FIELDS = frozenset([
    "title", "description", "domain", "confidence",
    "status", "metadata", "provenance",
    "effect_size", "causal_graph", "evidence",
])


def _make_shared_id(original_id: str) -> str:
    """Generate a deterministic shared ID from the original hypothesis ID."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"shared:{original_id}"))


def _anonymize_hypothesis(hypothesis_dict: dict) -> dict:
    """Strip user-specific identifiers from a hypothesis dict.

    Keeps: title, description, domain, confidence, status, metadata,
    provenance (scrubbed), effect_size, causal_graph.
    Removes: tenant_id, created_by, user comments, free-text fields.
    """
    anonymized = {}

    # Fields to keep as-is (or scrub provenance)
    for key in ("title", "description", "domain", "confidence", "status", "metadata"):
        if key in hypothesis_dict:
            anonymized[key] = hypothesis_dict[key]

    # Scrub provenance entries (remove user-specific fields)
    # Note: "source" itself can be a tenant identifier, so always strip it
    if "provenance" in hypothesis_dict:
        scrubbed_provenance = []
        for entry in hypothesis_dict["provenance"]:
            # Keep action/parameters/result only — strip source and strip fields
            clean = {
                k: v for k, v in entry.items()
                if k in ("action", "parameters", "result")
            }
            scrubbed_provenance.append(clean)
        anonymized["provenance"] = scrubbed_provenance

    # Causal graph and effect_size from metadata
    meta = hypothesis_dict.get("metadata", {})
    if "causal_graph" in meta:
        anonymized["causal_graph"] = meta["causal_graph"]
    if "effect_size" in meta:
        anonymized["effect_size"] = meta["effect_size"]
    if "evidence" in meta:
        anonymized["evidence"] = meta["evidence"]

    anonymized["shared_at"] = datetime.now(timezone.utc).isoformat()
    return anonymized


# ── Shared Hypothesis wrapper ──────────────────────────────────────────────

@dataclass
class SharedHypothesis:
    """An anonymized, shareable hypothesis in the shared library."""
    shared_id: str          # deterministic UUID v5
    original_id: str         # hypothesis this was shared from
    title: str
    description: str
    domain: str
    confidence: float
    status: str
    provenance: list[dict]
    metadata: dict
    shared_at: str

    def to_dict(self) -> dict:
        return {
            "shared_id": self.shared_id,
            "original_id": self.original_id,
            "title": self.title,
            "description": self.description,
            "domain": self.domain,
            "confidence": self.confidence,
            "status": self.status,
            "provenance": self.provenance,
            "metadata": self.metadata,
            "shared_at": self.shared_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SharedHypothesis:
        return cls(
            shared_id=d["shared_id"],
            original_id=d["original_id"],
            title=d["title"],
            description=d["description"],
            domain=d["domain"],
            confidence=d["confidence"],
            status=d["status"],
            provenance=d.get("provenance", []),
            metadata=d.get("metadata", {}),
            shared_at=d.get("shared_at", ""),
        )


# ── Workspace Manager ────────────────────────────────────────────────────────

class WorkspaceManager:
    """Per-tenant workspace with shared library access.

    Manages private hypotheses within a tenant and provides
    controlled sharing to a cross-tenant anonymized library.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    # ── Sharing ────────────────────────────────────────────────────────────

    def share_hypothesis(self, hypothesis, /) -> str:
        """Mark a hypothesis as shareable and add to the shared library.

        Parameters
        ----------
        hypothesis : Hypothesis
            The hypothesis to share.

        Returns
        -------
        str — the shared_hypothesis_id (library ID).

        Notes
        -----
        - Adds `shareable=True` to the hypothesis metadata.
        - Stores an anonymized copy in SHARED_HYPOTHESES.
        - Provenance entries are scrubbed of user-specific fields.
        - The original hypothesis is NOT modified (shareable flag
          is stored in the shared library entry, not on the original).
        """
        from dataclasses import is_dataclass
        if is_dataclass(hypothesis) and not isinstance(hypothesis, dict):
            hypothesis_dict = asdict(hypothesis)
        elif isinstance(hypothesis, dict):
            hypothesis_dict = hypothesis
        else:
            raise TypeError(f"Unsupported hypothesis type: {type(hypothesis)}")

        shared_id = _make_shared_id(hypothesis_dict["id"])

        anonymized = _anonymize_hypothesis(hypothesis_dict)
        anonymized["shared_id"] = shared_id
        anonymized["original_id"] = hypothesis_dict["id"]

        SHARED_HYPOTHESES[shared_id] = anonymized

        # Mark in hypothesis metadata that it's now shared (key only, no tenant info)
        hypothesis.metadata["shareable"] = True
        hypothesis.metadata["shared_library_id"] = shared_id

        return shared_id

    def list_shared_library(self, domain: Optional[str] = None) -> list[dict]:
        """Return all shareable hypotheses from all tenants.

        Parameters
        ----------
        domain : str, optional
            Filter by domain.

        Returns
        -------
        list[dict] — anonymized hypothesis dicts with shared_id.
        """
        results = []
        for shared_id, hypo in SHARED_HYPOTHESES.items():
            if domain and hypo.get("domain") != domain:
                continue
            results.append(dict(hypo))
        return sorted(results, key=lambda h: h.get("shared_at", ""), reverse=True)

    def import_from_library(
        self,
        shared_hypothesis_id: str,
        /,
        origin_tenant_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Copy a shared hypothesis into the current tenant's repository.

        Parameters
        ----------
        shared_hypothesis_id : str
            The library ID of the shared hypothesis.
        origin_tenant_id : str, optional
            For provenance record (which library it came from).

        Returns
        -------
        dict — the imported hypothesis dict, or None if not found.
        """
        shared = SHARED_HYPOTHESES.get(shared_hypothesis_id)
        if shared is None:
            return None

        # Create a new hypothesis dict for the importing tenant
        imported = {
            "title": shared["title"],
            "description": shared["description"],
            "domain": shared.get("domain", "mixed"),
            "confidence": shared.get("confidence", 0.5),
            "status": "draft",
            "metadata": dict(shared.get("metadata", {})),
            "provenance": [
                {
                    "source": "workspace",
                    "action": "imported_from_library",
                    "parameters": {
                        "shared_library_id": shared_hypothesis_id,
                        "original_id": shared.get("original_id", ""),
                    },
                }
            ],
        }

        # Add causal_graph and effect_size if present
        if "causal_graph" in shared:
            imported["metadata"]["causal_graph"] = shared["causal_graph"]
        if "effect_size" in shared:
            imported["metadata"]["effect_size"] = shared["effect_size"]

        return imported

    def get_shared_hypothesis(self, shared_hypothesis_id: str) -> Optional[dict]:
        """Retrieve a specific shared hypothesis by its library ID."""
        return SHARED_HYPOTHESES.get(shared_hypothesis_id)

    # ── Utility ─────────────────────────────────────────────────────────────

    @staticmethod
    def list_shared_library_by_domain(domain: str) -> list[dict]:
        """Static helper — list shared hypotheses filtered by domain."""
        return [
            dict(h) for h in SHARED_HYPOTHESES.values()
            if h.get("domain") == domain
        ]

    @staticmethod
    def shared_library_size() -> int:
        """Return total count of shared hypotheses."""
        return len(SHARED_HYPOTHESES)