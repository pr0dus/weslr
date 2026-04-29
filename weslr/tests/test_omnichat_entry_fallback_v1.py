"""
WESLR OmniChat Entry Fallback V1 — Tests
Verdict label: WESLR_OMNICHAT_ENTRY_FALLBACK_V1_DEFINED

Tests entry phrase handling, typo normalization, and fallback wording.
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
_is_entry_phrase = mod._is_entry_phrase
_normalize_message = mod._normalize_message
_entry_greeting = mod._entry_greeting


def make_response(response_text="I'm not able to process that request.", path="fallback"):
    return {
        "response_text": response_text,
        "path": path,
    }, {
        "final_response_type": "fallback",
        "expansion_layers": [],
        "depth_level": "standard",
    }


# ---------------------------------------------------------------------------
# Entry phrase detection
# ---------------------------------------------------------------------------

def test_greeting_recognized():
    for phrase in ["hi", "hey", "hello", "hallo", "servus"]:
        assert _is_entry_phrase(phrase), f"'{phrase}' should be entry phrase"
    print("PASS: test_greeting_recognized")


def test_start_prompts_recognized():
    for phrase in ["start", "help", "what can i do", "what now"]:
        assert _is_entry_phrase(phrase), f"'{phrase}' should be entry phrase"
    print("PASS: test_start_prompts_recognized")


def test_typos_normalized():
    assert _normalize_message("hry") == "hey"
    assert _normalize_message("helo") == "hello"
    assert _normalize_message("welsr") == "WESLR"
    print("PASS: test_typos_normalized")


def test_weslr_query_typo():
    assert _normalize_message("weslr?") == "what is WESLR"
    assert _is_entry_phrase("weslr?")
    print("PASS: test_weslr_query_typo")


def test_typos_routed_to_entry():
    for typo in ["hry", "helo", "welsr"]:
        assert _is_entry_phrase(typo), f"'{typo}' should route to entry"
    print("PASS: test_typos_routed_to_entry")


def test_non_entry_not_recognized():
    # Real queries should NOT be entry phrases
    for phrase in ["show system overview", "random unknown query", "explain proposal iss.not_integrated"]:
        assert not _is_entry_phrase(phrase), f"'{phrase}' should NOT be entry phrase"
    # Note: "what is WESLR" normalizes to "what is weslr" via _TYPO_MAP["welsr"]
    # which IS in _ENTRY_PHRASES, so it routes to entry — this is correct per spec
    # ("weslr?" should be treated like "what is WESLR")
    print("PASS: test_non_entry_not_recognized")


def test_entry_greeting_content():
    greeting = _entry_greeting()
    assert "I'm WESLR" in greeting
    # Phase 3: no quoted commands — capabilities described naturally
    assert "I can" in greeting
    assert "Just tell me" in greeting
    assert "LIMITATION" not in greeting.upper()
    assert "\n" not in greeting  # single paragraph
    # No command strings
    assert '"' not in greeting
    print("PASS: test_entry_greeting_content")


# ---------------------------------------------------------------------------
# Full expand_response with entry phrases
# ---------------------------------------------------------------------------

def test_hey_produces_entry_greeting():
    response, policy = make_response()
    result = expand_response(response, policy, "hey")

    assert "response_text" in result
    rt = result["response_text"]
    assert "I'm WESLR" in rt
    assert "LIMITATION" not in rt.upper()
    assert "structured" not in rt.lower() or "what is WESLR" in rt.lower()
    print("PASS: test_hey_produces_entry_greeting")


def test_hello_produces_entry_greeting():
    response, policy = make_response()
    result = expand_response(response, policy, "hello")

    assert "I'm WESLR" in result["response_text"]
    print("PASS: test_hello_produces_entry_greeting")


def test_hallo_produces_entry_greeting():
    response, policy = make_response()
    result = expand_response(response, policy, "hallo")

    assert "I'm WESLR" in result["response_text"]
    print("PASS: test_hallo_produces_entry_greeting")


def test_servus_produces_entry_greeting():
    response, policy = make_response()
    result = expand_response(response, policy, "servus")

    assert "I'm WESLR" in result["response_text"]
    print("PASS: test_servus_produces_entry_greeting")


def test_help_produces_entry_greeting():
    response, policy = make_response()
    result = expand_response(response, policy, "help")

    assert "I'm WESLR" in result["response_text"]
    print("PASS: test_help_produces_entry_greeting")


def test_start_produces_entry_greeting():
    response, policy = make_response()
    result = expand_response(response, policy, "start")

    assert "I'm WESLR" in result["response_text"]
    print("PASS: test_start_produces_entry_greeting")


def test_what_can_i_do_produces_entry_greeting():
    response, policy = make_response()
    result = expand_response(response, policy, "what can i do")

    assert "I'm WESLR" in result["response_text"]
    print("PASS: test_what_can_i_do_produces_entry_greeting")


def test_hry_routes_to_entry():
    response, policy = make_response()
    result = expand_response(response, policy, "hry")

    assert "I'm WESLR" in result["response_text"]
    print("PASS: test_hry_routes_to_entry")


def test_helo_routes_to_entry():
    response, policy = make_response()
    result = expand_response(response, policy, "helo")

    assert "I'm WESLR" in result["response_text"]
    print("PASS: test_helo_routes_to_entry")


def test_welsr_routes_to_entry():
    response, policy = make_response()
    result = expand_response(response, policy, "welsr")

    assert "I'm WESLR" in result["response_text"]
    print("PASS: test_welsr_routes_to_entry")


# ---------------------------------------------------------------------------
# Unknown input fallback
# ---------------------------------------------------------------------------

def test_unknown_input_not_robotic():
    response, policy = make_response()
    result = expand_response(response, policy, "qzxuepqoir")

    rt = result["response_text"]
    # Not robotic
    assert "LIMITATION" not in rt.upper()
    assert "not built in" not in rt.lower()
    assert "LIMITATION" not in rt
    # Friendly — Phase 4 evidence offer wording
    assert any(kw in rt.lower() for kw in ["don't have a confirmed", "look into", "keeping it"]), \
        f"Unknown input doesn't feel natural: {rt!r}"
    print("PASS: test_unknown_input_not_robotic")


def test_unknown_input_still_natural():
    response, policy = make_response()
    result = expand_response(response, policy, "asdfqwer")

    rt = result["response_text"]
    # Single paragraph, no numbered lists
    assert "\n1." not in rt
    assert "\n- " not in rt
    # No JSON/internal markers
    assert "expanded_response" not in rt
    assert "structured truth" not in rt.lower()
    # Phase 4: evidence offer is natural, conversational
    assert any(kw in rt.lower() for kw in ["look into", "what i find", "separate", "confirmed"]), \
        f"Unknown input doesn't include evidence offer: {rt!r}"
    print("PASS: test_unknown_input_still_natural")


# ---------------------------------------------------------------------------
# Metadata preservation
# ---------------------------------------------------------------------------

def test_metadata_preserved_entry():
    response, policy = make_response()
    result = expand_response(response, policy, "hey")

    assert "_omnichat_policy" in result
    assert "expanded_response" in result
    assert result["expanded_response"]["guidance"] == ""
    print("PASS: test_metadata_preserved_entry")


def test_metadata_preserved_unknown():
    response, policy = make_response()
    result = expand_response(response, policy, "random query")

    assert "_omnichat_policy" in result
    assert "expanded_response" in result
    print("PASS: test_metadata_preserved_unknown")


# ---------------------------------------------------------------------------
# No structural leakage in entry responses
# ---------------------------------------------------------------------------

def test_no_structural_leakage_entry():
    response, policy = make_response()
    for msg in ["hi", "hey", "hello", "start", "help", "hry", "helo", "welsr"]:
        result = expand_response(response, policy, msg)
        rt = result["response_text"].lower()
        forbidden = [
            "LIMITATION", "structured truth", "Evidence —",
            "expanded_response.", "not part of",
        ]
        for marker in forbidden:
            assert marker.lower() not in rt, f"'{marker}' leaked in entry response for '{msg}'"
    print("PASS: test_no_structural_leakage_entry")


# ---------------------------------------------------------------------------
# No-write proof
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


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

tests = [
    # Entry phrase detection
    test_greeting_recognized,
    test_start_prompts_recognized,
    test_typos_normalized,
    test_weslr_query_typo,
    test_typos_routed_to_entry,
    test_non_entry_not_recognized,
    test_entry_greeting_content,
    # Full expand_response with entry phrases
    test_hey_produces_entry_greeting,
    test_hello_produces_entry_greeting,
    test_hallo_produces_entry_greeting,
    test_servus_produces_entry_greeting,
    test_help_produces_entry_greeting,
    test_start_produces_entry_greeting,
    test_what_can_i_do_produces_entry_greeting,
    test_hry_routes_to_entry,
    test_helo_routes_to_entry,
    test_welsr_routes_to_entry,
    # Unknown input
    test_unknown_input_not_robotic,
    test_unknown_input_still_natural,
    # Metadata
    test_metadata_preserved_entry,
    test_metadata_preserved_unknown,
    # Leakage
    test_no_structural_leakage_entry,
    # No-write
    test_no_write_calls,
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
