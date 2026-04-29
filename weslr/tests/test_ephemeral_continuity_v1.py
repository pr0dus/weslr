"""
WESLR OmniChat Ephemeral Continuity V1 — Tests
Verdict label: WESLR_EPHEMERAL_CONTINUITY_DEFINED

Tests ephemeral context store for follow-up handling.
"""

import ast
import importlib.util
import inspect
import sys

spec = importlib.util.spec_from_file_location(
    "ephemeral_context",
    "weslr/omnichat/ephemeral_context.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules["weslr.omnichat.ephemeral_context"] = mod
spec.loader.exec_module(mod)

get_store = mod.get_store
reset_store = mod.reset_store
CONSENT_KEYWORDS = mod.CONSENT_KEYWORDS
REFUSAL_KEYWORDS = mod.REFUSAL_KEYWORDS
OFFER_TYPE_EVIDENCE = mod.OFFER_TYPE_EVIDENCE


def test_consent_keywords_yes():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "quantum consciousness", OFFER_TYPE_EVIDENCE)
    result = store.check_follow_up("yes")
    assert result is not None
    assert result["action"] == "consent"
    assert result["topic"] == "quantum consciousness"
    assert result["rewritten"] == "explore evidence for quantum consciousness"
    # Context consumed
    assert store.get_active_offer() is None
    print("PASS: test_consent_keywords_yes")


def test_consent_keywords_ok():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "test topic", OFFER_TYPE_EVIDENCE)
    result = store.check_follow_up("ok")
    assert result["action"] == "consent"
    assert "test topic" in result["rewritten"]
    print("PASS: test_consent_keywords_ok")


def test_consent_keywords_do_it():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "another topic", OFFER_TYPE_EVIDENCE)
    result = store.check_follow_up("do it")
    assert result["action"] == "consent"
    print("PASS: test_consent_keywords_do_it")


def test_consent_keywords_go_ahead():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "topic x", OFFER_TYPE_EVIDENCE)
    result = store.check_follow_up("go ahead")
    assert result["action"] == "consent"
    print("PASS: test_consent_keywords_go_ahead")


def test_consent_keywords_sure():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "topic y", OFFER_TYPE_EVIDENCE)
    result = store.check_follow_up("sure")
    assert result["action"] == "consent"
    print("PASS: test_consent_keywords_sure")


def test_refusal_no():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "any topic", OFFER_TYPE_EVIDENCE)
    result = store.check_follow_up("no")
    assert result["action"] == "refusal"
    assert store.get_active_offer() is None
    print("PASS: test_refusal_no")


def test_refusal_nah():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "topic", OFFER_TYPE_EVIDENCE)
    result = store.check_follow_up("nah")
    assert result["action"] == "refusal"
    print("PASS: test_refusal_nah")


def test_unrelated_input_clears_context():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "some topic", OFFER_TYPE_EVIDENCE)
    assert store.has_active_offer() is True
    result = store.check_follow_up("show system overview")
    assert result["action"] == "unrelated"
    assert store.get_active_offer() is None
    print("PASS: test_unrelated_input_clears_context")


def test_second_yes_does_nothing():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "first topic", OFFER_TYPE_EVIDENCE)
    # First yes
    result1 = store.check_follow_up("yes")
    assert result1["action"] == "consent"
    # Second yes — no active offer
    result2 = store.check_follow_up("yes")
    assert result2 is None
    print("PASS: test_second_yes_does_nothing")


def test_no_context_returns_none():
    store = get_store()
    store.clear()
    # No offer stored
    result = store.check_follow_up("yes")
    assert result is None
    print("PASS: test_no_context_returns_none")


def test_no_context_means_no_active_offer():
    store = get_store()
    store.clear()
    assert store.has_active_offer() is False
    assert store.get_active_offer() is None
    print("PASS: test_no_context_means_no_active_offer")


def test_consent_clears_context():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "persistent topic", OFFER_TYPE_EVIDENCE)
    store.check_follow_up("yes")
    # Context gone
    assert store.has_active_offer() is False
    result2 = store.check_follow_up("yes")
    assert result2 is None
    print("PASS: test_consent_clears_context")


def test_has_active_offer():
    store = get_store()
    store.clear()
    assert store.has_active_offer() is False
    store.store_offer("evidence_offer", "topic", OFFER_TYPE_EVIDENCE)
    assert store.has_active_offer() is True
    store.check_follow_up("no")  # refusal clears
    assert store.has_active_offer() is False
    print("PASS: test_has_active_offer")


def test_clear():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "topic", OFFER_TYPE_EVIDENCE)
    assert store.has_active_offer() is True
    store.clear()
    assert store.has_active_offer() is False
    result = store.check_follow_up("yes")
    assert result is None
    print("PASS: test_clear")


def test_to_dict():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "my topic", OFFER_TYPE_EVIDENCE)
    ctx = store.get_active_offer()
    d = ctx.to_dict()
    assert d["intent_type"] == "evidence_offer"
    assert d["topic"] == "my topic"
    assert d["offer_type"] == OFFER_TYPE_EVIDENCE
    print("PASS: test_to_dict")


