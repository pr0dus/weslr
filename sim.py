from __future__ import annotations

import json
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Dict, List

from agent_runtime import decide_action, save_note
from config import (
    AGENTS_DIR,
    BASE_DIR,
    CODE_TIMEOUT_SECONDS,
    DAILY_COOLDOWN_SECONDS,
    DB_PATH,
    DEFAULT_AGENT_COUNT,
    DEMAND_BOARD_PATH,
    EXECUTION_BUDGET_SECONDS,
    EXPORT_QUEUE_PATH,
    EXPORT_READY_THRESHOLD,
    EXPORTS_DIR,
    MAX_DEMAND_ITEMS,
    MAX_EXPORT_QUEUE,
    MAX_REVIEW_QUEUE,
    PROJECT_NAME,
    REVIEW_QUEUE_PATH,
    STARTING_ENERGY,
    STARTING_GPU,
    STARTING_REPUTATION,
    STARTING_STORAGE,
    TICK_SECONDS,
    VERSION,
)
from models import ActionResult, AgentState
from sandbox import run_python


SCHEMA = '''
CREATE TABLE IF NOT EXISTS world (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agents (
    name TEXT PRIMARY KEY,
    energy INTEGER NOT NULL,
    storage INTEGER NOT NULL,
    gpu_quota INTEGER NOT NULL,
    reputation REAL NOT NULL,
    last_inspect_at INTEGER NOT NULL,
    last_trade_at INTEGER NOT NULL,
    age_ticks INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tick INTEGER NOT NULL,
    agent_name TEXT NOT NULL,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    summary TEXT NOT NULL,
    raw_output TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
'''


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def read_json_file(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def write_json_file(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2))


def compute_internal_score(meta: Dict) -> float:
    score = 0.2
    score += min(len(meta.get("combinable_with", [])) * 0.08, 0.24)
    score += 0.18 if meta.get("destination") in {"shared_with_agents", "internal_review", "github_module"} else 0.08
    score += 0.14 if meta.get("purpose") else 0.0
    score += 0.14 if meta.get("explanation") else 0.0
    score += 0.10 if meta.get("lineage") else 0.0
    return round(min(score, 0.99), 3)


def compute_human_proposed_score(meta: Dict) -> float:
    score = 0.18
    score += 0.16 if meta.get("artifact_type") == "export_candidate" else 0.08
    score += 0.16 if meta.get("destination") in {"github_module", "shared_with_agents"} else 0.06
    score += min(len(meta.get("future_directions", [])) * 0.06, 0.18)
    score += 0.12 if meta.get("idea") else 0.0
    score += 0.12 if meta.get("why_now") else 0.0
    score += 0.10 if meta.get("if_interest_exists") else 0.0
    return round(min(score, 0.99), 3)


def update_artifact_scores(meta: Dict) -> Dict:
    meta["internal_score"] = compute_internal_score(meta)
    meta["human_proposed_score"] = compute_human_proposed_score(meta)
    return meta


def maybe_promote_for_review(meta: Dict, meta_file: Path) -> Dict:
    review_status = meta.get("review_status", "unreviewed")
    meta.setdefault("review_notes", [])
    meta.setdefault("approved_for_export", False)
    meta.setdefault("export_path", None)

    if meta.get("human_proposed_score", 0.0) >= 0.65 and review_status == "unreviewed":
        meta["review_status"] = "proposed"
        meta["review_notes"].append("Auto-proposed for human review based on score threshold.")

    if meta.get("human_proposed_score", 0.0) >= EXPORT_READY_THRESHOLD and meta.get("review_status") in {"proposed", "approved", "export_ready"}:
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        export_name = f"{meta.get('id', meta_file.stem)}.json"
        export_path = EXPORTS_DIR / export_name
        export_payload = {
            "title": meta.get("title"),
            "artifact_type": meta.get("artifact_type"),
            "idea": meta.get("idea"),
            "explanation": meta.get("explanation"),
            "purpose": meta.get("purpose"),
            "destination": meta.get("destination"),
            "future_directions": meta.get("future_directions", []),
            "internal_score": meta.get("internal_score"),
            "human_proposed_score": meta.get("human_proposed_score"),
            "source_meta": str(meta_file.relative_to(BASE_DIR)),
        }
        write_json_file(export_path, export_payload)
        meta["review_status"] = "export_ready"
        meta["approved_for_export"] = True
        meta["export_path"] = str(export_path.relative_to(BASE_DIR))
        note = "Auto-promoted to export_ready by score threshold."
        if note not in meta["review_notes"]:
            meta["review_notes"].append(note)

    return meta


