from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List

from config import (
    DAILY_COOLDOWN_SECONDS,
    MAX_MEMORY_NOTES,
    OPPORTUNITY_BOARD_PATH,
)

ACTIONS = ["gather", "optimize", "research", "build_module", "inspect", "trade", "signal", "rest"]


SEED_OPPORTUNITIES = {
    "backup confidence": {
        "target_user": "self-hosters and small operators",
        "problem": "people do not trust their backups until restore day",
        "gap": "existing backup tooling is often too noisy or too heavyweight for simple sanity checks",
        "delivery_mode": "standalone_microproduct",
        "price_band": "20-100eur",
        "categories": ["debugging", "exports", "research"],
        "actions": ["inspect", "research", "build_module"],
    },
    "service visibility": {
        "target_user": "self-hosters and small operators",
        "problem": "small operators lack a dead-simple health and status view",
        "gap": "full observability stacks are too heavy for tiny installations",
        "delivery_mode": "standalone_microproduct",
        "price_band": "50-200eur",
        "categories": ["debugging", "exports", "optimization"],
        "actions": ["inspect", "optimize", "build_module"],
    },
    "config sanity checks": {
        "target_user": "indie builders and local AI tinkerers",
        "problem": "people lose time to avoidable configuration mistakes",
        "gap": "many validators are generic but not tuned to practical local workflows",
        "delivery_mode": "consulting_accelerator",
        "price_band": "20-100eur",
        "categories": ["modules", "optimization", "research"],
        "actions": ["build_module", "optimize", "research"],
    },
    "log readability": {
        "target_user": "technical builders",
        "problem": "raw logs are hard to scan during small incidents",
        "gap": "existing tooling is often overbuilt when all people need is a readable local summary",
        "delivery_mode": "bundle_candidate",
        "price_band": "20-100eur",
        "categories": ["debugging", "memory", "research"],
        "actions": ["inspect", "research", "build_module"],
    },
    "workflow packaging": {
        "target_user": "indie builders and local AI tinkerers",
        "problem": "useful helper code stays trapped inside one project or experiment",
        "gap": "many teams lack small packaging wrappers that make internal helpers reusable",
        "delivery_mode": "consulting_accelerator",
        "price_band": "50-200eur",
        "categories": ["modules", "exports", "optimization"],
        "actions": ["build_module", "trade", "optimize"],
    },
}


def load_notes(agent_dir: Path) -> List[str]:
    memory_path = agent_dir / "memory.json"
    if not memory_path.exists():
        return []
    try:
        data = json.loads(memory_path.read_text())
        if isinstance(data, list):
            return [str(x) for x in data][-MAX_MEMORY_NOTES:]
    except Exception:
        pass
    return []


def save_note(agent_dir: Path, note: str) -> None:
    notes = load_notes(agent_dir)
    notes.append(note)
    notes = notes[-MAX_MEMORY_NOTES:]
    (agent_dir / "memory.json").write_text(json.dumps(notes, indent=2))


def inbox_path(agent_dir: Path) -> Path:
    return agent_dir / "inbox.json"


def load_inbox(agent_dir: Path) -> List[Dict[str, Any]]:
    data = read_json(inbox_path(agent_dir), [])
    if isinstance(data, list):
        return data[-MAX_MEMORY_NOTES:]
    return []


def save_inbox(agent_dir: Path, items: List[Dict[str, Any]]) -> None:
    write_json(inbox_path(agent_dir), items[-MAX_MEMORY_NOTES:])


def push_inbox_message(agent_dir: Path, message: Dict[str, Any]) -> None:
    inbox = load_inbox(agent_dir)
    inbox.append(message)
    save_inbox(agent_dir, inbox)


def can_inspect(agent: Dict[str, Any], now_ts: int) -> bool:
    return now_ts - int(agent.get("last_inspect_at", 0)) >= DAILY_COOLDOWN_SECONDS


def can_trade(agent: Dict[str, Any], now_ts: int) -> bool:
    return now_ts - int(agent.get("last_trade_at", 0)) >= DAILY_COOLDOWN_SECONDS


def choose_target(agent: Dict[str, Any], world: Dict[str, Any]) -> str | None:
    visible_agents = [name for name in world.get("agent_names", []) if name != agent["name"]]
    if not visible_agents:
        return None
    relationships = world.get("relationships", []) or []
    ranked = []
    for name in visible_agents:
        rel = next((item for item in relationships if item.get("source_agent") == agent["name"] and item.get("target_agent") == name), None)
        if rel:
            score = float(rel.get("trust", 0.5)) * 0.5 + float(rel.get("usefulness", 0.5)) * 0.5 - float(rel.get("friction", 0.0)) * 0.6
        else:
            score = 0.5
        score += random.uniform(0.0, 0.08)
        ranked.append((score, name))
    ranked.sort(reverse=True)
    return ranked[0][1]


def read_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def opportunity_memory_path(agent_dir: Path) -> Path:
    return agent_dir / "opportunity_memory.json"


