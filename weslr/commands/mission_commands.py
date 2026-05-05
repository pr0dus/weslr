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
    if lowered.startswith("mission add-question ") or lowered.startswith("/mission add-question "):
        return _handle_mission_add_question(message, lowered)
    if lowered.startswith("mission add-domain ") or lowered.startswith("/mission add-domain "):
        return _handle_mission_add_domain(message, lowered)
    if lowered.startswith("mission add-evidence ") or lowered.startswith("/mission add-evidence "):
        return _handle_mission_add_evidence(message, lowered)
    if lowered.startswith("mission add-hypothesis ") or lowered.startswith("/mission add-hypothesis "):
        return _handle_mission_add_hypothesis(message, lowered)
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
        "  /mission create --title '...' --goal '...' — create draft mission",
        "  /mission create --title '...' --goal '...' --active — create active mission",
        "  /mission create --title '...' --goal '...' --active --question '...' --domain 'materials,biocompatibility' --evidence 'path1' --hypothesis 'id' — create with fields",
        "  /mission list                        — list all missions",
        "  /mission details <mission_id>       — show mission details",
        "  /mission activate <mission_id>       — set mission status to active",
        "  /mission pause <mission_id>          — set mission status to paused",
        "  /mission close <mission_id>          — set mission status to closed",
        "  /mission add-question <id> 'question'   — add an open question",
        "  /mission add-domain <id> 'tag'         — add a domain tag",
        "  /mission add-evidence <id> 'path'      — add an evidence link",
        "  /mission add-hypothesis <id> 'hyp'     — add a hypothesis/id",
        "  /mission-review                       — run one-shot review of active missions",
        "",
        "Safety: no automatic execution. All suggestions require operator review.",
        "automatic_execution is always false. Suggestions → .weslr/pending_messages.jsonl",
    ]
    return "\n".join(lines)


