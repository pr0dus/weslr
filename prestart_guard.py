#!/bin/bash
# Prestart guard for Weslr embedded inference
# Add this to llm_runtime.py after health_endpoint() function

def prestart_guard() -> tuple[bool, str]:
    """Guard: refuse to start if embedded configured but server unreachable."""
    provider = (CIRCLEFORGE_LLM_PROVIDER or "fallback").strip().lower()
    if provider != "embedded":
        return True, "not embedded provider"
    h = health()
    if h["server_ready"]:
        return True, "server ready"
    return False, f"embedded server not ready: {h.get('status', 'unknown')}"
