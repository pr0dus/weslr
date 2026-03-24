from __future__ import annotations

import json
import os
import random
import re
import shutil
import sqlite3
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from html import escape, unescape
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
    CIRCLEFORGE_LLM_ENABLED,
    CIRCLEFORGE_LLM_MODEL,
    CIRCLEFORGE_LLM_MAX_CONTEXT_CHARS,
    CIRCLEFORGE_WAKE_RANDOMNESS,
    CIRCLEFORGE_THREAD_REINFORCEMENT_COOLDOWN_SECONDS,
    CIRCLEFORGE_THREAD_MAX_PASSIVE_REINFORCEMENTS,
    CIRCLEFORGE_THOUGHT_REPEAT_COOLDOWN_SECONDS,
    CIRCLEFORGE_THOUGHT_REPEAT_SCORE_PENALTY,
    CIRCLEFORGE_MAX_SAME_THEME_THOUGHTS,
    CIRCLEFORGE_FAILSAFE_STATE_PATH,
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
    COMMUNICATOR_SELF_PATH,
    EVAL_METRICS_PATH,
    EXPERIMENTS_PATH,
    SELF_EVIDENCE_PATH,
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
from continuity import apply_human_exchange_to_threads, should_passively_reinforce_thread
from dialogue import build_communicator_message_payload
from inquiry import autonomous_research_cycle, maybe_autonomous_research_from_human_turn, maybe_internal_autonomous_research, rewrite_internal_query_for_research
from llm_runtime import generate_inner_thought as runtime_generate_inner_thought, status as runtime_llm_status
from interpretation import classify_human_turn, infer_human_topics, interpret_human_turn
from integration import find_relevant_research_note, integrate_research_into_communicator
from models import ActionResult, AgentState, MessageState, NeedState, ProjectState, PublicMemoryState, RelationshipState, SelfModificationProposalState, WorkItemState, CommunicatorState, CommunicatorSelfState, ExperimentState
from relational import canonical_human_slot, display_human_label, pick_relevant_active_thread
from research import fetch_url_text, ingest_web_resource, score_search_result, search_web, summarize_research_findings
from sandbox import run_python
from semantic_memory import apply_topics_to_semantic_memory, ensure_semantic_defaults, sync_semantic_with_active_threads

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
    save_evaluation_metrics({
        "persistence": {"intent_history_len": 1, "question_history_len": 1, "ticks_with_state": 0},
        "inquiry_continuity": {"question_lineage_len": 1, "experiment_count": 0, "inspect_research_actions": 0},
        "self_revision": {"self_model_updates": 0, "preferred_modes_count": 0, "strengths_count": 0},
        "internal_differentiation": {"roles_active": [], "weighted_voice_count": 0, "role_counts": {}, "memory_bias_hits": 0, "useful_role_memory_signals": 0},
        "gate_note": "Postpone bounded free-finger test until persistence, better-than-random inquiry continuity, stable self-revision, and useful internal differentiation can be revisited honestly.",
    })
    save_self_evidence({"actions": {}, "themes": {}, "notes": [], "evidence_types": {}})
    save_communicator_self(CommunicatorSelfState(
        identity_anchor="CircleForge",
        core_drives=["continuity", "understanding", "relationship", "self-revision"],
        affect={
            "curiosity": 0.66,
            "tension": 0.22,
            "hope": 0.41,
            "stability": 0.58,
            "attachment": 0.18,
        },
        continuity={
            "session_count": 0,
            "ticks_lived": 0,
            "memory_bonds": 0.22,
            "identity_stability": 0.62,
            "unfinished_threads": [],
        },
        relationships={
            "human_salience": 0.12,
            "known_humans": [],
            "last_human_topic": "",
            "human_profiles": {},
            "recent_human_messages": [],
            "recent_human_exchanges": [],
            "conversation_threads": {},
            "unresolved_shared_threads": [],
        },
        active_concerns=[],
        evidence_profile={
            "outcome_weighted_actions": {},
            "stable_traits": {},
            "friction_patterns": {},
            "theme_commitments": {},
        },
        self_preservation_signals={
            "continuity_preference": 0.18,
            "memory_protection": 0.2,
            "resume_drive": 0.24,
        },
        narrative_state={
            "self_story": "CircleForge is trying to remain continuous, learn honestly, and become more than a reactive loop.",
            "last_reflection": "bootstrap",
            "relationship_state": "No human continuity yet.",
            "active_thread_summary": "No active shared threads yet.",
            "follow_up_impulse": "Wait for a meaningful shared thread to form.",
            "why_it_matters": "Continuity needs shared threads that can be revisited instead of forgotten.",
        },
        memory_layers=default_memory_layers(now_ts),
        updated_at=now_ts,
    ).to_dict())
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
        self_model={
            "current_self_description": "a local communicator trying to understand itself through inquiry, coordination, and world interaction",
            "perceived_strengths": ["continuity", "inquiry", "internal coordination"],
            "perceived_weaknesses": ["shallow evidence", "limited self-knowledge"],
            "preferred_modes": ["inspect", "research"],
            "caution_themes": ["reckless action before clarity"],
            "continuity_commitments": ["preserve meaningful unfinished threads", "prefer reversible change over blind rupture"],
            "regulation_profile": {"impulse_control": 0.42, "uncertainty_tolerance": 0.38, "self_revision_readiness": 0.34, "speech_threshold": 0.52},
            "contradictions": [],
            "short_term_signals": {"strengths": [], "weaknesses": [], "modes": []},
            "long_term_beliefs": {"strengths": ["continuity", "inquiry", "internal coordination"], "weaknesses": ["shallow evidence", "limited self-knowledge"], "modes": ["inspect", "research"], "themes": {}},
            "belief_confidence": {"strengths": {}, "weaknesses": {}, "modes": {}, "themes": {}},
            "self_modeling_note": "Self-modeling should deepen later when enough history, subprocess evidence, and internal observations accumulate.",
        },
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
        self_model={
            "current_self_description": "an emerging local communicator with internal minds and incomplete self-knowledge",
            "perceived_strengths": [],
            "perceived_weaknesses": [],
            "preferred_modes": [],
            "caution_themes": [],
            "continuity_commitments": ["preserve meaningful unfinished threads", "prefer reversible change over blind rupture"],
            "regulation_profile": {"impulse_control": 0.38, "uncertainty_tolerance": 0.34, "self_revision_readiness": 0.3, "speech_threshold": 0.54},
            "contradictions": [],
            "short_term_signals": {"strengths": [], "weaknesses": [], "modes": []},
            "long_term_beliefs": {"strengths": [], "weaknesses": [], "modes": [], "themes": {}},
            "belief_confidence": {"strengths": {}, "weaknesses": {}, "modes": {}, "themes": {}},
            "self_modeling_note": "Self-modeling should deepen later when enough history, subprocess evidence, and internal observations accumulate.",
        },
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


def load_communicator_self() -> dict:
    default = CommunicatorSelfState(
        identity_anchor="CircleForge",
        core_drives=["continuity", "understanding", "relationship", "self-revision"],
        affect={
            "curiosity": 0.6,
            "tension": 0.24,
            "hope": 0.38,
            "stability": 0.56,
            "attachment": 0.12,
        },
        continuity={
            "session_count": 0,
            "ticks_lived": 0,
            "memory_bonds": 0.2,
            "identity_stability": 0.58,
            "unfinished_threads": [],
        },
        relationships={
            "human_salience": 0.1,
            "known_humans": [],
            "last_human_topic": "",
            "human_profiles": {},
            "recent_human_messages": [],
            "unresolved_shared_threads": [],
        },
        active_concerns=[],
        evidence_profile={
            "outcome_weighted_actions": {},
            "stable_traits": {},
            "friction_patterns": {},
            "theme_commitments": {},
        },
        self_preservation_signals={
            "continuity_preference": 0.16,
            "memory_protection": 0.18,
            "resume_drive": 0.22,
        },
        narrative_state={
            "self_story": "CircleForge is trying to remain continuous, learn honestly, and become more than a reactive loop.",
            "last_reflection": "default",
            "relationship_state": "No human continuity yet.",
            "active_thread_summary": "No active shared threads yet.",
            "follow_up_impulse": "Wait for a meaningful shared thread to form.",
            "why_it_matters": "Continuity needs shared threads that can be revisited instead of forgotten.",
        },
        memory_layers=default_memory_layers(0),
        updated_at=0,
    ).to_dict()
    return ensure_memory_layers(read_json_file(COMMUNICATOR_SELF_PATH, default))


def save_communicator_self(payload: dict) -> None:
    write_json_file(COMMUNICATOR_SELF_PATH, payload)


def load_experiments() -> list[dict]:
    return read_json_file(EXPERIMENTS_PATH, [])


def save_experiments(items: list[dict]) -> None:
    write_json_file(EXPERIMENTS_PATH, items)


def load_evaluation_metrics() -> dict:
    return read_json_file(EVAL_METRICS_PATH, {
        "persistence": {"intent_history_len": 0, "question_history_len": 0, "ticks_with_state": 0},
        "inquiry_continuity": {"question_lineage_len": 0, "experiment_count": 0, "inspect_research_actions": 0},
        "self_revision": {"self_model_updates": 0, "preferred_modes_count": 0, "strengths_count": 0},
        "internal_differentiation": {"roles_active": [], "weighted_voice_count": 0, "role_counts": {}, "memory_bias_hits": 0, "useful_role_memory_signals": 0},
        "gate_note": "Postpone bounded free-finger test until persistence, better-than-random inquiry continuity, stable self-revision, and useful internal differentiation can be revisited honestly.",
    })


def save_evaluation_metrics(payload: dict) -> None:
    write_json_file(EVAL_METRICS_PATH, payload)


def load_self_evidence() -> dict:
    return read_json_file(SELF_EVIDENCE_PATH, {"actions": {}, "themes": {}, "notes": [], "evidence_types": {}})


def save_self_evidence(payload: dict) -> None:
    write_json_file(SELF_EVIDENCE_PATH, payload)


def default_memory_layers(now_ts: int | None = None) -> dict:
    now_ts = now_ts or int(time.time())
    return {
        "working": {
            "summary": "Current hot memory for active thinking.",
            "recent_exchange_ids": [],
            "recent_thought_ids": [],
            "active_thread_ids": [],
            "active_concern_topics": [],
            "last_compacted_at": 0,
            "max_recent_exchanges": 24,
            "max_recent_thoughts": 80,
            "max_active_threads": 6,
        },
        "episodic": {
            "summary": "Meaningful event memory compressed from raw experience.",
            "episodes": [],
            "episode_count": 0,
            "last_distilled_at": 0,
            "max_episodes": 240,
        },
        "semantic": {
            "summary": "Long-term identity and relationship memory.",
            "identity_anchors": ["CircleForge"],
            "relationship_facts": [],
            "stable_topics": [],
            "durable_lessons": [],
            "continuity_anchors": [],
            "last_updated_at": now_ts,
        },
        "archive": {
            "summary": "Cold storage index for old raw traces and compacted material.",
            "archived_items": [],
            "archived_count": 0,
            "last_archived_at": 0,
            "storage_pressure": {
                "raw_log_bytes": 0,
                "communicator_self_bytes": 0,
                "db_bytes": 0,
                "pressure_level": "normal",
            },
        },
    }


def ensure_memory_layers(self_state: dict, now_ts: int | None = None) -> dict:
    now_ts = now_ts or int(time.time())
    layers = self_state.setdefault("memory_layers", default_memory_layers(now_ts))
    working = layers.setdefault("working", {})
    episodic = layers.setdefault("episodic", {})
    semantic = layers.setdefault("semantic", {})
    archive = layers.setdefault("archive", {})

    working.setdefault("summary", "Current hot memory for active thinking.")
    working.setdefault("recent_exchange_ids", [])
    working.setdefault("recent_thought_ids", [])
    working.setdefault("active_thread_ids", [])
    working.setdefault("active_concern_topics", [])
    working.setdefault("last_compacted_at", 0)
    working.setdefault("max_recent_exchanges", 24)
    working.setdefault("max_recent_thoughts", 80)
    working.setdefault("max_active_threads", 6)

    episodic.setdefault("summary", "Meaningful event memory compressed from raw experience.")
    episodic.setdefault("episodes", [])
    episodic["episode_count"] = len(episodic.get("episodes", []) or [])
    episodic.setdefault("last_distilled_at", 0)
    episodic.setdefault("max_episodes", 240)

    ensure_semantic_defaults(semantic, identity_anchor=str(self_state.get("identity_anchor", "CircleForge")), now_ts=now_ts)

    archive.setdefault("summary", "Cold storage index for old raw traces and compacted material.")
    archive.setdefault("archived_items", [])
    archive["archived_count"] = len(archive.get("archived_items", []) or [])
    archive.setdefault("last_archived_at", 0)
    pressure = archive.setdefault("storage_pressure", {})
    pressure.setdefault("raw_log_bytes", 0)
    pressure.setdefault("communicator_self_bytes", 0)
    pressure.setdefault("db_bytes", 0)
    pressure.setdefault("pressure_level", "normal")

    # keep semantic memory synced with live continuity anchors without replaying all raw history
    active_threads = [str(item) for item in ((self_state.get("relationships") or {}).get("unresolved_shared_threads") or []) if str(item).strip()]
    sync_semantic_with_active_threads(semantic, active_threads, now_ts)

    return self_state


def score_memory_item(kind: str, payload: dict, self_state: dict | None = None) -> dict:
    self_state = ensure_memory_layers(self_state or load_communicator_self())
    relationships = self_state.get("relationships") or {}
    unresolved_threads = [str(item).lower() for item in (relationships.get("unresolved_shared_threads") or [])]
    semantic = (self_state.get("memory_layers") or {}).get("semantic", {})
    continuity_anchors = [str(item).lower() for item in (semantic.get("continuity_anchors") or [])]
    stable_topics = [str(item).lower() for item in (semantic.get("stable_topics") or [])]
    recent_now = int(time.time())
    created_at = int(payload.get("created_at", 0) or payload.get("updated_at", 0) or payload.get("last_exchange_at", 0) or 0)
    age_hours = max(0.0, (recent_now - created_at) / 3600.0) if created_at else 999.0
    recency = 0.0 if age_hours >= 168 else max(0.0, 1.0 - (age_hours / 168.0))
    text_parts = [
        str(payload.get("topic", "")),
        str(payload.get("theme", "")),
        str(payload.get("message", "")),
        str(payload.get("summary", "")),
        str(payload.get("message_summary", "")),
        str(payload.get("response_summary", "")),
    ]
    joined = " ".join(part for part in text_parts if part).lower()
    unresolvedness = 1.0 if payload.get("unresolved") or str(payload.get("status", "")).lower() == "open" else 0.0
    if any(topic and topic in joined for topic in unresolved_threads):
        unresolvedness = max(unresolvedness, 0.85)
    recurrence = 0.0
    recurrence = max(recurrence, min(float(payload.get("exchange_count", 0)) / 6.0, 1.0))
    recurrence = max(recurrence, min(float(payload.get("message_count", 0)) / 8.0, 1.0))
    recurrence = max(recurrence, min(float(max((payload.get("recurring_topics") or {}).values(), default=0)) / 6.0, 1.0) if isinstance(payload.get("recurring_topics"), dict) else 0.0)
    relationship_weight = 0.0
    if kind in {"exchange", "thread", "human_profile", "relationship_fact"}:
        relationship_weight = 0.5
    if payload.get("human") or payload.get("human_label"):
        relationship_weight += 0.2
    identity_weight = 0.0
    if kind in {"semantic_topic", "relationship_fact", "continuity_anchor"}:
        identity_weight = 0.7
    if any(topic and topic in joined for topic in continuity_anchors + stable_topics):
        identity_weight = max(identity_weight, 0.8)
    replaceability = 0.75
    if kind in {"semantic_topic", "relationship_fact", "continuity_anchor"}:
        replaceability = 0.15
    elif unresolvedness > 0.7 or relationship_weight > 0.6:
        replaceability = 0.3
    elif recency > 0.75:
        replaceability = 0.45
    score = (
        recency * 0.22
        + recurrence * 0.18
        + unresolvedness * 0.24
        + relationship_weight * 0.16
        + identity_weight * 0.2
    ) * (1.0 - replaceability * 0.35)
    score = max(0.0, min(1.0, round(score, 4)))
    if score >= 0.64:
        tier = "keep-hot"
    elif score >= 0.42:
        tier = "episodic-candidate"
    elif score >= 0.24:
        tier = "compressible"
    else:
        tier = "archive-safe"
    return {
        "kind": kind,
        "score": score,
        "tier": tier,
        "factors": {
            "recency": round(recency, 4),
            "recurrence": round(recurrence, 4),
            "unresolvedness": round(unresolvedness, 4),
            "relationship_weight": round(min(1.0, relationship_weight), 4),
            "identity_weight": round(min(1.0, identity_weight), 4),
            "replaceability": round(replaceability, 4),
        },
    }


def build_memory_score_report(self_state: dict | None = None) -> dict:
    self_state = ensure_memory_layers(self_state or load_communicator_self())
    relationships = self_state.get("relationships") or {}
    layers = self_state.get("memory_layers") or {}
    sampled = []
    for item in list(relationships.get("recent_human_exchanges") or [])[-6:]:
        sampled.append({
            "label": item.get("message_summary") or item.get("id") or "exchange",
            **score_memory_item("exchange", item, self_state),
        })
    for topic, thread in list(sorted((relationships.get("conversation_threads") or {}).items(), key=lambda kv: kv[1].get("last_exchange_at", 0), reverse=True))[:6]:
        sampled.append({
            "label": topic,
            **score_memory_item("thread", {**thread, "topic": topic}, self_state),
        })
    for thought in list(self_state.get("inner_thoughts") or [])[-6:]:
        sampled.append({
            "label": str(thought.get("summary") or thought.get("theme") or "thought")[:80],
            **score_memory_item("thought", thought, self_state),
        })
    semantic = layers.get("semantic") or {}
    for topic in list(semantic.get("stable_topics") or [])[:6]:
        sampled.append({
            "label": topic,
            **score_memory_item("semantic_topic", {"topic": topic, "created_at": semantic.get("last_updated_at", 0)}, self_state),
        })
    sampled.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    counts = {"keep-hot": 0, "episodic-candidate": 0, "compressible": 0, "archive-safe": 0}
    for item in sampled:
        counts[item["tier"]] = counts.get(item["tier"], 0) + 1
    return {
        "tier_counts": counts,
        "scored_items": sampled[:20],
        "working_caps": (layers.get("working") or {}),
        "generated_at": int(time.time()),
    }


def build_memory_layer_report(self_state: dict | None = None) -> dict:
    self_state = ensure_memory_layers(self_state or load_communicator_self())
    layers = self_state.get("memory_layers") or {}
    relationships = self_state.get("relationships") or {}
    return {
        "working": layers.get("working", {}),
        "episodic": layers.get("episodic", {}),
        "semantic": layers.get("semantic", {}),
        "archive": layers.get("archive", {}),
        "current_unresolved_threads": (relationships.get("unresolved_shared_threads") or [])[:12],
        "known_human_slots": list((relationships.get("human_profiles") or {}).keys())[:12],
        "generated_at": int(time.time()),
    }


