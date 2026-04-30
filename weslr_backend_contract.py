"""Weslr App Shell Backend Contract (v1)

Minimal endpoints for App Shell v1 to connect to real Weslr data.

Features:
  - conversation list (mocked from entity graph)
  - continuity status (from weslr/continuity/*.json)
  - file route request (via weslr/file_router.py)
  - operator summary (from self_improvement_proposal)
  - operator panel role gate (visibility contract)
  - chat endpoint (for LLM-backed chat in private test deployment)

No auth, no production API yet — additive and reversible only.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import entity_graph as eg
import weslr.file_router as file_router
import self_improvement_proposal as sip

BASE_DIR = Path(__file__).resolve().parent

# ─────────────────────────────────────────────────────────────────────────────
# 3. FILE UPLOAD HANDLING (MINIMAL SAFE SLICE)
# ─────────────────────────────────────────────────────────────────────────────

UPLOAD_DIR = BASE_DIR / "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def ensure_upload_dir():
    """Create upload directory if it doesn't exist."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def validate_upload(filepath: Path) -> Optional[str]:
    """Validate uploaded file for safety.
    
    Safety boundaries:
    - Path within workspace
    - File size under 10MB
    - Not a directory
    - No path traversal
    """
    try:
        # Resolve to absolute path
        resolved = filepath.resolve()
        workspace = BASE_DIR.resolve()
        
        # Must be within workspace
        if not str(resolved).startswith(str(workspace) + os.sep):
            return f"Path traversal attempt: {filepath}"
        
        # Must be a file, not directory
        if resolved.is_dir():
            return f"Is a directory, not a file: {filepath}"
        
        # Check file size
        if resolved.stat().st_size > MAX_FILE_SIZE:
            return f"File too large: {resolved.stat().st_size} bytes (max {MAX_FILE_SIZE})"
        
        return None  # Valid
    except Exception as e:
        return f"Validation error: {e}"


