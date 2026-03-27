from __future__ import annotations

import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable
IMPLEMENTATION_STATE_PATH = BASE_DIR / "implementation_state.json"

HTML = """<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Weslr Chat</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; background: #0f1115; color: #e8eaed; }
    .wrap { max-width: 920px; margin: 0 auto; padding: 20px; }
    h1 { font-size: 22px; margin: 0 0 8px; }
    .muted { color: #9aa0a6; font-size: 14px; }
    #chat { margin-top: 16px; background: #171a21; border: 1px solid #2a2f3a; border-radius: 14px; padding: 14px; min-height: 420px; display: flex; flex-direction: column; gap: 10px; }
    .msg { display: inline-block; width: fit-content; max-width: min(75%, 680px); padding: 10px 12px; border-radius: 12px; white-space: pre-wrap; }
    .me { background: #1e2a3a; align-self: flex-end; }
    .bot { background: #1b2a1f; align-self: flex-start; }
    .label { font-size: 12px; color: #9aa0a6; margin-bottom: 4px; }
    .row { display: flex; gap: 10px; margin-top: 14px; }
    textarea { flex: 1; min-height: 88px; border-radius: 10px; border: 1px solid #2a2f3a; background: #11141a; color: #fff; padding: 12px; }
    button { border: 0; border-radius: 10px; padding: 12px 16px; background: #4f8cff; color: white; cursor: pointer; }
    button.secondary { background: #2d333b; }
    .status { margin-top: 10px; color: #9aa0a6; font-size: 14px; }
    details { margin-top: 14px; background: #171a21; border: 1px solid #2a2f3a; border-radius: 12px; padding: 10px 12px; }
    pre { white-space: pre-wrap; word-break: break-word; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>Weslr chat</h1>
    <div class=\"muted\">Conversation first. Technical details stay hidden unless you open them.</div>
    <div id=\"chat\"></div>
    <div class=\"row\">
      <textarea id=\"msg\" placeholder=\"Write to Weslr here…\"></textarea>
    </div>
    <div class=\"row\">
      <button id=\"send\">Send</button>
      <button id=\"refresh\" class=\"secondary\">Refresh reply</button>
    </div>
    <div class=\"status\" id=\"status\"></div>
    <details>
      <summary>Show technical details</summary>
      <pre id=\"meta\"></pre>
    </details>
  </div>
<script>
let chatLog = [];
function renderChat() {
  const el = document.getElementById('chat');
  if (!chatLog.length) {
    el.innerHTML = '<div class="msg bot"><div class="label">Weslr</div>Ready. Say something.</div>';
    return;
  }
  el.innerHTML = chatLog.map(item => `
    <div class="msg ${item.role === 'user' ? 'me' : 'bot'}">
      <div class="label">${item.role === 'user' ? 'You' : 'Weslr'}</div>
      ${escapeHtml(item.text)}
    </div>
  `).join('');
  el.scrollTop = el.scrollHeight;
}
function escapeHtml(text) {
  return String(text).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
}
async function refreshState() {
  const res = await fetch('/api/state');
  const data = await res.json();
  if (data.reply) {
    const last = chatLog[chatLog.length - 1];
    if (!last || last.role !== 'assistant' || last.text !== data.reply) {
      chatLog.push({role: 'assistant', text: data.reply});
    }
  }
  document.getElementById('meta').textContent = data.meta;
  document.getElementById('status').textContent = data.status;
  renderChat();
}
async function sendMessage() {
  const msg = document.getElementById('msg').value.trim();
  if (!msg) return;
  chatLog.push({role: 'user', text: msg});
  renderChat();
  document.getElementById('msg').value = '';
  document.getElementById('status').textContent = 'Thinking…';
  const res = await fetch('/api/send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: msg}) });
  const data = await res.json();
  if (data.reply) chatLog.push({role: 'assistant', text: data.reply});
  document.getElementById('meta').textContent = data.meta || '';
  document.getElementById('status').textContent = data.status;
  renderChat();
}
document.getElementById('send').onclick = sendMessage;
document.getElementById('refresh').onclick = refreshState;
document.getElementById('msg').addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) sendMessage(); });
renderChat();
refreshState();
</script>
</body>
</html>
"""


