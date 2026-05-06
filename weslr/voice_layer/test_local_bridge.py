"""
test_local_bridge.py — Lightweight smoke tests for local_bridge.py

Tests only:
- module imports
- route_request is the only external cognition path (source inspection)
- error handling — no fake fallback
- voice flag does not auto-speak when disabled
- Response rendering handles all shapes
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ── Test 1: module imports ─────────────────────────────────────────────────

def test_module_imports():
    import weslr.voice_layer.local_bridge as lb
    assert hasattr(lb, "send_to_weslr")
    assert hasattr(lb, "stt_bridge")
    assert hasattr(lb, "main")
    assert hasattr(lb, "_render_response")
    print("  PASS  module imports")
    return True


# ── Test 2: send_to_weslr uses ONLY route_request as cognition ─────────────

def test_send_to_weslr_route_only():
    import inspect, weslr.voice_layer.local_bridge as lb
    src = inspect.getsource(lb.send_to_weslr)
    # Must call route_request
    assert "route_request(" in src, "send_to_weslr must call route_request"
    # Must NOT call forbidden cognition paths
    forbidden = ["llm", "openai", "anthropic", "chatbot", "model(", ".generate("]
    for f in forbidden:
        assert f.lower() not in src.lower(), f"forbidden pattern {f!r} in send_to_weslr"
    print("  PASS  send_to_weslr — route_request only, no competing cognition")
    return True


# ── Test 3: error handling — no fake fallback ──────────────────────────────

def test_no_fake_fallback():
    import weslr.voice_layer.local_bridge as lb
    from unittest.mock import patch

    def failing_route_request(raw):
        raise RuntimeError("simulated route_request failure")

    with patch("weslr.voice_layer.local_bridge.route_request", failing_route_request):
        with patch("weslr.voice_layer.local_bridge._speak_response"):
            try:
                lb.send_to_weslr("test", voice_response=False)
                assert False, "Should have raised"
            except RuntimeError as e:
                assert "simulated route_request failure" in str(e)
    print("  PASS  error propagates — no fake fallback response")
    return True


# ── Test 4: voice flag disabled → no speak ────────────────────────────────

def test_voice_disabled_no_speak():
    import weslr.voice_layer.local_bridge as lb
    from unittest.mock import patch

    speaks = []
    def track_speak(text):
        speaks.append(text)

    class FakeResponse:
        content = "hello"

    with patch("weslr.voice_layer.local_bridge.route_request", return_value=FakeResponse()):
        with patch("weslr.voice_layer.local_bridge._speak_response", track_speak):
            lb.send_to_weslr("hello", voice_response=False)

    assert len(speaks) == 0, f"speak called {len(speaks)} times with voice_response=False"
    print("  PASS  voice_response=False does not auto-speak")
    return True


# ── Test 5: Response rendering handles dict / .content / .message ───────────

def test_response_rendering():
    import weslr.voice_layer.local_bridge as lb

    d = {"content": "from dict"}
    obj_content = type("R", (), {"content": "from content attr"})()
    obj_message = type("R", (), {"message": "from message attr"})()
    assert lb._render_response(d) == "from dict"
    assert lb._render_response(obj_content) == "from content attr"
    assert lb._render_response(obj_message) == "from message attr"
    print("  PASS  _render_response handles dict/.content/.message")
    return True


# ── Test 6: CLI entry point callable ──────────────────────────────────────

def test_main_callable():
    from weslr.voice_layer.local_bridge import main
    import argparse
    # main should be callable and use argparse
    import inspect
    assert callable(main)
    src = inspect.getsource(main)
    assert "argparse" in src
    print("  PASS  main() entry point is argparse-based CLI")
    return True


# ── Run all ─────────────────────────────────────────────────────────────────

def main():
    print("\ntest_local_bridge.py")
    print("=" * 50)
    tests = [
        test_module_imports,
        test_send_to_weslr_route_only,
        test_no_fake_fallback,
        test_voice_disabled_no_speak,
        test_response_rendering,
        test_main_callable,
    ]
    passed = 0
    for t in tests:
        try:
            if t():
                passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\nRESULT: {passed}/{len(tests)} passed\n")


if __name__ == "__main__":
    main()