from __future__ import annotations


def canonical_human_slot(label: str) -> str:
    label = (label or "").strip()
    if not label:
        return "interlocutor_001"
    lowered = label.lower()
    if lowered in {"human", "unknown", "speaker", "current-speaker", "current_speaker", "operator", "user", "visitor", "someone"}:
        return "interlocutor_001"
    return label


def display_human_label(slot: str, profile: dict | None = None) -> str:
    profile = profile or {}
    discovered_name = str(profile.get("discovered_name") or "").strip()
    if discovered_name:
        return discovered_name
    if str(slot).startswith("interlocutor_"):
        return "you"
    return str(slot or "you")


def pick_relevant_active_thread(relationships: dict, preferred_topic: str = "") -> tuple[str, dict] | None:
    threads = relationships.get("conversation_threads") or {}
    open_threads = [item for item in sorted(threads.items(), key=lambda kv: kv[1].get("last_exchange_at", 0), reverse=True) if str(item[1].get("status", "open")) == "open"]
    if not open_threads:
        return None
    preferred_topic = str(preferred_topic or "").strip().lower()
    if preferred_topic:
        exact = next((item for item in open_threads if str(item[0]).strip().lower() == preferred_topic), None)
        if exact:
            return exact
    last_human_exchange_at = max((int(item[1].get("last_human_exchange_at", 0) or 0) for item in open_threads), default=0)
    fresh = [item for item in open_threads if int(item[1].get("last_human_exchange_at", 0) or 0) >= last_human_exchange_at]
    return fresh[0] if fresh else open_threads[0]
