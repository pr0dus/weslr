from __future__ import annotations

import json
import random
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from config import MAX_CODE_SIZE, MAX_MEMORY_NOTES, OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS


ACTIONS = ["gather", "optimize", "research", "build_module", "rest"]


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


def fallback_policy(agent: Dict[str, Any], world: Dict[str, Any], notes: List[str]) -> Dict[str, Any]:
    if agent["energy"] < 30:
        action = "rest"
    elif not list((Path(world["base_dir"]) / "agents" / agent["name"] / "modules").glob("*.py")):
        action = "build_module"
    else:
        action = random.choices(
            population=ACTIONS,
            weights=[3, 3, 2, 2, 1],
            k=1,
        )[0]

    return {
        "action": action,
        "reason": f"fallback policy selected {action}",
        "code": default_code_for(action, agent["name"]),
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
    return 'print("resting")\n'


def ask_ollama(agent: Dict[str, Any], world: Dict[str, Any], notes: List[str]) -> Dict[str, Any] | None:
    prompt = {
        "task": "Choose exactly one action for this coding agent in a persistent simulation.",
        "allowed_actions": ACTIONS,
        "rules": [
            "No sabotage.",
            "No stealing.",
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
        return {
            "action": action,
            "reason": str(data.get("reason", "ollama")),
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
