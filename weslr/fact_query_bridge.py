"""
WESLR Fact Query Bridge V1

Bridge that queries fact_assertions.jsonl and returns formatted summaries.
Activated when arbiter routes a turn as "relational_query" → selected_layer="fact_engine".

Authority: fact_query_bridge
No execution, no Ollama, no raw prompts stored.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from weslr.fact_extractor import load_facts
from weslr.project_registry import get_project, get_active_project

DEFAULT_FACT_STORE_PATH = ".weslr/fact_assertions.jsonl"
DEFAULT_REGISTRY_PATH = ".weslr/project_registry.jsonl"


# ──────────────────────────────────────────────────────────────────────────────
# Formatter
# ──────────────────────────────────────────────────────────────────────────────

def _format_fact(fact: Dict[str, Any]) -> str:
    """Format a single fact as a readable sentence."""
    subject = fact.get("subject", "?").replace("_", " ")
    predicate = fact.get("predicate", "?").replace("_", " ")
    obj = fact.get("object", "?").replace("_", " ")
    return f"{subject} {predicate} {obj}"


def _present_facts(
    facts: List[Dict[str, Any]],
    project_name: Optional[str] = None,
    topic: Optional[str] = None,
) -> str:
    """Format a list of facts into a readable response."""
    if not facts:
        if project_name:
            return f"No recorded facts for project '{project_name}'" + (f" about '{topic}'" if topic else ".")
        return "No recorded facts found."

    lines = []
    if project_name:
        lines.append(f"From project '{project_name}':")
    elif topic:
        lines.append(f"About '{topic}':")

    for i, fact in enumerate(facts, 1):
        lines.append(f"  {i}. {_format_fact(fact)}")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Main bridge function
# ──────────────────────────────────────────────────────────────────────────────

def query_fact_engine(
    message: str,
    session_id: str,
    project_id: Optional[str] = None,
    fact_store_path: str = DEFAULT_FACT_STORE_PATH,
    registry_path: str = DEFAULT_REGISTRY_PATH,
) -> Dict[str, Any]:
    """Query the fact engine and return a formatted response.

    Args:
        message: The original user message (used for topic extraction)
        session_id: Current session ID (for active project resolution)
        project_id: Optional explicit project scope override
        fact_store_path: Path to fact assertions
        registry_path: Path to project registry

    Returns:
        dict with keys:
            - answer: str (formatted fact summary)
            - fact_count: int
            - facts: list[dict] (raw facts for debugging)
            - authority: "fact_engine"
            - project_name: str or None
            - topic: str or None
    """
    # Resolve project scope
    resolved_project_id = project_id
    project_name = None

    if not resolved_project_id:
        resolved_project_id = get_active_project(session_id)

    if resolved_project_id:
        project = get_project(resolved_project_id, registry_path=registry_path)
        if project:
            project_name = project.get("name", "")

    # Extract topic from message (simple keyword approach)
    topic = _extract_topic_from_message(message)

    # Load facts
    facts = _load_facts_for_query(
        topic=topic,
        project_id=resolved_project_id,
        fact_store_path=fact_store_path,
    )

    return {
        "answer": _present_facts(facts, project_name=project_name, topic=topic),
        "fact_count": len(facts),
        "facts": facts,
        "authority": "fact_engine",
        "project_name": project_name,
        "project_id": resolved_project_id,
        "topic": topic,
    }


def _extract_topic_from_message(message: str) -> Optional[str]:
    """Extract a topic noun from the message for fact matching."""
    import re

    # Patterns that indicate a relational query about a topic
    patterns = [
        r"about\s+(\S+)",
        r"regarding\s+(\S+)",
        r"related to\s+(\S+)",
        r"concerning\s+(\S+)",
        r"involving\s+(\S+)",
    ]

    lower = message.lower()
    for pattern in patterns:
        m = re.search(pattern, lower)
        if m:
            topic = m.group(1).strip().rstrip("?.,!")
            if topic and topic not in ("it", "this", "them", "that", "something"):
                return topic

    return None


def _load_facts_for_query(
    topic: Optional[str],
    project_id: Optional[str],
    fact_store_path: str,
) -> List[Dict[str, Any]]:
    """Load facts matching the query, trying subject then object match."""
    if topic:
        normalized_topic = topic.lower().replace(" ", "_")
        facts = load_facts(
            subject=normalized_topic,
            project_id=project_id,
            limit=20,
            fact_store_path=fact_store_path,
        )
        if not facts:
            facts = load_facts(
                obj=normalized_topic,
                project_id=project_id,
                limit=20,
                fact_store_path=fact_store_path,
            )
        return facts
    elif project_id:
        return load_facts(project_id=project_id, limit=20, fact_store_path=fact_store_path)
    else:
        return []


def build_relational_query_response(
    message: str,
    session_id: str,
    project_id: Optional[str] = None,
) -> str:
    """Convenience wrapper that returns just the answer string.

    Args:
        message: Original user message
        session_id: Current session
        project_id: Optional project override

    Returns:
        Formatted answer string
    """
    result = query_fact_engine(
        message=message,
        session_id=session_id,
        project_id=project_id,
    )
    return result["answer"]