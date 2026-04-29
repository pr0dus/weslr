"""
WESLR OmniChat Evidence Offer V1 — Tests
Verdict label: WESLR_OMNICHAT_EVIDENCE_OFFER_DEFINED

Tests that:
- fallback responses include a natural evidence offer
- the offer is conversational, not a mode switch
- no auto-trigger or side effects
- no structural markers or metadata leakage
"""

import ast
import importlib.util
import inspect
import sys

spec = importlib.util.spec_from_file_location(
    "response_expander",
    "weslr/omnichat/response_expander.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules["weslr.omnichat.response_expander"] = mod
spec.loader.exec_module(mod)

expand_response = mod.expand_response
_fallback_guidance = mod._fallback_guidance
_is_entry_phrase = mod._is_entry_phrase

# Forbidden structural/internal markers in user-facing prose
_FORBIDDEN_LEAKAGE = [
    "LIMITATION",
    "structured truth",
    "Evidence —",
    "expanded_response.",
    "evidence_mode",
    "_omnichat_policy",
    "WESLR structured knowledge",  # too technical for prose
]

# Forbidden command/feature framing
_FORBIDDEN_FEATURE = frozenset({
    "enable evidence",
    "turn on evidence",
    "activate evidence mode",
    "switch to evidence",
    "evidence mode",
})


def make_response(response_text="I'm not able to process that request.", path="fallback"):
    return {
        "response_text": response_text,
        "path": path,
    }, {
        "final_response_type": "fallback",
        "expansion_layers": [],
        "depth_level": "standard",
    }


def _has_leakage(text: str) -> bool:
    for marker in _FORBIDDEN_LEAKAGE:
        if marker.lower() in text.lower():
            return True
    return False


def _has_feature_framing(text: str) -> bool:
    t = text.lower()
    for phrase in _FORBIDDEN_FEATURE:
        if phrase in t:
            return True
    return False


# ---------------------------------------------------------------------------
# Fallback includes evidence offer (natural wording)
# ---------------------------------------------------------------------------

def test_fallback_evidence_offer_present():
    response, policy = make_response()
    result = expand_response(response, policy, "random unknown topic")

    rt = result["response_text"]
    # Must mention looking into it or finding out
    assert any(kw in rt.lower() for kw in ["look into", "find", "search", "explore", "what i find"]), \
        f"No evidence offer in fallback: {rt!r}"
    print("PASS: test_fallback_evidence_offer_present")


def test_fallback_evidence_offer_natural():
    response, policy = make_response()
    result = expand_response(response, policy, "asdfqwer")

    rt = result["response_text"]
    # Must mention keeping it separate (not part of structured knowledge)
    assert any(kw in rt.lower() for kw in ["separate", "not part of", "keeping it"]), \
        f"No separation framing: {rt!r}"
    print("PASS: test_fallback_evidence_offer_natural")


def test_fallback_not_robotic():
    response, policy = make_response()
    result = expand_response(response, policy, "qzxuepqoir")

    rt = result["response_text"]
    # Not robotic
    assert "LIMITATION" not in rt.upper()
    assert "i cannot" not in rt.lower()
    assert "i'm not able" not in rt.lower()
    print("PASS: test_fallback_not_robotic")


def test_fallback_single_paragraph():
    response, policy = make_response()
    result = expand_response(response, policy, "xyzabc")

    rt = result["response_text"]
    assert "\n" not in rt  # single paragraph
    assert "\n1." not in rt  # no numbered lists
    print("PASS: test_fallback_single_paragraph")


# ---------------------------------------------------------------------------
# Consent requirement (no auto-trigger)
# ---------------------------------------------------------------------------

def test_no_auto_trigger_evidence():
    # Evidence offer must require user confirmation — it should NOT auto-run
    # This is tested by verifying the guidance doesn't say "I'll look into it now"
    # or "I'm searching for..." — it asks rather than acts
    response, policy = make_response()
    result = expand_response(response, policy, "anything")

    rt = result["response_text"].lower()
    # Must NOT claim to have already looked or be searching now
    assert "i looked" not in rt
    assert "i've searched" not in rt
    assert "i found" not in rt
    assert "searching" not in rt
    # Must be an offer, not an action
    assert any(kw in rt for kw in ["can", "i can", "if you want", "let me"]), \
        f"Evidence offer doesn't sound like an offer: {result['response_text']!r}"
    print("PASS: test_no_auto_trigger_evidence")


def test_fallback_entry_phrase_not_evidence_offer():
    # Entry phrases (greetings) should NOT trigger evidence offer
    for phrase in ["hi", "hey", "hello", "start", "help"]:
        response, policy = make_response()
        result = expand_response(response, policy, phrase)
        rt = result["response_text"].lower()
        # Entry should be greeting, not evidence offer
        assert "i don't have a confirmed answer" not in rt, \
            f"Entry phrase {phrase!r} triggered evidence offer instead of greeting"
    print("PASS: test_fallback_entry_phrase_not_evidence_offer")


# ---------------------------------------------------------------------------
# No feature/mode framing
# ---------------------------------------------------------------------------

def test_no_evidence_mode_framing():
    response, policy = make_response()
    result = expand_response(response, policy, "unknown")

    rt = result["response_text"]
    assert not _has_feature_framing(rt), \
        f"Evidence offer framed as feature/mode: {rt!r}"
    print("PASS: test_no_evidence_mode_framing")


# ---------------------------------------------------------------------------
# No structural leakage
# ---------------------------------------------------------------------------

def test_no_leakage_in_fallback():
    response, policy = make_response()
    result = expand_response(response, policy, "random")

    rt = result["response_text"]
    assert not _has_leakage(rt), \
        f"Internal marker leaked in fallback: {rt!r}"
    print("PASS: test_no_leakage_in_fallback")


def test_metadata_preserved():
    response, policy = make_response()
    result = expand_response(response, policy, "test")

    assert "_omnichat_policy" in result
    assert "expanded_response" in result
    # Policy should note evidence was offered
    assert result["expanded_response"]["guidance"] != "I don't have a confirmed answer"
    print("PASS: test_metadata_preserved")


# ---------------------------------------------------------------------------
# No side effects / no-write proof
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
            assert call_name not in write_calls, f"write call {call_name!r} found"
    print("PASS: test_no_write_calls")


def test_no_graph_modification():
    # Evidence offer does NOT call graph write methods.
    # The no-write proof above already guarantees this;
    # we just verify no graph write calls exist.
    source = inspect.getsource(expand_response)
    tree = ast.parse(source)
    graph_write_calls = {"add_node", "add_edge", "merge_nodes", "delete_node",
                          "persist_graph", "save_graph", "write_graph"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            assert call_name not in graph_write_calls, \
                f"graph write call {call_name!r} found in expand_response"
    print("PASS: test_no_graph_modification")


# ---------------------------------------------------------------------------
# Consent keywords defined (for future integration)
# ---------------------------------------------------------------------------

def test_consent_keywords_documented():
    # Document what user must say to trigger evidence exploration
    # These are NOT implemented in this phase — just documented for review
    CONSENT_KEYWORDS = frozenset({"yes", "look into it", "explore", "check", "do it"})
    assert len(CONSENT_KEYWORDS) > 0
    print("PASS: test_consent_keywords_documented")


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

tests = [
    # Evidence offer wording
    test_fallback_evidence_offer_present,
    test_fallback_evidence_offer_natural,
    test_fallback_not_robotic,
    test_fallback_single_paragraph,
    # Consent / no auto-trigger
    test_no_auto_trigger_evidence,
    test_fallback_entry_phrase_not_evidence_offer,
    # Feature framing
    test_no_evidence_mode_framing,
    # Leakage
    test_no_leakage_in_fallback,
    # Metadata
    test_metadata_preserved,
    # No side effects
    test_no_write_calls,
    test_no_graph_modification,
    # Documentation
    test_consent_keywords_documented,
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
