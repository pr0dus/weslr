"""
WESLR Evidence Graph Overlay V1 — Tests
Verdict label: WESLR_EVIDENCE_GRAPH_OVERLAY_V1_DEFINED
"""

import pytest
from weslr.evidence_graph_overlay import (
    attach_evidence_overlay,
    SAFETY_NOTE,
    MAX_LINKS_DEFAULT,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_graph_context(root_id, connection_ids=None):
    """Build a minimal graph_context dict for testing."""
    ctx = {"root": {"id": root_id}}
    if connection_ids is not None:
        ctx["connections"] = [{"id": cid} for cid in connection_ids]
    return ctx


def make_evidence(entity_id, summary="test summary", confidence=0.8, source="workspace"):
    return {
        "entity_id": entity_id,
        "summary": summary,
        "confidence": confidence,
        "source": source,
    }


# ---------------------------------------------------------------------------
# Overlay attaches correctly
# ---------------------------------------------------------------------------

def test_overlay_attaches_correctly():
    ctx = make_graph_context("entity-1", ["entity-2", "entity-3"])
    evidence = [
        make_evidence("entity-1", "Evidence for entity-1"),
        make_evidence("entity-2", "Evidence for entity-2"),
    ]

    result = attach_evidence_overlay(ctx, evidence)

    assert "graph_context" in result
    assert "evidence_overlay" in result
    overlay = result["evidence_overlay"]
    assert len(overlay) == 2
    assert overlay[0]["entity_id"] in ("entity-1", "entity-2")
    assert overlay[0]["evidence_summary"] == "Evidence for entity-1"
    assert overlay[0]["source_type"] == "workspace"
    assert overlay[1]["evidence_summary"] == "Evidence for entity-2"
    for entry in overlay:
        assert entry["note"] == SAFETY_NOTE


# ---------------------------------------------------------------------------
# No match → empty overlay
# ---------------------------------------------------------------------------

def test_no_match_empty_overlay():
    ctx = make_graph_context("entity-1")
    evidence = [
        make_evidence("entity-unrelated", "Some evidence"),
    ]

    result = attach_evidence_overlay(ctx, evidence)

    assert result["evidence_overlay"] == []


# ---------------------------------------------------------------------------
# max_links respected
# ---------------------------------------------------------------------------

def test_max_links_respected():
    ctx = make_graph_context("entity-1", [f"entity-{i}" for i in range(2, 20)])
    evidence = [make_evidence(f"entity-{i}", f"Evidence {i}") for i in range(1, 20)]

    result = attach_evidence_overlay(ctx, evidence, max_links=3)

    assert len(result["evidence_overlay"]) == 3


# ---------------------------------------------------------------------------
# note always present
# ---------------------------------------------------------------------------

def test_note_always_present():
    ctx = make_graph_context("entity-1")
    evidence = [
        make_evidence("entity-1", "test", 0.5, "external"),
    ]

    result = attach_evidence_overlay(ctx, evidence)

    for entry in result["evidence_overlay"]:
        assert "note" in entry
        assert entry["note"] == SAFETY_NOTE


# ---------------------------------------------------------------------------
# graph_context unchanged
# ---------------------------------------------------------------------------

def test_graph_context_unchanged():
    ctx = make_graph_context("entity-1", ["entity-2"])
    original_root_id = ctx["root"]["id"]

    evidence = [make_evidence("entity-X", "No match")]
    result = attach_evidence_overlay(ctx, evidence)

    assert result["graph_context"] is ctx
    assert result["graph_context"]["root"]["id"] == original_root_id


# ---------------------------------------------------------------------------
# no-write proof (static analysis)
# ---------------------------------------------------------------------------

def test_no_write_calls():
    """Verify attach_evidence_overlay contains no write/create/persistence calls."""
    import ast
    import inspect
    source = inspect.getsource(attach_evidence_overlay)
    tree = ast.parse(source)

    write_calls = ["open", "write", "dump", "dumpjson", "save", "store",
                   "json.dump", "json.dumps", "to_file", "persist"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            assert call_name not in write_calls, f"write call {call_name} found in source"


# ---------------------------------------------------------------------------
# source_type mapping
# ---------------------------------------------------------------------------

def test_source_type_external():
    ctx = make_graph_context("entity-1")
    evidence = [make_evidence("entity-1", "ext", source="external")]

    result = attach_evidence_overlay(ctx, evidence)

    assert result["evidence_overlay"][0]["source_type"] == "external"


def test_source_type_workspace():
    ctx = make_graph_context("entity-1")
    evidence = [make_evidence("entity-1", "ws")]

    result = attach_evidence_overlay(ctx, evidence)

    assert result["evidence_overlay"][0]["source_type"] == "workspace"


# ---------------------------------------------------------------------------
# confidence clamping
# ---------------------------------------------------------------------------

def test_confidence_clamped_high():
    ctx = make_graph_context("entity-1")
    evidence = [make_evidence("entity-1", "test", confidence=1.5)]

    result = attach_evidence_overlay(ctx, evidence)

    assert result["evidence_overlay"][0]["confidence"] == 1.0


def test_confidence_clamped_low():
    ctx = make_graph_context("entity-1")
    evidence = [make_evidence("entity-1", "test", confidence=-0.5)]

    result = attach_evidence_overlay(ctx, evidence)

    assert result["evidence_overlay"][0]["confidence"] == 0.0


# ---------------------------------------------------------------------------
# topic match fallback
# ---------------------------------------------------------------------------

def test_topic_match_fallback():
    ctx = make_graph_context("entity-alpha", ["entity-beta"])
    evidence = [
        {"entity_id": "", "summary": "Alpha workspace evidence", "confidence": 0.7, "source": "workspace"},
    ]

    result = attach_evidence_overlay(ctx, evidence)

    assert len(result["evidence_overlay"]) == 1
    assert result["evidence_overlay"][0]["entity_id"] == "entity-alpha"


# ---------------------------------------------------------------------------
# duplicate entity_id skipped
# ---------------------------------------------------------------------------

def test_duplicate_entity_id_skipped():
    ctx = make_graph_context("entity-1")
    evidence = [
        make_evidence("entity-1", "First"),
        make_evidence("entity-1", "Second"),
    ]

    result = attach_evidence_overlay(ctx, evidence)

    assert len(result["evidence_overlay"]) == 1