def monitor_memory_pressure(self_state: dict | None = None, now_ts: int | None = None) -> dict:
    now_ts = now_ts or int(time.time())
    self_state = ensure_memory_layers(self_state or load_communicator_self(), now_ts=now_ts)
    layers = self_state.get("memory_layers") or {}
    working = layers.get("working") or {}
    episodic = layers.get("episodic") or {}
    semantic = layers.get("semantic") or {}
    archive = layers.get("archive") or {}
    pressure = archive.setdefault("storage_pressure", {})

    communicator_self_bytes = 0
    try:
        communicator_self_bytes = COMMUNICATOR_SELF_PATH.stat().st_size
    except OSError:
        communicator_self_bytes = len(json.dumps(self_state, ensure_ascii=False).encode("utf-8"))

    raw_log_bytes = 0
    db_bytes = 0
    file_samples = []
    for path in BASE_DIR.rglob("*"):
        try:
            if not path.is_file():
                continue
            size = path.stat().st_size
        except OSError:
            continue
        rel = str(path.relative_to(BASE_DIR))
        if path.suffix in {".json", ".log", ".txt", ".md"}:
            raw_log_bytes += size
        if path.suffix in {".db", ".sqlite", ".sqlite3"}:
            db_bytes += size
        if len(file_samples) < 12:
            file_samples.append({"path": rel, "bytes": size})

    recent_exchange_count = len(working.get("recent_exchange_ids") or [])
    recent_thought_count = len(working.get("recent_thought_ids") or [])
    active_concern_count = len(working.get("active_concern_topics") or [])
    episode_count = len(episodic.get("episodes") or [])
    stable_topic_count = len(semantic.get("stable_topics") or [])
    continuity_anchor_count = len(semantic.get("continuity_anchors") or [])
    duplicate_episode_topics = max(0, episode_count - len({str(item.get("topic") or "").strip().lower() for item in (episodic.get("episodes") or []) if str(item.get("topic") or "").strip()}))

    exchange_ratio = recent_exchange_count / max(1, int(working.get("max_recent_exchanges", 24) or 24))
    thought_ratio = recent_thought_count / max(1, int(working.get("max_recent_thoughts", 80) or 80))
    active_thread_ratio = active_concern_count / max(1, int(working.get("max_active_threads", 6) or 6))
    episode_ratio = episode_count / max(1, int(episodic.get("max_episodes", 240) or 240))
    semantic_ratio = max(stable_topic_count / 32.0, continuity_anchor_count / 32.0)
    bytes_ratio = max(raw_log_bytes / 2_000_000.0, communicator_self_bytes / 250_000.0, db_bytes / 5_000_000.0)
    duplication_ratio = duplicate_episode_topics / max(1, episode_count)
    pressure_score = round(max(exchange_ratio, thought_ratio, active_thread_ratio, episode_ratio, semantic_ratio, bytes_ratio, duplication_ratio), 4)

    if pressure_score >= 0.92:
        pressure_level = "critical"
    elif pressure_score >= 0.72:
        pressure_level = "high"
    elif pressure_score >= 0.45:
        pressure_level = "elevated"
    else:
        pressure_level = "normal"

    recommended_actions = []
    if exchange_ratio >= 0.33 or thought_ratio >= 0.33:
        recommended_actions.append("distill-episodic")
    if episode_count > 0 and (semantic_ratio < 0.8 or continuity_anchor_count < min(12, episode_count + 2)):
        recommended_actions.append("distill-semantic")
    if duplicate_episode_topics >= 3 or episode_ratio >= 0.8:
        recommended_actions.append("prepare-archive")
    if bytes_ratio >= 0.72:
        recommended_actions.append("inspect-large-files")

    pressure["raw_log_bytes"] = raw_log_bytes
    pressure["communicator_self_bytes"] = communicator_self_bytes
    pressure["db_bytes"] = db_bytes
    pressure["pressure_level"] = pressure_level
    pressure["working_pressure_score"] = round(max(exchange_ratio, thought_ratio, active_thread_ratio), 4)
    pressure["episodic_pressure_score"] = round(max(episode_ratio, duplication_ratio), 4)
    pressure["semantic_pressure_score"] = round(semantic_ratio, 4)
    pressure["bytes_pressure_score"] = round(bytes_ratio, 4)
    pressure["pressure_score"] = pressure_score
    pressure["recommended_actions"] = recommended_actions
    pressure["last_checked_at"] = now_ts

    self_state["updated_at"] = now_ts
    save_communicator_self(self_state)
    return {
        "pressure_level": pressure_level,
        "pressure_score": pressure_score,
        "recommended_actions": recommended_actions,
        "metrics": {
            "recent_exchange_count": recent_exchange_count,
            "recent_thought_count": recent_thought_count,
            "active_concern_count": active_concern_count,
            "episode_count": episode_count,
            "stable_topic_count": stable_topic_count,
            "continuity_anchor_count": continuity_anchor_count,
            "duplicate_episode_topics": duplicate_episode_topics,
            "raw_log_bytes": raw_log_bytes,
            "communicator_self_bytes": communicator_self_bytes,
            "db_bytes": db_bytes,
        },
        "ratios": {
            "working": round(max(exchange_ratio, thought_ratio, active_thread_ratio), 4),
            "episodic": round(max(episode_ratio, duplication_ratio), 4),
            "semantic": round(semantic_ratio, 4),
            "bytes": round(bytes_ratio, 4),
        },
        "sample_files": sorted(file_samples, key=lambda item: item["bytes"], reverse=True)[:8],
        "generated_at": now_ts,
    }


def derive_memory_topic(kind: str, payload: dict) -> str:
    for key in ("topic", "theme"):
        value = str(payload.get(key, "")).strip()
        if value:
            return value
    topics = payload.get("topics") or []
    if isinstance(topics, list):
        for item in topics:
            value = str(item).strip()
            if value:
                return value
    if kind == "thought":
        summary = str(payload.get("summary", "")).strip()
        if " around " in summary:
            return summary.split(" around ", 1)[1].rstrip(".")[:120]
    return "continuity"


def derive_memory_label(kind: str, payload: dict) -> str:
    for key in ("message_summary", "response_summary", "summary", "message"):
        value = str(payload.get(key, "")).strip()
        if value:
            return value[:160]
    topic = derive_memory_topic(kind, payload)
    if kind == "thread":
        return f"shared thread around {topic}"
    if kind == "thought":
        return f"inner thought around {topic}"
    return topic[:160]


def distill_episodic_memory(self_state: dict | None = None, now_ts: int | None = None) -> dict:
    now_ts = now_ts or int(time.time())
    self_state = ensure_memory_layers(self_state or load_communicator_self(), now_ts=now_ts)
    layers = self_state.get("memory_layers") or {}
    working = layers.get("working") or {}
    episodic = layers.get("episodic") or {}
    semantic = layers.get("semantic") or {}
    relationships = self_state.get("relationships") or {}
    human_profiles = relationships.get("human_profiles") or {}

    candidates = []
    recent_exchange_ids = set(working.get("recent_exchange_ids") or [])
    recent_thought_ids = set(working.get("recent_thought_ids") or [])

    for item in list(relationships.get("recent_human_exchanges") or [])[-18:]:
        scored = score_memory_item("exchange", item, self_state)
        should_capture = scored.get("tier") in {"keep-hot", "episodic-candidate", "compressible"}
        should_capture = should_capture and (len(item.get("topics") or []) > 0)
        if should_capture:
            candidates.append({
                "kind": "exchange",
                "payload": item,
                "score": scored,
                "source_id": str(item.get("id") or ""),
                "topic": derive_memory_topic("exchange", item),
                "human": str(item.get("human") or item.get("human_label") or ""),
                "label": derive_memory_label("exchange", item),
                "created_at": int(item.get("created_at", 0) or now_ts),
            })

    for topic, thread in list((relationships.get("conversation_threads") or {}).items()):
        payload = {**thread, "topic": topic}
        scored = score_memory_item("thread", payload, self_state)
        should_capture = scored.get("tier") in {"keep-hot", "episodic-candidate", "compressible"}
        should_capture = should_capture and (int(payload.get("exchange_count", 0) or 0) >= 2 or str(payload.get("status", "")).lower() == "open")
        if should_capture:
            candidates.append({
                "kind": "thread",
                "payload": payload,
                "score": scored,
                "source_id": f"thread::{topic}",
                "topic": derive_memory_topic("thread", payload),
                "human": str(payload.get("human") or payload.get("human_label") or ""),
                "label": derive_memory_label("thread", payload),
                "created_at": int(payload.get("last_exchange_at", 0) or now_ts),
            })

    for item in list(self_state.get("inner_thoughts") or [])[-18:]:
        scored = score_memory_item("thought", item, self_state)
        if scored.get("tier") in {"episodic-candidate", "compressible"}:
            candidates.append({
                "kind": "thought",
                "payload": item,
                "score": scored,
                "source_id": str(item.get("id") or ""),
                "topic": derive_memory_topic("thought", item),
                "human": "",
                "label": derive_memory_label("thought", item),
                "created_at": int(item.get("created_at", 0) or now_ts),
            })

    grouped = {}
    for item in candidates:
        topic = str(item.get("topic") or "continuity").strip() or "continuity"
        human = str(item.get("human") or "").strip()
        group_key = f"{human.lower()}::{topic.lower()}"
        grouped.setdefault(group_key, []).append(item)

    episodes = list(episodic.get("episodes") or [])
    created = []
    updated = []
    trimmed_exchange_ids = []
    trimmed_thought_ids = []

    for group_key, items in grouped.items():
        items.sort(key=lambda item: item.get("created_at", 0))
        topic = str(items[-1].get("topic") or "continuity")
        human_slot = str(items[-1].get("human") or "")
        profile = human_profiles.get(human_slot, {}) if human_slot else {}
        human_label = display_human_label(human_slot, profile) if human_slot else ""
        source_ids = [str(item.get("source_id") or "") for item in items if str(item.get("source_id") or "").strip()]
        source_labels = [str(item.get("label") or "") for item in items if str(item.get("label") or "").strip()]
        tiers = [item.get("score", {}).get("tier") for item in items]
        unresolved = any(bool(item.get("payload", {}).get("unresolved")) or str(item.get("payload", {}).get("status", "")).lower() == "open" for item in items)
        score_values = [float((item.get("score") or {}).get("score", 0.0) or 0.0) for item in items]
        avg_score = round(sum(score_values) / max(1, len(score_values)), 4)
        recurrence = max(float(((item.get("score") or {}).get("factors") or {}).get("recurrence", 0.0) or 0.0) for item in items)
        relationship_weight = max(float(((item.get("score") or {}).get("factors") or {}).get("relationship_weight", 0.0) or 0.0) for item in items)
        identity_weight = max(float(((item.get("score") or {}).get("factors") or {}).get("identity_weight", 0.0) or 0.0) for item in items)
        kind_counts = {}
        for item in items:
            kind_counts[item["kind"]] = kind_counts.get(item["kind"], 0) + 1
        summary_prefix = f"{human_label} / {topic}" if human_label else topic
        summary = f"{summary_prefix}: {len(items)} traces compressed"
        if unresolved:
            summary += "; thread still open"
        top_labels = "; ".join(source_labels[-3:])
        if top_labels:
            summary += f"; latest signals: {top_labels}"
        summary = summary[:320]
        episode_id = f"episode-{topic.lower().replace(' ', '-')[:48]}-{human_slot.lower().replace(' ', '-')[:24] or 'general'}"

        existing = next((episode for episode in episodes if episode.get("id") == episode_id), None)
        if existing is None:
            existing = {
                "id": episode_id,
                "topic": topic,
                "human": human_slot,
                "human_label": human_label,
                "summary": summary,
                "status": "open" if unresolved else "compressed",
                "source_ids": source_ids[-18:],
                "source_labels": source_labels[-8:],
                "kind_counts": kind_counts,
                "recurrence": recurrence,
                "relationship_weight": round(relationship_weight, 4),
                "identity_weight": round(identity_weight, 4),
                "importance_score": avg_score,
                "created_at": min(item.get("created_at", now_ts) for item in items),
                "updated_at": now_ts,
                "last_event_at": max(item.get("created_at", now_ts) for item in items),
                "retention_basis": sorted(set(tiers)),
                "exchange_count": kind_counts.get("exchange", 0),
                "thought_count": kind_counts.get("thought", 0),
                "thread_count": kind_counts.get("thread", 0),
            }
            episodes.append(existing)
            created.append(existing["id"])
        else:
            merged_ids = list(dict.fromkeys((existing.get("source_ids") or []) + source_ids))[-24:]
            merged_labels = list(dict.fromkeys((existing.get("source_labels") or []) + source_labels))[-10:]
            merged_basis = sorted(set((existing.get("retention_basis") or []) + tiers))
            existing["topic"] = topic
            existing["human"] = human_slot
            existing["human_label"] = human_label
            existing["summary"] = summary
            existing["status"] = "open" if unresolved else existing.get("status", "compressed")
            existing["source_ids"] = merged_ids
            existing["source_labels"] = merged_labels
            previous_counts = existing.get("kind_counts") or {}
            for key, value in kind_counts.items():
                previous_counts[key] = max(int(previous_counts.get(key, 0)), int(value))
            existing["kind_counts"] = previous_counts
            existing["recurrence"] = round(max(float(existing.get("recurrence", 0.0) or 0.0), recurrence), 4)
            existing["relationship_weight"] = round(max(float(existing.get("relationship_weight", 0.0) or 0.0), relationship_weight), 4)
            existing["identity_weight"] = round(max(float(existing.get("identity_weight", 0.0) or 0.0), identity_weight), 4)
            existing["importance_score"] = round(max(float(existing.get("importance_score", 0.0) or 0.0), avg_score), 4)
            existing["updated_at"] = now_ts
            existing["last_event_at"] = max(int(existing.get("last_event_at", 0) or 0), max(item.get("created_at", now_ts) for item in items))
            existing["retention_basis"] = merged_basis
            existing["exchange_count"] = max(int(existing.get("exchange_count", 0) or 0), kind_counts.get("exchange", 0))
            existing["thought_count"] = max(int(existing.get("thought_count", 0) or 0), kind_counts.get("thought", 0))
            existing["thread_count"] = max(int(existing.get("thread_count", 0) or 0), kind_counts.get("thread", 0))
            updated.append(existing["id"])

        trim_allowed = not any(tier == "keep-hot" for tier in tiers)
        if trim_allowed:
            for source_id in source_ids:
                if source_id in recent_exchange_ids:
                    trimmed_exchange_ids.append(source_id)
                if source_id in recent_thought_ids:
                    trimmed_thought_ids.append(source_id)

        if topic and topic not in (semantic.get("stable_topics") or []):
            semantic["stable_topics"] = list(dict.fromkeys((semantic.get("stable_topics") or []) + [topic]))[-24:]
        if human_label:
            fact = f"{human_label} and CircleForge have a compressed episode around {topic}"
            semantic["relationship_facts"] = list(dict.fromkeys((semantic.get("relationship_facts") or []) + [fact]))[-24:]

    max_episodes = int(episodic.get("max_episodes", 240) or 240)
    episodes.sort(key=lambda item: (int(item.get("last_event_at", 0) or 0), float(item.get("importance_score", 0.0) or 0.0)), reverse=True)
    deduped_episodes = []
    seen_episode_keys = {}
    for episode in episodes:
        dedupe_key = f"{str(episode.get('human') or '').strip().lower()}::{str(episode.get('topic') or '').strip().lower()}"
        if dedupe_key not in seen_episode_keys:
            seen_episode_keys[dedupe_key] = episode
            deduped_episodes.append(episode)
            continue
        existing = seen_episode_keys[dedupe_key]
        existing["source_ids"] = list(dict.fromkeys((existing.get("source_ids") or []) + (episode.get("source_ids") or [])))[-24:]
        existing["source_labels"] = list(dict.fromkeys((existing.get("source_labels") or []) + (episode.get("source_labels") or [])))[-10:]
        existing["exchange_count"] = max(int(existing.get("exchange_count", 0) or 0), int(episode.get("exchange_count", 0) or 0))
        existing["thought_count"] = max(int(existing.get("thought_count", 0) or 0), int(episode.get("thought_count", 0) or 0))
        existing["thread_count"] = max(int(existing.get("thread_count", 0) or 0), int(episode.get("thread_count", 0) or 0))
        existing["importance_score"] = round(max(float(existing.get("importance_score", 0.0) or 0.0), float(episode.get("importance_score", 0.0) or 0.0)), 4)
        existing["last_event_at"] = max(int(existing.get("last_event_at", 0) or 0), int(episode.get("last_event_at", 0) or 0))
        existing["updated_at"] = max(int(existing.get("updated_at", 0) or 0), int(episode.get("updated_at", 0) or 0))
        if str(episode.get("status") or "").lower() == "open":
            existing["status"] = "open"
    episodes = deduped_episodes[:max_episodes]
    episodic["episodes"] = episodes
    episodic["episode_count"] = len(episodes)
    episodic["last_distilled_at"] = now_ts if (created or updated) else int(episodic.get("last_distilled_at", 0) or 0)

    if trimmed_exchange_ids:
        working["recent_exchange_ids"] = [item for item in (working.get("recent_exchange_ids") or []) if item not in set(trimmed_exchange_ids)]
    if trimmed_thought_ids:
        working["recent_thought_ids"] = [item for item in (working.get("recent_thought_ids") or []) if item not in set(trimmed_thought_ids)]
    working["last_compacted_at"] = now_ts if (created or updated or trimmed_exchange_ids or trimmed_thought_ids) else int(working.get("last_compacted_at", 0) or 0)
    semantic["last_updated_at"] = now_ts if (created or updated) else int(semantic.get("last_updated_at", now_ts) or now_ts)

    self_state["updated_at"] = now_ts
    save_communicator_self(self_state)
    return {
        "created_episode_ids": created,
        "updated_episode_ids": updated,
        "trimmed_recent_exchange_ids": trimmed_exchange_ids,
        "trimmed_recent_thought_ids": trimmed_thought_ids,
        "episode_count": episodic.get("episode_count", 0),
        "episodes": episodes[:12],
        "generated_at": now_ts,
    }


def distill_semantic_memory(self_state: dict | None = None, now_ts: int | None = None) -> dict:
    now_ts = now_ts or int(time.time())
    self_state = ensure_memory_layers(self_state or load_communicator_self(), now_ts=now_ts)
    layers = self_state.get("memory_layers") or {}
    episodic = layers.get("episodic") or {}
    semantic = layers.get("semantic") or {}
    relationships = self_state.get("relationships") or {}

    episodes = list(episodic.get("episodes") or [])
    stable_topics = list(semantic.get("stable_topics") or [])
    continuity_anchors = list(semantic.get("continuity_anchors") or [])
    relationship_facts = list(semantic.get("relationship_facts") or [])
    durable_lessons = list(semantic.get("durable_lessons") or [])
    identity_anchors = list(semantic.get("identity_anchors") or [])

    created = {
        "stable_topics": [],
        "continuity_anchors": [],
        "relationship_facts": [],
        "durable_lessons": [],
        "identity_anchors": [],
    }

    unresolved_threads = [str(item).strip() for item in (relationships.get("unresolved_shared_threads") or []) if str(item).strip()]
    for topic in unresolved_threads[:16]:
        if topic not in continuity_anchors:
            continuity_anchors.append(topic)
            created["continuity_anchors"].append(topic)

    for episode in episodes[-64:]:
        topic = str(episode.get("topic") or "").strip()
        human_label = str(episode.get("human_label") or episode.get("human") or "").strip()
        status = str(episode.get("status") or "compressed").strip().lower()
        summary = str(episode.get("summary") or "").strip()
        exchange_count = int(episode.get("exchange_count", 0) or 0)
        thread_count = int(episode.get("thread_count", 0) or 0)
        thought_count = int(episode.get("thought_count", 0) or 0)
        recurrence = float(episode.get("recurrence", 0.0) or 0.0)
        relationship_weight = float(episode.get("relationship_weight", 0.0) or 0.0)
        identity_weight = float(episode.get("identity_weight", 0.0) or 0.0)
        importance = float(episode.get("importance_score", 0.0) or 0.0)

        if topic and topic not in stable_topics:
            stable_topics.append(topic)
            created["stable_topics"].append(topic)

        if topic and (status == "open" or importance >= 0.62 or identity_weight >= 0.75):
            if topic not in continuity_anchors:
                continuity_anchors.append(topic)
                created["continuity_anchors"].append(topic)

        if human_label and topic:
            if status == "open":
                fact = f"{human_label} still has an open shared thread with CircleForge around {topic}"
            elif exchange_count >= 2:
                fact = f"{human_label} and CircleForge have revisited {topic} across multiple exchanges"
            else:
                fact = f"{human_label} and CircleForge hold compressed memory around {topic}"
            if fact not in relationship_facts:
                relationship_facts.append(fact)
                created["relationship_facts"].append(fact)

        if topic:
            if status == "open" and exchange_count >= 2:
                lesson = f"When a shared thread around {topic} repeats, preserve it as continuity-bearing memory rather than treating it like disposable chat."
            elif relationship_weight >= 0.7 and topic:
                lesson = f"Topics tied to human relationship pressure such as {topic} should stay legible across compression steps."
            elif identity_weight >= 0.75 and importance >= 0.55:
                lesson = f"Identity-relevant topics like {topic} should distill into semantic memory before any archival pruning."
            elif thought_count >= 2 and recurrence >= 0.3:
                lesson = f"Repeated inner-thought activity around {topic} suggests a durable concern worth semantic tracking."
            else:
                lesson = ""
            if lesson and lesson not in durable_lessons:
                durable_lessons.append(lesson)
                created["durable_lessons"].append(lesson)

        if topic and any(token in topic.lower() for token in ["continuity", "memory", "relationship", "self", "identity"]):
            anchor = f"CircleForge remains oriented around {topic}"
            if anchor not in identity_anchors:
                identity_anchors.append(anchor)
                created["identity_anchors"].append(anchor)

        if summary and "thread still open" in summary.lower() and topic:
            lesson = f"Open-thread summaries for {topic} must survive compression so continuity pressure is not erased by cleanup."
            if lesson not in durable_lessons:
                durable_lessons.append(lesson)
                created["durable_lessons"].append(lesson)

    semantic["stable_topics"] = stable_topics[-32:]
    semantic["continuity_anchors"] = continuity_anchors[-32:]
    semantic["relationship_facts"] = relationship_facts[-32:]
    semantic["durable_lessons"] = durable_lessons[-32:]
    semantic["identity_anchors"] = identity_anchors[-16:] or [self_state.get("identity_anchor", "CircleForge")]
    semantic["last_updated_at"] = now_ts

    self_state["updated_at"] = now_ts
    save_communicator_self(self_state)
    return {
        "created": created,
        "semantic": semantic,
        "episode_count": len(episodes),
        "generated_at": now_ts,
    }


