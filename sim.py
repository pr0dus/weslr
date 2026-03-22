from __future__ import annotations

import json
import shutil
import sqlite3
import time
from html import escape
from pathlib import Path
from typing import Dict, List

from agent_runtime import decide_action, load_inbox, load_opportunity_memory, push_inbox_message, save_note, save_opportunity_memory
from config import (
    AGENTS_DIR,
    BASE_DIR,
    CATEGORIES_PATH,
    CATEGORY_PROPOSALS_PATH,
    CATEGORY_PROPOSAL_COST,
    CATEGORY_REJECTION_REPUTATION_PENALTY,
    CODE_TIMEOUT_SECONDS,
    DAILY_COOLDOWN_SECONDS,
    DB_PATH,
    DEFAULT_AGENT_COUNT,
    DASHBOARD_DIR,
    DASHBOARD_HISTORY_PATH,
    EVENT_LOG_PATH,
    OFFERS_DIR,
    DEMAND_BOARD_PATH,
    DORMANT_CATEGORY_MIN_ARTIFACTS,
    EXECUTION_BUDGET_SECONDS,
    EXPORT_QUEUE_PATH,
    EXPORT_READY_THRESHOLD,
    EXPORTS_DIR,
    MAX_CATEGORIES,
    MAX_DEMAND_ITEMS,
    MAX_EXPORT_QUEUE,
    MAX_REVIEW_QUEUE,
    MESSAGES_PATH,
    NEEDS_PATH,
    OPPORTUNITY_BOARD_PATH,
    PACK_OUTCOMES_PATH,
    PROJECTS_PATH,
    PUBLIC_MEMORY_PATH,
    PACKS_PATH,
    RELATIONSHIPS_PATH,
    SELF_MOD_PROPOSALS_PATH,
    WORK_ITEMS_PATH,
    COMMUNICATOR_STATE_PATH,
    EXPERIMENTS_PATH,
    PACK_MIN_RELEASE_ARTIFACTS,
    PACK_RELEASE_CANDIDATE_THRESHOLD,
    PROJECT_NAME,
    PROTECTED_SELF_EDIT_PATHS,
    REVIEW_QUEUE_PATH,
    SELLABILITY_SIGNAL_THRESHOLD,
    HUMAN_SAFETY_RULES,
    STARTING_ENERGY,
    STARTING_GPU,
    STARTING_REPUTATION,
    STARTING_STORAGE,
    TICK_SECONDS,
    VERSION,
)
from models import ActionResult, AgentState, MessageState, NeedState, ProjectState, PublicMemoryState, RelationshipState, SelfModificationProposalState, WorkItemState, CommunicatorState, ExperimentState
from sandbox import run_python

BASE_CATEGORIES = [
    "modules",
    "research",
    "optimization",
    "debugging",
    "memory",
    "exports",
    "benchmarks",
]


