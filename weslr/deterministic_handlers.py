"""WESLR deterministic handler registry — read-only query dispatch.

Single registry entry point. Each entry is a declarative mapping:
  id          — unique handler identifier
  path        — deterministic response path label
  triggers    — list of prefix trigger strings
  match_type  — "prefix" for now
  priority    — higher = checked first (sorted descending at dispatch)
  handler_fn  — name of handler function in this module
  read_only   — True (no writes)
  writes      — empty list
  requires_confirmation — False
  category    — "iss", "plan", etc.

Extracted handlers are pure read-only query responders.
No execution, no proposals, no state changes.
"""

from __future__ import annotations

from typing import Optional

from weslr.response_formatter import build_deterministic_response
from weslr.iss.probe_registry import get_probe_registry


# ---- Handler functions ----

def handle_iss_probe_registry(message: str, lowered: str) -> dict:
    """ISS probe registry query — read-only."""
    probes = get_probe_registry()
    return build_deterministic_response(
        message=message,
        path="ISS_probe_registry_query",
        response_text="ISS has " + str(len(probes)) + " defined probe stubs. Execution allowed: False for all.",
        payload={"probe_registry": probes, "probe_count": len(probes)},
        confidence="high",
        suggested_mode="observe",
    )


# ---- Registry ----

HANDLER_REGISTRY = [
    {
        "id": "iss_probe_registry_query",
        "path": "ISS_probe_registry_query",
        "triggers": [
            "show iss probes",
            "show probe registry",
            "list probes",
            "what can iss check",
        ],
        "match_type": "prefix",
        "priority": 80,
        "handler_fn": "handle_iss_probe_registry",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "category": "iss",
    },
]


# ---- Dispatch ----

def dispatch_deterministic_handler(message: str, lowered: str) -> Optional[dict]:
    """
    Sort registry by priority descending, try prefix match, return handler result.
    Returns None if no trigger matches.
    """
    sorted_handlers = sorted(HANDLER_REGISTRY, key=lambda h: h["priority"], reverse=True)
    for entry in sorted_handlers:
        for trigger in entry["triggers"]:
            if lowered.startswith(trigger):
                handler_fn_name = entry["handler_fn"]
                handler_fn = globals().get(handler_fn_name)
                if handler_fn is not None:
                    return handler_fn(message, lowered)
    return None
