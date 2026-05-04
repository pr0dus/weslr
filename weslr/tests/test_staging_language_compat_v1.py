#!/usr/bin/env python3
"""
WESLR Staging Language Compatibility V1 — Tests

Validates:
- uncertainty_strong_response exists in language modules (en, de)
- en.uncertainty_strong_response() returns a string
- de.uncertainty_strong_response() returns a string
- both are different from uncertainty_response
- both are JSON-serializable
- backend contract no longer errors for "hello" and unknown inputs
- signal hook tests still pass

Confirms: STAGING_LANGUAGE_COMPAT_V1_OK
Exits non-zero on any failure.
"""

import sys
import json
import importlib
from pathlib import Path

_workspace = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_workspace))

PASS = 0
FAIL = 0


def check(condition: bool, description: str):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK: {description}")
    else:
        FAIL += 1
        print(f"  FAIL: {description}")


# ---------------------------------------------------------------------------
# SECTION 1 — en.py has uncertainty_strong_response
# ---------------------------------------------------------------------------
print("\nTest 1: en.py has uncertainty_strong_response")
import en
importlib.reload(en)
check(hasattr(en, "uncertainty_strong_response"), "en.uncertainty_strong_response exists")
result = en.uncertainty_strong_response()
check(isinstance(result, str), "en.uncertainty_strong_response() returns str")
check(len(result) > 5, "en.uncertainty_strong_response() returns non-empty string")

# ---------------------------------------------------------------------------
# SECTION 2 — de.py has uncertainty_strong_response
# ---------------------------------------------------------------------------
print("\nTest 2: de.py has uncertainty_strong_response")
import de
importlib.reload(de)
check(hasattr(de, "uncertainty_strong_response"), "de.uncertainty_strong_response exists")
result = de.uncertainty_strong_response()
check(isinstance(result, str), "de.uncertainty_strong_response() returns str")
check(len(result) > 5, "de.uncertainty_strong_response() returns non-empty string")

# ---------------------------------------------------------------------------
# SECTION 3 — uncertainty_strong_response differs from uncertainty_response
# ---------------------------------------------------------------------------
print("\nTest 3: uncertainty_strong_response differs from uncertainty_response")
en_strong = en.uncertainty_strong_response()
en_weak = en.uncertainty_response()
check(en_strong != en_weak, "en.uncertainty_strong_response differs from uncertainty_response")
check(json.dumps({"text": en_strong}), "en strong response JSON-serializable")

de_strong = de.uncertainty_strong_response()
de_weak = de.uncertainty_response()
check(de_strong != de_weak, "de.uncertainty_strong_response differs from uncertainty_response")
check(json.dumps({"text": de_strong}), "de strong response JSON-serializable")

# ---------------------------------------------------------------------------
# SECTION 4 — Backend contract no longer errors for "hello" and unknown input
# ---------------------------------------------------------------------------
print("\nTest 4: backend contract no longer errors for 'hello' and unknown input")
import weslr_backend_contract
importlib.reload(weslr_backend_contract)
from weslr_backend_contract import chat

test_messages = [
    "hello",
    "what is this?",
    "asdfghjkl nonsense",
    "tell me about something",
]
for msg in test_messages:
    try:
        r = chat(msg)
        check(isinstance(r, dict), f"chat({msg[:15]!r}) returns dict")
        check("success" in r and "reply" in r, f"  has success/reply keys")
        check(r.get("intent") is not None, f"  intent is not None")
        check(json.dumps(r), f"  response JSON-serializable")
    except AttributeError as e:
        if "uncertainty_strong_response" in str(e):
            check(False, f"uncertainty_strong_response missing error: {e}")
        else:
            check(False, f"AttributeError on {msg[:15]!r}: {e}")
    except Exception as e:
        check(False, f"Exception on {msg[:15]!r}: {e}")

# ---------------------------------------------------------------------------
# SECTION 5 — Signal hook still executes correctly (import from other test)
# ---------------------------------------------------------------------------
print("\nTest 5: signal hook still executes for all response paths")
from weslr.website_signal_integration import capture_website_signal

for msg in test_messages:
    r = chat(msg)
    try:
        capture_website_signal(
            message=msg,
            session_id="lang_compat_test",
            response_path=r.get("source") or r.get("intent", {}).get("path", "unknown"),
            quality_class=r.get("intent", {}).get("_quality_class") or "unknown",
            blocked_write=r.get("intent", {}).get("path") == "blocked_write",
            evidence_offer_shown=bool(
                r.get("intent", {}).get("_omnichat_policy", {}).get("evidence_offer")
                if isinstance(r.get("intent", {}).get("_omnichat_policy"), dict)
                else False
            ),
            evidence_offer_accepted=False,
            topic_normalized=(
                r.get("intent", {}).get("topics", [None])[0]
                if r.get("intent", {}).get("topics")
                else None
            ),
            fallback_triggered=r.get("intent", {}).get("path") in ("fallback_safe", "fallback_template"),
        )
        check(True, f"signal hook ok for {msg[:15]!r}")
    except Exception as e:
        check(False, f"signal hook error for {msg[:15]!r}: {e}")

# ---------------------------------------------------------------------------
# SECTION 6 — JSON-serializable for all paths
# ---------------------------------------------------------------------------
print("\nTest 6: all response paths JSON-serializable")
for msg in test_messages:
    r = chat(msg)
    try:
        json.dumps(r, ensure_ascii=False)
        check(True, f"JSON ok for {msg[:15]!r}")
    except Exception as e:
        check(False, f"JSON error for {msg[:15]!r}: {e}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    if FAIL:
        print("STAGING_LANGUAGE_COMPAT_V1_FAILED")
        sys.exit(1)
    else:
        print("STAGING_LANGUAGE_COMPAT_V1_OK")
        sys.exit(0)