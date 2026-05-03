"""
WESLR Project Query Handler V1

Deterministic handlers for project-scoped queries and commands.
All handlers are read-only except register_project.

Supported commands:
  - "create project <name> [description ...]" → register_project
  - "list projects" → list_projects
  - "switch to project <name>" → set_active_project (by name or ID)
  - "what does project <name> know about <topic>" → load_facts scoped to project
  - "what does project <name> know" → load all facts for project

Authority: project_query_handler
No execution, no Ollama, no raw prompts stored.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from weslr.project_registry import (
    register_project,
    list_projects,
    get_project,
    set_active_project,
    get_active_project,
)
from weslr.fact_extractor import load_facts

DEFAULT_REGISTRY_PATH = ".weslr/project_registry.jsonl"
DEFAULT_FACT_STORE_PATH = ".weslr/fact_assertions.jsonl"


# ──────────────────────────────────────────────────────────────────────────────
# Pattern definitions
# ──────────────────────────────────────────────────────────────────────────────

_CREATE_PROJECT_RE = re.compile(
    r"^(?:create|new)\s+project\s+([^\n]+?)(?:\s+with\s+description\s+(.+))?$",
    re.IGNORECASE,
)

_LIST_PROJECTS_RE = re.compile(r"^(?:list|show)\s+projects?$", re.IGNORECASE)

_SWITCH_PROJECT_RE = re.compile(
    r"^(?:switch|move|go)\s+to\s+project\s+(\S+)$",
    re.IGNORECASE,
)

_PROJECT_KNOWLEDGE_RE = re.compile(
    r"^(?:what\s+(?:does|do)\s+)?project\s+(\S+.*?)\s+(?:knows?|know\s+about|information\s+on|about)\s+(.+)$",
    re.IGNORECASE,
)

_PROJECT_KNOWLEDGE_ALL_RE = re.compile(
    r"^(?:what\s+(?:does|do)\s+)?project\s+(\S+.*?)\s+(?:knows?|know)\s*$",
    re.IGNORECASE,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_for_matching(name: str) -> str:
    """Strip quotes and normalize for project name matching."""
    name = name.strip().strip('"').strip("'")
    return name.lower()


def _find_project_id_by_name(
    name: str,
    owner_user_id: Optional[str] = None,
    registry_path: str = DEFAULT_REGISTRY_PATH,
) -> Optional[str]:
    """Find project_id by name (case-insensitive)."""
    projects = list_projects(owner_user_id=owner_user_id, registry_path=registry_path)
    normalized = _normalize_for_matching(name)
    for proj in projects:
        if _normalize_for_matching(proj.get("name", "")) == normalized:
            return proj.get("project_id")
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Command handlers
# ──────────────────────────────────────────────────────────────────────────────

def handle_project_command(
    message: str,
    session_id: str,
    owner_user_id: str = "arthur",
    registry_path: str = DEFAULT_REGISTRY_PATH,
    fact_store_path: str = DEFAULT_FACT_STORE_PATH,
) -> Dict[str, Any]:
    """Route a message to the appropriate project command handler.

    Returns a dict with keys:
        - handled: bool
        - command: str (one of: create_project, list_projects, switch_project,
                       project_knowledge, project_knowledge_all, unknown)
        - result: dict with command-specific keys
        - error: str or None
    """
    msg = message.strip()

    # ── create project ────────────────────────────────────────────────────────
    m = _CREATE_PROJECT_RE.match(msg)
    if m:
        name = m.group(1).strip()
        description = m.group(2).strip() if m.group(2) else ""
        try:
            result = register_project(
                name=name,
                description=description,
                owner_user_id=owner_user_id,
                registry_path=registry_path,
            )
            return {
                "handled": True,
                "command": "create_project",
                "result": {
                    "project_id": result["project"]["project_id"],
                    "name": result["project"]["name"],
                    "description": result["project"]["description"],
                    "status": "registered",
                },
                "error": None,
            }
        except ValueError as e:
            return {"handled": True, "command": "create_project", "result": {}, "error": str(e)}

    # ── list projects ─────────────────────────────────────────────────────────
    if _LIST_PROJECTS_RE.match(msg):
        projects = list_projects(owner_user_id=owner_user_id, registry_path=registry_path)
        return {
            "handled": True,
            "command": "list_projects",
            "result": {
                "projects": [
                    {"project_id": p["project_id"], "name": p["name"], "description": p.get("description", "")}
                    for p in projects
                ],
                "count": len(projects),
            },
            "error": None,
        }

    # ── switch to project ─────────────────────────────────────────────────────
    m = _SWITCH_PROJECT_RE.match(msg)
    if m:
        name_or_id = m.group(1).strip()
        # Try as project_id first, then as name
        project_id = None
        project = get_project(name_or_id, registry_path=registry_path)
        if project:
            project_id = name_or_id
        else:
            project_id = _find_project_id_by_name(name_or_id, owner_user_id, registry_path=registry_path)

        if not project_id:
            return {
                "handled": True,
                "command": "switch_project",
                "result": {},
                "error": f"Project '{name_or_id}' not found",
            }

        set_result = set_active_project(project_id, session_id, registry_path=registry_path)
        return {
            "handled": True,
            "command": "switch_project",
            "result": {
                "project_id": set_result["project_id"],
                "project_name": set_result.get("project_name", ""),
                "status": set_result["status"],
            },
            "error": None,
        }

    # ── what does project <name> know about <topic> ───────────────────────────
    m = _PROJECT_KNOWLEDGE_RE.match(msg)
    if m:
        project_name = m.group(1).strip()
        topic = m.group(2).strip()
        return _handle_project_knowledge(
            project_name=project_name,
            topic=topic,
            owner_user_id=owner_user_id,
            session_id=session_id,
            registry_path=registry_path,
            fact_store_path=fact_store_path,
        )

    # ── what does project <name> know (all facts) ────────────────────────────
    m = _PROJECT_KNOWLEDGE_ALL_RE.match(msg)
    if m:
        project_name = m.group(1).strip()
        return _handle_project_knowledge(
            project_name=project_name,
            topic=None,
            owner_user_id=owner_user_id,
            session_id=session_id,
            registry_path=registry_path,
            fact_store_path=fact_store_path,
        )

    return {"handled": False, "command": "unknown", "result": {}, "error": None}


def _handle_project_knowledge(
    project_name: str,
    topic: Optional[str],
    owner_user_id: str,
    session_id: str,
    registry_path: str,
    fact_store_path: str,
) -> Dict[str, Any]:
    """Handle 'what does project X know about Y' query."""
    # Resolve project: try active project first if name is "it" or empty
    project_id = None
    if project_name.lower() in ("it", "this", "the project"):
        project_id = get_active_project(session_id)

    if not project_id:
        project_id = _find_project_id_by_name(project_name, owner_user_id, registry_path=registry_path)

    if not project_id:
        return {
            "handled": True,
            "command": "project_knowledge",
            "result": {},
            "error": f"Project '{project_name}' not found",
        }

    # Load facts scoped to this project
    if topic:
        # Strip leading "about " or "information on " from topic
        clean_topic = topic
        for prefix in ("about ", "information on "):
            if clean_topic.lower().startswith(prefix):
                clean_topic = clean_topic[len(prefix):].strip()

        # Try matching topic against subject or object
        facts = load_facts(
            subject=clean_topic.lower().replace(" ", "_"),
            project_id=project_id,
            limit=20,
            fact_store_path=fact_store_path,
        )
        if not facts:
            facts = load_facts(
                obj=clean_topic.lower().replace(" ", "_"),
                project_id=project_id,
                limit=20,
                fact_store_path=fact_store_path,
            )
    else:
        facts = load_facts(project_id=project_id, limit=20, fact_store_path=fact_store_path)

    project = get_project(project_id, registry_path=registry_path)
    return {
        "handled": True,
        "command": "project_knowledge" if topic else "project_knowledge_all",
        "result": {
            "project_id": project_id,
            "project_name": project.get("name", "") if project else "",
            "topic": topic,
            "facts": [
                {
                    "subject": f["subject"],
                    "predicate": f["predicate"],
                    "object": f["object"],
                    "source_event_ref": f.get("source_event_ref", ""),
                }
                for f in facts
            ],
            "count": len(facts),
        },
        "error": None,
    }