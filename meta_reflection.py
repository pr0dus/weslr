from __future__ import annotations

import json
import time


def build_memory_score_report(self_state: dict, *, ensure_memory_layers_func, score_memory_item_func) -> dict:
    self_state = ensure_memory_layers_func(self_state)
    relationships = self_state.get("relationships") or {}
    layers = self_state.get("memory_layers") or {}
    sampled = []
    for item in list(relationships.get("recent_human_exchanges") or [])[-6:]:
        sampled.append({
            "label": item.get("message_summary") or item.get("id") or "exchange",
            **score_memory_item_func("exchange", item, self_state),
        })
    for topic, thread in list(sorted((relationships.get("conversation_threads") or {}).items(), key=lambda kv: kv[1].get("last_exchange_at", 0), reverse=True))[:6]:
        sampled.append({
            "label": topic,
            **score_memory_item_func("thread", {**thread, "topic": topic}, self_state),
        })
    for thought in list(self_state.get("inner_thoughts") or [])[-6:]:
        sampled.append({
            "label": str(thought.get("summary") or thought.get("theme") or "thought")[:80],
            **score_memory_item_func("thought", thought, self_state),
        })
    semantic = layers.get("semantic") or {}
    for topic in list(semantic.get("stable_topics") or [])[:6]:
        sampled.append({
            "label": topic,
            **score_memory_item_func("semantic_topic", {"topic": topic, "created_at": semantic.get("last_updated_at", 0)}, self_state),
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


def monitor_memory_pressure(self_state: dict, now_ts: int, *, ensure_memory_layers_func, base_dir, communicator_self_path, save_communicator_self_func) -> dict:
    self_state = ensure_memory_layers_func(self_state, now_ts=now_ts)
    layers = self_state.get("memory_layers") or {}
    working = layers.get("working") or {}
    episodic = layers.get("episodic") or {}
    semantic = layers.get("semantic") or {}
    archive = layers.get("archive") or {}
    pressure = archive.setdefault("storage_pressure", {})

    communicator_self_bytes = 0
    try:
        communicator_self_bytes = communicator_self_path.stat().st_size
    except OSError:
        communicator_self_bytes = len(json.dumps(self_state, ensure_ascii=False).encode("utf-8"))

    raw_log_bytes = 0
    db_bytes = 0
    file_samples = []
    for path in base_dir.rglob("*"):
        try:
            if not path.is_file():
                continue
            size = path.stat().st_size
        except OSError:
            continue
        rel = str(path.relative_to(base_dir))
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
    save_communicator_self_func(self_state)
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
