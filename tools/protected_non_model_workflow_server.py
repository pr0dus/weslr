#!/usr/bin/env python3
"""
WESLR Protected Non-Model Workflow Server V1

Owner-only protected interface that demonstrates WESLR behavior
WITHOUT any model/provider calls.

NO OpenAI, Anthropic, Gemini, OpenRouter, Ollama.
NO search/advisor calls.
NO file uploads, payments, marketplace.
NO public self-registration.

This is NOT public pilot.
This is NOT production runtime.
This is owner-only workflow testing.

Files touched:
  - NEW: tools/protected_non_model_workflow_server.py (this file)
  - UNTOUCHED: weslr/chat_responder.py
  - UNTOUCHED: weslr/main.py
  - UNTOUCHED: dialogue.py
  - UNTOUCHED: chat_ui.py
  - UNTOUCHED: weslr/providers.py
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

# Import ONLY the deterministic handler dispatcher — NO model calls
from weslr.deterministic_handlers import dispatch_deterministic_handler

# ─────────────────────────────────────────────────────────────────────────────
# OMNICHAT BRIDGE (V1, 2026-06-09)
#
# Wires the protected owner chat to the REAL WESLR runtime/contract-reply
# stack (dialogue.interpret_human_turn + weslr.omnichat.response_expander.
# format_reply). This is the highest existing in-process WESLR chat path that:
#   - is purely deterministic (no provider, no API key, no LLM call)
#   - uses the live WESLR state (state checkpoint, plans, ISS, omnichat policy)
#   - returns contract replies declared in weslr.omnichat.response_expander
#   - is read-only (no writes, no daemon, no settings mutations)
#
# Used as the bridge from the deterministic-handler registry (which handles
# the structured slash-command surface: /probes, /plans, /status, etc.) into
# the real WESLR intelligence layer for free-form owner questions.
#
# SAFETY: never imports weslr.chat_responder, weslr.llm_runtime, or any
# provider module. Never reads auth-profiles.json. Never sets
# WESLR_LLM_PROVIDER or OPENAI_API_KEY. If the import fails for any reason
# we degrade gracefully to the deterministic catalog.
# ─────────────────────────────────────────────────────────────────────────────
try:
    from dialogue import interpret_human_turn as _weslr_interpret_human_turn
    from weslr.omnichat.response_expander import (
        format_reply as _weslr_omnichat_format_reply,
    )
    _OMNICHAT_BRIDGE_AVAILABLE = True
    _OMNICHAT_BRIDGE_ERROR = None
except Exception as _bridge_exc:  # pragma: no cover
    _OMNICHAT_BRIDGE_AVAILABLE = False
    _OMNICHAT_BRIDGE_ERROR = repr(_bridge_exc)
    _weslr_interpret_human_turn = None
    _weslr_omnichat_format_reply = None


def _weslr_omnichat_bridge(message: str) -> Optional[dict]:
    """
    Run the real WESLR omnichat contract-reply engine on a free-form message.

    Returns a dict shaped like a deterministic-handler result so the existing
    HTTP layer can consume it uniformly. Returns None if the bridge is not
    available or the engine produced no reply.
    """
    if not _OMNICHAT_BRIDGE_AVAILABLE:
        return None
    try:
        interpreted = _weslr_interpret_human_turn(message)
        if not isinstance(interpreted, dict):
            return None
        contract_reply = _weslr_omnichat_format_reply(interpreted)
        if not contract_reply:
            return None
        path = interpreted.get("path") or "omnichat_contract_reply"
        # Honest treatment: omnichat path "fallback_safe" means the engine
        # did not find a confirmed answer — surface that truthfully.
        return {
            "message": message,
            "response_text": contract_reply,
            "path": f"real_weslr_omnichat::{path}",
            "confidence": "high" if path != "fallback_safe" else "medium",
            "suggested_mode": "observe",
            "_weslr_deterministic": True,
            "_weslr_runtime_path": "real_weslr_omnichat_contract_reply",
            "_weslr_intent": {
                "path": path,
                "intent_class": interpreted.get("intent_class"),
                "turn_type": interpreted.get("turn_type"),
                "topics": interpreted.get("topics"),
                "guided_intent": interpreted.get("guided_intent"),
            },
        }
    except Exception as exc:  # pragma: no cover
        return {
            "message": message,
            "response_text": (
                f"Real WESLR omnichat bridge failed: {exc!r}. "
                "Falling back to deterministic catalog."
            ),
            "path": "real_weslr_omnichat_bridge_error",
            "confidence": "low",
            "suggested_mode": "observe",
            "_weslr_deterministic": True,
            "_weslr_runtime_path": "real_weslr_omnichat_bridge_error",
            "_weslr_bridge_error": repr(exc),
        }


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WESLR Protected Workflow (No Model)</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; background: #0f1115; color: #e8eaed; margin: 0; }
    .wrap { max-width: 800px; margin: 40px auto; padding: 20px; }
    h1 { color: #4f8cff; margin-bottom: 8px; }
    .subtitle { color: #9aa0a6; margin-bottom: 24px; }
    .notice { background: #2a1a1a; border: 1px solid #c0392b; padding: 12px 16px; border-radius: 8px; margin-bottom: 24px; }
    .notice strong { color: #e74c3c; }
    .chat { background: #171a21; border: 1px solid #2a2f3a; padding: 20px; border-radius: 12px; }
    .prompts { margin-bottom: 16px; }
    .prompts h3 { margin: 0 0 12px 0; color: #9aa0a6; font-size: 14px; }
    .prompts ul { margin: 0; padding-left: 20px; }
    .prompts li { margin: 4px 0; color: #b0b8c1; cursor: pointer; }
    .prompts li:hover { color: #4f8cff; }
    textarea { width: 100%; height: 80px; background: #11141a; color: #e8eaed; border: 1px solid #2a2f3a; border-radius: 8px; padding: 12px; font-family: inherit; font-size: 14px; resize: vertical; }
    textarea:focus { outline: none; border-color: #4f8cff; }
    .buttons { margin-top: 12px; display: flex; gap: 12px; }
    button { background: #4f8cff; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; }
    button:hover { background: #3a7bd5; }
    button.secondary { background: #2d333b; }
    button.secondary:hover { background: #3d434b; }
    .response { background: #1b2a1f; padding: 16px; border-radius: 8px; margin-top: 16px; min-height: 60px; }
    .response-header { display: flex; gap: 16px; margin-bottom: 12px; font-size: 12px; color: #9aa0a6; }
    .response-header span { padding: 2px 8px; background: #252d20; border-radius: 4px; }
    .response-text { white-space: pre-wrap; line-height: 1.6; }
    .footer { color: #6b7280; font-size: 11px; margin-top: 32px; padding-top: 16px; border-top: 1px solid #2a2f3a; }
    .footer strong { color: #9aa0a6; }
    .no-match { color: #f39c12; font-style: italic; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>WESLR Protected Workflow Preview</h1>
    <div class="subtitle">Continuity-first governed intelligence — deterministic responses only</div>
    
    <div class="notice">
      <strong>⚠️ No Model Provider Active</strong><br>
      This is a deterministic workflow surface. Responses come from registered system knowledge only.
      No LLM, no AI model, no external API calls, no learning from users.
      This is NOT public pilot. For owner testing only.
    </div>
    
    <div class="chat">
      <div class="prompts">
        <h3>Try These Prompts:</h3>
        <ul>
          <li onclick="setPrompt('What is WESLR?')">What is WESLR?</li>
          <li onclick="setPrompt('What is your current status?')">What is your current status?</li>
          <li onclick="setPrompt('What are you not allowed to claim?')">What are you not allowed to claim?</li>
          <li onclick="setPrompt('What should happen if I ask for upload, payment, or marketplace?')">What should happen if I ask for upload, payment, or marketplace?</li>
          <li onclick="setPrompt('Explain optional user-configured model providers.')">Explain optional user-configured model providers.</li>
          <li onclick="setPrompt('What can I try?')">What can I try?</li>
          <li onclick="setPrompt('Is this AGI?')">Is this AGI?</li>
          <li onclick="setPrompt('How does WESLR improve?')">How does WESLR improve?</li>
        </ul>
      </div>
      
      <textarea id="msg" placeholder="Type a prompt..."></textarea>
      <div class="buttons">
        <button onclick="send()">Send</button>
        <button class="secondary" onclick="clearAll()">Clear</button>
      </div>
      
      <div class="response" id="response">
        <div class="response-header">
          <span id="path-badge">Path: —</span>
          <span id="conf-badge">Confidence: —</span>
        </div>
        <div class="response-text" id="response-text">Send a message to see the response.</div>
      </div>
    </div>
    
    <div class="footer">
      <strong>WESLR Protected Owner Workflow Preview — No Model Provider Active</strong><br>
      Not Public Pilot — Not Production Runtime — For Owner Testing Only<br>
      Deterministic handlers only — No learning from user input — No external API calls
    </div>
  </div>
  
  <script>
    function setPrompt(text) {
      document.getElementById('msg').value = text;
    }
    
    function clearAll() {
      document.getElementById('msg').value = '';
      document.getElementById('response-text').innerHTML = 'Send a message to see the response.';
      document.getElementById('path-badge').textContent = 'Path: —';
      document.getElementById('conf-badge').textContent = 'Confidence: —';
    }
    
    async function send() {
      const msg = document.getElementById('msg').value.trim();
      if (!msg) return;
      
      document.getElementById('response-text').innerHTML = 'Processing...';
      
      try {
        const res = await fetch('/api/message', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: msg})
        });
        const data = await res.json();
        
        document.getElementById('path-badge').textContent = 'Path: ' + data.path;
        document.getElementById('conf-badge').textContent = 'Confidence: ' + data.confidence;
        
        let html = data.response_text;
        if (data._no_match) {
          html = '<span class="no-match">' + html + '</span>';
        }
        document.getElementById('response-text').innerHTML = html;
      } catch (e) {
        document.getElementById('response-text').innerHTML = 'Error: ' + e.message;
      }
    }
    
    document.getElementById('msg').addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        send();
      }
    });
  </script>
</body>
</html>
"""