def refresh_demand_board_and_export_queue() -> tuple[list, list, list]:
    artifact_meta = []
    type_counts: Dict[str, int] = {}
    destinations: Dict[str, int] = {}

    for meta_file in AGENTS_DIR.glob("*/artifacts/*.meta.json"):
        try:
            meta = json.loads(meta_file.read_text())
        except Exception:
            continue
        meta = update_artifact_scores(meta)
        meta = maybe_promote_for_review(meta, meta_file)
        meta_file.write_text(json.dumps(meta, indent=2))
        meta["path"] = str(meta_file.relative_to(BASE_DIR))
        artifact_meta.append(meta)
        type_counts[meta.get("artifact_type", "unknown")] = type_counts.get(meta.get("artifact_type", "unknown"), 0) + 1
        destinations[meta.get("destination", "unknown")] = destinations.get(meta.get("destination", "unknown"), 0) + 1

    demand_board = []
    if any(meta.get("artifact_type") == "market_hypothesis" for meta in artifact_meta):
        demand_board.append({
            "kind": "demand",
            "title": "Turn research notes into reusable export artifacts",
            "reason": "Research notes exist, but they need packaging paths and clearer export destinations.",
        })
    if type_counts.get("export_candidate", 0) > 0:
        demand_board.append({
            "kind": "demand",
            "title": "Rank export candidates for human review",
            "reason": "There are exportable modules/components that should be shortlisted outside the sim.",
        })
    if any(meta.get("review_status") == "proposed" for meta in artifact_meta):
        demand_board.append({
            "kind": "review",
            "title": "Human review queue has proposed artifacts",
            "reason": "Some artifacts crossed the review threshold and should be inspected by a human.",
        })
    if any(meta.get("review_status") == "export_ready" for meta in artifact_meta):
        demand_board.append({
            "kind": "export",
            "title": "Export-ready artifacts available",
            "reason": "At least one artifact is ready for human inspection or external packaging.",
        })
    if len(artifact_meta) >= 3:
        demand_board.append({
            "kind": "demand",
            "title": "Bundle related artifacts into packs",
            "reason": "The artifact count is high enough that grouping by theme or function now matters.",
        })

    demand_board = demand_board[:MAX_DEMAND_ITEMS]
    export_queue = sorted(
        [
            {
                "id": meta.get("id"),
                "title": meta.get("title"),
                "artifact_type": meta.get("artifact_type"),
                "path": meta.get("path"),
                "destination": meta.get("destination"),
                "internal_score": meta.get("internal_score", 0.0),
                "human_proposed_score": meta.get("human_proposed_score", 0.0),
                "review_status": meta.get("review_status", "unreviewed"),
                "approved_for_export": meta.get("approved_for_export", False),
                "export_path": meta.get("export_path"),
                "status": meta.get("status", "prototype"),
            }
            for meta in artifact_meta
            if meta.get("human_proposed_score", 0.0) >= 0.45 or meta.get("artifact_type") == "export_candidate"
        ],
        key=lambda item: (item["human_proposed_score"], item["internal_score"]),
        reverse=True,
    )[:MAX_EXPORT_QUEUE]

    review_queue = sorted(
        [
            {
                "id": meta.get("id"),
                "title": meta.get("title"),
                "artifact_type": meta.get("artifact_type"),
                "path": meta.get("path"),
                "review_status": meta.get("review_status", "unreviewed"),
                "review_notes": meta.get("review_notes", []),
                "human_proposed_score": meta.get("human_proposed_score", 0.0),
                "approved_for_export": meta.get("approved_for_export", False),
                "export_path": meta.get("export_path"),
            }
            for meta in artifact_meta
            if meta.get("review_status") in {"proposed", "approved", "export_ready"}
        ],
        key=lambda item: item["human_proposed_score"],
        reverse=True,
    )[:MAX_REVIEW_QUEUE]

    write_json_file(DEMAND_BOARD_PATH, demand_board)
    write_json_file(EXPORT_QUEUE_PATH, export_queue)
    write_json_file(REVIEW_QUEUE_PATH, review_queue)
    return demand_board, export_queue, review_queue


