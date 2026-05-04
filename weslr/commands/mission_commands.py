"""
weslr/commands/mission_commands.py
===================================
Research Work Loop V1 — Mission CLI commands.

Commands:
- /mission help                          — show available commands
- /mission create --title "..." --goal "..."  — create a draft mission
- /mission list                          — list missions for tenant
- /mission details <mission_id>          — show mission details
- /mission activate <mission_id>         — set status to active
- /mission pause <mission_id>            — set status to paused
- /mission close <mission_id>           — set status to closed
- /mission-review                        — run one-shot mission review

Author: OCC (WESLR governed intelligence) — Research Work Loop V1
"""

from __future__ import annotations

import re
from typing import Optional

from ..mission_store import MissionStore
from ..schemas.mission import make_mission, Mission
from ..loop.research_work_loop import run_once_mission_review

# Default tenant for V1 (no multi-tenant system yet)
DEFAULT_TENANT = "default-tenant"
DEFAULT_USER = "operator"

# Module-level store instance (shared across command calls)
_STORE: Optional[MissionStore] = None


def _store() -> MissionStore:
    global _STORE
    if _STORE is None:
        _STORE = MissionStore()
    return _STORE


# ── Command handlers ─────────────────────────────────────────────────────────

async def handle_mission_command(message: str, lowered: str) -> str:
    """Route /mission commands."""
    if lowered == "mission help" or lowered == "/mission help":
        return _handle_mission_help()
    if lowered in ("/mission", "mission") and not _has_subcommand(lowered):
        return _handle_mission_help()
    if lowered.startswith("mission create ") or lowered.startswith("/mission create "):
        return _handle_mission_create(message, lowered)
    if lowered == "mission list" or lowered == "/mission list":
        return _handle_mission_list()
    if lowered.startswith("mission details ") or lowered.startswith("/mission details "):
        return _handle_mission_details(lowered)
    if lowered.startswith("mission activate ") or lowered.startswith("/mission activate "):
        return _handle_mission_activate(lowered)
    if lowered.startswith("mission pause ") or lowered.startswith("/mission pause "):
        return _handle_mission_pause(lowered)
    if lowered.startswith("mission close ") or lowered.startswith("/mission close "):
        return _handle_mission_close(lowered)
    if lowered in ("/mission-review", "mission-review", "mission review", "/mission review"):
        return _handle_mission_review()
    return _unknown("mission")


async def handle_mission_review_command(message: str, lowered: str) -> str:
    """Route /mission-review as a dedicated command."""
    return _handle_mission_review()


# ── Sub-handlers ──────────────────────────────────────────────────────────────

def _handle_mission_help() -> str:
    """Show available mission commands."""
    lines = [
        "WESLR Mission Commands (Research Work Loop V1)",
        "",
        "  /mission help                        — show this help",
        "  /mission create --title '...' --goal '...'  — create draft mission",
        "  /mission create --title '...' --goal '...' --active  — create active mission",
        "  /mission list                        — list all missions",
        "  /mission details <mission_id>       — show mission details",
        "  /mission activate <mission_id>       — set mission status to active",
        "  /mission pause <mission_id>          — set mission status to paused",
        "  /mission close <mission_id>          — set mission status to closed",
        "  /mission-review                       — run one-shot review of active missions",
        "",
        "Safety: no automatic execution. All suggestions require operator review.",
        "automatic_execution is always false. Suggestions written to .weslr/pending_messages.jsonl.",
    ]
    return "\n".join(lines)


