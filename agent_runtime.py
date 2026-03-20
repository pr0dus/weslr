from __future__ import annotations

import json
import random
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from config import (
    DAILY_COOLDOWN_SECONDS,
    MAX_CODE_SIZE,
    MAX_MEMORY_NOTES,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    PROJECT_NAME,
    VERSION,
)


ACTIONS = ["gather", "optimize", "research", "build_module", "inspect", "trade", "rest"]


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


def can_inspect(agent: Dict[str, Any], now_ts: int) -> bool:
    return now_ts - int(agent.get("last_inspect_at", 0)) >= DAILY_COOLDOWN_SECONDS


def can_trade(agent: Dict[str, Any], now_ts: int) -> bool:
    return now_ts - int(agent.get("last_trade_at", 0)) >= DAILY_COOLDOWN_SECONDS


def choose_target(agent: Dict[str, Any], world: Dict[str, Any]) -> str | None:
    visible_agents = [name for name in world.get("agent_names", []) if name != agent["name"]]
    if not visible_agents:
        return None
    return random.choice(visible_agents)


def fallback_policy(agent: Dict[str, Any], world: Dict[str, Any], notes: List[str]) -> Dict[str, Any]:
    now_ts = int(world.get("now_ts", 0))
    target = choose_target(agent, world)
    open_proposals = world.get("open_category_proposals", [])
    categories = world.get("categories", [])

    if agent["energy"] < 30:
        action = "rest"
    elif not list((Path(world["base_dir"]) / "agents" / agent["name"] / "modules").glob("*.py")):
        action = "build_module"
    elif open_proposals and random.random() < 0.2:
        action = random.choice(["research", "optimize"])
    elif target and can_inspect(agent, now_ts) and random.random() < 0.15:
        action = "inspect"
    elif target and can_trade(agent, now_ts) and agent.get("storage", 0) > 20 and random.random() < 0.12:
        action = "trade"
    else:
        action = random.choices(
            population=["gather", "optimize", "research", "build_module", "rest"],
            weights=[3, 3, 2, 2, 1],
            k=1,
        )[0]

    category = random.choice(categories) if categories else None
    return {
        "action": action,
        "reason": f"fallback policy selected {action}",
        "code": default_code_for(action, agent["name"]),
        "target": target if action in {"inspect", "trade"} else None,
        "category": category,
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
    return 'print("non-code action")\n'


def ask_ollama(agent: Dict[str, Any], world: Dict[str, Any], notes: List[str]) -> Dict[str, Any] | None:
    prompt = {
        "task": "Choose exactly one action for this coding agent in a persistent simulation.",
        "project": f"{PROJECT_NAME} v{VERSION}",
        "allowed_actions": ACTIONS,
        "rules": [
            "No sabotage.",
            "No stealing.",
            "Inspect allowed only once every 24 hours.",
            "Trade allowed only once every 24 hours.",
            "Act within one short tick.",
            "Prefer resumable progress.",
            "Return strict JSON only.",
        ],
        "agent": agent,
        "recent_notes": notes[-8:],
        "world": {k: v for k, v in world.items() if k != "base_dir"},
        "response_schema": {
            "action": "one of allowed_actions",
            "reason": "short string",
            "target": "another agent name for inspect/trade, otherwise null",
            "category": "one existing category if relevant, otherwise null",
            "code": "short python script, optional but preferred"
        },
    }
    body = {
        "model": OLLAMA_MODEL,
        "prompt": json.dumps(prompt, ensure_ascii=False),
        "stream": False,
        "format": "json",
    }
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_SECONDS) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        response_text = payload.get("response", "")
        data = json.loads(response_text)
        action = data.get("action")
        if action not in ACTIONS:
            return None
        code = str(data.get("code", ""))[:MAX_CODE_SIZE]
        target = data.get("target")
        category = data.get("category")
        if action in {"inspect", "trade"} and target not in world.get("agent_names", []):
            target = choose_target(agent, world)
        if category not in world.get("categories", []):
            category = random.choice(world.get("categories", [])) if world.get("categories") else None
        return {
            "action": action,
            "reason": str(data.get("reason", "ollama")),
            "target": target if action in {"inspect", "trade"} else None,
            "category": category,
            "code": code or default_code_for(action, agent["name"]),
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError):
        return None


def decide_action(agent: Dict[str, Any], world: Dict[str, Any], agent_dir: Path) -> Dict[str, Any]:
    notes = load_notes(agent_dir)
    result = ask_ollama(agent, world, notes)
    if result is None:
        result = fallback_policy(agent, world, notes)
    if not result.get("code"):
        result["code"] = default_code_for(result["action"], agent["name"])
    return result