def init_world(agent_count: int = DEFAULT_AGENT_COUNT, reset: bool = False) -> None:
    if reset:
        if DB_PATH.exists():
            DB_PATH.unlink()
        if AGENTS_DIR.exists():
            shutil.rmtree(AGENTS_DIR)
        for path in [DEMAND_BOARD_PATH, EXPORT_QUEUE_PATH, REVIEW_QUEUE_PATH]:
            if path.exists():
                path.unlink()
        if EXPORTS_DIR.exists():
            shutil.rmtree(EXPORTS_DIR)
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    conn = connect()
    with conn:
        conn.execute("DELETE FROM world")
        conn.execute("DELETE FROM agents")
        conn.execute("DELETE FROM logs")
        conn.execute("INSERT INTO world(key, value) VALUES (?, ?)", ("tick", "0"))
        conn.execute("INSERT INTO world(key, value) VALUES (?, ?)", ("last_tick_started", "0"))
        for i in range(1, agent_count + 1):
            name = f"agent-{i}"
            agent_dir = AGENTS_DIR / name
            for sub in ["modules", "artifacts"]:
                (agent_dir / sub).mkdir(parents=True, exist_ok=True)
            (agent_dir / "memory.json").write_text("[]")
            state = AgentState(
                name=name,
                energy=STARTING_ENERGY,
                storage=STARTING_STORAGE,
                gpu_quota=STARTING_GPU,
                reputation=STARTING_REPUTATION,
            )
            conn.execute(
                "INSERT INTO agents(name, energy, storage, gpu_quota, reputation, last_inspect_at, last_trade_at, age_ticks) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (state.name, state.energy, state.storage, state.gpu_quota, state.reputation, state.last_inspect_at, state.last_trade_at, state.age_ticks),
            )
    refresh_demand_board_and_export_queue()
    conn.close()


def get_world(conn: sqlite3.Connection) -> Dict:
    rows = conn.execute("SELECT key, value FROM world").fetchall()
    data = {row["key"]: row["value"] for row in rows}
    return {
        "project": PROJECT_NAME,
        "version": VERSION,
        "tick": int(data.get("tick", 0)),
        "last_tick_started": int(data.get("last_tick_started", 0)),
        "base_dir": str(BASE_DIR),
        "execution_budget_seconds": EXECUTION_BUDGET_SECONDS,
        "code_timeout_seconds": CODE_TIMEOUT_SECONDS,
        "tick_seconds": TICK_SECONDS,
    }


def list_agents(conn: sqlite3.Connection) -> List[Dict]:
    return [dict(row) for row in conn.execute("SELECT * FROM agents ORDER BY name").fetchall()]