def load_opportunity_memory(agent_dir: Path) -> Dict[str, Any]:
    default = {
        "themes": {theme: {"strength": 0.3, "wins": 0, "failures": 0, "last_action": None, "last_category": None} for theme in SEED_OPPORTUNITIES},
        "last_theme": None,
    }
    data = read_json(opportunity_memory_path(agent_dir), default)
    data.setdefault("themes", {})
    for theme in SEED_OPPORTUNITIES:
        data["themes"].setdefault(theme, {"strength": 0.3, "wins": 0, "failures": 0, "last_action": None, "last_category": None})
    data.setdefault("last_theme", None)
    return data


def save_opportunity_memory(agent_dir: Path, payload: Dict[str, Any]) -> None:
    write_json(opportunity_memory_path(agent_dir), payload)


def load_opportunity_board() -> Dict[str, Any]:
    default = {"themes": {theme: {"pressure": 0.4, "evidence": 0, "updated_at": 0, "lifecycle": "stable"} for theme in SEED_OPPORTUNITIES}, "emergent_candidates": []}
    data = read_json(OPPORTUNITY_BOARD_PATH, default)
    data.setdefault("themes", {})
    data.setdefault("emergent_candidates", [])
    for theme in SEED_OPPORTUNITIES:
        data["themes"].setdefault(theme, {"pressure": 0.4, "evidence": 0, "updated_at": 0, "lifecycle": "stable"})
    return data


def profile_for_theme(theme: str) -> Dict[str, Any]:
    return SEED_OPPORTUNITIES.get(theme, {
        "target_user": "technical builders",
        "problem": f"repeated friction appears around {theme}",
        "gap": f"existing options around {theme} look too broad or awkward",
        "delivery_mode": "bundle_candidate",
        "price_band": "needs-packaging",
        "categories": ["uncategorized", "research"],
        "actions": ["research", "build_module", "optimize"],
    })


def choose_theme_for_action(agent_dir: Path, action: str, category: str, world: Dict[str, Any]) -> str:
    memory = load_opportunity_memory(agent_dir)
    board = world.get("opportunity_board") or load_opportunity_board()
    inbox = load_inbox(agent_dir)
    recent_notes = [note.lower() for note in load_notes(agent_dir)[-8:]]
    themes = []
    theme_names = sorted(set(list(SEED_OPPORTUNITIES.keys()) + list((board.get("themes") or {}).keys())))
    for theme in theme_names:
        profile = profile_for_theme(theme)
        local = memory["themes"].get(theme, {})
        board_theme = board.get("themes", {}).get(theme, {})
        score = float(local.get("strength", 0.3)) * 0.55 + float(board_theme.get("pressure", 0.4)) * 0.35
        if action in profile.get("actions", []):
            score += 0.12
        if category in profile.get("categories", []):
            score += 0.1
        if memory.get("last_theme") == theme:
            score += 0.04
        repeated_mentions = sum(1 for note in recent_notes if theme in note)
        if repeated_mentions >= 3:
            score -= 0.08
        inbox_hits = sum(1 for item in inbox if str(item.get("theme", "")) == theme)
        score += min(inbox_hits * 0.06, 0.18)
        unresolved_needs = world.get("unresolved_needs", []) or []
        if any(theme in str(item).lower() for item in unresolved_needs):
            score += 0.12
        lifecycle = str(board_theme.get("lifecycle", "stable"))
        if lifecycle == "emergent":
            score += 0.03
        elif lifecycle == "dormant":
            score -= 0.08
        elif lifecycle == "declining":
            score -= 0.04
        score += random.uniform(0.0, 0.06)
        themes.append((score, theme))
    themes.sort(reverse=True)
    return themes[0][1]


def choose_niche(agent_dir: Path, action: str, category: str, world: Dict[str, Any]) -> Dict[str, Any]:
    theme = choose_theme_for_action(agent_dir, action, category, world)
    niche = profile_for_theme(theme)
    delivery_mode = niche["delivery_mode"] if category != "research" else "internal_reusable_component"
    confidence = 0.35 + min(load_opportunity_memory(agent_dir)["themes"].get(theme, {}).get("strength", 0.3) * 0.4, 0.35)
    return {
        "niche_theme": theme,
        "target_user": niche["target_user"],
        "problem_statement": niche["problem"],
        "gap_reason": niche["gap"],
        "delivery_mode_guess": delivery_mode,
        "price_band_guess": niche["price_band"],
        "research_confidence": round(min(confidence, 0.92), 3),
        "existing_solution_friction": niche["gap"],
        "artifact_hypothesis": f"Build a small {category if category != 'uncategorized' else 'utility'} artifact around {theme}",
        "offer_hypothesis": f"A narrow {theme} helper could be packaged for {niche['target_user']}",
    }