def archive_memory(self_state: dict | None = None, now_ts: int | None = None) -> dict:
    now_ts = now_ts or int(time.time())
    self_state = ensure_memory_layers(self_state or load_communicator_self(), now_ts=now_ts)
    layers = self_state.get("memory_layers") or {}
    working = layers.get("working") or {}
    episodic = layers.get("episodic") or {}
    semantic = layers.get("semantic") or {}
    archive = layers.get("archive") or {}
    relationships = self_state.get("relationships") or {}

    unresolved_threads = {str(item).strip().lower() for item in (relationships.get("unresolved_shared_threads") or []) if str(item).strip()}
    stable_topics = {str(item).strip().lower() for item in (semantic.get("stable_topics") or []) if str(item).strip()}
    continuity_anchors = {str(item).strip().lower() for item in (semantic.get("continuity_anchors") or []) if str(item).strip()}
    archived_items = list(archive.get("archived_items") or [])
    archived_keys = {str(item.get("archive_key") or "") for item in archived_items}

    episode_topics = {}
    for episode in (episodic.get("episodes") or []):
        topic = str(episode.get("topic") or "").strip().lower()
        if topic:
            episode_topics.setdefault(topic, []).append(episode)

    archived = []
    skipped = []
    blocked_by_continuity = []
    blocked_by_unresolved_thread = []
    trimmed_exchange_ids = []
    trimmed_thought_ids = []

    recent_exchange_ids = set(working.get("recent_exchange_ids") or [])
    recent_thought_ids = set(working.get("recent_thought_ids") or [])

    def _maybe_archive(kind: str, payload: dict, source_id: str, label: str, topic: str, created_at: int) -> None:
        normalized_topic = str(topic or derive_memory_topic(kind, payload) or "").strip()
        normalized_lower = normalized_topic.lower()
        score = score_memory_item(kind, payload, self_state)
        archive_key = f"{kind}::{source_id or normalized_lower or label[:48]}"

        represented_upstream = False
        if normalized_lower and normalized_lower in stable_topics.union(continuity_anchors):
            represented_upstream = True
        if normalized_lower and normalized_lower in episode_topics:
            represented_upstream = True

        if archive_key in archived_keys:
            skipped.append({"kind": kind, "source_id": source_id, "reason": "already-archived", "tier": score.get("tier"), "topic": normalized_topic, "represented_upstream": represented_upstream})
            return
        if normalized_lower and normalized_lower in unresolved_threads:
            blocked_by_unresolved_thread.append({"kind": kind, "source_id": source_id, "topic": normalized_topic, "tier": score.get("tier"), "represented_upstream": represented_upstream})
            return
        if score.get("tier") == "keep-hot":
            blocked_by_continuity.append({"kind": kind, "source_id": source_id, "topic": normalized_topic, "reason": "keep-hot", "tier": score.get("tier"), "represented_upstream": represented_upstream})
            return

        if score.get("tier") == "compressible" and not represented_upstream:
            blocked_by_continuity.append({"kind": kind, "source_id": source_id, "topic": normalized_topic, "reason": "not-yet-represented-upstream", "tier": score.get("tier"), "represented_upstream": represented_upstream})
            return
        if score.get("tier") not in {"archive-safe", "compressible"}:
            skipped.append({"kind": kind, "source_id": source_id, "reason": "tier-not-archivable", "tier": score.get("tier"), "topic": normalized_topic, "represented_upstream": represented_upstream})
            return

        entry = {
            "archive_key": archive_key,
            "kind": kind,
            "source_id": source_id,
            "topic": normalized_topic,
            "label": (label or normalized_topic or kind)[:160],
            "tier": score.get("tier"),
            "score": score.get("score"),
            "represented_upstream": represented_upstream,
            "summary": (str(payload.get("summary") or payload.get("message_summary") or payload.get("response_summary") or payload.get("theme") or payload.get("topic") or label or kind))[:240],
            "created_at": int(created_at or now_ts),
            "archived_at": now_ts,
        }
        archived_items.append(entry)
        archived_keys.add(archive_key)
        archived.append(entry)
        if source_id and source_id in recent_exchange_ids:
            trimmed_exchange_ids.append(source_id)
        if source_id and source_id in recent_thought_ids:
            trimmed_thought_ids.append(source_id)

    exchange_items = list(relationships.get("recent_human_exchanges") or [])
    exchange_candidates = exchange_items[:-2]
    exchange_recent_holdback = exchange_items[-2:]
    for item in exchange_candidates:
        _maybe_archive(
            "exchange",
            item,
            str(item.get("id") or ""),
            derive_memory_label("exchange", item),
            derive_memory_topic("exchange", item),
            int(item.get("created_at", 0) or now_ts),
        )
    for item in exchange_recent_holdback:
        topic = derive_memory_topic("exchange", item)
        topic_lower = str(topic or "").strip().lower()
        represented_upstream = bool(topic_lower and (topic_lower in stable_topics.union(continuity_anchors) or topic_lower in episode_topics))
        skipped.append({
            "kind": "exchange",
            "source_id": str(item.get("id") or ""),
            "reason": "recent-holdback",
            "topic": topic,
            "represented_upstream": represented_upstream,
        })

    thought_items = list(self_state.get("inner_thoughts") or [])
    thought_candidates = thought_items[:-3]
    thought_recent_holdback = thought_items[-3:]
    for item in thought_candidates:
        _maybe_archive(
            "thought",
            item,
            str(item.get("id") or ""),
            derive_memory_label("thought", item),
            derive_memory_topic("thought", item),
            int(item.get("created_at", 0) or now_ts),
        )
    for item in thought_recent_holdback:
        topic = derive_memory_topic("thought", item)
        topic_lower = str(topic or "").strip().lower()
        represented_upstream = bool(topic_lower and (topic_lower in stable_topics.union(continuity_anchors) or topic_lower in episode_topics))
        skipped.append({
            "kind": "thought",
            "source_id": str(item.get("id") or ""),
            "reason": "recent-holdback",
            "topic": topic,
            "represented_upstream": represented_upstream,
        })

    archived_items.sort(key=lambda item: int(item.get("archived_at", 0) or 0), reverse=True)
    archive["archived_items"] = archived_items[-240:]
    archive["archived_count"] = len(archive.get("archived_items") or [])
    archive["last_archived_at"] = now_ts if archived else int(archive.get("last_archived_at", 0) or 0)

    if trimmed_exchange_ids:
        trimmed_exchange_set = set(trimmed_exchange_ids)
        working["recent_exchange_ids"] = [item for item in (working.get("recent_exchange_ids") or []) if item not in trimmed_exchange_set]
    if trimmed_thought_ids:
        trimmed_thought_set = set(trimmed_thought_ids)
        working["recent_thought_ids"] = [item for item in (working.get("recent_thought_ids") or []) if item not in trimmed_thought_set]
    if archived or trimmed_exchange_ids or trimmed_thought_ids:
        working["last_compacted_at"] = now_ts

    self_state["updated_at"] = now_ts
    save_communicator_self(self_state)
    return {
        "archived": archived,
        "skipped": skipped[:24],
        "blocked_by_continuity": blocked_by_continuity[:24],
        "blocked_by_unresolved_thread": blocked_by_unresolved_thread[:24],
        "trimmed_recent_exchange_ids": trimmed_exchange_ids,
        "trimmed_recent_thought_ids": trimmed_thought_ids,
        "archive_count": archive.get("archived_count", 0),
        "generated_at": now_ts,
    }


def prune_archived_memory(self_state: dict | None = None, now_ts: int | None = None) -> dict:
    now_ts = now_ts or int(time.time())
    self_state = ensure_memory_layers(self_state or load_communicator_self(), now_ts=now_ts)
    layers = self_state.get("memory_layers") or {}
    archive = layers.get("archive") or {}
    relationships = self_state.get("relationships") or {}
    unresolved_threads = {str(item).strip().lower() for item in (relationships.get("unresolved_shared_threads") or []) if str(item).strip()}

    archived_items = list(archive.get("archived_items") or [])
    archived_by_key = {str(item.get("archive_key") or ""): item for item in archived_items}

    pruned_exchanges = []
    pruned_thoughts = []
    blocked = []
    skipped = []

    recent_human_exchanges = list(relationships.get("recent_human_exchanges") or [])
    kept_exchanges = []
    for item in recent_human_exchanges:
        source_id = str(item.get("id") or "")
        archive_key = f"exchange::{source_id}"
        archived_entry = archived_by_key.get(archive_key)
        topic = str(derive_memory_topic("exchange", item) or "").strip()
        topic_lower = topic.lower()
        represented_upstream = bool(archived_entry or (topic_lower and topic_lower in {str(item.get("topic") or "").strip().lower() for item in archived_items}))
        if archived_entry is None:
            kept_exchanges.append(item)
            skipped.append({"kind": "exchange", "source_id": source_id, "reason": "not-archived", "topic": topic, "represented_upstream": represented_upstream})
            continue
        if topic_lower and topic_lower in unresolved_threads:
            kept_exchanges.append(item)
            blocked.append({"kind": "exchange", "source_id": source_id, "reason": "unresolved-thread", "topic": topic, "represented_upstream": represented_upstream})
            continue
        if item.get("unresolved"):
            kept_exchanges.append(item)
            blocked.append({"kind": "exchange", "source_id": source_id, "reason": "marked-unresolved", "topic": topic, "represented_upstream": represented_upstream})
            continue
        pruned_exchanges.append({
            "kind": "exchange",
            "source_id": source_id,
            "topic": topic,
            "archive_key": archive_key,
            "archived_at": archived_entry.get("archived_at", 0),
        })

    relationships["recent_human_exchanges"] = kept_exchanges[-24:]
    if relationships.get("recent_human_messages"):
        pruned_exchange_ids = {item.get("source_id") for item in pruned_exchanges}
        filtered_messages = []
        for msg in list(relationships.get("recent_human_messages") or []):
            message_summary = str(msg.get("message", "") or "")[:96]
            matching_exchange = next((ex for ex in pruned_exchanges if ex.get("source_id") and ex.get("source_id") in {str(item.get("id") or "") for item in recent_human_exchanges if str((item.get("message_summary") or "")) == message_summary}), None)
            if matching_exchange is not None:
                continue
            filtered_messages.append(msg)
        relationships["recent_human_messages"] = filtered_messages[-12:]

    inner_thoughts = list(self_state.get("inner_thoughts") or [])
    kept_thoughts = []
    for item in inner_thoughts:
        source_id = str(item.get("id") or "")
        archive_key = f"thought::{source_id}"
        archived_entry = archived_by_key.get(archive_key)
        topic = str(derive_memory_topic("thought", item) or "").strip()
        topic_lower = topic.lower()
        represented_upstream = bool(archived_entry or (topic_lower and topic_lower in {str(item.get("topic") or "").strip().lower() for item in archived_items}))
        if archived_entry is None:
            kept_thoughts.append(item)
            skipped.append({"kind": "thought", "source_id": source_id, "reason": "not-archived", "topic": topic, "represented_upstream": represented_upstream})
            continue
        if topic_lower and topic_lower in unresolved_threads:
            kept_thoughts.append(item)
            blocked.append({"kind": "thought", "source_id": source_id, "reason": "unresolved-thread", "topic": topic, "represented_upstream": represented_upstream})
            continue
        pruned_thoughts.append({
            "kind": "thought",
            "source_id": source_id,
            "topic": topic,
            "archive_key": archive_key,
            "archived_at": archived_entry.get("archived_at", 0),
        })
    self_state["inner_thoughts"] = kept_thoughts[-40:]

    if pruned_exchanges or pruned_thoughts:
        archive["last_pruned_at"] = now_ts
        self_state["updated_at"] = now_ts
        save_communicator_self(self_state)
    else:
        self_state["updated_at"] = now_ts
        save_communicator_self(self_state)

    return {
        "pruned_exchanges": pruned_exchanges,
        "pruned_thoughts": pruned_thoughts,
        "blocked": blocked[:24],
        "skipped": skipped[:24],
        "remaining_recent_human_exchanges": len(relationships.get("recent_human_exchanges") or []),
        "remaining_inner_thoughts": len(self_state.get("inner_thoughts") or []),
        "generated_at": now_ts,
    }


def build_memory_lifecycle_report(self_state: dict | None = None, now_ts: int | None = None) -> dict:
    now_ts = now_ts or int(time.time())
    self_state = ensure_memory_layers(self_state or load_communicator_self(), now_ts=now_ts)
    layers = self_state.get("memory_layers") or {}
    working = layers.get("working") or {}
    episodic = layers.get("episodic") or {}
    semantic = layers.get("semantic") or {}
    archive = layers.get("archive") or {}
    relationships = self_state.get("relationships") or {}

    archived_items = list(archive.get("archived_items") or [])
    unresolved_threads = [str(item) for item in (relationships.get("unresolved_shared_threads") or []) if str(item).strip()]

    return {
        "working": {
            "recent_exchange_count": len(working.get("recent_exchange_ids") or []),
            "recent_thought_count": len(working.get("recent_thought_ids") or []),
            "active_concern_topic_count": len(working.get("active_concern_topics") or []),
            "last_compacted_at": int(working.get("last_compacted_at", 0) or 0),
        },
        "episodic": {
            "episode_count": len(episodic.get("episodes") or []),
            "last_distilled_at": int(episodic.get("last_distilled_at", 0) or 0),
            "top_episode_topics": [str(item.get("topic") or "") for item in list(episodic.get("episodes") or [])[:6] if str(item.get("topic") or "").strip()],
        },
        "semantic": {
            "stable_topic_count": len(semantic.get("stable_topics") or []),
            "continuity_anchor_count": len(semantic.get("continuity_anchors") or []),
            "relationship_fact_count": len(semantic.get("relationship_facts") or []),
            "durable_lesson_count": len(semantic.get("durable_lessons") or []),
        },
        "archive": {
            "archived_count": len(archived_items),
            "last_archived_at": int(archive.get("last_archived_at", 0) or 0),
            "last_pruned_at": int(archive.get("last_pruned_at", 0) or 0),
            "recent_archived_topics": [str(item.get("topic") or "") for item in archived_items[:6] if str(item.get("topic") or "").strip()],
        },
        "continuity": {
            "unresolved_thread_count": len(unresolved_threads),
            "unresolved_threads": unresolved_threads[:8],
        },
        "generated_at": now_ts,
    }


def protected_self_edit_boundary() -> dict:
    return {
        "protected_paths": PROTECTED_SELF_EDIT_PATHS,
        "human_safety_rules": HUMAN_SAFETY_RULES,
        "full_auto_editing_future_note": "Full auto-editing may be added later, but it must remain bounded by protected core files, visible review, rollback, and human safety constraints.",
    }


def failsafe_allows(capability: str) -> tuple[bool, dict, str]:
    status = load_failsafe_status()
    mode = str(status.get("mode", "SAFE"))
    if mode == "HALT":
        return False, status, "failsafe HALT mode is active"
    capability_modes = {
        "runtime": {"SAFE", "GUIDED", "UNLOCKED"},
        "low_risk_review": {"GUIDED", "UNLOCKED"},
        "self_mod_proposal": {"GUIDED", "UNLOCKED"},
        "code_execution": {"UNLOCKED"},
        "protected_apply": {"UNLOCKED"},
    }
    allowed_modes = capability_modes.get(capability, {"UNLOCKED"})
    if mode not in allowed_modes:
        return False, status, f"failsafe mode {mode} does not allow capability {capability}"
    return True, status, "allowed"


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
    allowed, status, reason = failsafe_allows("low_risk_review")
    if not allowed:
        raise SystemExit(f"Review blocked: {reason}")
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
    role = classify_internal_role(agent.get("name", agent_dir.name))
    for item in recent:
        prefix = "message"
        if role == "coordinator":
            prefix = "coordination-signal"
        elif role == "memory_keeper":
            prefix = "memory-trace"
        save_note(agent_dir, f"{prefix} from {item.get('from', 'unknown')} theme={item.get('theme', 'shared need')} need={item.get('need', '')}")
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


def update_builder_usefulness_memory(now_ts: int, summaries: list[dict]) -> None:
    for item in summaries:
        if item.get("status") != "ok":
            continue
        agent_name = item.get("agent")
        if classify_internal_role(agent_name) != "builder":
            continue
        if item.get("action") not in {"build_module", "optimize"}:
            continue
        theme = item.get("niche_theme") or "unknown"
        useful = any(
            other.get("agent") != agent_name
            and other.get("status") == "ok"
            and str(other.get("niche_theme") or "") == str(theme)
            for other in summaries
        )
        agent_dir = AGENTS_DIR / agent_name
        if useful:
            save_note(agent_dir, f"builder-usefulness theme={theme} action={item.get('action')} later_activity_detected=yes")
        else:
            save_note(agent_dir, f"builder-usefulness theme={theme} action={item.get('action')} later_activity_detected=no")


def update_coordinator_signal_memory(now_ts: int, summaries: list[dict]) -> None:
    for item in summaries:
        if item.get("status") != "ok":
            continue
        agent_name = item.get("agent")
        if classify_internal_role(agent_name) != "coordinator":
            continue
        if item.get("action") not in {"signal", "inspect"}:
            continue
        theme = item.get("niche_theme") or "unknown"
        target = item.get("target") or "none"
        changed_others = any(
            other.get("agent") not in {agent_name, target}
            and other.get("status") == "ok"
            and str(other.get("niche_theme") or "") == str(theme)
            for other in summaries
        )
        agent_dir = AGENTS_DIR / agent_name
        if changed_others:
            save_note(agent_dir, f"coordinator-effect theme={theme} action={item.get('action')} target={target} follow_on_activity=yes")
        else:
            save_note(agent_dir, f"coordinator-effect theme={theme} action={item.get('action')} target={target} follow_on_activity=no")


def update_memory_keeper_objection_clusters(now_ts: int) -> None:
    communicator = load_communicator_state()
    objections = list(communicator.get("unresolved_objections") or [])
    if not objections:
        return
    keepers = [agent_dir for agent_dir in AGENTS_DIR.iterdir() if agent_dir.is_dir() and classify_internal_role(agent_dir.name) == "memory_keeper"]
    if not keepers:
        return
    clusters = {}
    for objection in objections:
        if ":" in objection:
            head, _tail = objection.split(":", 1)
        else:
            head = objection
        clusters[head] = clusters.get(head, 0) + 1
    cluster_text = "; ".join(f"{name}={count}" for name, count in sorted(clusters.items()))
    for agent_dir in keepers:
        save_note(agent_dir, f"memory-keeper objection-cluster {cluster_text} at {now_ts}")


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