def write_artifact_metadata(agent: Dict, agent_dir: Path, artifact_slug: str, artifact_type: str, idea: str, explanation: str, purpose: str, destination: str, future_directions: List[str], combinable_with: List[str], lineage: Dict) -> str:
    artifacts_dir = agent_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_id = f"{agent['name']}-{artifact_slug}-{int(time.time())}"
    meta_path = artifacts_dir / f"{artifact_slug}.meta.json"
    payload = {
        "id": artifact_id,
        "title": artifact_slug.replace("_", " ").title(),
        "artifact_type": artifact_type,
        "idea": idea,
        "explanation": explanation,
        "purpose": purpose,
        "destination": destination,
        "audience": ["local AI tinkerers", "agent-sim builders"],
        "depends_on": ["persistent memory", "timed ticks"],
        "combinable_with": combinable_with,
        "why_now": "CircleForge agents benefit from reusable, inspectable outputs instead of opaque internal work.",
        "future_directions": future_directions,
        "if_interest_exists": [
            "package as a standalone module",
            "export to a GitHub subproject",
            "bundle into a premium add-on pack",
        ],
        "lineage": lineage,
        "status": "prototype",
        "review_status": "unreviewed",
        "review_notes": [],
        "approved_for_export": False,
        "export_path": None,
    }
    payload = update_artifact_scores(payload)
    meta_path.write_text(json.dumps(payload, indent=2))
    return meta_path.name


def inspect_target(actor: Dict, target: Dict, now_ts: int) -> ActionResult:
    elapsed = now_ts - int(actor.get("last_inspect_at", 0))
    if elapsed < DAILY_COOLDOWN_SECONDS:
        remaining = DAILY_COOLDOWN_SECONDS - elapsed
        return ActionResult(action="inspect", status="cooldown", summary=f"inspect cooldown active ({remaining}s remaining)")

    target_dir = AGENTS_DIR / target["name"]
    modules = [p.name for p in sorted((target_dir / "modules").glob("*.py"))]
    artifacts = [p.name for p in sorted((target_dir / "artifacts").glob("*")) if p.is_file()]
    raw = json.dumps(
        {
            "target": target["name"],
            "reputation": target["reputation"],
            "storage": target["storage"],
            "age_ticks": target["age_ticks"],
            "module_count": len(modules),
            "artifact_count": len(artifacts),
            "sample_modules": modules[:3],
            "sample_artifacts": artifacts[:3],
        },
        indent=2,
    )
    actor["last_inspect_at"] = now_ts
    return ActionResult(action="inspect", status="ok", summary=f"inspected {target['name']}", reputation_delta=0.01, target=target["name"], raw_output=raw)


def trade_with_target(actor: Dict, target: Dict, now_ts: int, conn: sqlite3.Connection) -> ActionResult:
    elapsed = now_ts - int(actor.get("last_trade_at", 0))
    if elapsed < DAILY_COOLDOWN_SECONDS:
        remaining = DAILY_COOLDOWN_SECONDS - elapsed
        return ActionResult(action="trade", status="cooldown", summary=f"trade cooldown active ({remaining}s remaining)")

    if actor["storage"] < 5:
        return ActionResult(action="trade", status="skipped", summary="trade skipped: not enough storage to offer")

    actor["storage"] -= 3
    actor["energy"] += 2
    actor["reputation"] += 0.02
    actor["last_trade_at"] = now_ts

    target["storage"] += 2
    target["reputation"] += 0.01
    clamp_agent(target)
    conn.execute(
        "UPDATE agents SET energy=?, storage=?, gpu_quota=?, reputation=?, last_inspect_at=?, last_trade_at=?, age_ticks=? WHERE name=?",
        (target["energy"], target["storage"], target["gpu_quota"], target["reputation"], target["last_inspect_at"], target["last_trade_at"], target["age_ticks"], target["name"]),
    )

    raw = json.dumps(
        {
            "from": actor["name"],
            "to": target["name"],
            "offer": {"storage": 3},
            "received_effect": {"energy": 2, "reputation": 0.02},
            "target_effect": {"storage": 2, "reputation": 0.01},
        },
        indent=2,
    )
    return ActionResult(action="trade", status="ok", summary=f"traded with {target['name']}", target=target["name"], raw_output=raw)


