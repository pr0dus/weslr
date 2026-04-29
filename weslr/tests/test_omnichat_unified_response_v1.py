"""
WESLR OmniChat Unified Response V1 — Tests
Verdict label: WESLR_OMNICHAT_UNIFICATION_PHASE1_DEFINED
"""

import ast
import inspect
import sys
import importlib.util

# Load module directly without triggering __init__.py
spec = importlib.util.spec_from_file_location(
    "response_expander",
    "weslr/omnichat/response_expander.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules["weslr.omnichat.response_expander"] = mod
spec.loader.exec_module(mod)

expand_response = mod.expand_response
_BLOCKED_WRITE_GUIDANCE = "That operation requires write access"
_FALLBACK_GUIDANCE = "I don't have anything built in for that specifically"
_EXPAND_NOTE = "Evidence is not part of confirmed system knowledge"
_GRAPH_NOTE = "Related structured connections were found"
_GUIDANCE_MARKERS = ["LIMITATION", "You might also want to know", "Related things you can try",
                     "- show", "structured truth", "Evidence —"]


def make_response(response_text="test response", path="test_path",
                 graph_context=None, evidence_overlay=None,
                 final_type="deterministic"):
    """Build minimal response + policy."""
    response = {
        "response_text": response_text,
        "path": path,
    }
    if graph_context is not None or evidence_overlay is not None:
        selected = {"context_type": "graph"}
        if graph_context is not None:
            selected["graph_context"] = graph_context
        if evidence_overlay is not None:
            selected["evidence_overlay"] = evidence_overlay
        response["_selected_context"] = selected

    policy = {
        "final_response_type": final_type,
        "expansion_layers": [],
        "depth_level": "standard",
    }
    return response, policy


def make_graph_context(root_id, connection_ids=None):
    ctx = {"root": {"id": root_id}}
    if connection_ids is not None:
        ctx["connections"] = [
            {"id": str(cid), "type": "related", "relation": "uses", "depth": 1}
            for cid in connection_ids
        ]
    return ctx


# ---------------------------------------------------------------------------
# Test: response_text exists and is string
# ---------------------------------------------------------------------------

def test_response_text_exists_and_is_string():
    response, policy = make_response("hello world")
    result = expand_response(response, policy, "test")

    assert "response_text" in result
    assert isinstance(result["response_text"], str)
    assert result["response_text"] == "hello world"
    print("PASS: test_response_text_exists_and_is_string")


# ---------------------------------------------------------------------------
# Test: no structural markers inside response_text
# ---------------------------------------------------------------------------

def test_no_structural_markers_in_response_text():
    forbidden = [
        "LIMITATION", "LIMITATION:", "[Evidence", "Evidence —",
        "not part of structured truth", "Structured relationships",
        "See expanded_response.graph_summary",
        "You might also want to know:", "Related things you can try:",
    ]

    # deterministic with graph + evidence
    gc = make_graph_context("entity-root", ["entity-a"])
    evidence = [
        {"entity_id": "entity-a", "evidence_summary": "some evidence",
         "confidence": 0.8, "source_type": "workspace",
         "note": "not part of structured truth"},
    ]
    response, policy = make_response(
        "WESLR is a governed system.",
        graph_context=gc, evidence_overlay=evidence
    )
    result = expand_response(response, policy, "test")

    rt_lower = result["response_text"].lower()
    for marker in forbidden:
        assert marker.lower() not in rt_lower, f"forbidden marker '{marker}' found in response_text"
    print("PASS: test_no_structural_markers_in_response_text")


# ---------------------------------------------------------------------------
# Test: metadata still present
# ---------------------------------------------------------------------------

def test_metadata_still_present():
    response, policy = make_response("test answer")
    result = expand_response(response, policy, "test")

    assert "_omnichat_policy" in result
    assert "expanded_response" in result
    assert result["expanded_response"]["guidance"] == ""
    print("PASS: test_metadata_still_present")


# ---------------------------------------------------------------------------
# Test: graph_summary still present in expanded_response
# ---------------------------------------------------------------------------

def test_graph_summary_in_expanded_response():
    gc = make_graph_context("entity-root", ["entity-a", "entity-b"])
    response, policy = make_response("test", graph_context=gc)

    result = expand_response(response, policy, "test")

    assert "graph_summary" in result["expanded_response"]
    gs = result["expanded_response"]["graph_summary"]
    assert gs["connection_count"] == 2
    assert len(gs["connections"]) == 2
    print("PASS: test_graph_summary_in_expanded_response")


# ---------------------------------------------------------------------------
# Test: knowledge_view.evidence still present in expanded_response
# ---------------------------------------------------------------------------

def test_knowledge_view_evidence_in_expanded_response():
    evidence = [
        {"entity_id": "entity-x", "evidence_summary": "sig",
         "confidence": 0.7, "source_type": "workspace",
         "note": "not part of structured truth"},
    ]
    response, policy = make_response("test", evidence_overlay=evidence)
    result = expand_response(response, policy, "test")

    assert "knowledge_view" in result["expanded_response"]
    kv = result["expanded_response"]["knowledge_view"]
    assert "evidence" in kv
    assert kv["evidence"]["label"] == "not part of structured truth"
    assert len(kv["evidence"]["items"]) == 1
    print("PASS: test_knowledge_view_evidence_in_expanded_response")


# ---------------------------------------------------------------------------
# Test: fallback is natural language (no numbered lists)
# ---------------------------------------------------------------------------

def test_fallback_is_natural_language():
    # Must pass empty response_text or the exact guard string to trigger fallback guidance
    response, policy = make_response(
        response_text="I'm not able to process that request.",
        final_type="fallback"
    )
    result = expand_response(response, policy, "test")

    rt = result["response_text"]
    # No numbered lists
    assert "\n1." not in rt
    assert "\n- " not in rt
    assert "LIMITATION" not in rt.upper()
    # Should mention evidence offer conversationally
    assert "look into" in rt.lower() or "explore" in rt.lower() or "evidence" in rt.lower()
    print("PASS: test_fallback_is_natural_language")


# ---------------------------------------------------------------------------
# Test: blocked_write is natural language
# ---------------------------------------------------------------------------

def test_blocked_write_is_natural_language():
    response, policy = make_response(final_type="blocked_write")
    result = expand_response(response, policy, "test")

    rt = result["response_text"]
    # No "This action is disabled" boilerplate
    assert "This action is disabled" not in rt
    # No numbered suggestions
    assert "\n1." not in rt
    assert "\n- " not in rt
    assert _BLOCKED_WRITE_GUIDANCE in rt
    print("PASS: test_blocked_write_is_natural_language")


# ---------------------------------------------------------------------------
# Test: no structural markers in any response type
# ---------------------------------------------------------------------------

def test_no_structural_markers_in_all_types():
    forbidden_in_text = [
        "LIMITATION", "[Evidence", "Evidence —", "structured truth",
        "See expanded_response.",
    ]

    for final_type in ["deterministic", "guided", "fallback", "blocked_write"]:
        response, policy = make_response(final_type=final_type)
        result = expand_response(response, policy, "test")
        rt_lower = result["response_text"].lower()
        for marker in forbidden_in_text:
            assert marker.lower() not in rt_lower, \
                f"forbidden marker '{marker}' in {final_type} response_text"
    print("PASS: test_no_structural_markers_in_all_types")


# ---------------------------------------------------------------------------
# Test: no-write proof — AST scan
# ---------------------------------------------------------------------------

def test_no_write_calls():
    source = inspect.getsource(expand_response)
    tree = ast.parse(source)
    write_calls = [
        "open", "write", "dump", "dumpjson", "save", "store",
        "json.dump", "json.dumps", "to_file", "persist",
        "append", "writelines",
    ]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            assert call_name not in write_calls, f"write call {call_name!r} found"
    print("PASS: test_no_write_calls")


# ---------------------------------------------------------------------------
# Test: graph_summary note NOT in response_text
# ---------------------------------------------------------------------------

def test_graph_summary_note_not_in_response_text():
    gc = make_graph_context("entity-root", ["entity-a"])
    response, policy = make_response("WESLR is active.", graph_context=gc)
    result = expand_response(response, policy, "test")

    assert _GRAPH_NOTE not in result["response_text"]
    print("PASS: test_graph_summary_note_not_in_response_text")


# ---------------------------------------------------------------------------
# Test: expand note NOT in response_text
# ---------------------------------------------------------------------------

def test_expand_note_not_in_response_text():
    evidence = [
        {"entity_id": "entity-x", "evidence_summary": "sig",
         "confidence": 0.7, "source_type": "workspace",
         "note": "not part of structured truth"},
    ]
    response, policy = make_response("test response", evidence_overlay=evidence)
    result = expand_response(response, policy, "test")

    assert _EXPAND_NOTE not in result["response_text"]
    print("PASS: test_expand_note_not_in_response_text")


# ---------------------------------------------------------------------------
# Test: guidance is inline (single space, not double newline)
# ---------------------------------------------------------------------------

def test_guidance_inline_not_double_newline():
    response, policy = make_response("Here is the answer.", final_type="deterministic")
    result = expand_response(response, policy, "test")

    # If guidance is present, it should be appended inline (single space)
    rt = result["response_text"]
    # Should not have double newline separating main text from guidance
    assert "\n\n" not in rt or rt.count("\n") <= 1, \
        f"double newline found in response_text: {repr(rt)}"
    print("PASS: test_guidance_inline_not_double_newline")


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

tests = [
    test_response_text_exists_and_is_string,
    test_no_structural_markers_in_response_text,
    test_metadata_still_present,
    test_graph_summary_in_expanded_response,
    test_knowledge_view_evidence_in_expanded_response,
    test_fallback_is_natural_language,
    test_blocked_write_is_natural_language,
    test_no_structural_markers_in_all_types,
    test_no_write_calls,
    test_graph_summary_note_not_in_response_text,
    test_expand_note_not_in_response_text,
    test_guidance_inline_not_double_newline,
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
    print(f"All {len(tests)} tests passed.")
else:
    print(f"{failed} test(s) failed.")
    sys.exit(1)
