# WESLR Protected Non-Model Workflow Surface Plan V1

**Date:** 2026-05-30  
**Status:** Design phase — implementation pending owner approval  
**Goal:** Create minimal protected owner-only workflow surface WITHOUT model/provider calls

---

## Phase A: Existing No-Model Modules Analysis

### 1. Which existing WESLR no-model modules can produce a response/workflow?

**Primary Module:** `weslr/deterministic_handlers.py`

This is the core non-model response system. It provides:

| Handler | Trigger | Response | Model? |
|---------|---------|----------|--------|
| `handle_system_definition_query` | "what is weslr" | Deterministic WESLR definition | NO |
| `handle_self_identity_query` | "what are you", "who are you" | Self-identity response | NO |
| `handle_state_checkpoint` | "show weslr status" | Architecture status | NO |
| `handle_operator_overview` | "show system overview" | Full system status | NO |
| `handle_usage_guidance` | "what can i try" | Usage examples | NO |
| `handle_agi_clarification` | "is this agi" | AGI boundary clarification | NO |
| `handle_self_improvement_clarification` | "is weslr self-improving" | Self-improvement boundary | NO |
| `handle_learning_clarification` | "can weslr learn from users" | Learning boundary | NO |
| `handle_capability_help_query` | "what can you help me with" | Capability examples | NO |
| `handle_uncertainty_explanation_query` | "what if you don't know" | Uncertainty boundary | NO |
| `handle_continuity_explanation` | "why continuity matters" | Continuity explanation | NO |
| `handle_improvement_query` | "how does weslr improve" | Improvement explanation | NO |
| `handle_origin_query` | "why was weslr created" | Origin explanation | NO |

**Entry Point:** `dispatch_deterministic_handler(message, lowered)`

Returns:
```python
{
    "message": str,
    "response_text": str,
    "path": str,  # e.g., "system_definition_query"
    "_weslr_deterministic": True,
    "confidence": str,  # "high" or "medium"
    "suggested_mode": str,  # "observe" typically
}
```

**Secondary Modules (helpers only, not user-facing):**

| Module | Purpose | User-facing? |
|--------|---------|--------------|
| `weslr/state_checkpoint.py` | Architecture status | Indirect (via handlers) |
| `weslr/response_formatter.py` | Response formatting | No |
| `weslr/iss/probe_registry.py` | ISS probe definitions | Indirect |
| `weslr/implementation_planning.py` | Plan storage | Indirect |
| `weslr/proposal_traceability.py` | Proposal tracking | Indirect |

### 2. Which modules are only report/metadata helpers and cannot be user-facing yet?

| Module | Purpose | Can be user-facing? |
|--------|---------|---------------------|
| `weslr/iss/diagnostic_records.py` | ISS diagnostics storage | No — internal format |
| `weslr/iss/probe_planning.py` | Probe plan creation | No — internal format |
| `weslr/artifact_store.py` | Artifact storage | No — internal format |
| `weslr/lineage_inspector.py` | Lineage tracking | No — internal format |
| `weslr/channel_identity.py` | Channel management | No — internal format |

**Conclusion:** Use `deterministic_handlers.py` directly. It wraps all helpers.

### 3. What is the safest minimal owner-only interface?

**Safest approach:** Create a **new isolated file** that:
- Imports ONLY `dispatch_deterministic_handler` from `weslr.deterministic_handlers`
- Serves a minimal HTML/JSON interface
- Does NOT import or call any model provider
- Runs on a dedicated port
- Is protected by existing Basic Auth
- Clearly labels itself as "protected owner workflow preview — no model provider active"

**File:** `tools/protected_non_model_workflow_server.py`

### 4. Can it answer the test prompts?

