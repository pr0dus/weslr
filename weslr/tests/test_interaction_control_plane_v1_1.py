"""test_interaction_control_plane_v1_1.py — Structural filtering upgrade."""
from __future__ import annotations
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/.openclaw/workspace')

from interpretation import (
    _eliminate_impossible_frames,
    _select_best_frame,
    _classify_interaction_frame,
    interpret_human_turn,
)

def run():
    print("=== test_interaction_control_plane_v1_1 ===\n")

    # ── _eliminate_impossible_frames ────────────────────────────────────────
    print("[_eliminate_impossible_frames]")
    tests = [
        ("hello",               {"entry"}),
        ("hey",                {"entry"}),
        ("hi there",            {"entry"}),
        ("I want to learn coding",    {"task_help", "exploration"}),
        ("help me build a website",  {"task_help", "exploration"}),
        ("can you help me",           {"task_help", "exploration"}),
        ("what is a neural network", {"explanation"}),
        ("explain python",            {"explanation"}),
        ("tell me about python",      {"explanation"}),
        ("show me how to code",       {"task_help", "exploration"}),  # overlap
        ("show system overview",      {"system"}),
        ("random nonsense xyz",       {"unknown"}),
        ("asdasd123",                 {"unknown"}),
        ("",                          {"unknown"}),
    ]
    all_ok = True
    for msg, expected in tests:
        result = _eliminate_impossible_frames(msg)
        ok = result == expected
        status = "✓" if ok else "✗"
        if not ok:
            all_ok = False
        print(f"  {status} {msg!r:40s} → {result!r}  {'expected '+str(expected) if not ok else ''}")

    # ── _select_best_frame ───────────────────────────────────────────────────
    print("\n[_select_best_frame]")
    priority_tests = [
        ({},                        "unknown"),      # empty set → unknown
        ({"unknown"},               "unknown"),
        ({"entry"},                 "entry"),
        ({"task_help", "exploration"}, "task_help"),  # task_help wins
        ({"explanation", "entry"},  "explanation"),   # explanation wins
        ({"exploration", "entry"},   "exploration"),   # exploration wins
        ({"system", "task_help"},   "task_help"),      # task_help wins
        ({"entry", "explanation", "task_help"}, "task_help"),  # highest priority
    ]
    for frames, expected in priority_tests:
        result = _select_best_frame(frames)
        ok = result == expected
        status = "✓" if ok else "✗"
        if not ok:
            all_ok = False
        print(f"  {status} {frames!r:40s} → {result!r}  {'expected '+expected if not ok else ''}")

    # ── Full interpret_human_turn integration ────────────────────────────────
    print("\n[interpret_human_turn — interaction_frame propagation]")
    integration_tests = [
        ("hello",             "entry",       "conversational_entry"),
        ("I want to learn coding", "task_help", "guided_help"),
        ("what is a neural network", "explanation", "structured_answer"),
        ("random xyz",        "unknown",      "uncertainty"),
    ]
    for msg, expected_frame, expected_turn_type in integration_tests:
        r = interpret_human_turn(msg)
        frame = r.get("interaction_frame")
        turn_type = r.get("turn_type")
        ok = frame == expected_frame
        status = "✓" if ok else "✗"
        if not ok:
            all_ok = False
        print(f"  {status} {msg!r:35s} frame={frame!r:15s} turn_type={turn_type!r}  {'expected '+expected_frame if not ok else ''}")

    # ── No regression: existing path still works ──────────────────────────────
    print("\n[no regression — backend paths]")
    r = interpret_human_turn("hello")
    assert r.get("path") == "fallback_safe", f"entry path broken: {r.get('path')}"
    assert r.get("interaction_frame") == "entry", f"entry frame broken: {r.get('interaction_frame')}"
    print("  ✓ hello → fallback_safe (entry frame detected)")

    r = interpret_human_turn("I want to learn coding")
    assert r.get("path") == "task_help_query", f"task_help path broken: {r.get('path')}"
    print("  ✓ task_help_query path intact")

    r = interpret_human_turn("asdasd123")
    assert r.get("path") == "fallback_safe", f"fallback path broken: {r.get('path')}"
    print("  ✓ fallback_safe path intact")

    print()
    if all_ok:
        print("=== WESLR_INTERACTION_CONTROL_PLANE_V1_1_OK ===")
    else:
        print("=== FAILURES DETECTED ===")
        raise SystemExit(1)

if __name__ == "__main__":
    run()