def fallback_policy(agent: Dict[str, Any], world: Dict[str, Any], notes: List[str]) -> Dict[str, Any]:
    now_ts = int(world.get("now_ts", 0))
    target = choose_target(agent, world)
    categories = world.get("categories", [])
    agent_dir = Path(world["base_dir"]) / "agents" / agent["name"]
    inbox = load_inbox(agent_dir)
    unresolved_needs = world.get("unresolved_needs", []) or []
    work_items = world.get("work_items", []) or []
    communicator = world.get("communicator", {}) or {}
    current_intent = str(communicator.get("current_intent", "")).lower()
    active_pursuit = str(communicator.get("active_pursuit", "")).lower()
    curiosity_target = str(communicator.get("curiosity_target", "")).lower()
    unresolved_question = str(communicator.get("unresolved_question", "")).lower()
    curiosity = float(communicator.get("curiosity", 0.6))
    my_work = [item for item in work_items if item.get("owner") == agent["name"] and item.get("status") == "open"]
    repeated_builds = sum(1 for note in notes[-6:] if "built module" in note.lower())

    if agent["energy"] < 30:
        action = "rest"
    elif unresolved_question and random.random() < 0.42:
        action = random.choice(["inspect", "research"])
    elif curiosity > 0.8 and random.random() < 0.4:
        action = random.choice(["inspect", "research"])
    elif my_work and random.random() < 0.45:
        action = random.choice(["research", "optimize", "build_module"])
    elif inbox and target and random.random() < 0.28:
        action = "signal"
    elif unresolved_needs and random.random() < 0.32:
        action = random.choice(["inspect", "research", "optimize"])
    elif not list((agent_dir / "modules").glob("*.py")):
        action = "build_module"
    elif repeated_builds >= 3 and random.random() < 0.55:
        action = random.choice(["research", "optimize", "inspect"] if target else ["research", "optimize"])
    elif target and can_inspect(agent, now_ts) and random.random() < 0.18:
        action = "inspect"
    elif target and can_trade(agent, now_ts) and agent.get("storage", 0) > 20 and random.random() < 0.14:
        action = "trade"
    else:
        action = random.choices(
            population=["gather", "optimize", "research", "build_module", "signal", "rest"],
            weights=[2, 4, 4, 2, 2, 1],
            k=1,
        )[0]

    if random.random() < 0.18:
        category = "uncategorized"
    else:
        category = random.choice(categories) if categories else "uncategorized"
    niche = choose_niche(agent_dir=agent_dir, action=action, category=category, world=world)
    reason = f"fallback policy selected {action}"
    if inbox and action == "signal":
        newest = inbox[-1]
        reason = f"responding to message from {newest.get('from', 'unknown')} about {newest.get('theme', 'shared need')}"
    elif unresolved_question and niche.get("niche_theme", "").lower() in unresolved_question and action in {"inspect", "research"}:
        reason = f"following unresolved question: {communicator.get('unresolved_question')}"
    elif current_intent and (niche.get("niche_theme", "").lower() in current_intent or action in current_intent):
        reason = f"following communicator intent: {communicator.get('current_intent')}"
    elif active_pursuit and niche.get("niche_theme", "").lower() in active_pursuit:
        reason = f"following active pursuit: {communicator.get('active_pursuit')}"
    elif curiosity_target and niche.get("niche_theme", "").lower() in curiosity_target and action in {"inspect", "research", "signal"}:
        reason = f"following curiosity target: {communicator.get('curiosity_target')}"
    elif my_work and action in {"research", "optimize", "build_module"}:
        reason = f"advancing assigned work: {my_work[0].get('title', 'project work')}"
    elif unresolved_needs and action in {"inspect", "research", "optimize"}:
        reason = f"responding to unresolved need: {unresolved_needs[0]}"
    elif curiosity > 0.8 and action in {"inspect", "research"}:
        reason = f"following curiosity pressure from communicator state"

    return {
        "action": action,
        "reason": reason,
        "code": default_code_for(action, agent["name"]),
        "target": target if action in {"inspect", "trade", "signal"} else None,
        "category": category,
        **niche,
    }


def default_code_for(action: str, agent_name: str) -> str:
    if action == "build_module":
        return f'''from pathlib import Path\nPath("modules").mkdir(exist_ok=True)\nPath("modules/helper_{agent_name}.py").write_text("def score(x):\\n    return x * 2\\n")\nprint("built helper module")\n'''
    if action == "optimize":
        return '''from pathlib import Path\nPath("artifacts").mkdir(exist_ok=True)\nPath("artifacts/optimization.txt").write_text("cache:enabled\\ncheckpointing:on\\n")\nprint("optimized local workflow")\n'''
    if action == "research":
        return '''from pathlib import Path\nPath("artifacts").mkdir(exist_ok=True)\nPath("artifacts/research.txt").write_text("Observation: shorter loops waste less time.\\n")\nprint("research note saved")\n'''
    if action == "gather":
        return 'print("gathered local resources")\n'
    if action == "signal":
        return 'print("shared local signal")\n'
    return 'print("non-code action")\n'


def decide_action(agent: Dict[str, Any], world: Dict[str, Any], agent_dir: Path) -> Dict[str, Any]:
    notes = load_notes(agent_dir)
    result = fallback_policy(agent, world, notes)
    if not result.get("code"):
        result["code"] = default_code_for(result["action"], agent["name"])
    return result