def _handle_mission_create(message: str, lowered: str) -> str:
    """Handle /mission create --title '...' --goal '...' [--active] [--question '...'] [--domain '...'] [--evidence '...'] [--hypothesis '...']"""
    title = _extract_flag(message, "--title") or _extract_flag(message, "-t")
    goal = _extract_flag(message, "--goal") or _extract_flag(message, "-g")
    is_active = "--active" in message.lower() or "-a" in message.lower()
    question_str = _extract_flag(message, "--question") or _extract_flag(message, "-q")
    domain_str = _extract_flag(message, "--domain") or _extract_flag(message, "-d")
    evidence_str = _extract_flag(message, "--evidence") or _extract_flag(message, "-e")
    hypothesis_str = _extract_flag(message, "--hypothesis") or _extract_flag(message, "-h")

    if not title:
        return ("Usage: /mission create --title 'Mission Title' --goal 'Research goal'\n"
                "Optional: --active, --question '...', --domain 'materials,robotics', --evidence 'path1,path2', --hypothesis '...'\n"
                "Example: /mission create --title 'My Mission' --goal 'Research X' --active --question 'What is X?' --domain materials,biocompatibility")
    if not goal:
        return "Usage: /mission create --title 'Mission Title' --goal 'Research goal'"

    # Parse comma/semicolon-separated lists
    questions = _parse_list(question_str) if question_str else []
    domains = _parse_list(domain_str) if domain_str else []
    evidence_links = _parse_list(evidence_str) if evidence_str else []
    hypotheses = _parse_list(hypothesis_str) if hypothesis_str else []

    mission = make_mission(
        tenant_id=DEFAULT_TENANT,
        owner_user_id=DEFAULT_USER,
        title=title.strip('"').strip("'"),
        research_goal=goal.strip('"').strip("'"),
    )

    mission.current_questions = questions
    mission.domain_tags = domains
    mission.evidence_links = evidence_links
    mission.hypotheses = hypotheses

    if is_active:
        mission.status = "active"

    store = _store()
    try:
        store.save(mission)
    except ValueError as e:
        return f"Error creating mission: {e}"

    status_note = f"Status: {mission.status}"
    auto_exec_note = "automatic_execution: false (always)"
    fields_note = ""
    if questions:
        fields_note += f"Questions: {len(questions)}\n"
    if domains:
        fields_note += f"Domains: {', '.join(domains)}\n"
    if evidence_links:
        fields_note += f"Evidence links: {len(evidence_links)}\n"
    if hypotheses:
        fields_note += f"Hypotheses: {len(hypotheses)}\n"

    return (
        f"Mission created: {mission.mission_id}\n"
        f"Title: {mission.title}\n"
        f"Goal: {mission.research_goal}\n"
        f"{status_note}\n"
        f"{auto_exec_note}\n"
        + (fields_note + "\n" if fields_note else "\n") +
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
    Stops at next -- flag, end of string, or trailing whitespace.

    Examples:
        --title "My Title"  -> "My Title"
        --title 'My Title'  -> "My Title"
        --title MyTitle     -> "MyTitle"
        --domain a,b,c --active  -> "a,b,c"
    """
    # Quoted value: stops at matching quote
    pattern = rf'{re.escape(flag)}\s+(["\'])([^"\']+)\1'
    m = re.search(pattern, message)
    if m:
        return m.group(2).strip()
    # Bare word: stop at ' --' (next flag) or end of string
    pattern2 = rf'{re.escape(flag)}\s+(\S+?)(?=\s+--|\s*$)'
    m2 = re.search(pattern2, message)
    if m2:
        return m2.group(1).strip()
    return None


def _handle_mission_add_question(message: str, lowered: str) -> str:
    """Handle /mission add-question <mission_id> 'question text'"""
    # Extract mission_id and question text
    m = re.search(r"\ add-question\s+(\S+)\s+(.+)", lowered)
    if not m:
        m = re.search(r"\ add-question\s+(\S+)", lowered)
    if not m:
        return "Usage: /mission add-question <mission_id> 'question text'"

    mission_id = m.group(1).strip()
    question_text = m.group(2).strip().strip('"').strip("'") if m.lastindex and m.lastindex >= 2 else ""

    if not question_text:
        return "Usage: /mission add-question <mission_id> 'question text'"

    store = _store()
    mission = store.get(mission_id, DEFAULT_TENANT)
    if not mission:
        return f"Mission '{mission_id}' not found."

    updated_questions = list(mission.current_questions) + [question_text]
    success = store.update_mission(mission_id, DEFAULT_TENANT, {"current_questions": updated_questions})
    if success:
        return f"Added question to mission {mission_id[:8]}...: '{question_text}'\nTotal questions: {len(updated_questions)}"
    return f"Failed to add question."


def _handle_mission_add_domain(message: str, lowered: str) -> str:
    """Handle /mission add-domain <mission_id> 'domain_tag'"""
    m = re.search(r"\ add-domain\s+(\S+)\s+(.+)", lowered)
    if not m:
        m = re.search(r"\ add-domain\s+(\S+)", lowered)
    if not m:
        return "Usage: /mission add-domain <mission_id> 'domain_tag'"

    mission_id = m.group(1).strip()
    domain_tag = m.group(2).strip().strip('"').strip("'") if m.lastindex and m.lastindex >= 2 else ""

    if not domain_tag:
        return "Usage: /mission add-domain <mission_id> 'domain_tag'"

    # Support comma/semicolon separated for multiple
    tags = _parse_list(domain_tag)

    store = _store()
    mission = store.get(mission_id, DEFAULT_TENANT)
    if not mission:
        return f"Mission '{mission_id}' not found."

    updated_domains = list(mission.domain_tags) + tags
    success = store.update_mission(mission_id, DEFAULT_TENANT, {"domain_tags": updated_domains})
    if success:
        return f"Added domain tag(s) to mission {mission_id[:8]}...: {', '.join(tags)}\nTotal domains: {len(updated_domains)}"
    return f"Failed to add domain tag."


def _handle_mission_add_evidence(message: str, lowered: str) -> str:
    """Handle /mission add-evidence <mission_id> 'path'"""
    m = re.search(r"\ add-evidence\s+(\S+)\s+(.+)", lowered)
    if not m:
        m = re.search(r"\ add-evidence\s+(\S+)", lowered)
    if not m:
        return "Usage: /mission add-evidence <mission_id> 'path'"

    mission_id = m.group(1).strip()
    evidence_path = m.group(2).strip().strip('"').strip("'") if m.lastindex and m.lastindex >= 2 else ""

    if not evidence_path:
        return "Usage: /mission add-evidence <mission_id> 'path'"

    store = _store()
    mission = store.get(mission_id, DEFAULT_TENANT)
    if not mission:
        return f"Mission '{mission_id}' not found."

    paths = _parse_list(evidence_path)
    updated_links = list(mission.evidence_links) + paths
    success = store.update_mission(mission_id, DEFAULT_TENANT, {"evidence_links": updated_links})
    if success:
        return f"Added evidence link(s) to mission {mission_id[:8]}...: {', '.join(paths)}\nTotal evidence links: {len(updated_links)}"
    return f"Failed to add evidence link."


def _handle_mission_add_hypothesis(message: str, lowered: str) -> str:
    """Handle /mission add-hypothesis <mission_id> 'hypothesis or id'"""
    m = re.search(r"\ add-hypothesis\s+(\S+)\s+(.+)", lowered)
    if not m:
        m = re.search(r"\ add-hypothesis\s+(\S+)", lowered)
    if not m:
        return "Usage: /mission add-hypothesis <mission_id> 'hypothesis text or ID'"

    mission_id = m.group(1).strip()
    hypothesis_text = m.group(2).strip().strip('"').strip("'") if m.lastindex and m.lastindex >= 2 else ""

    if not hypothesis_text:
        return "Usage: /mission add-hypothesis <mission_id> 'hypothesis text or ID'"

    store = _store()
    mission = store.get(mission_id, DEFAULT_TENANT)
    if not mission:
        return f"Mission '{mission_id}' not found."

    hypotheses = _parse_list(hypothesis_text)
    updated_hypotheses = list(mission.hypotheses) + hypotheses
    success = store.update_mission(mission_id, DEFAULT_TENANT, {"hypotheses": updated_hypotheses})
    if success:
        return f"Added hypothesis/ID(s) to mission {mission_id[:8]}...: {len(hypotheses)} item(s) added"
    return f"Failed to add hypothesis."


def _parse_list(value: Optional[str]) -> list[str]:
    """Parse comma or semicolon-separated list into cleaned strings."""
    if not value:
        return []
    # Split on comma or semicolon
    parts = re.split(r"[,;]", value)
    return [p.strip() for p in parts if p.strip()]


# ── Test reset function ───────────────────────────────────────────────────────

def _reset_store() -> None:
    """Reset the module-level store. Used in tests."""
    global _STORE
    _STORE = None

def _unknown(subcommand: str) -> str:
    """Return an unknown command message."""
    return (
        f"Unknown /{subcommand} command.\n"
        f"Use /{subcommand} help to see available commands."
    )
