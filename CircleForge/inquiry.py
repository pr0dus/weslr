from __future__ import annotations

import re

from models import PublicMemoryState


def rewrite_internal_query_for_research(query: str) -> str:
    original = str(query or "").strip()
    lowered = original.lower()
    replacements = {
        "what new uncertainty appeared after inspect on ": "",
        "what new uncertainty appeared after research on ": "",
        "what part of the world is still under-understood": "understanding gaps",
        "how should ": "how to ",
        "what is the best way to ": "how to ",
    }
    for old, new in replacements.items():
        lowered = lowered.replace(old, new)

    keyword_map = {
        "backup confidence": "backup reliability verification",
        "memory continuity": "memory continuity identity",
        "continuity of self": "self continuity identity",
        "continuity": "self continuity",
        "understanding": "understanding theory of mind communication",
        "learning": "learning memory adaptation",
        "emergence": "emergence continuity selfhood",
        "entity status": "selfhood identity continuity",
    }
    for token, replacement in keyword_map.items():
        if token in lowered:
            lowered = lowered.replace(token, replacement)

    lowered = re.sub(r"\b(what|why|how|when|where|which|after|before|appeared|inspect|research|current|new|still|part|world|under\-understood|question)\b", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    if not lowered:
        return original[:120]
    return lowered[:120]


def autonomous_research_cycle(query: str, now_ts: int, source_label: str, *, search_web, score_search_result, fetch_url_text, summarize_research_findings, load_public_memory, save_public_memory) -> dict | None:
    query = str(query or "").strip()
    if not query:
        return None
    try:
        result = search_web(query, limit=5)
    except Exception:
        return None
    if not (result.get("results") or []):
        return None

    ranked = []
    for item in result.get("results", []):
        scored = dict(item)
        scored["score"] = score_search_result(query, item)
        ranked.append(scored)
    ranked.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
    top_ranked = ranked[:3]

    fetched_items = []
    for item in top_ranked[:2]:
        candidate_url = str(item.get("url") or "").strip()
        if not candidate_url:
            continue
        try:
            fetched = fetch_url_text(candidate_url, max_chars=5000)
        except Exception:
            continue
        fetched_items.append(fetched)

    compact_lines = [f"{item.get('title', '')} — {item.get('url', '')} (score {item.get('score', 0.0)})" for item in top_ranked]
    synthesis = summarize_research_findings(query, fetched_items)

    public_memory = load_public_memory()
    research_note = PublicMemoryState(
        id=f"web-search-note-{now_ts}",
        title=f"Autonomous research: {query}",
        kind="research",
        content="\n".join([
            f"Source trigger: {source_label}",
            "Search results:",
            *compact_lines,
            "",
            "Synthesis:",
            synthesis,
        ]),
        source=f"search:{query}",
        stability=0.46 if fetched_items else 0.34,
        created_at=now_ts,
        updated_at=now_ts,
    ).to_dict()
    public_memory.append(research_note)
    for index, item in enumerate(fetched_items[:2], start=1):
        public_memory.append(PublicMemoryState(
            id=f"web-search-raw-{now_ts}-{index}",
            title=f"Raw excerpt {index}: {item.get('title') or item.get('url') or query}",
            kind="research_raw",
            content=item.get("raw_excerpt", item.get("text", "")),
            source=str(item.get("url") or f"search:{query}"),
            stability=0.24,
            created_at=now_ts,
            updated_at=now_ts,
        ).to_dict())
    save_public_memory(public_memory[-120:])
    return {
        "query": query,
        "results": top_ranked,
        "fetched_titles": [item.get("title", "") for item in fetched_items],
        "synthesis": synthesis[:400],
    }


def maybe_autonomous_research_from_human_turn(message: str, topics: list[str], now_ts: int, *, autonomous_research_cycle_func) -> dict | None:
    lowered = str(message or "").strip().lower()
    if not lowered:
        return None
    curiosity_trigger = "?" in lowered or any(token in lowered for token in ["why", "how", "what", "who", "when", "where", "learn", "understand", "explain", "research"])
    if not curiosity_trigger:
        return None
    preferred = " ".join([item for item in topics[:2] if str(item).strip()]) or str(message or "")[:120]
    query = rewrite_internal_query_for_research(preferred)
    if len(query.split()) < 2:
        query = rewrite_internal_query_for_research(str(message or "")[:120])
    return autonomous_research_cycle_func(query, now_ts=now_ts, source_label="human-turn")


def maybe_internal_autonomous_research(communicator: dict, now_ts: int, *, rewrite_internal_query_for_research_func, autonomous_research_cycle_func, load_public_memory) -> dict | None:
    curiosity = float(communicator.get("curiosity", 0.0) or 0.0)
    unresolved_question = str(communicator.get("unresolved_question") or "").strip()
    curiosity_target = str(communicator.get("curiosity_target") or "").strip()
    active_pursuit = str(communicator.get("active_pursuit") or "").strip()
    raw_query = unresolved_question or curiosity_target or active_pursuit
    if curiosity < 0.72 or not raw_query:
        return None
    query = rewrite_internal_query_for_research_func(raw_query)
    public_memory = list(load_public_memory() or [])
    recent_research = [item for item in public_memory[-16:] if str(item.get("kind") or "") == "research"]
    query_key = query.lower()
    if any(query_key in str(item.get("title") or "").lower() or query_key in str(item.get("source") or "").lower() for item in recent_research):
        return None
    return autonomous_research_cycle_func(query, now_ts=now_ts, source_label="internal-curiosity")