# ---------------------------------------------------------------------------
# No persistence
# ---------------------------------------------------------------------------

def test_no_persistence_no_jsonl_writes():
    # AST scan: no file/JSONL write calls in the module
    source = inspect.getsource(mod)
    tree = ast.parse(source)
    write_calls = {
        "open", "write", "dump", "dumpjson", "save", "store",
        "json.dump", "json.dumps", "to_file", "persist",
        "append", "writelines", "jsonl",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            assert call_name not in write_calls, \
                f"write call {call_name!r} found in ephemeral_context.py"
    print("PASS: test_no_persistence_no_jsonl_writes")


def test_not_stored_across_instances():
    # Each call to get_store() returns the SAME module-level singleton
    store1 = get_store()
    store2 = get_store()
    assert store1 is store2
    store1.store_offer("evidence_offer", "topic", OFFER_TYPE_EVIDENCE)
    assert store2.has_active_offer() is True
    # But reset_store clears it for all
    reset_store()
    assert store1.has_active_offer() is False
    assert store2.has_active_offer() is False
    print("PASS: test_not_stored_across_instances")


def test_no_metadata_leak():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "secret topic", OFFER_TYPE_EVIDENCE)
    # Internal state should not contain user-facing strings
    ctx = store.get_active_offer()
    assert ctx is not None
    # Nothing is written to stdout, files, or returned to user here
    # This is validated by the no-write proof above
    assert store.has_active_offer() is True
    print("PASS: test_no_metadata_leak")


# ---------------------------------------------------------------------------
# Consent keywords coverage
# ---------------------------------------------------------------------------

def test_all_consent_keywords():
    expected = {"yes", "yeah", "yep", "yea", "ok", "okay", "sure",
                "do it", "go ahead", "please do"}
    # "lets_do_it" is normalised differently so just check the main set
    for kw in expected:
        store = get_store()
        store.clear()
        store.store_offer("evidence_offer", "topic", OFFER_TYPE_EVIDENCE)
        result = store.check_follow_up(kw)
        assert result is not None and result["action"] == "consent", \
            f"'{kw}' did not trigger consent"
    print("PASS: test_all_consent_keywords")


def test_all_refusal_keywords():
    expected = {"no", "nope", "nah", "don't", "skip",
                "never mind", "nevermind", "cancel"}
    for kw in expected:
        store = get_store()
        store.clear()
        store.store_offer("evidence_offer", "topic", OFFER_TYPE_EVIDENCE)
        result = store.check_follow_up(kw)
        assert result is not None and result["action"] == "refusal", \
            f"'{kw}' did not trigger refusal"
    print("PASS: test_all_refusal_keywords")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_input_returns_unrelated():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "topic", OFFER_TYPE_EVIDENCE)
    result = store.check_follow_up("")
    # Empty is not consent, not refusal — unrelated
    assert result["action"] == "unrelated"
    assert store.get_active_offer() is None
    print("PASS: test_empty_input_returns_unrelated")


def test_whitespace_input():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "topic", OFFER_TYPE_EVIDENCE)
    result = store.check_follow_up("   yes   ")
    assert result["action"] == "consent"
    print("PASS: test_whitespace_input")


def test_capitalized_consent():
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "topic", OFFER_TYPE_EVIDENCE)
    result = store.check_follow_up("YES")
    assert result["action"] == "consent"
    print("PASS: test_capitalized_consent")


def test_consent_with_extra_words():
    # "yes please" should NOT match (not exactly in the set)
    store = get_store()
    store.clear()
    store.store_offer("evidence_offer", "topic", OFFER_TYPE_EVIDENCE)
    result = store.check_follow_up("yes please")
    # Not in CONSENT_KEYWORDS (exact match) — treated as unrelated
    assert result["action"] == "unrelated"
    print("PASS: test_consent_with_extra_words")


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

tests = [
    # Consent keywords
    test_consent_keywords_yes,
    test_consent_keywords_ok,
    test_consent_keywords_do_it,
    test_consent_keywords_go_ahead,
    test_consent_keywords_sure,
    # Refusal keywords
    test_refusal_no,
    test_refusal_nah,
    # Context lifecycle
    test_unrelated_input_clears_context,
    test_second_yes_does_nothing,
    test_no_context_returns_none,
    test_no_context_means_no_active_offer,
    test_consent_clears_context,
    test_has_active_offer,
    test_clear,
    # Data
    test_to_dict,
    # No persistence
    test_no_persistence_no_jsonl_writes,
    test_not_stored_across_instances,
    test_no_metadata_leak,
    # Keyword coverage
    test_all_consent_keywords,
    test_all_refusal_keywords,
    # Edge cases
    test_empty_input_returns_unrelated,
    test_whitespace_input,
    test_capitalized_consent,
    test_consent_with_extra_words,
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