def _handle_mission_create(message: str, lowered: str) -> str:
    """Handle /mission create --title '...' --goal '...' [--active]"""
    # Parse --title and --goal flags from message
    title = _extract_flag(message, "--title") or _extract_flag(message, "-t")
    goal = _extract_flag(message, "--goal") or _extract_flag(message, "-g")
    is_active = "--active" in message.lower() or "-a" in message.lower()

    if not title:
        return "Usage: /mission create --title 'Mission Title' --goal 'Research goal'\nOptional: --active to create as active."
    if not goal:
        return "Usage: /mission create --title 'Mission Title' --goal 'Research goal'\nOptional: --active to create as active."

    mission = make_mission(
        tenant_id=DEFAULT_TENANT,
        owner_user_id=DEFAULT_USER,
        title=title.strip('"').strip("'"),
        research_goal=goal.strip('"').strip("'"),
    )

    if is_active:
        mission.status = "active"

    store = _store()
    try:
        store.save(mission)
    except ValueError as e:
        return f"Error creating mission: {e}"

    status_note = f"Status: {mission.status}"
    auto_exec_note = "automatic_execution: false (always)"

    return (
        f"Mission created: {mission.mission_id}\n"
        f"Title: {mission.title}\n"
        f"Goal: {mission.research_goal}\n"
        f"{status_note}\n"
        f"{auto_exec_note}\n\n"
        f"Use /mission activate {mission.mission_id} to activate.\n"
        f"Use /mission details {mission.mission_id} to view details."
    )


def _handle_mission_list() -> str:
    """Handle /mission list — list all missions for default tenant."""
    store = _store()
    missions = store.list(DEFAULT_TENANT)

    if not missions:
        return "No missions found. Use /mission create --title '...' --goal '...' to create one."

    lines = [f"Missions for tenant '{DEFAULT_TENANT}' ({len(missions)} total):", ""]

    for m in missions:
        status_icon = {"draft": "📝", "active": "✅", "paused": "⏸", "closed": "🔴"}.get(m.status, "?")
        lines.append(f"  {status_icon} [{m.status}] {m.mission_id[:8]}... | {m.title}")
        if m.current_questions:
            lines.append(f"       Questions: {len(m.current_questions)}")
        lines.append(f"       Created: {m.created_at[:10]}")

    lines.append("")
    lines.append("Use /mission details <id> for full details.")

    return "\n".join(lines)


def _handle_mission_details(lowered: str) -> str:
    """Handle /mission details <mission_id>"""
    m = re.search(r"\/mission\s+details\s+(\S+)", lowered)
    if not m:
        m = re.search(r"mission\s+details\s+(\S+)", lowered)

    if not m:
        return "Usage: /mission details <mission_id>"

    mission_id = m.group(1).strip()
    store = _store()
    mission = store.get(mission_id, DEFAULT_TENANT)

    if not mission:
        return f"Mission '{mission_id}' not found."

    return _format_mission_details(mission)


def _format_mission_details(mission: Mission) -> str:
    """Format a mission as a detailed multi-line string."""
    status_icon = {"draft": "📝", "active": "✅", "paused": "⏸", "closed": "🔴"}.get(mission.status, "?")
    lines = [
        f"Mission: {mission.title}",
        f"ID: {mission.mission_id}",
        f"Tenant: {mission.tenant_id} | Owner: {mission.owner_user_id}",
        f"Status: {status_icon} {mission.status}",
        f"",
        f"Research Goal: {mission.research_goal}",
        f"",
        f"Domain Tags: {', '.join(mission.domain_tags) or '(none)'}",
        f"Allowed Sources: {', '.join(mission.allowed_sources) or '(none)'}",
        f"",
    ]

    if mission.current_questions:
        lines.append(f"Open Questions ({len(mission.current_questions)}):")
        for q in mission.current_questions:
            lines.append(f"  • {q}")
        lines.append("")

    if mission.hypotheses:
        lines.append(f"Hypotheses ({len(mission.hypotheses)}):")
        for h in mission.hypotheses:
            lines.append(f"  • {h}")
        lines.append("")

    if mission.evidence_links:
        lines.append(f"Evidence Links ({len(mission.evidence_links)}):")
        for e in mission.evidence_links:
            lines.append(f"  • {e}")
        lines.append("")

    lines.append(f"automatic_execution: {mission.automatic_execution} (always False)")
    lines.append(f"operator_visible: {mission.operator_visible} | public_user_visible: {mission.public_user_visible}")
    lines.append(f"")
    lines.append(f"Created: {mission.created_at}")
    lines.append(f"Last Reviewed: {mission.last_reviewed_at}")

    if mission.mission_note:
        lines.append(f"Note: {mission.mission_note}")

    return "\n".join(lines)


