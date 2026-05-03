#!/usr/bin/env python3
"""
WESLR Staging Demo Server V1 — With Hybrid Turn Arbiter

Provides /chat endpoint, calls weslr_backend_contract.chat(),
wires arbiter-based dispatch, and logs arbiter decisions.

Rules:
- Arbiter determines which bridge answers
- Append-only arbiter decision logging
- No raw prompt storage
- No PII
- No behavior change beyond routing
- ignore storage failures silently
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Workspace path
WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE))

from weslr_backend_contract import chat as weslr_chat


# ─────────────────────────────────────────────────────────────────────────────
# Per-session turn history (in-memory, not persisted)
# ─────────────────────────────────────────────────────────────────────────────

# Map from session_id → list of prior analyze_turn results
_SESSION_HISTORY: dict[str, list] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Arbiter decision logger (append-only)
# ─────────────────────────────────────────────────────────────────────────────

_ARBITER_LOG_PATH = Path(__file__).resolve().parents[1] / "weslr" / "arbiter_decisions.jsonl"
_ARBITER_LOG_PATH = _ARBITER_LOG_PATH.resolve()


def _log_arbiter_decision(
    user_id: str,
    session_id: str,
    message: str,
    analysis: dict,
) -> None:
    """Append an arbiter decision to arbiter_decisions.jsonl.

    Errors are silent — logging failure never affects the response.
    """
    try:
        log_entry = {
            "timestamp": time.time(),
            "datetime_utc": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
            "selected_layer": analysis.get("selected_layer"),
            "turn_kind": analysis.get("turn_kind"),
            "target_scope": analysis.get("target_scope"),
            "requires_evidence": analysis.get("requires_evidence"),
            "requires_memory": analysis.get("requires_memory"),
            "requires_action": analysis.get("requires_action"),
            "confidence": analysis.get("confidence"),
            "ambiguity": analysis.get("ambiguity"),
            "candidate_capabilities": analysis.get("candidate_capabilities", []),
            "external_topic": analysis.get("external_topic"),
            "clarification_question": analysis.get("clarification_question"),
            "authority": analysis.get("authority"),
            "automatic_action": analysis.get("automatic_action", False),
        }
        with open(_ARBITER_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Arbiter dispatch
# ─────────────────────────────────────────────────────────────────────────────

def _dispatch_by_arbiter(
    message: str,
    analysis: dict,
    user_id: str,
    session_id: str,
    original_response: dict,
) -> dict:
    """Dispatch to the appropriate bridge based on arbiter selected_layer.

    Each branch returns a response dict with at least: reply, path.
    """
    selected = analysis.get("selected_layer", "fallback")
    continuity_metadata = None
    workplace_metadata = None
    capability_metadata = None
    evidence_metadata = None

    # ── Continuity ──────────────────────────────────────────────────────
    if selected == "continuity":
        try:
            from weslr.continuity_note_chat_bridge import maybe_answer_with_continuity_note
            result = maybe_answer_with_continuity_note(message)
            if result:
                return {
                    "reply": result["reply"],
                    "path": result["path"],
                    "response_contract": result.get("response_contract"),
                    "_continuity_metadata": result["_continuity_metadata"],
                }
        except Exception:
            pass  # Fall through to next

    # ── Workplace ────────────────────────────────────────────────────────
    if selected == "workplace":
        try:
            from weslr.workplace_chat_bridge import maybe_answer_with_workplace
            result = maybe_answer_with_workplace(message)
            if result:
                return {
                    "reply": result["reply"],
                    "path": result["path"],
                    "response_contract": result.get("response_contract"),
                    "_workplace_metadata": result["_workplace_metadata"],
                }
        except Exception:
            pass  # Fall through to next

    # ── Clarification ───────────────────────────────────────────────────
    if selected == "clarification":
        return {
            "reply": analysis.get(
                "clarification_question",
                "I'm not sure what you're asking. Could you rephrase?",
            ),
            "path": "clarification",
            "response_contract": "clarification",
            "_arbiter_metadata": {
                "authority": "routing_analysis_only",
                "automatic_action": False,
            },
        }

    # ── Capability Welcome ──────────────────────────────────────────────
    if selected == "capability_welcome":
        try:
            from weslr.capability_welcome_chat_bridge import maybe_answer_with_capability_welcome
            result = maybe_answer_with_capability_welcome(message)
            if result:
                return {
                    "reply": result["reply"],
                    "path": result["path"],
                    "response_contract": result.get("response_contract"),
                    "_capability_metadata": result["_capability_metadata"],
                }
        except Exception:
            pass  # Fall through to fallback

    # ── Evidence ────────────────────────────────────────────────────────
    if selected == "evidence":
        try:
            from weslr.evidence_chat_bridge import maybe_answer_with_evidence
            result = maybe_answer_with_evidence(message, original_response.get("reply"))
            if result:
                return {
                    "reply": result["message"],
                    "path": result["path"],
                    "response_contract": result.get("response_contract"),
                    "_evidence_metadata": result["evidence_metadata"],
                }
        except Exception:
            pass  # Fall through to fallback

    # ── Fallback (including "fallback" layer and any unhandled case) ──
    return {
        "reply": original_response.get(
            "reply",
            "I'm not sure how to respond to that. Try /help or ask a more specific question.",
        ),
        "path": "fallback",
        "response_contract": "conversational_entry",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Session helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_session_id(request) -> str:
    """Derive or generate a session ID from the request."""
    return str(uuid.uuid4())


def _get_user_id(data: dict) -> str:
    """Extract user_id from request data, default 'arthur'."""
    return data.get("user_id", "arthur")


# ─────────────────────────────────────────────────────────────────────────────
# Signal capture (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_signal_fields(response: dict) -> dict:
    """Extract signal-relevant fields from the chat response dict."""
    return {
        "response_path": response.get("source") or response.get("intent", {}).get("path") or "unknown",
        "quality_class": response.get("intent", {}).get("_quality_class") or "unknown",
        "blocked_write": bool(response.get("intent", {}).get("path") == "blocked_write"),
        "evidence_offer_shown": bool(
            response.get("intent", {}).get("_omnichat_policy", {}).get("evidence_offer")
            if isinstance(response.get("intent", {}).get("_omnichat_policy"), dict)
            else False
        ),
        "evidence_offer_accepted": False,
        "fallback_triggered": bool(
            response.get("intent", {}).get("path") in ("fallback_safe", "fallback_template")
        ),
        "topic_normalized": (
            response.get("intent", {}).get("topics", [None])[0]
            if response.get("intent", {}).get("topics")
            else None
        ),
    }


def _capture_signal(message: str, session_id: str, response: dict) -> None:
    """Fire-and-forget signal capture after chat response is built."""
    try:
        from weslr.website_signal_integration import capture_website_signal
    except Exception:
        return

    fields = _extract_signal_fields(response)

    try:
        capture_website_signal(
            message=message,
            session_id=session_id,
            response_path=fields["response_path"],
            quality_class=fields["quality_class"],
            blocked_write=fields["blocked_write"],
            evidence_offer_shown=fields["evidence_offer_shown"],
            evidence_offer_accepted=fields["evidence_offer_accepted"],
            topic_normalized=fields["topic_normalized"],
            fallback_triggered=fields["fallback_triggered"],
        )
    except Exception:
        return


# ─────────────────────────────────────────────────────────────────────────────
# HTTP Handler
# ─────────────────────────────────────────────────────────────────────────────

class WeslrDemoHandler(BaseHTTPRequestHandler):
    """Handles /chat and health endpoints for staging demo with arbiter routing."""

    def log_message(self, format, *args):
        pass  # Silent in staging

    # ── Static / Health ─────────────────────────────────────────────────────

    STATIC_DIR = WORKSPACE / "deploy" / "staging" / "static"

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            index_path = self.STATIC_DIR / "index.html"
            if index_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(index_path.read_bytes())
                return
            self.send_error(404, "index.html not found")
            return

        if self.path.startswith("/static/"):
            rel_path = self.path[len("/static/"):]
            file_path = self.STATIC_DIR / rel_path
            if file_path.is_file():
                import mimetypes
                mime, _ = mimetypes.guess_type(str(file_path))
                self.send_response(200)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return
            self.send_error(404, "not found")
            return

        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "weslr-demo-staging"}).encode())
            return

        self.send_error(404, "Not found")

    # ── Chat ─────────────────────────────────────────────────────────────────

    def do_POST(self):
        if self.path != "/chat":
            self.send_error(404, "Not found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            data = json.loads(body) if body.strip() else {}
        except Exception:
            self.send_error(400, "Invalid JSON")
            return

        message = data.get("message", "")
        if not message:
            self.send_error(400, "message field required")
            return

        # ── Session setup ────────────────────────────────────────────────────
        session_id = _get_session_id(self)
        user_id = _get_user_id(data)

        # ── Build original response (for fallback) ────────────────────────────
        try:
            original_response = weslr_chat(message)
        except Exception as e:
            original_response = {"reply": f"Error: {e}", "error": str(e)}

        # ── Build arbiter context ─────────────────────────────────────────────
        try:
            from weslr.arbiter_context_builder import build_arbiter_context
            ctx = build_arbiter_context(
                user_id=user_id,
                current_message=message,
                session_turn_history=_SESSION_HISTORY.get(session_id, []),
            )
        except Exception:
            # Non-critical: use minimal context
            ctx = {
                "user_id": user_id,
                "recent_timeline_events": [],
                "entity_timeline_events": [],
                "workplace_overview": None,
                "pending_experiment_proposals": [],
                "session_turn_history": _SESSION_HISTORY.get(session_id, []),
            }

        # ── Run arbiter ───────────────────────────────────────────────────────
        try:
            from weslr.hybrid_turn_arbiter import analyze_turn
            analysis = analyze_turn(message, context=ctx)
        except Exception as e:
            # Non-critical: fallback routing if arbiter fails
            analysis = {
                "selected_layer": "fallback",
                "turn_kind": "unknown",
                "ambiguity": "high",
                "confidence": 0.0,
                "authority": "routing_analysis_only",
                "automatic_action": False,
            }

        # ── Update session history ─────────────────────────────────────────────
        if session_id not in _SESSION_HISTORY:
            _SESSION_HISTORY[session_id] = []
        _SESSION_HISTORY[session_id].append(analysis)
        # Keep history bounded to last 20 turns
        if len(_SESSION_HISTORY[session_id]) > 20:
            _SESSION_HISTORY[session_id] = _SESSION_HISTORY[session_id][-20:]

        # ── Log arbiter decision (append-only) ────────────────────────────────
        _log_arbiter_decision(
            user_id=user_id,
            session_id=session_id,
            message=message,
            analysis=analysis,
        )

        # ── Dispatch to bridge based on arbiter decision ─────────────────────
        response = _dispatch_by_arbiter(
            message=message,
            analysis=analysis,
            user_id=user_id,
            session_id=session_id,
            original_response=original_response,
        )

        # ── Inject pending queue messages ─────────────────────────────
        try:
            from weslr.pending_messages_queue import dequeue_all, format_queue_messages
            pending = dequeue_all(session_id=session_id)
            if pending:
                queue_text = format_queue_messages(pending)
                if queue_text:
                    response["reply"] = queue_text + "\n\n" + response["reply"]
        except Exception:
            pass

        # ── Signal capture (fire-and-forget, zero user impact) ────────────────
        _capture_signal(message=message, session_id=session_id, response=response)

        # ── Return response ───────────────────────────────────────────────────
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())

    # CORS preflight
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Session-ID")
        self.end_headers()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def run(port: int = 8080, host: str = "0.0.0.0") -> None:
    server = ThreadingHTTPServer((host, port), WeslrDemoHandler)
    print(f"WESLR Staging Demo Server — http://{host}:{port}/chat")
    print(f"Arbiter routing: ENABLED")
    print(f"Arbiter log: {_ARBITER_LOG_PATH}")
    print(f"Signal capture: website_signal_integration.capture_website_signal")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WESLR Staging Demo Server")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    run(port=args.port, host=args.host)
