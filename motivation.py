from __future__ import annotations

import json
from pathlib import Path

from config import CIRCLEFORGE_LANGUAGE


def resolve_or_extend_question(communicator: dict, chosen: dict, final_action: str | None) -> tuple[str, bool]:
    from languages import de, en
    
    lang_module = de if CIRCLEFORGE_LANGUAGE == "de" else en
    
    previous_question = str(communicator.get("unresolved_question", "")).strip()
    theme = chosen.get("niche_theme") or communicator.get("active_pursuit") or "current pressure"
    if final_action in {"inspect", "research"}:
        new_question = lang_module.theme_inspection_question(final_action, theme)
        return new_question, True
    if chosen.get("niche_theme"):
        new_question = lang_module.theme_unclear_question(theme)
        return new_question, False
    return previous_question or lang_module.fallback_question(), False


def average_internal_reputation(agent_name: str, *, load_relationships_func) -> tuple[float, float, float]:
    relationships = load_relationships_func()
    relevant = [item for item in relationships if item.get("target_agent") == agent_name]
    if not relevant:
        return 0.5, 0.5, 0.0
    trust = sum(float(item.get("trust", 0.5)) for item in relevant) / len(relevant)
    usefulness = sum(float(item.get("usefulness", 0.5)) for item in relevant) / len(relevant)
    friction = sum(float(item.get("friction", 0.0)) for item in relevant) / len(relevant)
    return round(trust, 3), round(usefulness, 3), round(friction, 3)


def role_memory_weight(agent_name: str, *, agents_dir: Path, classify_internal_role_func) -> float:
    agent_dir = agents_dir / str(agent_name)
    if not agent_dir.exists():
        return 0.0
    try:
        notes = json.loads((agent_dir / "memory.json").read_text())
    except Exception:
        notes = []
    role = classify_internal_role_func(agent_name)
    score = 0.0
    if role == "builder":
        yes = sum(1 for note in notes[-20:] if "builder-usefulness" in str(note).lower() and "later_activity_detected=yes" in str(note).lower())
        no = sum(1 for note in notes[-20:] if "builder-usefulness" in str(note).lower() and "later_activity_detected=no" in str(note).lower())
        score += max(0, yes - no) * 0.04
    elif role == "coordinator":
        yes = sum(1 for note in notes[-20:] if "coordinator-effect" in str(note).lower() and "follow_on_activity=yes" in str(note).lower())
        no = sum(1 for note in notes[-20:] if "coordinator-effect" in str(note).lower() and "follow_on_activity=no" in str(note).lower())
        score += max(0, yes - no) * 0.04
    elif role == "memory_keeper":
        clusters = sum(1 for note in notes[-20:] if "memory-keeper objection-cluster" in str(note).lower())
        score += clusters * 0.02
    return min(score, 0.18)


def decision_style_weight(communicator: dict, action: str | None, mode: str | None) -> float:
    memory = communicator.get("decision_style_memory") or {}
    score = 0.0
    if action:
        action_mem = memory.get("actions", {}).get(action, {})
        score += float(action_mem.get("confidence", 0.0)) * 0.12
    if mode:
        mode_mem = memory.get("modes", {}).get(mode, {})
        score += float(mode_mem.get("confidence", 0.0)) * 0.1
    return score


def update_decision_style_memory(communicator: dict, decision_mode: str, final_action: str | None, chosen: dict, unresolved_needs: list[str]) -> None:
    memory = communicator.get("decision_style_memory") or {}
    actions = memory.setdefault("actions", {})
    modes = memory.setdefault("modes", {})
    if final_action:
        entry = actions.setdefault(final_action, {"count": 0, "confidence": 0.0, "last_theme": ""})
        entry["count"] = int(entry.get("count", 0)) + 1
        delta = 0.06 if final_action in {"inspect", "research"} else 0.03
        if unresolved_needs and final_action in {"inspect", "research", "optimize"}:
            delta += 0.03
        entry["confidence"] = round(min(float(entry.get("confidence", 0.0)) + delta, 0.95), 3)
        entry["last_theme"] = chosen.get("niche_theme") or ""
    mode_entry = modes.setdefault(decision_mode, {"count": 0, "confidence": 0.0})
    mode_entry["count"] = int(mode_entry.get("count", 0)) + 1
    mode_delta = 0.05 if decision_mode in {"inspect-first", "reconsider"} else 0.03
    if decision_mode == "defer":
        mode_delta = 0.01
    mode_entry["confidence"] = round(min(float(mode_entry.get("confidence", 0.0)) + mode_delta, 0.95), 3)
    communicator["decision_style_memory"] = memory
