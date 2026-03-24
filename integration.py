from __future__ import annotations


def find_relevant_research_note(public_memory: list[dict], topic: str) -> dict | None:
    topic = str(topic or "").strip().lower()
    if not topic:
        return None
    topic_terms = [term for term in topic.replace('-', ' ').split() if len(term) > 2]
    best = None
    best_score = 0
    for item in reversed(list(public_memory or [])):
        if str(item.get("kind") or "") != "research":
            continue
        haystack = f"{item.get('title', '')} {item.get('content', '')} {item.get('source', '')}".lower()
        score = 0
        if topic in haystack:
            score += 5
        for term in topic_terms[:6]:
            if term in haystack:
                score += 1
        if score > best_score:
            best = item
            best_score = score
    return best if best_score > 0 else None


def extract_working_summary(research_note: dict) -> str:
    content = str((research_note or {}).get("content") or "").strip()
    if not content:
        return ""
    marker = "Working summary for"
    if marker in content:
        tail = content.split(marker, 1)[1]
        tail = tail.split("Evidence:", 1)[0].strip()
        return tail[:700]
    return content[:700]


def integrate_research_into_communicator(communicator: dict, public_memory: list[dict], topic: str) -> dict | None:
    note = find_relevant_research_note(public_memory, topic)
    if not note:
        return None
    summary = extract_working_summary(note)
    if not summary:
        return None
    communicator["last_research_topic"] = topic
    communicator["last_research_summary"] = summary[:700]
    communicator["last_research_source"] = str(note.get("source") or "")
    communicator["last_decision_summary"] = f"integrated research on {topic}: {summary[:180]}"
    return {
        "topic": topic,
        "summary": summary[:700],
        "source": str(note.get("source") or ""),
        "title": str(note.get("title") or ""),
    }