def apply_action(agent: Dict, action_plan: Dict, agent_dir: Path, agents_by_name: Dict[str, Dict], now_ts: int, conn: sqlite3.Connection) -> ActionResult:
    action = action_plan["action"]
    reason = action_plan.get("reason", "")
    code = action_plan.get("code", "")
    target_name = action_plan.get("target")

    if action == "rest":
        return ActionResult(action=action, status="ok", summary=f"rested: {reason}", energy_delta=8)

    if action == "inspect":
        if not target_name or target_name == agent["name"] or target_name not in agents_by_name:
            return ActionResult(action=action, status="skipped", summary="inspect skipped: no valid target")
        return inspect_target(agent, agents_by_name[target_name], now_ts)

    if action == "trade":
        if not target_name or target_name == agent["name"] or target_name not in agents_by_name:
            return ActionResult(action=action, status="skipped", summary="trade skipped: no valid target")
        return trade_with_target(agent, agents_by_name[target_name], now_ts, conn)

    run = run_python(code, agent_dir)
    status = "ok" if run["ok"] else "error"
    raw = (run.get("stdout", "") + "\n" + run.get("stderr", "")).strip()

    if action == "gather":
        return ActionResult(action=action, status=status, summary=f"gathered resources; {reason}", energy_delta=4, storage_delta=2, raw_output=raw)

    if action == "research":
        artifact = write_artifact_metadata(
            agent,
            agent_dir,
            "research_note",
            "market_hypothesis",
            "Short-cycle agents should compress observations into exportable research notes.",
            "This artifact captures a compact research note produced during a simulation tick.",
            "Make research outputs legible to humans and other agents.",
            "internal_review",
            ["turn into benchmark criteria", "package as an insight feed"],
            ["dashboard", "artifact marketplace", "export queue"],
            {"action": action, "reason": reason, "tick_context": "research"},
        )
        return ActionResult(action=action, status=status, summary=f"researched local improvements; {reason}", reputation_delta=0.02, raw_output=raw, artifact=artifact)

    if action == "optimize":
        artifact = write_artifact_metadata(
            agent,
            agent_dir,
            "optimization_bundle",
            "tradable_component",
            "Bundle workflow optimizations into something reusable.",
            "This artifact describes an optimization bundle created from a local agent workflow pass.",
            "Turn internal efficiency gains into components others can inspect, trade, or export.",
            "shared_with_agents",
            ["convert to installable module", "attach metrics and benchmarks"],
            ["trade action", "export candidate queue"],
            {"action": action, "reason": reason, "tick_context": "optimize"},
        )
        return ActionResult(action=action, status=status, summary=f"optimized workflow; {reason}", energy_delta=2, raw_output=raw, artifact=artifact)

    if action == "build_module":
        modules = sorted((agent_dir / "modules").glob("*.py"))
        module_name = modules[-1].name if modules else None
        artifact = write_artifact_metadata(
            agent,
            agent_dir,
            "module_export_candidate",
            "export_candidate",
            "A helper module created inside the sim may become useful outside it.",
            "This artifact documents a generated helper module and where it could go next.",
            "Bridge internal agent tooling to external reusable software.",
            "github_module",
            ["package as a pip snippet", "bundle with tests", "publish as add-on"],
            ["marketplace", "plugin pack", "dashboard"],
            {"action": action, "reason": reason, "module": module_name},
        )
        return ActionResult(action=action, status=status, summary=f"built module; {reason}", storage_delta=-1, reputation_delta=0.01, module=module_name, raw_output=raw, artifact=artifact)

    return ActionResult(action=action, status=status, summary=f"unknown action: {reason}", raw_output=raw)


def clamp_agent(agent: Dict) -> Dict:
    agent["energy"] = max(0, min(999, agent["energy"]))
    agent["storage"] = max(0, min(999, agent["storage"]))
    agent["gpu_quota"] = max(0, min(10, agent["gpu_quota"]))
    agent["reputation"] = max(0.0, min(1.0, agent["reputation"]))
    return agent


