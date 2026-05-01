"""WESLR Capability Welcome Surface V1 — Registry-Generated Help

Provides human-readable welcome, category help, and capability suggestions
derived entirely from the Capability Registry. No execution, no LLM calls.

Authority: registry_generated / automatic_change: false
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .capability_registry import (
    load_registry,
    get_capability,
    group_capabilities_by_category,
)


# ---- Human-friendly category labels ----

_CATEGORY_LABELS: Dict[str, str] = {
    "evidence/search/sources": "Search and Evidence",
    "system/state": "WESLR System State",
    "governance/safety": "Governance and Safety",
    "operator/attention/review": "Operator Review",
    "commands/help": "Help and Commands",
    "experiments/learning": "Experiments and Learning",
    "projects/planning": "Planning and Projects",
}


def _get_category_label(category: str) -> str:
    """Map registry category to human-friendly label."""
    return _CATEGORY_LABELS.get(category, category.replace("/", " ").replace("_", " ").title())


def _is_user_facing(capability: Dict[str, Any]) -> bool:
    """Return True if this capability is for normal users (not operator-only)."""
    if capability.get("operator_required"):
        return False
    return True


# ---- Human-facing category groups ----

# system/state is included in user-facing for normal users (what is implemented, identity)
_USER_CATEGORY_ORDER = [
    "evidence/search/sources",
    "commands/help",
    "system/state",
    "projects/planning",
    "experiments/learning",
]

_OPERATOR_CATEGORIES = [
    "governance/safety",
    "operator/attention/review",
]


# ---- Public API ----

def build_welcome_overview(max_examples_per_category: int = 2) -> Dict[str, Any]:
    """Build the main welcome/overview surface from the Capability Registry.

    Returns:
        dict with record_type, title, message, categories, suggested_prompts,
        slash_suggestions, authority, automatic_change
    """
    entries = load_registry()

    if not entries:
        return _fallback_welcome()

    # Group by category
    grouped = group_capabilities_by_category(entries)

    user_categories: List[Dict[str, Any]] = []
    operator_categories: List[Dict[str, Any]] = []

    # Build user-facing categories in preferred order
    for cat_key in _USER_CATEGORY_ORDER:
        if cat_key in grouped:
            caps = [c for c in grouped[cat_key] if _is_user_facing(c)]
            if caps:
                user_categories.append({
                    "category_key": cat_key,
                    "label": _get_category_label(cat_key),
                    "capabilities": [_build_capability_summary(c, max_examples_per_category) for c in caps],
                })

    # Operator categories
    for cat_key in _OPERATOR_CATEGORIES:
        if cat_key in grouped:
            caps = grouped[cat_key]
            operator_categories.append({
                "category_key": cat_key,
                "label": _get_category_label(cat_key),
                "capabilities": [_build_capability_summary(c, max_examples_per_category) for c in caps],
            })

    # Collect all slash commands for suggestions
    all_slashes: List[str] = []
    for entry in entries:
        all_slashes.extend(entry.get("slash_commands", []))
    all_slashes = sorted(set(all_slashes))

    # Collect suggested prompts from registry
    suggested: List[str] = []
    for cat_key in _USER_CATEGORY_ORDER:
        if cat_key in grouped:
            for cap in grouped[cat_key]:
                if _is_user_facing(cap):
                    for ex in cap.get("examples", [])[:1]:
                        suggested.append(ex)
                    if len(suggested) >= 6:
                        break
        if len(suggested) >= 6:
            break

    # Build message
    lines = [
        "Here are the main ways I can help:",
    ]
    for cat in user_categories:
        lines.append(f"\n**{cat['label']}**")
        for cap in cat["capabilities"]:
            lines.append(f"  • {cap['label']}: {cap['one_liner']}")

    if operator_categories:
        lines.append("\n*For operators / internal WESLR work:*")
        for cat in operator_categories:
            lines.append(f"\n**{cat['label']}**")
            for cap in cat["capabilities"]:
                lines.append(f"  • {cap['label']}: {cap['one_liner']}")

    message = "\n".join(lines)

    return {
        "record_type": "capability_welcome_overview_v1",
        "title": "What WESLR can help with",
        "message": message,
        "categories": {
            "user": user_categories,
            "operator": operator_categories,
        },
        "suggested_prompts": suggested[:6],
        "slash_suggestions": all_slashes,
        "authority": "registry_generated",
        "automatic_change": False,
    }


def _build_capability_summary(cap: Dict[str, Any], max_examples: int) -> Dict[str, Any]:
    """Build a compact capability summary for the welcome surface."""
    examples = cap.get("examples", [])[:max_examples]
    return {
        "capability_id": cap["capability_id"],
        "label": cap.get("label", cap["capability_id"]),
        "one_liner": cap.get("description", "")[:80],
        "examples": examples,
    }


def build_category_help(category_or_command: str) -> Dict[str, Any]:
    """Build help surface for a specific category or slash command.

    Args:
        category_or_command: e.g. "evidence", "/evidence", "system", "governance",
            "learning", "operator"

    Returns:
        dict with record_type, category, message, capabilities, examples,
        slash_suggestions, authority, automatic_change
    """
    entries = load_registry()
    normalized = category_or_command.strip().lstrip("/").lower()

    # Handle slash commands
    if category_or_command.startswith("/"):
        cap = None
        for entry in entries:
            for cmd in entry.get("slash_commands", []):
                if cmd.strip().lstrip("/").lower() == normalized:
                    cap = entry
                    break
            if cap:
                break

        if cap:
            category_key = cap.get("category", "unknown")
            return {
                "record_type": "capability_category_help_v1",
                "category": category_key,
                "message": _build_single_capability_message(cap),
                "capabilities": [_build_capability_summary(cap, 3)],
                "examples": cap.get("examples", []),
                "slash_suggestions": cap.get("slash_commands", []),
                "authority": "registry_generated",
                "automatic_change": False,
            }

    # Handle category keywords
    category_map: Dict[str, str] = {
        "evidence": "evidence/search/sources",
        "search": "evidence/search/sources",
        "sources": "evidence/search/sources",
        "system": "system/state",
        "state": "system/state",
        "identity": "system/state",
        "governance": "governance/safety",
        "safety": "governance/safety",
        "learning": "experiments/learning",
        "experiments": "experiments/learning",
        "operator": "operator/attention/review",
        "attention": "operator/attention/review",
        "review": "operator/attention/review",
        "help": "commands/help",
        "commands": "commands/help",
        "planning": "projects/planning",
        "projects": "projects/planning",
        "analysis": "system/state",
    }

    target_category = category_map.get(normalized)

    if target_category:
        caps_in_cat = [e for e in entries if e.get("category") == target_category]
    else:
        # Fuzzy match: search capability labels and descriptions
        caps_in_cat = []
        for entry in entries:
            label = entry.get("label", "").lower()
            desc = entry.get("description", "").lower()
            if normalized in label or normalized in desc:
                caps_in_cat.append(entry)

    if not caps_in_cat:
        return _fallback_category_help(category_or_command)

    category_key = caps_in_cat[0].get("category", "unknown")

    lines = [f"**{_get_category_label(category_key)}**\n"]
    cap_summaries = []
    all_examples: List[str] = []
    all_slashes: List[str] = []

    for cap in caps_in_cat:
        lines.append(f"\n**{cap.get('label', cap['capability_id'])}**")
        lines.append(f"{cap.get('description', '')}")
        cap_summaries.append(_build_capability_summary(cap, 3))
        all_examples.extend(cap.get("examples", []))
        all_slashes.extend(cap.get("slash_commands", []))

    all_examples = _deduplicate_preserve_order(all_examples)
    all_slashes = sorted(set(all_slashes))

    message = "\n".join(lines)

    return {
        "record_type": "capability_category_help_v1",
        "category": category_key,
        "message": message,
        "capabilities": cap_summaries,
        "examples": all_examples[:6],
        "slash_suggestions": all_slashes,
        "authority": "registry_generated",
        "automatic_change": False,
    }


def _build_single_capability_message(cap: Dict[str, Any]) -> str:
    """Build a help message for a single capability."""
    lines = [
        f"**{cap.get('label', cap['capability_id'])}**",
        f"\n{cap.get('description', '')}",
    ]
    examples = cap.get("examples", [])
    if examples:
        lines.append("\nExamples:")
        for ex in examples[:3]:
            lines.append(f"  • {ex}")
    slashes = cap.get("slash_commands", [])
    if slashes:
        lines.append(f"\nSlash commands: {', '.join(slashes)}")
    status = cap.get("status", "unknown")
    lines.append(f"\nStatus: {status}")
    return "\n".join(lines)


def build_capability_suggestions(message: str) -> Dict[str, Any]:
    """Suggest capabilities based on a user message, using the Capability Router.

    Args:
        message: The user's message or question

    Returns:
        dict with record_type, route, message, suggestions, authority, automatic_change
    """
    # Import here to keep router dependency lazy
    from .capability_router import route_request

    route = route_request(message)

    selected_capability_id = route.get("selected_capability")
    suggestions: List[Dict[str, Any]] = []

    if selected_capability_id:
        cap = get_capability(selected_capability_id)
        if cap:
            suggestions.append({
                "type": "primary",
                "capability_id": selected_capability_id,
                "label": cap.get("label", selected_capability_id),
                "description": cap.get("description", ""),
                "examples": cap.get("examples", [])[:2],
                "confidence": route.get("confidence", 0.0),
                "slash_commands": cap.get("slash_commands", []),
            })

            # Add related capabilities from same category
            entries = load_registry()
            category = cap.get("category")
            if category:
                related = [
                    e for e in entries
                    if e.get("category") == category
                    and e["capability_id"] != selected_capability_id
                    and _is_user_facing(e)
                ]
                for rel in related[:3]:
                    suggestions.append({
                        "type": "related",
                        "capability_id": rel["capability_id"],
                        "label": rel.get("label", rel["capability_id"]),
                        "description": rel.get("description", ""),
                        "examples": rel.get("examples", [])[:1],
                        "confidence": None,
                        "slash_commands": rel.get("slash_commands", []),
                    })
    else:
        # No confident match — suggest top-level categories
        entries = load_registry()
        grouped = group_capabilities_by_category(entries)
        for cat_key in _USER_CATEGORY_ORDER:
            if cat_key in grouped:
                user_caps = [c for c in grouped[cat_key] if _is_user_facing(c)]
                if user_caps:
                    suggestions.append({
                        "type": "category",
                        "category": cat_key,
                        "label": _get_category_label(cat_key),
                        "description": user_caps[0].get("description", "")[:80],
                        "examples": user_caps[0].get("examples", [])[:1],
                        "confidence": None,
                        "slash_commands": [],
                    })

    # Build message
    if suggestions:
        if suggestions[0]["type"] == "primary":
            primary = suggestions[0]
            message_text = f"I think you're asking about **{primary['label']}**. "
            message_text += f"{primary['description']}"
            if primary.get("examples"):
                message_text += f"\n\nFor example: {primary['examples'][0]}"
        elif suggestions[0]["type"] == "category":
            cat_label = suggestions[0]["label"]
            message_text = f"It sounds like you want to explore **{cat_label}**. Here are the main areas I can help with in that category."
        else:
            message_text = "Here are some things I can help with:"
    else:
        message_text = "I'm not sure what you're looking for. Here are the main ways I can help:"

    return {
        "record_type": "capability_suggestion_surface_v1",
        "route": route,
        "message": message_text,
        "suggestions": suggestions,
        "authority": "registry_generated",
        "automatic_change": False,
    }


# ---- Fallbacks ----

def _fallback_welcome() -> Dict[str, Any]:
    """Return fallback welcome when registry cannot be loaded."""
    return {
        "record_type": "capability_welcome_overview_v1",
        "title": "What WESLR can help with",
        "message": (
            "Here are the main ways I can help:\n\n"
            "**Search and Evidence**\n"
            "  • Look up topics with source citations\n\n"
            "**Planning and Projects**\n"
            "  • Break down goals into next steps\n\n"
            "**Experiments and Learning**\n"
            "  • Plan structured experiments together\n\n"
            "**WESLR System State**\n"
            "  • Check what is implemented and what needs attention\n\n"
            "Try asking me something specific, or say /help for commands."
        ),
        "categories": [],
        "suggested_prompts": [
            "What is entropy?",
            "Help me plan this project",
            "What is implemented?",
        ],
        "slash_suggestions": ["/help", "/evidence", "/state", "/plan"],
        "authority": "registry_generated",
        "automatic_change": False,
    }


def _fallback_category_help(category_or_command: str) -> Dict[str, Any]:
    """Return safe fallback for unknown category."""
    return {
        "record_type": "capability_category_help_v1",
        "category": "unknown",
        "message": (
            f"I don't have specific help for '{category_or_command}' yet. "
            "Try asking about: evidence, governance, system, planning, or experiments. "
            "You can also say /help for an overview."
        ),
        "capabilities": [],
        "examples": [],
        "slash_suggestions": ["/help"],
        "authority": "registry_generated",
        "automatic_change": False,
    }


def _deduplicate_preserve_order(seq: List[str]) -> List[str]:
    """Deduplicate a list while preserving first-occurrence order."""
    seen = set()
    result = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result