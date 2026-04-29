"""
WESLR Graph Context Selector V1 — Read-Only Graph Integration

Integrates multi_graph_traversal into context selection as a bounded
graph-context helper for WESLR's context selection layer.

This is NOT graph mutation, NOT response expansion, NOT LLM integration.

STRICT RULES:
- NO writes
- NO JSONL modification
- NO persistence
- NO LLM
- NO evidence promotion
- NO full graph loading
- max_depth <= 2
- max connections <= 20

Verdict label: WESLR_GRAPH_CONTEXT_SELECTOR_V1_DEFINED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from weslr.multi_graph_traversal import (
    traverse_related,
    TraversalResult,
    Connection,
    MAX_DEPTH as MODULE_MAX_DEPTH,
    MAX_CONNECTIONS,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_MODES = frozenset({"public_demo_readonly", "local_demo", "private_dev", "gated_beta", "production"})
VALID_RELATION_TYPES = frozenset({"proposal", "plan", "diagnostic"})

# Source labels only — no raw paths exposed
SOURCE_REFS = [
    "proposal_trace.jsonl",
    "implementation_plans.jsonl",
    "iss_diagnostic_records.jsonl",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GraphContext:
    """Sub-structure returned inside the context bundle."""
    root: dict
    connections: tuple[Connection, ...]  # frozen list
    truncated: bool


@dataclass(frozen=True)
class GraphContextBundle:
    """
    Assembled context bundle for graph queries.
    Frozen — no mutation after construction.
    """
    context_type: str
    truth_status: str
    mode: str
    scope: str
    allowed_for_llm: bool
    expires_after_turn: bool
    source_refs: tuple[str, ...]
    selection_reason: str
    graph_context: GraphContext


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def select_context_for_graph_query(
    root: dict,
    relation_types: list[str] | None = None,
    mode: str = "private_dev",
    max_depth: int = MODULE_MAX_DEPTH,
) -> GraphContextBundle:
    """
    Select and assemble a graph-context bundle for a graph reasoning query.

    This is a read-only, bounded operation — no writes, no state modification.

    Parameters
    ----------
    root : dict
        Must contain at least an "id" key.
    relation_types : list[str] | None
        Filter to specific relation types. None = all known types.
        Unknown types are silently ignored.
    mode : str
        WESLR mode. Controls allowed_for_llm gate.
    max_depth : int
        Traversal depth. Hard-clamped to 2.

    Returns
    -------
    GraphContextBundle
        Frozen dataclass containing the full context bundle.
        graph_context may be empty if root is malformed or no connections found.

    Safety rules enforced:
    - max_depth clamped to 2
    - max connections enforced by traverse_related (20)
    - malformed root → empty graph_context
    - allowed_for_llm always False in V1 (read-only graph helper, no LLM integration)
    - source_refs contains labels only, no raw file paths
    """

    # ---- Safety: clamp max_depth -----------------------------------------
    max_depth = min(max_depth, MODULE_MAX_DEPTH)

    # ---- Safety: validate mode -------------------------------------------
    if mode not in VALID_MODES:
        mode = "private_dev"  # fallback to safest mode

    # ---- Safety: filter unknown relation types ---------------------------
    if relation_types is None:
        relation_types = list(VALID_RELATION_TYPES)
    else:
        relation_types = [rt for rt in relation_types if rt in VALID_RELATION_TYPES]

    # ---- Malformed root check --------------------------------------------
    if not isinstance(root, dict) or not root.get("id"):
        # Return empty graph context bundle
        empty_graph = GraphContext(
            root={"id": "", "type": "unknown"},
            connections=(),
            truncated=False,
        )
        return GraphContextBundle(
            context_type="graph",
            truth_status="structured_truth",
            mode=mode,
            scope="minimal",
            allowed_for_llm=False,  # V1: always False, no LLM integration
            expires_after_turn=True,
            source_refs=tuple(SOURCE_REFS),
            selection_reason="malformed root — no traversal performed",
            graph_context=empty_graph,
        )

    # ---- Traverse ---------------------------------------------------------
    traversal_result: TraversalResult = traverse_related(
        root=root,
        relation_types=relation_types,
        max_depth=max_depth,
    )

    # ---- Assemble graph_context -------------------------------------------
    graph_context = GraphContext(
        root=traversal_result.root,
        connections=tuple(traversal_result.connections),
        truncated=traversal_result.truncated,
    )

    # ---- Build selection reason -------------------------------------------
    conn_count = len(traversal_result.connections)
    depth_used = max_depth if traversal_result.connections else 0

    if conn_count == 0:
        reason = (
            f"graph traversal performed (depth={depth_used}) — "
            f"no connections found for root id='{root.get('id', '')}'"
        )
    else:
        truncated_note = " [TRUNCATED]" if traversal_result.truncated else ""
        reason = (
            f"graph traversal performed (depth={depth_used}, "
            f"connections={conn_count}/{MAX_CONNECTIONS}{truncated_note}) — "
            f"root id='{root.get('id', '')}'"
        )

    # ---- Mode-based allowed_for_llm gate --------------------------------
    # V1: always False — graph context selector is a read-only helper,
    # not an LLM integration layer. LLM integration requires separate implementation.
    allowed_for_llm = False

    return GraphContextBundle(
        context_type="graph",
        truth_status="structured_truth",
        mode=mode,
        scope="minimal",
        allowed_for_llm=allowed_for_llm,
        expires_after_turn=True,
        source_refs=tuple(SOURCE_REFS),
        selection_reason=reason,
        graph_context=graph_context,
    )


# ---------------------------------------------------------------------------
# Dict-style convenience export (for compatibility with existing patterns)
# ---------------------------------------------------------------------------

def select_context_for_graph_query_dict(
    root: dict,
    relation_types: list[str] | None = None,
    mode: str = "private_dev",
    max_depth: int = MODULE_MAX_DEPTH,
) -> dict[str, Any]:
    """
    Same as select_context_for_graph_query but returns a plain dict
    for callers that expect dict-style access.
    """
    bundle = select_context_for_graph_query(
        root=root,
        relation_types=relation_types,
        mode=mode,
        max_depth=max_depth,
    )
    return {
        "context_type": bundle.context_type,
        "truth_status": bundle.truth_status,
        "mode": bundle.mode,
        "scope": bundle.scope,
        "allowed_for_llm": bundle.allowed_for_llm,
        "expires_after_turn": bundle.expires_after_turn,
        "source_refs": list(bundle.source_refs),
        "selection_reason": bundle.selection_reason,
        "graph_context": {
            "root": bundle.graph_context.root,
            "connections": [
                {
                    "type": c.type,
                    "id": c.id,
                    "relation": c.relation,
                    "depth": c.depth,
                }
                for c in bundle.graph_context.connections
            ],
            "truncated": bundle.graph_context.truncated,
        },
    }