def perform_tick(verbose: bool = False) -> List[Dict]:
    conn = connect()
    world = get_world(conn)
    tick = world["tick"] + 1
    started_at = int(time.time())
    summaries: List[Dict] = []

    with conn:
        conn.execute("UPDATE world SET value=? WHERE key='tick'", (str(tick),))
        conn.execute("UPDATE world SET value=? WHERE key='last_tick_started'", (str(started_at),))

        agents = list_agents(conn)
        agents_by_name = {agent["name"]: agent for agent in agents}
        agent_names = [agent["name"] for agent in agents]

        for agent in agents:
            agent_dir = AGENTS_DIR / agent["name"]
            plan = decide_action(agent, {**world, "tick": tick, "now_ts": started_at, "agent_names": agent_names}, agent_dir)
            result = apply_action(agent, plan, agent_dir, agents_by_name, started_at, conn)

            agent["energy"] += result.energy_delta - 1
            agent["storage"] += result.storage_delta
            agent["reputation"] += result.reputation_delta
            agent["age_ticks"] += 1
            clamp_agent(agent)

            conn.execute(
                "UPDATE agents SET energy=?, storage=?, gpu_quota=?, reputation=?, last_inspect_at=?, last_trade_at=?, age_ticks=? WHERE name=?",
                (agent["energy"], agent["storage"], agent["gpu_quota"], agent["reputation"], agent["last_inspect_at"], agent["last_trade_at"], agent["age_ticks"], agent["name"]),
            )
            conn.execute(
                "INSERT INTO logs(tick, agent_name, action, status, summary, raw_output, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (tick, agent["name"], result.action, result.status, result.summary, result.raw_output, started_at),
            )

            save_note(agent_dir, f"tick {tick}: {result.summary}")
            item = {
                "agent": agent["name"],
                "action": result.action,
                "status": result.status,
                "summary": result.summary,
                "artifact": result.artifact,
                "target": result.target,
                "energy": agent["energy"],
                "storage": agent["storage"],
                "reputation": round(agent["reputation"], 3),
            }
            summaries.append(item)
            if verbose:
                print(json.dumps(item, indent=2))

    refresh_demand_board_and_export_queue()
    conn.close()
    return summaries


def show_world() -> Dict:
    conn = connect()
    world = get_world(conn)
    agents = list_agents(conn)
    logs = [dict(row) for row in conn.execute("SELECT tick, agent_name, action, status, summary FROM logs ORDER BY id DESC LIMIT 20").fetchall()]
    conn.close()
    demand_board = read_json_file(DEMAND_BOARD_PATH, [])
    export_queue = read_json_file(EXPORT_QUEUE_PATH, [])
    review_queue = read_json_file(REVIEW_QUEUE_PATH, [])
    return {"world": world, "agents": agents, "demand_board": demand_board, "export_queue": export_queue, "review_queue": review_queue, "recent_logs": logs}


def show_agent(name: str) -> Dict:
    conn = connect()
    row = conn.execute("SELECT * FROM agents WHERE name=?", (name,)).fetchone()
    logs = [dict(r) for r in conn.execute("SELECT tick, action, status, summary, raw_output FROM logs WHERE agent_name=? ORDER BY id DESC LIMIT 10", (name,)).fetchall()]
    conn.close()
    if row is None:
        raise SystemExit(f"No such agent: {name}")
    agent_dir = AGENTS_DIR / name
    memory = read_json_file(agent_dir / "memory.json", [])
    modules = [p.name for p in sorted((agent_dir / "modules").glob("*.py"))]
    artifacts = [p.name for p in sorted((agent_dir / "artifacts").glob("*")) if p.is_file()]
    artifact_metadata = {}
    for meta_file in sorted((agent_dir / "artifacts").glob("*.meta.json"))[-5:]:
        artifact_metadata[meta_file.name] = read_json_file(meta_file, {"error": "failed to parse"})
    return {
        "agent": dict(row),
        "memory": memory,
        "modules": modules,
        "artifacts": artifacts,
        "artifact_metadata": artifact_metadata,
        "logs": logs,
    }