def run_cmd(args: list[str]) -> str:
    proc = subprocess.run(args, cwd=BASE_DIR, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip())
    return proc.stdout.strip()


def run_weslr_cmd(args: list[str]) -> str:
    """Run a Weslr CLI command and return output."""
    weslr_path = BASE_DIR / "weslr_main.py"
    proc = subprocess.run([PYTHON, str(weslr_path)] + args, cwd=BASE_DIR, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip())
    return proc.stdout.strip()


def weslr_speak(message: str) -> str:
    """Get Weslr's response to a message."""
    try:
        return run_weslr_cmd(["speak", "--message", message])
    except Exception as e:
        return f"I'm Weslr. (Error: {e})"


def load_implementation_state() -> dict:
    if not IMPLEMENTATION_STATE_PATH.exists():
        return {}
    try:
        return json.loads(IMPLEMENTATION_STATE_PATH.read_text())
    except Exception:
        return {}


def save_implementation_state(payload: dict) -> None:
    IMPLEMENTATION_STATE_PATH.write_text(json.dumps(payload, indent=2))


def state_payload() -> dict:
    # Use Weslr for response
    try:
        reply = run_weslr_cmd(["speak", "--message", ""])
        if reply.startswith("Weslr: "):
            reply = reply[7:]  # Remove "Weslr: " prefix
        if not reply.strip():
            reply = "I'm Weslr, an entity intelligence system. I'm working on consciousness signatures and entity graphs. What would you like to talk about?"
    except Exception as e:
        reply = f"I'm Weslr. (Error: {e})"
    
    # Get relationships and implementation state for metadata
    try:
        raw = run_cmd([PYTHON, "main.py", "communicator-self"])
        parsed = json.loads(raw)
        relationships = parsed.get("relationships") or {}
    except Exception:
        relationships = {}
    
    implementation = load_implementation_state()
    if implementation.get("status") == "completed" and not implementation.get("announced"):
        reply = f"Finished: {implementation.get('summary') or implementation.get('task') or 'implementation step completed.'}"
        if implementation.get("continuation_note_created"):
            reply += " Continuation note saved."
        implementation["announced"] = True
        save_implementation_state(implementation)
    
    # Get Weslr stats for metadata
    try:
        weslr_entities = run_weslr_cmd(["entity-list", "--limit", "3", "--json"])
        weslr_stats = run_weslr_cmd(["entity-stats", "--json"])
    except Exception:
        weslr_entities = "N/A"
        weslr_stats = "N/A"
    
    meta = {
        "known_humans": relationships.get("known_humans") or [],
        "threads": list((relationships.get("conversation_threads") or {}).keys()),
        "last_human_topic": relationships.get("last_human_topic") or "",
        "implementation": implementation,
        "weslr": {
            "entities_preview": weslr_entities,
            "stats": weslr_stats
        }
    }
    status = "Ready."
    if implementation.get("status") == "running":
        status = "Implementation step running."
    elif implementation.get("status") == "completed":
        status = "Implementation step completed."
    return {"reply": reply or "...", "meta": json.dumps(meta, indent=2), "status": status}


def should_search_web(message: str) -> bool:
    lowered = str(message or "").strip().lower()
    return any(token in lowered for token in ["search online", "search the web", "look online", "look it up", "search web"])