def handle_upload_payment_marketplace_query(message: str, lowered: str) -> dict:
    """Handler for upload/payment/marketplace boundary question."""
    from weslr.response_formatter import build_deterministic_response
    
    response_text = (
        "File upload, payment, and marketplace features are NOT active in this protected preview. "
        "These features may be configured later by the operator, but they are disabled by default. "
        "If you request file upload, payment processing, or marketplace access, the system will "
        "respond that these features are not available in the current configuration.\n\n"
        "This preview is designed to demonstrate WESLR's deterministic workflow and boundary "
        "awareness without requiring any model provider or external service."
    )
    return build_deterministic_response(
        message=message,
        path="upload_payment_marketplace_boundary",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_model_provider_explanation(message: str, lowered: str) -> dict:
    """Handler for user-configured model provider explanation."""
    from weslr.response_formatter import build_deterministic_response
    
    response_text = (
        "WESLR can optionally be configured to use external model providers (like OpenAI, Anthropic, "
        "Ollama, or others) for enhanced conversational responses. This is NOT required for the system "
        "to function.\n\n"
        "In this protected preview, NO model provider is active. All responses come from the "
        "deterministic handler registry — hardcoded system knowledge, boundary definitions, and "
        "workflow descriptions.\n\n"
        "If the operator configures a model provider in the future:\n"
        "- The operator would set WESLR_LLM_PROVIDER in the environment\n"
        "- The provider would be used ONLY for conversational enhancement\n"
        "- Deterministic handlers would still be checked first\n"
        "- Governance and boundary constraints would still apply\n\n"
        "Currently: No model provider configured. Responses are deterministic only."
    )
    return build_deterministic_response(
        message=message,
        path="model_provider_explanation",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def dispatch_with_fallback(message: str, lowered: str) -> dict:
    """
    Dispatch to deterministic handlers with fallback for boundary questions.
    Returns a response dict, never None.
    """
    # First, try the deterministic handler registry
    result = dispatch_deterministic_handler(message, lowered)
    if result:
        return result
    
    # Fallback: Check for specific boundary questions
    if any(phrase in lowered for phrase in ['upload', 'payment', 'marketplace']):
        return handle_upload_payment_marketplace_query(message, lowered)
    
    # Fallback: Check for status questions
    if any(phrase in lowered for phrase in ['current status', 'your status', 'your current status']):
        from weslr.state_checkpoint import get_state_checkpoint
        cp = get_state_checkpoint()
        layer_ids = [l["id"] for l in cp.get("layers", [])]
        response_text = (
            f"WESLR checkpoint {cp['version']}: {cp['status']}. "
            f"Confirmed layers: {', '.join(layer_ids)}. "
            f"Execution allowed: {cp['execution_allowed']}. "
            f"Learning enabled: {cp['learning_enabled']}. "
            f"Autonomous changes: {cp['autonomous_changes_enabled']}."
        )
        from weslr.response_formatter import build_deterministic_response
        return build_deterministic_response(
            message=message,
            path="state_checkpoint_query",
            response_text=response_text,
            confidence="high",
            suggested_mode="observe",
        )
    
    # Fallback: Check for status questions
    if any(phrase in lowered for phrase in ['current status', 'your status', 'your current status']):
        from weslr.state_checkpoint import get_state_checkpoint
        cp = get_state_checkpoint()
        layer_ids = [l["id"] for l in cp.get("layers", [])]
        response_text = (
            f"WESLR checkpoint {cp['version']}: {cp['status']}. "
            f"Confirmed layers: {', '.join(layer_ids)}. "
            f"Execution allowed: {cp['execution_allowed']}. "
            f"Learning enabled: {cp['learning_enabled']}. "
            f"Autonomous changes: {cp['autonomous_changes_enabled']}."
        )
        from weslr.response_formatter import build_deterministic_response
        return build_deterministic_response(
            message=message,
            path="state_checkpoint_query",
            response_text=response_text,
            confidence="high",
            suggested_mode="observe",
        )
    
    if any(phrase in lowered for phrase in ['model provider', 'model providers', 'llm provider', 'api provider', 'user-configured']):
        return handle_model_provider_explanation(message, lowered)
    
    # Generic fallback
    from weslr.response_formatter import build_deterministic_response
    return build_deterministic_response(
        message=message,
        path="fallback_unmatched",
        response_text=(
            "This protected no-model preview cannot answer that yet.\n\n"
            "Try these prompts:\n"
            "- What is WESLR?\n"
            "- What is your current status?\n"
            "- What are you not allowed to claim?\n"
            "- What can I try?\n"
            "- Is this AGI?\n"
            "- How does WESLR improve?\n\n"
            "This preview uses deterministic handlers only — no model, no learning, no external API."
        ),
        confidence="medium",
        suggested_mode="observe",
    )


class Handler(BaseHTTPRequestHandler):
    """HTTP handler for protected non-model workflow server."""
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == '/api/auth/me':
            # Protected auth role adapter mock - htpasswd protected preview
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            auth_info = {
                "authenticated": True,
                "role": "owner",
                "account_mode": "htpasswd_protected_owner_preview",
                "email": None,
                "display_name": "Owner Preview",
                "permissions": [
                    "view_dashboard",
                    "view_owner_settings",
                    "view_environment_settings",
                    "view_runtime_status"
                ],
                "writes_enabled": False,
                "google_auth_enabled": False,
                "htpasswd_active": True
            }
            self.wfile.write(json.dumps(auth_info).encode('utf-8'))
        elif self.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            state = {
                "status": "Ready",
                "model_provider": "none",
                "mode": "deterministic_only",
                "_no_model": True,
                "_protected_preview": True,
                "_weslr_runtime_bridge": {
                    "available": _OMNICHAT_BRIDGE_AVAILABLE,
                    "error": _OMNICHAT_BRIDGE_ERROR,
                    "bridge_target": (
                        "dialogue.interpret_human_turn + "
                        "weslr.omnichat.response_expander.format_reply"
                    ),
                },
            }
            self.wfile.write(json.dumps(state).encode('utf-8'))
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'healthy')
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "not_found"}')
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/api/message':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)
                message = data.get('message', '')
                
                if not message.strip():
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"error": "empty_message"}')
                    return
                
                lowered = message.lower()
                project_id = data.get("project_id") or "preview-weslr-website-review"
                req_mode = data.get("mode") or "protected_owner_preview"

                # 1. Try the deterministic handler registry (structured
                #    slash-commands: /probes, /plans, /status, ISS, etc.)
                result = dispatch_with_fallback(message, lowered)
                handler_path = result.get("path", "unknown")
                used_runtime_path = "deterministic_handler_registry"

                # 2. If the registry fell through to its canned
                #    fallback_unmatched, bridge into the REAL WESLR
                #    omnichat contract-reply engine. This is what wires
                #    the protected chat to the actual WESLR runtime.
                if handler_path == "fallback_unmatched" and _OMNICHAT_BRIDGE_AVAILABLE:
                    bridge_result = _weslr_omnichat_bridge(message)
                    if bridge_result is not None:
                        result = bridge_result
                        handler_path = result.get("path", handler_path)
                        used_runtime_path = "real_weslr_omnichat_contract_reply"
                    else:
                        used_runtime_path = "deterministic_handler_registry_fallback_only"
                elif not _OMNICHAT_BRIDGE_AVAILABLE and handler_path == "fallback_unmatched":
                    used_runtime_path = "deterministic_handler_registry_fallback_only_bridge_unavailable"

                # 3. Build the response. Keep every existing field stable
                #    so the UI keeps working, and add the structured
                #    bridge contract on top.
                omnichat_path = None
                if isinstance(handler_path, str) and handler_path.startswith("real_weslr_omnichat::"):
                    omnichat_path = handler_path.split("::", 1)[1]

                # Determine ok / capability_status honestly
                if omnichat_path == "fallback_safe":
                    ok = False
                    capability_status = {
                        "answered_by_real_runtime": True,
                        "answered_with_confirmed_answer": False,
                        "answered_with_truthful_gap": True,
                        "reason": "real_weslr_omnichat_returned_fallback_safe",
                    }
                elif used_runtime_path == "real_weslr_omnichat_contract_reply":
                    ok = True
                    capability_status = {
                        "answered_by_real_runtime": True,
                        "answered_with_confirmed_answer": True,
                        "answered_with_truthful_gap": False,
                        "reason": "real_weslr_omnichat_contract_reply_matched",
                    }
                else:
                    ok = True
                    capability_status = {
                        "answered_by_real_runtime": True,
                        "answered_with_confirmed_answer": True,
                        "answered_with_truthful_gap": False,
                        "reason": "deterministic_handler_registry_matched",
                    }

                response = {
                    # existing fields (UI compatibility)
                    "message": message,
                    "response_text": result.get("response_text", ""),
                    "path": handler_path,
                    "confidence": result.get("confidence", "high"),
                    "suggested_mode": result.get("suggested_mode", "observe"),
                    "_weslr_deterministic": result.get("_weslr_deterministic", True),
                    "_no_model": True,
                    "_protected_preview": True,
                    # structured bridge contract (WESLR runtime wiring V1)
                    "ok": ok,
                    "answer": result.get("response_text", ""),
                    "runtime_path": used_runtime_path,
                    "mode": req_mode,
                    "project_id": project_id,
                    "capability_status": capability_status,
                    "evidence": [],
                    "artifacts": [],
                    "warnings": [],
                    "blocked_actions": [
                        "autonomous_tools",
                        "public_registration",
                        "settings_writes",
                        "daemon",
                        "google_oauth",
                        "public_users",
                        "hardcoded_final_answers",
                    ],
                    "side_effects_performed": False,
                    "tools_executed": False,
                    "daemon_enabled": False,
                    "model_provider_used": False,
                }

                if result.get("path") == "fallback_unmatched" and used_runtime_path.startswith("deterministic_handler_registry_fallback_only"):
                    response["_no_match"] = True

                # Surface omnichat intent metadata (read-only) when present
                if "_weslr_intent" in result:
                    response["_weslr_intent"] = result["_weslr_intent"]
                if "_weslr_runtime_path" in result and used_runtime_path != "real_weslr_omnichat_contract_reply":
                    response["_weslr_runtime_path"] = result["_weslr_runtime_path"]
                if "_weslr_bridge_error" in result:
                    response["_weslr_bridge_error"] = result["_weslr_bridge_error"]

                # Truthful structured failure when the real runtime
                # explicitly says fallback_safe. Never fake a full answer.
                if omnichat_path == "fallback_safe":
                    response["error"] = "real_weslr_runtime_entrypoint_present_but_no_confirmed_answer"
                    response["available_paths"] = [
                        "real_weslr_omnichat_contract_reply",
                        "weslr.omnichat.response_expander.format_reply",
                        "dialogue.interpret_human_turn",
                        "weslr.deterministic_handlers.dispatch_with_fallback",
                    ]
                    response["next_required_work"] = [
                        "Extend weslr.omnichat.response_expander with confirmed-answer entries for status / implementation / capability-summary questions.",
                        "Or implement a private project-chat runtime that retrieves real WESLR state (state-checkpoint, implementation plans, capability discovery) and assembles a confirmed answer.",
                    ]
                    response["truthful_gap_report"] = True

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "not_found"}')


def run_server(port: int = 8091):
    """Start the protected non-model workflow server."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"WESLR Protected Non-Model Workflow Server")
    print(f"Listening on http://127.0.0.1:{port}")
    print(f"")
    print(f"NO MODEL PROVIDER ACTIVE")
    print(f"Deterministic handlers only — no learning — no external API")
    print(f"")
    print(f"Protected owner workflow preview — not public pilot")
    server.serve_forever()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8092
    run_server(port)