def _handle_mission_activate(lowered: str) -> str:
    """Handle /mission activate <mission_id>"""
    return _change_status(lowered, "activate", "active")


def _handle_mission_pause(lowered: str) -> str:
    """Handle /mission pause <mission_id>"""
    return _change_status(lowered, "pause", "paused")


def _handle_mission_close(lowered: str) -> str:
    """Handle /mission close <mission_id>"""
    return _change_status(lowered, "close", "closed")


def _change_status(lowered: str, action: str, new_status: str) -> str:
    """Common status change handler."""
    m = re.search(r"\/mission\s+" + action + r"\s+(\S+)", lowered)
    if not m:
        m = re.search(r"mission\s+" + action + r"\s+(\S+)", lowered)

    if not m:
        return f"Usage: /mission {action} <mission_id>"

    mission_id = m.group(1).strip()

    # Verify mission exists
    store = _store()
    existing = store.get(mission_id, DEFAULT_TENANT)
    if not existing:
        return f"Mission '{mission_id}' not found."

    success = store.update_status(mission_id, DEFAULT_TENANT, new_status)
    if not success:
        return f"Failed to update mission status."

    status_icon = {"active": "✅", "paused": "⏸", "closed": "🔴"}.get(new_status, "?")
    return f"Mission {mission_id[:8]}... status changed to {status_icon} {new_status}."


def _handle_mission_review() -> str:
    """Handle /mission-review — run one-shot review of active missions."""
    result = run_once_mission_review(DEFAULT_TENANT)

    missions_reviewed = result.get("missions_reviewed", 0)
    suggestions_generated = result.get("suggestions_generated", 0)
    suggestions_written = result.get("suggestions_written", 0)
    suggestions_blocked = result.get("suggestions_blocked", 0)
    errors = result.get("errors", [])

    lines = [
        "=== Mission Review Results ===",
        f"Missions reviewed: {missions_reviewed}",
        f"Suggestions generated: {suggestions_generated}",
        f"Suggestions written: {suggestions_written}",
        f"Suggestions blocked (safety filter): {suggestions_blocked}",
        "",
        f"Output target: .weslr/pending_messages.jsonl",
        f"automatic_execution: false (no suggestions are auto-executed)",
        f"Safety: all suggestions reviewed by operator before any action",
    ]

    if errors:
        lines.append("")
        lines.append(f"Errors ({len(errors)}):")
        for err in errors:
            lines.append(f"  • Mission {err.get('mission_id', 'unknown')}: {err.get('error', 'unknown')}")

    lines.append("")
    lines.append("Run /mission list to see current missions.")
    lines.append("Run /mission-review again after updating missions.")

    return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _match(lowered: str, patterns: tuple[str, ...]) -> bool:
    """Return True if lowered matches any of the patterns exactly."""
    return lowered in patterns


def _has_subcommand(lowered: str) -> bool:
    """Return True if the command has a known subcommand after /mission."""
    subcommands = (
        "create", "list", "details", "activate", "pause", "close",
    )
    return any(lowered.startswith(f"/mission {sc}") or lowered.startswith(f"mission {sc}")
               for sc in subcommands)


def _extract_flag(message: str, flag: str) -> Optional[str]:
    """
    Extract a quoted or bare value after a flag.

    Examples:
        --title "My Title"  -> "My Title"
        --title 'My Title'  -> "My Title"
        --title MyTitle     -> "MyTitle"
    """
    # Simple regex: flag followed by quoted or bare word
    pattern = rf"{re.escape(flag)}\s+([\"']?)([^\"'\n]+)\1"
    m = re.search(pattern, message)
    if m:
        return m.group(2).strip()
    # Bare word (no quotes)
    pattern2 = rf"{re.escape(flag)}\s+(\S+)"
    m2 = re.search(pattern2, message)
    if m2:
        return m2.group(1).strip()
    return None


def _unknown(subcommand: str) -> str:
    """Return an unknown command message."""
    return (
        f"Unknown /{subcommand} command.\n"
        f"Use /{subcommand} help to see available commands."
    )


# ── Test reset function ───────────────────────────────────────────────────────

def _reset_store() -> None:
    """Reset the module-level store. Used in tests."""
    global _STORE
    _STORE = None