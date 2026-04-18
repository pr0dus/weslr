"""
Regression tests for /chat internal capability routing.

Validates that factual/system questions are routed through WESLR's own
modules (datetime, load_failsafe_status, load_llm_status) rather than
falling through to the generic LLM simple_response() fallback.

These tests pin the behavior fixed in commit 4046305 so future changes
cannot silently revert the routing.

Tests go through the HTTP /chat endpoint — the actual boundary both
text and voice input traverse.
"""
import pytest
import re
import json
import subprocess


@pytest.fixture(scope="module")
def _server():
    """Ensure the WESLR server is running on port 8001."""
    # Check if already running
    import socket
    s = socket.socket()
    result = s.connect_ex(('127.0.0.1', 8001))
    s.close()
    if result == 0:
        # Already running
        yield
        return

    # Start it
    import os, signal
    proc = subprocess.Popen(
        ["python", "main.py", "serve", "--port", "8001"],
        cwd="/data/data/com.termux/files/home/.openclaw/workspace",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    import time
    time.sleep(10)  # Wait for startup
    yield
    # Teardown
    proc.terminate()
    proc.wait(timeout=5)


def _chat(message: str, timeout: float = 10.0) -> dict:
    """Call /chat and return parsed JSON response."""
    proc = subprocess.run(
        ["curl", "-s", "--max-time", str(timeout), "-X", "POST",
         "http://127.0.0.1:8001/chat",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"message": message})],
        capture_output=True, text=True,
    )
    return json.loads(proc.stdout)


# ─── Internal fact routing — time ────────────────────────────────────────────

def test_time_question_returns_clock_value(_server):
    """'What time is it?' must return actual clock output, not generic fallback."""
    result = _chat("what time is it")
    msg = result["message"]
    # Must contain a time pattern like "HH:MM"
    assert re.search(r"\d{1,2}:\d{2}", msg), f"Expected clock time, got: {msg!r}"
    # Must NOT be the generic simple_response fallback
    assert "I'm here. Say something simple" not in msg


def test_time_question_includes_timezone(_server):
    """Clock response must include timezone reference."""
    result = _chat("what time is it")
    msg = result["message"]
    assert any(tz in msg for tz in ["Europe/Berlin", "UTC", "local time"]), f"Expected timezone in: {msg!r}"


# ─── Internal fact routing — system status ────────────────────────────────────

def test_system_status_returns_weslr_status(_server):
    """'What is your system status?' must use WESLR's own status modules."""
    result = _chat("what is your system status")
    msg = result["message"]
    # Must reference WESLR internal state (initialized/provider), not generic ramble
    assert any(k in msg for k in ["initialized", "not yet initialized", "provider"]), f"Got: {msg!r}"
    # Must NOT be the generic concept explanation ramble
    assert "Aristotle" not in msg


def test_your_status_variant_routes_internally(_server):
    """'your status' variant should also use internal routing."""
    result = _chat("what's your status")
    msg = result["message"]
    assert any(k in msg for k in ["initialized", "not yet initialized", "provider"]), f"Got: {msg!r}"
    assert "Aristotle" not in msg


# ─── Internal fact routing — health ───────────────────────────────────────────

def test_health_question_returns_mode(_server):
    """'Are you healthy?' must use load_failsafe_status, not generic response."""
    result = _chat("are you healthy")
    msg = result["message"]
    assert any(k in msg for k in ["SAFE", "GUIDED", "mode", "operational"]), f"Got: {msg!r}"
    # Must NOT be the generic self-report ramble
    assert "I'm someone trying to understand" not in msg


def test_are_you_ok_routes_internally(_server):
    """'Are you ok?' should also route to internal health path."""
    result = _chat("are you ok")
    msg = result["message"]
    assert any(k in msg for k in ["SAFE", "GUIDED", "mode", "operational"]), f"Got: {msg!r}"


# ─── Internal fact routing — capability ────────────────────────────────────────

def test_capability_question_routes_to_status(_server):
    """'What can you do?' is routed through the status path (captured by 'your capabilities' pattern).

    Note: This phrase is intentionally captured by the status routing in self_report
    branch (status_patterns includes 'your capabilities'). The response correctly
    uses internal state rather than falling through to generic LLM.
    """
    result = _chat("what can you do")
    msg = result["message"]
    # Should reference WESLR internal state, not generic ramble
    assert any(k in msg for k in ["initialized", "not yet initialized", "provider"]), f"Got: {msg!r}"
    # Must NOT be the generic simple_response
    assert "I'm here. Say something simple" not in msg


# ─── Normal prompt — must NOT be captured by system routing ─────────────────────

def test_ordinary_story_prompt_not_captured_by_system_routing(_server):
    """An ordinary non-system prompt must NOT be captured by internal routing."""
    result = _chat("tell me a short story about the moon")
    msg = result["message"]
    # Should NOT be one of the fixed internal responses
    assert not msg.startswith("It is ")   # not a clock response
    assert not msg.startswith("Running in ")  # not a health response


def test_greeting_preserves_existing_behavior(_server):
    """A greeting must still produce the existing simple_response."""
    result = _chat("hello there")
    msg = result["message"]
    # Greeting should still produce simple_response
    assert "I'm here. Say something simple" in msg or "I'm here and responding." in msg