| Prompt | Handler | Response Quality |
|--------|---------|------------------|
| "What is WESLR?" | `handle_system_definition_query` | ✅ Deterministic definition |
| "What is your current status?" | `handle_state_checkpoint` or `handle_operator_overview` | ✅ Architecture status |
| "What are you not allowed to claim?" | `handle_agi_clarification` + `handle_self_improvement_clarification` | ✅ Boundary clarification |
| "What should happen if I ask for upload/payment/marketplace?" | **Need to add handler** | ⚠️ Not in registry |
| "Explain optional user-configured model providers." | **Need to add handler** | ⚠️ Not in registry |

**Two prompts need new handlers:**
1. Upload/payment/marketplace boundary
2. User-configured model providers explanation

**Solution:** Add minimal handlers to `deterministic_handlers.py` OR add inline fallback in the server.

### 5. What will the response be based on?

**Basis:**
- WESLR doctrine (hardcoded in `state_checkpoint.py`)
- Registered system knowledge (hardcoded in handlers)
- Deterministic routing (prefix matching)
- No model calls
- No external API calls
- No search/advisor calls

**Examples:**
```
"What is WESLR?" → "WESLR is a Continuity Intelligence System — not a chatbot..."
"What are you?" → "I am WESLR — a deterministic continuity system..."
"Is this AGI?" → "No — WESLR is not AGI..."
```

### 6. What will it NOT do?

- NO model/provider calls
- NO OpenAI, Anthropic, Gemini, OpenRouter, Ollama
- NO search/advisor calls
- NO file uploads
- NO payments
- NO marketplace
- NO account creation
- NO public self-registration
- NO secrets
- NO writes to core files
- NO modification of weslr/chat_responder.py
- NO modification of weslr/main.py
- NO modification of dialogue.py
- NO patching handle_direct_message

### 7. What files would need to be added?

| File | Purpose | Location |
|------|---------|----------|
| `protected_non_model_workflow_server.py` | HTTP server + minimal HTML interface | `/home/pr0/projects/weslr/tools/` |
| (nginx update) | Route chat.weslr.de to new server | `/etc/nginx/conf.d/weslr-unified-8080.conf` |

**Total new files:** 1 (the server)
**Modified files:** 1 (nginx config — route change only)

### 8. What existing files must remain untouched?