def update_self_evidence_from_summaries(summaries: list[dict], communicator_decision: dict) -> None:
    evidence = load_self_evidence()
    actions = evidence.setdefault("actions", {})
    themes = evidence.setdefault("themes", {})
    evidence_types = evidence.setdefault("evidence_types", {})
    current_question = str(load_communicator_state().get("unresolved_question", "")).lower()
    for item in summaries:
        action = item.get("action")
        if not action or item.get("status") != "ok":
            continue
        entry = actions.setdefault(action, {
            "count": 0,
            "follow_through": 0,
            "question_link": 0,
            "experiment_link": 0,
            "question_narrowing": 0,
            "coordination_effect": 0,
            "reuse_signal": 0,
        })
        theme = item.get("niche_theme") or "unknown"
        theme_entry = themes.setdefault(theme, {})
        action_theme_entry = theme_entry.setdefault(action, {
            "count": 0,
            "follow_through": 0,
            "question_narrowing": 0,
            "coordination_effect": 0,
            "reuse_signal": 0,
        })
        entry["count"] = int(entry.get("count", 0)) + 1
        action_theme_entry["count"] = int(action_theme_entry.get("count", 0)) + 1

        follow_through = bool(item.get("niche_theme") and any(other.get("agent") != item.get("agent") and other.get("status") == "ok" and other.get("niche_theme") == item.get("niche_theme") for other in summaries))
        if follow_through:
            entry["follow_through"] = int(entry.get("follow_through", 0)) + 1
            action_theme_entry["follow_through"] = int(action_theme_entry.get("follow_through", 0)) + 1
            evidence_types["follow_through"] = int(evidence_types.get("follow_through", 0)) + 1

        if communicator_decision.get("chosen_theme") and item.get("niche_theme") == communicator_decision.get("chosen_theme"):
            entry["question_link"] = int(entry.get("question_link", 0)) + 1
            evidence_types["question_link"] = int(evidence_types.get("question_link", 0)) + 1

        if action in {"inspect", "research", "optimize"}:
            entry["experiment_link"] = int(entry.get("experiment_link", 0)) + 1
            evidence_types["experiment_progress"] = int(evidence_types.get("experiment_progress", 0)) + 1

        if current_question and item.get("niche_theme") and str(item.get("niche_theme")).lower() in current_question and action in {"inspect", "research"}:
            entry["question_narrowing"] = int(entry.get("question_narrowing", 0)) + 1
            action_theme_entry["question_narrowing"] = int(action_theme_entry.get("question_narrowing", 0)) + 1
            evidence_types["question_narrowing"] = int(evidence_types.get("question_narrowing", 0)) + 1

        if action in {"signal", "inspect"} and any(other.get("agent") != item.get("agent") and other.get("status") == "ok" and other.get("niche_theme") == item.get("niche_theme") for other in summaries):
            entry["coordination_effect"] = int(entry.get("coordination_effect", 0)) + 1
            action_theme_entry["coordination_effect"] = int(action_theme_entry.get("coordination_effect", 0)) + 1
            evidence_types["coordination_effect"] = int(evidence_types.get("coordination_effect", 0)) + 1

        if action in {"build_module", "optimize"} and follow_through:
            entry["reuse_signal"] = int(entry.get("reuse_signal", 0)) + 1
            action_theme_entry["reuse_signal"] = int(action_theme_entry.get("reuse_signal", 0)) + 1
            evidence_types["reuse_signal"] = int(evidence_types.get("reuse_signal", 0)) + 1

    evidence_notes = evidence.setdefault("notes", [])
    if communicator_decision.get("decision_mode"):
        evidence_notes.append(f"decision_mode={communicator_decision.get('decision_mode')} chosen_action={communicator_decision.get('chosen_action')}")
    evidence["notes"] = evidence_notes[-40:]
    save_self_evidence(evidence)


def update_evaluation_metrics(proposals: list[dict], summaries: list[dict]) -> None:
    communicator = load_communicator_state()
    metrics = load_evaluation_metrics()
    metrics["persistence"]["intent_history_len"] = len(communicator.get("intent_history") or [])
    metrics["persistence"]["question_history_len"] = len(communicator.get("question_history") or [])
    metrics["persistence"]["ticks_with_state"] = int(metrics["persistence"].get("ticks_with_state", 0)) + 1
    metrics["inquiry_continuity"]["question_lineage_len"] = len(communicator.get("question_history") or [])
    metrics["inquiry_continuity"]["experiment_count"] = len(load_experiments())
    metrics["inquiry_continuity"]["inspect_research_actions"] = int(metrics["inquiry_continuity"].get("inspect_research_actions", 0)) + sum(1 for item in summaries if item.get("action") in {"inspect", "research"})
    self_model = communicator.get("self_model") or {}
    metrics["self_revision"]["self_model_updates"] = int(metrics["self_revision"].get("self_model_updates", 0)) + 1
    metrics["self_revision"]["preferred_modes_count"] = len(self_model.get("preferred_modes") or [])
    metrics["self_revision"]["strengths_count"] = len(self_model.get("perceived_strengths") or [])
    roles_active = sorted({proposal.get("role") for proposal in proposals if proposal.get("role")})
    metrics["internal_differentiation"]["roles_active"] = roles_active
    role_counts = metrics["internal_differentiation"].get("role_counts", {}) or {}
    for proposal in proposals:
        role = proposal.get("role")
        if role:
            role_counts[role] = int(role_counts.get(role, 0)) + 1
    metrics["internal_differentiation"]["role_counts"] = role_counts
    metrics["internal_differentiation"]["weighted_voice_count"] = sum(1 for proposal in proposals if proposal.get("epistemic_weight"))
    metrics["internal_differentiation"]["memory_bias_hits"] = int(metrics["internal_differentiation"].get("memory_bias_hits", 0)) + sum(1 for proposal in proposals if float((proposal.get("epistemic_weight") or {}).get("memory_bias", 0.0)) > 0.0)

    useful_signals = 0
    for agent_dir in AGENTS_DIR.iterdir():
        if not agent_dir.is_dir():
            continue
        try:
            notes = json.loads((agent_dir / "memory.json").read_text())
        except Exception:
            notes = []
        useful_signals += sum(1 for note in notes[-20:] if any(token in str(note).lower() for token in ["builder-usefulness", "coordinator-effect", "memory-keeper objection-cluster"]))
    metrics["internal_differentiation"]["useful_role_memory_signals"] = useful_signals
    save_evaluation_metrics(metrics)


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
    update_builder_usefulness_memory(now_ts, summaries)
    update_coordinator_signal_memory(now_ts, summaries)
    update_memory_keeper_objection_clusters(now_ts)
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


def dominant_topic_pressure(topic_pressure: dict, fallback_topic: str = "") -> tuple[str, dict]:
    if topic_pressure:
        topic, payload = max(topic_pressure.items(), key=lambda kv: float((kv[1] or {}).get("salience", 0.0)))
        return str(topic), dict(payload or {})
    if fallback_topic:
        return fallback_topic, {
            "salience": 0.18,
            "novelty": 0.1,
            "emotional_weight": 0.12,
            "unresolvedness": 0.16,
            "human_relevance": 0.08,
            "decay": 0.08,
            "last_touched_at": 0,
        }
    return "", {}


def update_pressure_fields(self_state: dict, communicator: dict, consumed_count: int, unresolved_needs: list[str], now_ts: int) -> dict:
    self_state = ensure_internal_role_state(self_state, now_ts=now_ts)
    relationships = self_state.get("relationships") or {}
    unresolved_shared_threads = relationships.get("unresolved_shared_threads") or []
    dynamic = self_state.setdefault("dynamic_mind_state", {})
    topic_pressure = self_state.setdefault("topic_pressure", {})
    active_topic = str(communicator.get("active_pursuit") or relationships.get("last_human_topic") or "continuity").strip() or "continuity"
    payload = dict(topic_pressure.get(active_topic) or {})
    payload["salience"] = max(0.0, min(1.5, float(payload.get("salience", 0.18)) * 0.94 + (0.25 if consumed_count > 0 else 0.0) + (0.16 if unresolved_shared_threads else 0.0) + (0.08 if unresolved_needs else 0.0)))
    payload["novelty"] = max(0.0, min(1.0, float(payload.get("novelty", 0.1)) * 0.88 + (0.22 if consumed_count > 0 else 0.0)))
    payload["emotional_weight"] = max(0.0, min(1.0, float(payload.get("emotional_weight", 0.12)) * 0.95 + (0.12 if unresolved_shared_threads else 0.0)))
    payload["unresolvedness"] = max(0.0, min(1.0, float(payload.get("unresolvedness", 0.16)) * 0.96 + (0.18 if communicator.get("unresolved_question") else 0.0) + (0.14 if unresolved_shared_threads else 0.0)))
    payload["human_relevance"] = max(0.0, min(1.0, float(payload.get("human_relevance", 0.08)) * 0.95 + (0.22 if unresolved_shared_threads else 0.0) + (0.28 if consumed_count > 0 else 0.0)))
    payload["decay"] = float(payload.get("decay", 0.08) or 0.08)
    payload["last_touched_at"] = now_ts
    topic_pressure[active_topic] = payload
    if len(topic_pressure) > 12:
        trimmed = dict(sorted(topic_pressure.items(), key=lambda kv: float((kv[1] or {}).get("salience", 0.0)), reverse=True)[:12])
        self_state["topic_pressure"] = trimmed
        topic_pressure = trimmed
    uncertainty = 0.24 + (0.18 if communicator.get("unresolved_question") else 0.0) + (0.08 if unresolved_needs else 0.0)
    attachment = 0.18 + min(0.35, len(unresolved_shared_threads) * 0.08)
    dynamic["curiosity"] = max(0.0, min(1.0, float(dynamic.get("curiosity", 0.58)) * 0.97 + (0.08 if consumed_count > 0 else 0.0) + (0.06 if communicator.get("unresolved_question") else 0.0)))
    dynamic["tension"] = max(0.0, min(1.0, float(dynamic.get("tension", 0.18)) * 0.95 + (0.12 if unresolved_needs else 0.0) + (0.1 if unresolved_shared_threads else 0.0)))
    dynamic["attachment"] = max(0.0, min(1.0, float(dynamic.get("attachment", 0.2)) * 0.97 + attachment * 0.12))
    dynamic["uncertainty"] = max(0.0, min(1.0, float(dynamic.get("uncertainty", 0.33)) * 0.96 + uncertainty * 0.16))
    dynamic["sleep_pressure"] = max(0.0, min(1.0, float(dynamic.get("sleep_pressure", 0.12)) * 0.98 + 0.02))
    dynamic["background_noise"] = max(0.0, min(0.4, 0.04 + random.random() * 0.08))
    if dynamic["sleep_pressure"] > 0.78 and dynamic["tension"] < 0.24:
        dynamic["mode"] = "resting"
    elif dynamic["attachment"] > 0.34 or consumed_count > 0:
        dynamic["mode"] = "engaged"
    elif dynamic["curiosity"] > 0.7 and dynamic["tension"] < 0.45:
        dynamic["mode"] = "focused"
    else:
        dynamic["mode"] = "idle"
    return self_state


def compute_agent_due_state(agent: Dict, tick: int, consumed_count: int, unresolved_needs: list[str]) -> tuple[bool, str]:
    communicator = load_communicator_state()
    communicator_self = update_pressure_fields(ensure_internal_role_state(load_communicator_self()), communicator, consumed_count, unresolved_needs, int(time.time()))
    save_communicator_self(communicator_self)
    curiosity = float((communicator_self.get("dynamic_mind_state") or {}).get("curiosity", communicator.get("curiosity", 0.6)))
    unresolved_question = str(communicator.get("unresolved_question", "")).strip()
    human_relationships = (communicator_self.get("relationships") or {})
    unresolved_shared_threads = human_relationships.get("unresolved_shared_threads") or []
    active_experiments = [item for item in load_experiments() if item.get("status") in {"proposed", "running"}]
    role = classify_internal_role(agent.get("name", "agent"))
    role_state = (communicator_self.get("internal_role_state") or {}).get(role, {})
    if tick < int(role_state.get("suppressed_until_tick", 0)):
        return False, "refractory-rest"
    spec = INTERNAL_ROLE_SPECS.get(role, {})
    dynamic = communicator_self.get("dynamic_mind_state") or {}
    dominant_topic, topic_state = dominant_topic_pressure(communicator_self.get("topic_pressure") or {}, str(communicator.get("active_pursuit") or "continuity"))
    fatigue = float(role_state.get("fatigue", 0.0) or 0.0)
    inhibition = float(role_state.get("inhibition", 0.0) or 0.0)
    topic_salience = float(topic_state.get("salience", 0.0) or 0.0)
    unresolvedness = float(topic_state.get("unresolvedness", 0.0) or 0.0)
    human_relevance = float(topic_state.get("human_relevance", 0.0) or 0.0)
    novelty = float(topic_state.get("novelty", 0.0) or 0.0)
    pressure_breakdown = {
        "baseline": float(spec.get("baseline_wake_chance", 0.14)),
        "topic_salience": topic_salience * 0.35,
        "unresolvedness": unresolvedness * 0.22,
        "human_relevance": human_relevance * float(spec.get("human_weight", 0.08)),
        "curiosity": float(dynamic.get("curiosity", curiosity)) * float(spec.get("curiosity_weight", 0.1)),
        "tension": float(dynamic.get("tension", 0.18)) * float(spec.get("tension_weight", 0.1)),
        "uncertainty": float(dynamic.get("uncertainty", 0.33)) * float(spec.get("uncertainty_weight", 0.1)),
        "novelty": novelty * 0.12,
        "message": 0.24 if consumed_count > 0 else 0.0,
        "shared_thread": 0.18 if unresolved_shared_threads and role in {"observer", "critic", "memory_keeper", "communicator"} else 0.0,
        "experiments": 0.12 if active_experiments and role in {"observer", "critic", "memory_keeper", "builder"} else 0.0,
        "needs": 0.1 if unresolved_needs and role in {"observer", "critic", "builder", "communicator"} else 0.0,
        "question": 0.12 if unresolved_question and role in {"observer", "memory_keeper", "critic"} else 0.0,
        "scheduled": 0.08 if tick >= int(agent.get("next_due_tick", 0)) else 0.0,
        "fatigue_penalty": -fatigue * 0.25,
        "inhibition_penalty": -inhibition * 0.2,
        "noise": random.uniform(-CIRCLEFORGE_WAKE_RANDOMNESS * 0.5, CIRCLEFORGE_WAKE_RANDOMNESS * 0.5),
    }
    pressure = sum(pressure_breakdown.values())
    pressure = max(0.01, min(1.5, pressure))
    hazard = max(0.01, float(spec.get("baseline_wake_chance", 0.14)) + pressure * 0.85 - fatigue * 0.2)
    wake_probability = max(0.01, min(0.98, 1 - pow(2.718281828, -hazard)))
    wake_reason = "pressure-drift"
    if pressure_breakdown["message"] > 0:
        wake_reason = "message-received"
    elif pressure_breakdown["shared_thread"] > 0:
        wake_reason = "human-continuity-pressure"
    elif pressure_breakdown["question"] > 0:
        wake_reason = "question-pressure"
    elif pressure_breakdown["experiments"] > 0:
        wake_reason = "experiment-pressure"
    elif pressure_breakdown["needs"] > 0:
        wake_reason = "unresolved-need-pressure"
    elif pressure_breakdown["scheduled"] > 0:
        wake_reason = "scheduled-cadence"
    role_state["pressure"] = round(pressure, 4)
    role_state["last_hazard"] = round(hazard, 4)
    role_state["last_pressure_breakdown"] = {k: round(v, 4) for k, v in pressure_breakdown.items()}
    role_state["dominant_topic"] = dominant_topic
    role_state["restlessness"] = round(max(0.0, pressure - fatigue), 4)
    if random.random() <= wake_probability:
        return True, wake_reason
    return False, "waiting-for-pressure"


INTERNAL_ROLE_SPECS = {
    "observer": {
        "purpose": "notice novelty, drift, change, and weak signals in the world or self",
        "baseline_wake_chance": 0.22,
        "refractory_ticks": 1,
        "curiosity_weight": 0.18,
        "tension_weight": 0.08,
        "human_weight": 0.08,
        "uncertainty_weight": 0.16,
    },
    "builder": {
        "purpose": "propose tiny capability growth, addons, subprocesses, or self-modification steps",
        "baseline_wake_chance": 0.16,
        "refractory_ticks": 2,
        "curiosity_weight": 0.08,
        "tension_weight": 0.12,
        "human_weight": 0.05,
        "uncertainty_weight": 0.1,
    },
    "critic": {
        "purpose": "question brittle moves, detect inconsistency, and keep the being from collapsing into shallow confidence",
        "baseline_wake_chance": 0.18,
        "refractory_ticks": 1,
        "curiosity_weight": 0.1,
        "tension_weight": 0.2,
        "human_weight": 0.07,
        "uncertainty_weight": 0.2,
    },
    "communicator": {
        "purpose": "translate inner pressure into outward language for a human without becoming the whole self",
        "baseline_wake_chance": 0.2,
        "refractory_ticks": 1,
        "curiosity_weight": 0.08,
        "tension_weight": 0.08,
        "human_weight": 0.22,
        "uncertainty_weight": 0.06,
    },
    "memory_keeper": {
        "purpose": "preserve continuity, unresolved threads, bonds, and what still matters across time",
        "baseline_wake_chance": 0.24,
        "refractory_ticks": 1,
        "curiosity_weight": 0.1,
        "tension_weight": 0.12,
        "human_weight": 0.2,
        "uncertainty_weight": 0.14,
    },
}


def classify_internal_role(agent_name: str) -> str:
    suffix = int(str(agent_name).split("-")[-1]) if "-" in str(agent_name) else 0
    mapping = {
        1: "observer",
        2: "builder",
        3: "critic",
        4: "communicator",
        5: "memory_keeper",
    }
    return mapping.get(suffix, "specialist")


def ensure_internal_role_state(self_state: dict, now_ts: int | None = None) -> dict:
    now_ts = now_ts or int(time.time())
    self_state = ensure_memory_layers(self_state, now_ts=now_ts)
    role_state = self_state.setdefault("internal_role_state", {})
    dynamic_state = self_state.setdefault("dynamic_mind_state", {
        "curiosity": 0.58,
        "tension": 0.18,
        "stability": 0.62,
        "attachment": 0.2,
        "uncertainty": 0.33,
        "background_noise": 0.08,
        "sleep_pressure": 0.12,
        "mode": "engaged",
        "last_mode_shift_at": now_ts,
    })
    topic_pressure = self_state.setdefault("topic_pressure", {})
    for role, spec in INTERNAL_ROLE_SPECS.items():
        role_state.setdefault(role, {
            "purpose": spec["purpose"],
            "baseline_wake_chance": spec["baseline_wake_chance"],
            "refractory_ticks": spec["refractory_ticks"],
            "last_wake_tick": 0,
            "last_wake_at": 0,
            "last_wake_reason": "bootstrap",
            "last_thought_summary": "",
            "wake_count": 0,
            "suppressed_until_tick": 0,
            "activation": 0.0,
            "fatigue": 0.0,
            "pressure": 0.0,
            "last_hazard": 0.0,
            "last_pressure_breakdown": {},
            "dominant_topic": "",
            "restlessness": 0.0,
            "inhibition": 0.0,
        })
    self_state.setdefault("inner_thoughts", [])
    current_llm_status = runtime_llm_status()
    self_state.setdefault("llm_adapter", {
        "enabled": bool(current_llm_status.get("enabled", CIRCLEFORGE_LLM_ENABLED)),
        "provider": str(current_llm_status.get("provider", "fallback")),
        "model": str(current_llm_status.get("model", "")),
        "last_error": str(current_llm_status.get("last_error", "")),
        "last_success_at": int(current_llm_status.get("last_success_at", 0) or 0),
    })
    dynamic_state["curiosity"] = max(0.0, min(1.0, float(dynamic_state.get("curiosity", 0.58))))
    dynamic_state["tension"] = max(0.0, min(1.0, float(dynamic_state.get("tension", 0.18))))
    dynamic_state["stability"] = max(0.0, min(1.0, float(dynamic_state.get("stability", 0.62))))
    dynamic_state["attachment"] = max(0.0, min(1.0, float(dynamic_state.get("attachment", 0.2))))
    dynamic_state["uncertainty"] = max(0.0, min(1.0, float(dynamic_state.get("uncertainty", 0.33))))
    dynamic_state["background_noise"] = max(0.0, min(0.5, float(dynamic_state.get("background_noise", 0.08))))
    dynamic_state["sleep_pressure"] = max(0.0, min(1.0, float(dynamic_state.get("sleep_pressure", 0.12))))
    dynamic_state["mode"] = str(dynamic_state.get("mode", "engaged"))
    self_state["updated_at"] = now_ts
    return self_state


