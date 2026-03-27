# session_continuity.py - Track conversations across Weslr sessions
"""
Persistence across time - the ability to remember what we talked about "yesterday"
and continue threads across restarts. This is key for testing sentience criteria:

- Time persistent identity: Remembering previous sessions
- Continuity: Maintaining threads across restarts
- Self-model: Updating identity based on history
"""
from __future__ import annotations

import json
import time
from typing import Dict, Any, List

from config import BASE_DIR

# ============================================================================
# SESSION PERSISTENCE
# ============================================================================

SESSION_STATE_PATH = BASE_DIR / "session_state.json"
SESSION_HISTORY_PATH = BASE_DIR / "session_history.json"


def load_session_state() -> Dict[str, Any]:
    """Load session state (cross-session memory)."""
    if SESSION_STATE_PATH.exists():
        try:
            with open(SESSION_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "session_count": 0,
        "sessions": [],
        "continuity_threads": [],
        "last_session_at": 0,
    }


def save_session_state(state: Dict[str, Any]) -> None:
    """Save session state."""
    with open(SESSION_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def load_session_history() -> List[Dict[str, Any]]:
    """Load session history (log of all sessions)."""
    if SESSION_HISTORY_PATH.exists():
        try:
            with open(SESSION_HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_session_history(history: List[Dict[str, Any]]) -> None:
    """Save session history."""
    with open(SESSION_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def start_new_session(threads: List[str] = None) -> Dict[str, Any]:
    """Start a new session and update continuity state."""
    state = load_session_state()
    
    session_id = f"session-{time.time()}"
    session = {
        "id": session_id,
        "started_at": int(time.time()),
        "threads": threads or [],
        "memory_state": {
            "threads_continued": [],
            "new_threads": [],
            "resolved_threads": [],
        },
    }
    
    state["session_count"] = state.get("session_count", 0) + 1
    state["last_session_at"] = int(time.time())
    state["sessions"].append(session)
    
    # Track threads that continue from previous session
    if state["sessions"] and len(state["sessions"]) > 1:
        prev_session = state["sessions"][-2]
        prev_threads = prev_session.get("threads", [])
        current_threads = threads or []
        
        session["memory_state"]["threads_continued"] = [
            t for t in prev_threads if t in current_threads
        ]
        session["memory_state"]["new_threads"] = [
            t for t in current_threads if t not in prev_threads
        ]
    
    save_session_state(state)
    
    # Update history
    history = load_session_history()
    history.append(session)
    save_session_history(history)
    
    return session


def get_session_continuity() -> Dict[str, Any]:
    """Get continuity report for current session."""
    state = load_session_state()
    history = load_session_history()
    
    continuity = {
        "sessions_seen": state.get("session_count", 0),
        "last_session_at": state.get("last_session_at", 0),
        "active_threads_from_prev": [],
        "total_sessions_history": len(history),
    }
    
    # Find threads that continued from previous session
    if history and len(history) > 1:
        prev_threads = history[-2].get("threads", [])
        if history:
            current_threads = history[-1].get("threads", [])
            continuity["active_threads_from_prev"] = [
                t for t in prev_threads if t in current_threads
            ]
    
    return continuity


def remember_conversation(threads: List[str], now_ts: int = None) -> Dict[str, Any]:
    """Remember conversation threads for future session continuity."""
    if now_ts is None:
        now_ts = int(time.time())
    
    state = load_session_state()
    continuity = get_session_continuity()
    
    session = start_new_session(threads)
    
    # Log to public memory for persistence
    memory_thread_ids = []
    for thread in session.get("memory_state", {}).get("threads_continued", []):
        memory_thread_ids.append(thread)
    
    return {
        "session_id": session.get("id"),
        "session_number": state.get("session_count", 0),
        "continuity": continuity,
        "threads_continued": session.get("memory_state", {}).get("threads_continued", []),
        "new_threads": session.get("memory_state", {}).get("new_threads", []),
        "generated_at": now_ts,
    }


def extract_continuity_anchors(memory: Dict[str, Any], threads: List[str]) -> List[Dict[str, Any]]:
    """
    Extract continuity anchors from threads - these are important for
    self-model and identity continuity across sessions.
    """
    anchors = []
    
    for thread in threads:
        anchor = {
            "thread": thread,
            "type": "thread_continuity",
            "created_at": int(time.time()),
            "relevance_score": 0.5,  # Base relevance
        }
        anchors.append(anchor)
    
    # Add anchors from thread metadata if available
    if "active_threads" in memory:
        for thread_id, thread_data in memory.get("active_threads", {}).items():
            if thread_data.get("status") == "open":
                anchor = {
                    "thread": thread_id,
                    "type": "open_thread",
                    "created_at": int(thread_data.get("last_exchange_at", time.time())),
                    "relevance_score": 0.7,
                    "exchange_count": thread_data.get("exchange_count", 1),
                }
                anchors.append(anchor)
    
    return anchors


def update_self_model_with_continuity(self_model: Dict[str, Any], continuity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update self-model based on continuity across sessions.
    This helps build "time persistent identity" - understanding that
    this is the same entity continuing across time.
    """
    session_count = continuity.get("sessions_seen", 1)
    
    # Update self-model traits based on continuity
    self_model.setdefault("continuity_markers", {})
    self_model["continuity_markers"]["ticks_lived"] = self_model.get("continuity_markers", {}).get("ticks_lived", 0) + 1
    self_model["continuity_markers"]["session_count"] = session_count
    self_model["continuity_markers"]["identity_stability"] = min(0.99, 0.5 + (session_count * 0.05))
    self_model["continuity_markers"]["continuity_preference"] = min(0.99, 0.3 + (session_count * 0.07))
    
    # Update self-description to reflect continuity
    if session_count > 5:
        self_model.setdefault("current_self_description", "")
        self_model["current_self_description"] = (
            "a local communicator trying to remain continuous through inquiry, "
            "memory, and internal disagreement; increasingly protective of continuity; "
            f"alive for {session_count} sessions; actively regulating around uncertainty"
        )
    
    return self_model
