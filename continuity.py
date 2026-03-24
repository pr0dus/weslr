from __future__ import annotations


def should_passively_reinforce_thread(thread: dict, now_ts: int, *, cooldown_seconds: int, max_passive_reinforcements: int) -> bool:
    last_human_exchange_at = int(thread.get("last_human_exchange_at", 0) or 0)
    last_passive_reinforced_at = int(thread.get("last_passive_reinforced_at", 0) or 0)
    passive_reinforcement_count = int(thread.get("passive_reinforcement_count", 0) or 0)

    if passive_reinforcement_count >= max_passive_reinforcements:
        return False
    if last_passive_reinforced_at > 0 and now_ts - last_passive_reinforced_at < cooldown_seconds:
        return False
    if last_human_exchange_at <= 0:
        return True
    if passive_reinforcement_count <= 0:
        return True
    return now_ts - last_human_exchange_at >= cooldown_seconds


def apply_human_exchange_to_threads(relationships: dict, exchange: dict, human_name: str, display_name: str, topics: list[str], unresolved: bool, now_ts: int) -> dict:
    relationships.setdefault("conversation_threads", {})
    relationships.setdefault("unresolved_shared_threads", [])
    threads = relationships.setdefault("conversation_threads", {})
    for topic in topics[:6]:
        thread = threads.setdefault(topic, {
            "topic": topic,
            "human": human_name,
            "human_label": display_name,
            "exchange_count": 0,
            "last_message_summary": "",
            "last_response_summary": "",
            "last_exchange_at": 0,
            "status": "open",
            "recent_exchange_ids": [],
        })
        thread["human"] = human_name
        thread["human_label"] = display_name
        thread["exchange_count"] = int(thread.get("exchange_count", 0)) + 1
        thread["last_message_summary"] = exchange["message_summary"]
        thread["last_response_summary"] = exchange["response_summary"]
        thread["last_exchange_at"] = now_ts
        thread["last_human_exchange_at"] = now_ts
        thread["last_passive_reinforced_at"] = int(thread.get("last_passive_reinforced_at", 0) or 0)
        thread["passive_reinforcement_count"] = 0
        thread["status"] = "open" if unresolved else "resolved"
        recent_ids = list(thread.get("recent_exchange_ids") or [])
        recent_ids.append(exchange["id"])
        thread["recent_exchange_ids"] = recent_ids[-6:]
        if unresolved and topic not in relationships["unresolved_shared_threads"]:
            relationships["unresolved_shared_threads"].append(topic)
    relationships["unresolved_shared_threads"] = relationships.get("unresolved_shared_threads", [])[-12:]
    return relationships
