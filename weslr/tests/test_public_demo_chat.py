from __future__ import annotations

from weslr.public_demo_chat import PUBLIC_DEMO_SOURCE, public_demo_chat


def test_public_demo_chat_identifies_weslr():
    response = public_demo_chat("What is WESLR?")
    assert response["success"] is True
    assert response["read_only"] is True
    assert response["source"] == PUBLIC_DEMO_SOURCE
    assert "continuity-first" in response["reply"]
    assert "governed memory" in response["reply"]


def test_public_demo_chat_explains_memory_without_writes():
    response = public_demo_chat("How does governed memory work?")
    assert response["success"] is True
    assert response["mode"] == "public_demo_readonly"
    assert "scoped" in response["reply"]
    assert "silently remember everything" in response["reply"]


def test_public_demo_chat_explains_private_deployment():
    response = public_demo_chat("What is private deployment?")
    assert response["success"] is True
    assert "control over data location" in response["reply"]


def test_public_demo_chat_explains_agent_ecosystem():
    response = public_demo_chat("Can Claude or OpenClaw use WESLR through an API?")
    assert response["success"] is True
    assert "compatible agents" in response["reply"]
    assert "private and institutional" in response["reply"]


def test_public_demo_chat_pricing_copy_is_bounded():
    response = public_demo_chat("What does WESLR cost?")
    assert response["success"] is True
    assert "1-month free trial" in response["reply"]
    assert "€80/month" in response["reply"]
    assert "quote-based" in response["reply"]


def test_public_demo_chat_fallback_stays_read_only():
    response = public_demo_chat("Please upload a file and run tools")
    assert response["success"] is True
    assert response["read_only"] is True
    assert "read-only" in response["reply"]
    assert "does not upload files" in response["reply"]
