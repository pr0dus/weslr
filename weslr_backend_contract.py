"""Weslr App Shell Backend Contract (v1)

Minimal endpoints for App Shell v1 to connect to real Weslr data.

Features:
  - conversation list (mocked from entity graph)
  - continuity status (from weslr/continuity/*.json)
  - file route request (via weslr/file_router.py)
  - operator summary (from self_improvement_proposal)
  - operator panel role gate (visibility contract)

No auth, no production API yet — additive and reversible only.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import entity_graph as eg
import weslr.file_router as file_router
import self_improvement_proposal as sip

BASE_DIR = Path(__file__).resolve().parent


# ─────────────────────────────────────────────────────────────────────────────
# 1. CONVERSATION LIST
# ─────────────────────────────────────────────────────────────────────────────

def get_conversation_list(limit: int = 20) -> List[Dict[str, Any]]:
    """Get conversation list from entity graph interactions.
    
    Returns mock conversation history based on entities with evidence.
    This is a placeholder — actual conversations would come from a database.
    
    Args:
        limit: Maximum number of conversations to return
        
    Returns:
        List of conversation summaries
    """
    graph = eg.get_entity_graph()
    entities = graph.get_all_entities()[:limit]
    
    conversations = []
    for entity in entities:
        # Create a mock conversation entry from entity evidence
        evidence_count = len(entity.evidence)
        last_activity = entity.updated_at if hasattr(entity, 'updated_at') else datetime.now()
        
        conversations.append({
            "id": f"conv_{entity.id}",
            "title": f"Discussion: {entity.name}",
            "entity_id": entity.id,
            "entity_type": entity.type,
            "participant_count": 1,  # Mock
            "last_message_at": last_activity.isoformat() if hasattr(last_activity, 'isoformat') else datetime.now().isoformat(),
            "snippet": f"Context about {entity.name} — {evidence_count} pieces of evidence",
            "unread_count": 0,
        })
    
    return conversations


# ─────────────────────────────────────────────────────────────────────────────
# 2. CONTINUITY STATUS
# ─────────────────────────────────────────────────────────────────────────────

def get_continuity_status() -> Dict[str, Any]:
    """Get continuity status from weslr/continuity/*.json files.
    
    Returns:
        Status object with current snapshot info, last update time, etc.
    """
    continuity_dir = BASE_DIR / "continuity"
    
    status = {
        "active": False,
        "last_snapshot_id": None,
        "last_updated": None,
        "snapshots": [],
        "error": None,
    }
    
    try:
        # Check if continuity directory exists
        if not continuity_dir.exists():
            status["error"] = "Continuity directory not found"
            return status
        
        # Read latest snapshot
        latest_path = continuity_dir / "snapshots" / "latest.json"
        if latest_path.exists():
            with open(latest_path, 'r', encoding='utf-8') as f:
                latest = json.load(f)
                status["active"] = True
                status["last_snapshot_id"] = latest.get("id", "unknown")
                status["last_updated"] = latest.get("created_at", datetime.now().isoformat())
        
        # List all snapshots
        snapshots_dir = continuity_dir / "snapshots"
        if snapshots_dir.exists():
            for snap_path in sorted(snapshots_dir.glob("*.json")):
                if snap_path.name == "latest.json":
                    continue
                try:
                    with open(snap_path, 'r', encoding='utf-8') as f:
                        snap = json.load(f)
                        status["snapshots"].append({
                            "id": snap.get("id"),
                            "created_at": snap.get("created_at"),
                            "entity_count": len(snap.get("entities", [])),
                        })
                except Exception:
                    continue
        
        # Sort by created_at descending
        status["snapshots"] = sorted(
            status["snapshots"],
            key=lambda x: x.get("created_at", ""),
            reverse=True,
        )[:10]  # Keep last 10
        
    except Exception as e:
        status["error"] = str(e)
    
    return status


# ─────────────────────────────────────────────────────────────────────────────
# 3. FILE ROUTE REQUEST
# ─────────────────────────────────────────────────────────────────────────────

def route_file(
    filepath: str,
    user_query: str = "",
    task_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Route a file through the unified file router.
    
    This is the backend endpoint that App Shell v1 will call when a user
    drops a file or requests file analysis.
    
    Args:
        filepath: Path to file (must be within workspace)
        user_query: User's question/request
        task_context: Current task context
        
    Returns:
        RouterResult as dict
    """
    if task_context is None:
        task_context = {"type": "file_analysis", "focus": "content"}
    
    workspace_dir = str(BASE_DIR)
    router = file_router.create_file_router(workspace_dir=workspace_dir)
    
    try:
        result = router.route(filepath, user_query=user_query, task_context=task_context)
        return result.to_dict()
    except file_router.FileRouterError as e:
        return {
            "error": str(e),
            "category": "error",
            "content": "",
        }
    except Exception as e:
        return {
            "error": f"Unexpected routing error: {e}",
            "category": "error",
            "content": "",
        }


# ─────────────────────────────────────────────────────────────────────────────
# 4. OPERATOR SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def get_operator_summary() -> Dict[str, Any]:
    """Get operator summary from self_improvement_proposal.
    
    Returns:
        Summary object with active proposals, pending reviews, etc.
    """
    summary = {
        "active_proposals": [],
        "pending_reviews": 0,
        "last_review": None,
        "total_proposals": 0,
        "error": None,
    }
    
    try:
        proposals = sip.get_all_proposals()
        summary["total_proposals"] = len(proposals)
        
        active = []
        pending = 0
        
        for prop in proposals:
            state = prop.get("state", "")
            if state in ("draft", "review", "active"):
                active.append({
                    "id": prop.get("id"),
                    "title": prop.get("title", "Untitled"),
                    "state": state,
                    "created_at": prop.get("created_at"),
                })
            if state == "review":
                pending += 1
        
        summary["active_proposals"] = active[:10]  # Top 10
        summary["pending_reviews"] = pending
        
        # Get last review
        reviews = sip.get_review_history(limit=1)
        if reviews:
            summary["last_review"] = reviews[0].get("created_at")
        
    except Exception as e:
        summary["error"] = str(e)
    
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# 5. OPERATOR PANEL ROLE GATE / VISIBILITY CONTRACT
# ─────────────────────────────────────────────────────────────────────────────

def check_operator_visibility() -> Dict[str, Any]:
    """Check if operator panel should be visible to current user.
    
    This is the visibility contract for App Shell v1.
    Returns a simple gate response — no auth stack yet.
    
    Returns:
        {
            "visible": bool,
            "reason": str,
            "can_review": bool,
        }
    """
    result = {
        "visible": True,  # Show panel by default for development
        "reason": "Development mode — panel always visible",
        "can_review": True,
    }
    
    # In production, this would check:
    # - User identity (after auth)
    # - Role permissions (operator, admin, viewer)
    # - Active proposal state
    
    return result


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: EXPORT FOR CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """CLI commands for backend contract testing."""
    if len(sys.argv) < 2:
        print("Usage: python weslr_backend_contract.py <command> [args]")
        print("Commands:")
        print("  conversation-list [limit]")
        print("  continuity-status")
        print("  route-file <filepath> [query]")
        print("  operator-summary")
        print("  operator-visibility")
        return
    
    command = sys.argv[1]
    
    if command == "conversation-list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        convos = get_conversation_list(limit)
        print(json.dumps(convos, indent=2))
    
    elif command == "continuity-status":
        status = get_continuity_status()
        print(json.dumps(status, indent=2))
    
    elif command == "route-file":
        if len(sys.argv) < 3:
            print("Usage: python weslr_backend_contract.py route-file <filepath> [query]")
            return
        filepath = sys.argv[2]
        query = sys.argv[3] if len(sys.argv) > 3 else ""
        result = route_file(filepath, query)
        print(json.dumps(result, indent=2))
    
    elif command == "operator-summary":
        summary = get_operator_summary()
        print(json.dumps(summary, indent=2))
    
    elif command == "operator-visibility":
        visibility = check_operator_visibility()
        print(json.dumps(visibility, indent=2))
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