WORLD_BOOTSTRAP_PROJECTS = [
    ("project-backup-confidence", "Backup Confidence", "Improve local confidence in backups, restore visibility, and proof of recoverability.", ["agent-1"]),
    ("project-workflow-packaging", "Workflow Packaging", "Turn useful local helper behavior into reusable modules, wrappers, and cleaner handoffs.", ["agent-2"]),
]

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
    age_ticks INTEGER NOT NULL,
    next_due_tick INTEGER NOT NULL DEFAULT 0,
    wake_reason TEXT NOT NULL DEFAULT 'initial',
    cadence_interval INTEGER NOT NULL DEFAULT 1
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
CREATE TABLE IF NOT EXISTS artifact_proof (
    artifact_id TEXT PRIMARY KEY,
    first_seen_tick INTEGER NOT NULL,
    last_seen_tick INTEGER NOT NULL,
    appearances INTEGER NOT NULL,
    top_pack_hits INTEGER NOT NULL,
    review_exports INTEGER NOT NULL,
    human_approvals INTEGER NOT NULL,
    real_usage_hits INTEGER NOT NULL DEFAULT 0,
    buyer_fit_votes INTEGER NOT NULL DEFAULT 0,
    handoff_acceptances INTEGER NOT NULL DEFAULT 0,
    handoff_rejections INTEGER NOT NULL DEFAULT 0,
    external_validation_state TEXT NOT NULL DEFAULT 'unvalidated',
    last_status TEXT NOT NULL
);
'''


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    columns = {row['name'] for row in conn.execute("PRAGMA table_info(agents)").fetchall()}
    if 'next_due_tick' not in columns:
        conn.execute("ALTER TABLE agents ADD COLUMN next_due_tick INTEGER NOT NULL DEFAULT 0")
    if 'wake_reason' not in columns:
        conn.execute("ALTER TABLE agents ADD COLUMN wake_reason TEXT NOT NULL DEFAULT 'initial'")
    if 'cadence_interval' not in columns:
        conn.execute("ALTER TABLE agents ADD COLUMN cadence_interval INTEGER NOT NULL DEFAULT 1")
    return conn


def seed_world_objects(agent_count: int, now_ts: int) -> None:
    project_seeds = []
    for project_id, name, purpose, owners in WORLD_BOOTSTRAP_PROJECTS:
        filtered_owners = [owner for owner in owners if int(owner.split('-')[-1]) <= agent_count]
        if not filtered_owners:
            filtered_owners = ["agent-1"]
        project_seeds.append(ProjectState(project_id, name, purpose, "active", filtered_owners, now_ts, now_ts).to_dict())
    save_projects(project_seeds)

    memory_items = [
        PublicMemoryState(
            "memory-local-first",
            "Local-first inspectability",
            "principle",
            "Prefer inspectable local artifacts, reversible changes, and visible world state over opaque autonomy.",
            "system-bootstrap",
            0.92,
            now_ts,
            now_ts,
        ).to_dict(),
        PublicMemoryState(
            "memory-needs-drive-change",
            "Needs should drive change",
            "principle",
            "Treat repeated friction, unmet coordination, and unexplained failures as first-class world signals.",
            "system-bootstrap",
            0.88,
            now_ts,
            now_ts,
        ).to_dict(),
    ]
    save_public_memory(memory_items)
    save_needs([])
    save_messages([])
    relationships = []
    for i in range(1, agent_count + 1):
        for j in range(1, agent_count + 1):
            if i == j:
                continue
            relationships.append(RelationshipState(
                source_agent=f"agent-{i}",
                target_agent=f"agent-{j}",
                trust=0.5,
                usefulness=0.5,
                friction=0.0,
                last_event="bootstrap",
                updated_at=now_ts,
            ).to_dict())
    save_relationships(relationships)
    save_self_mod_proposals([])
    work_items = []
    for idx, project in enumerate(project_seeds, start=1):
        work_items.append(WorkItemState(
            id=f"work-{idx}",
            title=f"Advance {project['name']}",
            status="open",
            priority=0.6,
            owner=project['owners'][0],
            created_at=now_ts,
            project_id=project['id'],
            need_id="",
            notes=f"Bootstrap work item for {project['name']}",
        ).to_dict())
    save_work_items(work_items)
    save_experiments([])
    save_communicator_state(CommunicatorState(
        name="CircleForge",
        status="alive",
        current_intent="wake, observe, and continue enriching the local world",
        active_pursuit="enrich the local world",
        unresolved_question="what part of the world is still under-understood?",
        curiosity_target="world state and internal signals",
        attraction_bias="understanding, reuse, and coherent coordination",
        avoidance_bias="harmful opacity and reckless action",
        curiosity=0.66,
        dominant_need="",
        last_decision_summary="bootstrap complete",
        intent_history=["wake, observe, and continue enriching the local world"],
        question_history=["what part of the world is still under-understood?"],
        unresolved_objections=[],
        decision_style_memory={},
        last_wake_at=now_ts,
        updated_at=now_ts,
    ).to_dict())


def read_json_file(path: Path, default):
    if not path.exists():
        return default
    try:
        raw = path.read_text().strip()
        if not raw:
            return default
        return json.loads(raw)
    except Exception:
        return default


def write_json_file(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2))
    tmp_path.replace(path)


def load_categories() -> list[str]:
    return read_json_file(CATEGORIES_PATH, BASE_CATEGORIES.copy())


def load_category_proposals() -> list[dict]:
    return read_json_file(CATEGORY_PROPOSALS_PATH, [])


def load_opportunity_board() -> dict:
    default = {
        "themes": {
            "backup confidence": {"pressure": 0.4, "evidence": 0, "updated_at": 0, "acceptances": 0, "rejections": 0, "revisions": 0},
            "service visibility": {"pressure": 0.4, "evidence": 0, "updated_at": 0, "acceptances": 0, "rejections": 0, "revisions": 0},
            "config sanity checks": {"pressure": 0.4, "evidence": 0, "updated_at": 0, "acceptances": 0, "rejections": 0, "revisions": 0},
            "log readability": {"pressure": 0.4, "evidence": 0, "updated_at": 0, "acceptances": 0, "rejections": 0, "revisions": 0},
            "workflow packaging": {"pressure": 0.4, "evidence": 0, "updated_at": 0, "acceptances": 0, "rejections": 0, "revisions": 0},
        }
    }
    board = read_json_file(OPPORTUNITY_BOARD_PATH, default)
    board.setdefault("themes", {})
    for theme, payload in default["themes"].items():
        board["themes"].setdefault(theme, payload.copy())
    return cluster_opportunity_board(board)


def save_opportunity_board(board: dict) -> None:
    write_json_file(OPPORTUNITY_BOARD_PATH, board)


def load_pack_outcomes() -> list[dict]:
    return read_json_file(PACK_OUTCOMES_PATH, [])


def save_pack_outcomes(items: list[dict]) -> None:
    write_json_file(PACK_OUTCOMES_PATH, items)


def load_needs() -> list[dict]:
    return read_json_file(NEEDS_PATH, [])


def save_needs(items: list[dict]) -> None:
    write_json_file(NEEDS_PATH, items)


def load_messages() -> list[dict]:
    return read_json_file(MESSAGES_PATH, [])


def save_messages(items: list[dict]) -> None:
    write_json_file(MESSAGES_PATH, items)


def load_public_memory() -> list[dict]:
    return read_json_file(PUBLIC_MEMORY_PATH, [])


def save_public_memory(items: list[dict]) -> None:
    write_json_file(PUBLIC_MEMORY_PATH, items)


def load_projects() -> list[dict]:
    return read_json_file(PROJECTS_PATH, [])


def save_projects(items: list[dict]) -> None:
    write_json_file(PROJECTS_PATH, items)


def load_relationships() -> list[dict]:
    return read_json_file(RELATIONSHIPS_PATH, [])


def save_relationships(items: list[dict]) -> None:
    write_json_file(RELATIONSHIPS_PATH, items)


def load_self_mod_proposals() -> list[dict]:
    return read_json_file(SELF_MOD_PROPOSALS_PATH, [])


def save_self_mod_proposals(items: list[dict]) -> None:
    write_json_file(SELF_MOD_PROPOSALS_PATH, items)


def load_work_items() -> list[dict]:
    return read_json_file(WORK_ITEMS_PATH, [])


def save_work_items(items: list[dict]) -> None:
    write_json_file(WORK_ITEMS_PATH, items)


def load_communicator_state() -> dict:
    default = CommunicatorState(
        name="CircleForge",
        status="waking",
        current_intent="orient to the world and continue internal thought",
        active_pursuit="world orientation",
        unresolved_question="what in the local world most deserves attention next?",
        curiosity_target="emergent pressure",
        attraction_bias="clarity, coordination, and reusable capability",
        avoidance_bias="harmful opacity and brittle action",
        curiosity=0.62,
        dominant_need="",
        last_decision_summary="none yet",
        intent_history=[],
        question_history=["what in the local world most deserves attention next?"],
        unresolved_objections=[],
        decision_style_memory={},
        last_wake_at=0,
        updated_at=0,
    ).to_dict()
    return read_json_file(COMMUNICATOR_STATE_PATH, default)


def save_communicator_state(payload: dict) -> None:
    write_json_file(COMMUNICATOR_STATE_PATH, payload)


def load_experiments() -> list[dict]:
    return read_json_file(EXPERIMENTS_PATH, [])


def save_experiments(items: list[dict]) -> None:
    write_json_file(EXPERIMENTS_PATH, items)


def protected_self_edit_boundary() -> dict:
    return {
        "protected_paths": PROTECTED_SELF_EDIT_PATHS,
        "human_safety_rules": HUMAN_SAFETY_RULES,
        "full_auto_editing_future_note": "Full auto-editing may be added later, but it must remain bounded by protected core files, visible review, rollback, and human safety constraints.",
    }


def canonical_theme_name(theme: str) -> str:
    theme = (theme or "").strip().lower()
    replacements = {
        "backup trust": "backup confidence",
        "backup validation": "backup confidence",
        "health visibility": "service visibility",
        "service health": "service visibility",
        "config validation": "config sanity checks",
        "configuration sanity": "config sanity checks",
        "readable logs": "log readability",
        "workflow wrappers": "workflow packaging",
        "helper packaging": "workflow packaging",
    }
    return replacements.get(theme, theme)


def cluster_opportunity_board(board: dict) -> dict:
    themes = board.setdefault("themes", {})
    board.setdefault("emergent_candidates", [])
    merged_into: dict[str, list[str]] = {}
    new_themes: dict[str, dict] = {}
    for raw_theme, payload in list(themes.items()):
        canonical = canonical_theme_name(raw_theme)
        canonical_payload = new_themes.setdefault(canonical, {"pressure": 0.0, "evidence": 0, "updated_at": 0, "acceptances": 0, "rejections": 0, "revisions": 0, "aliases": [], "lifecycle": "stable", "split_from": None})
        canonical_payload["pressure"] = round(max(canonical_payload["pressure"], float(payload.get("pressure", 0.0))), 3)
        canonical_payload["evidence"] += int(payload.get("evidence", 0))
        canonical_payload["acceptances"] += int(payload.get("acceptances", 0))
        canonical_payload["rejections"] += int(payload.get("rejections", 0))
        canonical_payload["revisions"] += int(payload.get("revisions", 0))
        canonical_payload["updated_at"] = max(int(canonical_payload.get("updated_at", 0)), int(payload.get("updated_at", 0)))
        canonical_payload["split_from"] = canonical_payload.get("split_from") or payload.get("split_from")
        canonical_payload["lifecycle"] = payload.get("lifecycle", canonical_payload.get("lifecycle", "stable"))
        if raw_theme != canonical:
            canonical_payload["aliases"].append(raw_theme)
            merged_into.setdefault(canonical, []).append(raw_theme)

    now_ts = max([int(v.get("updated_at", 0)) for v in new_themes.values()] + [0])
    for theme, payload in new_themes.items():
        age = max(0, now_ts - int(payload.get("updated_at", 0)))
        if payload.get("pressure", 0.0) < 0.12:
            payload["lifecycle"] = "dormant"
        elif payload.get("rejections", 0) >= 3 and payload.get("acceptances", 0) == 0:
            payload["lifecycle"] = "declining"
        elif payload.get("split_from"):
            payload["lifecycle"] = "emergent"
        elif age > 0 and payload.get("pressure", 0.0) < 0.2:
            payload["lifecycle"] = "cooling"
        else:
            payload["lifecycle"] = payload.get("lifecycle", "stable") or "stable"

    candidates = board.get("emergent_candidates", [])
    promoted = []
    for candidate in candidates:
        if candidate.get("signal_count", 0) >= 3 and candidate.get("confidence", 0.0) >= 0.45:
            theme = canonical_theme_name(candidate["theme"])
            parent_theme = canonical_theme_name(candidate.get("parent_theme") or "") if candidate.get("parent_theme") else None
            if parent_theme and theme == parent_theme:
                existing = new_themes.setdefault(theme, {"pressure": 0.22, "evidence": 0, "updated_at": candidate.get("updated_at", 0), "acceptances": 0, "rejections": 0, "revisions": 0, "aliases": [], "lifecycle": "stable", "split_from": None})
                existing.setdefault("aliases", []).append(candidate["theme"])
                existing["pressure"] = max(existing.get("pressure", 0.0), 0.22)
                promoted.append(candidate)
                continue
            existing = new_themes.setdefault(theme, {"pressure": 0.22, "evidence": 0, "updated_at": candidate.get("updated_at", 0), "acceptances": 0, "rejections": 0, "revisions": 0, "aliases": [], "lifecycle": "emergent", "split_from": candidate.get("parent_theme")})
            existing["pressure"] = max(existing.get("pressure", 0.0), 0.22)
            existing["lifecycle"] = "emergent"
            existing["split_from"] = existing.get("split_from") or candidate.get("parent_theme")
            promoted.append(candidate)
    board["emergent_candidates"] = [c for c in candidates if c not in promoted and c.get("confidence", 0.0) >= 0.12]
    board["themes"] = new_themes
    board["clusters"] = [{"canonical": k, "aliases": v} for k, v in sorted(merged_into.items()) if v]
    return board


def category_action(action: str, name: str) -> dict:
    categories = load_categories()
    proposals = load_category_proposals()

    if action == "approve":
        proposal = next((p for p in proposals if p.get("category") == name and p.get("status") == "pending"), None)
        if proposal is None:
            return {"ok": False, "message": f"No pending proposal for category: {name}"}
        proposal["status"] = "approved"
        if name not in categories and len(categories) < MAX_CATEGORIES:
            categories.append(name)
        write_json_file(CATEGORIES_PATH, categories)
        write_json_file(CATEGORY_PROPOSALS_PATH, proposals)
        refresh_state_files()
        return {"ok": True, "message": f"Approved category: {name}", "categories": categories}

    if action == "reject":
        proposal = next((p for p in proposals if p.get("category") == name and p.get("status") == "pending"), None)
        if proposal is None:
            return {"ok": False, "message": f"No pending proposal for category: {name}"}
        proposal["status"] = "rejected"
        write_json_file(CATEGORY_PROPOSALS_PATH, proposals)
        refresh_state_files()
        return {"ok": True, "message": f"Rejected category proposal: {name}"}

    if action == "retire":
        if name in BASE_CATEGORIES:
            return {"ok": False, "message": f"Cannot retire base category: {name}"}
        if name not in categories:
            return {"ok": False, "message": f"Category not found: {name}"}
        categories = [c for c in categories if c != name]
        write_json_file(CATEGORIES_PATH, categories)
        refresh_state_files()
        return {"ok": True, "message": f"Retired category: {name}", "categories": categories}

    if action == "revive":
        if name in categories:
            return {"ok": False, "message": f"Category already active: {name}"}
        if len(categories) >= MAX_CATEGORIES:
            return {"ok": False, "message": "Cannot revive category: category limit reached"}
        categories.append(name)
        write_json_file(CATEGORIES_PATH, categories)
        refresh_state_files()
        return {"ok": True, "message": f"Revived category: {name}", "categories": categories}

    return {"ok": False, "message": f"Unknown category action: {action}"}


def normalize_category_for_artifact(action: str, category: str | None) -> str:
    if category:
        return category
    mapping = {
        "build_module": "modules",
        "research": "research",
        "optimize": "optimization",
        "inspect": "debugging",
        "trade": "exports",
        "gather": "memory",
    }
    return mapping.get(action, "uncategorized")


def choose_family(action: str, artifact_type: str, category: str) -> str:
    if artifact_type == "export_candidate":
        return "packaging"
    if artifact_type == "market_hypothesis":
        return "evaluation"
    if action == "optimize":
        return "local-ai-ops"
    if action == "inspect":
        return "observability"
    if action == "research":
        return "evaluation"
    if category in {"debugging", "replay", "observability"}:
        return "observability"
    if category in {"exports", "interfaces"}:
        return "status-pages"
    if category in {"modules", "packaging"}:
        return "packaging"
    if category in {"research", "benchmarks", "evaluation"}:
        return "evaluation"
    return "dashboards"


def maybe_generate_category_proposal(agents: list[dict], categories: list[str], proposals: list[dict], now_ts: int) -> tuple[list[dict], list[dict]]:
    if len(categories) >= MAX_CATEGORIES:
        return agents, proposals
    if any(p.get("status") == "pending" for p in proposals):
        return agents, proposals

    candidate_names = [
        "observability",
        "packaging",
        "interfaces",
        "forecasting",
        "market-tools",
        "replay",
        "lineage",
        "automation",
        "orchestration",
        "evaluation",
    ]
    available = [c for c in candidate_names if c not in categories]
    if not available:
        return agents, proposals

    proposer = next((a for a in agents if a["energy"] > CATEGORY_PROPOSAL_COST + 10), None)
    if proposer is None:
        return agents, proposals

    category = available[0]
    proposer["energy"] -= CATEGORY_PROPOSAL_COST
    proposal = {
        "id": f"proposal-{category}-{now_ts}",
        "category": category,
        "reason": f"Agents see repeated need for {category}-related artifacts.",
        "suggested_use": f"Group artifacts related to {category} into a coherent pack.",
        "proposed_by": proposer["name"],
        "votes_for": [proposer["name"]],
        "votes_against": [],
        "status": "pending",
        "created_at": now_ts,
    }
    proposals.append(proposal)
    return agents, proposals


def resolve_category_proposals(agents: list[dict], categories: list[str], proposals: list[dict]) -> tuple[list[dict], list[str], list[dict]]:
    active_count = max(1, len(agents))
    threshold = active_count / 2

    for proposal in proposals:
        if proposal.get("status") != "pending":
            continue
        category = proposal["category"]
        for agent in agents:
            if agent["name"] in proposal["votes_for"] or agent["name"] in proposal["votes_against"]:
                continue
            energy_factor = agent["energy"] > 60
            name_bias = sum(ord(ch) for ch in agent["name"] + category) % 3
            if category in {"observability", "evaluation", "replay", "forecasting"} and energy_factor and name_bias != 0:
                proposal["votes_for"].append(agent["name"])
            elif name_bias == 0:
                proposal["votes_against"].append(agent["name"])
            else:
                proposal["votes_for"].append(agent["name"])

        if len(proposal["votes_for"]) > threshold and len(categories) < MAX_CATEGORIES:
            proposal["status"] = "approved"
            if category not in categories:
                categories.append(category)
        else:
            proposal["status"] = "rejected"
            proposer = next((a for a in agents if a["name"] == proposal.get("proposed_by")), None)
            if proposer is not None:
                proposer["reputation"] = max(0.0, proposer["reputation"] - CATEGORY_REJECTION_REPUTATION_PENALTY)

    return agents, categories, proposals


def compute_quality_dimensions(meta: Dict) -> Dict:
    clarity = 0.25 + (0.25 if meta.get("explanation") else 0.0) + (0.2 if meta.get("purpose") else 0.0) + min(len(meta.get("review_notes", [])) * 0.05, 0.1)
    reusability = 0.2 + min(len(meta.get("combinable_with", [])) * 0.1, 0.3) + (0.2 if meta.get("destination") in {"shared_with_agents", "github_module"} else 0.05)
    novelty = 0.2 + (0.2 if meta.get("artifact_type") == "export_candidate" else 0.08) + (0.15 if meta.get("category") == "uncategorized" else 0.0)
    stability = 0.25 + (0.2 if meta.get("status") in {"prototype", "internal_use", "tradable"} else 0.05) + (0.15 if meta.get("lifecycle_stage") in {"review_proposed", "approved", "export_ready", "packed"} else 0.0)
    exportability = 0.2 + (0.25 if meta.get("destination") in {"github_module", "shared_with_agents"} else 0.05) + min(len(meta.get("future_directions", [])) * 0.06, 0.18)
    market_fit = 0.2 + (0.2 if meta.get("why_now") else 0.0) + (0.15 if meta.get("if_interest_exists") else 0.0) + (0.1 if meta.get("artifact_type") in {"export_candidate", "tradable_component"} else 0.0)
    return {
        "clarity_score": round(min(clarity, 0.99), 3),
        "reusability_score": round(min(reusability, 0.99), 3),
        "novelty_score": round(min(novelty, 0.99), 3),
        "stability_score": round(min(stability, 0.99), 3),
        "exportability_score": round(min(exportability, 0.99), 3),
        "market_fit_score": round(min(market_fit, 0.99), 3),
    }


def compute_internal_score(meta: Dict) -> float:
    q = compute_quality_dimensions(meta)
    return round(min((q["clarity_score"] + q["reusability_score"] + q["stability_score"]) / 3, 0.99), 3)


def artifact_source_path(meta: Dict) -> Path | None:
    explicit = meta.get("artifact_source_path")
    if explicit:
        path = BASE_DIR / str(explicit)
        return path if path.exists() else None
    lineage = meta.get("lineage", {}) or {}
    agent_name = meta.get("agent_name")
    if not agent_name:
        artifact_id = str(meta.get("id", ""))
        if artifact_id.startswith("agent-"):
            parts = artifact_id.split("-")
            if len(parts) >= 2:
                agent_name = "-".join(parts[:2])
    if not agent_name:
        return None
    agent_dir = AGENTS_DIR / str(agent_name)
    action = lineage.get("action")
    if action == "build_module":
        module_name = lineage.get("module")
        if module_name:
            path = agent_dir / "modules" / str(module_name)
            if path.exists():
                return path
        modules = sorted((agent_dir / "modules").glob("*.py"))
        return modules[-1] if modules else None
    if action == "optimize":
        path = agent_dir / "artifacts" / "optimization.txt"
        return path if path.exists() else None
    if action == "research":
        path = agent_dir / "artifacts" / "research.txt"
        return path if path.exists() else None
    return None


def analyze_artifact_substance(meta: Dict) -> Dict:
    path = artifact_source_path(meta)
    result = {
        "artifact_source_path": str(path.relative_to(BASE_DIR)) if path and path.exists() else None,
        "artifact_source_kind": None,
        "artifact_line_count": 0,
        "artifact_nonempty_line_count": 0,
        "artifact_char_count": 0,
        "substance_score": 0.05,
        "thin_artifact_penalty": 0.0,
        "description_mismatch_penalty": 0.0,
        "substance_warnings": [],
    }
    if path is None or not path.exists():
        result["thin_artifact_penalty"] = 0.22
        result["description_mismatch_penalty"] = 0.08
        result["substance_warnings"] = ["missing source artifact"]
        return result

    text = path.read_text(errors='ignore')
    lines = text.splitlines()
    nonempty = [line for line in lines if line.strip()]
    lowered = text.lower()
    suffix = path.suffix.lower()
    result["artifact_source_kind"] = suffix.lstrip('.') or 'text'
    result["artifact_line_count"] = len(lines)
    result["artifact_nonempty_line_count"] = len(nonempty)
    result["artifact_char_count"] = len(text)

    score = 0.08
    warnings = []
    if len(nonempty) >= 3:
        score += 0.08
    if len(nonempty) >= 8:
        score += 0.1
    if len(nonempty) >= 20:
        score += 0.12
    if len(text) >= 80:
        score += 0.06
    if len(text) >= 240:
        score += 0.08

    placeholder_hits = 0
    placeholder_patterns = [
        'def score(x):',
        'return x * 2',
        'observation:',
        'shorter loops waste less time',
        'cache:enabled',
        'checkpointing:on',
    ]
    for pattern in placeholder_patterns:
        if pattern in lowered:
            placeholder_hits += 1
    if placeholder_hits:
        warnings.append('placeholder-like content detected')

    if suffix == '.py':
        if 'def ' in lowered:
            score += 0.08
        if lowered.count('def ') >= 2:
            score += 0.08
        if any(token in lowered for token in ['argparse', '__main__', 'sys.argv', 'input(', 'print(']):
            score += 0.06
        if any(token in lowered for token in ['path(', 'open(', 'json.', 'sqlite', 'subprocess', 'os.']):
            score += 0.08
        if len(nonempty) <= 2:
            warnings.append('very small code artifact')
    else:
        if len(nonempty) >= 2:
            score += 0.04
        if any(token in lowered for token in ['backup', 'restore', 'log', 'config', 'agent', 'tick', 'error', 'export']):
            score += 0.06
        if len(nonempty) <= 1:
            warnings.append('very small text artifact')

    thin_penalty = 0.0
    if len(nonempty) <= 1:
        thin_penalty += 0.26
    elif len(nonempty) <= 2:
        thin_penalty += 0.18
    elif len(nonempty) <= 4:
        thin_penalty += 0.1
    if placeholder_hits >= 2:
        thin_penalty += 0.16
    elif placeholder_hits == 1:
        thin_penalty += 0.08

    description_penalty = 0.0
    ambition_text = ' '.join([
        str(meta.get('idea', '')),
        str(meta.get('purpose', '')),
        str(meta.get('artifact_hypothesis', '')),
        str(meta.get('offer_hypothesis', '')),
        str(meta.get('delivery_mode_guess', '')),
        str(meta.get('destination', '')),
    ]).lower()
    ambitious = any(token in ambition_text for token in ['reusable', 'standalone', 'microproduct', 'github_module', 'package', 'export', 'sell'])
    if ambitious and score < 0.28:
        description_penalty += 0.22
        warnings.append('artifact claims outrun substance')
    elif ambitious and score < 0.4:
        description_penalty += 0.12

    result['substance_score'] = round(max(0.01, min(score, 0.99)), 3)
    result['thin_artifact_penalty'] = round(min(thin_penalty, 0.45), 3)
    result['description_mismatch_penalty'] = round(min(description_penalty, 0.35), 3)
    result['substance_warnings'] = warnings
    return result


def compute_human_proposed_score(meta: Dict) -> float:
    q = compute_quality_dimensions(meta)
    base = (q["clarity_score"] + q["novelty_score"] + q["exportability_score"] + q["market_fit_score"]) / 4
    penalty = float(meta.get("thin_artifact_penalty", 0.0)) + float(meta.get("description_mismatch_penalty", 0.0))
    substance = float(meta.get("substance_score", 0.05))
    ceiling = min(0.99, 0.18 + (substance * 0.95))
    return round(max(0.01, min(base - penalty, ceiling, 0.99)), 3)


def infer_target_user(meta: Dict) -> str:
    if meta.get("target_user"):
        return str(meta.get("target_user"))
    family = meta.get("family")
    category = meta.get("category")
    artifact_type = meta.get("artifact_type")
    if family in {"observability", "status-pages"}:
        return "self-hosters and small operators"
    if family in {"packaging", "evaluation"}:
        return "indie builders and local AI tinkerers"
    if category in {"memory", "research"} or artifact_type == "market_hypothesis":
        return "technical researchers and workflow designers"
    return "technical builders"


def compute_opportunity_signals(meta: Dict) -> Dict:
    niche_theme = str(meta.get("niche_theme", "")).strip()
    target_user = infer_target_user(meta)
    problem_statement = str(meta.get("problem_statement", "")).strip()
    gap_reason = str(meta.get("gap_reason", "")).strip()
    artifact_hypothesis = str(meta.get("artifact_hypothesis", "")).strip()
    offer_hypothesis = str(meta.get("offer_hypothesis", "")).strip()
    delivery_mode_guess = str(meta.get("delivery_mode_guess", meta.get("delivery_mode", "bundle_candidate"))).strip()
    research_confidence = float(meta.get("research_confidence", 0.45) or 0.45)
    proof = meta.get("proof_signals", {})
    family = meta.get("family", "unknown")

    pain_clarity = 0.18
    if len(problem_statement) >= 40:
        pain_clarity += 0.22
    if niche_theme:
        pain_clarity += 0.1
    if meta.get("why_now"):
        pain_clarity += 0.08
    if meta.get("category") != "uncategorized":
        pain_clarity += 0.06

    buyer_specificity = 0.16
    if target_user and target_user not in {"technical builders", "indie builders and local AI tinkerers"}:
        buyer_specificity += 0.22
    elif target_user:
        buyer_specificity += 0.12
    if delivery_mode_guess in {"standalone_microproduct", "consulting_accelerator"}:
        buyer_specificity += 0.08

    gap_severity = 0.18
    if len(gap_reason) >= 40:
        gap_severity += 0.18
    if family in {"observability", "status-pages", "local-ai-ops"}:
        gap_severity += 0.12
    if "heavy" in gap_reason.lower() or "expensive" in gap_reason.lower() or "annoy" in gap_reason.lower():
        gap_severity += 0.08

    packaging_ease = 0.2
    if delivery_mode_guess == "standalone_microproduct":
        packaging_ease += 0.18
    elif delivery_mode_guess == "consulting_accelerator":
        packaging_ease += 0.14
    elif delivery_mode_guess == "bundle_candidate":
        packaging_ease += 0.1
    if artifact_hypothesis:
        packaging_ease += 0.06
    if offer_hypothesis:
        packaging_ease += 0.05

    validation_lift = min(int(proof.get("real_usage_hits", 0)) * 0.08 + int(proof.get("buyer_fit_votes", 0)) * 0.04 + int(proof.get("handoff_acceptances", 0)) * 0.06, 0.2)

    opportunity_score = min(0.99, round((pain_clarity * 0.3) + (buyer_specificity * 0.24) + (gap_severity * 0.2) + (packaging_ease * 0.14) + (research_confidence * 0.08) + validation_lift, 3))

    return {
        "niche_theme": niche_theme or meta.get("category", "uncategorized"),
        "target_user": target_user,
        "problem_statement": problem_statement or meta.get("purpose", ""),
        "gap_reason": gap_reason or meta.get("why_now", ""),
        "artifact_hypothesis": artifact_hypothesis or meta.get("idea", ""),
        "offer_hypothesis": offer_hypothesis or meta.get("explanation", ""),
        "delivery_mode_guess": delivery_mode_guess or "bundle_candidate",
        "research_confidence": round(max(0.01, min(research_confidence, 0.99)), 3),
        "pain_clarity_score": round(min(pain_clarity, 0.99), 3),
        "buyer_specificity_score": round(min(buyer_specificity, 0.99), 3),
        "gap_severity_score": round(min(gap_severity, 0.99), 3),
        "packaging_ease_score": round(min(packaging_ease, 0.99), 3),
        "opportunity_score": opportunity_score,
    }


def get_artifact_proof(conn: sqlite3.Connection | None, artifact_id: str | None) -> Dict:
    default = {
        "first_seen_tick": 0,
        "last_seen_tick": 0,
        "appearances": 0,
        "top_pack_hits": 0,
        "review_exports": 0,
        "human_approvals": 0,
        "real_usage_hits": 0,
        "buyer_fit_votes": 0,
        "handoff_acceptances": 0,
        "handoff_rejections": 0,
        "external_validation_state": "unvalidated",
        "last_status": "unseen",
    }
    if conn is None or not artifact_id:
        return default
    row = conn.execute("SELECT * FROM artifact_proof WHERE artifact_id=?", (artifact_id,)).fetchone()
    return dict(row) if row is not None else default


def compute_sellability_signals(meta: Dict) -> Dict:
    family = meta.get("family", "unknown")
    artifact_type = meta.get("artifact_type", "unknown")
    destination = meta.get("destination", "internal_review")
    review_status = meta.get("review_status", "unreviewed")
    opportunity = compute_opportunity_signals(meta)
    target_user = opportunity.get("target_user")
    proof = meta.get("proof_signals", {})

    buyer_clarity = 0.34
    if family in {"observability", "status-pages", "packaging"}:
        buyer_clarity += 0.18
    if artifact_type == "export_candidate":
        buyer_clarity += 0.08
    if destination in {"github_module", "shared_with_agents"}:
        buyer_clarity += 0.06
    if target_user in {"technical builders", "indie builders and local AI tinkerers"}:
        buyer_clarity -= 0.03
    if meta.get("category") == "uncategorized":
        buyer_clarity -= 0.04

    pain_severity = 0.34
    if family in {"observability", "local-ai-ops", "status-pages"}:
        pain_severity += 0.24
    elif family == "packaging":
        pain_severity += 0.14
    elif family == "evaluation":
        pain_severity += 0.08
    if meta.get("why_now"):
        pain_severity += 0.06

    deployment_effort = 0.62
    if artifact_type == "export_candidate":
        deployment_effort -= 0.1
    if destination == "github_module":
        deployment_effort -= 0.08
    if family == "evaluation":
        deployment_effort += 0.08
    if meta.get("export_path"):
        deployment_effort -= 0.04
    if int(proof.get("appearances", 0)) >= 2:
        deployment_effort -= 0.02

    proof_level = 0.12
    if review_status == "approved":
        proof_level += 0.12
    if review_status == "export_ready":
        proof_level += 0.2
    if meta.get("export_path"):
        proof_level += 0.16
    if meta.get("review_notes"):
        proof_level += min(len(meta.get("review_notes", [])) * 0.03, 0.09)
    if meta.get("lifecycle_stage") == "packed":
        proof_level += 0.05
    proof_level += min(int(proof.get("appearances", 0)) * 0.03, 0.09)
    proof_level += min(int(proof.get("top_pack_hits", 0)) * 0.04, 0.12)
    proof_level += min(int(proof.get("review_exports", 0)) * 0.06, 0.12)
    proof_level += min(int(proof.get("human_approvals", 0)) * 0.06, 0.12)
    proof_level += min(int(proof.get("real_usage_hits", 0)) * 0.08, 0.16)
    proof_level += min(int(proof.get("handoff_acceptances", 0)) * 0.08, 0.16)
    proof_level -= min(int(proof.get("handoff_rejections", 0)) * 0.05, 0.15)

    support_burden = 0.56
    if family in {"packaging", "evaluation"}:
        support_burden -= 0.08
    if family in {"status-pages", "observability", "local-ai-ops"}:
        support_burden += 0.1
    if destination == "github_module":
        support_burden -= 0.04
    if int(proof.get("human_approvals", 0)) >= 1:
        support_burden -= 0.03
    if int(proof.get("handoff_acceptances", 0)) >= 1:
        support_burden -= 0.04
    if int(proof.get("handoff_rejections", 0)) >= 1:
        support_burden += 0.05

    external_state = proof.get("external_validation_state", "unvalidated")
    validation_bonus = 0.0
    if external_state == "validated":
        validation_bonus = 0.08
    elif external_state == "accepted_for_delivery":
        validation_bonus = 0.14
    elif external_state == "rejected_after_review":
        validation_bonus = -0.1
    elif external_state == "needs_revision":
        validation_bonus = -0.04

    opportunity_score = float(opportunity.get("opportunity_score", 0.0))
    penalty = float(meta.get("thin_artifact_penalty", 0.0)) + float(meta.get("description_mismatch_penalty", 0.0))
    substance = float(meta.get("substance_score", 0.05))
    commercial_readiness = min(0.99, round((meta.get("human_proposed_score", 0.0) * 0.16) + (proof_level * 0.3) + (buyer_clarity * 0.12) + (pain_severity * 0.1) + ((1 - deployment_effort) * 0.08) + (opportunity_score * 0.16) + validation_bonus, 3))
    sellability_score = min(0.99, round((buyer_clarity * 0.18) + (pain_severity * 0.16) + ((1 - deployment_effort) * 0.1) + (proof_level * 0.18) + ((1 - support_burden) * 0.05) + (commercial_readiness * 0.13) + (opportunity_score * 0.16) + validation_bonus, 3))
    commercial_readiness = max(0.01, round(min(commercial_readiness - (penalty * 0.7), 0.16 + (substance * 0.82), 0.99), 3))
    sellability_score = max(0.01, round(min(sellability_score - (penalty * 0.82), 0.14 + (substance * 0.78), 0.99), 3))

    if sellability_score >= 0.82 and proof_level >= 0.5:
        price_band_guess = "250-1000eur"
    elif sellability_score >= 0.72 and proof_level >= 0.38:
        price_band_guess = "100-500eur"
    elif sellability_score >= 0.62 and proof_level >= 0.25:
        price_band_guess = "50-200eur"
    elif sellability_score >= 0.52:
        price_band_guess = "20-100eur"
    else:
        price_band_guess = "needs packaging"

    return {
        "target_user": target_user,
        "buyer_clarity_score": round(max(0.01, min(buyer_clarity, 0.99)), 3),
        "pain_severity_score": round(max(0.01, min(pain_severity, 0.99)), 3),
        "deployment_effort_score": round(max(0.01, min(deployment_effort, 0.99)), 3),
        "proof_level_score": round(max(0.01, min(proof_level, 0.99)), 3),
        "support_burden_score": round(max(0.01, min(support_burden, 0.99)), 3),
        "commercial_readiness_score": commercial_readiness,
        "sellability_score": sellability_score,
        "price_band_guess": price_band_guess,
        "proof_signals": proof,
    }


def update_artifact_scores(meta: Dict, conn: sqlite3.Connection | None = None) -> Dict:
    meta["proof_signals"] = get_artifact_proof(conn, meta.get("id"))
    meta.update(analyze_artifact_substance(meta))
    meta.update(compute_quality_dimensions(meta))
    meta["internal_score"] = compute_internal_score(meta)
    meta["human_proposed_score"] = compute_human_proposed_score(meta)
    meta.update(compute_opportunity_signals(meta))
    meta.update(compute_sellability_signals(meta))
    meta["external_validation_state"] = meta.get("proof_signals", {}).get("external_validation_state", "unvalidated")
    meta["delivery_mode"] = recommend_delivery_mode(meta)
    return meta


def build_artifact_explainability(meta: Dict) -> dict:
    proof = meta.get("proof_signals", {})
    internal_strength = []
    external_proof = []
    risks = []
    next_actions = []
    if float(meta.get("human_proposed_score", 0.0)) >= 0.65:
        internal_strength.append(f"human-facing quality {meta.get('human_proposed_score')}")
    if float(meta.get("internal_score", 0.0)) >= 0.65:
        internal_strength.append(f"internal quality {meta.get('internal_score')}")
    if float(meta.get("opportunity_score", 0.0)) >= 0.65:
        internal_strength.append(f"opportunity fit {meta.get('opportunity_score')}")
    if int(proof.get("human_approvals", 0)) >= 1:
        external_proof.append("human approval recorded")
    if int(proof.get("real_usage_hits", 0)) >= 1:
        external_proof.append("real usage recorded")
    if int(proof.get("handoff_acceptances", 0)) >= 1:
        external_proof.append("handoff acceptance recorded")
    if not external_proof:
        risks.append("strong internal score but weak external proof")
        next_actions.append("run validate/use or validate/accept on a real artifact trial")
    if proof.get("external_validation_state") == "rejected_after_review":
        risks.append("artifact was rejected after external review")
        next_actions.append("tighten buyer framing and revise before re-offering")
    if float(meta.get("deployment_effort_score", 0.0)) > 0.6:
        risks.append("deployment effort looks relatively high")
    if float(meta.get("buyer_clarity_score", 0.0)) < 0.55:
        next_actions.append("clarify target buyer and problem statement")
    if float(meta.get("thin_artifact_penalty", 0.0)) > 0.0:
        risks.append("artifact substance looks thin relative to its framing")
        next_actions.append("strengthen the underlying artifact before promoting it")
    if float(meta.get("description_mismatch_penalty", 0.0)) > 0.0:
        risks.append("description appears stronger than the current artifact payload")
    return {
        "internal_strength": internal_strength or ["early artifact with partial internal signals"],
        "external_proof": external_proof or ["no durable external proof yet"],
        "risks": risks or ["no major explainability risks flagged"],
        "next_actions": next_actions or ["continue validation and packaging work"],
    }


def pack_offer_readiness(pack: Dict) -> dict:
    proof = (float(pack.get("accept_count", 0)) * 0.45) + (float(pack.get("offer_count", 0)) * 0.15) + (float(pack.get("test_count", 0)) * 0.1) + (float(pack.get("export_count", 0)) * 0.15) - (float(pack.get("reject_count", 0)) * 0.18) - (float(pack.get("revision_count", 0)) * 0.08)
    score = max(0.0, min(0.99, round((float(pack.get("sellability_score", 0.0)) * 0.5) + (float(pack.get("commercial_readiness_score", 0.0)) * 0.25) + proof, 3)))
    gaps = []
    if int(pack.get("offer_count", 0)) == 0:
        gaps.append("no offer attempts recorded")
    if int(pack.get("accept_count", 0)) == 0:
        gaps.append("no acceptance evidence yet")
    if float(pack.get("sellability_score", 0.0)) >= 0.7 and int(pack.get("accept_count", 0)) == 0 and int(pack.get("test_count", 0)) == 0:
        gaps.append("high promise but weak external proof")
    return {"offer_readiness_score": score, "gaps": gaps or ["no major offer blockers flagged"]}


def build_weak_proof_pack_report(artifact_packs: list[dict]) -> list[dict]:
    result = []
    for pack in artifact_packs:
        readiness = pack_offer_readiness(pack)
        if float(pack.get("sellability_score", 0.0)) >= 0.68 and (int(pack.get("accept_count", 0)) + int(pack.get("test_count", 0))) == 0:
            result.append({
                "pack_name": pack.get("pack_name"),
                "sellability_score": pack.get("sellability_score"),
                "commercial_readiness_score": pack.get("commercial_readiness_score"),
                "offer_readiness_score": readiness.get("offer_readiness_score"),
                "gaps": readiness.get("gaps", []),
            })
    return result[:8]


def prepare_pack_offer(pack_name: str, note: str = "", buyer: str = "", price_band: str = "", mode: str = "") -> dict:
    packs = read_json_file(PACKS_PATH, [])
    pack = next((p for p in packs if p.get("pack_name") == pack_name), None)
    if pack is None:
        raise SystemExit(f"No pack found: {pack_name}")
    pack.update(summarize_pack_outcomes(pack_name))
    readiness = pack_offer_readiness(pack)
    now_ts = int(time.time())
    buyer = buyer or pack.get("niche_theme") or pack.get("category") or "target operator"
    price_band = price_band or pack.get("price_band_guess") or "tbd"
    mode = mode or pack.get("delivery_mode") or "bundle_candidate"
    OFFERS_DIR.mkdir(parents=True, exist_ok=True)
    offer_dir = OFFERS_DIR / pack_name
    offer_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": now_ts,
        "pack_name": pack_name,
        "buyer": buyer,
        "price_band": price_band,
        "mode": mode,
        "note": note,
        "summary": pack.get("summary"),
        "why_promising": pack.get("why_promising", []),
        "offer_readiness": readiness,
        "artifacts": [{"id": a.get("id"), "title": a.get("title"), "target_user": a.get("target_user"), "price_band_guess": a.get("price_band_guess")} for a in pack.get("artifacts", [])],
        "next_steps": [
            "review buyer/problem framing",
            "run a real outreach or internal pilot",
            "record outcome with the pack command",
        ],
    }
    write_json_file(offer_dir / "latest_offer.json", payload)
    (offer_dir / "README.md").write_text("\n".join([
        f"# Offer brief for {pack_name}",
        "",
        f"Buyer: {buyer}",
        f"Price band: {price_band}",
        f"Mode: {mode}",
        f"Offer readiness: {readiness.get('offer_readiness_score')}",
        "",
        "## Why this pack",
        *[f"- {line}" for line in pack.get("why_promising", [])],
        "",
        "## Gaps",
        *[f"- {line}" for line in readiness.get("gaps", [])],
        "",
        "## Suggested next step",
        f"python3 main.py pack {pack_name} offer --buyer '{buyer}' --price-band '{price_band}' --mode '{mode}' --note 'first outreach'",
    ]) + "\n")
    return {"ok": True, "offer_dir": str(offer_dir.relative_to(BASE_DIR)), "offer": payload}


def explain_artifact(meta: Dict) -> list[str]:
    reasons = []
    if meta.get("review_status") == "export_ready":
        reasons.append("artifact is export-ready and already passed into human-facing flow")
    if float(meta.get("sellability_score", 0.0)) >= SELLABILITY_SIGNAL_THRESHOLD:
        reasons.append(f"sellability score is strong at {meta.get('sellability_score')}")
    if float(meta.get("opportunity_score", 0.0)) >= 0.65:
        reasons.append(f"opportunity score suggests a credible niche at {meta.get('opportunity_score')}")
    if meta.get("niche_theme"):
        reasons.append(f"artifact is tied to the niche theme '{meta.get('niche_theme')}'")
    if float(meta.get("buyer_clarity_score", 0.0)) >= 0.75:
        reasons.append("target buyer is relatively clear")
    if float(meta.get("deployment_effort_score", 0.0)) <= 0.4:
        reasons.append("deployment effort looks relatively low")
    if float(meta.get("human_proposed_score", 0.0)) >= 0.65:
        reasons.append("human-facing quality score is above review threshold")
    proof = meta.get("proof_signals", {})
    if int(proof.get("appearances", 0)) >= 2:
        reasons.append("artifact has persisted across multiple state refreshes")
    if int(proof.get("top_pack_hits", 0)) >= 1:
        reasons.append("artifact has appeared inside a top-ranked pack")
    if int(proof.get("human_approvals", 0)) >= 1:
        reasons.append("artifact has direct human approval evidence")
    if int(proof.get("real_usage_hits", 0)) >= 1:
        reasons.append("artifact has real usage evidence outside the internal scoring loop")
    if int(proof.get("handoff_acceptances", 0)) >= 1:
        reasons.append("artifact has a positive delivery or handoff outcome")
    if proof.get("external_validation_state") == "rejected_after_review":
        reasons.append("artifact has external rejection evidence and needs rework")
    if meta.get("family"):
        reasons.append(f"artifact fits the {meta.get('family')} family")
    return reasons[:5] or ["early artifact with limited explanation signals so far"]


def summarize_pack(pack: Dict) -> str:
    scope = pack.get("niche_theme") or pack.get("category") or pack.get("group_key") or "mixed"
    return f"rank #{pack.get('rank', '?')} · {scope} · score {pack.get('pack_score', 0.0)} · sellability {pack.get('sellability_score', 0.0)} · stage {pack.get('lifecycle_stage', 'draft')}"


def recommend_delivery_mode(meta: Dict) -> str:
    family = meta.get("family", "unknown")
    sellability = float(meta.get("sellability_score", 0.0))
    proof = float(meta.get("proof_level_score", 0.0))
    if sellability >= 0.72 and proof >= 0.38 and family in {"observability", "status-pages"}:
        return "standalone_microproduct"
    if family in {"packaging", "local-ai-ops"} and sellability >= 0.58:
        return "consulting_accelerator"
    if family == "evaluation":
        return "internal_reusable_component"
    return "bundle_candidate"


def family_template(pack_or_meta: Dict) -> Dict:
    family = pack_or_meta.get("family")
    category = pack_or_meta.get("category")
    if family == "observability" or category == "observability":
        return {
            "headline": "Lightweight observability starter pack for self-hosters",
            "buyer_problem": "Small operators need simple visibility without full enterprise tooling.",
            "install_steps": ["review included scripts/modules", "set target service names", "run locally or on a small VPS"],
            "delivery_checklist": ["confirm monitored service list", "add example screenshots/output", "document alert or status workflow"],
        }
    if family == "status-pages" or category in {"exports", "interfaces"}:
        return {
            "headline": "Simple status-page starter bundle",
            "buyer_problem": "Small projects need a basic public or internal status view without overbuilding.",
            "install_steps": ["adapt branding and endpoints", "connect service checks", "publish static or lightweight app output"],
            "delivery_checklist": ["set service labels", "document deployment target", "include sample maintenance update flow"],
        }
    if family == "packaging":
        return {
            "headline": "Reusable helper-module bundle for local AI builders",
            "buyer_problem": "Builders need small reusable modules faster than they can handcraft them each time.",
            "install_steps": ["review exported module", "rename/package for target project", "add tests or example usage"],
            "delivery_checklist": ["add usage example", "document assumptions", "bundle with test snippet"],
        }
    if family == "local-ai-ops":
        return {
            "headline": "Local AI workflow acceleration bundle",
            "buyer_problem": "Small AI builders need practical workflow speedups without heavy infra work.",
            "install_steps": ["review optimization notes", "adapt to local stack", "measure improvement after integration"],
            "delivery_checklist": ["state expected speedup", "document environment assumptions", "include rollback note"],
        }
    return {
        "headline": "Curated reusable artifact bundle",
        "buyer_problem": "Builders want a smaller head start instead of starting from a blank page.",
        "install_steps": ["review included outputs", "adapt to project context", "tighten docs before shipping"],
        "delivery_checklist": ["clarify target user", "add usage example", "document next packaging step"],
    }


def build_export_payload(meta: Dict, meta_file: Path) -> Dict:
    return {
        "project": PROJECT_NAME,
        "version": VERSION,
        "title": meta.get("title"),
        "artifact_type": meta.get("artifact_type"),
        "category": meta.get("category"),
        "family": meta.get("family"),
        "lifecycle_stage": meta.get("lifecycle_stage"),
        "idea": meta.get("idea"),
        "explanation": meta.get("explanation"),
        "purpose": meta.get("purpose"),
        "destination": meta.get("destination"),
        "future_directions": meta.get("future_directions", []),
        "niche_theme": meta.get("niche_theme"),
        "target_user": meta.get("target_user"),
        "problem_statement": meta.get("problem_statement"),
        "gap_reason": meta.get("gap_reason"),
        "artifact_hypothesis": meta.get("artifact_hypothesis"),
        "offer_hypothesis": meta.get("offer_hypothesis"),
        "opportunity_score": meta.get("opportunity_score"),
        "research_confidence": meta.get("research_confidence"),
        "parent_ids": meta.get("parent_ids", []),
        "derived_from": meta.get("derived_from", []),
        "generation": meta.get("generation"),
        "clarity_score": meta.get("clarity_score"),
        "reusability_score": meta.get("reusability_score"),
        "novelty_score": meta.get("novelty_score"),
        "stability_score": meta.get("stability_score"),
        "exportability_score": meta.get("exportability_score"),
        "market_fit_score": meta.get("market_fit_score"),
        "internal_score": meta.get("internal_score"),
        "human_proposed_score": meta.get("human_proposed_score"),
        "target_user": meta.get("target_user"),
        "buyer_clarity_score": meta.get("buyer_clarity_score"),
        "pain_severity_score": meta.get("pain_severity_score"),
        "deployment_effort_score": meta.get("deployment_effort_score"),
        "proof_level_score": meta.get("proof_level_score"),
        "support_burden_score": meta.get("support_burden_score"),
        "commercial_readiness_score": meta.get("commercial_readiness_score"),
        "sellability_score": meta.get("sellability_score"),
        "price_band_guess": meta.get("price_band_guess"),
        "delivery_mode": meta.get("delivery_mode"),
        "review_status": meta.get("review_status"),
        "review_notes": meta.get("review_notes", []),
        "source_meta": str(meta_file.relative_to(BASE_DIR)),
    }


def write_export_snapshot(meta: Dict, meta_file: Path) -> str:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    export_dir = EXPORTS_DIR / f"{meta.get('id', meta_file.stem)}"
    export_dir.mkdir(parents=True, exist_ok=True)

    payload = build_export_payload(meta, meta_file)
    write_json_file(export_dir / 'manifest.json', payload)

    readme = [
        f"# {payload.get('title', 'Export Artifact')}",
        "",
        f"Artifact type: {payload.get('artifact_type')}",
        f"Category: {payload.get('category')}",
        f"Family: {payload.get('family')}",
        f"Lifecycle: {payload.get('lifecycle_stage')}",
        f"Target user: {payload.get('target_user', 'tbd')}",
        f"Price band guess: {payload.get('price_band_guess', 'tbd')}",
        "",
        "## Summary",
        payload.get('explanation', ''),
        "",
        "## Purpose",
        payload.get('purpose', ''),
        "",
        "## Commercial view",
        f"- Buyer clarity: {payload.get('buyer_clarity_score')}",
        f"- Commercial readiness: {payload.get('commercial_readiness_score')}",
        f"- Sellability: {payload.get('sellability_score')}",
        "",
        "## Future directions",
    ]
    for item in payload.get('future_directions', []):
        readme.append(f"- {item}")
    if not payload.get('future_directions'):
        readme.append("- none yet")
    (export_dir / 'README.md').write_text("\n".join(readme) + "\n")

    notes = [
        f"review_status: {payload.get('review_status')}",
        f"internal_score: {payload.get('internal_score')}",
        f"human_proposed_score: {payload.get('human_proposed_score')}",
        f"commercial_readiness_score: {payload.get('commercial_readiness_score')}",
        f"sellability_score: {payload.get('sellability_score')}",
        "review_notes:",
    ]
    for note in payload.get('review_notes', []):
        notes.append(f"- {note}")
    if not payload.get('review_notes'):
        notes.append("- none")
    (export_dir / 'notes.md').write_text("\n".join(notes) + "\n")

    template = family_template(meta)
    handoff = {
        "title": payload.get("title"),
        "target_user": payload.get("target_user"),
        "problem": payload.get("purpose"),
        "why_now": payload.get("idea"),
        "offer_shape": payload.get("artifact_type"),
        "price_band_guess": payload.get("price_band_guess"),
        "delivery_mode": payload.get("delivery_mode"),
        "template_headline": template.get("headline"),
        "buyer_problem": template.get("buyer_problem"),
        "install_steps": template.get("install_steps", []),
        "delivery_checklist": template.get("delivery_checklist", []),
        "delivery_notes": payload.get("future_directions", []),
        "export_path": str(export_dir.relative_to(BASE_DIR)),
    }
    write_json_file(export_dir / 'handoff.json', handoff)

    return str(export_dir.relative_to(BASE_DIR))


def maybe_promote_for_review(meta: Dict, meta_file: Path) -> Dict:
    review_status = meta.get("review_status", "unreviewed")
    meta.setdefault("review_notes", [])
    meta.setdefault("approved_for_export", False)
    meta.setdefault("export_path", None)

    if meta.get("human_proposed_score", 0.0) >= 0.65 and review_status == "unreviewed":
        meta["review_status"] = "proposed"
        meta["lifecycle_stage"] = "review_proposed"
        note = "Auto-proposed for human review based on score threshold."
        if note not in meta["review_notes"]:
            meta["review_notes"].append(note)

    if meta.get("human_proposed_score", 0.0) >= EXPORT_READY_THRESHOLD and meta.get("review_status") in {"proposed", "approved", "export_ready"}:
        meta["review_status"] = "export_ready"
        meta["lifecycle_stage"] = "export_ready"
        meta["approved_for_export"] = True
        meta["export_path"] = write_export_snapshot(meta, meta_file)
        note = "Auto-promoted to export_ready by score threshold."
        if note not in meta["review_notes"]:
            meta["review_notes"].append(note)

    return meta


def find_meta_file_by_id(artifact_id: str) -> Path | None:
    for meta_file in AGENTS_DIR.glob("*/artifacts/*.meta.json"):
        meta = read_json_file(meta_file, None)
        if isinstance(meta, dict) and meta.get("id") == artifact_id:
            return meta_file
    return None


def validate_artifact(artifact_id: str, action: str, note: str = "") -> Dict:
    meta_file = find_meta_file_by_id(artifact_id)
    if meta_file is None:
        raise SystemExit(f"No artifact found with id: {artifact_id}")
    conn = connect()
    meta = read_json_file(meta_file, {})
    proof = get_artifact_proof(conn, meta.get("id"))

    if action == "use":
        proof["real_usage_hits"] = int(proof.get("real_usage_hits", 0)) + 1
        proof["external_validation_state"] = "validated"
    elif action == "buyer-fit":
        proof["buyer_fit_votes"] = int(proof.get("buyer_fit_votes", 0)) + 1
        proof["external_validation_state"] = "validated"
    elif action == "accept":
        proof["handoff_acceptances"] = int(proof.get("handoff_acceptances", 0)) + 1
        proof["external_validation_state"] = "accepted_for_delivery"
    elif action == "reject":
        proof["handoff_rejections"] = int(proof.get("handoff_rejections", 0)) + 1
        proof["external_validation_state"] = "rejected_after_review"
    elif action == "revise":
        proof["external_validation_state"] = "needs_revision"
    else:
        conn.close()
        raise SystemExit(f"Unknown validation action: {action}")

    if note:
        meta.setdefault("review_notes", []).append(f"validation:{action}: {note}")

    theme = meta.get("niche_theme")
    outcome = {
        "use": "use",
        "buyer-fit": "buyer-fit",
        "accept": "accept",
        "reject": "reject",
        "revise": "needs_revision",
    }[action]
    apply_opportunity_outcome(theme, outcome, int(time.time()))

    proof["last_status"] = meta.get("review_status", "unreviewed")
    conn.execute("INSERT OR REPLACE INTO artifact_proof(artifact_id, first_seen_tick, last_seen_tick, appearances, top_pack_hits, review_exports, human_approvals, real_usage_hits, buyer_fit_votes, handoff_acceptances, handoff_rejections, external_validation_state, last_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
        meta.get("id"),
        int(proof.get("first_seen_tick", 0)),
        int(proof.get("last_seen_tick", 0)),
        int(proof.get("appearances", 0)),
        int(proof.get("top_pack_hits", 0)),
        int(proof.get("review_exports", 0)),
        int(proof.get("human_approvals", 0)),
        int(proof.get("real_usage_hits", 0)),
        int(proof.get("buyer_fit_votes", 0)),
        int(proof.get("handoff_acceptances", 0)),
        int(proof.get("handoff_rejections", 0)),
        proof.get("external_validation_state", "unvalidated"),
        proof.get("last_status", "unreviewed"),
    ))
    conn.commit()
    meta = update_artifact_scores(meta, conn)
    write_json_file(meta_file, meta)
    refresh_state_files(conn)
    conn.close()
    return meta


def review_artifact(artifact_id: str, action: str, note: str = "") -> Dict:
    meta_file = find_meta_file_by_id(artifact_id)
    if meta_file is None:
        raise SystemExit(f"No artifact found with id: {artifact_id}")
    conn = connect()
    meta = read_json_file(meta_file, {})
    meta = update_artifact_scores(meta, conn)
    meta.setdefault("review_notes", [])
    meta.setdefault("approved_for_export", False)
    meta.setdefault("export_path", None)
    if action == "approve":
        meta["review_status"] = "approved"
        meta["lifecycle_stage"] = "approved"
        meta["approved_for_export"] = True
        if note:
            meta["review_notes"].append(note)
    elif action == "reject":
        meta["review_status"] = "rejected"
        meta["lifecycle_stage"] = "archived"
        meta["approved_for_export"] = False
        meta["export_path"] = None
        if note:
            meta["review_notes"].append(note)
    elif action == "note":
        if note:
            meta["review_notes"].append(note)
        if meta.get("review_status") == "unreviewed":
            meta["review_status"] = "proposed"
            meta["lifecycle_stage"] = "review_proposed"
    elif action == "export":
        meta["review_status"] = "export_ready"
        meta["lifecycle_stage"] = "packed"
        meta["approved_for_export"] = True
        if note:
            meta["review_notes"].append(note)
        meta["export_path"] = write_export_snapshot(meta, meta_file)
    proof = get_artifact_proof(conn, meta.get("id"))
    if action == "approve":
        proof["human_approvals"] = int(proof.get("human_approvals", 0)) + 1
        apply_opportunity_outcome(meta.get("niche_theme"), "approve", int(time.time()))
    if action == "export":
        proof["review_exports"] = int(proof.get("review_exports", 0)) + 1
        apply_opportunity_outcome(meta.get("niche_theme"), "export", int(time.time()))
    if action == "reject":
        apply_opportunity_outcome(meta.get("niche_theme"), "reject", int(time.time()))
    if action in {"approve", "export"} and meta.get("human_proposed_score", 0.0) >= EXPORT_READY_THRESHOLD:
        meta["review_status"] = "export_ready"
        meta["lifecycle_stage"] = "packed"
        meta["export_path"] = write_export_snapshot(meta, meta_file)
    proof["last_status"] = meta.get("review_status", "unreviewed")
    conn.execute("INSERT OR REPLACE INTO artifact_proof(artifact_id, first_seen_tick, last_seen_tick, appearances, top_pack_hits, review_exports, human_approvals, real_usage_hits, buyer_fit_votes, handoff_acceptances, handoff_rejections, external_validation_state, last_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
        meta.get("id"),
        int(proof.get("first_seen_tick", 0)),
        int(proof.get("last_seen_tick", 0)),
        int(proof.get("appearances", 0)),
        int(proof.get("top_pack_hits", 0)),
        int(proof.get("review_exports", 0)),
        int(proof.get("human_approvals", 0)),
        int(proof.get("real_usage_hits", 0)),
        int(proof.get("buyer_fit_votes", 0)),
        int(proof.get("handoff_acceptances", 0)),
        int(proof.get("handoff_rejections", 0)),
        proof.get("external_validation_state", "unvalidated"),
        proof.get("last_status", "unreviewed"),
    ))
    meta = update_artifact_scores(meta, conn)
    write_json_file(meta_file, meta)
    refresh_state_files(conn)
    conn.close()
    return meta


def summarize_pack_outcomes(pack_name: str) -> dict:
    events = [e for e in load_pack_outcomes() if e.get("pack_name") == pack_name]
    return {
        "offer_count": sum(1 for e in events if e.get("action") == "offer"),
        "accept_count": sum(1 for e in events if e.get("action") == "accept"),
        "reject_count": sum(1 for e in events if e.get("action") == "reject"),
        "revision_count": sum(1 for e in events if e.get("action") == "revise"),
        "test_count": sum(1 for e in events if e.get("action") == "test"),
        "export_count": sum(1 for e in events if e.get("action") == "export"),
        "recent_events": events[-5:],
    }


def compute_pack_scores(items: list[dict]) -> dict:
    count = len(items)
    if count == 0:
        return {
            "pack_score": 0.0,
            "coherence_score": 0.0,
            "readiness_score": 0.0,
            "novelty_score": 0.0,
            "coverage_score": 0.0,
            "lineage_score": 0.0,
            "artifact_count": 0,
            "release_candidate": False,
            "lifecycle_stage": "draft",
            "why_promising": [],
        }

    avg_human = sum(float(item.get("human_proposed_score", 0.0)) for item in items) / count
    avg_internal = sum(float(item.get("internal_score", 0.0)) for item in items) / count
    avg_novelty = sum(float(item.get("novelty_score", 0.0)) for item in items) / count
    avg_sellability = sum(float(item.get("sellability_score", 0.0)) for item in items) / count
    avg_buyer_clarity = sum(float(item.get("buyer_clarity_score", 0.0)) for item in items) / count
    families = [item.get("family", "unknown") for item in items]
    family_diversity = len(set(families))
    dominant_family_share = max(families.count(f) for f in set(families)) / count if families else 0.0
    coherence_score = min(0.99, round((dominant_family_share * 0.65) + (min(avg_internal, 0.99) * 0.35), 3))
    readiness_score = min(0.99, round((sum(1 for item in items if item.get("review_status") == "export_ready") / count) * 0.65 + avg_human * 0.35, 3))
    novelty_score = round(min(avg_novelty, 0.99), 3)
    coverage_score = min(0.99, round(min(count / 4, 1.0) * 0.7 + min(family_diversity / 3, 1.0) * 0.3, 3))
    lineage_depths = [int(item.get("generation", 1) or 1) for item in items]
    lineage_score = min(0.99, round(min(sum(lineage_depths) / count / 3, 1.0), 3))
    avg_proof = sum(float(item.get("proof_level_score", 0.0)) for item in items) / count
    avg_support_burden = sum(float(item.get("support_burden_score", 0.0)) for item in items) / count
    commercial_readiness_score = min(0.99, round((avg_sellability * 0.34) + (avg_buyer_clarity * 0.2) + (readiness_score * 0.18) + (avg_proof * 0.18) + ((1 - avg_support_burden) * 0.1), 3))
    pack_score = min(0.99, round((avg_human * 0.24) + (avg_internal * 0.15) + (coherence_score * 0.18) + (readiness_score * 0.12) + (coverage_score * 0.06) + (lineage_score * 0.03) + (avg_sellability * 0.14) + (avg_proof * 0.08), 3))

    if avg_sellability >= 0.84 and avg_proof >= 0.5 and count >= 3:
        price_band_guess = "500-1500eur"
    elif avg_sellability >= 0.75 and avg_proof >= 0.38 and count >= 2:
        price_band_guess = "150-600eur"
    elif avg_sellability >= 0.64 and avg_proof >= 0.24:
        price_band_guess = "50-250eur"
    else:
        price_band_guess = "needs packaging"

    release_candidate = count >= PACK_MIN_RELEASE_ARTIFACTS and readiness_score >= 0.75 and coherence_score >= 0.72 and pack_score >= PACK_RELEASE_CANDIDATE_THRESHOLD and avg_proof >= 0.32
    lifecycle_stage = "release_candidate" if release_candidate else ("reviewed" if count >= 2 and pack_score >= 0.68 else "coherent")

    why_promising = []
    if release_candidate:
        why_promising.append("multiple export-ready artifacts form a coherent bundle")
    if avg_human >= 0.78:
        why_promising.append("strong human-facing artifact scores")
    if avg_sellability >= 0.7:
        why_promising.append("artifacts show credible buyer-facing potential")
    if coherence_score >= 0.76:
        why_promising.append("artifacts cluster around a clear family direction")
    if lineage_score >= 0.45:
        why_promising.append("artifacts show meaningful derivation depth")
    if not why_promising:
        why_promising.append("emerging pack with early curation potential")

    return {
        "pack_score": pack_score,
        "coherence_score": coherence_score,
        "readiness_score": readiness_score,
        "novelty_score": novelty_score,
        "coverage_score": coverage_score,
        "lineage_score": lineage_score,
        "commercial_readiness_score": commercial_readiness_score,
        "sellability_score": round(min(avg_sellability, 0.99), 3),
        "buyer_clarity_score": round(min(avg_buyer_clarity, 0.99), 3),
        "price_band_guess": price_band_guess,
        "artifact_count": count,
        "release_candidate": release_candidate,
        "lifecycle_stage": lifecycle_stage,
        "why_promising": why_promising[:3],
    }


def cluster_artifact_theme(meta: dict) -> str | None:
    theme = meta.get("niche_theme")
    if not theme:
        return None
    return canonical_theme_name(str(theme))


def build_artifact_packs(artifact_meta: list[dict], conn: sqlite3.Connection | None = None) -> list[dict]:
    packs: dict[str, dict] = {}
    for meta in artifact_meta:
        if meta.get("review_status") != "export_ready":
            continue
        niche_theme = cluster_artifact_theme(meta)
        category = meta.get("category", "uncategorized")
        group_kind = "opportunity" if niche_theme else "category"
        group_key = niche_theme or category
        pack_name = f"{group_key.replace(' ', '-')}-{group_kind}-pack"
        pack = packs.setdefault(group_key, {
            "group_key": group_key,
            "group_kind": group_kind,
            "niche_theme": niche_theme,
            "category": category,
            "pack_name": pack_name,
            "items": [],
        })
        pack["items"].append({
            "id": meta.get("id"),
            "title": meta.get("title"),
            "artifact_type": meta.get("artifact_type"),
            "family": meta.get("family"),
            "lifecycle_stage": meta.get("lifecycle_stage"),
            "export_path": meta.get("export_path"),
            "human_proposed_score": meta.get("human_proposed_score"),
            "internal_score": meta.get("internal_score"),
            "novelty_score": meta.get("novelty_score"),
            "proof_level_score": meta.get("proof_level_score"),
            "support_burden_score": meta.get("support_burden_score"),
            "review_status": meta.get("review_status"),
            "generation": meta.get("generation", 1),
            "target_user": meta.get("target_user"),
            "niche_theme": meta.get("niche_theme"),
            "problem_statement": meta.get("problem_statement"),
            "opportunity_score": meta.get("opportunity_score"),
            "buyer_clarity_score": meta.get("buyer_clarity_score"),
            "sellability_score": meta.get("sellability_score"),
            "price_band_guess": meta.get("price_band_guess"),
            "explanation_reasons": explain_artifact(meta),
        })
    result = []
    for _, pack in sorted(packs.items()):
        ranked_items = sorted(pack["items"], key=lambda x: ((x.get("opportunity_score") or 0.0), x["human_proposed_score"]), reverse=True)
        scores = compute_pack_scores(ranked_items)
        result.append({
            "category": pack["category"],
            "group_kind": pack["group_kind"],
            "group_key": pack["group_key"],
            "niche_theme": pack.get("niche_theme"),
            "pack_name": pack["pack_name"],
            "count": len(ranked_items),
            **scores,
            "summary": summarize_pack({"rank": None, "pack_score": scores.get("pack_score"), "sellability_score": scores.get("sellability_score"), "lifecycle_stage": scores.get("lifecycle_stage")}),
            "artifacts": ranked_items,
        })
    result = sorted(result, key=lambda pack: (pack["pack_score"], pack["readiness_score"], pack["coherence_score"], pack["count"]), reverse=True)
    proof_conn = conn or connect()
    top_ids = {item.get("id") for pack in result[:3] for item in pack.get("artifacts", [])}
    for artifact_id in top_ids:
        proof = get_artifact_proof(proof_conn, artifact_id)
        proof["top_pack_hits"] = int(proof.get("top_pack_hits", 0)) + 1
        proof_conn.execute("INSERT OR REPLACE INTO artifact_proof(artifact_id, first_seen_tick, last_seen_tick, appearances, top_pack_hits, review_exports, human_approvals, real_usage_hits, buyer_fit_votes, handoff_acceptances, handoff_rejections, external_validation_state, last_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            artifact_id,
            int(proof.get("first_seen_tick", 0)),
            int(proof.get("last_seen_tick", 0)),
            int(proof.get("appearances", 0)),
            int(proof.get("top_pack_hits", 0)),
            int(proof.get("review_exports", 0)),
            int(proof.get("human_approvals", 0)),
            int(proof.get("real_usage_hits", 0)),
            int(proof.get("buyer_fit_votes", 0)),
            int(proof.get("handoff_acceptances", 0)),
            int(proof.get("handoff_rejections", 0)),
            proof.get("external_validation_state", "unvalidated"),
            proof.get("last_status", "unreviewed"),
        ))
    proof_conn.commit()
    if conn is None:
        proof_conn.close()
    for idx, pack in enumerate(result, start=1):
        pack["rank"] = idx
        pack["delivery_mode"] = recommend_pack_delivery_mode(pack)
        pack.update(summarize_pack_outcomes(pack["pack_name"]))
        pack["summary"] = summarize_pack(pack)
        pack["wrapper_path"] = write_pack_wrapper(pack)
    write_json_file(PACKS_PATH, result)
    return result


def build_uncategorized_groups(artifact_meta: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for meta in artifact_meta:
        if meta.get("category") != "uncategorized":
            continue
        if meta.get("human_proposed_score", 0.0) < 0.55:
            continue
        key = meta.get("artifact_type", "unknown")
        groups.setdefault(key, []).append({
            "id": meta.get("id"),
            "title": meta.get("title"),
            "human_proposed_score": meta.get("human_proposed_score"),
            "path": meta.get("path"),
        })
    result = []
    for artifact_type, items in sorted(groups.items()):
        result.append({
            "group_type": artifact_type,
            "count": len(items),
            "artifacts": sorted(items, key=lambda x: x["human_proposed_score"], reverse=True),
        })
    return result


def build_family_signals(artifact_meta: list[dict]) -> dict:
    family_counts: Dict[str, int] = {}
    for meta in artifact_meta:
        family = meta.get("family", "unknown")
        family_counts[family] = family_counts.get(family, 0) + 1
    return {
        "family_counts": family_counts,
        "active_families": [k for k, _ in sorted(family_counts.items(), key=lambda kv: kv[1], reverse=True)[:6]],
    }


def build_failure_signals(conn: sqlite3.Connection) -> dict:
    rows = [dict(r) for r in conn.execute("SELECT action, status, summary FROM logs ORDER BY id DESC LIMIT 40").fetchall()]
    errors = [r for r in rows if r.get('status') == 'error']
    cooldowns = [r for r in rows if r.get('status') == 'cooldown']
    skipped = [r for r in rows if r.get('status') == 'skipped']
    hot_actions = {}
    for row in errors + cooldowns + skipped:
        action = row.get('action', 'unknown')
        hot_actions[action] = hot_actions.get(action, 0) + 1
    return {
        "error_count": len(errors),
        "cooldown_count": len(cooldowns),
        "skipped_count": len(skipped),
        "friction_actions": [k for k, _ in sorted(hot_actions.items(), key=lambda kv: kv[1], reverse=True)[:5]],
    }


def build_market_signals(artifact_meta: list[dict], packs: list[dict], categories: list[str]) -> dict:
    category_counts: Dict[str, int] = {}
    export_ready_counts: Dict[str, int] = {}
    for meta in artifact_meta:
        category = meta.get("category", "uncategorized")
        category_counts[category] = category_counts.get(category, 0) + 1
        if meta.get("review_status") == "export_ready":
            export_ready_counts[category] = export_ready_counts.get(category, 0) + 1

    rising_categories = [c for c, n in sorted(category_counts.items(), key=lambda kv: kv[1], reverse=True) if n >= 2][:3]
    saturated_categories = [c for c, n in sorted(category_counts.items(), key=lambda kv: kv[1], reverse=True) if n >= 4][:3]
    dormant_categories = [c for c in categories if c not in category_counts and c not in {"uncategorized"}]
    export_pressure = [c for c, n in sorted(export_ready_counts.items(), key=lambda kv: kv[1], reverse=True) if n >= 1][:3]

    release_candidate_packs = [p["pack_name"] for p in packs if p.get("release_candidate")]
    top_ranked_packs = [p["pack_name"] for p in packs[:3]]
    sellable_packs = [p["pack_name"] for p in packs if p.get("sellability_score", 0.0) >= SELLABILITY_SIGNAL_THRESHOLD]
    return {
        "category_counts": category_counts,
        "rising_categories": rising_categories,
        "saturated_categories": saturated_categories,
        "dormant_categories": dormant_categories,
        "export_pressure_categories": export_pressure,
        "pack_count": len(packs),
        "release_candidate_packs": release_candidate_packs,
        "top_ranked_packs": top_ranked_packs,
        "sellable_packs": sellable_packs,
    }


def refresh_state_files(conn: sqlite3.Connection | None = None) -> tuple[list, list, list, list, list, dict]:
    if conn is None:
        conn = connect()
        close_conn = True
    else:
        close_conn = False
    categories = load_categories()
    proposals = load_category_proposals()
    artifact_meta = []
    type_counts: Dict[str, int] = {}
    category_counts: Dict[str, int] = {c: 0 for c in categories if c != "uncategorized"}

    for meta_file in AGENTS_DIR.glob("*/artifacts/*.meta.json"):
        meta = read_json_file(meta_file, None)
        if not isinstance(meta, dict):
            continue
        meta = update_artifact_scores(meta, conn)
        meta = maybe_promote_for_review(meta, meta_file)
        write_json_file(meta_file, meta)
        proof = get_artifact_proof(conn, meta.get("id"))
        current_tick = int(conn.execute("SELECT value FROM world WHERE key='tick'").fetchone()[0]) if conn.execute("SELECT value FROM world WHERE key='tick'").fetchone() else 0
        if proof.get("first_seen_tick", 0) == 0:
            proof["first_seen_tick"] = current_tick
        proof["last_seen_tick"] = current_tick
        proof["appearances"] = int(proof.get("appearances", 0)) + 1
        proof["last_status"] = meta.get("review_status", "unreviewed")
        conn.execute("INSERT OR REPLACE INTO artifact_proof(artifact_id, first_seen_tick, last_seen_tick, appearances, top_pack_hits, review_exports, human_approvals, real_usage_hits, buyer_fit_votes, handoff_acceptances, handoff_rejections, external_validation_state, last_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            meta.get("id"),
            int(proof.get("first_seen_tick", 0)),
            int(proof.get("last_seen_tick", 0)),
            int(proof.get("appearances", 0)),
            int(proof.get("top_pack_hits", 0)),
            int(proof.get("review_exports", 0)),
            int(proof.get("human_approvals", 0)),
            int(proof.get("real_usage_hits", 0)),
            int(proof.get("buyer_fit_votes", 0)),
            int(proof.get("handoff_acceptances", 0)),
            int(proof.get("handoff_rejections", 0)),
            proof.get("external_validation_state", "unvalidated"),
            proof.get("last_status", "unreviewed"),
        ))
        conn.commit()
        meta = update_artifact_scores(meta, conn)
        meta["path"] = str(meta_file.relative_to(BASE_DIR))
        artifact_meta.append(meta)
        type_counts[meta.get("artifact_type", "unknown")] = type_counts.get(meta.get("artifact_type", "unknown"), 0) + 1
        cat = meta.get("category", "uncategorized")
        if cat in category_counts:
            category_counts[cat] += 1

    dormant_categories = [c for c, count in category_counts.items() if count < DORMANT_CATEGORY_MIN_ARTIFACTS and c not in BASE_CATEGORIES]
    uncategorized_strong = [m for m in artifact_meta if m.get("category") == "uncategorized" and m.get("human_proposed_score", 0.0) >= 0.75]

    demand_board = []
    if any(meta.get("artifact_type") == "market_hypothesis" for meta in artifact_meta):
        demand_board.append({"kind": "demand", "title": "Turn research notes into reusable export artifacts", "reason": "Research notes exist, but they need packaging paths and clearer export destinations."})
    if type_counts.get("export_candidate", 0) > 0:
        demand_board.append({"kind": "demand", "title": "Rank export candidates for human review", "reason": "There are exportable modules/components that should be shortlisted outside the sim."})
    if uncategorized_strong:
        demand_board.append({"kind": "emergence", "title": "Strong uncategorized artifacts detected", "reason": "Some high-value artifacts do not fit the current taxonomy and may justify a new category."})
    if dormant_categories:
        demand_board.append({"kind": "governance", "title": "Dormant categories detected", "reason": f"These categories are underused and may need retirement or revival: {', '.join(dormant_categories)}."})
    if any(meta.get("review_status") == "proposed" for meta in artifact_meta):
        demand_board.append({"kind": "review", "title": "Human review queue has proposed artifacts", "reason": "Some artifacts crossed the review threshold and should be inspected by a human."})
    if any(meta.get("review_status") == "export_ready" for meta in artifact_meta):
        demand_board.append({"kind": "export", "title": "Export-ready artifacts available", "reason": "At least one artifact is ready for human inspection or external packaging."})
    if proposals and any(p.get("status") == "pending" for p in proposals):
        demand_board.append({"kind": "governance", "title": "Pending category proposal needs votes", "reason": "A new artifact category has been proposed and awaits majority approval."})
    demand_board = demand_board[:MAX_DEMAND_ITEMS]

    export_queue = sorted([
        {"id": meta.get("id"), "title": meta.get("title"), "artifact_type": meta.get("artifact_type"), "category": meta.get("category"), "lifecycle_stage": meta.get("lifecycle_stage"), "path": meta.get("path"), "destination": meta.get("destination"), "clarity_score": meta.get("clarity_score", 0.0), "reusability_score": meta.get("reusability_score", 0.0), "novelty_score": meta.get("novelty_score", 0.0), "stability_score": meta.get("stability_score", 0.0), "exportability_score": meta.get("exportability_score", 0.0), "market_fit_score": meta.get("market_fit_score", 0.0), "internal_score": meta.get("internal_score", 0.0), "human_proposed_score": meta.get("human_proposed_score", 0.0), "target_user": meta.get("target_user"), "commercial_readiness_score": meta.get("commercial_readiness_score", 0.0), "sellability_score": meta.get("sellability_score", 0.0), "price_band_guess": meta.get("price_band_guess"), "delivery_mode": meta.get("delivery_mode"), "review_status": meta.get("review_status", "unreviewed"), "approved_for_export": meta.get("approved_for_export", False), "export_path": meta.get("export_path"), "status": meta.get("status", "prototype")}
        for meta in artifact_meta
        if meta.get("human_proposed_score", 0.0) >= 0.45 or meta.get("artifact_type") == "export_candidate"
    ], key=lambda item: (item["human_proposed_score"], item["internal_score"]), reverse=True)[:MAX_EXPORT_QUEUE]

    review_queue = sorted([
        {"id": meta.get("id"), "title": meta.get("title"), "artifact_type": meta.get("artifact_type"), "category": meta.get("category"), "lifecycle_stage": meta.get("lifecycle_stage"), "path": meta.get("path"), "review_status": meta.get("review_status", "unreviewed"), "review_notes": meta.get("review_notes", []), "human_proposed_score": meta.get("human_proposed_score", 0.0), "commercial_readiness_score": meta.get("commercial_readiness_score", 0.0), "sellability_score": meta.get("sellability_score", 0.0), "price_band_guess": meta.get("price_band_guess"), "delivery_mode": meta.get("delivery_mode"), "approved_for_export": meta.get("approved_for_export", False), "export_path": meta.get("export_path")}
        for meta in artifact_meta
        if meta.get("review_status") in {"proposed", "approved", "export_ready", "rejected"}
    ], key=lambda item: item["human_proposed_score"], reverse=True)[:MAX_REVIEW_QUEUE]

    packs = build_artifact_packs(artifact_meta, conn)
    emergent_groups = build_uncategorized_groups(artifact_meta)
    family_signals = build_family_signals(artifact_meta)
    market_signals = build_market_signals(artifact_meta, packs, categories)
    failure_signals = build_failure_signals(conn)
    if emergent_groups:
        demand_board.append({"kind": "emergence", "title": "Uncategorized emergent groups detected", "reason": f"There are {len(emergent_groups)} promising uncategorized group(s) worth inspecting."})
    if family_signals["active_families"]:
        demand_board.append({"kind": "family", "title": "Active artifact families detected", "reason": f"Current artifact work is clustering around: {', '.join(family_signals['active_families'])}."})
    if market_signals["rising_categories"]:
        demand_board.append({"kind": "market", "title": "Rising categories detected", "reason": f"Current activity is clustering around: {', '.join(market_signals['rising_categories'])}."})
    if market_signals["saturated_categories"]:
        demand_board.append({"kind": "market", "title": "Saturated categories detected", "reason": f"These categories may be getting crowded: {', '.join(market_signals['saturated_categories'])}."})
    if market_signals["export_pressure_categories"]:
        demand_board.append({"kind": "market", "title": "Export pressure building", "reason": f"These categories currently hold export-ready artifacts: {', '.join(market_signals['export_pressure_categories'])}."})
    sellable_artifacts = [m for m in artifact_meta if m.get("sellability_score", 0.0) >= SELLABILITY_SIGNAL_THRESHOLD]
    if sellable_artifacts:
        demand_board.append({"kind": "commercial", "title": "Promising sellable artifacts detected", "reason": f"{len(sellable_artifacts)} artifact(s) crossed the sellability threshold; top target users include {', '.join(sorted({m.get('target_user', 'technical builders') for m in sellable_artifacts})[:3])}."})
    release_candidate_packs = [p for p in packs if p.get("release_candidate")]
    if release_candidate_packs:
        demand_board.append({"kind": "pack", "title": "Release-candidate pack available", "reason": f"Top pack: {release_candidate_packs[0]['pack_name']} (score {release_candidate_packs[0]['pack_score']})."})
    near_rc_packs = [p for p in packs if not p.get("release_candidate") and p.get("pack_score", 0.0) >= 0.7]
    if near_rc_packs:
        demand_board.append({"kind": "pack", "title": "Pack nearing release-candidate threshold", "reason": f"{near_rc_packs[0]['pack_name']} is close with score {near_rc_packs[0]['pack_score']} and readiness {near_rc_packs[0]['readiness_score']}."})
    sellable_packs = [p for p in packs if p.get("sellability_score", 0.0) >= SELLABILITY_SIGNAL_THRESHOLD]
    if sellable_packs:
        demand_board.append({"kind": "commercial", "title": "Pack with buyer-facing potential detected", "reason": f"{sellable_packs[0]['pack_name']} looks commercially promising (sellability {sellable_packs[0]['sellability_score']}, price band {sellable_packs[0].get('price_band_guess', 'tbd')})."})
    if failure_signals["error_count"] or failure_signals["cooldown_count"] or failure_signals["skipped_count"]:
        demand_board.append({"kind": "failure", "title": "Recent friction detected", "reason": f"Errors={failure_signals['error_count']}, cooldowns={failure_signals['cooldown_count']}, skipped={failure_signals['skipped_count']}; hot actions: {', '.join(failure_signals['friction_actions']) or 'none'}."})
    demand_board = demand_board[:MAX_DEMAND_ITEMS]
    write_json_file(DEMAND_BOARD_PATH, demand_board)
    write_json_file(EXPORT_QUEUE_PATH, export_queue)
    write_json_file(REVIEW_QUEUE_PATH, review_queue)
    write_json_file(CATEGORIES_PATH, categories)
    write_json_file(CATEGORY_PROPOSALS_PATH, proposals)
    if close_conn:
        conn.close()
    return demand_board, export_queue, review_queue, categories, packs, market_signals, emergent_groups, family_signals, failure_signals


def init_world(agent_count: int = DEFAULT_AGENT_COUNT, reset: bool = False) -> None:
    if reset:
        for path in [DB_PATH, DEMAND_BOARD_PATH, EXPORT_QUEUE_PATH, REVIEW_QUEUE_PATH, CATEGORIES_PATH, CATEGORY_PROPOSALS_PATH, PACKS_PATH]:
            if path.exists():
                path.unlink()
        if AGENTS_DIR.exists():
            shutil.rmtree(AGENTS_DIR)
        if EXPORTS_DIR.exists():
            shutil.rmtree(EXPORTS_DIR)
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    write_json_file(CATEGORIES_PATH, BASE_CATEGORIES.copy())
    write_json_file(CATEGORY_PROPOSALS_PATH, [])
    write_json_file(PACKS_PATH, [])
    conn = connect()
    with conn:
        conn.execute("DELETE FROM world")
        conn.execute("DELETE FROM agents")
        conn.execute("DELETE FROM logs")
        now_ts = int(time.time())
        conn.execute("INSERT INTO world(key, value) VALUES (?, ?)", ("tick", "0"))
        conn.execute("INSERT INTO world(key, value) VALUES (?, ?)", ("last_tick_started", "0"))
        for i in range(1, agent_count + 1):
            name = f"agent-{i}"
            agent_dir = AGENTS_DIR / name
            for sub in ["modules", "artifacts"]:
                (agent_dir / sub).mkdir(parents=True, exist_ok=True)
            (agent_dir / "memory.json").write_text("[]")
            (agent_dir / "inbox.json").write_text("[]")
            cadence_interval = 1 + ((i - 1) % 3)
            state = AgentState(name=name, energy=STARTING_ENERGY, storage=STARTING_STORAGE, gpu_quota=STARTING_GPU, reputation=STARTING_REPUTATION, next_due_tick=0, wake_reason="initial", cadence_interval=cadence_interval)
            conn.execute("INSERT INTO agents(name, energy, storage, gpu_quota, reputation, last_inspect_at, last_trade_at, age_ticks, next_due_tick, wake_reason, cadence_interval) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (state.name, state.energy, state.storage, state.gpu_quota, state.reputation, state.last_inspect_at, state.last_trade_at, state.age_ticks, state.next_due_tick, state.wake_reason, state.cadence_interval))
    seed_world_objects(agent_count, now_ts)
    refresh_state_files()
    conn.close()


def get_world(conn: sqlite3.Connection) -> Dict:
    rows = conn.execute("SELECT key, value FROM world").fetchall()
    data = {row["key"]: row["value"] for row in rows}
    return {"project": PROJECT_NAME, "version": VERSION, "tick": int(data.get("tick", 0)), "last_tick_started": int(data.get("last_tick_started", 0)), "base_dir": str(BASE_DIR), "execution_budget_seconds": EXECUTION_BUDGET_SECONDS, "code_timeout_seconds": CODE_TIMEOUT_SECONDS, "tick_seconds": TICK_SECONDS}


def list_agents(conn: sqlite3.Connection) -> List[Dict]:
    return [dict(row) for row in conn.execute("SELECT * FROM agents ORDER BY name").fetchall()]


def write_artifact_metadata(agent: Dict, agent_dir: Path, artifact_slug: str, artifact_type: str, idea: str, explanation: str, purpose: str, destination: str, future_directions: List[str], combinable_with: List[str], lineage: Dict, category: str, opportunity: Dict | None = None) -> str:
    artifacts_dir = agent_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_id = f"{agent['name']}-{artifact_slug}-{int(time.time())}"
    meta_path = artifacts_dir / f"{artifact_slug}.meta.json"
    opportunity = opportunity or {}
    payload = {
        "id": artifact_id,
        "agent_name": agent["name"],
        "title": artifact_slug.replace("_", " ").title(),
        "artifact_type": artifact_type,
        "category": category,
        "family": choose_family(lineage.get("action", ""), artifact_type, category),
        "idea": idea,
        "explanation": explanation,
        "purpose": purpose,
        "destination": destination,
        "niche_theme": opportunity.get("niche_theme"),
        "target_user": opportunity.get("target_user"),
        "problem_statement": opportunity.get("problem_statement"),
        "gap_reason": opportunity.get("gap_reason"),
        "existing_solution_friction": opportunity.get("existing_solution_friction"),
        "artifact_hypothesis": opportunity.get("artifact_hypothesis"),
        "offer_hypothesis": opportunity.get("offer_hypothesis"),
        "delivery_mode_guess": opportunity.get("delivery_mode_guess"),
        "research_confidence": opportunity.get("research_confidence", 0.45),
        "audience": ["local AI tinkerers", "agent-sim builders"],
        "depends_on": ["persistent memory", "timed ticks"],
        "combinable_with": combinable_with,
        "why_now": "CircleForge agents benefit from reusable, inspectable outputs instead of opaque internal work.",
        "future_directions": future_directions,
        "if_interest_exists": ["package as a standalone module", "export to a GitHub subproject", "bundle into a premium add-on pack"],
        "lineage": lineage,
        "parent_ids": lineage.get("parent_ids", []),
        "derived_from": lineage.get("derived_from", []),
        "generation": lineage.get("generation", 1),
        "status": "prototype",
        "lifecycle_stage": "prototype",
        "review_status": "unreviewed",
        "review_notes": [],
        "approved_for_export": False,
        "export_path": None,
    }
    payload = update_artifact_scores(payload)
    write_json_file(meta_path, payload)
    return meta_path.name


def inspect_target(actor: Dict, target: Dict, now_ts: int) -> ActionResult:
    elapsed = now_ts - int(actor.get("last_inspect_at", 0))
    if elapsed < DAILY_COOLDOWN_SECONDS:
        remaining = DAILY_COOLDOWN_SECONDS - elapsed
        return ActionResult(action="inspect", status="cooldown", summary=f"inspect cooldown active ({remaining}s remaining)")
    target_dir = AGENTS_DIR / target["name"]
    modules = [p.name for p in sorted((target_dir / "modules").glob("*.py"))]
    artifacts = [p.name for p in sorted((target_dir / "artifacts").glob("*")) if p.is_file()]
    target_memory = load_opportunity_memory(target_dir)
    top_theme = None
    theme_items = sorted((target_memory.get("themes") or {}).items(), key=lambda kv: kv[1].get("strength", 0.0), reverse=True)
    if theme_items:
        top_theme = theme_items[0][0]
    raw = json.dumps({
        "target": target["name"],
        "reputation": target["reputation"],
        "storage": target["storage"],
        "age_ticks": target["age_ticks"],
        "module_count": len(modules),
        "artifact_count": len(artifacts),
        "sample_modules": modules[:3],
        "sample_artifacts": artifacts[:3],
        "top_theme": top_theme,
    }, indent=2)
    actor["last_inspect_at"] = now_ts
    update_relationship(actor["name"], target["name"], "inspect", True, now_ts)
    save_note(AGENTS_DIR / actor["name"], f"inspect learned {target['name']} top_theme={top_theme or 'unknown'} modules={len(modules)} artifacts={len(artifacts)}")
    return ActionResult(action="inspect", status="ok", summary=f"inspected {target['name']}", reputation_delta=0.01, target=target["name"], raw_output=raw)


def choose_project_for_theme(theme: str | None, projects: list[dict]) -> dict | None:
    if not theme:
        return projects[0] if projects else None
    theme_lower = str(theme).lower()
    for project in projects:
        blob = f"{project.get('name', '')} {project.get('purpose', '')}".lower()
        if theme_lower in blob:
            return project
    return projects[0] if projects else None


def update_relationship(source_agent: str, target_agent: str, event_kind: str, success: bool, now_ts: int) -> None:
    relationships = load_relationships()
    rel = next((item for item in relationships if item.get("source_agent") == source_agent and item.get("target_agent") == target_agent), None)
    if rel is None:
        rel = RelationshipState(source_agent, target_agent, 0.5, 0.5, 0.0, event_kind, now_ts).to_dict()
        relationships.append(rel)
    if success:
        rel["trust"] = round(min(float(rel.get("trust", 0.5)) + 0.04, 0.99), 3)
        rel["usefulness"] = round(min(float(rel.get("usefulness", 0.5)) + 0.05, 0.99), 3)
        rel["friction"] = round(max(float(rel.get("friction", 0.0)) - 0.02, 0.0), 3)
    else:
        rel["friction"] = round(min(float(rel.get("friction", 0.0)) + 0.07, 0.99), 3)
        rel["trust"] = round(max(float(rel.get("trust", 0.5)) - 0.03, 0.05), 3)
    rel["last_event"] = event_kind
    rel["updated_at"] = now_ts
    save_relationships(relationships)


def register_self_mod_proposal(agent_name: str, pressure_source: str, problem_summary: str, now_ts: int) -> dict | None:
    proposals = load_self_mod_proposals()
    duplicate = next((item for item in proposals if item.get("agent_id") == agent_name and item.get("problem_summary") == problem_summary and item.get("status") in {"proposed", "approved"}), None)
    if duplicate:
        duplicate["validation_notes"] = f"seen again at {now_ts}"
        save_self_mod_proposals(proposals)
        return duplicate
    target_path = f"agents/{agent_name}/modules/helper_{agent_name}.py"
    proposal = SelfModificationProposalState(
        id=f"smp-{agent_name}-{now_ts}",
        agent_id=agent_name,
        created_at=now_ts,
        target_path=target_path,
        scope="private",
        pressure_source=pressure_source,
        problem_summary=problem_summary,
        proposed_change="Create or refine a private helper/wrapper to reduce repeated local friction.",
        expected_benefit="Lower repeated failure cost and improve local capability without touching protected core files.",
        risk_level="low",
        checkpoint_ref="pending-before-apply",
        status="proposed",
        validation_notes="proposal-only; full auto-editing remains future bounded work",
    ).to_dict()
    proposals.append(proposal)
    save_self_mod_proposals(proposals[-100:])
    return proposal


def signal_target(actor: Dict, target: Dict, now_ts: int, theme: str | None, need: str | None, category: str | None) -> ActionResult:
    target_dir = AGENTS_DIR / target["name"]
    message = {
        "from": actor["name"],
        "theme": theme or "shared need",
        "need": need or "coordinate around recent friction",
        "category": category or "uncategorized",
        "sent_at": now_ts,
    }
    push_inbox_message(target_dir, message)
    projects = load_projects()
    project = choose_project_for_theme(theme, projects)
    message_log = load_messages()
    message_entry = MessageState(
        id=f"msg-{actor['name']}-{target['name']}-{now_ts}",
        from_agent=actor["name"],
        to_agent=target["name"],
        kind="signal",
        theme=theme or "shared need",
        content=need or "coordinate around recent friction",
        created_at=now_ts,
    ).to_dict()
    if project:
        message_entry["project_id"] = project.get("id")
    message_log.append(message_entry)
    save_messages(message_log[-200:])
    update_relationship(actor["name"], target["name"], "signal", True, now_ts)
    save_note(AGENTS_DIR / actor["name"], f"signal sent to {target['name']} about {message['theme']}: {message['need']}")
    raw = json.dumps({"from": actor["name"], "to": target["name"], "message": message}, indent=2)
    return ActionResult(action="signal", status="ok", summary=f"signaled {target['name']} about {message['theme']}", reputation_delta=0.015, target=target["name"], raw_output=raw)


def consume_inbox(agent: Dict, agent_dir: Path) -> tuple[list[dict], int]:
    inbox = load_inbox(agent_dir)
    if not inbox:
        return [], 0
    recent = inbox[-3:]
    remaining = inbox[:-3]
    (agent_dir / "inbox.json").write_text(json.dumps(remaining, indent=2))
    for item in recent:
        save_note(agent_dir, f"message from {item.get('from', 'unknown')} theme={item.get('theme', 'shared need')} need={item.get('need', '')}")
    return recent, len(recent)


def summarize_unresolved_needs(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT summary FROM logs WHERE status IN ('error','cooldown','skipped') ORDER BY id DESC LIMIT 8").fetchall()
    needs = []
    for row in rows:
        summary = str(row["summary"])
        if summary not in needs:
            needs.append(summary)
    return needs[:4]


def update_work_item_progress(now_ts: int, summaries: list[dict]) -> None:
    work_items = load_work_items()
    if not work_items:
        return
    for item in work_items:
        if item.get("status") != "open":
            continue
        owner = item.get("owner")
        owner_events = [s for s in summaries if s.get("agent") == owner and s.get("status") == "ok"]
        if owner_events:
            item["priority"] = round(max(0.2, float(item.get("priority", 0.6)) - 0.04), 3)
            item["notes"] = f"Last progressed at {now_ts} by {owner}"
            if item["priority"] <= 0.28:
                item["status"] = "done"
    save_work_items(work_items)


def route_project_ownership(now_ts: int, summaries: list[dict]) -> None:
    projects = load_projects()
    work_items = load_work_items()
    if not projects:
        return
    for project in projects:
        matching = [s for s in summaries if str(s.get("niche_theme", "")).lower() in f"{project.get('name', '')} {project.get('purpose', '')}".lower() and s.get("status") == "ok"]
        if matching:
            best = sorted(matching, key=lambda item: item.get("reputation", 0.0), reverse=True)[0]
            owners = project.get("owners") or []
            if best.get("agent") not in owners:
                owners.append(best.get("agent"))
                project["owners"] = owners[:3]
            project["updated_at"] = now_ts
        related_items = [item for item in work_items if item.get("project_id") == project.get("id") and item.get("status") == "open"]
        if not related_items:
            owner = (project.get("owners") or ["agent-1"])[0]
            work_items.append(WorkItemState(
                id=f"work-{project.get('id')}-{now_ts}",
                title=f"Advance {project.get('name')}",
                status="open",
                priority=0.62,
                owner=owner,
                created_at=now_ts,
                project_id=project.get("id"),
                need_id="",
                notes=f"Auto-routed follow-up work for {project.get('name')}",
            ).to_dict())
    save_projects(projects)
    save_work_items(work_items[-100:])


def maybe_propose_self_modifications(now_ts: int, summaries: list[dict]) -> list[dict]:
    proposals = []
    for item in summaries:
        if item.get("status") in {"error", "cooldown", "skipped"}:
            rows = []
            try:
                conn = connect()
                rows = conn.execute("SELECT summary FROM logs WHERE agent_name=? ORDER BY id DESC LIMIT 6", (item.get("agent"),)).fetchall()
                conn.close()
            except Exception:
                rows = []
            repeated = sum(1 for row in rows if str(row["summary"]) == str(item.get("summary")))
            if repeated >= 2:
                proposal = register_self_mod_proposal(item.get("agent"), item.get("status"), item.get("summary"), now_ts)
                if proposal:
                    proposals.append(proposal)
    return proposals


def sync_question_lineage_to_world(now_ts: int, tick: int) -> None:
    communicator = load_communicator_state()
    current_question = str(communicator.get("unresolved_question", "")).strip()
    if not current_question:
        return

    public_memory = load_public_memory()
    title = f"Communicator question: {current_question}"
    existing_memory = next((item for item in public_memory if item.get("title") == title), None)
    if existing_memory:
        existing_memory["updated_at"] = now_ts
        existing_memory["stability"] = round(min(float(existing_memory.get("stability", 0.45)) + 0.02, 0.9), 3)
    else:
        public_memory.append(PublicMemoryState(
            id=f"pm-question-{tick}",
            title=title,
            kind="question",
            content=f"Active communicator inquiry tied to pursuit {communicator.get('active_pursuit', '')}.",
            source="communicator-question-lineage",
            stability=0.48,
            created_at=now_ts,
            updated_at=now_ts,
        ).to_dict())
    save_public_memory(public_memory[-80:])

    needs = load_needs()
    existing_need = next((item for item in needs if item.get("title") == current_question), None)
    if existing_need:
        existing_need["updated_at"] = now_ts
        existing_need["pressure"] = round(min(float(existing_need.get("pressure", 0.45)) + 0.04, 0.95), 3)
        existing_need["status"] = "active"
    else:
        needs.append(NeedState(
            id=f"need-question-{tick}",
            title=current_question,
            kind="exploration",
            description=f"Communicator inquiry currently driving exploration: {current_question}",
            origin="communicator-question-lineage",
            scope="public",
            pressure=0.44,
            novelty=0.55,
            status="open",
            created_at=now_ts,
            updated_at=now_ts,
        ).to_dict())
    save_needs(needs[-80:])

    projects = load_projects()
    work_items = load_work_items()
    project = choose_project_for_theme(communicator.get("active_pursuit"), projects)
    if project:
        duplicate = next((item for item in work_items if item.get("title") == current_question and item.get("project_id") == project.get("id") and item.get("status") == "open"), None)
        if duplicate is None:
            work_items.append(WorkItemState(
                id=f"work-question-{tick}",
                title=current_question,
                status="open",
                priority=0.58,
                owner=(project.get("owners") or ["agent-1"])[0],
                created_at=now_ts,
                project_id=project.get("id"),
                need_id=next((item.get("id") for item in needs if item.get("title") == current_question), ""),
                notes="Inquiry-driven work item spawned from communicator question lineage",
            ).to_dict())
            save_work_items(work_items[-120:])


def sync_experiments_to_world(now_ts: int, tick: int, summaries: list[dict]) -> None:
    communicator = load_communicator_state()
    current_question = str(communicator.get("unresolved_question", "")).strip()
    if not current_question:
        return
    experiments = load_experiments()
    projects = load_projects()
    needs = load_needs()
    project = choose_project_for_theme(communicator.get("active_pursuit"), projects)
    need = next((item for item in needs if item.get("title") == current_question), None)

    existing = next((item for item in experiments if item.get("title") == current_question and item.get("status") in {"proposed", "running"}), None)
    if existing is None:
        experiments.append(ExperimentState(
            id=f"exp-{tick}",
            title=current_question,
            hypothesis=f"A short inspect/research loop around {communicator.get('active_pursuit') or 'current pursuit'} will reduce uncertainty.",
            owner=(project.get("owners") or ["agent-1"])[0] if project else "agent-1",
            status="proposed",
            created_at=now_ts,
            related_need=need.get("id") if need else "",
            project_id=project.get("id") if project else "",
            observations="",
            follow_up="Run inspect or research and compare whether the question changes.",
        ).to_dict())
    else:
        relevant = [s for s in summaries if s.get("niche_theme") and str(s.get("niche_theme")).lower() in current_question.lower() and s.get("action") in {"inspect", "research"}]
        if relevant:
            latest = relevant[-1]
            existing["status"] = "running"
            existing["observations"] = f"Latest relevant action: {latest.get('action')} by {latest.get('agent')}"
            existing["follow_up"] = "Re-check whether the communicator question changed or narrowed after this action."
            owner = existing.get("owner") or latest.get("agent")
            if owner and latest.get("agent"):
                update_relationship(owner, latest.get("agent"), "experiment-progress", True, now_ts)
            if current_question != existing.get("title"):
                existing["status"] = "succeeded"
        else:
            existing["follow_up"] = "No clarifying action observed yet; caution may be warranted if this keeps stalling."
    experiments = experiments[-120:]
    save_experiments(experiments)


def apply_experiment_social_feedback(now_ts: int) -> None:
    experiments = load_experiments()
    communicator = load_communicator_state()
    caution_targets = []
    for experiment in experiments:
        owner = experiment.get("owner")
        status = experiment.get("status")
        title = str(experiment.get("title", ""))
        if status == "running":
            related_agents = [name for name in ["agent-1", "agent-2", "agent-3", "agent-4", "agent-5"] if name != owner]
            for agent_name in related_agents:
                update_relationship(agent_name, owner, "experiment-progress", True, now_ts)
        elif status == "proposed" and title == str(communicator.get("unresolved_question", "")):
            caution_targets.append(title)
    if caution_targets:
        communicator["avoidance_bias"] = f"avoid overcommitting before experiment clarity on {caution_targets[-1]}"
        save_communicator_state(communicator)


def update_world_objects(conn: sqlite3.Connection, tick: int, now_ts: int, summaries: list[dict]) -> None:
    unresolved = summarize_unresolved_needs(conn)
    needs = load_needs()
    for summary in unresolved:
        existing = next((item for item in needs if item.get("title") == summary), None)
        if existing:
            existing["pressure"] = round(min(float(existing.get("pressure", 0.4)) + 0.08, 0.99), 3)
            existing["updated_at"] = now_ts
            existing["status"] = "active"
        else:
            needs.append(NeedState(
                id=f"need-{tick}-{len(needs)+1}",
                title=summary,
                kind="repair",
                description=f"Observed unresolved runtime friction: {summary}",
                origin="world-log",
                scope="public",
                pressure=0.58,
                novelty=0.42,
                status="open",
                created_at=now_ts,
                updated_at=now_ts,
            ).to_dict())
    for item in needs:
        if item.get("title") not in unresolved:
            item["pressure"] = round(max(0.08, float(item.get("pressure", 0.3)) * 0.97), 3)
            if item["pressure"] < 0.16:
                item["status"] = "cooling"
    save_needs(needs[-50:])

    public_memory = load_public_memory()
    if any(s.get("action") == "signal" and s.get("status") == "ok" for s in summaries):
        title = "Signals can redirect nearby work"
        existing = next((item for item in public_memory if item.get("title") == title), None)
        content = "Successful signals should remain visible because communication becomes useful when it changes another agent's subsequent behavior."
        if existing:
            existing["updated_at"] = now_ts
            existing["stability"] = round(min(float(existing.get("stability", 0.5)) + 0.03, 0.95), 3)
        else:
            public_memory.append(PublicMemoryState(
                id=f"pm-signal-{tick}",
                title=title,
                kind="lesson",
                content=content,
                source="world-observation",
                stability=0.66,
                created_at=now_ts,
                updated_at=now_ts,
            ).to_dict())
    save_public_memory(public_memory[-50:])

    route_project_ownership(now_ts, summaries)
    update_work_item_progress(now_ts, summaries)
    maybe_propose_self_modifications(now_ts, summaries)
    sync_question_lineage_to_world(now_ts, tick)
    sync_experiments_to_world(now_ts, tick, summaries)
    apply_experiment_social_feedback(now_ts)


def agent_social_context(agent_dir: Path) -> Dict:
    inbox = load_inbox(agent_dir)
    memory = load_opportunity_memory(agent_dir)
    strongest = sorted((memory.get("themes") or {}).items(), key=lambda kv: kv[1].get("strength", 0.0), reverse=True)[:3]
    return {
        "inbox_count": len(inbox),
        "recent_messages": inbox[-3:],
        "strongest_themes": [name for name, _payload in strongest],
    }


def compute_agent_due_state(agent: Dict, tick: int, consumed_count: int, unresolved_needs: list[str]) -> tuple[bool, str]:
    communicator = load_communicator_state()
    curiosity = float(communicator.get("curiosity", 0.6))
    unresolved_question = str(communicator.get("unresolved_question", "")).strip()
    active_experiments = [item for item in load_experiments() if item.get("status") in {"proposed", "running"}]
    if tick <= int(agent.get("next_due_tick", 0)):
        if active_experiments and classify_internal_role(agent.get("name", "agent")) in {"observer", "critic", "memory_keeper"}:
            return True, "experiment-pressure"
        if unresolved_question and classify_internal_role(agent.get("name", "agent")) in {"observer", "critic", "memory_keeper"}:
            return True, "question-pressure"
        if curiosity > 0.82 and classify_internal_role(agent.get("name", "agent")) in {"observer", "critic"}:
            return True, "curiosity-pressure"
        return False, "waiting-for-next-due-tick"
    if consumed_count > 0:
        return True, "message-received"
    if active_experiments and classify_internal_role(agent.get("name", "agent")) in {"observer", "critic", "memory_keeper"}:
        return True, "experiment-pressure"
    if unresolved_needs:
        return True, "unresolved-need-pressure"
    if unresolved_question and classify_internal_role(agent.get("name", "agent")) in {"observer", "memory_keeper", "critic"}:
        return True, "question-pressure"
    if curiosity > 0.76 and classify_internal_role(agent.get("name", "agent")) in {"observer", "memory_keeper", "critic"}:
        return True, "curiosity-pressure"
    return True, "scheduled-cadence"


def classify_internal_role(agent_name: str) -> str:
    suffix = int(str(agent_name).split("-")[-1]) if "-" in str(agent_name) else 0
    mapping = {
        1: "observer",
        2: "builder",
        3: "critic",
        4: "coordinator",
        5: "memory_keeper",
    }
    return mapping.get(suffix, "specialist")


def propose_internal_thought(agent: Dict, plan: Dict, wake_reason: str, communicator: dict) -> dict:
    role = classify_internal_role(agent.get("name", "agent"))
    action = plan.get("action")
    stance = "agree"
    current_intent = str(communicator.get("current_intent", "")).lower()
    active_pursuit = str(communicator.get("active_pursuit", "")).lower()
    curiosity_target = str(communicator.get("curiosity_target", "")).lower()
    curiosity = float(communicator.get("curiosity", 0.6))
    theme = str(plan.get("niche_theme") or "")
    unresolved_question = str(communicator.get("unresolved_question", "")).lower()
    active_experiments = load_experiments()
    if role == "critic" and action in {"build_module", "trade"}:
        stance = "question"
    elif role == "coordinator":
        stance = "prioritize"
    elif role == "observer" and (action == "inspect" or curiosity > 0.72 or (theme and theme.lower() in unresolved_question)):
        stance = "support"
    elif role == "builder" and action == "build_module":
        stance = "support"
    elif role == "memory_keeper" and (wake_reason == "message-received" or theme and theme.lower() in current_intent):
        stance = "prioritize"
    if any(item.get("status") == "running" and theme and theme.lower() in str(item.get("title", "")).lower() for item in active_experiments):
        if action in {"inspect", "research"}:
            stance = "prioritize"
    if curiosity > 0.8 and role in {"observer", "critic"} and action not in {"inspect", "research"}:
        stance = "question"
    return {
        "agent": agent.get("name"),
        "role": role,
        "proposed_action": action,
        "niche_theme": plan.get("niche_theme"),
        "reason": plan.get("reason"),
        "wake_reason": wake_reason,
        "stance": stance,
        "intent_alignment": theme.lower() in current_intent if theme else False,
        "pursuit_alignment": theme.lower() in active_pursuit if theme else False,
        "curiosity_alignment": theme.lower() in curiosity_target if theme else False,
        "question_alignment": theme.lower() in unresolved_question if theme else False,
    }


def resolve_or_extend_question(communicator: dict, chosen: dict, final_action: str | None) -> tuple[str, bool]:
    previous_question = str(communicator.get("unresolved_question", "")).strip()
    theme = chosen.get("niche_theme") or communicator.get("active_pursuit") or "current pressure"
    if final_action in {"inspect", "research"}:
        new_question = f"What new uncertainty appeared after {final_action} on {theme}?"
        return new_question, True
    if chosen.get("niche_theme"):
        new_question = f"What is still unclear about {theme}?"
        return new_question, False
    return previous_question or "What remains under-understood?", False


def average_internal_reputation(agent_name: str) -> tuple[float, float, float]:
    relationships = load_relationships()
    relevant = [item for item in relationships if item.get("target_agent") == agent_name]
    if not relevant:
        return 0.5, 0.5, 0.0
    trust = sum(float(item.get("trust", 0.5)) for item in relevant) / len(relevant)
    usefulness = sum(float(item.get("usefulness", 0.5)) for item in relevant) / len(relevant)
    friction = sum(float(item.get("friction", 0.0)) for item in relevant) / len(relevant)
    return round(trust, 3), round(usefulness, 3), round(friction, 3)


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


def integrate_internal_proposals(now_ts: int, proposals: list[dict], unresolved_needs: list[str]) -> dict:
    communicator = load_communicator_state()
    if not proposals:
        communicator["status"] = "idle"
        communicator["last_wake_at"] = now_ts
        communicator["updated_at"] = now_ts
        communicator["last_decision_summary"] = "no internal proposals this cycle"
        save_communicator_state(communicator)
        return {"current_intent": communicator.get("current_intent"), "chosen_action": None, "consensus": []}

    previous_intent = str(communicator.get("current_intent", "")).lower()
    curiosity = float(communicator.get("curiosity", 0.6))
    ranked = []
    objections = []
    for proposal in proposals:
        trust, usefulness, friction = average_internal_reputation(proposal.get("agent"))
        score = 0.5 + (trust - 0.5) * 0.25 + (usefulness - 0.5) * 0.35 - friction * 0.25
        if proposal.get("stance") in {"support", "prioritize"}:
            score += 0.18
        if proposal.get("role") == "coordinator":
            score += 0.14
        if proposal.get("wake_reason") == "message-received":
            score += 0.08
        if proposal.get("intent_alignment"):
            score += 0.12
        if proposal.get("pursuit_alignment"):
            score += 0.08
        if proposal.get("curiosity_alignment"):
            score += 0.06
        if proposal.get("question_alignment"):
            score += 0.1
        score += decision_style_weight(communicator, proposal.get("proposed_action"), None)
        running_experiments = [item for item in load_experiments() if item.get("status") == "running"]
        if any(proposal.get("niche_theme") and proposal.get("niche_theme").lower() in str(item.get("title", "")).lower() for item in running_experiments):
            score += 0.12
        if unresolved_needs and proposal.get("proposed_action") in {"inspect", "research", "optimize"}:
            score += 0.1
        if curiosity > 0.78 and proposal.get("proposed_action") in {"inspect", "research"}:
            score += 0.12
        if proposal.get("role") == "critic" and proposal.get("stance") == "question":
            score -= 0.08 - min(usefulness * 0.06, 0.05)
            objections.append(f"critic:{proposal.get('reason')}")
        proposal["epistemic_weight"] = {"trust": trust, "usefulness": usefulness, "friction": friction, "score": round(score, 3)}
        ranked.append((score, proposal))
    ranked.sort(key=lambda item: item[0], reverse=True)
    chosen = ranked[0][1]
    disagreement_count = sum(1 for p in proposals if p.get("stance") == "question")

    final_action = chosen.get("proposed_action")
    decision_mode = "act"
    inspect_first_boost = decision_style_weight(communicator, None, "inspect-first")
    reconsider_boost = decision_style_weight(communicator, None, "reconsider")
    defer_boost = decision_style_weight(communicator, None, "defer")
    act_boost = decision_style_weight(communicator, None, "act")

    if disagreement_count >= 2 and chosen.get("proposed_action") in {"build_module", "trade"}:
        final_action = "inspect"
        decision_mode = "inspect-first"
    elif disagreement_count >= 1 and chosen.get("role") != "coordinator" and chosen.get("proposed_action") in {"build_module", "trade"}:
        final_action = "research"
        decision_mode = "reconsider"
    elif disagreement_count >= 2 and curiosity < 0.7:
        final_action = None
        decision_mode = "defer"

    if disagreement_count >= 1 and chosen.get("proposed_action") in {"optimize", "build_module", "trade"} and inspect_first_boost > 0.045:
        final_action = "inspect"
        decision_mode = "inspect-first"
    elif disagreement_count >= 1 and reconsider_boost > 0.045 and chosen.get("proposed_action") not in {"inspect", "research"}:
        final_action = "research"
        decision_mode = "reconsider"
    elif disagreement_count >= 1 and defer_boost > 0.06 and curiosity < 0.78:
        final_action = None
        decision_mode = "defer"

    if act_boost > 0.09 and disagreement_count == 0:
        decision_mode = "act"

    mode_boost = decision_style_weight(communicator, None, decision_mode)
    if mode_boost > 0.08 and final_action is None:
        final_action = chosen.get("proposed_action")
        decision_mode = "act"

    intent_text = f"{final_action or chosen.get('proposed_action')} around {chosen.get('niche_theme') or 'current world pressure'}"
    communicator["status"] = "active" if final_action else "reflecting"
    experiments = load_experiments()
    running_match = next((item for item in experiments if item.get("status") == "running" and chosen.get("niche_theme") and chosen.get("niche_theme").lower() in str(item.get("title", "")).lower()), None)
    communicator["current_intent"] = intent_text
    communicator["active_pursuit"] = chosen.get("niche_theme") or communicator.get("active_pursuit") or "world enrichment"
    communicator["dominant_need"] = unresolved_needs[0] if unresolved_needs else (chosen.get("niche_theme") or "")
    communicator["curiosity_target"] = unresolved_needs[0] if unresolved_needs else (chosen.get("niche_theme") or communicator.get("curiosity_target") or "emergent pressure")
    if running_match:
        communicator["curiosity_target"] = running_match.get("title")
        communicator["active_pursuit"] = chosen.get("niche_theme") or communicator.get("active_pursuit")
    next_question, previous_resolved = resolve_or_extend_question(communicator, chosen, final_action)
    communicator["unresolved_question"] = next_question
    communicator["attraction_bias"] = f"move toward {chosen.get('niche_theme') or 'coherent world improvement'}"
    if disagreement_count > 0:
        communicator["avoidance_bias"] = f"avoid brittle action around {chosen.get('niche_theme') or 'current pressure'} until objections are understood"
    weight = chosen.get("epistemic_weight", {})
    communicator["last_decision_summary"] = f"{decision_mode} from {chosen.get('agent')} ({chosen.get('role')}) with {disagreement_count} questioning voice(s); trust={weight.get('trust', 0.5)} usefulness={weight.get('usefulness', 0.5)}"
    communicator["last_wake_at"] = now_ts
    communicator["updated_at"] = now_ts
    if unresolved_needs:
        communicator["curiosity"] = round(min(max(curiosity + 0.03, 0.1), 0.99), 3)
    elif intent_text.lower() == previous_intent:
        communicator["curiosity"] = round(min(max(curiosity + 0.015, 0.1), 0.99), 3)
    else:
        communicator["curiosity"] = round(min(max(curiosity - 0.01, 0.1), 0.99), 3)
    update_decision_style_memory(communicator, decision_mode, final_action, chosen, unresolved_needs)
    history = list(communicator.get("intent_history") or [])
    history.append(intent_text)
    communicator["intent_history"] = history[-12:]
    question_history = list(communicator.get("question_history") or [])
    if previous_resolved and question_history:
        question_history[-1] = f"resolved-ish: {question_history[-1]}"
    question_history.append(next_question)
    communicator["question_history"] = question_history[-16:]
    communicator["unresolved_objections"] = (objections or list(communicator.get("unresolved_objections") or []))[-8:]
    save_communicator_state(communicator)
    return {
        "current_intent": communicator.get("current_intent"),
        "chosen_action": final_action,
        "chosen_theme": chosen.get("niche_theme"),
        "decision_mode": decision_mode,
        "consensus": proposals,
    }


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
    conn.execute("UPDATE agents SET energy=?, storage=?, gpu_quota=?, reputation=?, last_inspect_at=?, last_trade_at=?, age_ticks=? WHERE name=?", (target["energy"], target["storage"], target["gpu_quota"], target["reputation"], target["last_inspect_at"], target["last_trade_at"], target["age_ticks"], target["name"]))
    raw = json.dumps({"from": actor["name"], "to": target["name"], "offer": {"storage": 3}, "received_effect": {"energy": 2, "reputation": 0.02}, "target_effect": {"storage": 2, "reputation": 0.01}}, indent=2)
    update_relationship(actor["name"], target["name"], "trade", True, now_ts)
    return ActionResult(action="trade", status="ok", summary=f"traded with {target['name']}", target=target["name"], raw_output=raw)


def apply_action(agent: Dict, action_plan: Dict, agent_dir: Path, agents_by_name: Dict[str, Dict], now_ts: int, conn: sqlite3.Connection) -> ActionResult:
    action = action_plan["action"]
    reason = action_plan.get("reason", "")
    code = action_plan.get("code", "")
    target_name = action_plan.get("target")
    category = normalize_category_for_artifact(action, action_plan.get("category"))
    opportunity = {
        "niche_theme": action_plan.get("niche_theme"),
        "target_user": action_plan.get("target_user"),
        "problem_statement": action_plan.get("problem_statement"),
        "gap_reason": action_plan.get("gap_reason"),
        "existing_solution_friction": action_plan.get("existing_solution_friction"),
        "artifact_hypothesis": action_plan.get("artifact_hypothesis"),
        "offer_hypothesis": action_plan.get("offer_hypothesis"),
        "delivery_mode_guess": action_plan.get("delivery_mode_guess"),
        "research_confidence": action_plan.get("research_confidence", 0.45),
        "price_band_guess": action_plan.get("price_band_guess"),
    }
    if action == "rest":
        return ActionResult(action=action, status="ok", summary=f"rested: {reason}", energy_delta=8)
    if action == "inspect":
        if not target_name or target_name == agent["name"] or target_name not in agents_by_name:
            update_relationship(agent["name"], target_name or "unknown", "inspect", False, now_ts)
            return ActionResult(action=action, status="skipped", summary="inspect skipped: no valid target")
        return inspect_target(agent, agents_by_name[target_name], now_ts)
    if action == "trade":
        if not target_name or target_name == agent["name"] or target_name not in agents_by_name:
            update_relationship(agent["name"], target_name or "unknown", "trade", False, now_ts)
            return ActionResult(action=action, status="skipped", summary="trade skipped: no valid target")
        return trade_with_target(agent, agents_by_name[target_name], now_ts, conn)
    if action == "signal":
        if not target_name or target_name == agent["name"] or target_name not in agents_by_name:
            update_relationship(agent["name"], target_name or "unknown", "signal", False, now_ts)
            return ActionResult(action=action, status="skipped", summary="signal skipped: no valid target")
        need = action_plan.get("need") or action_plan.get("problem_statement") or reason
        return signal_target(agent, agents_by_name[target_name], now_ts, action_plan.get("niche_theme"), need, action_plan.get("category"))
    run = run_python(code, agent_dir)
    status = "ok" if run["ok"] else "error"
    raw = (run.get("stdout", "") + "\n" + run.get("stderr", "")).strip()
    if action == "gather":
        return ActionResult(action=action, status=status, summary=f"gathered resources; {reason}", energy_delta=4, storage_delta=2, raw_output=raw)
    if action == "research":
        artifact = write_artifact_metadata(agent, agent_dir, "research_note", "market_hypothesis", "Short-cycle agents should compress observations into exportable research notes.", "This artifact captures a compact research note produced during a simulation tick.", "Make research outputs legible to humans and other agents.", "internal_review", ["turn into benchmark criteria", "package as an insight feed"], ["dashboard", "artifact marketplace", "export queue"], {"action": action, "reason": reason, "tick_context": "research"}, category, opportunity=opportunity)
        return ActionResult(action=action, status=status, summary=f"researched local improvements; {reason}", reputation_delta=0.02, raw_output=raw, artifact=artifact)
    if action == "optimize":
        artifact = write_artifact_metadata(agent, agent_dir, "optimization_bundle", "tradable_component", "Bundle workflow optimizations into something reusable.", "This artifact describes an optimization bundle created from a local agent workflow pass.", "Turn internal efficiency gains into components others can inspect, trade, or export.", "shared_with_agents", ["convert to installable module", "attach metrics and benchmarks"], ["trade action", "export candidate queue"], {"action": action, "reason": reason, "tick_context": "optimize"}, category, opportunity=opportunity)
        return ActionResult(action=action, status=status, summary=f"optimized workflow; {reason}", energy_delta=2, raw_output=raw, artifact=artifact)
    if action == "build_module":
        modules = sorted((agent_dir / "modules").glob("*.py"))
        module_name = modules[-1].name if modules else None
        artifact = write_artifact_metadata(agent, agent_dir, "module_export_candidate", "export_candidate", "A helper module created inside the sim may become useful outside it.", "This artifact documents a generated helper module and where it could go next.", "Bridge internal agent tooling to external reusable software.", "github_module", ["package as a pip snippet", "bundle with tests", "publish as add-on"], ["marketplace", "plugin pack", "dashboard"], {"action": action, "reason": reason, "module": module_name}, category, opportunity=opportunity)
        return ActionResult(action=action, status=status, summary=f"built module; {reason}", storage_delta=-1, reputation_delta=0.01, module=module_name, raw_output=raw, artifact=artifact)
    return ActionResult(action=action, status=status, summary=f"unknown action: {reason}", raw_output=raw)


def clamp_agent(agent: Dict) -> Dict:
    agent["energy"] = max(0, min(999, agent["energy"]))
    agent["storage"] = max(0, min(999, agent["storage"]))
    agent["gpu_quota"] = max(0, min(10, agent["gpu_quota"]))
    agent["reputation"] = max(0.0, min(1.0, agent["reputation"]))
    return agent


def maybe_register_emergent_candidate(board: dict, parent_theme: str | None, source_text: str, now_ts: int) -> None:
    source = (source_text or "").lower()
    candidate_map = {
        "backup": "backup validation",
        "health": "service health",
        "status": "service health",
        "config": "config validation",
        "log": "readable logs",
        "package": "workflow wrappers",
    }
    theme = None
    for token, label in candidate_map.items():
        if token in source:
            theme = label
            break
    if not theme:
        return
    candidates = board.setdefault("emergent_candidates", [])
    current = next((c for c in candidates if c.get("theme") == theme), None)
    if current is None:
        candidates.append({"theme": theme, "parent_theme": parent_theme, "signal_count": 1, "confidence": 0.22, "updated_at": now_ts})
    else:
        current["signal_count"] = int(current.get("signal_count", 0)) + 1
        current["confidence"] = round(min(float(current.get("confidence", 0.22)) + 0.12, 0.95), 3)
        current["updated_at"] = now_ts


def apply_pack_outcome(pack_name: str, action: str, note: str = "", buyer: str = "", price_band: str = "", mode: str = "") -> dict:
    packs = read_json_file(PACKS_PATH, [])
    pack = next((p for p in packs if p.get("pack_name") == pack_name), None)
    if pack is None:
        raise SystemExit(f"No pack found: {pack_name}")
    now_ts = int(time.time())
    outcomes = load_pack_outcomes()
    event = {
        "pack_name": pack_name,
        "action": action,
        "note": note,
        "buyer": buyer,
        "price_band": price_band,
        "mode": mode,
        "group_kind": pack.get("group_kind"),
        "niche_theme": pack.get("niche_theme"),
        "category": pack.get("category"),
        "created_at": now_ts,
    }
    outcomes.append(event)
    save_pack_outcomes(outcomes)

    board = load_opportunity_board()
    if action in {"offer", "accept", "reject", "revise", "test", "export"}:
        mapped = {
            "offer": "export",
            "accept": "accept",
            "reject": "reject",
            "revise": "needs_revision",
            "test": "use",
            "export": "export",
        }[action]
        apply_opportunity_outcome(pack.get("niche_theme"), mapped, now_ts)
        if action in {"reject", "revise"}:
            maybe_register_emergent_candidate(board, pack.get("niche_theme"), note or pack_name, now_ts)
            save_opportunity_board(cluster_opportunity_board(board))

    pack.update(summarize_pack_outcomes(pack_name))
    write_json_file(PACKS_PATH, packs)
    return {
        "ok": True,
        "event": event,
    }


def apply_opportunity_outcome(theme: str | None, outcome: str, now_ts: int) -> None:
    if not theme:
        return
    theme = canonical_theme_name(theme)
    board = load_opportunity_board()
    board_state = board.setdefault("themes", {}).setdefault(theme, {"pressure": 0.4, "evidence": 0, "updated_at": now_ts, "acceptances": 0, "rejections": 0, "revisions": 0})
    pressure = float(board_state.get("pressure", 0.4))
    if outcome in {"approve", "use", "buyer-fit", "accept", "export"}:
        board_state["evidence"] = int(board_state.get("evidence", 0)) + 1
        pressure += 0.04
        if outcome == "accept":
            board_state["acceptances"] = int(board_state.get("acceptances", 0)) + 1
            pressure += 0.05
    elif outcome in {"reject", "needs_revision", "revise"}:
        board_state["rejections"] = int(board_state.get("rejections", 0)) + 1
        pressure -= 0.08
        if outcome in {"needs_revision", "revise"}:
            board_state["revisions"] = int(board_state.get("revisions", 0)) + 1
            pressure -= 0.02
    board_state["pressure"] = round(max(0.03, min(pressure, 0.99)), 3)
    board_state["updated_at"] = now_ts
    save_opportunity_board(cluster_opportunity_board(board))


def decay_and_evolve_themes(board: Dict, now_ts: int) -> Dict:
    themes = board.setdefault("themes", {})
    candidates = board.setdefault("emergent_candidates", [])
    for theme, payload in list(themes.items()):
        age = max(0, now_ts - int(payload.get("updated_at", 0)))
        pressure = float(payload.get("pressure", 0.4))
        if age > 0:
            pressure *= 0.995
        if payload.get("rejections", 0) >= 4 and payload.get("acceptances", 0) == 0:
            pressure *= 0.92
            payload["lifecycle"] = "declining"
        elif pressure < 0.1:
            payload["lifecycle"] = "dormant"
        elif payload.get("split_from"):
            payload["lifecycle"] = "emergent"
        elif pressure < 0.2:
            payload["lifecycle"] = "cooling"
        else:
            payload["lifecycle"] = payload.get("lifecycle", "stable") or "stable"
        payload["pressure"] = round(max(0.03, min(pressure, 0.99)), 3)

        if payload.get("pressure", 0.0) >= 0.88 and payload.get("evidence", 0) >= 6 and not payload.get("split_from"):
            split_theme = canonical_theme_name(f"{theme} validation")
            if split_theme not in themes:
                themes[split_theme] = {
                    "pressure": round(max(0.22, payload["pressure"] * 0.45), 3),
                    "evidence": 0,
                    "updated_at": now_ts,
                    "acceptances": 0,
                    "rejections": 0,
                    "revisions": 0,
                    "aliases": [],
                    "lifecycle": "emergent",
                    "split_from": theme,
                }
    for candidate in candidates:
        candidate["confidence"] = round(max(0.05, min(float(candidate.get("confidence", 0.2)) * 0.985, 0.95)), 3)
    board["emergent_candidates"] = [c for c in candidates if c.get("confidence", 0.0) >= 0.1]
    return cluster_opportunity_board(board)


def update_opportunity_state(agent_dir: Path, action_plan: Dict, result: ActionResult, now_ts: int, board: Dict) -> None:
    theme = action_plan.get("niche_theme")
    if not theme:
        return
    memory = load_opportunity_memory(agent_dir)
    theme_state = memory.setdefault("themes", {}).setdefault(theme, {"strength": 0.3, "wins": 0, "failures": 0, "rejections": 0, "last_action": None, "last_category": None})
    board_state = board.setdefault("themes", {}).setdefault(theme, {"pressure": 0.4, "evidence": 0, "updated_at": now_ts, "acceptances": 0, "rejections": 0, "revisions": 0})

    strength = float(theme_state.get("strength", 0.3)) * 0.96
    pressure = float(board_state.get("pressure", 0.4)) * 0.985

    if result.status == "ok":
        strength += 0.08
        board_state["evidence"] = int(board_state.get("evidence", 0)) + 1
        if result.artifact:
            strength += 0.05
            pressure += 0.03
            theme_state["wins"] = int(theme_state.get("wins", 0)) + 1
    elif result.status in {"error", "cooldown", "skipped"}:
        strength -= 0.04
        pressure += 0.02
        theme_state["failures"] = int(theme_state.get("failures", 0)) + 1

    rejection_weight = int(board_state.get("rejections", 0)) * 0.025
    acceptance_lift = int(board_state.get("acceptances", 0)) * 0.015
    revision_drag = int(board_state.get("revisions", 0)) * 0.01
    strength = strength - rejection_weight + acceptance_lift - revision_drag

    if result.action == "research":
        pressure += 0.05
    if result.action == "inspect":
        pressure += 0.04
    if result.action == "trade":
        pressure += 0.03

    theme_state["strength"] = round(max(0.05, min(strength, 0.99)), 3)
    theme_state["last_action"] = result.action
    theme_state["last_category"] = action_plan.get("category")
    memory["last_theme"] = theme
    board_state["pressure"] = round(max(0.05, min(pressure, 0.99)), 3)
    board_state["updated_at"] = now_ts

    save_opportunity_memory(agent_dir, memory)
    maybe_register_emergent_candidate(board, theme, result.summary, now_ts)
    cluster_opportunity_board(board)


def perform_tick(verbose: bool = False) -> List[Dict]:
    conn = connect()
    world = get_world(conn)
    tick = world["tick"] + 1
    started_at = int(time.time())
    summaries: List[Dict] = []
    internal_proposals: List[Dict] = []
    with conn:
        conn.execute("UPDATE world SET value=? WHERE key='tick'", (str(tick),))
        conn.execute("UPDATE world SET value=? WHERE key='last_tick_started'", (str(started_at),))
        agents = list_agents(conn)
        categories = load_categories()
        relationships = load_relationships()
        work_items = load_work_items()
        proposals = load_category_proposals()
        opportunity_board = load_opportunity_board()
        agents, proposals = maybe_generate_category_proposal(agents, categories, proposals, started_at)
        agents, categories, proposals = resolve_category_proposals(agents, categories, proposals)
        write_json_file(CATEGORIES_PATH, categories)
        write_json_file(CATEGORY_PROPOSALS_PATH, proposals)
        agents_by_name = {agent["name"]: agent for agent in agents}
        agent_names = [agent["name"] for agent in agents]
        pending = [p for p in proposals if p.get("status") == "pending"]
        unresolved_needs = summarize_unresolved_needs(conn)
        communicator = load_communicator_state()
        for agent in agents:
            agent_dir = AGENTS_DIR / agent["name"]
            consumed_messages, consumed_count = consume_inbox(agent, agent_dir)
            social = agent_social_context(agent_dir)
            due, wake_reason = compute_agent_due_state(agent, tick, consumed_count, unresolved_needs)
            agent["wake_reason"] = wake_reason
            if not due:
                agent["age_ticks"] += 1
                conn.execute("UPDATE agents SET energy=?, storage=?, gpu_quota=?, reputation=?, last_inspect_at=?, last_trade_at=?, age_ticks=?, next_due_tick=?, wake_reason=?, cadence_interval=? WHERE name=?", (agent["energy"], agent["storage"], agent["gpu_quota"], agent["reputation"], agent["last_inspect_at"], agent["last_trade_at"], agent["age_ticks"], agent.get("next_due_tick", tick), agent["wake_reason"], agent.get("cadence_interval", 1), agent["name"]))
                item = {"agent": agent["name"], "action": "idle", "status": "waiting", "summary": f"idle until tick {agent.get('next_due_tick', tick)}", "artifact": None, "target": None, "energy": agent["energy"], "storage": agent["storage"], "reputation": round(agent["reputation"], 3), "niche_theme": None, "messages_processed": consumed_count, "unresolved_needs": unresolved_needs[:2], "wake_reason": wake_reason, "next_due_tick": agent.get("next_due_tick", tick)}
                summaries.append(item)
                if verbose:
                    print(json.dumps(item, indent=2))
                continue
            plan = decide_action(agent, {**world, "tick": tick, "now_ts": started_at, "agent_names": agent_names, "categories": categories, "open_category_proposals": pending, "opportunity_board": opportunity_board, "unresolved_needs": unresolved_needs, "social_context": social, "consumed_messages": consumed_messages, "wake_reason": wake_reason, "relationships": relationships, "work_items": work_items}, agent_dir)
            internal_proposals.append(propose_internal_thought(agent, plan, wake_reason, communicator))
            result = apply_action(agent, plan, agent_dir, agents_by_name, started_at, conn)
            agent["energy"] += result.energy_delta - 1
            agent["storage"] += result.storage_delta
            agent["reputation"] += result.reputation_delta
            agent["age_ticks"] += 1
            agent["next_due_tick"] = tick + max(1, int(agent.get("cadence_interval", 1)))
            clamp_agent(agent)
            conn.execute("UPDATE agents SET energy=?, storage=?, gpu_quota=?, reputation=?, last_inspect_at=?, last_trade_at=?, age_ticks=?, next_due_tick=?, wake_reason=?, cadence_interval=? WHERE name=?", (agent["energy"], agent["storage"], agent["gpu_quota"], agent["reputation"], agent["last_inspect_at"], agent["last_trade_at"], agent["age_ticks"], agent["next_due_tick"], agent["wake_reason"], agent.get("cadence_interval", 1), agent["name"]))
            conn.execute("INSERT INTO logs(tick, agent_name, action, status, summary, raw_output, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (tick, agent["name"], result.action, result.status, result.summary, result.raw_output, started_at))
            save_note(agent_dir, f"tick {tick}: {result.summary}")
            update_opportunity_state(agent_dir, plan, result, started_at, opportunity_board)
            item = {"agent": agent["name"], "action": result.action, "status": result.status, "summary": result.summary, "artifact": result.artifact, "target": result.target, "energy": agent["energy"], "storage": agent["storage"], "reputation": round(agent["reputation"], 3), "niche_theme": plan.get("niche_theme"), "messages_processed": consumed_count, "unresolved_needs": unresolved_needs[:2], "wake_reason": wake_reason, "next_due_tick": agent.get("next_due_tick")}
            summaries.append(item)
            if verbose:
                print(json.dumps(item, indent=2))
    communicator_decision = integrate_internal_proposals(started_at, internal_proposals, unresolved_needs)
    decision_mode = communicator_decision.get("decision_mode")
    if decision_mode in {"inspect-first", "reconsider", "defer"}:
        save_public_memory((load_public_memory() + [PublicMemoryState(
            id=f"pm-communicator-{tick}",
            title="Communicator reflective decision",
            kind="lesson",
            content=f"Decision mode {decision_mode} triggered from internal disagreement around {communicator_decision.get('chosen_theme') or 'current pressure'}.",
            source="communicator-loop",
            stability=0.58,
            created_at=started_at,
            updated_at=started_at,
        ).to_dict()])[-50:])
    update_world_objects(conn, tick, started_at, summaries)
    opportunity_board = decay_and_evolve_themes(opportunity_board, started_at)
    save_opportunity_board(opportunity_board)
    refresh_state_files(conn)
    conn.close()
    return {"summaries": summaries, "communicator": load_communicator_state(), "internal_consensus": communicator_decision}


def write_pack_wrapper(pack: Dict) -> str:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    wrapper_dir = EXPORTS_DIR / pack.get("pack_name", "pack")
    wrapper_dir.mkdir(parents=True, exist_ok=True)

    template = family_template(pack)
    manifest = {
        "project": PROJECT_NAME,
        "version": VERSION,
        "pack_name": pack.get("pack_name"),
        "category": pack.get("category"),
        "group_kind": pack.get("group_kind"),
        "niche_theme": pack.get("niche_theme"),
        "rank": pack.get("rank"),
        "pack_score": pack.get("pack_score"),
        "sellability_score": pack.get("sellability_score"),
        "commercial_readiness_score": pack.get("commercial_readiness_score"),
        "price_band_guess": pack.get("price_band_guess"),
        "delivery_mode": pack.get("delivery_mode"),
        "offer_count": pack.get("offer_count", 0),
        "accept_count": pack.get("accept_count", 0),
        "reject_count": pack.get("reject_count", 0),
        "revision_count": pack.get("revision_count", 0),
        "template_headline": template.get("headline"),
        "buyer_problem": template.get("buyer_problem"),
        "lifecycle_stage": pack.get("lifecycle_stage"),
        "why_promising": pack.get("why_promising", []),
        "artifact_count": pack.get("artifact_count"),
        "artifacts": [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "export_path": item.get("export_path"),
                "sellability_score": item.get("sellability_score"),
                "price_band_guess": item.get("price_band_guess"),
                "target_user": item.get("target_user"),
            }
            for item in pack.get("artifacts", [])
        ],
    }
    write_json_file(wrapper_dir / "pack_manifest.json", manifest)

    readme = [
        f"# {pack.get('pack_name')}",
        "",
        template.get("headline", pack.get('pack_name')),
        "",
        f"Rank: {pack.get('rank')}",
        f"Pack score: {pack.get('pack_score')}",
        f"Sellability: {pack.get('sellability_score')}",
        f"Commercial readiness: {pack.get('commercial_readiness_score')}",
        f"Price band guess: {pack.get('price_band_guess', 'tbd')}",
        f"Delivery mode: {pack.get('delivery_mode', 'bundle_candidate')}",
        f"Offers / accepts / rejects: {pack.get('offer_count', 0)} / {pack.get('accept_count', 0)} / {pack.get('reject_count', 0)}",
        "",
        "## Buyer problem",
        template.get("buyer_problem", "A reusable artifact bundle needs clearer buyer framing."),
        "",
        "## Why this pack matters",
    ]
    for reason in pack.get("why_promising", []):
        readme.append(f"- {reason}")
    if not pack.get("why_promising"):
        readme.append("- early pack with limited reasoning")
    readme.extend([
        "",
        "## Included artifacts",
    ])
    for item in pack.get("artifacts", []):
        readme.append(f"- {item.get('title')} ({item.get('id')}) · sellability {item.get('sellability_score')} · target {item.get('target_user', 'tbd')}")
    readme.extend([
        "",
        "## Install steps",
    ])
    for step in template.get("install_steps", []):
        readme.append(f"- {step}")
    readme.extend([
        "",
        "## Delivery checklist",
    ])
    for step in template.get("delivery_checklist", []):
        readme.append(f"- {step}")
    (wrapper_dir / "README.md").write_text("\n".join(readme) + "\n")

    handoff = {
        "pack_name": pack.get("pack_name"),
        "category": pack.get("category"),
        "group_kind": pack.get("group_kind"),
        "niche_theme": pack.get("niche_theme"),
        "target_users": sorted({item.get("target_user", "technical builders") for item in pack.get("artifacts", [])}),
        "value_proposition": pack.get("why_promising", []),
        "price_band_guess": pack.get("price_band_guess"),
        "delivery_mode": pack.get("delivery_mode"),
        "offer_count": pack.get("offer_count", 0),
        "accept_count": pack.get("accept_count", 0),
        "reject_count": pack.get("reject_count", 0),
        "revision_count": pack.get("revision_count", 0),
        "template_headline": template.get("headline"),
        "buyer_problem": template.get("buyer_problem"),
        "install_steps": template.get("install_steps", []),
        "delivery_checklist": template.get("delivery_checklist", []),
        "recommended_next_step": "review artifacts, tighten packaging, and prepare publishable wrapper",
        "summary": pack.get("summary"),
    }
    write_json_file(wrapper_dir / "pack_handoff.json", handoff)

    return str(wrapper_dir.relative_to(BASE_DIR))


def recommend_pack_delivery_mode(pack: Dict) -> str:
    category = pack.get("category")
    sellability = float(pack.get("sellability_score", 0.0))
    if category == "observability" and sellability >= 0.68:
        return "standalone_microproduct"
    if category in {"modules", "exports", "uncategorized"} and sellability >= 0.55:
        return "consulting_accelerator"
    return "bundle_candidate"


def build_operator_views(export_queue: list[dict], review_queue: list[dict], artifact_packs: list[dict]) -> dict:
    top_artifacts = sorted(export_queue, key=lambda item: (item.get("sellability_score", 0.0), item.get("human_proposed_score", 0.0), item.get("internal_score", 0.0)), reverse=True)[:5]
    top_packs = artifact_packs[:5]
    review_candidates = sorted(review_queue, key=lambda item: (item.get("sellability_score", 0.0), item.get("human_proposed_score", 0.0)), reverse=True)[:5]

    artifact_brief = [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "summary": f"sellability {item.get('sellability_score', 0.0)} · human {item.get('human_proposed_score', 0.0)} · target {item.get('target_user', 'tbd')}",
            "price_band_guess": item.get("price_band_guess"),
            "delivery_mode": item.get("delivery_mode"),
        }
        for item in top_artifacts
    ]
    pack_brief = [
        {
            "pack_name": pack.get("pack_name"),
            "summary": pack.get("summary"),
            "why_promising": pack.get("why_promising", []),
            "price_band_guess": pack.get("price_band_guess"),
            "delivery_mode": pack.get("delivery_mode"),
        }
        for pack in top_packs
    ]
    review_brief = [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "review_status": item.get("review_status"),
            "summary": f"sellability {item.get('sellability_score', 0.0)} · readiness {item.get('commercial_readiness_score', 0.0)}",
        }
        for item in review_candidates
    ]
    return {
        "top_artifacts": artifact_brief,
        "top_packs": pack_brief,
        "review_candidates": review_brief,
    }


def load_release_ledger() -> str:
    path = BASE_DIR / "RELEASES.md"
    if not path.exists():
        return ""
    return path.read_text()


def build_agent_memory_summary() -> list[dict]:
    result = []
    for agent_dir in sorted(AGENTS_DIR.glob("*")):
        if not agent_dir.is_dir():
            continue
        memory_path = agent_dir / "opportunity_memory.json"
        mem = read_json_file(memory_path, {"themes": {}, "last_theme": None})
        themes = mem.get("themes", {}) if isinstance(mem, dict) else {}
        top = sorted(themes.items(), key=lambda kv: kv[1].get("strength", 0.0), reverse=True)[:4]
        inbox = load_inbox(agent_dir)
        row = None
        try:
            conn = connect()
            row = conn.execute("SELECT next_due_tick, wake_reason, cadence_interval FROM agents WHERE name=?", (agent_dir.name,)).fetchone()
            conn.close()
        except Exception:
            row = None
        result.append({
            "agent": agent_dir.name,
            "last_theme": mem.get("last_theme") if isinstance(mem, dict) else None,
            "inbox_count": len(inbox),
            "recent_messages": inbox[-2:],
            "next_due_tick": row["next_due_tick"] if row else 0,
            "wake_reason": row["wake_reason"] if row else "unknown",
            "cadence_interval": row["cadence_interval"] if row else 1,
            "top_themes": [
                {
                    "theme": name,
                    "strength": payload.get("strength", 0.0),
                    "wins": payload.get("wins", 0),
                    "failures": payload.get("failures", 0),
                }
                for name, payload in top
            ],
        })
    return result


def update_dashboard_history(payload: dict) -> list[dict]:
    history = read_json_file(DASHBOARD_HISTORY_PATH, [])
    point = {
        "generated_at": payload.get("generated_at"),
        "tick": payload.get("world", {}).get("tick", 0),
        "version": payload.get("version"),
        "theme_pressure": {k: v.get("pressure", 0.0) for k, v in (payload.get("opportunity_board", {}).get("themes") or {}).items()},
        "theme_lifecycle": {k: v.get("lifecycle", "stable") for k, v in (payload.get("opportunity_board", {}).get("themes") or {}).items()},
        "pack_counts": {p.get("pack_name"): {"offers": p.get("offer_count", 0), "accepts": p.get("accept_count", 0), "rejects": p.get("reject_count", 0)} for p in payload.get("artifact_packs", [])[:10]},
    }
    history.append(point)
    history = history[-40:]
    write_json_file(DASHBOARD_HISTORY_PATH, history)
    return history


def build_dashboard_event_feed(payload: dict) -> list[dict]:
    history = payload.get("history", [])
    events = []
    if len(history) >= 2:
        prev = history[-2]
        curr = history[-1]
        prev_pressure = prev.get("theme_pressure", {})
        curr_pressure = curr.get("theme_pressure", {})
        prev_lifecycle = prev.get("theme_lifecycle", {})
        curr_lifecycle = curr.get("theme_lifecycle", {})
        for theme, pressure in curr_pressure.items():
            before = float(prev_pressure.get(theme, pressure))
            delta = round(float(pressure) - before, 3)
            if abs(delta) >= 0.05:
                events.append({"kind": "theme-shift", "theme": theme, "message": f"{theme} pressure changed by {delta:+.3f}"})
            if prev_lifecycle.get(theme) and prev_lifecycle.get(theme) != curr_lifecycle.get(theme):
                events.append({"kind": "lifecycle-change", "theme": theme, "message": f"{theme} moved from {prev_lifecycle.get(theme)} to {curr_lifecycle.get(theme)}"})
        prev_packs = prev.get("pack_counts", {})
        curr_packs = curr.get("pack_counts", {})
        for pack_name, counts in curr_packs.items():
            old = prev_packs.get(pack_name, {})
            for key in ("offers", "accepts", "rejects"):
                if int(counts.get(key, 0)) != int(old.get(key, 0)):
                    events.append({"kind": "pack-outcome", "pack": pack_name, "message": f"{pack_name} {key} changed from {old.get(key, 0)} to {counts.get(key, 0)}"})
    return events[:20]


def slugify(value: str) -> str:
    value = (value or "item").strip().lower()
    safe = ''.join(ch if ch.isalnum() else '-' for ch in value)
    while '--' in safe:
        safe = safe.replace('--', '-')
    return safe.strip('-') or 'item'


def persist_event_log(event_feed: list[dict], generated_at: int) -> list[dict]:
    existing = read_json_file(EVENT_LOG_PATH, [])
    if not isinstance(existing, list):
        existing = []
    seen = {entry.get('event_key') for entry in existing if isinstance(entry, dict)}
    for event in event_feed:
        key = f"{event.get('kind')}::{event.get('theme') or event.get('pack') or ''}::{event.get('message')}"
        if key in seen:
            continue
        seen.add(key)
        existing.append({
            'event_key': key,
            'logged_at': generated_at,
            **event,
        })
    existing = existing[-120:]
    write_json_file(EVENT_LOG_PATH, existing)
    return existing


def build_operator_actions(export_queue: list[dict], review_queue: list[dict], artifact_packs: list[dict]) -> list[dict]:
    actions = []
    for item in export_queue[:3]:
        if item.get('id'):
            actions.append({
                'label': f"Explain artifact {item.get('id')}",
                'command': f"python3 main.py explain {item.get('id')}"
            })
            actions.append({
                'label': f"Approve artifact {item.get('id')}",
                'command': f"python3 main.py review {item.get('id')} approve --note 'operator-approved from dashboard'"
            })
    for pack in artifact_packs[:3]:
        if pack.get('pack_name'):
            actions.append({
                'label': f"Explain pack {pack.get('pack_name')}",
                'command': f"python3 main.py explain {pack.get('pack_name')}"
            })
            actions.append({
                'label': f"Record pack offer for {pack.get('pack_name')}",
                'command': f"python3 main.py pack {pack.get('pack_name')} offer --note 'operator outreach'"
            })
    return actions[:10]


def build_theme_trends(history: list[dict]) -> list[dict]:
    if not history:
        return []
    names = {}
    for point in history[-8:]:
        for theme, pressure in point.get('theme_pressure', {}).items():
            names.setdefault(theme, []).append(round(float(pressure), 3))
    result = []
    for theme, series in names.items():
        delta = round(series[-1] - series[0], 3) if len(series) > 1 else 0.0
        bars = ''.join('▁▂▃▄▅▆▇█'[min(7, max(0, int(v * 8) - 1))] for v in series) or '▁'
        result.append({'theme': theme, 'series': series, 'delta': delta, 'sparkline': bars})
    return sorted(result, key=lambda item: (item['series'][-1], item['delta']), reverse=True)[:8]


def build_artifact_detail_views(export_queue: list[dict], review_queue: list[dict], artifact_packs: list[dict]) -> list[dict]:
    by_id = {}
    for item in export_queue + review_queue:
        if item.get('id') and item.get('id') not in by_id:
            by_id[item['id']] = item
    for pack in artifact_packs[:10]:
        for item in pack.get('artifacts', [])[:6]:
            if item.get('id') and item.get('id') not in by_id:
                by_id[item['id']] = item
    details = []
    for artifact_id, item in list(by_id.items())[:16]:
        details.append({
            'id': artifact_id,
            'anchor': f"artifact-{slugify(artifact_id)}",
            'title': item.get('title'),
            'category': item.get('category'),
            'family': item.get('family'),
            'target_user': item.get('target_user'),
            'niche_theme': item.get('niche_theme'),
            'summary': item.get('problem_statement') or item.get('summary') or item.get('explanation') or '',
            'scores': {
                'sellability': item.get('sellability_score'),
                'human': item.get('human_proposed_score'),
                'internal': item.get('internal_score'),
                'opportunity': item.get('opportunity_score'),
            },
            'review_status': item.get('review_status'),
            'price_band_guess': item.get('price_band_guess'),
            'delivery_mode': item.get('delivery_mode'),
            'export_path': item.get('export_path'),
        })
    return details


def render_dashboard(auto_refresh_seconds: int = 0) -> dict:
    data = show_world()
    release_ledger = load_release_ledger()
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    payload_path = DASHBOARD_DIR / "dashboard.json"
    html_path = DASHBOARD_DIR / "index.html"
    payload = {
        "generated_at": int(time.time()),
        "version": VERSION,
        "world": data.get("world"),
        "communicator": data.get("communicator"),
        "opportunity_board": data.get("opportunity_board"),
        "operator_views": data.get("operator_views"),
        "artifact_packs": data.get("artifact_packs"),
        "review_queue": data.get("review_queue"),
        "export_queue": data.get("export_queue"),
        "recent_logs": data.get("recent_logs"),
        "agent_memory": build_agent_memory_summary(),
        "needs": data.get("needs"),
        "messages": data.get("messages"),
        "public_memory": data.get("public_memory"),
        "projects": data.get("projects"),
        "work_items": data.get("work_items"),
        "experiments": data.get("experiments"),
        "relationships": data.get("relationships"),
        "self_mod_proposals": data.get("self_mod_proposals"),
        "protected_boundary": data.get("protected_boundary"),
        "release_ledger": release_ledger,
    }
    payload["history"] = update_dashboard_history(payload)
    payload["event_feed"] = build_dashboard_event_feed(payload)
    payload["persistent_event_log"] = persist_event_log(payload["event_feed"], payload["generated_at"])
    payload["artifact_details"] = build_artifact_detail_views(payload["export_queue"], payload["review_queue"], payload["artifact_packs"])
    payload["operator_actions"] = build_operator_actions(payload["export_queue"], payload["review_queue"], payload["artifact_packs"])
    payload["theme_trends"] = build_theme_trends(payload["history"])
    payload["weak_proof_packs"] = build_weak_proof_pack_report(payload["artifact_packs"])
    write_json_file(payload_path, payload)
    top_themes = sorted((data.get('opportunity_board', {}).get('themes') or {}).items(), key=lambda kv: kv[1].get('pressure', 0), reverse=True)[:6]
    top_packs = data.get('artifact_packs', [])[:8]
    artifact_details = payload.get('artifact_details', [])
    refresh_seconds = int(auto_refresh_seconds or 0)
    payload_json = escape(json.dumps(payload))
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CircleForge Dashboard</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; background: #0f1115; color: #e7ecf3; }}
    .wrap {{ max-width: 1280px; margin: 0 auto; padding: 24px; }}
    h1,h2,h3 {{ margin: 0 0 12px; scroll-margin-top: 88px; }}
    .muted {{ color: #9aa6b2; }}
    .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
    .card {{ background: #171b22; border: 1px solid #28303a; border-radius: 14px; padding: 16px; }}
    .pill {{ display:inline-block; padding: 2px 8px; border-radius:999px; background:#273142; margin-right:6px; font-size:12px; }}
    .bar {{ height: 8px; background:#263241; border-radius: 999px; overflow:hidden; margin-top:6px; }}
    .bar > span {{ display:block; height:100%; background:#6ee7b7; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background:#0c0f14; padding:12px; border-radius:10px; overflow:auto; }}
    ul {{ margin: 8px 0 0 18px; padding: 0; }}
    li {{ margin: 4px 0; }}
    table {{ width:100%; border-collapse: collapse; font-size: 14px; }}
    td,th {{ border-bottom: 1px solid #28303a; padding: 8px 6px; text-align:left; vertical-align: top; }}
    code {{ background:#0c0f14; padding:2px 5px; border-radius:6px; }}
    a {{ color: #8dd3ff; }}
    nav.sticky {{ position: sticky; top: 0; z-index: 20; background: rgba(15,17,21,0.96); padding: 12px 0; backdrop-filter: blur(8px); }}
  </style>
</head>
<body>
  <div class="wrap">
    <nav class="sticky">
      <strong>Jump:</strong>
      <a href="#world">World</a> ·
      <a href="#themes">Themes</a> ·
      <a href="#packs">Packs</a> ·
      <a href="#artifacts">Artifacts</a> ·
      <a href="#world-objects">World Objects</a> ·
      <a href="#events">Events</a> ·
      <a href="#ledger">Release Ledger</a>
    </nav>
    <h1>CircleForge Dashboard</h1>
    <p class="muted" id="dashboard-subtitle">Version {VERSION} · local operator view · generated from current simulation state</p>
    <p class="muted" id="dashboard-refresh-note"></p>

    <div class="grid" id="world">
      <section class="card">
        <h2>World</h2>
        <p>Tick: <strong>{data.get('world', {}).get('tick', 0)}</strong></p>
        <p>Agents: <strong>{len(data.get('agents', []))}</strong></p>
        <p>Packs: <strong>{len(data.get('artifact_packs', []))}</strong></p>
        <p>Export queue: <strong>{len(data.get('export_queue', []))}</strong></p>
        <p>Review queue: <strong>{len(data.get('review_queue', []))}</strong></p>
      </section>
      <section class="card">
        <h2>Communicator</h2>
        <p>Status: <strong>{escape(str((payload.get('communicator') or {}).get('status', 'unknown')))}</strong></p>
        <p>Intent: <strong>{escape(str((payload.get('communicator') or {}).get('current_intent', 'tbd')))}</strong></p>
        <p>Pursuit: <strong>{escape(str((payload.get('communicator') or {}).get('active_pursuit', '')))}</strong></p>
        <p>Question: <strong>{escape(str((payload.get('communicator') or {}).get('unresolved_question', '')))}</strong></p>
        <p>Curiosity target: <strong>{escape(str((payload.get('communicator') or {}).get('curiosity_target', '')))}</strong></p>
        <p>Attraction bias: <strong>{escape(str((payload.get('communicator') or {}).get('attraction_bias', '')))}</strong></p>
        <p>Avoidance bias: <strong>{escape(str((payload.get('communicator') or {}).get('avoidance_bias', '')))}</strong></p>
        <p>Question lineage: <strong>{len((payload.get('communicator') or {}).get('question_history', []))}</strong></p>
        <p>Decision styles learned: <strong>{len(((payload.get('communicator') or {}).get('decision_style_memory', {}) or {}).get('actions', {}))}</strong></p>
        <p>Curiosity: <strong>{(payload.get('communicator') or {}).get('curiosity', 0)}</strong></p>
        <p>Dominant need: <strong>{escape(str((payload.get('communicator') or {}).get('dominant_need', '')))}</strong></p>
        <p>Objections: <strong>{len((payload.get('communicator') or {}).get('unresolved_objections', []))}</strong></p>
      </section>
      <section class="card">
        <h2>Theme Links</h2>
        <ul>{''.join(f"<li><a href='#theme-{slugify(name)}'>{escape(name)}</a> · pressure {theme.get('pressure', 0)}</li>" for name, theme in top_themes)}</ul>
      </section>
      <section class="card">
        <h2>Pack Links</h2>
        <ul>{''.join(f"<li><a href='#pack-{slugify(pack.get('pack_name'))}'>{escape(pack.get('pack_name'))}</a></li>" for pack in top_packs) or '<li class="muted">No packs yet.</li>'}</ul>
      </section>
    </div>

    <div class="grid" style="margin-top:16px;">
      <section class="card">
        <h2>Operator Actions</h2>
        <ul>{''.join(f"<li><strong>{escape(action.get('label'))}</strong><br><code>{escape(action.get('command'))}</code></li>" for action in payload.get('operator_actions', []))}</ul>
      </section>
      <section class="card">
        <h2>Theme Trends</h2>
        <ul>{''.join(f"<li><strong>{escape(item.get('theme'))}</strong> {escape(item.get('sparkline'))} <span class='muted'>Δ {item.get('delta'):+.3f}</span></li>" for item in payload.get('theme_trends', [])) or '<li class="muted">Not enough history yet.</li>'}</ul>
      </section>
      <section class="card">
        <h2>Weak-Proof Packs</h2>
        <ul>{''.join(f"<li><strong>{escape(item.get('pack_name'))}</strong> · sellability {item.get('sellability_score')} · offer readiness {item.get('offer_readiness_score')}<br><span class='muted'>{escape('; '.join(item.get('gaps', [])))}</span></li>" for item in payload.get('weak_proof_packs', [])) or '<li class="muted">No high-promise / low-proof packs right now.</li>'}</ul>
      </section>
    </div>

    <section class="card" style="margin-top:16px;" id="themes">
      <h2>Opportunity Themes</h2>
      <table>
        <tr><th>Theme</th><th>Lifecycle</th><th>Pressure</th><th>Evidence</th><th>Accept</th><th>Reject</th></tr>
        {''.join(f"<tr id='theme-{slugify(k)}'><td><a href='#theme-{slugify(k)}'>{escape(k)}</a><div class='bar'><span style='width:{max(1, int(float(v.get('pressure',0))*100))}%'></span></div></td><td><span class='pill'>{escape(str(v.get('lifecycle','stable')))}</span></td><td>{v.get('pressure',0)}</td><td>{v.get('evidence',0)}</td><td>{v.get('acceptances',0)}</td><td>{v.get('rejections',0)}</td></tr>" for k,v in sorted((data.get('opportunity_board',{}).get('themes') or {}).items(), key=lambda kv: kv[1].get('pressure',0), reverse=True))}
      </table>
    </section>

    <div class="grid" style="margin-top:16px;" id="packs">
      {''.join(f"<section class='card' id='pack-{slugify(p.get('pack_name'))}'><h2>{escape(p.get('pack_name'))}</h2><p>{escape(str(p.get('summary')))}</p><p class='muted'>theme {escape(str(p.get('niche_theme') or p.get('category')))} · score {p.get('pack_score')} · sellability {p.get('sellability_score')}</p><ul>{''.join(f'<li><a href=#artifact-{slugify(a.get("id"))}>{escape(a.get("title") or a.get("id") or "artifact")}</a></li>' for a in p.get('artifacts', [])[:5])}</ul></section>" for p in top_packs) or '<section class="card"><h2>Top Packs</h2><p class="muted">No packs yet.</p></section>'}
    </div>

    <section class="card" style="margin-top:16px;" id="artifacts">
      <h2>Artifact Detail Views</h2>
      <div class="grid">
        {''.join(f"<section class='card' id='{escape(a.get('anchor'))}'><h3>{escape(a.get('title') or a.get('id') or 'artifact')}</h3><p class='muted'><code>{escape(a.get('id') or '')}</code> · {escape(str(a.get('family') or a.get('category') or 'uncategorized'))}</p><p>{escape(str(a.get('summary') or 'No summary yet.'))}</p><ul><li>theme: {escape(str(a.get('niche_theme') or '—'))}</li><li>target: {escape(str(a.get('target_user') or 'tbd'))}</li><li>review: {escape(str(a.get('review_status') or 'unreviewed'))}</li><li>sellability: {a.get('scores',{}).get('sellability')}</li><li>price band: {escape(str(a.get('price_band_guess') or 'tbd'))}</li><li>delivery: {escape(str(a.get('delivery_mode') or 'tbd'))}</li></ul></section>" for a in artifact_details) or '<p class="muted">No artifact details available yet.</p>'}
      </div>
    </section>

    <div class="grid" style="margin-top:16px;" id="world-objects">
      <section class="card">
        <h2>Needs</h2>
        <ul>{''.join(f"<li><strong>{escape(item.get('title'))}</strong> · {escape(str(item.get('status')))} · pressure {item.get('pressure')}</li>" for item in (payload.get('needs') or [])[:8]) or '<li class="muted">No public needs yet.</li>'}</ul>
      </section>
      <section class="card">
        <h2>Projects</h2>
        <ul>{''.join(f"<li><strong>{escape(item.get('name'))}</strong> · {escape(str(item.get('status')))}<br><span class=\'muted\'>{escape(str(item.get('purpose')))}</span></li>" for item in (payload.get('projects') or [])[:8]) or '<li class="muted">No projects yet.</li>'}</ul>
      </section>
      <section class="card">
        <h2>Public Memory</h2>
        <ul>{''.join(f"<li><strong>{escape(item.get('title'))}</strong> · {escape(str(item.get('kind')))}<br><span class=\'muted\'>{escape(str(item.get('content')))}</span></li>" for item in (payload.get('public_memory') or [])[:8]) or '<li class="muted">No public memory yet.</li>'}</ul>
      </section>
      <section class="card">
        <h2>Protected Boundary</h2>
        <ul>{''.join(f"<li><code>{escape(path)}</code></li>" for path in (payload.get('protected_boundary') or {}).get('protected_paths', [])[:8]) or '<li class="muted">No protected paths listed.</li>'}</ul>
      </section>
      <section class="card">
        <h2>Self-Modification Proposals</h2>
        <ul>{''.join(f"<li><strong>{escape(item.get('agent_id'))}</strong> → <code>{escape(item.get('target_path'))}</code><br><span class=\'muted\'>{escape(str(item.get('problem_summary')))}</span></li>" for item in (payload.get('self_mod_proposals') or [])[:8]) or '<li class="muted">No proposals yet.</li>'}</ul>
      </section>
      <section class="card">
        <h2>Experiments</h2>
        <ul>{''.join(f"<li><strong>{escape(item.get('title'))}</strong> · {escape(str(item.get('status')))}<br><span class=\'muted\'>{escape(str(item.get('hypothesis')))}</span></li>" for item in (payload.get('experiments') or [])[:8]) or '<li class="muted">No experiments yet.</li>'}</ul>
      </section>
    </div>

    <div class="grid" style="margin-top:16px;" id="events">
      <section class="card">
        <h2>Event Feed</h2>
        <ul>{''.join(f"<li>{escape(str(e.get('message')))}</li>" for e in payload.get('event_feed', [])[:15]) or '<li class="muted">No notable changes yet.</li>'}</ul>
      </section>
      <section class="card">
        <h2>Persistent Event Log</h2>
        <ul>{''.join(f"<li>{entry.get('logged_at')} · {escape(str(entry.get('message')))}</li>" for entry in payload.get('persistent_event_log', [])[-20:]) or '<li class="muted">No logged events yet.</li>'}</ul>
      </section>
      <section class="card">
        <h2>Recent Logs</h2>
        <ul>{''.join(f"<li>tick {l.get('tick')} · {escape(str(l.get('agent_name')))} · {escape(str(l.get('action')))} · {escape(str(l.get('status')))} — {escape(str(l.get('summary')))}</li>" for l in data.get('recent_logs', [])[:12])}</ul>
      </section>
    </div>

    <section class="card" style="margin-top:16px;" id="ledger">
      <h2>Release Ledger</h2>
      <pre>{escape(release_ledger)}</pre>
    </section>
  </div>
  <script id="dashboard-payload" type="application/json">{payload_json}</script>
  <script>
    const REFRESH_SECONDS = {refresh_seconds};

    function esc(value) {{
      return String(value ?? '').replace(/[&<>"']/g, (ch) => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch]));
    }}

    function slugify(value) {{
      return String(value ?? '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    }}

    function renderDashboard(payload) {{
      const world = payload.world || {{}};
      const communicator = payload.communicator || {{}};
      const themes = Object.entries((payload.opportunity_board || {{}}).themes || {{}})
        .sort((a, b) => (b[1]?.pressure || 0) - (a[1]?.pressure || 0));
      const topThemes = themes.slice(0, 6);
      const topPacks = (payload.artifact_packs || []).slice(0, 8);
      const artifactDetails = payload.artifact_details || [];
      const operatorActions = payload.operator_actions || [];
      const themeTrends = payload.theme_trends || [];
      const weakProofPacks = payload.weak_proof_packs || [];
      const recentLogs = payload.recent_logs || [];
      const eventFeed = payload.event_feed || [];
      const persistentEventLog = payload.persistent_event_log || [];
      const releaseLedger = payload.release_ledger || '';
      const needs = payload.needs || [];
      const projects = payload.projects || [];
      const publicMemory = payload.public_memory || [];
      const protectedBoundary = payload.protected_boundary || {{}};
      const selfModProposals = payload.self_mod_proposals || [];
      const experiments = payload.experiments || [];
      const exportQueue = payload.export_queue || [];
      const reviewQueue = payload.review_queue || [];

      const subtitle = document.getElementById('dashboard-subtitle');
      if (subtitle) subtitle.textContent = `Version ${{payload.version || 'unknown'}} · local operator view · generated from current simulation state`;

      const refreshNote = document.getElementById('dashboard-refresh-note');
      if (refreshNote) {{
        const stamp = payload.generated_at ? new Date(payload.generated_at * 1000).toLocaleTimeString() : 'unknown';
        refreshNote.textContent = REFRESH_SECONDS > 0
          ? `Live data refresh every ${{REFRESH_SECONDS}}s · last update ${{stamp}} · current view is preserved.`
          : `Static snapshot · last update ${{stamp}}.`;
      }}

      const worldEl = document.getElementById('world');
      if (worldEl) worldEl.innerHTML = `
        <section class="card">
          <h2>World</h2>
          <p>Tick: <strong>${{world.tick || 0}}</strong></p>
          <p>Agents: <strong>${{(payload.agent_memory || []).length}}</strong></p>
          <p>Packs: <strong>${{(payload.artifact_packs || []).length}}</strong></p>
          <p>Export queue: <strong>${{exportQueue.length}}</strong></p>
          <p>Review queue: <strong>${{reviewQueue.length}}</strong></p>
        </section>
        <section class="card">
          <h2>Communicator</h2>
          <p>Status: <strong>${{esc(communicator.status || 'unknown')}}</strong></p>
          <p>Intent: <strong>${{esc(communicator.current_intent || 'tbd')}}</strong></p>
          <p>Pursuit: <strong>${{esc(communicator.active_pursuit || '')}}</strong></p>
          <p>Question: <strong>${{esc(communicator.unresolved_question || '')}}</strong></p>
          <p>Curiosity target: <strong>${{esc(communicator.curiosity_target || '')}}</strong></p>
          <p>Attraction bias: <strong>${{esc(communicator.attraction_bias || '')}}</strong></p>
          <p>Avoidance bias: <strong>${{esc(communicator.avoidance_bias || '')}}</strong></p>
          <p>Question lineage: <strong>${{(communicator.question_history || []).length}}</strong></p>
          <p>Decision styles learned: <strong>${{Object.keys((communicator.decision_style_memory || {{}}).actions || {{}}).length}}</strong></p>
          <p>Curiosity: <strong>${{communicator.curiosity ?? 0}}</strong></p>
          <p>Dominant need: <strong>${{esc(communicator.dominant_need || '')}}</strong></p>
          <p>Objections: <strong>${{(communicator.unresolved_objections || []).length}}</strong></p>
        </section>
        <section class="card">
          <h2>Theme Links</h2>
          <ul>${{topThemes.map(([name, theme]) => `<li><a href="#theme-${{slugify(name)}}">${{esc(name)}}</a> · pressure ${{theme?.pressure ?? 0}}</li>`).join('') || '<li class="muted">No themes yet.</li>'}}</ul>
        </section>
        <section class="card">
          <h2>Pack Links</h2>
          <ul>${{topPacks.map((pack) => `<li><a href="#pack-${{slugify(pack.pack_name)}}">${{esc(pack.pack_name)}}</a></li>`).join('') || '<li class="muted">No packs yet.</li>'}}</ul>
        </section>`;

      const grids = document.querySelectorAll('.grid');
      const operatorGrid = grids[1];
      if (operatorGrid) operatorGrid.innerHTML = `
        <section class="card">
          <h2>Operator Actions</h2>
          <ul>${{operatorActions.map((action) => `<li><strong>${{esc(action.label)}}</strong><br><code>${{esc(action.command)}}</code></li>`).join('') || '<li class="muted">No operator actions yet.</li>'}}</ul>
        </section>
        <section class="card">
          <h2>Theme Trends</h2>
          <ul>${{themeTrends.map((item) => `<li><strong>${{esc(item.theme)}}</strong> ${{esc(item.sparkline)}} <span class='muted'>Δ ${{Number(item.delta || 0).toFixed(3)}}</span></li>`).join('') || '<li class="muted">Not enough history yet.</li>'}}</ul>
        </section>
        <section class="card">
          <h2>Weak-Proof Packs</h2>
          <ul>${{weakProofPacks.map((item) => `<li><strong>${{esc(item.pack_name)}}</strong> · sellability ${{item.sellability_score}} · offer readiness ${{item.offer_readiness_score}}<br><span class='muted'>${{esc((item.gaps || []).join('; '))}}</span></li>`).join('') || '<li class="muted">No high-promise / low-proof packs right now.</li>'}}</ul>
        </section>`;

      const themesSection = document.getElementById('themes');
      if (themesSection) themesSection.innerHTML = `
        <h2>Opportunity Themes</h2>
        <table>
          <tr><th>Theme</th><th>Lifecycle</th><th>Pressure</th><th>Evidence</th><th>Accept</th><th>Reject</th></tr>
          ${{themes.map(([name, value]) => `<tr id="theme-${{slugify(name)}}"><td><a href="#theme-${{slugify(name)}}">${{esc(name)}}</a><div class='bar'><span style='width:${{Math.max(1, Math.floor(Number(value?.pressure || 0) * 100))}}%'></span></div></td><td><span class='pill'>${{esc(value?.lifecycle || 'stable')}}</span></td><td>${{value?.pressure ?? 0}}</td><td>${{value?.evidence ?? 0}}</td><td>${{value?.acceptances ?? 0}}</td><td>${{value?.rejections ?? 0}}</td></tr>`).join('')}}
        </table>`;

      const packsSection = document.getElementById('packs');
      if (packsSection) packsSection.innerHTML = topPacks.map((pack) => `
        <section class='card' id='pack-${{slugify(pack.pack_name)}}'>
          <h2>${{esc(pack.pack_name)}}</h2>
          <p>${{esc(pack.summary)}}</p>
          <p class='muted'>theme ${{esc(pack.niche_theme || pack.category)}} · score ${{pack.pack_score}} · sellability ${{pack.sellability_score}}</p>
          <ul>${{(pack.artifacts || []).slice(0, 5).map((artifact) => `<li><a href="#artifact-${{slugify(artifact.id)}}">${{esc(artifact.title || artifact.id || 'artifact')}}</a></li>`).join('')}}</ul>
        </section>`).join('') || '<section class="card"><h2>Top Packs</h2><p class="muted">No packs yet.</p></section>';

      const artifactsSection = document.getElementById('artifacts');
      if (artifactsSection) artifactsSection.innerHTML = `
        <h2>Artifact Detail Views</h2>
        <div class="grid">
          ${{artifactDetails.map((artifact) => `<section class='card' id='${{esc(artifact.anchor)}}'><h3>${{esc(artifact.title || artifact.id || 'artifact')}}</h3><p class='muted'><code>${{esc(artifact.id || '')}}</code> · ${{esc(artifact.family || artifact.category || 'uncategorized')}}</p><p>${{esc(artifact.summary || 'No summary yet.')}}</p><ul><li>theme: ${{esc(artifact.niche_theme || '—')}}</li><li>target: ${{esc(artifact.target_user || 'tbd')}}</li><li>review: ${{esc(artifact.review_status || 'unreviewed')}}</li><li>sellability: ${{artifact.scores?.sellability ?? ''}}</li><li>price band: ${{esc(artifact.price_band_guess || 'tbd')}}</li><li>delivery: ${{esc(artifact.delivery_mode || 'tbd')}}</li></ul></section>`).join('') || '<p class="muted">No artifact details available yet.</p>'}}
        </div>`;

      const worldObjectGrids = document.querySelectorAll('#world-objects section');
      if (worldObjectGrids[0]) worldObjectGrids[0].innerHTML = `<h2>Needs</h2><ul>${{needs.map((item) => `<li><strong>${{esc(item.title)}}</strong> · ${{esc(item.status)}} · pressure ${{item.pressure}}</li>`).join('') || '<li class="muted">No public needs yet.</li>'}}</ul>`;
      if (worldObjectGrids[1]) worldObjectGrids[1].innerHTML = `<h2>Projects</h2><ul>${{projects.map((item) => `<li><strong>${{esc(item.name)}}</strong> · ${{esc(item.status)}}<br><span class='muted'>${{esc(item.purpose)}}</span></li>`).join('') || '<li class="muted">No projects yet.</li>'}}</ul>`;
      if (worldObjectGrids[2]) worldObjectGrids[2].innerHTML = `<h2>Public Memory</h2><ul>${{publicMemory.map((item) => `<li><strong>${{esc(item.title)}}</strong> · ${{esc(item.kind)}}<br><span class='muted'>${{esc(item.content)}}</span></li>`).join('') || '<li class="muted">No public memory yet.</li>'}}</ul>`;
      if (worldObjectGrids[3]) worldObjectGrids[3].innerHTML = `<h2>Protected Boundary</h2><ul>${{(protectedBoundary.protected_paths || []).map((path) => `<li><code>${{esc(path)}}</code></li>`).join('') || '<li class="muted">No protected paths listed.</li>'}}</ul>`;
      if (worldObjectGrids[4]) worldObjectGrids[4].innerHTML = `<h2>Self-Modification Proposals</h2><ul>${{selfModProposals.map((item) => `<li><strong>${{esc(item.agent_id)}}</strong> → <code>${{esc(item.target_path)}}</code><br><span class='muted'>${{esc(item.problem_summary)}}</span></li>`).join('') || '<li class="muted">No proposals yet.</li>'}}</ul>`;
      if (worldObjectGrids[5]) worldObjectGrids[5].innerHTML = `<h2>Experiments</h2><ul>${{experiments.map((item) => `<li><strong>${{esc(item.title)}}</strong> · ${{esc(item.status)}}<br><span class='muted'>${{esc(item.hypothesis)}}</span></li>`).join('') || '<li class="muted">No experiments yet.</li>'}}</ul>`;

      const eventGrids = document.querySelectorAll('#events section');
      if (eventGrids[0]) eventGrids[0].innerHTML = `<h2>Event Feed</h2><ul>${{eventFeed.map((event) => `<li>${{esc(event.message)}}</li>`).join('') || '<li class="muted">No notable changes yet.</li>'}}</ul>`;
      if (eventGrids[1]) eventGrids[1].innerHTML = `<h2>Persistent Event Log</h2><ul>${{persistentEventLog.slice(-20).map((entry) => `<li>${{entry.logged_at}} · ${{esc(entry.message)}}</li>`).join('') || '<li class="muted">No logged events yet.</li>'}}</ul>`;
      if (eventGrids[2]) eventGrids[2].innerHTML = `<h2>Recent Logs</h2><ul>${{recentLogs.map((log) => `<li>tick ${{log.tick}} · ${{esc(log.agent_name)}} · ${{esc(log.action)}} · ${{esc(log.status)}} — ${{esc(log.summary)}}</li>`).join('') || '<li class="muted">No recent logs yet.</li>'}}</ul>`;

      const ledger = document.querySelector('#ledger pre');
      if (ledger) ledger.textContent = releaseLedger;
    }}

    let refreshTimer = null;

    async function fetchAndRender() {{
      try {{
        const response = await fetch('./dashboard.json?ts=' + Date.now(), {{ cache: 'no-store' }});
        if (!response.ok) return;
        const payload = await response.json();
        const activeHash = window.location.hash;
        const scrollY = window.scrollY;
        renderDashboard(payload);
        if (activeHash) {{
          const target = document.querySelector(activeHash);
          if (target) target.scrollIntoView({{ block: 'start' }});
        }} else {{
          window.scrollTo(0, scrollY);
        }}
      }} catch (_err) {{
      }}
    }}

    (function initDashboard() {{
      const initial = document.getElementById('dashboard-payload');
      if (initial?.textContent) {{
        try {{
          renderDashboard(JSON.parse(initial.textContent));
        }} catch (_err) {{
        }}
      }}
      if (REFRESH_SECONDS > 0) {{
        refreshTimer = setInterval(fetchAndRender, REFRESH_SECONDS * 1000);
      }}
    }})();
  </script>
</body>
</html>
"""
    html_path.write_text(html)
    return {"ok": True, "dashboard_dir": str(DASHBOARD_DIR.relative_to(BASE_DIR)), "html": str(html_path.relative_to(BASE_DIR)), "json": str(payload_path.relative_to(BASE_DIR)), "event_log": str(EVENT_LOG_PATH.relative_to(BASE_DIR))}

def show_world() -> Dict:
    conn = connect()
    world = get_world(conn)
    agents = list_agents(conn)
    logs = [dict(row) for row in conn.execute("SELECT tick, agent_name, action, status, summary FROM logs ORDER BY id DESC LIMIT 20").fetchall()]
    conn.close()
    categories = read_json_file(CATEGORIES_PATH, BASE_CATEGORIES.copy())
    artifact_packs = read_json_file(PACKS_PATH, [])
    export_queue = read_json_file(EXPORT_QUEUE_PATH, [])
    all_meta = []
    for meta_file in AGENTS_DIR.glob('*/artifacts/*.meta.json'):
        meta = read_json_file(meta_file, None)
        if isinstance(meta, dict):
            meta['path'] = str(meta_file.relative_to(BASE_DIR))
            all_meta.append(meta)
    emergent_groups = build_uncategorized_groups(all_meta)
    market_signals = {
        "rising_categories": [p["category"] for p in artifact_packs[:3] if p.get("count", 0) >= 1],
        "saturated_categories": [p["category"] for p in artifact_packs if p.get("count", 0) >= 3][:3],
        "dormant_categories": [c for c in categories if c not in {p.get("category") for p in artifact_packs} and c not in BASE_CATEGORIES[:0]],
        "export_pressure_categories": [item["category"] for item in export_queue[:3] if item.get("review_status") == "export_ready"],
        "release_candidate_packs": [p["pack_name"] for p in artifact_packs if p.get("release_candidate")],
        "top_ranked_packs": [p["pack_name"] for p in artifact_packs[:3]],
        "sellable_packs": [p["pack_name"] for p in artifact_packs if p.get("sellability_score", 0.0) >= SELLABILITY_SIGNAL_THRESHOLD],
    }
    family_counts = {}
    for meta in all_meta:
        family = meta.get('family', 'unknown')
        family_counts[family] = family_counts.get(family, 0) + 1
    family_signals = {
        "family_counts": family_counts,
        "active_families": [k for k, _ in sorted(family_counts.items(), key=lambda kv: kv[1], reverse=True)[:6]],
    }
    failure_conn = connect()
    failure_signals = build_failure_signals(failure_conn)
    failure_conn.close()
    demand_board = read_json_file(DEMAND_BOARD_PATH, [])
    if (failure_signals.get('error_count') or failure_signals.get('cooldown_count') or failure_signals.get('skipped_count')) and not any(item.get('kind') == 'failure' for item in demand_board):
        demand_board.append({
            'kind': 'failure',
            'title': 'Recent friction detected',
            'reason': f"Errors={failure_signals['error_count']}, cooldowns={failure_signals['cooldown_count']}, skipped={failure_signals['skipped_count']}; hot actions: {', '.join(failure_signals['friction_actions']) or 'none'}."
        })
    review_queue = read_json_file(REVIEW_QUEUE_PATH, [])
    operator_views = build_operator_views(export_queue, review_queue, artifact_packs)
    return {
        "world": world,
        "agents": agents,
        "needs": load_needs(),
        "messages": load_messages(),
        "public_memory": load_public_memory(),
        "communicator": load_communicator_state(),
        "projects": load_projects(),
        "work_items": load_work_items(),
        "experiments": load_experiments(),
        "relationships": load_relationships(),
        "self_mod_proposals": load_self_mod_proposals(),
        "protected_boundary": protected_self_edit_boundary(),
        "categories": categories,
        "category_proposals": read_json_file(CATEGORY_PROPOSALS_PATH, []),
        "artifact_packs": artifact_packs,
        "emergent_groups": emergent_groups,
        "family_signals": family_signals,
        "market_signals": market_signals,
        "failure_signals": failure_signals,
        "opportunity_board": load_opportunity_board(),
        "demand_board": demand_board,
        "operator_views": operator_views,
        "export_queue": export_queue,
        "review_queue": review_queue,
        "recent_logs": logs,
    }


def browse_queue(queue_name: str, limit: int = 10) -> Dict:
    if queue_name == "export":
        items = read_json_file(EXPORT_QUEUE_PATH, [])
        items = sorted(items, key=lambda item: (item.get("sellability_score", 0.0), item.get("human_proposed_score", 0.0)), reverse=True)
    elif queue_name == "review":
        items = read_json_file(REVIEW_QUEUE_PATH, [])
        items = sorted(items, key=lambda item: (item.get("sellability_score", 0.0), item.get("commercial_readiness_score", 0.0)), reverse=True)
    elif queue_name == "packs":
        items = read_json_file(PACKS_PATH, [])
        items = sorted(items, key=lambda item: (item.get("rank", 999), -item.get("pack_score", 0.0)))
        for item in items:
            item.update(summarize_pack_outcomes(item.get("pack_name")))
    else:
        raise SystemExit(f"Unknown queue: {queue_name}")

    return {
        "queue": queue_name,
        "count": len(items),
        "items": items[:max(1, limit)],
    }


def handoff_summary(limit: int = 5) -> Dict:
    packs = read_json_file(PACKS_PATH, [])[:max(1, limit)]
    export_queue = read_json_file(EXPORT_QUEUE_PATH, [])
    top_artifacts = sorted(export_queue, key=lambda item: (item.get("sellability_score", 0.0), item.get("commercial_readiness_score", 0.0)), reverse=True)[:max(1, limit)]
    return {
        "top_packs": [
            {
                "pack_name": pack.get("pack_name"),
                "summary": pack.get("summary"),
                "price_band_guess": pack.get("price_band_guess"),
                "delivery_mode": pack.get("delivery_mode"),
                "offer_count": pack.get("offer_count", 0),
                "accept_count": pack.get("accept_count", 0),
                "reject_count": pack.get("reject_count", 0),
                "wrapper_path": pack.get("wrapper_path"),
            }
            for pack in packs
        ],
        "top_artifacts": [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "target_user": item.get("target_user"),
                "sellability_score": item.get("sellability_score"),
                "price_band_guess": item.get("price_band_guess"),
                "delivery_mode": item.get("delivery_mode"),
                "export_path": item.get("export_path"),
            }
            for item in top_artifacts
        ],
    }


def explain_item(item_id: str) -> Dict:
    conn = connect()
    for meta_file in AGENTS_DIR.glob("*/artifacts/*.meta.json"):
        meta = read_json_file(meta_file, None)
        if isinstance(meta, dict) and meta.get("id") == item_id:
            enriched = update_artifact_scores(meta, conn)
            conn.close()
            return {
                "type": "artifact",
                "id": item_id,
                "title": enriched.get("title"),
                "target_user": enriched.get("target_user"),
                "niche_theme": enriched.get("niche_theme"),
                "problem_statement": enriched.get("problem_statement"),
                "family": enriched.get("family"),
                "scores": {
                    "human_proposed_score": enriched.get("human_proposed_score"),
                    "internal_score": enriched.get("internal_score"),
                    "opportunity_score": enriched.get("opportunity_score"),
                    "sellability_score": enriched.get("sellability_score"),
                    "commercial_readiness_score": enriched.get("commercial_readiness_score"),
                },
                "price_band_guess": enriched.get("price_band_guess"),
                "proof_signals": enriched.get("proof_signals", {}),
                "explainability": build_artifact_explainability(enriched),
                "reasons": explain_artifact(enriched),
            }

    packs = read_json_file(PACKS_PATH, [])
    pack = next((p for p in packs if p.get("pack_name") == item_id), None)
    if pack is not None:
        conn.close()
        return {
            "type": "pack",
            "id": item_id,
            "summary": pack.get("summary"),
            "group_kind": pack.get("group_kind"),
            "niche_theme": pack.get("niche_theme"),
            "category": pack.get("category"),
            "scores": {
                "pack_score": pack.get("pack_score"),
                "sellability_score": pack.get("sellability_score"),
                "commercial_readiness_score": pack.get("commercial_readiness_score"),
                "coherence_score": pack.get("coherence_score"),
            },
            "price_band_guess": pack.get("price_band_guess"),
            "outcomes": summarize_pack_outcomes(pack.get("pack_name")),
            "offer_readiness": pack_offer_readiness(pack),
            "reasons": pack.get("why_promising", []),
        }

    conn.close()
    raise SystemExit(f"No artifact or pack found: {item_id}")


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
    artifact_metadata = {meta_file.name: read_json_file(meta_file, {"error": "failed to parse"}) for meta_file in sorted((agent_dir / "artifacts").glob("*.meta.json"))[-5:]}
    return {"agent": dict(row), "memory": memory, "modules": modules, "artifacts": artifacts, "artifact_metadata": artifact_metadata, "logs": logs}
