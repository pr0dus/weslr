"""
WESLR OmniChat Inline Guidance V1 — Tests
Verdict label: WESLR_OMNICHAT_INLINE_GUIDANCE_DEFINED

Tests that guidance uses capability phrasing, not command strings.
"""

import ast
import importlib.util
import inspect
import re
import sys

spec = importlib.util.spec_from_file_location(
    "response_expander",
    "weslr/omnichat/response_expander.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules["weslr.omnichat.response_expander"] = mod
spec.loader.exec_module(mod)

expand_response = mod.expand_response
_capability_for_path = mod._capability_for_path
_entry_greeting = mod._entry_greeting


# Patterns that indicate command strings (forbidden in response_text)
_COMMAND_PATTERNS = [
    re.compile(r'"[^"]+"'),          # double-quoted strings
    re.compile(r"'[^']+'"),          # single-quoted strings
    re.compile(r"\b(show|ask|tell|try)\s+[A-Z]"),  # command-like imperative
]
# Specific forbidden command substrings
_FORBIDDEN_COMMANDS = frozenset({
    '"show system overview"',
    '"show diagnostics"',
    '"show proposals"',
    '"show iss probes"',
    '"show capabilities"',
    '"what is WESLR"',
    '"why was WESLR created"',
    '"how is WESLR different from ChatGPT"',
    '"explain proposal iss.not_integrated"',
})

# Forbidden structural markers
_FORBIDDEN_LEAKAGE = [
    "LIMITATION",
    "structured truth",
    "Evidence —",
    "expanded_response.",
]


def make_response(response_text="test answer", path="system_definition_query",
                  final_type="deterministic"):
    return {
        "response_text": response_text,
        "path": path,
    }, {
        "final_response_type": final_type,
        "expansion_layers": [],
        "depth_level": "standard",
    }


# ---------------------------------------------------------------------------
# Helper: check no command strings in text
# ---------------------------------------------------------------------------

def _has_command_string(text: str) -> bool:
    """Return True if text contains a quoted command string."""
    for cmd in _FORBIDDEN_COMMANDS:
        if cmd in text:
            return True
    return False


# ---------------------------------------------------------------------------
# Entry greeting
# ---------------------------------------------------------------------------

def test_entry_greeting_no_command_strings():
    greeting = _entry_greeting()
    assert not _has_command_string(greeting), \
        f"Entry greeting contains command string: {greeting!r}"
    print("PASS: test_entry_greeting_no_command_strings")


def test_entry_greeting_capability_phrasing():
    greeting = _entry_greeting()
    # Should describe capabilities, not list commands
    assert "I can" in greeting
    assert "Just tell me" in greeting
    print("PASS: test_entry_greeting_capability_phrasing")


# ---------------------------------------------------------------------------
# Capability map — no command strings
# ---------------------------------------------------------------------------

def test_capability_map_no_command_strings():
    for path in mod._CAPABILITY_MAP:
        cap = _capability_for_path(path)
        assert not _has_command_string(cap), \
            f"Path {path!r} has command string: {cap!r}"
    print("PASS: test_capability_map_no_command_strings")


def test_capability_map_capability_prefix():
    for path in mod._CAPABILITY_MAP:
        cap = _capability_for_path(path)
        if cap:
            assert cap.startswith("I can "), \
                f"Path {path!r} doesn't start with 'I can ': {cap!r}"
    print("PASS: test_capability_map_capability_prefix")


def test_all_paths_covered():
    known_paths = [
        "system_definition_query",
        "operator_overview",
        "ISS_probe_registry_query",
        "ISS_probe_plan",
        "implementation_plan_query",
        "proposal_trace_query",
        "state_checkpoint_query",
        "iss_intake_query",
    ]
    for path in known_paths:
        assert path in mod._CAPABILITY_MAP, f"Path {path!r} not in _CAPABILITY_MAP"
    print("PASS: test_all_paths_covered")


# ---------------------------------------------------------------------------
# Full expand_response — no command strings
# ---------------------------------------------------------------------------

def test_deterministic_no_command_strings():
    for path in mod._CAPABILITY_MAP:
        response, policy = make_response("WESLR is a governed entity intelligence system.", path=path)
        result = expand_response(response, policy, "test")
        rt = result["response_text"]
        assert not _has_command_string(rt), \
            f"deterministic/{path}: {rt!r}"
    print("PASS: test_deterministic_no_command_strings")


def test_guided_no_command_strings():
    for path in mod._CAPABILITY_MAP:
        response, policy = make_response("Here is some information.", path=path, final_type="guided")
        result = expand_response(response, policy, "test")
        rt = result["response_text"]
        assert not _has_command_string(rt), \
            f"guided/{path}: {rt!r}"
    print("PASS: test_guided_no_command_strings")


def test_fallback_no_command_strings():
    response, policy = make_response(final_type="fallback")
    result = expand_response(response, policy, "random unknown thing")
    rt = result["response_text"]
    assert not _has_command_string(rt), f"fallback: {rt!r}"
    print("PASS: test_fallback_no_command_strings")


def test_entry_phrases_no_command_strings():
    for phrase in ["hi", "hey", "hello", "start", "help"]:
        response, policy = make_response(final_type="fallback")
        result = expand_response(response, policy, phrase)
        rt = result["response_text"]
        assert not _has_command_string(rt), \
            f"entry phrase {phrase!r}: {rt!r}"
    print("PASS: test_entry_phrases_no_command_strings")


# ---------------------------------------------------------------------------
# Guidance still semantically present
# ---------------------------------------------------------------------------

def test_deterministic_guidance_semantic():
    response, policy = make_response("WESLR is a governed system.", path="operator_overview")
    result = expand_response(response, policy, "test")
    rt = result["response_text"]
    # Should still have guidance appended inline
    assert "I can" in rt or "diagnostics" in rt.lower() or "proposals" in rt.lower()
    print("PASS: test_deterministic_guidance_semantic")


def test_fallback_feels_natural():
    response, policy = make_response(final_type="fallback")
    result = expand_response(response, policy, "asdfqwer")
    rt = result["response_text"]
    # No robotic markers
    assert "LIMITATION" not in rt.upper()
    assert "\n1." not in rt
    assert "\n- " not in rt
    print("PASS: test_fallback_feels_natural")


# ---------------------------------------------------------------------------
# No metadata leakage
# ---------------------------------------------------------------------------

def test_no_leakage_in_entry():
    response, policy = make_response(final_type="fallback")
    result = expand_response(response, policy, "hi")
    rt = result["response_text"]
    for marker in _FORBIDDEN_LEAKAGE:
        assert marker not in rt, f"leaked {marker!r} in entry response"
    print("PASS: test_no_leakage_in_entry")


def test_no_leakage_in_deterministic():
    response, policy = make_response("Structured answer.", path="system_definition_query")
    result = expand_response(response, policy, "test")
    rt = result["response_text"]
    for marker in _FORBIDDEN_LEAKAGE:
        assert marker not in rt, f"leaked {marker!r} in deterministic response"
    print("PASS: test_no_leakage_in_deterministic")


# ---------------------------------------------------------------------------
# Metadata preserved
# ---------------------------------------------------------------------------

def test_metadata_preserved():
    for final_type in ["deterministic", "guided", "fallback"]:
        response, policy = make_response(final_type=final_type)
        result = expand_response(response, policy, "test")
        assert "_omnichat_policy" in result
        assert "expanded_response" in result
    print("PASS: test_metadata_preserved")


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
    # Entry greeting
    test_entry_greeting_no_command_strings,
    test_entry_greeting_capability_phrasing,
    # Capability map
    test_capability_map_no_command_strings,
    test_capability_map_capability_prefix,
    test_all_paths_covered,
    # No command strings in full responses
    test_deterministic_no_command_strings,
    test_guided_no_command_strings,
    test_fallback_no_command_strings,
    test_entry_phrases_no_command_strings,
    # Semantic guidance
    test_deterministic_guidance_semantic,
    test_fallback_feels_natural,
    # No leakage
    test_no_leakage_in_entry,
    test_no_leakage_in_deterministic,
    # Metadata
    test_metadata_preserved,
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