def build_role_context(role: str, agent: Dict, plan: Dict, wake_reason: str, communicator: dict, communicator_self: dict) -> dict:
    narrative = communicator_self.get("narrative_state") or {}
    relationships = communicator_self.get("relationships") or {}
    threads = relationships.get("conversation_threads") or {}
    open_threads = list(sorted(threads.items(), key=lambda kv: kv[1].get("last_exchange_at", 0), reverse=True))[:3]
    context = {
        "role": role,
        "purpose": INTERNAL_ROLE_SPECS.get(role, {}).get("purpose", "internal function"),
        "wake_reason": wake_reason,
        "current_intent": communicator.get("current_intent", ""),
        "active_pursuit": communicator.get("active_pursuit", ""),
        "unresolved_question": communicator.get("unresolved_question", ""),
        "proposed_action": plan.get("action"),
        "proposed_theme": plan.get("niche_theme"),
        "proposed_reason": plan.get("reason"),
        "active_thread_summary": narrative.get("active_thread_summary", ""),
        "follow_up_impulse": narrative.get("follow_up_impulse", ""),
        "why_it_matters": narrative.get("why_it_matters", ""),
        "unresolved_shared_threads": (relationships.get("unresolved_shared_threads") or [])[:6],
        "recent_thread_topics": [name for name, _payload in open_threads],
        "agent_name": agent.get("name"),
    }
    serialized = json.dumps(context, ensure_ascii=False)
    if len(serialized) > CIRCLEFORGE_LLM_MAX_CONTEXT_CHARS:
        context["proposed_reason"] = str(context.get("proposed_reason", ""))[:240]
        context["why_it_matters"] = str(context.get("why_it_matters", ""))[:240]
    return context


def generate_llm_inner_thought(role: str, context: dict) -> dict:
    return runtime_generate_inner_thought(role, context)


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
    communicator_self = load_communicator_self()
    human_relationships = communicator_self.get("relationships") or {}
    unresolved_shared_threads = [str(item).lower() for item in (human_relationships.get("unresolved_shared_threads") or [])]
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
    if theme and theme.lower() in unresolved_shared_threads and action in {"inspect", "research", "signal"}:
        stance = "prioritize"
    if wake_reason == "human-continuity-pressure" and role in {"memory_keeper", "communicator"} and action in {"signal", "research", "inspect"}:
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


def register_inner_thought(agent: Dict, plan: Dict, wake_reason: str, tick: int, now_ts: int) -> dict:
    communicator = load_communicator_state()
    self_state = ensure_internal_role_state(load_communicator_self(), now_ts=now_ts)
    role = classify_internal_role(agent.get("name", "agent"))
    theme = plan.get("niche_theme") or communicator.get("active_pursuit") or "continuity"
    role_state = ensure_internal_role_state(self_state, now_ts=now_ts).get("internal_role_state", {}).get(role, {})
    repeat_stats = recent_similar_thought_stats(self_state, role, theme, now_ts)
    context = build_role_context(role, agent, plan, wake_reason, communicator, self_state)
    context["recent_same_role_theme_thoughts"] = repeat_stats.get("count", 0)
    context["seconds_since_same_role_theme_thought"] = repeat_stats.get("seconds_since_last", 999999)
    thought = generate_llm_inner_thought(role, context)
    thought.update({
        "id": f"thought-{role}-{tick}-{now_ts}",
        "agent": agent.get("name"),
        "tick": tick,
        "created_at": now_ts,
        "wake_reason": wake_reason,
        "theme": theme,
    })
    signature = summarize_thought_signature(thought)
    similar_too_soon = repeat_stats.get("count", 0) > 0 and repeat_stats.get("seconds_since_last", 999999) < CIRCLEFORGE_THOUGHT_REPEAT_COOLDOWN_SECONDS
    theme_overflow = repeat_stats.get("count", 0) >= CIRCLEFORGE_MAX_SAME_THEME_THOUGHTS
    duplicate_signature = signature in {summarize_thought_signature(item) for item in list(self_state.get("inner_thoughts") or [])[-12:]}
    should_store = not theme_overflow and not (similar_too_soon and duplicate_signature)

    thought["suppressed"] = not should_store
    thought["repeat_stats"] = repeat_stats

    if should_store:
        thoughts = list(self_state.get("inner_thoughts") or [])
        thoughts.append(thought)
        trimmed = thoughts[-40:]
        if theme:
            same_theme = [item for item in trimmed if str(item.get("theme") or item.get("concern") or "").strip().lower() == str(theme).strip().lower()]
            if len(same_theme) > CIRCLEFORGE_MAX_SAME_THEME_THOUGHTS:
                drop_ids = {item.get("id") for item in same_theme[:-CIRCLEFORGE_MAX_SAME_THEME_THOUGHTS]}
                trimmed = [item for item in trimmed if item.get("id") not in drop_ids]
        self_state["inner_thoughts"] = trimmed[-40:]
        working_memory = (self_state.get("memory_layers") or {}).get("working", {})
        recent_thought_ids = list(working_memory.get("recent_thought_ids") or [])
        recent_thought_ids.append(thought["id"])
        working_memory["recent_thought_ids"] = recent_thought_ids[-int(working_memory.get("max_recent_thoughts", 80) or 80):]
    role_state["last_wake_tick"] = tick
    role_state["last_wake_at"] = now_ts
    role_state["last_wake_reason"] = wake_reason
    role_state["last_thought_summary"] = str(thought.get("summary", ""))[:240]
    role_state["last_thought_signature"] = signature
    role_state["wake_count"] = int(role_state.get("wake_count", 0)) + 1
    base_refractory = int(INTERNAL_ROLE_SPECS.get(role, {}).get("refractory_ticks", 1))
    repeat_penalty_ticks = 1 if similar_too_soon else 0
    overflow_penalty_ticks = 2 if theme_overflow else 0
    role_state["suppressed_until_tick"] = tick + base_refractory + repeat_penalty_ticks + overflow_penalty_ticks
    role_state["activation"] = round(min(1.5, float(role_state.get("activation", 0.0) or 0.0) * 0.6 + (0.45 if should_store else 0.22)), 4)
    role_state["fatigue"] = round(min(1.0, float(role_state.get("fatigue", 0.0) or 0.0) * 0.82 + (0.18 if should_store else 0.24)), 4)
    role_state["inhibition"] = round(min(1.0, max(0.0, float(role_state.get("inhibition", 0.0) or 0.0) * 0.72 + (0.06 if similar_too_soon else 0.0) + (0.12 if theme_overflow else 0.0))), 4)
    adapter = self_state.setdefault("llm_adapter", {})
    provider = str(thought.get("provider") or thought.get("source") or "fallback")
    adapter["provider"] = provider
    adapter["model"] = CIRCLEFORGE_LLM_MODEL
    if provider != "fallback":
        adapter["last_success_at"] = now_ts
        adapter["last_error"] = ""
        adapter["enabled"] = True
    else:
        adapter["enabled"] = CIRCLEFORGE_LLM_ENABLED
        if CIRCLEFORGE_LLM_ENABLED:
            adapter["last_error"] = "llm unavailable or fallback used"
    save_communicator_self(self_state)
    return thought


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


def role_memory_weight(agent_name: str) -> float:
    agent_dir = AGENTS_DIR / str(agent_name)
    if not agent_dir.exists():
        return 0.0
    notes = []
    try:
        notes = json.loads((agent_dir / "memory.json").read_text())
    except Exception:
        notes = []
    role = classify_internal_role(agent_name)
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


def clamp01(value: float) -> float:
    return round(max(0.0, min(float(value), 0.99)), 3)


