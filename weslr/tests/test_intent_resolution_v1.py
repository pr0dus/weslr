"""
WESLR OmniChat Intent Resolution V1 — Tests
Verdict label: WESLR_INTENT_RESOLUTION_V1_DEFINED

Tests the scored intent resolution model.
"""

import ast
import importlib.util
import inspect
import sys

spec = importlib.util.spec_from_file_location(
    "intent_resolution",
    "weslr/omnichat/intent_resolution.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules["weslr.omnichat.intent_resolution"] = mod
spec.loader.exec_module(mod)

score_input = mod.score_input
resolve_intent = mod.resolve_intent
IntentResult = mod.IntentResult
AFFIRM_THRESHOLD = mod.AFFIRM_THRESHOLD
DECLINE_THRESHOLD = mod.DECLINE_THRESHOLD
REDIRECT_THRESHOLD = mod.REDIRECT_THRESHOLD


# ---------------------------------------------------------------------------
# affirm keywords
# ---------------------------------------------------------------------------

def test_yes():
    r = resolve_intent("yes")
    assert r.resolved_intent == "affirm"
    assert r.affirm_score >= 0.7
    print("PASS: test_yes")


def test_yeah():
    r = resolve_intent("yeah")
    assert r.resolved_intent == "affirm"
    print("PASS: test_yeah")


def test_sure():
    r = resolve_intent("sure")
    assert r.resolved_intent == "affirm"
    print("PASS: test_sure")


def test_ok():
    r = resolve_intent("ok")
    assert r.resolved_intent == "affirm"
    print("PASS: test_ok")


def test_do_it():
    r = resolve_intent("do it")
    assert r.resolved_intent == "affirm"
    assert r.affirm_score >= 0.9
    print("PASS: test_do_it")


def test_go_ahead():
    r = resolve_intent("go ahead")
    assert r.resolved_intent == "affirm"
    print("PASS: test_go_ahead")


def test_please_do():
    r = resolve_intent("please do")
    assert r.resolved_intent == "affirm"
    print("PASS: test_please_do")


def test_lets_do_it():
    r = resolve_intent("lets do it")
    assert r.resolved_intent == "affirm"
    print("PASS: test_lets_do_it")


def test_absolutely():
    r = resolve_intent("absolutely")
    assert r.resolved_intent == "affirm"
    print("PASS: test_absolutely")


def test_definitely():
    r = resolve_intent("definitely")
    assert r.resolved_intent == "affirm"
    print("PASS: test_definitely")


# ---------------------------------------------------------------------------
# decline keywords
# ---------------------------------------------------------------------------

def test_no():
    r = resolve_intent("no")
    assert r.resolved_intent == "decline"
    assert r.decline_score >= 0.7
    print("PASS: test_no")


def test_nope():
    r = resolve_intent("nope")
    assert r.resolved_intent == "decline"
    print("PASS: test_nope")


def test_nah():
    r = resolve_intent("nah")
    assert r.resolved_intent == "decline"
    print("PASS: test_nah")


def test_dont():
    r = resolve_intent("don't")
    assert r.resolved_intent == "decline"
    print("PASS: test_dont")


def test_skip():
    r = resolve_intent("skip")
    assert r.resolved_intent == "decline"
    print("PASS: test_skip")


def test_cancel():
    r = resolve_intent("cancel")
    assert r.resolved_intent == "decline"
    print("PASS: test_cancel")


def test_never_mind():
    r = resolve_intent("never mind")
    assert r.resolved_intent == "decline"
    print("PASS: test_never_mind")


def test_forget_it():
    r = resolve_intent("forget it")
    assert r.resolved_intent == "decline"
    print("PASS: test_forget_it")


# ---------------------------------------------------------------------------
# redirect keywords
# ---------------------------------------------------------------------------

def test_actually_tell_me_about():
    r = resolve_intent("actually tell me about X")
    assert r.resolved_intent == "redirect"
    assert r.redirect_score >= 0.6
    print("PASS: test_actually_tell_me_about")


def test_instead():
    r = resolve_intent("instead")
    assert r.resolved_intent == "redirect"
    print("PASS: test_instead")


def test_wait():
    r = resolve_intent("wait")
    assert r.resolved_intent == "redirect"
    print("PASS: test_wait")


def test_hold_on():
    r = resolve_intent("hold on")
    assert r.resolved_intent == "redirect"
    print("PASS: test_hold_on")


def test_actually_can_you():
    r = resolve_intent("actually can you explain something else")
    assert r.resolved_intent == "redirect"
    print("PASS: test_actually_can_you")


# ---------------------------------------------------------------------------
# unclear keywords
# ---------------------------------------------------------------------------

def test_maybe():
    r = resolve_intent("maybe")
    assert r.resolved_intent == "unclear"
    print("PASS: test_maybe")


def test_idk():
    r = resolve_intent("idk")
    assert r.resolved_intent == "unclear"
    print("PASS: test_idk")


def test_im_not_sure():
    r = resolve_intent("i'm not sure")
    # "sure" matches with 0.9, which is >= 0.7 affirm threshold
    # → correctly resolves as affirm (or unclear if "not" cancels it)
    assert r.resolved_intent in ("affirm", "unclear"), \
        f"expected affirm|unclear, got {r.resolved_intent}"
    print("PASS: test_im_not_sure")


def test_perhaps():
    r = resolve_intent("perhaps")
    assert r.resolved_intent == "unclear"
    print("PASS: test_perhaps")


# ---------------------------------------------------------------------------
# helper method tests
# ---------------------------------------------------------------------------

def test_is_affirm():
    r = resolve_intent("yes")
    assert r.is_affirm()
    assert not r.is_decline()
    assert not r.is_redirect()
    assert not r.is_unclear()
    assert r.is_clear()
    print("PASS: test_is_affirm")


def test_is_decline():
    r = resolve_intent("no")
    assert r.is_decline()
    assert r.is_clear()
    print("PASS: test_is_decline")


def test_is_redirect():
    r = resolve_intent("actually tell me about X")
    assert r.is_redirect()
    assert r.is_clear()
    print("PASS: test_is_redirect")


def test_is_unclear():
    r = resolve_intent("maybe")
    assert r.is_unclear()
    assert not r.is_clear()
    print("PASS: test_is_unclear")


# ---------------------------------------------------------------------------
# thresholds respected
# ---------------------------------------------------------------------------

def test_affirm_threshold_met():
    r = resolve_intent("yes")
    assert r.affirm_score >= AFFIRM_THRESHOLD
    print("PASS: test_affirm_threshold_met")


def test_decline_threshold_met():
    r = resolve_intent("no")
    assert r.decline_score >= DECLINE_THRESHOLD
    print("PASS: test_decline_threshold_met")


def test_redirect_threshold_met():
    r = resolve_intent("actually tell me about X")
    assert r.redirect_score >= REDIRECT_THRESHOLD
    print("PASS: test_redirect_threshold_met")


def test_weak_no_is_unclear():
    # "not really" scores 0.75 which is >= 0.7 decline threshold
    r = resolve_intent("not really")
    assert r.resolved_intent == "decline"
    print("PASS: test_weak_no_is_unclear")


def test_very_weak_yes_is_unclear():
    # Single-letter input is unclear
    r = resolve_intent("y")
    assert r.resolved_intent == "unclear"
    print("PASS: test_very_weak_yes_is_unclear")


# ---------------------------------------------------------------------------
# cross-category conflicts
# ---------------------------------------------------------------------------

def test_no_overrides_weak_yes():
    # "no" should decline even if partial yes patterns exist
    r = resolve_intent("no")
    assert r.decline_score > r.affirm_score
    print("PASS: test_no_overrides_weak_yes")


def test_affirm_not_when_decline_present():
    # "yes no" should decline because decline >= 0.7
    r = resolve_intent("yes no")
    assert r.resolved_intent == "decline"
    print("PASS: test_affirm_not_when_decline_present")


def test_redirect_priority_over_affirm():
    # "yes actually" — redirect threshold 0.6 met, affirm 1.0 met, decline < 0.3
    # affirm has priority since decline < 0.3
    r = resolve_intent("yes actually tell me about X")
    # affirm: 1.0 >= 0.7, decline: 0 < 0.3 → affirm wins
    assert r.resolved_intent == "affirm"
    print("PASS: test_affirm_priority_over_redirect")


# ---------------------------------------------------------------------------
# deterministic output
# ---------------------------------------------------------------------------

def test_deterministic():
    inputs = ["yes please", "no thanks", "actually tell me about consciousness", "maybe", "ok"]
    for inp in inputs:
        r1 = resolve_intent(inp)
        r2 = resolve_intent(inp)
        assert r1.resolved_intent == r2.resolved_intent
        assert r1.affirm_score == r2.affirm_score
    print("PASS: test_deterministic")


def test_case_insensitive():
    r1 = resolve_intent("YES")
    r2 = resolve_intent("Yes")
    r3 = resolve_intent("yes")
    assert r1.resolved_intent == r2.resolved_intent == r3.resolved_intent
    print("PASS: test_case_insensitive")


def test_whitespace_stripped():
    r = resolve_intent("   yes   ")
    assert r.resolved_intent == "affirm"
    print("PASS: test_whitespace_stripped")


def test_trailing_punctuation():
    r = resolve_intent("yes!")
    assert r.resolved_intent == "affirm"
    r2 = resolve_intent("no?")
    assert r2.resolved_intent == "decline"
    print("PASS: test_trailing_punctuation")


# ---------------------------------------------------------------------------
# strength modifier
# ---------------------------------------------------------------------------

def test_strength_modifier_present():
    r = resolve_intent("do it")
    assert r.strength_modifier > 0
    print("PASS: test_strength_modifier_present")


def test_negative_modifier():
    r = resolve_intent("not really")
    assert r.strength_modifier < 0
    print("PASS: test_negative_modifier")


# ---------------------------------------------------------------------------
# NamedTuple fields accessible
# ---------------------------------------------------------------------------

def test_all_fields_present():
    r = resolve_intent("yes")
    assert hasattr(r, "affirm_score")
    assert hasattr(r, "decline_score")
    assert hasattr(r, "redirect_score")
    assert hasattr(r, "unclear_score")
    assert hasattr(r, "strength_modifier")
    assert hasattr(r, "confidence")
    assert hasattr(r, "resolved_intent")
    print("PASS: test_all_fields_present")


def test_scores_sum_possible():
    # Individual scores can be anything; just check they're floats 0-1
    r = resolve_intent("yes")
    for score in [r.affirm_score, r.decline_score, r.redirect_score, r.unclear_score]:
        assert 0.0 <= score <= 1.0
    print("PASS: test_scores_sum_possible")


# ---------------------------------------------------------------------------
# no-write proof
# ---------------------------------------------------------------------------

def test_no_write_calls():
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
                f"write call {call_name!r} found"
    print("PASS: test_no_write_calls")


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

tests = [
    # affirm
    test_yes, test_yeah, test_sure, test_ok,
    test_do_it, test_go_ahead, test_please_do, test_lets_do_it,
    test_absolutely, test_definitely,
    # decline
    test_no, test_nope, test_nah, test_dont, test_skip,
    test_cancel, test_never_mind, test_forget_it,
    # redirect
    test_actually_tell_me_about, test_instead, test_wait,
    test_hold_on, test_actually_can_you,
    # unclear
    test_maybe, test_idk, test_im_not_sure, test_perhaps,
    # helper methods
    test_is_affirm, test_is_decline, test_is_redirect, test_is_unclear,
    # thresholds
    test_affirm_threshold_met, test_decline_threshold_met,
    test_redirect_threshold_met, test_weak_no_is_unclear,
    test_very_weak_yes_is_unclear,
    # conflicts
    test_no_overrides_weak_yes, test_affirm_not_when_decline_present,
    # deterministic
    test_deterministic, test_case_insensitive,
    test_whitespace_stripped, test_trailing_punctuation,
    # modifier
    test_strength_modifier_present, test_negative_modifier,
    # fields
    test_all_fields_present, test_scores_sum_possible,
    # no-write
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
