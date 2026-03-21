from __future__ import annotations

import json
import shutil
import sqlite3
import time
from html import escape
from pathlib import Path
from typing import Dict, List

from agent_runtime import decide_action, load_opportunity_memory, save_note, save_opportunity_memory
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
    OPPORTUNITY_BOARD_PATH,
    PACK_OUTCOMES_PATH,
    PACKS_PATH,
    PACK_MIN_RELEASE_ARTIFACTS,
    PACK_RELEASE_CANDIDATE_THRESHOLD,
    PROJECT_NAME,
    REVIEW_QUEUE_PATH,
    SELLABILITY_SIGNAL_THRESHOLD,
    STARTING_ENERGY,
    STARTING_GPU,
    STARTING_REPUTATION,
    STARTING_STORAGE,
    TICK_SECONDS,
    VERSION,
)
from models import ActionResult, AgentState
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
    return conn


def read_json_file(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def write_json_file(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


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


def compute_human_proposed_score(meta: Dict) -> float:
    q = compute_quality_dimensions(meta)
    return round(min((q["clarity_score"] + q["novelty_score"] + q["exportability_score"] + q["market_fit_score"]) / 4, 0.99), 3)


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
    commercial_readiness = min(0.99, round((meta.get("human_proposed_score", 0.0) * 0.16) + (proof_level * 0.3) + (buyer_clarity * 0.12) + (pain_severity * 0.1) + ((1 - deployment_effort) * 0.08) + (opportunity_score * 0.16) + validation_bonus, 3))
    sellability_score = min(0.99, round((buyer_clarity * 0.18) + (pain_severity * 0.16) + ((1 - deployment_effort) * 0.1) + (proof_level * 0.18) + ((1 - support_burden) * 0.05) + (commercial_readiness * 0.13) + (opportunity_score * 0.16) + validation_bonus, 3))

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
    meta.update(compute_quality_dimensions(meta))
    meta["internal_score"] = compute_internal_score(meta)
    meta["human_proposed_score"] = compute_human_proposed_score(meta)
    meta.update(compute_opportunity_signals(meta))
    meta.update(compute_sellability_signals(meta))
    meta["external_validation_state"] = meta.get("proof_signals", {}).get("external_validation_state", "unvalidated")
    meta["delivery_mode"] = recommend_delivery_mode(meta)
    return meta


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
        conn.execute("INSERT INTO world(key, value) VALUES (?, ?)", ("tick", "0"))
        conn.execute("INSERT INTO world(key, value) VALUES (?, ?)", ("last_tick_started", "0"))
        for i in range(1, agent_count + 1):
            name = f"agent-{i}"
            agent_dir = AGENTS_DIR / name
            for sub in ["modules", "artifacts"]:
                (agent_dir / sub).mkdir(parents=True, exist_ok=True)
            (agent_dir / "memory.json").write_text("[]")
            state = AgentState(name=name, energy=STARTING_ENERGY, storage=STARTING_STORAGE, gpu_quota=STARTING_GPU, reputation=STARTING_REPUTATION)
            conn.execute("INSERT INTO agents(name, energy, storage, gpu_quota, reputation, last_inspect_at, last_trade_at, age_ticks) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (state.name, state.energy, state.storage, state.gpu_quota, state.reputation, state.last_inspect_at, state.last_trade_at, state.age_ticks))
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
    raw = json.dumps({"target": target["name"], "reputation": target["reputation"], "storage": target["storage"], "age_ticks": target["age_ticks"], "module_count": len(modules), "artifact_count": len(artifacts), "sample_modules": modules[:3], "sample_artifacts": artifacts[:3]}, indent=2)
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
    conn.execute("UPDATE agents SET energy=?, storage=?, gpu_quota=?, reputation=?, last_inspect_at=?, last_trade_at=?, age_ticks=? WHERE name=?", (target["energy"], target["storage"], target["gpu_quota"], target["reputation"], target["last_inspect_at"], target["last_trade_at"], target["age_ticks"], target["name"]))
    raw = json.dumps({"from": actor["name"], "to": target["name"], "offer": {"storage": 3}, "received_effect": {"energy": 2, "reputation": 0.02}, "target_effect": {"storage": 2, "reputation": 0.01}}, indent=2)
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
    with conn:
        conn.execute("UPDATE world SET value=? WHERE key='tick'", (str(tick),))
        conn.execute("UPDATE world SET value=? WHERE key='last_tick_started'", (str(started_at),))
        agents = list_agents(conn)
        categories = load_categories()
        proposals = load_category_proposals()
        opportunity_board = load_opportunity_board()
        agents, proposals = maybe_generate_category_proposal(agents, categories, proposals, started_at)
        agents, categories, proposals = resolve_category_proposals(agents, categories, proposals)
        write_json_file(CATEGORIES_PATH, categories)
        write_json_file(CATEGORY_PROPOSALS_PATH, proposals)
        agents_by_name = {agent["name"]: agent for agent in agents}
        agent_names = [agent["name"] for agent in agents]
        pending = [p for p in proposals if p.get("status") == "pending"]
        for agent in agents:
            agent_dir = AGENTS_DIR / agent["name"]
            plan = decide_action(agent, {**world, "tick": tick, "now_ts": started_at, "agent_names": agent_names, "categories": categories, "open_category_proposals": pending, "opportunity_board": opportunity_board}, agent_dir)
            result = apply_action(agent, plan, agent_dir, agents_by_name, started_at, conn)
            agent["energy"] += result.energy_delta - 1
            agent["storage"] += result.storage_delta
            agent["reputation"] += result.reputation_delta
            agent["age_ticks"] += 1
            clamp_agent(agent)
            conn.execute("UPDATE agents SET energy=?, storage=?, gpu_quota=?, reputation=?, last_inspect_at=?, last_trade_at=?, age_ticks=? WHERE name=?", (agent["energy"], agent["storage"], agent["gpu_quota"], agent["reputation"], agent["last_inspect_at"], agent["last_trade_at"], agent["age_ticks"], agent["name"]))
            conn.execute("INSERT INTO logs(tick, agent_name, action, status, summary, raw_output, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (tick, agent["name"], result.action, result.status, result.summary, result.raw_output, started_at))
            save_note(agent_dir, f"tick {tick}: {result.summary}")
            update_opportunity_state(agent_dir, plan, result, started_at, opportunity_board)
            item = {"agent": agent["name"], "action": result.action, "status": result.status, "summary": result.summary, "artifact": result.artifact, "target": result.target, "energy": agent["energy"], "storage": agent["storage"], "reputation": round(agent["reputation"], 3), "niche_theme": plan.get("niche_theme")}
            summaries.append(item)
            if verbose:
                print(json.dumps(item, indent=2))
    opportunity_board = decay_and_evolve_themes(opportunity_board, started_at)
    save_opportunity_board(opportunity_board)
    refresh_state_files(conn)
    conn.close()
    return summaries


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
        result.append({
            "agent": agent_dir.name,
            "last_theme": mem.get("last_theme") if isinstance(mem, dict) else None,
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


def render_dashboard() -> dict:
    data = show_world()
    release_ledger = load_release_ledger()
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    payload_path = DASHBOARD_DIR / "dashboard.json"
    html_path = DASHBOARD_DIR / "index.html"
    payload = {
        "generated_at": int(time.time()),
        "version": VERSION,
        "world": data.get("world"),
        "opportunity_board": data.get("opportunity_board"),
        "operator_views": data.get("operator_views"),
        "artifact_packs": data.get("artifact_packs"),
        "review_queue": data.get("review_queue"),
        "export_queue": data.get("export_queue"),
        "recent_logs": data.get("recent_logs"),
        "agent_memory": build_agent_memory_summary(),
        "release_ledger": release_ledger,
    }
    payload["history"] = update_dashboard_history(payload)
    payload["event_feed"] = build_dashboard_event_feed(payload)
    payload["persistent_event_log"] = persist_event_log(payload["event_feed"], payload["generated_at"])
    payload["artifact_details"] = build_artifact_detail_views(payload["export_queue"], payload["review_queue"], payload["artifact_packs"])
    write_json_file(payload_path, payload)
    top_themes = sorted((data.get('opportunity_board', {}).get('themes') or {}).items(), key=lambda kv: kv[1].get('pressure', 0), reverse=True)[:6]
    top_packs = data.get('artifact_packs', [])[:8]
    artifact_details = payload.get('artifact_details', [])
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
      <a href="#events">Events</a> ·
      <a href="#ledger">Release Ledger</a>
    </nav>
    <h1>CircleForge Dashboard</h1>
    <p class="muted">Version {VERSION} · local operator view · generated from current simulation state</p>

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
        <h2>Theme Links</h2>
        <ul>{''.join(f"<li><a href='#theme-{slugify(name)}'>{escape(name)}</a> · pressure {theme.get('pressure', 0)}</li>" for name, theme in top_themes)}</ul>
      </section>
      <section class="card">
        <h2>Pack Links</h2>
        <ul>{''.join(f"<li><a href='#pack-{slugify(pack.get('pack_name'))}'>{escape(pack.get('pack_name'))}</a></li>" for pack in top_packs) or '<li class="muted">No packs yet.</li>'}</ul>
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
