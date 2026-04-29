"""
WESLR Graph + Evidence Presentation V1 — Tests
Verdict label: WESLR_GRAPH_EVIDENCE_PRESENTATION_V1_DEFINED
"""

import ast
import inspect
import sys
import importlib.util

# Load module without triggering __init__.py
spec = importlib.util.spec_from_file_location(
    "response_expander",
    "weslr/omnichat/response_expander.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules["weslr.omnichat.response_expander"] = mod
spec.loader.exec_module(mod)

expand_response = mod.expand_response
_EXPAND_NOTE = mod._EXPAND_NOTE
_SAFETY_NOTE = "not part of structured truth"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_response(
    response_text="test response",
    graph_context=None,
    evidence_overlay=None,
):
    """Build a minimal response with optional _selected_context."""
    response = {
        "response_text": response_text,
        "path": "test_path",
    }
    if graph_context is not None or evidence_overlay is not None:
        selected = {"context_type": "graph"}
        if graph_context is not None:
            selected["graph_context"] = graph_context
        if evidence_overlay is not None:
            selected["evidence_overlay"] = evidence_overlay
        response["_selected_context"] = selected
    return response


def make_graph_context(root_id, connection_ids=None):
    ctx = {"root": {"id": root_id}}
    if connection_ids is not None:
        ctx["connections"] = [{"id": str(cid), "type": "related", "relation": "uses", "depth": 1}
                            for cid in connection_ids]
    return ctx


def make_policy(type_="deterministic"):
    return {"final_response_type": type_, "expansion_layers": [], "depth_level": "standard"}


def make_graph_summary(connections):
    return {
        "connections": connections,
        "connection_count": len(connections),
        "root_id": "entity-root",
        "truncated": False,
        "display_truncated": False,
    }


# ---------------------------------------------------------------------------
# Test: both graph + evidence present
# ---------------------------------------------------------------------------

def test_both_graph_and_evidence_present():
    gc = make_graph_context("entity-root", ["entity-a", "entity-b"])
    evidence = [
        {"entity_id": "entity-a", "evidence_summary": "some evidence", "confidence": 0.8,
         "source_type": "workspace", "note": "not part of structured truth"},
    ]
    response = make_response(graph_context=gc, evidence_overlay=evidence)
    result = expand_response(response, make_policy(), message="test")

    kv = result["expanded_response"].get("knowledge_view")
    assert kv is not None, "knowledge_view must be present"
    assert "structured" in kv, "structured section must be present"
    assert "evidence" in kv, "evidence section must be present"
    assert kv["structured"]["count"] == 2
    assert len(kv["evidence"]["items"]) == 1
    assert kv["evidence"]["label"] == _SAFETY_NOTE
    assert _EXPAND_NOTE in result["response_text"]
    print("PASS: test_both_graph_and_evidence_present")


# ---------------------------------------------------------------------------
# Test: graph only (no evidence)
# ---------------------------------------------------------------------------

def test_graph_only_no_evidence():
    gc = make_graph_context("entity-root", ["entity-a"])
    response = make_response(graph_context=gc)
    result = expand_response(response, make_policy(), message="test")

    kv = result["expanded_response"].get("knowledge_view")
    # No evidence → no knowledge_view at all
    assert kv is None or "evidence" not in kv
    # Graph only → structured present
    if kv is not None:
        assert "structured" in kv
    assert _EXPAND_NOTE in result["response_text"]
    print("PASS: test_graph_only_no_evidence")


# ---------------------------------------------------------------------------
# Test: evidence only (no graph)
# ---------------------------------------------------------------------------

def test_evidence_only_no_graph():
    evidence = [
        {"entity_id": "entity-x", "evidence_summary": "unconfirmed signal",
         "confidence": 0.6, "source_type": "external", "note": "not part of structured truth"},
    ]
    # No graph_context, but evidence in overlay
    response = make_response(evidence_overlay=evidence)
    result = expand_response(response, make_policy(), message="test")

    kv = result["expanded_response"].get("knowledge_view")
    assert kv is not None
    assert "structured" not in kv, "no graph → no structured section"
    assert "evidence" in kv
    assert kv["evidence"]["label"] == _SAFETY_NOTE
    assert len(kv["evidence"]["items"]) == 1
    assert _EXPAND_NOTE in result["response_text"]
    print("PASS: test_evidence_only_no_graph")


# ---------------------------------------------------------------------------
# Test: no mixing — structured and evidence kept separate
# ---------------------------------------------------------------------------

def test_no_mixing():
    gc = make_graph_context("entity-root", ["entity-a", "entity-b"])
    evidence = [
        {"entity_id": "entity-x", "evidence_summary": "E1",
         "confidence": 0.8, "source_type": "workspace",
         "note": "not part of structured truth"},
        {"entity_id": "entity-y", "evidence_summary": "E2",
         "confidence": 0.7, "source_type": "external",
         "note": "not part of structured truth"},
    ]
    response = make_response(graph_context=gc, evidence_overlay=evidence)
    result = expand_response(response, make_policy(), message="test")

    kv = result["expanded_response"]["knowledge_view"]
    # structured and evidence are top-level sibling keys, not merged
    assert "structured" in kv
    assert "evidence" in kv
    assert len(kv) == 2, "only structured + evidence keys, nothing merged"
    # Evidence label is present on the evidence section (not on structured)
    assert "label" in kv["evidence"]
    assert kv["evidence"]["label"] == _SAFETY_NOTE
    assert "label" not in kv["structured"]
    print("PASS: test_no_mixing")


# ---------------------------------------------------------------------------
# Test: evidence label always present
# ---------------------------------------------------------------------------

def test_evidence_label_always_present():
    evidence = [
        {"entity_id": "entity-x", "evidence_summary": "unconfirmed",
         "confidence": 0.5, "source_type": "workspace", "note": _SAFETY_NOTE},
    ]
    response = make_response(evidence_overlay=evidence)
    result = expand_response(response, make_policy(), message="test")

    kv = result["expanded_response"]["knowledge_view"]
    assert "evidence" in kv
    assert "label" in kv["evidence"]
    assert kv["evidence"]["label"] == _SAFETY_NOTE
    # Each item also carries the note (from evidence_graph_overlay layer)
    for item in kv["evidence"]["items"]:
        assert item.get("note") == _SAFETY_NOTE
    print("PASS: test_evidence_label_always_present")


# ---------------------------------------------------------------------------
# Test: no-write proof — AST scan of expand_response
# ---------------------------------------------------------------------------

def test_no_write_calls():
    source = inspect.getsource(expand_response)
    tree = ast.parse(source)
    write_calls = {
        "open", "write", "dump", "dumpjson", "save", "store",
        "json.dump", "json.dumps", "to_file", "persist",
        "append", "writelines",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            assert call_name not in write_calls, f"write call {call_name!r} found in expand_response"
    print("PASS: test_no_write_calls")


# ---------------------------------------------------------------------------
# Test: no graph → structured section omitted
# ---------------------------------------------------------------------------

def test_no_graph_omits_structured():
    # Neither graph_context nor evidence_overlay
    response = make_response()
    result = expand_response(response, make_policy(), message="test")

    kv = result["expanded_response"].get("knowledge_view")
    # Neither section → no knowledge_view
    assert kv is None or ("structured" not in kv and "evidence" not in kv)
    print("PASS: test_no_graph_omits_structured")


# ---------------------------------------------------------------------------
# Test: graph_summary + evidence_overlay in same response → both shown
# ---------------------------------------------------------------------------

def test_graph_summary_plus_evidence_overlay():
    gc = make_graph_context("entity-root", ["entity-a"])
    evidence = [{"entity_id": "entity-a", "evidence_summary": "sig",
                 "confidence": 0.8, "source_type": "workspace",
                 "note": _SAFETY_NOTE}]
    response = make_response(graph_context=gc, evidence_overlay=evidence)
    result = expand_response(response, make_policy(), message="test")

    kv = result["expanded_response"]["knowledge_view"]
    assert "structured" in kv
    assert "evidence" in kv
    # Note: same entity can appear in both — that's intentional separation
    print("PASS: test_graph_summary_plus_evidence_overlay")


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

tests = [
    test_both_graph_and_evidence_present,
    test_graph_only_no_evidence,
    test_evidence_only_no_graph,
    test_no_mixing,
    test_evidence_label_always_present,
    test_no_write_calls,
    test_no_graph_omits_structured,
    test_graph_summary_plus_evidence_overlay,
]

failed = 0
for fn in tests:
    try:
        fn()
    except Exception as e:
        print(f"FAIL: {fn.__name__}: {e}")
        failed += 1

print()
if failed == 0:
    print("All 8 tests passed.")
else:
    print(f"{failed} test(s) failed.")
    sys.exit(1)
