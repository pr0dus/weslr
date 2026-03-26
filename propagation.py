from __future__ import annotations

import time
from pathlib import Path


def load_semantic_memory() -> dict:
    """Load semantic memory from public_memory.json, extracting or creating the semantic dict."""
    from sim import PUBLIC_MEMORY_PATH, read_json_file

    public = read_json_file(PUBLIC_MEMORY_PATH, [])
    # Find or create the semantic memory entry in public memory
    semantic = None
    for item in public:
        if isinstance(item, dict) and item.get("kind") == "semantic-memory":
            semantic = item
            break
    if semantic is None:
        semantic = {
            "kind": "semantic-memory",
            "id": "semantic-memory",
            "summary": "Long-term identity and relationship memory.",
            "identity_anchors": ["CircleForge"],
            "relationship_facts": [],
            "stable_topics": [],
            "durable_lessons": [],
            "continuity_anchors": [],
            "last_updated_at": 0,
        }
        public.append(semantic)
    return semantic


def save_semantic_memory(semantic: dict) -> None:
    """Save semantic memory back to public_memory.json."""
    from sim import PUBLIC_MEMORY_PATH, read_json_file, write_json_file

    public = list(read_json_file(PUBLIC_MEMORY_PATH, []))
    # Replace or append the semantic entry
    found = False
    for i, item in enumerate(public):
        if isinstance(item, dict) and item.get("kind") == "semantic-memory":
            public[i] = semantic
            found = True
            break
    if not found:
        public.append(semantic)
    write_json_file(PUBLIC_MEMORY_PATH, public)


def propagate_self_model_to_memory(now_ts: int) -> dict:
    """
    Minimal propagation: sync self-model traits into semantic memory.
    Loads state, updates, and saves back.
    """
    from sim import load_communicator_self
    from self_model import ensure_identity_scaffold
    from semantic_memory import ensure_semantic_defaults

    self_state = load_communicator_self()
    semantic = load_semantic_memory()

    ensure_identity_scaffold(self_state)
    identity_state = self_state.get("identity_state") or {}

    traits = identity_state.get("identity_traits", []) or []
    stable_topics = list(semantic.get("stable_topics") or [])

    # Add recent traits as stable topics for continuity
    for trait in traits[-3:]:
        if trait and trait not in stable_topics:
            stable_topics.append(trait)

    semantic["stable_topics"] = stable_topics[-24:]
    semantic["last_updated_at"] = now_ts

    save_semantic_memory(semantic)

    return {
        "traits_propagated": len(traits),
        "stable_topics_count": len(stable_topics),
        "timestamp": now_ts,
    }


def propagate_continuity_to_self_model(now_ts: int) -> dict:
    """
    Propagate continuity thread state back into self-model.
    """
    from sim import load_communicator_self, save_communicator_self

    self_state = load_communicator_self()
    continuity = self_state.get("continuity") or {}
    relationships = self_state.get("relationships") or {}

    threads = relationships.get("conversation_threads", {}) or {}
    unresolved = [t for t in threads.values() if t.get("status") == "open"]

    self_state.setdefault("continuity", {})
    self_state["continuity"]["unresolved_threads"] = len(unresolved)
    self_state["continuity"]["last_thread_update"] = now_ts

    save_communicator_self(self_state)

    return {
        "unresolved_threads": len(unresolved),
        "self_model_continuity_updated": True,
    }


def synchronized_propagation(now_ts: int | None = None) -> dict:
    """
    Run both propagation directions in order: self-model -> semantic memory,
    then continuity -> self-model. Returns combined result for logging.
    """
    now_ts = int(now_ts or time.time())
    result1 = propagate_self_model_to_memory(now_ts)
    result2 = propagate_continuity_to_self_model(now_ts)
    return {
        "self_model_to_semantic": result1,
        "continuity_to_self_model": result2,
        "complete": True,
        "timestamp": now_ts,
    }
