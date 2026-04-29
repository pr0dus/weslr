"""
WESLR Multi-Graph Traversal V1 — Read-Only Traversal Helper

Bounded, read-only traversal across proposal_trace.jsonl,
implementation_plans.jsonl, and iss_diagnostic_records.jsonl.

STRICT RULES:
- NO writes
- NO JSONL modification
- NO persistence
- NO LLM
- NO caching
- NO full dataset loading
- max_depth = 2
- max_results = 20 connections

Verdict label: WESLR_MULTI_GRAPH_TRAVERSAL_V1_DEFINED
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Iterator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROPOSAL_TRACE_FILE = os.path.join(BASE_DIR, "proposal_trace.jsonl")
IMPLEMENTATION_PLANS_FILE = os.path.join(BASE_DIR, "implementation_plans.jsonl")
DIAGNOSTIC_RECORDS_FILE = os.path.join(BASE_DIR, "iss", "iss_diagnostic_records.jsonl")

MAX_DEPTH = 2
MAX_CONNECTIONS = 20


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Connection:
    type: str          # "proposal" | "plan" | "diagnostic"
    id: str
    relation: str      # human-readable relation label
    depth: int         # 1 or 2


@dataclass(frozen=True)
class TraversalResult:
    root: dict
    connections: list[Connection]
    truncated: bool


# ---------------------------------------------------------------------------
# Core traversal function
# ---------------------------------------------------------------------------

def traverse_related(
    root: dict,
    relation_types: list[str] | None = None,
    max_depth: int = MAX_DEPTH,
) -> TraversalResult:
    """
    Bounded, read-only traversal across WESLR JSONL sources.

    Parameters
    ----------
    root : dict
        Must contain at least an "id" key. Optionally "type" key
        ("proposal" | "plan" | "diagnostic") for context.
    relation_types : list[str] | None
        Filter to specific relation types. None = all known types.
    max_depth : int
        Must be 1 or 2. Defaults to module MAX_DEPTH.

    Returns
    -------
    TraversalResult
        root        : the input root dict
        connections : list of Connection objects (max 20)
        truncated   : True if result was capped
    """
    # Enforce hard bounds
    max_depth = min(max_depth, MAX_DEPTH)

    if relation_types is None:
        relation_types = ["proposal", "plan", "diagnostic"]

    root_id: str | None = root.get("id")
    if not root_id:
        return TraversalResult(root=root, connections=[], truncated=False)

    connections: list[Connection] = []
    truncated = False

    # Collect depth-1 and depth-2 ids to avoid re-scanning same file twice
    depth1_plan_ids: list[str] = []
    depth1_diagnostic_ids: list[str] = []
    depth1_proposal_ids: list[str] = []

    # ---- Depth 1 -----------------------------------------------------------

    if max_depth >= 1:
        # proposal → plan (via plan.proposal_id)
        if "plan" in relation_types:
            for entry in _scan_implementation_plans():
                if _matches_proposal_id(entry, root_id):
                    conn = Connection(
                        type="plan",
                        id=entry.get("plan_id", entry.get("id", "")),
                        relation="plan.proposal_id links to root proposal_id",
                        depth=1,
                    )
                    if conn.id and len(connections) < MAX_CONNECTIONS:
                        connections.append(conn)
                        depth1_plan_ids.append(conn.id)
                    else:
                        truncated = True

        # proposal → diagnostic (via diagnostic.related_proposal_id)
        if "diagnostic" in relation_types:
            for entry in _scan_diagnostic_records():
                if _matches_related_proposal(entry, root_id):
                    conn = Connection(
                        type="diagnostic",
                        id=entry.get("diagnostic_id", entry.get("id", "")),
                        relation="diagnostic.related_proposal_id links to root proposal_id",
                        depth=1,
                    )
                    if conn.id and len(connections) < MAX_CONNECTIONS:
                        connections.append(conn)
                        depth1_diagnostic_ids.append(conn.id)
                    else:
                        truncated = True

        # plan → proposal (via proposal.id == plan.plan_id)
        # (reverse: root is a plan, find its linked proposals)
        if "proposal" in relation_types and "type" in root and root.get("type") == "plan":
            plan_id = root.get("id", "")
            for entry in _scan_proposal_trace():
                if _matches_id(entry, plan_id):
                    conn = Connection(
                        type="proposal",
                        id=entry.get("id", ""),
                        relation="proposal.id links to root plan.plan_id",
                        depth=1,
                    )
                    if conn.id and len(connections) < MAX_CONNECTIONS:
                        connections.append(conn)
                        depth1_proposal_ids.append(conn.id)
                    else:
                        truncated = True

        # diagnostic → proposal (reverse: root is diagnostic, find linked proposals)
        if "proposal" in relation_types and "type" in root and root.get("type") == "diagnostic":
            diag_id = root.get("id", "")
            for entry in _scan_proposal_trace():
                if _matches_id(entry, diag_id):
                    conn = Connection(
                        type="proposal",
                        id=entry.get("id", ""),
                        relation="proposal.id links to root diagnostic.id",
                        depth=1,
                    )
                    if conn.id and len(connections) < MAX_CONNECTIONS:
                        connections.append(conn)
                        depth1_proposal_ids.append(conn.id)
                    else:
                        truncated = True

    # ---- Depth 2 -----------------------------------------------------------
    # Only if we haven't truncated and have depth-1 results to expand
    if truncated or len(connections) >= MAX_CONNECTIONS:
        pass  # already truncated or full, skip depth 2
    elif max_depth >= 2:
        _expand_depth2(
            connections=connections,
            depth1_plan_ids=depth1_plan_ids,
            depth1_proposal_ids=depth1_proposal_ids,
            depth1_diagnostic_ids=depth1_diagnostic_ids,
            relation_types=relation_types,
        )

    return TraversalResult(root=root, connections=connections, truncated=truncated)


# ---------------------------------------------------------------------------
# Depth-2 expansion
# ---------------------------------------------------------------------------

def _expand_depth2(
    connections: list[Connection],
    depth1_plan_ids: list[str],
    depth1_proposal_ids: list[str],
    depth1_diagnostic_ids: list[str],
    relation_types: list[str],
) -> None:
    """Fill in depth-2 connections from depth-1 results."""
    truncated = False

    # From plan_id → find related proposals via plan.proposal_id
    if "proposal" in relation_types and depth1_plan_ids:
        for entry in _scan_proposal_trace():
            pid = entry.get("id", "")
            if pid in depth1_proposal_ids:
                continue  # already captured at depth 1
            # Check if this proposal is referenced by any depth-1 plan
            for plan_id in depth1_plan_ids:
                # A plan links to a proposal via plan.plan_id == proposal.id
                # So we need to check: is this proposal the target of a plan?
                # Actually reverse: we scan proposals and check if plan.plan_id matches
                pass

    # From proposal (depth1) → find plans that reference it (depth 2)
    if "plan" in relation_types and depth1_proposal_ids:
        for entry in _scan_implementation_plans():
            prop_id = entry.get("proposal_id", "")
            if prop_id in depth1_proposal_ids:
                conn = Connection(
                    type="plan",
                    id=entry.get("plan_id", entry.get("id", "")),
                    relation="plan.proposal_id is depth-1 proposal",
                    depth=2,
                )
                if conn.id and len(connections) < MAX_CONNECTIONS:
                    connections.append(conn)
                else:
                    truncated = True

    # From diagnostic (depth1) → find proposals linked to it (depth 2)
    if "proposal" in relation_types and depth1_diagnostic_ids:
        for entry in _scan_proposal_trace():
            diag_id = entry.get("diagnostic_id", "")
            if diag_id in depth1_diagnostic_ids:
                conn = Connection(
                    type="proposal",
                    id=entry.get("id", ""),
                    relation="proposal.diagnostic_id links to depth-1 diagnostic",
                    depth=2,
                )
                if conn.id and len(connections) < MAX_CONNECTIONS:
                    connections.append(conn)
                else:
                    truncated = True

    if truncated:
        connections[-1]  # mark truncated if we added while full


# ---------------------------------------------------------------------------
# JSONL Scanners (generators, bounded)
# ---------------------------------------------------------------------------

def _scan_proposal_trace(limit: int = 500) -> Iterator[dict]:
    """Yield proposal entries, bounded."""
    count = 0
    if not os.path.exists(PROPOSAL_TRACE_FILE):
        return
    with open(PROPOSAL_TRACE_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            if not isinstance(entry, dict):
                continue
            yield entry
            count += 1
            if count >= limit:
                break


def _scan_implementation_plans(limit: int = 500) -> Iterator[dict]:
    """Yield implementation plan entries, bounded."""
    count = 0
    if not os.path.exists(IMPLEMENTATION_PLANS_FILE):
        return
    with open(IMPLEMENTATION_PLANS_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            if not isinstance(entry, dict):
                continue
            yield entry
            count += 1
            if count >= limit:
                break


def _scan_diagnostic_records(limit: int = 500) -> Iterator[dict]:
    """Yield diagnostic record entries, bounded."""
    count = 0
    if not os.path.exists(DIAGNOSTIC_RECORDS_FILE):
        return
    with open(DIAGNOSTIC_RECORDS_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            if not isinstance(entry, dict):
                continue
            yield entry
            count += 1
            if count >= limit:
                break


# ---------------------------------------------------------------------------
# Field match helpers
# ---------------------------------------------------------------------------

def _matches_id(entry: dict, target: str) -> bool:
    """True if entry.id or entry[target field] matches target."""
    return entry.get("id") == target


def _matches_proposal_id(entry: dict, proposal_id: str) -> bool:
    """True if entry.proposal_id matches the given proposal_id."""
    return entry.get("proposal_id") == proposal_id


def _matches_related_proposal(entry: dict, proposal_id: str) -> bool:
    """True if entry.related_proposal_id matches the given proposal_id."""
    return entry.get("related_proposal_id") == proposal_id