from __future__ import annotations


def ensure_semantic_defaults(semantic: dict, *, identity_anchor: str, now_ts: int) -> dict:
    semantic.setdefault("summary", "Long-term identity and relationship memory.")
    semantic.setdefault("identity_anchors", [identity_anchor or "CircleForge"])
    semantic.setdefault("relationship_facts", [])
    semantic.setdefault("stable_topics", [])
    semantic.setdefault("durable_lessons", [])
    semantic.setdefault("continuity_anchors", [])
    semantic.setdefault("last_updated_at", 0)
    return semantic


def sync_semantic_with_active_threads(semantic: dict, active_threads: list[str], now_ts: int) -> dict:
    continuity_anchors = list(semantic.setdefault("continuity_anchors", []))
    stable_topics = list(semantic.get("stable_topics") or [])
    changed = False
    for topic in active_threads[:12]:
        if topic not in continuity_anchors:
            continuity_anchors.append(topic)
            changed = True
    merged_topics = list(dict.fromkeys(stable_topics + active_threads))[-24:]
    if continuity_anchors[-24:] != (semantic.get("continuity_anchors") or []):
        changed = True
    if merged_topics != (semantic.get("stable_topics") or []):
        changed = True
    semantic["continuity_anchors"] = continuity_anchors[-24:]
    semantic["stable_topics"] = merged_topics
    if changed:
        semantic["last_updated_at"] = now_ts
    return semantic


def apply_topics_to_semantic_memory(semantic: dict, topics: list[str], relationship_fact: str = "", now_ts: int | None = None) -> dict:
    semantic["stable_topics"] = list(dict.fromkeys((semantic.get("stable_topics") or []) + [topic for topic in topics if str(topic).strip()]))[-24:]
    if relationship_fact:
        relationship_facts = list(dict.fromkeys((semantic.get("relationship_facts") or []) + [relationship_fact]))
        semantic["relationship_facts"] = relationship_facts[-24:]
    if now_ts is not None:
        semantic["last_updated_at"] = now_ts
    return semantic
