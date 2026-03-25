from __future__ import annotations

import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable

HTML = """<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>CircleForge Chat</title>
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
    <h1>CircleForge chat</h1>
    <div class=\"muted\">Conversation first. Technical details stay hidden unless you open them.</div>
    <div id=\"chat\"></div>
    <div class=\"row\">
      <textarea id=\"msg\" placeholder=\"Write to CircleForge here…\"></textarea>
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
    el.innerHTML = '<div class="msg bot"><div class="label">CircleForge</div>Ready. Say something.</div>';
    return;
  }
  el.innerHTML = chatLog.map(item => `
    <div class="msg ${item.role === 'user' ? 'me' : 'bot'}">
      <div class="label">${item.role === 'user' ? 'You' : 'CircleForge'}</div>
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


def state_payload() -> dict:
    reply = run_cmd([PYTHON, "main.py", "speak"])
    raw = run_cmd([PYTHON, "main.py", "communicator-self"])
    parsed = json.loads(raw)
    relationships = parsed.get("relationships") or {}
    meta = {
        "known_humans": relationships.get("known_humans") or [],
        "threads": list((relationships.get("conversation_threads") or {}).keys()),
        "last_human_topic": relationships.get("last_human_topic") or "",
    }
    return {"reply": reply or "...", "meta": json.dumps(meta, indent=2), "status": "Ready."}


def should_search_web(message: str) -> bool:
    lowered = str(message or "").strip().lower()
    return any(token in lowered for token in ["search online", "search the web", "look online", "look it up", "search web"])


def extract_search_query(message: str) -> str:
    lowered = str(message or "").strip()
    query = lowered
    for phrase in ["search online for", "search the web for", "look online for", "search web for", "look it up for"]:
        if phrase in query.lower():
            idx = query.lower().index(phrase)
            query = query[idx + len(phrase):].strip(" .,:;!?-")
            break
    return query or lowered


def summarize_search_reply(query: str, raw_result: str) -> str:
    try:
        parsed = json.loads(raw_result)
    except Exception:
        parsed = {}
    results = list(parsed.get("results") or [])[:3]
    if not results:
        return f"I searched for {query}, but I didn't get usable results yet."
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
            if should_search_web(message):
                query = extract_search_query(message)
                search_result = run_cmd([PYTHON, "main.py", "search-web", query, "--limit", "5"])
                immediate_reply = summarize_search_reply(query, search_result)
                bridged_message = (
                    f"{message}\n\n"
                    f"Web search results for: {query}\n"
                    f"{search_result[:4000]}\n\n"
                    f"Use these results to answer directly and practically."
                )
                run_cmd([PYTHON, "main.py", "human-exchange", "human", bridged_message, "--response", immediate_reply])
            else:
                run_cmd([PYTHON, "main.py", "human-exchange", "human", message])
            run_cmd([PYTHON, "main.py", "run", "--ticks", "12", "--interval", "0"])
            data = state_payload()
            if immediate_reply:
                data["reply"] = immediate_reply
            data["status"] = "Message processed."
            self._json(data)
        except Exception as e:
            self._json({"reply": str(e), "meta": "", "status": "Send failed."}, 500)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8790), Handler)
    print("CircleForge chat at http://127.0.0.1:8790")
    server.serve_forever()
