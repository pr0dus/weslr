"""Public demo chat contract.

This module provides a tiny read-only responder for public_demo_readonly mode.
It is intentionally not a general WESLR cognition path and does not write
memory, run tools, access private state, expose operator internals, or call
external providers.
"""

from __future__ import annotations

from typing import Any, Dict

PUBLIC_DEMO_SOURCE = "public_demo_contract"


def _normalize(message: str) -> str:
    return " ".join((message or "").lower().strip().split())


def _reply(text: str, intent: str) -> Dict[str, Any]:
    return {
        "success": True,
        "reply": text,
        "intent": {"path": "public_demo_readonly", "intent": intent},
        "source": PUBLIC_DEMO_SOURCE,
        "mode": "public_demo_readonly",
        "read_only": True,
    }


def public_demo_chat(message: str) -> Dict[str, Any]:
    """Return a safe read-only public demo chat response."""

    text = _normalize(message)

    if not text:
        return _reply(
            "This is a read-only WESLR demo. You can ask what WESLR is, how governed memory works, or why private deployment matters.",
            "empty_message",
        )

    if any(term in text for term in ["what is weslr", "who are you", "what are you", "about weslr"]):
        return _reply(
            "WESLR is a continuity-first reasoning platform for long-running work. It is designed to preserve project context, governed memory, evidence, proposals, and approval boundaries around people, teams, and compatible agents.",
            "weslr_identity",
        )

    if any(term in text for term in ["just another chatbot", "another chatbot", "normal chatbot", "only a chatbot", "just a chatbot"]):
        return _reply(
            "WESLR is not just another chatbot. It is built around continuity, governed memory, evidence, proposal tracking, and approval-aware workflows, so long-running work can stay coherent without silently expanding what WESLR is allowed to do.",
            "weslr_not_chatbot",
        )

    if any(term in text for term in ["improve itself", "self-improve", "self improve", "improve automatically", "automatically improve"]):
        return _reply(
            "WESLR is designed so small cognitive refinements can be evaluated against tests, but governed memory, authority changes, deployment, file handling, and important system-changing actions require approval. This public demo is read-only and does not upload files or apply changes.",
            "self_improvement_boundary",
        )

    if any(term in text for term in ["governed memory", "memory", "remember"]):
        return _reply(
            "Governed memory means WESLR should not silently remember everything. Memory is scoped by person, project, team, company, or institution, and important memory or system-changing actions require clear rules and review.",
            "governed_memory",
        )

    if any(term in text for term in [
        "hosted", "private", "self-hosted", "self hosted", "deployment", "deploy",
        "company", "data location", "data go", "where does the data", "where does my data",
    ]):
        return _reply(
            "Hosted WESLR is the fastest way to start. Private or self-hosted WESLR is for organizations that need control over data location, runtime, access, updates, and integrations.",
            "deployment_options",
        )

    if any(term in text for term in ["demo", "can this demo", "public demo", "what can"]):
        return _reply(
            "This public demo is read-only. It can explain WESLR and selected safe workflows, but it does not upload files, write memory, expose operator controls, execute actions, or deploy anything.",
            "demo_limits",
        )

    if any(term in text for term in ["agent", "claude", "chatgpt", "hermes", "openclaw", "api"]):
        return _reply(
            "WESLR can complement compatible agents and tools by providing continuity, governed memory, evidence, proposal tracking, approval-aware workflow, and compact task context. Agent/API integrations are planned for private and institutional deployments.",
            "agent_ecosystem",
        )

    if any(term in text for term in ["price", "pricing", "cost", "trial", "subscription", "€", "euro"]):
        return _reply(
            "The planned hosted WESLR offer is a 1-month free trial, then €80/month per user. Private and institutional deployments are quote-based.",
            "pricing",
        )

    return _reply(
        "This public demo only supports selected read-only WESLR routes and does not upload files, write memory, expose operator controls, execute actions, or deploy anything. I can explain WESLR, governed memory, hosted versus private deployment, agent/API positioning, pricing, or what the public demo can do.",
        "public_fallback",
    )