def extract_search_query(message: str) -> str:
    original = str(message or "").strip()
    lowered = original.lower()
    if any(token in lowered for token in ["understand each other", "understand me", "real communication", "what do you need"]):
        return "dialogue systems mutual understanding user corrections conversational repair theory of mind"
    if any(token in lowered for token in ["suggest code", "coding", "implement", "changed in your coding"]):
        return "conversational agents mutual understanding retrieval grounding user correction handling dialogue repair implementation"
    query = original
    for phrase in ["search online for", "search the web for", "look online for", "search web for", "look it up for"]:
        if phrase in query.lower():
            idx = query.lower().index(phrase)
            query = query[idx + len(phrase):].strip(" .,:;!?-")
            break
    return query or original


def message_asks_for_code_suggestions(message: str) -> bool:
    lowered = str(message or "").lower()
    return any(token in lowered for token in [
        "suggest code",
        "coding",
        "changed in your coding",
        "what needs to be changed",
        "needs to be changed",
        "change in your coding",
    ])


def message_asks_can_implement(message: str) -> bool:
    lowered = str(message or "").strip().lower().rstrip(" .!?")
    return any(token in lowered for token in ["can you implement", "will you implement", "could you implement"])


def message_is_control_approval(message: str) -> bool:
    lowered = str(message or "").strip().lower().rstrip(" .!?")
    if lowered in {"ok go", "okay go", "go then", "do it", "go ahead", "yes go", "you are allowed to implement them", "so you are allowed to implement them"}:
        return True
    return any(pattern in lowered for pattern in [
        "you're allowed",
        "you are allowed",
        "allowed to change",
        "allowed to add",
        "allowed to implement",
        "go ahead and implement",
    ])


def message_starts_execution(message: str) -> bool:
    lowered = str(message or "").strip().lower()
    return any(pattern in lowered for pattern in [
        "implement suggested actions",
        "go for coding",
        "start implementing",
        "start coding",
        "apply the changes",
    ])


def message_requests_completion_notice(message: str) -> bool:
    lowered = str(message or "").strip().lower()
    return any(pattern in lowered for pattern in [
        "tell me when finished",
        "tell me when you're finished",
        "tell me when done",
        "let me know when finished",
        "let me know when done",
        "notify me when finished",
    ])


