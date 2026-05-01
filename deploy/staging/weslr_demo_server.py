#!/usr/bin/env python3
"""
WESLR Staging Demo Server V1

Minimal HTTP server for staging validation of public signal capture.
Provides /chat endpoint, calls weslr_backend_contract.chat(),
and wires capture_website_signal() after response is built.

Rules:
- return original response unchanged
- no raw prompt storage
- no PII
- no behavior change
- ignore storage failures
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Workspace path
WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE))

from weslr_backend_contract import chat as weslr_chat


def _get_session_id(request) -> str:
    """Derive or generate a session ID from the request.
    
    Uses X-Session-ID header if present, otherwise generates
    an anonymous UUID. Raw session ID is never stored —
    only its hash goes into signals.
    """
    return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# Signal capture — extracted from response metadata only
# ─────────────────────────────────────────────────────────────────────────────

def _extract_signal_fields(response: dict) -> dict:
    """Extract signal-relevant fields from the chat response dict.
    
    Never extracts raw message content — only metadata about
    the response path and classification.
    """
    return {
        "response_path": response.get("source") or response.get("intent", {}).get("path") or "unknown",
        "quality_class": response.get("intent", {}).get("_quality_class") or "unknown",
        "blocked_write": bool(response.get("intent", {}).get("path") == "blocked_write"),
        "evidence_offer_shown": bool(
            response.get("intent", {}).get("_omnichat_policy", {}).get("evidence_offer")
            if isinstance(response.get("intent", {}).get("_omnichat_policy"), dict)
            else False
        ),
        "evidence_offer_accepted": False,  # Not surfaced in response metadata in V1
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
    """Fire-and-forget signal capture after chat response is built.
    
    Errors are silent — response is NEVER affected.
    """
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
    """Handles /chat and health endpoints for staging demo."""

    def log_message(self, format, *args):
        pass  # Silent in staging

    # ── Health ────────────────────────────────────────────────────────────────

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

        # Serve static files from /static/ prefix
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

        # Generate session ID for this request
        session_id = _get_session_id(self)

        # ── Build response (original chat behavior unchanged) ────────────────
        try:
            response = weslr_chat(message)
        except Exception as e:
            response = {"success": False, "reply": f"Error: {e}", "error": str(e)}

        # ── Capability Welcome Bridge ─────────────────────────────────────────
        # Only activates for help/welcome/capability overview queries.
        # Runs BEFORE evidence bridge — /help must never trigger evidence search.
        # Bounded: additive only, never overrides genuine synthesis.
        try:
            from weslr.capability_welcome_chat_bridge import maybe_answer_with_capability_welcome
            _bridge_result = maybe_answer_with_capability_welcome(message, response)
            if _bridge_result:
                response["reply"] = _bridge_result["reply"]
                response["path"] = _bridge_result["path"]
                response["response_contract"] = _bridge_result.get("response_contract")
                response["_capability_metadata"] = _bridge_result["_capability_metadata"]
        except Exception:
            pass  # Non-critical — keep existing response on any bridge failure

        # ── Evidence Chat Bridge (Tier-A safe injection) ─────────────────────
        # Only activates when: search enabled, evidence_needed=true,
        # current reply is fallback/template/generic, message is not self/system.
        # Bounded: additive only, never overrides genuine synthesis.
        try:
            from weslr.evidence_chat_bridge import maybe_answer_with_evidence
            _bridge_result = maybe_answer_with_evidence(
                message,
                response.get("reply"),
            )
            if _bridge_result:
                response["reply"] = _bridge_result["message"]
                response["path"] = _bridge_result["path"]
                response["response_contract"] = _bridge_result.get("response_contract")
                response["_evidence_metadata"] = _bridge_result["evidence_metadata"]
        except Exception:
            pass  # Non-critical — keep existing response on any bridge failure

        # ── Signal capture (fire-and-forget, zero user impact) ────────────────
        _capture_signal(message=message, session_id=session_id, response=response)

        # ── Return original response unchanged ─────────────────────────────────
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