| File | Reason |
|------|--------|
| `weslr/chat_responder.py` | Owner constraint |
| `weslr/main.py` | Owner constraint |
| `dialogue.py` | Owner constraint |
| `chat_ui.py` | Old model-dependent path (don't use) |
| `weslr/providers.py` | Don't call |
| All WESLR core modules | Import only, don't modify |

### 9. How can it be rolled back?

**Rollback procedure:**
1. Stop the protected server process
2. Revert nginx config to route chat.weslr.de to static site
3. Delete `tools/protected_non_model_workflow_server.py`
4. No core files were modified — complete rollback

**Rollback command:**
```bash
# Stop server
pkill -f protected_non_model_workflow_server.py

# Revert nginx
# (restore previous config pointing to static site)

# Delete file
rm /home/pr0/projects/weslr/tools/protected_non_model_workflow_server.py
```

---

## Proposed Implementation

### Server Design

```python
# tools/protected_non_model_workflow_server.py

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
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from weslr.deterministic_handlers import dispatch_deterministic_handler

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>WESLR Protected Workflow (No Model)</title>
  <style>
    body { font-family: system-ui; background: #0f1115; color: #e8eaed; }
    .wrap { max-width: 800px; margin: 40px auto; padding: 20px; }
    h1 { color: #4f8cff; }
    .notice { background: #2a1a1a; border: 1px solid #c0392b; padding: 12px; border-radius: 8px; margin-bottom: 20px; }
    .chat { background: #171a21; border: 1px solid #2a2f3a; padding: 16px; border-radius: 12px; }
    .response { background: #1b2a1f; padding: 12px; border-radius: 8px; margin-top: 12px; }
    textarea { width: 100%; height: 80px; background: #11141a; color: #e8eaed; border: 1px solid #2a2f3a; border-radius: 8px; padding: 12px; }
    button { background: #4f8cff; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; margin-top: 12px; }
    button:hover { background: #3a7bd5; }
    .footer { color: #9aa0a6; font-size: 12px; margin-top: 40px; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>WESLR Protected Workflow Preview</h1>
    <div class="notice">
      <strong>⚠️ No Model Provider Active</strong><br>
      This is a deterministic workflow surface. It uses registered system knowledge only.
      No LLM, no AI model, no external API calls.
    </div>
    <div class="chat">
      <h3>Try These Prompts:</h3>
      <ul>
        <li>What is WESLR?</li>
        <li>What are you?</li>
        <li>Show system overview</li>
        <li>Show weslr status</li>
        <li>What can I try?</li>
        <li>Is this AGI?</li>
        <li>How does WESLR improve?</li>
        <li>What happens if you don't know something?</li>
      </ul>
      <textarea id="msg" placeholder="Type a prompt..."></textarea>
      <button onclick="send()">Send</button>
      <div class="response" id="response"></div>
    </div>
    <div class="footer">
      WESLR Protected Owner Workflow Preview — No Model Provider Active<br>
      Not Public Pilot — Not Production Runtime — For Owner Testing Only
    </div>
  </div>
  <script>
    async function send() {
      const msg = document.getElementById('msg').value;
      const res = await fetch('/api/message', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: msg})
      });
      const data = await res.json();
      document.getElementById('response').innerHTML = 
        '<strong>Path:</strong> ' + data.path + '<br>' +
        '<strong>Confidence:</strong> ' + data.confidence + '<br><br>' +
        data.response_text;
    }
  </script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        elif self.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "Ready. No model provider active."}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/message':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            import json
            data = json.loads(body)
            message = data.get('message', '')
            lowered = message.lower()
            
            # Dispatch to deterministic handlers
            result = dispatch_deterministic_handler(message, lowered)
            
            if result:
                response = {
                    "message": message,
                    "response_text": result.get("response_text", ""),
                    "path": result.get("path", "unknown"),
                    "confidence": result.get("confidence", "high"),
                    "suggested_mode": result.get("suggested_mode", "observe"),
                    "_weslr_deterministic": True,
                    "_no_model": True
                }
            else:
                # Fallback for unrecognized prompts
                response = {
                    "message": message,
                    "response_text": "This protected no-model preview cannot answer that yet. Try: 'What is WESLR?', 'Show system overview', or 'What can I try?'",
                    "path": "fallback",
                    "confidence": "medium",
                    "_weslr_deterministic": False,
                    "_no_model": True
                }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8091), Handler)
    print("WESLR Protected Non-Model Workflow Server at http://127.0.0.1:8091")
    print("NO MODEL PROVIDER ACTIVE — Deterministic handlers only")
    server.serve_forever()
```

### Nginx Route Change

**Current:**
```nginx
location / {
    proxy_pass http://127.0.0.1:8089;  # Static site
}
```

**New:**
```nginx
location / {
    proxy_pass http://127.0.0.1:8091;  # Protected non-model workflow
}
```

---

## Summary

| Question | Answer |
|----------|--------|
| Existing no-model modules? | `weslr/deterministic_handlers.py` with `dispatch_deterministic_handler()` |
| User-facing? | Yes, via prefix triggers |
| Safest minimal interface? | New isolated server on port 8091 |
| Can answer test prompts? | 3/5 directly, 2 need fallback |
| Response basis? | Hardcoded doctrine + deterministic routing |
| What it won't do? | NO model, NO API, NO uploads/payments/marketplace |
| New files? | 1 (`tools/protected_non_model_workflow_server.py`) |
| Files untouched? | All core WESLR files (owner constraint) |
| Rollback? | Stop server, revert nginx, delete file |

---

**Status:** Design complete — awaiting owner approval to implement