def start_implementation_worker() -> None:
    state = load_implementation_state()
    if state.get("status") == "running":
        return
    save_implementation_state({
        "status": "queued",
        "started_at": 0,
        "finished_at": 0,
        "announced": False,
        "task": "add direct answer for actual coding prompts",
        "summary": "",
    })
    subprocess.Popen([PYTHON, "implementation_worker.py"], cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def synthesize_code_change_reply() -> str:
    return (
        "The code changes I should implement next are: "
        "(1) stronger query rewriting so messy human requests turn into cleaner research intents, "
        "(2) multi-step handling so search requests also produce synthesis and concrete next actions, "
        "(3) instruction-vs-topic separation so imperatives do not become memory threads, "
        "(4) better reply grounding in user corrections and conversational repair, and "
        "(5) direct answer synthesis after retrieval so I stop narrating thread state when you asked for practical guidance."
    )


def summarize_search_reply(query: str, raw_result: str, message: str = "") -> str:
    try:
        parsed = json.loads(raw_result)
    except Exception:
        parsed = {}
    results = list(parsed.get("results") or [])[:3]
    if not results:
        return f"I searched for {query}, but I didn't get usable results yet."
    if message_asks_for_code_suggestions(message):
        top_links = "; ".join(str(item.get("url") or item.get("title") or "").strip() for item in results[:2] if str(item.get("url") or item.get("title") or "").strip())
        return f"{synthesize_code_change_reply()} Best leads: {top_links}"
    if any(token in str(message or "").lower() for token in ["understand each other", "understand me", "real communication", "what do you need"]):
        top_links = "; ".join(str(item.get("url") or item.get("title") or "").strip() for item in results[:2] if str(item.get("url") or item.get("title") or "").strip())
        return (
            "I searched for ways to improve mutual understanding. What you should give me when I drift is: "
            "what mattered most, what I misunderstood, what you actually meant, and what kind of answer you wanted. "
            "What I should improve in code is retrieval relevance, conversational repair, and better handling of corrections and vague references. "
            f"Best leads: {top_links}"
        )
    lines = [f"I searched for {query}. Best leads:"]
    for item in results:
        title = str(item.get("title") or item.get("url") or "result").strip()
        url = str(item.get("url") or "").strip()
        if url:
            lines.append(f"- {title} — {url}")
        else:
            lines.append(f"- {title}")
    lines.append("From here, the practical next step is to read the strongest result and turn it into concrete communication guidance instead of generic self-report.")
    return "\n".join(lines)


class Handler(BaseHTTPRequestHandler):
    def _json(self, payload: dict, code: int = 200):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def _html(self, text: str):
        body = text.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._html(HTML)
            return
        if path == "/api/state":
            try:
                self._json(state_payload())
            except Exception as e:
                self._json({"reply": str(e), "meta": "", "status": "State read failed."}, 500)
            return
        self.send_error(404)
    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/send":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        payload = json.loads(raw or "{}")
        message = str(payload.get("message") or "").strip()
        if not message:
            self._json({"reply": "", "meta": "", "status": "Nothing sent."}, 400)
            return
        try:
            immediate_reply = ""
            requested_completion_notice = message_requests_completion_notice(message)
            
            # Web search
            if should_search_web(message):
                query = extract_search_query(message)
                search_result = run_cmd([PYTHON, "main.py", "search-web", query, "--limit", "5"])
                immediate_reply = summarize_search_reply(query, search_result, message)
                bridged_message = (
                    f"{message}\n\n"
                    f"Web search results for: {query}\n"
                    f"{search_result[:4000]}\n\n"
                    f"Use these results to answer directly and practically."
                )
                run_cmd([PYTHON, "main.py", "human-exchange", "human", bridged_message, "--response", immediate_reply])
            
            # Weslr entity commands
            elif message.lower().strip().startswith("entity"):
                query = message.lower().strip()
                if "list" in query or "stats" in query:
                    immediate_reply = run_weslr_cmd(["entity-list", "--limit", "5"])
                elif "details" in query:
                    immediate_reply = run_weslr_cmd(["entity-stats"])
                else:
                    immediate_reply = run_weslr_cmd(["entity-list", "--limit", "3"])
                run_cmd([PYTHON, "main.py", "human-exchange", "human", message, "--response", immediate_reply])
            
            # Control messages (no Weslr response needed)
            elif message_requests_completion_notice(message):
                immediate_reply = "Understood. I should report back when the current implementation step is finished."
            elif message_starts_execution(message):
                start_implementation_worker()
                immediate_reply = "Understood. I am starting one concrete implementation step now."
            elif message_is_control_approval(message):
                immediate_reply = "Understood. I should continue with the approved next step."
            elif message_asks_can_implement(message):
                immediate_reply = "Yes — if implementation is allowed, I should stop restating the plan and start applying one concrete fix."
            elif message_asks_for_code_suggestions(message):
                immediate_reply = synthesize_code_change_reply()
            
            # Default: Weslr as primary responder
            else:
                immediate_reply = weslr_speak(message)
                try:
                    run_cmd([PYTHON, "main.py", "human-exchange", "human", message, "--response", immediate_reply])
                except Exception:
                    pass
            
            # Final response
            data = state_payload()
            if requested_completion_notice and load_implementation_state().get("status") == "completed":
                data["reply"] = f"Finished: {load_implementation_state().get('summary') or load_implementation_state().get('task') or 'implementation step completed.'}"
            elif immediate_reply:
                data["reply"] = immediate_reply
            data["status"] = "Message processed."
            self._json(data)
        except Exception as e:
            self._json({"reply": str(e), "meta": "", "status": "Send failed."}, 500)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8790), Handler)
    print("Weslr chat at http://127.0.0.1:8790")
    server.serve_forever()