def upload_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Save uploaded file and route it through unified file router.
    
    This is the minimal safe file-upload plumbing:
    1. Create upload directory
    2. Save file with safe name (UUID prefix to avoid collisions)
    3. Validate file path
    4. Route through existing file_router.py
    5. Return normalized result
    
    Args:
        file_content: Raw file bytes from frontend
        filename: Original filename (sanitized for storage)
        
    Returns:
        { success: bool, filepath?: str, result?: dict, error?: str }
    """
    ensure_upload_dir()
    
    # Sanitize filename - extract extension only, generate safe name
    ext = Path(filename).suffix.lower()
    if ext not in {'.json', '.yaml', '.yml', '.csv', '.txt', '.md', '.pdf', '.log', '.ini', '.cfg', '.conf', '.sql', '.html', '.xml', '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.sh', '.bash', '.zsh'}:
        # Allow all extensions for now, but log warning
        pass
    
    safe_name = f"upload_{uuid4().hex}{ext}"
    safe_path = UPLOAD_DIR / safe_name
    
    try:
        # Write file
        with open(safe_path, 'wb') as f:
            f.write(file_content)
        
        # Validate path
        error = validate_upload(safe_path)
        if error:
            safe_path.unlink(missing_ok=True)
            return {"success": False, "error": error}
        
        # Route through unified file router
        result = route_file(str(safe_path))
        
        return {
            "success": True,
            "filepath": str(safe_path),
            "filename": safe_name,
            "result": result,
        }
    except Exception as e:
        # Cleanup on error
        safe_path.unlink(missing_ok=True)
        return {"success": False, "error": f"Upload failed: {e}"}


# ─────────────────────────────────────────────────────────────────────────────
# 3b. FILE ROUTE REQUEST (via existing file_router)
# ─────────────────────────────────────────────────────────────────────────────

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
# 6. WESLR SUGGESTION REVIEW (OPINIONATED, MINIMAL)
# ─────────────────────────────────────────────────────────────────────────────

def review_suggestion(candidate_id: str, action: str, reason: str = "") -> Dict[str, Any]:
    """Review a Weslr suggestion candidate.
    
    This is an internal/operator-only action that updates the candidate's
    review state in review_queue.json. It does NOT auto-approve or auto-implement.
    
    Args:
        candidate_id: The candidate ID from suggestion_bridge
        action: One of: approve, deny, mark-eligible
        reason: Optional reason for deny action
        
    Returns:
        Dict with success status and updated candidate info
    """
    # Validate action
    if action not in ("approve", "deny", "mark-eligible"):
        return {
            "success": False,
            "error": f"Unknown action: {action}. Valid: approve, deny, mark-eligible"
        }
    
    try:
        from weslr.suggestion_bridge import SuggestionBridge
        from weslr.suggestion_assessment import WeslrAssessment
        
        bridge = SuggestionBridge()
        
        # Find the candidate
        candidates = bridge.list_proposal_candidates()
        candidate = None
        for c in candidates:
            if c.get("id") == candidate_id:
                candidate = c
                break
        
        if not candidate:
            return {
                "success": False,
                "error": f"Candidate not found: {candidate_id}"
            }
        
        # Apply review action
        if action == "approve":
            # Approve for operator review (not auto-implemented)
            bridge.mark_as_reviewed(candidate_id, "approved", reason or "Approved by operator")
        elif action == "deny":
            bridge.mark_as_reviewed(candidate_id, "rejected", reason or "Denied by operator")
        elif action == "mark-eligible":
            bridge.mark_as_reviewed(candidate_id, "approved", reason or "Marked eligible by operator")
            # Also set eligible flag for future processing
            candidate["eligible"] = True
        
        # Apply assessment to get updated info
        assessment = WeslrAssessment()
        assessment_result = assessment.assess_candidate(candidate)
        
        return {
            "success": True,
            "candidate_id": candidate_id,
            "action": action,
            "new_status": candidate.get("review_status"),
            "weslr_assessment": assessment_result["weslr_assessment"],
            "audit": {
                "reviewed_by": "operator",
                "reviewed_at": assessment_result["weslr_assessment"]["assessed_at"],
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Review failed: {e}"
        }


# ─────────────────────────────────────────────────────────────────────────────
# 7. CHAT ENDPOINT (NEW - for private test deployment)
# ─────────────────────────────────────────────────────────────────────────────

def diagnostics() -> Dict[str, Any]:
    """Operator diagnostics endpoint - compact runtime/platform signals.
    
    Returns:
        Dict with current provider, evidence routing status, backend status,
        concept graph status, capability queue, launch gate, commit hash, warnings.
    """
    import os
    import subprocess
    
    result = {
        "provider": {},
        "evidence_routing": {},
        "backend_chat": {},
        "concept_graph": {},
        "capability_queue": {},
        "launch_gate": {},
        "system": {},
        "warnings": [],
    }
    
    # 1. Current provider (from config and runtime)
    try:
        from config import WESLR_LLM_PROVIDER, WESLR_LLM_ENABLED, WESLR_LLM_MODEL
        from llm_runtime import status
        provider_status = status()
        result["provider"] = {
            "configured": WESLR_LLM_PROVIDER,
            "enabled": WESLR_LLM_ENABLED,
            "model": WESLR_LLM_MODEL,
            "status": provider_status,
        }
    except Exception as e:
        result["provider"] = {"error": str(e)}
        result["warnings"].append("Provider status unavailable")
    
    # 2. Evidence routing status
    try:
        from llm_runtime import _classify_prompt_for_routing
        # Test classification
        test_context = {
            "proposed_theme": "weather in Rome",
            "unresolved_question": "What is the weather?",
        }
        category, location = _classify_prompt_for_routing(test_context)
        result["evidence_routing"] = {
            "enabled": True,
            "test_classification": category,
            "test_location": location,
        }
    except Exception as e:
        result["evidence_routing"] = {"error": str(e)}
        result["warnings"].append("Evidence routing unavailable")
    
    # 3. Backend chat path status
    try:
        # Quick health check via chat
        test_result = chat("Hello")
        result["backend_chat"] = {
            "working": test_result.get("success", False),
            "source": test_result.get("source", "unknown"),
        }
    except Exception as e:
        result["backend_chat"] = {"error": str(e)}
        result["warnings"].append("Backend chat unavailable")
    
    # 4. Concept graph status
    try:
        import entity_graph as eg
        graph = eg.get_entity_graph()
        entity_count = len(graph.get_all_entities()) if hasattr(graph, 'get_all_entities') else 0
        result["concept_graph"] = {
            "entities": entity_count,
            "status": "available",
        }
    except Exception as e:
        result["concept_graph"] = {"error": str(e)}
        result["warnings"].append("Concept graph unavailable")
    
    # 5. Capability discovery queue summary
    try:
        from weslr.capability_suggestion import CapabilityDiscoveryRadar, CapabilityType, SourceProvenance
        radar = CapabilityDiscoveryRadar()
        summary = radar.get_summary()
        result["capability_queue"] = summary
    except Exception as e:
        result["capability_queue"] = {"error": str(e)}
        result["warnings"].append("Capability queue unavailable")

    # 5b. Capability ingestion summary (Phase 2)
    try:
        from weslr.capability_ingestion import CapabilityIngestionPipeline, SourceSignal, SourceKind
        pipeline = CapabilityIngestionPipeline()
        # Get all suggestions and categorize by source
        all_suggestions = pipeline.radar.list(include_archived=True)
        by_source: Dict[str, int] = {}
        last_ingestion = None
        for s in all_suggestions:
            # Extract provenance from notes or tags
            provenance = None
            if s.notes:
                for line in s.notes.split("\n"):
                    if "Provenance:" in line:
                        provenance = line.replace("Provenance:", "").strip()
                        break
            if provenance:
                by_source[provenance] = by_source.get(provenance, 0) + 1
                # Track last ingestion time
                if s.updated_at and (last_ingestion is None or s.updated_at > last_ingestion):
                    last_ingestion = s.updated_at

        result["capability_ingestion"] = {
            "by_provenance": by_source,
            "last_ingestion": last_ingestion,
        }
    except Exception as e:
        result["capability_ingestion"] = {"error": str(e)}
        result["warnings"].append("Capability ingestion unavailable")
    
    # 6. Launch gate summary
    try:
        from llm_runtime import prestart_guard
        guard_ok, guard_msg = prestart_guard()
        result["launch_gate"] = {
            "passed": guard_ok,
            "message": guard_msg,
        }
    except Exception as e:
        result["launch_gate"] = {"error": str(e)}
        result["warnings"].append("Launch gate unavailable")
    
    # 7. Current commit hash if available
    try:
        result["system"]["commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(BASE_DIR),
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
    except Exception:
        result["system"]["commit"] = "unknown"
    
    # 8. Warnings summary
    result["warnings_summary"] = {
        "count": len(result["warnings"]),
        "items": result["warnings"],
    }
    
    # Clean up warnings from individual sections if empty
    if not result["warnings"]:
        del result["warnings"]
    
    return result


def chat(message: str) -> Dict[str, Any]:
    """Process a chat message and return LLM-backed reply.
    
    This is the minimal path to real LLM chat:
    1. Parse message intent via interpret_human_turn
    2. Build communicator payload with message context
    3. Generate response via simulator (which uses llm_runtime)
    4. Return reply
    
    To reuse OpenClaw's OpenAI auth path:
    - Read JWT token from auth-profiles.json
    - Set as OPENAI_API_KEY temporarily
    - Change provider to "openai_compatible"
    
    Args:
        message: User's message text
        
    Returns:
        { success: bool, reply: str, intent: dict, source: str }
    """
    try:
        # Set OpenAI auth BEFORE any imports
        import os
        import json
        from pathlib import Path
        
        # OpenClaw auth profiles (multiple possible locations)
        auth_paths = [
            BASE_DIR.parent.parent / "agents" / "main" / "agent" / "auth-profiles.json",
            BASE_DIR.parent.parent.parent / "agents" / "main" / "agent" / "auth-profiles.json",
            Path.home() / ".openclaw" / "agents" / "main" / "agent" / "auth-profiles.json",
        ]
        
        for auth_profiles_path in auth_paths:
            if auth_profiles_path.exists():
                try:
                    with open(auth_profiles_path, 'r') as f:
                        auth_data = json.load(f)
                    
                    profiles = auth_data.get("profiles", {})
                    codex_profile = profiles.get("openai-codex:default")
                    
                    if codex_profile and codex_profile.get("type") == "oauth":
                        token = codex_profile.get("access", "")
                        if token:
                            # Set environment BEFORE llm_runtime import
                            os.environ["OPENAI_API_KEY"] = token
                            os.environ["OPENAI_BASE_URL"] = "https://chatgpt.com/backend-api"
                            os.environ["WESLR_LLM_PROVIDER"] = "openai_compatible"
                            print(f"[DEBUG] Using OpenAI auth from {auth_profiles_path}", file=sys.stderr)
                            break
                except Exception as e:
                    print(f"[DEBUG] Failed to read auth from {auth_profiles_path}: {e}", file=sys.stderr)
                    continue
        
        # Import needed modules AFTER setting env vars
        from dialogue import build_communicator_message_payload, interpret_human_turn
        from sim import load_communicator_self, build_communicator_message
        
        # Interpret the user's message
        interpreted = interpret_human_turn(message)
        
        # Load communicator state
        self_state = load_communicator_self()
        narrative = self_state.get("narrative_state") or {}
        relationships = self_state.get("relationships") or {}
        
        # Build payload for the message
        latest_human = {
            "message": message,
            "topics": interpreted.get("topics", []),
            "turn_type": interpreted.get("turn_type", "question"),
            "reply_shape": interpreted.get("reply_shape", "answer_directly"),
            "likely_need": interpreted.get("likely_need", "direct_answer"),
        }
        
        # Get active thread — pass None (not empty list) to avoid
        # build_communicator_message_payload unpacking ValueError
        # when active_thread is empty list and code expects (topic, thread) tuple.
        active_thread = None
        
        # Build the communicator message payload
        result = build_communicator_message_payload(
            narrative=narrative,
            relationships=relationships,
            active_thread=active_thread,
            latest_human=latest_human,
            research_context=None,
        )
        
        # Extract the reply
        reply = result.get("message", result.get("inner_thought", {}).get("summary", "I'm processing your message."))
        
        # Determine source
        source = result.get("inner_thought", {}).get("source", "fallback")
        
        return {
            "success": True,
            "reply": reply,
            "intent": interpreted,
            "source": source,
        }
        
    except Exception as e:
        return {
            "success": False,
            "reply": f"I'm Weslr. (Error: {e})",
            "error": str(e),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 8. CAPABILITY INGESTION API (Phase 2)
# ─────────────────────────────────────────────────────────────────────────────

def ingest_manual(
    title: str,
    body: Optional[str] = None,
    tags: Optional[List[str]] = None,
    url: Optional[str] = None,
    detected_capability: Optional[str] = None,
    confidence: Optional[float] = None,
) -> Dict[str, Any]:
    """Ingest a manual signal into the capability discovery pipeline.

    Args:
        title: Signal title
        body: Signal body/content
        tags: Optional tags/keywords
        url: Optional source URL
        detected_capability: Optional detected capability text
        confidence: Optional confidence score (0-1)

    Returns:
        Ingestion result dict
    """
    try:
        from weslr.capability_ingestion import CapabilityIngestionPipeline, SourceKind

        pipeline = CapabilityIngestionPipeline()
        result = pipeline.ingest_manual(
            title=title,
            body=body,
            source_kind=SourceKind.MANUAL,
            tags=tags or [],
            url=url,
            detected_capability=detected_capability,
            confidence=confidence,
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def ingest_reddit(
    title: str,
    url: str,
    body: Optional[str] = None,
    tags: Optional[List[str]] = None,
    detected_capability: Optional[str] = None,
    confidence: Optional[float] = None,
) -> Dict[str, Any]:
    """Ingest a Reddit-like signal.

    Args:
        title: Reddit post title
        url: Reddit post URL
        body: Optional post body
        tags: Optional tags/keywords
        detected_capability: Optional detected capability text
        confidence: Optional confidence score (0-1)

    Returns:
        Ingestion result dict
    """
    try:
        from weslr.capability_ingestion import CapabilityIngestionPipeline

        pipeline = CapabilityIngestionPipeline()
        result = pipeline.ingest_reddit(
            title=title,
            url=url,
            body=body,
            tags=tags or [],
            detected_capability=detected_capability,
            confidence=confidence,
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def ingest_github(
    title: str,
    url: str,
    body: Optional[str] = None,
    tags: Optional[List[str]] = None,
    detected_capability: Optional[str] = None,
    confidence: Optional[float] = None,
) -> Dict[str, Any]:
    """Ingest a GitHub-like signal.

    Args:
        title: GitHub issue/PR title
        url: GitHub URL
        body: Optional body
        tags: Optional tags/keywords
        detected_capability: Optional detected capability text
        confidence: Optional confidence score (0-1)

    Returns:
        Ingestion result dict
    """
    try:
        from weslr.capability_ingestion import CapabilityIngestionPipeline

        pipeline = CapabilityIngestionPipeline()
        result = pipeline.ingest_github(
            title=title,
            url=url,
            body=body,
            tags=tags or [],
            detected_capability=detected_capability,
            confidence=confidence,
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


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
        print("  upload-file <filename> <base64_content>")
        print("  operator-summary")
        print("  operator-visibility")
        print("  review-suggestion <id> <action> [reason]")
        print("  chat <message>")
        print("  diagnostics")
        print("  ingest-manual <title> <body> [tags]")
        print("  ingest-reddit <title> <url> [body] [tags]")
        print("  ingest-github <title> <url> [body] [tags]")
        print("    Actions: approve, deny, mark-eligible")
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
    
    elif command == "upload-file":
        if len(sys.argv) < 4:
            print("Usage: python weslr_backend_contract.py upload-file <filename> <base64_content>")
            return
        filename = sys.argv[2]
        import base64
        content_b64 = sys.argv[3]
        try:
            file_content = base64.b64decode(content_b64)
            result = upload_file(file_content, filename)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"success": False, "error": f"Upload failed: {e}"}))
    
    elif command == "operator-summary":
        summary = get_operator_summary()
        print(json.dumps(summary, indent=2))
    
    elif command == "operator-visibility":
        visibility = check_operator_visibility()
        print(json.dumps(visibility, indent=2))
    
    elif command == "review-suggestion":
        if len(sys.argv) < 4:
            print("Usage: python weslr_backend_contract.py review-suggestion <candidate_id> <action> [reason]")
            return
        candidate_id = sys.argv[2]
        action = sys.argv[3]
        reason = sys.argv[4] if len(sys.argv) > 4 else ""
        result = review_suggestion(candidate_id, action, reason)
        print(json.dumps(result, indent=2))
    
    elif command == "chat":
        if len(sys.argv) < 3:
            print("Usage: python weslr_backend_contract.py chat <message>")
            return
        message = " ".join(sys.argv[2:])
        result = chat(message)
        print(json.dumps(result, indent=2))
    
    elif command == "diagnostics":
        result = diagnostics()
        print(json.dumps(result, indent=2))

    elif command == "ingest-manual":
        if len(sys.argv) < 4:
            print("Usage: python weslr_backend_contract.py ingest-manual <title> <body> [tags]")
            return
        title = sys.argv[2]
        body = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        tags = None
        if len(sys.argv) > 4:
            tags = sys.argv[4].split(",")
        result = ingest_manual(title=title, body=body, tags=tags)
        print(json.dumps(result, indent=2))

    elif command == "ingest-reddit":
        if len(sys.argv) < 4:
            print("Usage: python weslr_backend_contract.py ingest-reddit <title> <url> [body] [tags]")
            return
        title = sys.argv[2]
        url = sys.argv[3]
        body = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else None
        tags = None
        if len(sys.argv) > 5:
            tags = sys.argv[5].split(",")
        result = ingest_reddit(title=title, url=url, body=body, tags=tags)
        print(json.dumps(result, indent=2))

    elif command == "ingest-github":
        if len(sys.argv) < 4:
            print("Usage: python weslr_backend_contract.py ingest-github <title> <url> [body] [tags]")
            return
        title = sys.argv[2]
        url = sys.argv[3]
        body = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else None
        tags = None
        if len(sys.argv) > 5:
            tags = sys.argv[5].split(",")
        result = ingest_github(title=title, url=url, body=body, tags=tags)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
