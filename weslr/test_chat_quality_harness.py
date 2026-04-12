import os
import sys
import re

CORE = os.environ.get("WESLR_CORE_PATH")
if not CORE:
    raise SystemExit("WESLR_CORE_PATH required")
if CORE not in sys.path:
    sys.path.insert(0, CORE)

from weslr.ingress_adapter import route_request

FALLBACK_PATTERNS = [
    r"tell me a bit more",
    r"ill help you work through it",
    r"try a simple plan",
    r"draft the email goal",
    r"ok"  # generic short
]

def is_fallback(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in FALLBACK_PATTERNS)


def send(msg: str):
    resp = route_request({"message": msg, "workspace_id": "ws1", "user_id": "userA"})
    return resp.content or "", resp.metadata or {}

def test_modes_and_context():
    # A) chat mode for normal prompts, no status leakage
    normal_msgs = [
        "Hey",
        "What should I eat for lunch?",
        "I want to eat lighter today because I may work out later.",
        "Help me plan my afternoon.",
        "I also need to send an important email.",
    ]
    replies = []
    for m in normal_msgs:
        txt, meta = send(m)
        replies.append((m, txt, meta))
        assert not (txt.lower().startswith("we see that signal: status summary")), f"Status leakage on '{m}'"
    # B) status mode only for explicit prompts
    status_msgs = ["what matters now?", "anything important?"]
    for m in status_msgs:
        txt, meta = send(m)
        assert txt.lower().startswith("we see that signal: status summary"), f"Status not returned on '{m}'"
    # C) continuity/context check: later replies should not all be identical; require some variation
    texts = [t for _, t, _ in replies]
    assert len(set(texts)) > 2, "Replies look identical / no variation"
    # D) generic reply detection: allow some generic, but not all
    fallback_count = sum(1 for _, t, _ in replies if is_fallback(t))
    assert fallback_count < len(replies), "All replies fallback-heavy"


def test_context_use():
    flow = [
        "light meal before workout",
        "lunch suggestion",
        "afternoon planning",
        "important email",
        "workout timing",
    ]
    got = []
    for m in flow:
        txt, meta = send(m)
        got.append(txt)
    # continuity heuristic: check that not all replies are the same and at least one references planning/food/email/workout
    text_blob = " ".join(got).lower()
    hits = sum(1 for kw in ["lunch", "meal", "afternoon", "email", "workout"] if kw in text_blob)
    assert hits >= 2, "Context hints not present in replies"


def run_suite():
    ok = True
    errors = []
    for test in [test_modes_and_context, test_context_use]:
        try:
            test()
        except AssertionError as e:
            ok = False
            errors.append(str(e))
    print("RESULT:", "PASS" if ok else "FAIL")
    if errors:
        for e in errors:
            print("ERROR:", e)
    return ok

if __name__ == "__main__":
    success = run_suite()
    sys.exit(0 if success else 1)
