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


NICHES = [
    {
        "theme": "backup confidence",
        "target_user": "self-hosters and small operators",
        "problem": "people do not trust their backups until restore day",
        "gap": "existing backup tooling is often too noisy or too heavyweight for simple sanity checks",
        "delivery_mode": "standalone_microproduct",
        "price_band": "20-100eur",
    },
    {
        "theme": "service visibility",
        "target_user": "self-hosters and small operators",
        "problem": "small operators lack a dead-simple health and status view",
        "gap": "full observability stacks are too heavy for tiny installations",
        "delivery_mode": "standalone_microproduct",
        "price_band": "50-200eur",
    },
    {
        "theme": "config sanity checks",
        "target_user": "indie builders and local AI tinkerers",
        "problem": "people lose time to avoidable configuration mistakes",
        "gap": "many validators are generic but not tuned to practical local workflows",
        "delivery_mode": "consulting_accelerator",
        "price_band": "20-100eur",
    },
    {
        "theme": "log readability",
        "target_user": "technical builders",
        "problem": "raw logs are hard to scan during small incidents",
        "gap": "existing tooling is often overbuilt when all people need is a readable local summary",
        "delivery_mode": "bundle_candidate",
        "price_band": "20-100eur",
    },
    {
        "theme": "workflow packaging",
        "target_user": "indie builders and local AI tinkerers",
        "problem": "useful helper code stays trapped inside one project or experiment",
        "gap": "many teams lack small packaging wrappers that make internal helpers reusable",
        "delivery_mode": "consulting_accelerator",
        "price_band": "50-200eur",
    },
]


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


def choose_niche(action: str, category: str) -> Dict[str, Any]:
    niche = random.choice(NICHES).copy()
    if action == "inspect":
        niche["theme"] = "service visibility"
        niche["problem"] = "small operators cannot quickly inspect service state and drift"
    elif action == "optimize":
        niche["theme"] = "workflow packaging"
        niche["problem"] = "repeated local workflow pain should become a reusable helper"
    elif action == "research":
        niche["theme"] = random.choice(["backup confidence", "config sanity checks", "log readability"])
    if category == "research":
        niche["delivery_mode"] = "internal_reusable_component"
    return {
        "niche_theme": niche["theme"],
        "target_user": niche["target_user"],
        "problem_statement": niche["problem"],
        "gap_reason": niche["gap"],
        "delivery_mode_guess": niche["delivery_mode"],
        "price_band_guess": niche["price_band"],
        "research_confidence": round(random.uniform(0.42, 0.78), 3),
        "existing_solution_friction": niche["gap"],
        "artifact_hypothesis": f"Build a small {category if category != 'uncategorized' else 'utility'} artifact around {niche['theme']}",
        "offer_hypothesis": f"A narrow {niche['theme']} helper could be packaged for {niche['target_user']}",
    }


def fallback_policy(agent: Dict[str, Any], world: Dict[str, Any], notes: List[str]) -> Dict[str, Any]:
    now_ts = int(world.get("now_ts", 0))
    target = choose_target(agent, world)
    categories = world.get("categories", [])

    if agent["energy"] < 30:
        action = "rest"
    elif not list((Path(world["base_dir"]) / "agents" / agent["name"] / "modules").glob("*.py")):
        action = "build_module"
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

    if random.random() < 0.18:
        category = "uncategorized"
    else:
        category = random.choice(categories) if categories else "uncategorized"
    niche = choose_niche(action, category)

    return {
        "action": action,
        "reason": f"fallback policy selected {action}",
        "code": default_code_for(action, agent["name"]),
        "target": target if action in {"inspect", "trade"} else None,
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
            "category": "one existing category or uncategorized",
            "niche_theme": "short niche or opportunity label",
            "target_user": "specific likely user",
            "problem_statement": "specific repeated pain",
            "gap_reason": "why existing options are too annoying, expensive, broad, or heavyweight",
            "delivery_mode_guess": "standalone_microproduct|consulting_accelerator|bundle_candidate|internal_reusable_component",
            "price_band_guess": "small plausible price band",
            "research_confidence": "0-1 confidence",
            "artifact_hypothesis": "small tool or artifact concept tied to the niche",
            "offer_hypothesis": "how it could be packaged or sold",
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
        valid_categories = set(world.get("categories", [])) | {"uncategorized"}
        if action in {"inspect", "trade"} and target not in world.get("agent_names", []):
            target = choose_target(agent, world)
        if category not in valid_categories:
            category = "uncategorized"
        niche = {
            "niche_theme": str(data.get("niche_theme", "local workflow gap"))[:120],
            "target_user": str(data.get("target_user", "technical builders"))[:160],
            "problem_statement": str(data.get("problem_statement", "A repeated local workflow problem should be reduced."))[:240],
            "gap_reason": str(data.get("gap_reason", "Existing options look heavier than the actual need."))[:240],
            "delivery_mode_guess": str(data.get("delivery_mode_guess", "bundle_candidate"))[:80],
            "price_band_guess": str(data.get("price_band_guess", "20-100eur"))[:80],
            "research_confidence": max(0.01, min(float(data.get("research_confidence", 0.55)), 0.99)),
            "artifact_hypothesis": str(data.get("artifact_hypothesis", "Build a small reusable local helper."))[:240],
            "offer_hypothesis": str(data.get("offer_hypothesis", "Package the helper into a small reusable offer."))[:240],
            "existing_solution_friction": str(data.get("gap_reason", "Existing options look heavier than the actual need."))[:240],
        }
        return {
            "action": action,
            "reason": str(data.get("reason", "ollama")),
            "target": target if action in {"inspect", "trade"} else None,
            "category": category,
            "code": code or default_code_for(action, agent["name"]),
            **niche,
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