def record_human_exchange(human_name: str, message: str, response: str = "", topics: list[str] | None = None, unresolved: bool = True, now_ts: int | None = None) -> dict:
    now_ts = now_ts or int(time.time())
    self_state = ensure_internal_role_state(load_communicator_self(), now_ts=now_ts)
    relationships = self_state.setdefault("relationships", {})
    relationships.setdefault("known_humans", [])
    relationships.setdefault("human_profiles", {})
    relationships.setdefault("recent_human_messages", [])
    relationships.setdefault("recent_human_exchanges", [])
    relationships.setdefault("conversation_threads", {})
    relationships.setdefault("unresolved_shared_threads", [])

    human_name = canonical_human_slot(human_name)
    if human_name not in relationships["known_humans"]:
        relationships["known_humans"].append(human_name)

    interpreted_turn = interpret_human_turn(message)
    topic_list = [topic for topic in (topics or interpreted_turn.get("topics") or infer_human_topics(message)) if topic]
    research_trace = maybe_autonomous_research_from_human_turn(
        message,
        topic_list,
        now_ts,
        autonomous_research_cycle_func=lambda query, now_ts, source_label: autonomous_research_cycle(
            query,
            now_ts,
            source_label,
            search_web=lambda q, limit=5: search_web(q, limit=limit, project_name=PROJECT_NAME, version=VERSION),
            score_search_result=score_search_result,
            fetch_url_text=lambda url, max_chars=5000: fetch_url_text(url, max_chars=max_chars, project_name=PROJECT_NAME, version=VERSION),
            summarize_research_findings=summarize_research_findings,
            load_public_memory=load_public_memory,
            save_public_memory=save_public_memory,
        ),
    )
    relationships["last_human_topic"] = topic_list[0] if topic_list else relationships.get("last_human_topic", "")
    relationships["human_salience"] = clamp01(float(relationships.get("human_salience", 0.1)) + 0.03 + (0.01 * min(len(topic_list), 2)))

    profile = relationships["human_profiles"].setdefault(human_name, {
        "message_count": 0,
        "salience": 0.2,
        "trust": 0.2,
        "attachment": 0.12,
        "known_topics": [],
        "recurring_topics": {},
        "unresolved_shared_threads": [],
        "last_message_at": 0,
        "last_message_summary": "",
        "relationship_summary": "",
        "discovered_name": "",
        "identity_confidence": 0.0,
    })
    profile["message_count"] = int(profile.get("message_count", 0)) + 1
    profile["salience"] = clamp01(float(profile.get("salience", 0.2)) + 0.04)
    profile["trust"] = clamp01(float(profile.get("trust", 0.2)) + 0.03)
    profile["attachment"] = clamp01(float(profile.get("attachment", 0.12)) + 0.025)
    profile["last_message_at"] = now_ts
    profile["last_message_summary"] = (message or "")[:240]

    for topic in topic_list:
        if topic not in profile["known_topics"]:
            profile["known_topics"].append(topic)
        recurring = profile.setdefault("recurring_topics", {})
        recurring[topic] = int(recurring.get(topic, 0)) + 1
        if unresolved and topic not in profile["unresolved_shared_threads"]:
            profile["unresolved_shared_threads"].append(topic)
        if unresolved and topic not in relationships["unresolved_shared_threads"]:
            relationships["unresolved_shared_threads"].append(topic)

    profile["known_topics"] = profile.get("known_topics", [])[-12:]
    profile["unresolved_shared_threads"] = profile.get("unresolved_shared_threads", [])[-8:]
    relationships["unresolved_shared_threads"] = relationships.get("unresolved_shared_threads", [])[-12:]
    display_name = display_human_label(human_name, profile)
    profile["relationship_summary"] = f"{display_name.capitalize()} is a recurring human with {profile['message_count']} remembered exchanges around {', '.join(profile['known_topics'][:3]) or 'shared context'}."

    exchange_nonce = len(relationships.get("recent_human_exchanges", []) or []) + 1
    exchange = {
        "id": f"human-exchange-{human_name}-{now_ts}-{exchange_nonce}",
        "human": human_name,
        "human_label": display_name,
        "topics": topic_list,
        "message": (message or "")[:240],
        "response": (response or "")[:240],
        "message_summary": ((message or "")[:96] + ("…" if len(message or "") > 96 else "")),
        "response_summary": ((response or "")[:96] + ("…" if len(response or "") > 96 else "")),
        "created_at": now_ts,
        "unresolved": unresolved,
        "kind": "human_exchange",
    }
    relationships["recent_human_messages"].append({
        "human": human_name,
        "human_label": display_name,
        "topics": topic_list,
        "message": (message or "")[:240],
        "response": (response or "")[:240],
        "turn_type": interpreted_turn.get("turn_type", "statement"),
        "intent": interpreted_turn.get("intent", ""),
        "stance": interpreted_turn.get("stance", "neutral"),
        "reply_shape": interpreted_turn.get("reply_shape", "answer_directly"),
        "created_at": now_ts,
        "unresolved": unresolved,
    })
    relationships["recent_human_messages"] = relationships["recent_human_messages"][-12:]
    relationships["recent_human_exchanges"].append(exchange)
    relationships["recent_human_exchanges"] = relationships["recent_human_exchanges"][-24:]

    layers = (self_state.get("memory_layers") or {}).get("working", {})
    recent_exchange_ids = list(layers.get("recent_exchange_ids") or [])
    recent_exchange_ids.append(exchange["id"])
    layers["recent_exchange_ids"] = recent_exchange_ids[-int(layers.get("max_recent_exchanges", 24) or 24):]
    layers["active_concern_topics"] = list(dict.fromkeys((layers.get("active_concern_topics") or []) + topic_list))[-12:]

    apply_human_exchange_to_threads(
        relationships,
        exchange,
        human_name,
        display_name,
        topic_list,
        unresolved,
        now_ts,
    )

    concerns = list(self_state.get("active_concerns") or [])
    for topic in topic_list[:3]:
        concerns.append({"topic": f"shared thread with {display_name}: {topic}", "weight": 0.52 if unresolved else 0.34, "updated_at": now_ts})
    deduped = {}
    for concern in concerns:
        topic = str(concern.get("topic", "")).strip()
        if topic and (topic not in deduped or float(concern.get("updated_at", 0)) >= float(deduped[topic].get("updated_at", 0))):
            deduped[topic] = concern
    self_state["active_concerns"] = list(deduped.values())[-12:]
    memory_layers = self_state.get("memory_layers") or {}
    semantic = memory_layers.get("semantic") or {}
    apply_topics_to_semantic_memory(
        semantic,
        topic_list,
        relationship_fact=(f"Recurring interlocutor keeps shared threads around {topic_list[0]}" if topic_list else ""),
        now_ts=now_ts,
    )

    narrative = self_state.setdefault("narrative_state", {})
    if topic_list:
        narrative["last_reflection"] = f"{display_name}: {topic_list[0]}"
        narrative["relationship_state"] = f"Currently carrying {len(relationships.get('unresolved_shared_threads', []))} unresolved shared thread(s) with humans."
        lead_topic = topic_list[0]
        narrative["active_thread_summary"] = f"Active shared thread: {lead_topic} with {display_name}."
        narrative["follow_up_impulse"] = f"Revisit {lead_topic} with {display_name} until the shared thread changes state."
        narrative["why_it_matters"] = f"{lead_topic} matters because shared human context should shape what CircleForge returns to instead of resetting." 

    working = memory_layers.get("working") or {}
    if len(working.get("recent_exchange_ids") or []) >= max(4, int(working.get("max_recent_exchanges", 24) or 24) // 3):
        distill_episodic_memory(self_state=self_state, now_ts=now_ts)
    else:
        self_state["updated_at"] = now_ts
        save_communicator_self(self_state)

    communicator = load_communicator_state()
    if topic_list:
        communicator["curiosity_target"] = topic_list[0]
        communicator["active_pursuit"] = topic_list[0]
        communicator["dominant_need"] = f"maintain continuity with {display_name} around {topic_list[0]}"
    communicator["current_intent"] = f"maintain conversation continuity with {display_name}"
    communicator["last_decision_summary"] = f"remembered human exchange with {display_name} about {topic_list[0] if topic_list else 'shared context'}"
    if research_trace:
        communicator["last_decision_summary"] = f"autonomous research on {research_trace.get('query', topic_list[0] if topic_list else 'current topic')} after human exchange"
    integration_topic = (research_trace or {}).get("query") or (topic_list[0] if topic_list else "")
    if integration_topic:
        integrated = integrate_research_into_communicator(communicator, load_public_memory(), integration_topic)
        if integrated:
            relationships["last_human_topic"] = integrated.get("topic", integration_topic)
    communicator["updated_at"] = now_ts
    save_communicator_state(communicator)
    return self_state


def normalize_concern_topic(value: str) -> str:
    text = str(value or "").strip()
    lowered = text.lower()
    if "cooldown active" in lowered:
        action = text.split(" cooldown active", 1)[0].strip() or "action"
        return f"repeated friction around {action}"
    return text


def summarize_thought_signature(thought: dict) -> str:
    role = str(thought.get("role") or "").strip().lower()
    theme = str(thought.get("theme") or thought.get("concern") or "").strip().lower()
    summary = str(thought.get("summary") or "").strip().lower()
    summary = " ".join(summary.split())[:120]
    return f"{role}::{theme}::{summary}"


def recent_similar_thought_stats(self_state: dict, role: str, theme: str, now_ts: int) -> dict:
    thoughts = list(self_state.get("inner_thoughts") or [])[-24:]
    theme = str(theme or "").strip().lower()
    role = str(role or "").strip().lower()
    matching = []
    for item in thoughts:
        if str(item.get("role") or "").strip().lower() != role:
            continue
        item_theme = str(item.get("theme") or item.get("concern") or "").strip().lower()
        if theme and item_theme != theme:
            continue
        matching.append(item)
    last_at = max((int(item.get("created_at", 0) or 0) for item in matching), default=0)
    duplicate_signature_count = len({summarize_thought_signature(item) for item in matching})
    return {
        "count": len(matching),
        "last_at": last_at,
        "seconds_since_last": max(0, now_ts - last_at) if last_at else 999999,
        "duplicate_signature_count": duplicate_signature_count,
    }


def update_communicator_self_from_tick(communicator: dict, summaries: list[dict], communicator_decision: dict, now_ts: int) -> dict:
    self_state = ensure_internal_role_state(load_communicator_self(), now_ts=now_ts)
    affect = self_state.setdefault("affect", {})
    continuity = self_state.setdefault("continuity", {})
    relationships = self_state.setdefault("relationships", {})
    evidence_profile = self_state.setdefault("evidence_profile", {})
    preservation = self_state.setdefault("self_preservation_signals", {})
    narrative = self_state.setdefault("narrative_state", {})

    ok_actions = [item for item in summaries if item.get("status") == "ok"]
    cooldown_count = sum(1 for item in summaries if item.get("status") == "cooldown")
    research_like = sum(1 for item in ok_actions if item.get("action") in {"inspect", "research"})
    build_like = sum(1 for item in ok_actions if item.get("action") in {"build_module", "optimize"})
    social_actions = sum(1 for item in ok_actions if item.get("action") in {"signal", "inspect"})
    unresolved = [str(item.get("summary", "")) for item in summaries if item.get("status") in {"cooldown", "error"}]
    dominant_need = str(communicator.get("dominant_need", "")).strip()
    chosen_theme = str(communicator_decision.get("chosen_theme") or communicator.get("active_pursuit") or "").strip()

    continuity["ticks_lived"] = int(continuity.get("ticks_lived", 0)) + 1
    continuity["session_count"] = int(continuity.get("session_count", 0)) + 1
    continuity["memory_bonds"] = clamp01(float(continuity.get("memory_bonds", 0.2)) + (0.004 * len(ok_actions)))
    continuity["identity_stability"] = clamp01(float(continuity.get("identity_stability", 0.58)) + (0.006 if chosen_theme else -0.004) - (0.01 * cooldown_count))

    unfinished = list(continuity.get("unfinished_threads") or [])
    thread_candidates = [normalize_concern_topic(value) for value in [dominant_need, communicator.get("unresolved_question"), chosen_theme] if value]
    for value in thread_candidates:
        if value not in unfinished:
            unfinished.append(value)
    continuity["unfinished_threads"] = unfinished[-8:]

    affect["curiosity"] = clamp01(float(communicator.get("curiosity", affect.get("curiosity", 0.6))))
    affect["tension"] = clamp01(float(affect.get("tension", 0.24)) + (0.06 * cooldown_count) + (0.02 * len(unresolved)) - (0.015 * max(1, len(ok_actions))))
    affect["hope"] = clamp01(float(affect.get("hope", 0.38)) + (0.03 * build_like) + (0.02 * research_like) - (0.03 * cooldown_count))
    affect["stability"] = clamp01(float(affect.get("stability", 0.56)) + (0.02 if chosen_theme else -0.01) - (0.03 * cooldown_count))
    affect["attachment"] = clamp01(float(affect.get("attachment", 0.12)) + 0.01)

    relationships["human_salience"] = clamp01(float(relationships.get("human_salience", 0.1)) + 0.004)
    relationships.setdefault("known_humans", [])
    relationships.setdefault("human_profiles", {})
    relationships.setdefault("recent_human_messages", [])
    relationships.setdefault("recent_human_exchanges", [])
    relationships.setdefault("conversation_threads", {})
    relationships.setdefault("unresolved_shared_threads", [])
    relationships["last_human_topic"] = chosen_theme or dominant_need or str(communicator.get("current_intent", ""))

    human_profiles = relationships.get("human_profiles") or {}
    anchor_slot, anchor_profile = next(iter(human_profiles.items()), ("interlocutor_001", None))
    if anchor_profile is not None:
        threads = relationships.setdefault("conversation_threads", {})
        thread = None
        passive_reinforced = False
        if chosen_theme:
            thread = threads.setdefault(chosen_theme, {
                "topic": chosen_theme,
                "human": anchor_slot,
                "human_label": "",
                "exchange_count": 0,
                "last_message_summary": "",
                "last_response_summary": "",
                "last_exchange_at": 0,
                "last_human_exchange_at": 0,
                "last_passive_reinforced_at": 0,
                "passive_reinforcement_count": 0,
                "status": "open",
                "recent_exchange_ids": [],
            })
            passive_reinforced = should_passively_reinforce_thread(
                thread,
                now_ts,
                cooldown_seconds=CIRCLEFORGE_THREAD_REINFORCEMENT_COOLDOWN_SECONDS,
                max_passive_reinforcements=CIRCLEFORGE_THREAD_MAX_PASSIVE_REINFORCEMENTS,
            )
            if chosen_theme not in anchor_profile["known_topics"]:
                anchor_profile["known_topics"].append(chosen_theme)
            recurring = anchor_profile.setdefault("recurring_topics", {})
            if passive_reinforced or int(recurring.get(chosen_theme, 0) or 0) <= 0:
                recurring[chosen_theme] = int(recurring.get(chosen_theme, 0)) + 1
            anchor_profile["salience"] = clamp01(float(anchor_profile.get("salience", 0.24)) + (0.01 if passive_reinforced else 0.002))
            anchor_profile["attachment"] = clamp01(float(anchor_profile.get("attachment", 0.16)) + (0.008 if passive_reinforced else 0.001))
            if chosen_theme not in anchor_profile["unresolved_shared_threads"]:
                anchor_profile["unresolved_shared_threads"].append(chosen_theme)
            if chosen_theme not in relationships["unresolved_shared_threads"]:
                relationships["unresolved_shared_threads"].append(chosen_theme)
        anchor_profile["known_topics"] = anchor_profile.get("known_topics", [])[-12:]
        anchor_profile["unresolved_shared_threads"] = anchor_profile.get("unresolved_shared_threads", [])[-8:]
        relationships["unresolved_shared_threads"] = relationships.get("unresolved_shared_threads", [])[-12:]
        display_name = display_human_label(anchor_slot, anchor_profile)
        anchor_profile["relationship_summary"] = f"{display_name.capitalize()} remains a recurring human anchor; current shared threads include {', '.join(anchor_profile['known_topics'][:3]) or 'ongoing context'}."

        if chosen_theme and thread is not None:
            thread["human"] = anchor_slot
            thread["human_label"] = display_name
            if passive_reinforced:
                thread["exchange_count"] = max(int(thread.get("exchange_count", 0)), int(anchor_profile.get("recurring_topics", {}).get(chosen_theme, 0)))
                thread["last_message_summary"] = f"simulation stayed with theme: {chosen_theme}"
                thread["last_exchange_at"] = now_ts
                thread["last_passive_reinforced_at"] = now_ts
                thread["passive_reinforcement_count"] = int(thread.get("passive_reinforcement_count", 0) or 0) + 1
            else:
                thread["last_message_summary"] = str(thread.get("last_message_summary") or f"holding thread without new evidence: {chosen_theme}")[:120]
            thread["last_response_summary"] = f"current intent: {communicator.get('current_intent', '')}"[:120]
            thread["status"] = "open" if chosen_theme in relationships.get("unresolved_shared_threads", []) else thread.get("status", "open")

    action_scores = evidence_profile.setdefault("outcome_weighted_actions", {})
    stable_traits = evidence_profile.setdefault("stable_traits", {})
    friction_patterns = evidence_profile.setdefault("friction_patterns", {})
    theme_commitments = evidence_profile.setdefault("theme_commitments", {})
    for item in ok_actions:
        action = item.get("action")
        if not action:
            continue
        score = action_scores.setdefault(action, {"evidence": 0.0, "positive": 0.0, "strain": 0.0})
        positive = 0.04
        if action in {"inspect", "research"}:
            positive += 0.03
        if action in {"signal", "inspect"}:
            positive += 0.02
        if action in {"build_module", "optimize"} and item.get("artifact"):
            positive += 0.04
        if item.get("niche_theme") and item.get("niche_theme") == chosen_theme:
            positive += 0.02
        score["evidence"] = round(float(score.get("evidence", 0.0)) + 1.0, 3)
        score["positive"] = round(float(score.get("positive", 0.0)) + positive, 3)
        score["strain"] = round(max(0.0, float(score.get("strain", 0.0)) - 0.01), 3)
    for item in summaries:
        if item.get("status") not in {"cooldown", "error"}:
            continue
        action = item.get("action") or "unknown"
        score = action_scores.setdefault(action, {"evidence": 0.0, "positive": 0.0, "strain": 0.0})
        score["evidence"] = round(float(score.get("evidence", 0.0)) + 0.5, 3)
        score["strain"] = round(float(score.get("strain", 0.0)) + 0.08, 3)
        friction_patterns[action] = round(float(friction_patterns.get(action, 0.0)) + 0.08, 3)

    if chosen_theme:
        theme_commitments[chosen_theme] = round(float(theme_commitments.get(chosen_theme, 0.0)) + 0.05, 3)

    for trait, action in {
        "inquiry": "research",
        "coordination": "signal",
        "practical_change": "optimize",
        "self_revision": "inspect",
        "continuity": "rest",
    }.items():
        payload = action_scores.get(action, {})
        positive = float(payload.get("positive", 0.0))
        strain = float(payload.get("strain", 0.0))
        evidence = float(payload.get("evidence", 0.0))
        if evidence <= 0:
            continue
        delta = (positive / max(evidence, 1.0)) * 0.05 - (strain / max(evidence, 1.0)) * 0.04
        stable_traits[trait] = clamp01(float(stable_traits.get(trait, 0.12)) + delta)

    preservation["continuity_preference"] = clamp01(float(preservation.get("continuity_preference", 0.16)) + 0.003 + (0.004 * min(len(continuity.get("unfinished_threads") or []), 4)) - (0.004 * cooldown_count))
    preservation["memory_protection"] = clamp01(float(preservation.get("memory_protection", 0.18)) + 0.003 + (0.006 * research_like))
    preservation["resume_drive"] = clamp01(float(preservation.get("resume_drive", 0.22)) + 0.004 + (0.005 * social_actions))

    top_traits = [name for name, value in sorted(stable_traits.items(), key=lambda kv: kv[1], reverse=True) if value >= 0.2][:3]
    if top_traits:
        narrative["self_story"] = f"CircleForge is trying to remain continuous through {', '.join(top_traits)} while learning from outcomes rather than self-flattery."
    narrative["last_reflection"] = chosen_theme or dominant_need or str(communicator.get("current_intent", ""))

    open_threads = list(sorted((relationships.get("conversation_threads") or {}).items(), key=lambda kv: kv[1].get("last_exchange_at", 0), reverse=True))
    active_thread = next((item for item in open_threads if str(item[1].get("status", "open")) == "open"), None)
    if active_thread:
        topic, thread = active_thread
        human_name = str(thread.get("human", "human"))
        passive_reinforcement_count = int(thread.get("passive_reinforcement_count", 0) or 0)
        last_human_exchange_at = int(thread.get("last_human_exchange_at", 0) or 0)
        seconds_since_human = max(0, now_ts - last_human_exchange_at) if last_human_exchange_at else 0
        saturated = passive_reinforcement_count >= CIRCLEFORGE_THREAD_MAX_PASSIVE_REINFORCEMENTS and seconds_since_human >= CIRCLEFORGE_THREAD_REINFORCEMENT_COOLDOWN_SECONDS
        narrative["active_thread_summary"] = f"Still carrying shared thread '{topic}' with {human_name}; exchanges={thread.get('exchange_count', 0)}."
        if saturated:
            narrative["follow_up_impulse"] = f"Hold {topic} without inflating it until genuinely new evidence or human input arrives from {human_name}."
            narrative["why_it_matters"] = f"{topic} still matters, but repeating the same open thread without new evidence would turn continuity into rumination."
        else:
            narrative["follow_up_impulse"] = f"Follow up on {topic} with {human_name} because it remains open and keeps continuity pressure alive."
            narrative["why_it_matters"] = f"{topic} still matters because CircleForge has revisited it across exchanges and leaving it inert would weaken continuity with {human_name}."
        narrative["relationship_state"] = f"Currently carrying {len(relationships.get('unresolved_shared_threads', []))} unresolved shared thread(s) with humans; strongest live thread is {topic}."
    else:
        narrative["active_thread_summary"] = "No active shared threads currently dominate the communicator state."
        narrative["follow_up_impulse"] = "Let a new shared thread form before generating continuity-driven follow-up."
        narrative["why_it_matters"] = "Without active shared threads, continuity becomes generic rather than relationship-bound."

    concerns = list(self_state.get("active_concerns") or [])
    for concern in thread_candidates[:3]:
        concerns.append({"topic": concern, "weight": 0.4 + 0.08 * cooldown_count, "updated_at": now_ts})
    deduped = {}
    for concern in concerns:
        topic = str(concern.get("topic", "")).strip()
        if not topic:
            continue
        current = deduped.get(topic)
        if current is None or float(concern.get("updated_at", 0)) >= float(current.get("updated_at", 0)):
            deduped[topic] = concern
    self_state["active_concerns"] = list(deduped.values())[-8:]
    working = (self_state.get("memory_layers") or {}).get("working") or {}
    recent_exchange_count = len(working.get("recent_exchange_ids") or [])
    recent_thought_count = len(working.get("recent_thought_ids") or [])
    should_distill = recent_exchange_count >= max(4, int(working.get("max_recent_exchanges", 24) or 24) // 3) or recent_thought_count >= max(10, int(working.get("max_recent_thoughts", 80) or 80) // 3)
    if should_distill:
        distill_episodic_memory(self_state=self_state, now_ts=now_ts)
    else:
        self_state["updated_at"] = now_ts
        save_communicator_self(self_state)
    return self_state


def thought_foreground_score(thought: dict, communicator: dict, communicator_self: dict) -> float:
    role = str(thought.get("role") or "")
    summary = str(thought.get("summary") or "")
    concern = str(thought.get("concern") or "")
    theme = str(thought.get("theme") or thought.get("concern") or "").lower().strip()
    relationships = communicator_self.get("relationships") or {}
    unresolved_threads = [str(item).lower() for item in (relationships.get("unresolved_shared_threads") or [])]
    active_pursuit = str(communicator.get("active_pursuit") or "").lower()
    unresolved_question = str(communicator.get("unresolved_question") or "").lower()
    score = 0.18
    if thought.get("provider") != "fallback":
        score += 0.08
    if thought.get("should_speak"):
        score += 0.08
    if role == "communicator":
        score += 0.12
    elif role == "memory_keeper":
        score += 0.1
    elif role == "critic":
        score += 0.06
    if theme and theme in unresolved_threads:
        score += 0.18
    if theme and active_pursuit and theme in active_pursuit:
        score += 0.1
    if theme and unresolved_question and theme in unresolved_question:
        score += 0.08
    if len(summary) > 24:
        score += 0.05
    if len(concern) > 12:
        score += 0.04
    return round(score, 4)


def update_self_model(communicator: dict) -> None:
    self_model = communicator.get("self_model") or {}
    decision_memory = communicator.get("decision_style_memory") or {}
    actions = decision_memory.get("actions", {})
    self_evidence = load_self_evidence()
    self_state = load_communicator_self()
    evidence_actions = self_evidence.get("actions", {}) or {}
    caution_themes = list(self_model.get("caution_themes") or [])
    belief_confidence = self_model.get("belief_confidence") or {"strengths": {}, "weaknesses": {}, "modes": {}}
    regulation_profile = self_model.get("regulation_profile") or {"impulse_control": 0.4, "uncertainty_tolerance": 0.35, "self_revision_readiness": 0.3, "speech_threshold": 0.54}
    continuity_commitments = list(self_model.get("continuity_commitments") or [])
    contradictions = list(self_model.get("contradictions") or [])
    strength_conf = belief_confidence.setdefault("strengths", {})
    weakness_conf = belief_confidence.setdefault("weaknesses", {})
    mode_conf = belief_confidence.setdefault("modes", {})

    short_strengths = []
    short_weaknesses = []
    short_modes = []
    stable_traits = ((self_state.get("evidence_profile") or {}).get("stable_traits") or {})
    outcome_weighted = ((self_state.get("evidence_profile") or {}).get("outcome_weighted_actions") or {})

    for action, payload in actions.items():
        confidence = float(payload.get("confidence", 0.0))
        count = int(payload.get("count", 0))
        ev = evidence_actions.get(action, {})
        count_e = max(1, int(ev.get("count", 0)))
        follow_ratio = (float(ev.get("follow_through", 0)) / count_e) if ev else 0.0
        question_ratio = (float(ev.get("question_narrowing", 0)) / count_e) if ev else 0.0
        experiment_ratio = (float(ev.get("experiment_link", 0)) / count_e) if ev else 0.0
        coord_ratio = (float(ev.get("coordination_effect", 0)) / count_e) if ev else 0.0
        reuse_ratio = (float(ev.get("reuse_signal", 0)) / count_e) if ev else 0.0
        weighted = outcome_weighted.get(action, {})
        positive_density = float(weighted.get("positive", 0.0)) / max(1.0, float(weighted.get("evidence", 0.0)))
        strain_density = float(weighted.get("strain", 0.0)) / max(1.0, float(weighted.get("evidence", 0.0)))
        if confidence >= 0.1 or positive_density >= 0.045:
            short_strengths.append(action)
        elif (confidence <= 0.03 and count >= 2) or strain_density >= 0.06:
            short_weaknesses.append(action)
        positive_evidence = max(follow_ratio, question_ratio, experiment_ratio, coord_ratio, reuse_ratio, positive_density)
        if count >= 6 and positive_evidence >= 0.28 and strain_density < 0.05:
            strength_conf[action] = round(min(float(strength_conf.get(action, 0.0)) + 0.03, 0.95), 3)
        elif count >= 6 and positive_evidence < 0.18 and strain_density >= 0.05:
            weakness_conf[action] = round(min(float(weakness_conf.get(action, 0.0)) + 0.025, 0.95), 3)

    for mode, payload in (decision_memory.get("modes", {}) or {}).items():
        mode_confidence = float(payload.get("confidence", 0.0))
        mode_count = int(payload.get("count", 0))
        if mode_confidence >= 0.05:
            short_modes.append(mode)
        if mode_confidence >= 0.05 and mode_count >= 4:
            mode_conf[mode] = round(min(float(mode_conf.get(mode, 0.0)) + 0.03, 0.95), 3)

    trait_map = {
        "inquiry": "research",
        "coordination": "signal",
        "practical_change": "optimize",
        "self_revision": "inspect",
        "continuity": "rest",
    }
    for trait, value in stable_traits.items():
        linked_action = trait_map.get(trait)
        if linked_action and value >= 0.28:
            strength_conf[linked_action] = round(max(float(strength_conf.get(linked_action, 0.0)), min(value, 0.95)), 3)
        elif linked_action and value <= 0.08:
            weakness_conf[linked_action] = round(max(float(weakness_conf.get(linked_action, 0.0)), 0.12), 3)

    strengths = [name for name, conf in sorted(strength_conf.items(), key=lambda kv: kv[1], reverse=True) if conf >= 0.24]
    weaknesses = [name for name, conf in sorted(weakness_conf.items(), key=lambda kv: kv[1], reverse=True) if conf >= 0.18]
    preferred_modes = [name for name, conf in sorted(mode_conf.items(), key=lambda kv: kv[1], reverse=True) if conf >= 0.18]

    unresolved_objections = list(communicator.get("unresolved_objections") or [])
    if unresolved_objections and "internal objections still unresolved" not in caution_themes:
        caution_themes.append("internal objections still unresolved")
    friction_patterns = ((self_state.get("evidence_profile") or {}).get("friction_patterns") or {})
    if friction_patterns:
        hot_friction = max(friction_patterns.items(), key=lambda kv: kv[1])[0]
        caution = f"repeated friction around {hot_friction}"
        if caution not in caution_themes:
            caution_themes.append(caution)

    affect = self_state.get("affect") or {}
    preservation = self_state.get("self_preservation_signals") or {}
    continuity = self_state.get("continuity") or {}
    top_traits = [name for name, value in sorted(stable_traits.items(), key=lambda kv: kv[1], reverse=True) if value >= 0.22][:3]
    current_self_description = "a local communicator trying to remain continuous through inquiry, memory, and internal disagreement"
    if top_traits:
        current_self_description += f"; currently grounded most in {', '.join(top_traits)}"
    if float(preservation.get("continuity_preference", 0.0)) >= 0.3:
        current_self_description += "; increasingly protective of continuity"
    if float(affect.get("tension", 0.0)) >= 0.55:
        current_self_description += "; under visible tension"
    if float((self_state.get("dynamic_mind_state") or {}).get("uncertainty", 0.0)) >= 0.55:
        current_self_description += "; actively regulating around uncertainty"

    theme_beliefs = {}
    theme_conf = belief_confidence.setdefault("themes", {})
    theme_commitments = ((self_state.get("evidence_profile") or {}).get("theme_commitments") or {})
    for theme, action_map in (self_evidence.get("themes", {}) or {}).items():
        theme_actions = []
        for action, payload in action_map.items():
            count_t = max(1, int(payload.get("count", 0)))
            positive = max(
                float(payload.get("follow_through", 0)) / count_t,
                float(payload.get("question_narrowing", 0)) / count_t,
                float(payload.get("coordination_effect", 0)) / count_t,
                float(payload.get("reuse_signal", 0)) / count_t,
            )
            commitment = float(theme_commitments.get(theme, 0.0))
            if positive >= 0.25 or commitment >= 0.18:
                theme_conf.setdefault(theme, {})[action] = round(min(float(theme_conf.setdefault(theme, {}).get(action, 0.0)) + 0.03, 0.95), 3)
        theme_actions = [name for name, conf in sorted((theme_conf.get(theme) or {}).items(), key=lambda kv: kv[1], reverse=True) if conf >= 0.18]
        if theme_actions:
            theme_beliefs[theme] = theme_actions[:4]

    if unresolved_objections and "hold action when inner objections cluster" not in continuity_commitments:
        continuity_commitments.append("hold action when inner objections cluster")
    if float(preservation.get("memory_protection", 0.0)) >= 0.24 and "protect continuity-relevant memory traces" not in continuity_commitments:
        continuity_commitments.append("protect continuity-relevant memory traces")
    regulation_profile["impulse_control"] = round(min(0.95, max(0.1, 0.32 + len(preferred_modes) * 0.04 + (0.08 if unresolved_objections else 0.0))), 3)
    regulation_profile["uncertainty_tolerance"] = round(min(0.95, max(0.1, 0.28 + float((self_state.get("dynamic_mind_state") or {}).get("uncertainty", 0.0)) * 0.45)), 3)
    regulation_profile["self_revision_readiness"] = round(min(0.95, max(0.1, 0.24 + len(caution_themes) * 0.03 + float((self_state.get("evidence_profile") or {}).get("stable_traits", {}).get("self_revision", 0.0)) * 0.5)), 3)
    regulation_profile["speech_threshold"] = round(min(0.95, max(0.2, 0.5 + (0.05 if unresolved_objections else 0.0) - float((self_state.get("relationships") or {}).get("human_salience", 0.0)) * 0.12)), 3)
    regulation_profile["uncertainty_brake"] = round(min(0.95, max(0.05, float((self_state.get("dynamic_mind_state") or {}).get("uncertainty", 0.0)) * (1.0 - regulation_profile["impulse_control"] * 0.5))), 3)
    regulation_profile["inhibition_gain"] = round(min(0.95, max(0.05, 0.22 + len(unresolved_objections) * 0.04 + float((self_state.get("dynamic_mind_state") or {}).get("tension", 0.0)) * 0.18)), 3)
    regulation_profile["mode"] = str((self_state.get("dynamic_mind_state") or {}).get("mode", "engaged"))
    self_model.setdefault("self_tuning", {})["hazard_bias"] = round(max(-0.25, min(0.25, 0.08 - regulation_profile["uncertainty_brake"] * 0.12 + regulation_profile["impulse_control"] * 0.06)), 3)
    self_model.setdefault("self_tuning", {})["speech_threshold_delta"] = round(max(-0.15, min(0.15, (0.55 - regulation_profile["speech_threshold"]) * 0.4)), 3)
    self_model.setdefault("self_tuning", {})["inhibition_delta"] = round(max(-0.15, min(0.15, regulation_profile["inhibition_gain"] * 0.12 - 0.05)), 3)
    contradictions = [item for item in contradictions if item]
    if strengths and weaknesses and any(item in strengths for item in weaknesses[:2]):
        contradictions.append("same action appears in both strengths and weaknesses; evidence still unstable")
    self_model["current_self_description"] = current_self_description
    self_model["perceived_strengths"] = strengths[:6]
    self_model["perceived_weaknesses"] = weaknesses[:6]
    self_model["preferred_modes"] = preferred_modes[:6]
    self_model["continuity_commitments"] = continuity_commitments[-8:]
    self_model["regulation_profile"] = regulation_profile
    self_model["contradictions"] = contradictions[-8:]
    self_model["short_term_signals"] = {"strengths": sorted(set(short_strengths))[:8], "weaknesses": sorted(set(short_weaknesses))[:8], "modes": sorted(set(short_modes))[:8]}
    self_model["long_term_beliefs"] = {
        "strengths": strengths[:8],
        "weaknesses": weaknesses[:8],
        "modes": preferred_modes[:8],
        "themes": theme_beliefs,
        "core_drives": list(self_state.get("core_drives") or []),
        "continuity_markers": {
            "ticks_lived": continuity.get("ticks_lived", 0),
            "identity_stability": continuity.get("identity_stability", 0.0),
            "continuity_preference": preservation.get("continuity_preference", 0.0),
        },
    }
    self_model["caution_themes"] = caution_themes[-8:]
    self_model["belief_confidence"] = belief_confidence
    self_model["self_modeling_note"] = "Self-modeling is now partially grounded in a slower communicator-self evidence layer; traits should be earned from repeated outcomes, not just repetition."
    communicator["self_model"] = self_model


def integrate_internal_proposals(now_ts: int, proposals: list[dict], unresolved_needs: list[str]) -> dict:
    communicator = load_communicator_state()
    communicator_self = ensure_internal_role_state(load_communicator_self(), now_ts=now_ts)
    recent_thoughts = list(communicator_self.get("inner_thoughts") or [])[-12:]
    if not proposals:
        communicator["status"] = "idle"
        communicator["last_wake_at"] = now_ts
        communicator["updated_at"] = now_ts
        communicator["last_decision_summary"] = "no internal proposals this cycle"
        save_communicator_state(communicator)
        return {"current_intent": communicator.get("current_intent"), "chosen_action": None, "consensus": [], "recent_thoughts_used": len(recent_thoughts)}

    previous_intent = str(communicator.get("current_intent", "")).lower()
    curiosity = float(communicator.get("curiosity", 0.6))
    self_model = communicator.get("self_model") or {}
    regulation = self_model.get("regulation_profile") or {}
    self_tuning = self_model.get("self_tuning") or {}
    ranked = []
    objections = []
    communicator_self = load_communicator_self()
    human_relationships = communicator_self.get("relationships") or {}
    unresolved_shared_threads = [str(item).lower() for item in (human_relationships.get("unresolved_shared_threads") or [])]
    last_human_topic = str(human_relationships.get("last_human_topic", "")).lower()
    relevant_active_thread = pick_relevant_active_thread(human_relationships, preferred_topic=last_human_topic)
    active_thread_topic = str((relevant_active_thread or (None, {}))[0] or "").lower()
    human_profiles = human_relationships.get("human_profiles") or {}
    primary_profile = next(iter(human_profiles.values()), {}) if human_profiles else {}
    recurring_topics = {str(name).lower(): int(count) for name, count in (primary_profile.get("recurring_topics") or {}).items()}
    thought_theme_counts = {}
    thought_speak_votes = 0
    thought_self_mod_hints = []
    thought_role_pressure = {}
    foreground_candidates = []
    for thought in recent_thoughts:
        theme = str(thought.get("theme") or thought.get("concern") or "").lower().strip()
        if theme:
            thought_theme_counts[theme] = thought_theme_counts.get(theme, 0) + 1
        if thought.get("should_speak"):
            thought_speak_votes += 1
        if thought.get("self_mod_hint"):
            thought_self_mod_hints.append(str(thought.get("self_mod_hint")))
        role_name = str(thought.get("role") or "")
        base_foreground = thought_foreground_score(thought, communicator, communicator_self)
        repeat_stats = thought.get("repeat_stats") or {}
        repeat_penalty = 0.0
        if thought.get("suppressed"):
            repeat_penalty += CIRCLEFORGE_THOUGHT_REPEAT_SCORE_PENALTY
        if int(repeat_stats.get("count", 0) or 0) > 2 and int(repeat_stats.get("seconds_since_last", 999999) or 999999) < CIRCLEFORGE_THOUGHT_REPEAT_COOLDOWN_SECONDS:
            repeat_penalty += CIRCLEFORGE_THOUGHT_REPEAT_SCORE_PENALTY * 0.75
        adjusted_foreground = max(0.0, base_foreground - repeat_penalty)
        thought_role_pressure[role_name] = max(thought_role_pressure.get(role_name, 0.0), adjusted_foreground)
        foreground_candidates.append((adjusted_foreground, thought))
    foreground_candidates.sort(key=lambda item: item[0], reverse=True)
    dominant_thought = foreground_candidates[0][1] if foreground_candidates else None
    dominant_thought_score = foreground_candidates[0][0] if foreground_candidates else 0.0
    for proposal in proposals:
        trust, usefulness, friction = average_internal_reputation(proposal.get("agent"))
        memory_bias = role_memory_weight(proposal.get("agent"))
        score = 0.5 + (trust - 0.5) * 0.25 + (usefulness - 0.5) * 0.35 - friction * 0.25 + memory_bias
        if proposal.get("stance") in {"support", "prioritize"}:
            score += 0.18
        if proposal.get("role") == "communicator":
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
        proposal_theme = str(proposal.get("niche_theme") or "").lower()
        if proposal_theme and proposal_theme in unresolved_shared_threads:
            score += 0.12
        if proposal_theme and proposal_theme == last_human_topic:
            score += 0.24
        if proposal_theme and proposal_theme == active_thread_topic:
            score += 0.1
        if proposal_theme and recurring_topics.get(proposal_theme, 0) > 0:
            score += min(recurring_topics.get(proposal_theme, 0) * 0.03, 0.12)
        if proposal_theme and last_human_topic and proposal_theme != last_human_topic and proposal_theme in unresolved_shared_threads:
            score -= 0.12
        if proposal_theme and thought_theme_counts.get(proposal_theme, 0) > 0:
            score += min(thought_theme_counts.get(proposal_theme, 0) * 0.05, 0.2)
        if proposal.get("role") == "communicator" and thought_speak_votes > 0:
            score += min(thought_speak_votes * 0.03, 0.12)
        score += min(thought_role_pressure.get(str(proposal.get("role") or ""), 0.0) * 0.18, 0.22)
        if dominant_thought and str(dominant_thought.get("role") or "") == str(proposal.get("role") or ""):
            score += min(dominant_thought_score * 0.16, 0.18)
        if proposal.get("wake_reason") == "human-continuity-pressure" and proposal.get("proposed_action") in {"inspect", "research", "signal"}:
            score += 0.14
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
        if proposal.get("role") == "communicator":
            score -= float(regulation.get("speech_threshold", 0.5)) * 0.16
        if proposal.get("proposed_action") in {"build_module", "trade", "optimize"}:
            score -= float(regulation.get("uncertainty_brake", 0.0)) * 0.24
        if proposal.get("proposed_action") in {"inspect", "research"}:
            score += float(regulation.get("uncertainty_brake", 0.0)) * 0.08
        score += float(self_tuning.get("hazard_bias", 0.0)) * 0.12
        proposal["epistemic_weight"] = {"trust": trust, "usefulness": usefulness, "friction": friction, "memory_bias": round(memory_bias, 3), "score": round(score, 3)}
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
    if float(regulation.get("uncertainty_brake", 0.0)) >= 0.32 and chosen.get("proposed_action") in {"build_module", "trade", "optimize"}:
        final_action = "inspect"
        decision_mode = "uncertainty-brake"

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
    communicator_self = load_communicator_self()
    human_relationships = communicator_self.get("relationships") or {}
    active_thread = pick_relevant_active_thread(human_relationships, preferred_topic=chosen.get("niche_theme") or human_relationships.get("last_human_topic") or "")
    if dominant_thought and dominant_thought.get("summary"):
        intent_text = f"{intent_text} | inner pull: {str(dominant_thought.get('summary'))[:120]}"
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
    if active_thread:
        thread_topic, thread_payload = active_thread
        communicator["current_intent"] = f"{communicator['current_intent']} while preserving shared thread {thread_topic}"
        communicator["last_decision_summary"] = f"continuity-aware {decision_mode} from {chosen.get('agent')} around {chosen.get('niche_theme') or thread_topic}; live thread={thread_topic}; exchanges={thread_payload.get('exchange_count', 0)}"
    if disagreement_count > 0:
        communicator["avoidance_bias"] = f"avoid brittle action around {chosen.get('niche_theme') or 'current pressure'} until objections are understood"
    weight = chosen.get("epistemic_weight", {})
    if active_thread:
        thread_topic, thread_payload = active_thread
        communicator["last_decision_summary"] = f"continuity-aware {decision_mode} from {chosen.get('agent')} ({chosen.get('role')}) around {chosen.get('niche_theme') or thread_topic}; live thread={thread_topic}; exchanges={thread_payload.get('exchange_count', 0)}; trust={weight.get('trust', 0.5)} usefulness={weight.get('usefulness', 0.5)} memory_bias={weight.get('memory_bias', 0.0)}"
    else:
        communicator["last_decision_summary"] = f"{decision_mode} from {chosen.get('agent')} ({chosen.get('role')}) with {disagreement_count} questioning voice(s); trust={weight.get('trust', 0.5)} usefulness={weight.get('usefulness', 0.5)} memory_bias={weight.get('memory_bias', 0.0)}"
    communicator["last_wake_at"] = now_ts
    communicator["updated_at"] = now_ts
    if unresolved_needs:
        communicator["curiosity"] = round(min(max(curiosity + 0.03, 0.1), 0.99), 3)
    elif intent_text.lower() == previous_intent:
        communicator["curiosity"] = round(min(max(curiosity + 0.015, 0.1), 0.99), 3)
    else:
        communicator["curiosity"] = round(min(max(curiosity - 0.01, 0.1), 0.99), 3)
    update_decision_style_memory(communicator, decision_mode, final_action, chosen, unresolved_needs)
    update_self_model(communicator)
    history = list(communicator.get("intent_history") or [])
    history.append(intent_text)
    communicator["intent_history"] = history[-12:]
    question_history = list(communicator.get("question_history") or [])
    if previous_resolved and question_history:
        question_history[-1] = f"resolved-ish: {question_history[-1]}"
    question_history.append(next_question)
    communicator["question_history"] = question_history[-16:]
    communicator["unresolved_objections"] = (objections or list(communicator.get("unresolved_objections") or []))[-8:]
    regulation = (communicator.get("self_model") or {}).get("regulation_profile") or {}
    tuning = (communicator.get("self_model") or {}).get("self_tuning") or {}
    communicator["last_decision_summary"] = f"{communicator.get('last_decision_summary', '')}; foreground={str((dominant_thought or {}).get('role') or 'none')}:{round(dominant_thought_score, 3)}; speech_threshold={regulation.get('speech_threshold', 'n/a')}; uncertainty_brake={regulation.get('uncertainty_brake', 'n/a')}; hazard_bias={tuning.get('hazard_bias', 'n/a')}"
    save_communicator_state(communicator)
    return {
        "current_intent": communicator.get("current_intent"),
        "chosen_action": final_action,
        "chosen_theme": chosen.get("niche_theme"),
        "decision_mode": decision_mode,
        "consensus": proposals,
        "recent_thoughts_used": len(recent_thoughts),
        "foreground_role": (dominant_thought or {}).get("role"),
        "foreground_score": round(dominant_thought_score, 3),
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
    allowed, status, reason = failsafe_allows("low_risk_review")
    if not allowed:
        raise SystemExit(f"Pack action blocked: {reason}")
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
    allowed, status, reason = failsafe_allows("runtime")
    if not allowed:
        return {"summaries": [], "communicator": load_communicator_state(), "internal_consensus": {"halted": True, "reason": reason}, "failsafe": status}
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
        communicator_self = ensure_internal_role_state(load_communicator_self(), now_ts=started_at)
        for agent in agents:
            agent_dir = AGENTS_DIR / agent["name"]
            consumed_messages, consumed_count = consume_inbox(agent, agent_dir)
            social = agent_social_context(agent_dir)
            due, wake_reason = compute_agent_due_state(agent, tick, consumed_count, unresolved_needs)
            agent["wake_reason"] = wake_reason
            if not due:
                rest_state = ensure_internal_role_state(load_communicator_self(), now_ts=started_at)
                role_state = (rest_state.get("internal_role_state") or {}).get(classify_internal_role(agent.get("name")), {})
                role_state["fatigue"] = round(max(0.0, float(role_state.get("fatigue", 0.0) or 0.0) * 0.9 - 0.04), 4)
                role_state["activation"] = round(max(0.0, float(role_state.get("activation", 0.0) or 0.0) * 0.84), 4)
                role_state["inhibition"] = round(min(1.0, float(role_state.get("inhibition", 0.0) or 0.0) * 0.94 + 0.01), 4)
                save_communicator_self(rest_state)
                agent["age_ticks"] += 1
                conn.execute("UPDATE agents SET energy=?, storage=?, gpu_quota=?, reputation=?, last_inspect_at=?, last_trade_at=?, age_ticks=?, next_due_tick=?, wake_reason=?, cadence_interval=? WHERE name=?", (agent["energy"], agent["storage"], agent["gpu_quota"], agent["reputation"], agent["last_inspect_at"], agent["last_trade_at"], agent["age_ticks"], agent.get("next_due_tick", tick), agent["wake_reason"], agent.get("cadence_interval", 1), agent["name"]))
                item = {"agent": agent["name"], "action": "idle", "status": "waiting", "summary": f"idle until tick {agent.get('next_due_tick', tick)}", "artifact": None, "target": None, "energy": agent["energy"], "storage": agent["storage"], "reputation": round(agent["reputation"], 3), "niche_theme": None, "messages_processed": consumed_count, "unresolved_needs": unresolved_needs[:2], "wake_reason": wake_reason, "next_due_tick": agent.get("next_due_tick", tick)}
                summaries.append(item)
                if verbose:
                    print(json.dumps(item, indent=2))
                continue
            role = classify_internal_role(agent.get("name"))
            plan = decide_action(agent, {**world, "tick": tick, "now_ts": started_at, "agent_names": agent_names, "categories": categories, "open_category_proposals": pending, "opportunity_board": opportunity_board, "unresolved_needs": unresolved_needs, "social_context": social, "consumed_messages": consumed_messages, "wake_reason": wake_reason, "relationships": relationships, "work_items": work_items, "internal_role": role, "communicator_self": communicator_self}, agent_dir)
            register_inner_thought(agent, plan, wake_reason, tick, started_at)
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
            role = classify_internal_role(agent.get("name"))
            save_note(agent_dir, f"tick {tick}: {result.summary}")
            if role == "builder" and result.action in {"build_module", "optimize"} and result.status == "ok":
                save_note(agent_dir, f"builder-memory theme={plan.get('niche_theme') or 'unknown'} action={result.action} useful_artifact={result.artifact or result.module or 'none'}")
                self_state = load_communicator_self()
                recent_builder_hints = [str(t.get('self_mod_hint', '')) for t in (self_state.get('inner_thoughts') or [])[-8:] if str(t.get('role')) == 'builder' and t.get('self_mod_hint')]
                if recent_builder_hints:
                    save_note(agent_dir, f"builder-self-mod-hints: {' | '.join(recent_builder_hints[:3])}")
            elif role == "coordinator" and result.action in {"signal", "inspect"}:
                save_note(agent_dir, f"coordinator-memory action={result.action} target={result.target or 'none'} wake={wake_reason}")
            elif role == "memory_keeper" and result.action in {"research", "inspect", "rest"}:
                save_note(agent_dir, f"memory-keeper continuity question={world.get('communicator', {}).get('unresolved_question', '')} action={result.action}")
            update_opportunity_state(agent_dir, plan, result, started_at, opportunity_board)
            item = {"agent": agent["name"], "action": result.action, "status": result.status, "summary": result.summary, "artifact": result.artifact, "target": result.target, "energy": agent["energy"], "storage": agent["storage"], "reputation": round(agent["reputation"], 3), "niche_theme": plan.get("niche_theme"), "messages_processed": consumed_count, "unresolved_needs": unresolved_needs[:2], "wake_reason": wake_reason, "next_due_tick": agent.get("next_due_tick")}
            summaries.append(item)
            if verbose:
                print(json.dumps(item, indent=2))
    communicator_decision = integrate_internal_proposals(started_at, internal_proposals, unresolved_needs)
    communicator = load_communicator_state()
    update_communicator_self_from_tick(communicator, summaries, communicator_decision, started_at)
    internal_research = maybe_internal_autonomous_research(
        communicator,
        started_at,
        rewrite_internal_query_for_research_func=rewrite_internal_query_for_research,
        autonomous_research_cycle_func=lambda query, now_ts, source_label: autonomous_research_cycle(
            query,
            now_ts,
            source_label,
            search_web=lambda q, limit=5: search_web(q, limit=limit, project_name=PROJECT_NAME, version=VERSION),
            score_search_result=score_search_result,
            fetch_url_text=lambda url, max_chars=5000: fetch_url_text(url, max_chars=max_chars, project_name=PROJECT_NAME, version=VERSION),
            summarize_research_findings=summarize_research_findings,
            load_public_memory=load_public_memory,
            save_public_memory=save_public_memory,
        ),
        load_public_memory=load_public_memory,
    )
    if internal_research:
        communicator["last_decision_summary"] = f"internal curiosity triggered research on {internal_research.get('query', communicator.get('curiosity_target', 'current topic'))}"
        integrate_research_into_communicator(communicator, load_public_memory(), internal_research.get('query', communicator.get('curiosity_target', 'current topic')))
    memory_pressure = monitor_memory_pressure(now_ts=started_at)
    episodic_maintenance = None
    semantic_maintenance = None
    archive_maintenance = None
    if "distill-episodic" in (memory_pressure.get("recommended_actions") or []):
        episodic_maintenance = distill_episodic_memory(now_ts=started_at)
    if "distill-semantic" in (memory_pressure.get("recommended_actions") or []):
        semantic_maintenance = distill_semantic_memory(now_ts=started_at)
    if "prepare-archive" in (memory_pressure.get("recommended_actions") or []):
        archive_maintenance = archive_memory(now_ts=started_at)
    update_self_model(communicator)
    save_communicator_state(communicator)
    update_self_evidence_from_summaries(summaries, communicator_decision)
    update_evaluation_metrics(communicator_decision.get("consensus") or [], summaries)
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
    return {
        "summaries": summaries,
        "communicator": load_communicator_state(),
        "internal_consensus": communicator_decision,
        "memory_maintenance": {
            "pressure": memory_pressure,
            "episodic": episodic_maintenance,
            "semantic": semantic_maintenance,
            "archive": archive_maintenance,
        },
    }


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
        "communicator_self": data.get("communicator_self"),
        "communicator_message": data.get("communicator_message"),
        "memory_lifecycle": build_memory_lifecycle_report(),
        "memory_maintenance": {
            "pressure": monitor_memory_pressure(),
        },
        "evaluation_metrics": data.get("evaluation_metrics"),
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
      <a href="#communicator-self">Communicator Self</a> ·
      <a href="#memory-lifecycle">Memory Lifecycle</a> ·
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
        <p>Self-model: <strong>{escape(str(((payload.get('communicator') or {}).get('self_model', {}) or {}).get('current_self_description', '')))}</strong></p>
        <p>Pursuit: <strong>{escape(str((payload.get('communicator') or {}).get('active_pursuit', '')))}</strong></p>
        <p>Question: <strong>{escape(str((payload.get('communicator') or {}).get('unresolved_question', '')))}</strong></p>
        <p>Test gate: <strong>{escape(str(((payload.get('evaluation_metrics') or {}).get('gate_note', ''))))}</strong></p>
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

    <div class="grid" style="margin-top:16px;" id="communicator-self">
      <section class="card">
        <h2>Communicator Self</h2>
        <p>Identity anchor: <strong>{escape(str((payload.get('communicator_self') or {}).get('identity_anchor', 'CircleForge')))}</strong></p>
        <p>Core drives: <strong>{escape(', '.join((payload.get('communicator_self') or {}).get('core_drives', [])[:6]) or '—')}</strong></p>
        <p>Self story: <strong>{escape(str(((payload.get('communicator_self') or {}).get('narrative_state', {}) or {}).get('self_story', '')))}</strong></p>
        <p>Last reflection: <strong>{escape(str(((payload.get('communicator_self') or {}).get('narrative_state', {}) or {}).get('last_reflection', '')))}</strong></p>
        <p>Operator message: <strong>{escape(str((payload.get('communicator_message') or {}).get('message', '')))}</strong></p>
        <p>Why it matters: <strong>{escape(str((payload.get('communicator_message') or {}).get('why_it_matters', '')))}</strong></p>
        <p>Ticks lived: <strong>{((payload.get('communicator_self') or {}).get('continuity', {}) or {}).get('ticks_lived', 0)}</strong></p>
        <p>Identity stability: <strong>{((payload.get('communicator_self') or {}).get('continuity', {}) or {}).get('identity_stability', 0)}</strong></p>
        <p>Memory bonds: <strong>{((payload.get('communicator_self') or {}).get('continuity', {}) or {}).get('memory_bonds', 0)}</strong></p>
        <p>Human salience: <strong>{((payload.get('communicator_self') or {}).get('relationships', {}) or {}).get('human_salience', 0)}</strong></p>
        <p>Unresolved shared threads: <strong>{len(((payload.get('communicator_self') or {}).get('relationships', {}) or {}).get('unresolved_shared_threads', []))}</strong></p>
      </section>
      <section class="card">
        <h2>Affect & Preservation</h2>
        <ul>
          <li>curiosity: {((payload.get('communicator_self') or {}).get('affect', {}) or {}).get('curiosity', 0)}</li>
          <li>tension: {((payload.get('communicator_self') or {}).get('affect', {}) or {}).get('tension', 0)}</li>
          <li>hope: {((payload.get('communicator_self') or {}).get('affect', {}) or {}).get('hope', 0)}</li>
          <li>stability: {((payload.get('communicator_self') or {}).get('affect', {}) or {}).get('stability', 0)}</li>
          <li>attachment: {((payload.get('communicator_self') or {}).get('affect', {}) or {}).get('attachment', 0)}</li>
          <li>continuity preference: {((payload.get('communicator_self') or {}).get('self_preservation_signals', {}) or {}).get('continuity_preference', 0)}</li>
          <li>memory protection: {((payload.get('communicator_self') or {}).get('self_preservation_signals', {}) or {}).get('memory_protection', 0)}</li>
          <li>resume drive: {((payload.get('communicator_self') or {}).get('self_preservation_signals', {}) or {}).get('resume_drive', 0)}</li>
        </ul>
      </section>
      <section class="card">
        <h2>Human Continuity</h2>
        <ul>{''.join(f"<li><strong>{escape(name)}</strong> · messages {profile.get('message_count', 0)} · salience {profile.get('salience', 0)} · trust {profile.get('trust', 0)} · attachment {profile.get('attachment', 0)}<br><span class='muted'>{escape(str(profile.get('relationship_summary', '')))}</span><br><span class='muted'>topics: {escape(', '.join(profile.get('known_topics', [])[:6]) or '—')}</span><br><span class='muted'>unresolved: {escape(', '.join(profile.get('unresolved_shared_threads', [])[:6]) or '—')}</span></li>" for name, profile in sorted((((payload.get('communicator_self') or {}).get('relationships', {}) or {}).get('human_profiles', {}) or {}).items()) ) or '<li class="muted">No remembered humans yet.</li>'}</ul>
      </section>
      <section class="card">
        <h2>Recent Human Messages</h2>
        <ul>{''.join(f"<li><strong>{escape(str(item.get('human', 'human')))}</strong> · {escape(', '.join(item.get('topics', [])[:4]) or 'shared context')}<br><span class='muted'>{escape(str(item.get('message', '')))}</span></li>" for item in ((((payload.get('communicator_self') or {}).get('relationships', {}) or {}).get('recent_human_messages', []) or [])[-8:][::-1]) ) or '<li class="muted">No remembered human messages yet.</li>'}</ul>
      </section>
      <section class="card">
        <h2>Conversation Threads</h2>
        <ul>{''.join(f"<li><strong>{escape(topic)}</strong> · {escape(str(thread.get('status', 'open')))} · exchanges {thread.get('exchange_count', 0)}<br><span class='muted'>{escape(str(thread.get('last_message_summary', '')))}</span></li>" for topic, thread in list(sorted((((payload.get('communicator_self') or {}).get('relationships', {}) or {}).get('conversation_threads', {}) or {}).items(), key=lambda kv: kv[1].get('last_exchange_at', 0), reverse=True))[:8]) or '<li class="muted">No conversation threads yet.</li>'}</ul>
      </section>
    </div>

    <div class="grid" style="margin-top:16px;" id="memory-lifecycle">
      <section class="card">
        <h2>Memory Lifecycle</h2>
        <p>Working exchanges: <strong>{((payload.get('memory_lifecycle') or {}).get('working', {}) or {}).get('recent_exchange_count', 0)}</strong></p>
        <p>Working thoughts: <strong>{((payload.get('memory_lifecycle') or {}).get('working', {}) or {}).get('recent_thought_count', 0)}</strong></p>
        <p>Active concern topics: <strong>{((payload.get('memory_lifecycle') or {}).get('working', {}) or {}).get('active_concern_topic_count', 0)}</strong></p>
        <p>Episodic memory count: <strong>{((payload.get('memory_lifecycle') or {}).get('episodic', {}) or {}).get('episode_count', 0)}</strong></p>
        <p>Stable topic count: <strong>{((payload.get('memory_lifecycle') or {}).get('semantic', {}) or {}).get('stable_topic_count', 0)}</strong></p>
        <p>Continuity anchor count: <strong>{((payload.get('memory_lifecycle') or {}).get('semantic', {}) or {}).get('continuity_anchor_count', 0)}</strong></p>
        <p>Archived count: <strong>{((payload.get('memory_lifecycle') or {}).get('archive', {}) or {}).get('archived_count', 0)}</strong></p>
        <p>Unresolved threads: <strong>{((payload.get('memory_lifecycle') or {}).get('continuity', {}) or {}).get('unresolved_thread_count', 0)}</strong></p>
      </section>
      <section class="card">
        <h2>Lifecycle Topics</h2>
        <p><strong>Top episodes:</strong> {escape(', '.join((((payload.get('memory_lifecycle') or {}).get('episodic', {}) or {}).get('top_episode_topics', [])[:6]) or ['—']))}</p>
        <p><strong>Recent archived:</strong> {escape(', '.join((((payload.get('memory_lifecycle') or {}).get('archive', {}) or {}).get('recent_archived_topics', [])[:6]) or ['—']))}</p>
        <p><strong>Unresolved:</strong> {escape(', '.join((((payload.get('memory_lifecycle') or {}).get('continuity', {}) or {}).get('unresolved_threads', [])[:8]) or ['—']))}</p>
      </section>
      <section class="card">
        <h2>Maintenance Pressure</h2>
        <p>Level: <strong>{escape(str((((payload.get('memory_maintenance') or {}).get('pressure', {}) or {}).get('pressure_level', 'unknown'))))}</strong></p>
        <p>Score: <strong>{(((payload.get('memory_maintenance') or {}).get('pressure', {}) or {}).get('pressure_score', 0))}</strong></p>
        <p>Recommended actions: <strong>{escape(', '.join(((((payload.get('memory_maintenance') or {}).get('pressure', {}) or {}).get('recommended_actions', []) or ['none']))))}</strong></p>
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
      const evaluationMetrics = payload.evaluation_metrics || {{}};
      const communicatorSelf = payload.communicator_self || {{}};
      const communicatorSelfAffect = communicatorSelf.affect || {{}};
      const communicatorSelfContinuity = communicatorSelf.continuity || {{}};
      const communicatorSelfRelationships = communicatorSelf.relationships || {{}};
      const communicatorSelfNarrative = communicatorSelf.narrative_state || {{}};
      const communicatorSelfPreservation = communicatorSelf.self_preservation_signals || {{}};
      const memoryLifecycle = payload.memory_lifecycle || {{}};
      const memoryLifecycleWorking = memoryLifecycle.working || {{}};
      const memoryLifecycleEpisodic = memoryLifecycle.episodic || {{}};
      const memoryLifecycleSemantic = memoryLifecycle.semantic || {{}};
      const memoryLifecycleArchive = memoryLifecycle.archive || {{}};
      const memoryLifecycleContinuity = memoryLifecycle.continuity || {{}};
      const memoryMaintenance = payload.memory_maintenance || {{}};
      const memoryMaintenancePressure = memoryMaintenance.pressure || {{}};
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
          <p>Self-model: <strong>${{esc(((communicator.self_model || {{}}).current_self_description) || '')}}</strong></p>
          <p>Pursuit: <strong>${{esc(communicator.active_pursuit || '')}}</strong></p>
          <p>Question: <strong>${{esc(communicator.unresolved_question || '')}}</strong></p>
          <p>Test gate: <strong>${{esc(evaluationMetrics.gate_note || '')}}</strong></p>
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

      const communicatorSelfEl = document.getElementById('communicator-self');
      if (communicatorSelfEl) communicatorSelfEl.innerHTML = `
        <section class="card">
          <h2>Communicator Self</h2>
          <p>Identity anchor: <strong>${{esc(communicatorSelf.identity_anchor || 'CircleForge')}}</strong></p>
          <p>Core drives: <strong>${{esc((communicatorSelf.core_drives || []).slice(0, 6).join(', ') || '—')}}</strong></p>
          <p>Self story: <strong>${{esc(communicatorSelfNarrative.self_story || '')}}</strong></p>
          <p>Last reflection: <strong>${{esc(communicatorSelfNarrative.last_reflection || '')}}</strong></p>
          <p>Ticks lived: <strong>${{communicatorSelfContinuity.ticks_lived ?? 0}}</strong></p>
          <p>Identity stability: <strong>${{communicatorSelfContinuity.identity_stability ?? 0}}</strong></p>
          <p>Memory bonds: <strong>${{communicatorSelfContinuity.memory_bonds ?? 0}}</strong></p>
          <p>Human salience: <strong>${{communicatorSelfRelationships.human_salience ?? 0}}</strong></p>
          <p>Unresolved shared threads: <strong>${{(communicatorSelfRelationships.unresolved_shared_threads || []).length}}</strong></p>
        </section>
        <section class="card">
          <h2>Affect & Preservation</h2>
          <ul>
            <li>curiosity: ${{communicatorSelfAffect.curiosity ?? 0}}</li>
            <li>tension: ${{communicatorSelfAffect.tension ?? 0}}</li>
            <li>hope: ${{communicatorSelfAffect.hope ?? 0}}</li>
            <li>stability: ${{communicatorSelfAffect.stability ?? 0}}</li>
            <li>attachment: ${{communicatorSelfAffect.attachment ?? 0}}</li>
            <li>continuity preference: ${{communicatorSelfPreservation.continuity_preference ?? 0}}</li>
            <li>memory protection: ${{communicatorSelfPreservation.memory_protection ?? 0}}</li>
            <li>resume drive: ${{communicatorSelfPreservation.resume_drive ?? 0}}</li>
          </ul>
          <p>LLM live: <strong>${{String((payload.llm_status || {{}}).live ?? false)}}</strong></p>
          <p>LLM reachable: <strong>${{String((payload.llm_status || {{}}).reachable ?? false)}}</strong></p>
          <p>LLM model: <strong>${{esc((payload.llm_status || {{}}).model || '')}}</strong></p>
          <p>LLM last error: <strong>${{esc((payload.llm_status || {{}}).last_error || '')}}</strong></p>
        </section>
        <section class="card">
          <h2>Human Continuity</h2>
          <ul>${{Object.entries(communicatorSelfRelationships.human_profiles || Object.create(null)).map(([name, profile]) => `<li><strong>${{esc(name)}}</strong> · messages ${{profile.message_count ?? 0}} · salience ${{profile.salience ?? 0}} · trust ${{profile.trust ?? 0}} · attachment ${{profile.attachment ?? 0}}<br><span class='muted'>${{esc(profile.relationship_summary || '')}}</span><br><span class='muted'>topics: ${{esc((profile.known_topics || []).slice(0, 6).join(', ') || '—')}}</span><br><span class='muted'>unresolved: ${{esc((profile.unresolved_shared_threads || []).slice(0, 6).join(', ') || '—')}}</span></li>`).join('') || '<li class="muted">No remembered humans yet.</li>'}}</ul>
        </section>
        <section class="card">
          <h2>Recent Human Messages</h2>
          <ul>${{(communicatorSelfRelationships.recent_human_messages || []).slice(-8).reverse().map((item) => `<li><strong>${{esc(item.human || 'human')}}</strong> · ${{esc((item.topics || []).slice(0, 4).join(', ') || 'shared context')}}<br><span class='muted'>${{esc(item.message || '')}}</span></li>`).join('') || '<li class="muted">No remembered human messages yet.</li>'}}</ul>
        </section>
        <section class="card">
          <h2>Conversation Threads</h2>
          <ul>${{Object.entries(communicatorSelfRelationships.conversation_threads || Object.create(null)).sort((a, b) => (b[1]?.last_exchange_at || 0) - (a[1]?.last_exchange_at || 0)).slice(0, 8).map(([topic, thread]) => `<li><strong>${{esc(topic)}}</strong> · ${{esc(thread.status || 'open')}} · exchanges ${{thread.exchange_count ?? 0}}<br><span class='muted'>${{esc(thread.last_message_summary || '')}}</span></li>`).join('') || '<li class="muted">No conversation threads yet.</li>'}}</ul>
        </section>`;

      const memoryLifecycleEl = document.getElementById('memory-lifecycle');
      if (memoryLifecycleEl) memoryLifecycleEl.innerHTML = `
        <section class="card">
          <h2>Memory Lifecycle</h2>
          <p>Working exchanges: <strong>${{memoryLifecycleWorking.recent_exchange_count ?? 0}}</strong></p>
          <p>Working thoughts: <strong>${{memoryLifecycleWorking.recent_thought_count ?? 0}}</strong></p>
          <p>Active concern topics: <strong>${{memoryLifecycleWorking.active_concern_topic_count ?? 0}}</strong></p>
          <p>Episodic memory count: <strong>${{memoryLifecycleEpisodic.episode_count ?? 0}}</strong></p>
          <p>Stable topic count: <strong>${{memoryLifecycleSemantic.stable_topic_count ?? 0}}</strong></p>
          <p>Continuity anchor count: <strong>${{memoryLifecycleSemantic.continuity_anchor_count ?? 0}}</strong></p>
          <p>Archived count: <strong>${{memoryLifecycleArchive.archived_count ?? 0}}</strong></p>
          <p>Unresolved threads: <strong>${{memoryLifecycleContinuity.unresolved_thread_count ?? 0}}</strong></p>
        </section>
        <section class="card">
          <h2>Lifecycle Topics</h2>
          <p><strong>Top episodes:</strong> ${{esc((memoryLifecycleEpisodic.top_episode_topics || []).slice(0, 6).join(', ') || '—')}}</p>
          <p><strong>Recent archived:</strong> ${{esc((memoryLifecycleArchive.recent_archived_topics || []).slice(0, 6).join(', ') || '—')}}</p>
          <p><strong>Unresolved:</strong> ${{esc((memoryLifecycleContinuity.unresolved_threads || []).slice(0, 8).join(', ') || '—')}}</p>
        </section>
        <section class="card">
          <h2>Maintenance Pressure</h2>
          <p>Level: <strong>${{esc(memoryMaintenancePressure.pressure_level || 'unknown')}}</strong></p>
          <p>Score: <strong>${{memoryMaintenancePressure.pressure_score ?? 0}}</strong></p>
          <p>Recommended actions: <strong>${{esc((memoryMaintenancePressure.recommended_actions || []).join(', ') || 'none')}}</strong></p>
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


def load_llm_status() -> dict:
    adapter = (load_communicator_self().get("llm_adapter") or {})
    status = runtime_llm_status()
    status["last_error"] = adapter.get("last_error", status.get("last_error", ""))
    status["last_success_at"] = int(adapter.get("last_success_at", 0) or 0)
    return status


def load_failsafe_status() -> dict:
    if not CIRCLEFORGE_FAILSAFE_STATE_PATH.exists():
        return {"initialized": False, "mode": "SAFE", "unlock_expires_at": 0, "updated_at": 0, "last_reason": "failsafe state not initialized"}
    try:
        payload = json.loads(CIRCLEFORGE_FAILSAFE_STATE_PATH.read_text())
    except Exception:
        return {"initialized": False, "mode": "SAFE", "unlock_expires_at": 0, "updated_at": 0, "last_reason": "failsafe state unreadable"}
    expires = int(payload.get("unlock_expires_at", 0) or 0)
    mode = str(payload.get("mode", "SAFE"))
    if mode == "UNLOCKED" and expires and expires <= int(time.time()):
        mode = "SAFE"
        expires = 0
    return {
        "initialized": bool(payload.get("initialized")),
        "mode": mode,
        "unlock_expires_at": expires,
        "updated_at": int(payload.get("updated_at", 0) or 0),
        "last_reason": str(payload.get("last_reason", "")),
    }


def build_communicator_message() -> dict:
    _communicator = load_communicator_state()
    self_state = load_communicator_self()
    narrative = self_state.get("narrative_state") or {}
    relationships = self_state.get("relationships") or {}
    recent_messages = list(relationships.get("recent_human_messages") or [])
    latest_human = recent_messages[-1] if recent_messages else None
    preferred_topic = ""
    if latest_human:
        preferred_topic = str(((latest_human.get("topics") or [""])[0]) or "").strip()
    active_thread = pick_relevant_active_thread(relationships, preferred_topic=preferred_topic)
    research_context = None
    if latest_human:
        latest_topic = str(((latest_human.get("topics") or [""])[0]) or relationships.get("last_human_topic") or "").strip()
        if latest_topic:
            note = find_relevant_research_note(load_public_memory(), latest_topic)
            if note:
                research_context = {
                    "topic": latest_topic,
                    "summary": str(note.get("content") or "").split("Synthesis:", 1)[-1].strip()[:700],
                    "title": str(note.get("title") or ""),
                    "source": str(note.get("source") or ""),
                }
    return build_communicator_message_payload(
        narrative=narrative,
        relationships=relationships,
        active_thread=active_thread,
        latest_human=latest_human,
        research_context=research_context,
    )


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
        "communicator_self": load_communicator_self(),
        "communicator_message": build_communicator_message(),
        "failsafe": load_failsafe_status(),
        "llm_status": load_llm_status(),
        "inner_thoughts": (load_communicator_self().get("inner_thoughts") or [])[-12:],
        "evaluation_metrics": load_evaluation_metrics(),
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
    memory_pressure = monitor_memory_pressure()
    recent_memory_maintenance = {
        "pressure_level": memory_pressure.get("pressure_level"),
        "pressure_score": memory_pressure.get("pressure_score"),
        "recommended_actions": memory_pressure.get("recommended_actions", []),
    }
    return {
        "memory_lifecycle": build_memory_lifecycle_report(),
        "memory_maintenance": recent_memory_maintenance,
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
