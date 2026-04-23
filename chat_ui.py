from __future__ import annotations

import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
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
    .contamination-advisory { margin-top: 8px; padding: 8px 10px; border-radius: 8px; font-size: 13px; border: 1px solid transparent; }
    .contamination-advisory.high { background: #2a1a1a; border-color: #c0392b; }
    .contamination-advisory.medium { background: #2a2510; border-color: #d68910; }
    .contamin-icon { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
    .contamin-icon.high { background: #e74c3c; }
    .contamin-icon.medium { background: #f39c12; }
    .contamin-type { font-weight: 600; color: #e8eaed; }
    .contamin-reason { margin-top: 5px; color: #9aa0a6; }
    .contamin-expand { color: #4f8cff; cursor: pointer; font-size: 12px; }
    .contamin-signals { margin-top: 4px; font-size: 11px; color: #7f8c8d; display: none; }
    .lineage-advisory { margin-top: 8px; padding: 7px 10px; border-radius: 8px; font-size: 13px; border: 1px solid transparent; display: flex; align-items: center; gap: 6px; }
    .lineage-advisory.root { background: #1a2028; border-color: #2a3540; }
    .lineage-advisory.derived { background: #1a2028; border-color: #2a3540; }
    .lineage-advisory.legacy, .lineage-advisory.incomplete { background: #1e1e14; border-color: #4a4020; }
    .lineage-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
    .lineage-dot.root { background: #4f8cff; }
    .lineage-dot.derived { background: #4caf50; }
    .lineage-dot.legacy { background: #9aa0a6; }
    .lineage-dot.incomplete { background: #f39c12; }
    .lineage-label { color: #e8eaed; }
    .lineage-expand { color: #4f8cff; cursor: pointer; font-size: 12px; margin-left: 4px; }
    .lineage-notes { display: none; font-size: 11px; color: #9aa0a6; margin-top: 5px; }
    .advisory-secondary .contamin-reason { display: none; }
    .advisory-secondary .contamin-signals { display: none; }
    .advisory-secondary .lineage-notes { display: none; }
    .inspect-section { margin-top: 14px; background: #171a21; border: 1px solid #2a2f3a; border-radius: 12px; padding: 10px 12px; }
    .inspect-section summary { cursor: pointer; color: #9aa0a6; }
    .inspect-row { display: flex; gap: 8px; margin-top: 8px; align-items: center; }
    .inspect-input { flex: 1; border-radius: 8px; border: 1px solid #2a2f3a; background: #11141a; color: #fff; padding: 7px 10px; font-size: 13px; }
    .inspect-btn { border: 0; border-radius: 8px; padding: 7px 12px; background: #2d333b; color: #e8eaed; cursor: pointer; font-size: 13px; }
    .inspect-result { margin-top: 10px; font-size: 13px; color: #9aa0a6; }
    .inspect-field { margin-top: 5px; }
    .inspect-label { color: #6b7280; font-size: 11px; display: inline-block; width: 100px; }
    .inspect-value { color: #e8eaed; }
    .inspect-error { color: #e74c3c; }
    .inspect-ok { color: #4caf50; }
    .inspect-warn { color: #f39c12; }
    .inspect-current-btn { border: 0; border-radius: 8px; padding: 7px 12px; background: #2d333b; color: #e8eaed; cursor: pointer; font-size: 13px; margin-top: 8px; display: none; }
    .inspect-recent-btn { border: 0; border-radius: 8px; padding: 7px 12px; background: #2d333b; color: #e8eaed; cursor: pointer; font-size: 13px; margin-top: 6px; display: inline-block; }
    .inspect-recent-list { margin-top: 8px; max-height: 200px; overflow-y: auto; display: none; }
    .inspect-recent-item { padding: 5px 8px; border-radius: 6px; cursor: pointer; font-size: 12px; color: #9aa0a6; border-bottom: 1px solid #2a2f3a; }
    .inspect-recent-item:hover { background: #2a2f3a; color: #e8eaed; }
    .inspect-recent-meta { font-size: 11px; color: #6b7280; }
    .inspect-recent-status { display: inline-block; margin-left: 4px; }
    .inspect-recent-status.root { color: #4f8cff; }
    .inspect-recent-status.derived { color: #4caf50; }
    .inspect-recent-status.incomplete, .inspect-recent-status.legacy_unknown { color: #f39c12; }
    pre { white-space: pre-wrap; word-break: break-word; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>Weslr chat</h1>
    <div class=\"muted\">Conversation first. Technical details stay hidden unless you open them.</div>
    <div id=\"chat\"></div>
    <div class=\"row\">
      <textarea id=\"msg\" placeholder=\"Write to Weslr here...\"></textarea>
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
    <details class="inspect-section">
      <summary>Inspect artifact</summary>
      <div class="inspect-row">
        <input class="inspect-input" id="inspect-id" placeholder="art-..." />
        <button class="inspect-btn" id="inspect-go">Go</button>
      </div>
      <div class="inspect-result" id="inspect-result"></div>
      <button class="inspect-current-btn" id="inspect-current-btn">Inspect current artifact</button>
      <button class="inspect-recent-btn" id="inspect-recent-btn">Show recent artifacts</button>
      <div class="inspect-recent-list" id="inspect-recent-list"></div>
    </details>
  </div>
<script>
let chatLog = [];
const ADVISORY_PRIORITY = { contamination: 0, lineage: 1 };
function sortAdvisories(advisoryHtmls) {
  return advisoryHtmls.sort(function(a, b) {
    const pa = ADVISORY_PRIORITY[a.priorityKey] ?? 99;
    const pb = ADVISORY_PRIORITY[b.priorityKey] ?? 99;
    return pa - pb;
  });
}
function renderChat() {
  const el = document.getElementById('chat');
  if (!chatLog.length) {
    el.innerHTML = '<div class="msg bot"><div class="label">Weslr</div>Ready. Say something.</div>';
    return;
  }
  el.innerHTML = chatLog.map(item => {
    const advisoryHtmls = [];
    if (item.contamination) {
      const level = item.contamination.risk_level;
      if (level === 'high') {
        const typeLabel = item.contamination.type || 'Unknown';
        const reason = item.contamination.reason || '';
        const signals = (item.contamination.source_signals || []).map(s => '#' + s).join(' ');
        advisoryHtmls.push({ priorityKey: 'contamination', html: '<div class="contamination-advisory high"><span class="contamin-icon high"></span><span class="contamin-type">' + escapeHtml(typeLabel) + '</span><div class="contamin-reason">' + escapeHtml(reason) + '</div><span class="contamin-expand" onclick="this.style.display=\'none\';this.nextElementSibling.style.display=\'block\'">Show signals ▾</span><div class="contamin-signals">' + escapeHtml(signals) + '</div></div>' });
      } else if (level === 'medium') {
        const typeLabel = item.contamination.type || 'Unknown';
        advisoryHtmls.push({ priorityKey: 'contamination', html: '<div class="contamination-advisory medium"><span class="contamin-icon medium"></span><span class="contamin-type">' + escapeHtml(typeLabel) + '</span><span class="contamin-expand" onclick="this.parentElement.querySelector(\'.contamin-reason\').style.display=\'block\';this.style.display=\'none\'">Why? ▾</span><div class="contamin-reason" style="display:none">' + escapeHtml(item.contamination.reason || '') + '</div></div>' });
      }
    }
    if (item.lineage) {
      const ls = item.lineage.lineage_status || '';
      const notes = item.lineage.notes || '';
      let dotClass = 'legacy';
      let label = 'Lineage unknown';
      if (ls === 'root') {
        dotClass = 'root';
        label = 'Root artifact';
      } else if (ls === 'derived') {
        dotClass = 'derived';
        label = 'Based on previous artifact';
      } else if (ls === 'incomplete') {
        dotClass = 'incomplete';
        label = 'Lineage incomplete';
      } else if (ls === 'legacy_unknown') {
        dotClass = 'legacy';
        label = 'Older artifact';
      }
      advisoryHtmls.push({ priorityKey: 'lineage', html: '<div class="lineage-advisory ' + dotClass + '"><span class="lineage-dot ' + dotClass + '"></span><span class="lineage-label">' + escapeHtml(label) + '</span><span class="lineage-expand" onclick="this.style.display=\'none\';this.nextElementSibling.style.display=\'block\'">Details ▾</span><div class="lineage-notes">' + escapeHtml(notes) + '</div></div>' });
    }
    const sortedAdvisories = sortAdvisories(advisoryHtmls).slice(0, 2);
    const advisoryBlocks = sortedAdvisories.map(function(a, i) {
      if (i === 0) return a.html;
      // Secondary: wrap existing HTML in a div that applies minimal/collapsed styling
      return '<div class="advisory-secondary">' + a.html + '</div>';
    }).join('');
    return '<div class="msg ' + (item.role === 'user' ? 'me' : 'bot') + '">' +
      '<div class="label">' + (item.role === 'user' ? 'You' : 'Weslr') + '</div>' +
      escapeHtml(item.text) + advisoryBlocks + '</div>';
  }).join('');
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
      chatLog.push({role: 'assistant', text: data.reply, contamination: data._contamination_metadata || null, lineage: data._lineage_inspection || null});
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
  document.getElementById('status').textContent = 'Thinking...';
  const res = await fetch('/api/send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: msg}) });
  const data = await res.json();
  if (data.reply) chatLog.push({role: 'assistant', text: data.reply, contamination: data._contamination_metadata || null, lineage: data._lineage_inspection || null});
  document.getElementById('meta').textContent = data.meta || '';
  document.getElementById('status').textContent = data.status;
  renderChat();
}
document.getElementById('send').onclick = sendMessage;
document.getElementById('refresh').onclick = refreshState;
document.getElementById('msg').addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) sendMessage(); });
document.getElementById('inspect-go').onclick = async function() {
  const id = document.getElementById('inspect-id').value.trim();
  const el = document.getElementById('inspect-result');
  if (!id) { el.innerHTML = '<span class="inspect-error">Enter an artifact ID.</span>'; return; }
  el.innerHTML = '<span class="inspect-warn">Loading...</span>';
  try {
    const res = await fetch('/api/artifact_inspect', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({artifact_id: id}) });
    const data = await res.json();
    if (data.error) {
      el.innerHTML = '<span class="inspect-error">' + escapeHtml(data.error) + '</span>';
      return;
    }
    const li = data.lineage_inspection || {};
    const co = data.continuity || {};
    const statusColor = li.lineage_status === 'root' ? 'inspect-ok' : li.lineage_status === 'derived' ? 'inspect-ok' : li.lineage_status === 'incomplete' ? 'inspect-warn' : 'inspect-warn';
    const genLabel = li.generation !== null ? 'gen ' + li.generation : '—';
    const threadLabel = co.in_active_thread ? '<span class="inspect-ok">yes</span>' : '<span class="inspect-warn">no</span>';
    el.innerHTML = (
      '<div class="inspect-field"><span class="inspect-label">type</span><span class="inspect-value">' + escapeHtml(data.artifact.type || '—') + '</span></div>' +
      '<div class="inspect-field"><span class="inspect-label">created</span><span class="inspect-value">' + escapeHtml(data.artifact.created_at || '—') + '</span></div>' +
      '<div class="inspect-field"><span class="inspect-label">source</span><span class="inspect-value">' + escapeHtml(data.artifact.source || '—') + '</span></div>' +
      '<div class="inspect-field"><span class="inspect-label">lineage</span><span class="' + statusColor + '">' + escapeHtml(li.lineage_status || '—') + '</span></div>' +
      '<div class="inspect-field"><span class="inspect-label">generation</span><span class="inspect-value">' + genLabel + '</span></div>' +
      '<div class="inspect-field"><span class="inspect-label">root</span><span class="inspect-value">' + escapeHtml(li.root_artifact_id || '—') + '</span></div>' +
      '<div class="inspect-field"><span class="inspect-label">active thread</span>' + threadLabel + '</div>' +
      '<div class="inspect-field"><span class="inspect-label">notes</span><span class="inspect-value">' + escapeHtml(li.notes || '—') + '</span></div>'
    );
  } catch(e) {
    el.innerHTML = '<span class="inspect-error">Request failed.</span>';
  }
};
document.getElementById('inspect-current-btn').onclick = async function() {
  const el = document.getElementById('inspect-result');
  el.innerHTML = '<span class="inspect-warn">Loading...</span>';
  try {
    const res = await fetch('/api/current_artifact');
    const data = await res.json();
    if (!data.active_artifact_id) {
      el.innerHTML = '<span class="inspect-warn">No active artifact in continuity.</span>';
      document.getElementById('inspect-current-btn').style.display = 'none';
      return;
    }
    document.getElementById('inspect-id').value = data.active_artifact_id;
    document.getElementById('inspect-go').click();
  } catch(e) {
    el.innerHTML = '<span class="inspect-error">Request failed.</span>';
  }
};
document.getElementById('inspect-recent-btn').onclick = async function() {
  const listEl = document.getElementById('inspect-recent-list');
  const btn = document.getElementById('inspect-recent-btn');
  if (listEl.style.display === 'block') {
    listEl.style.display = 'none';
    btn.textContent = 'Show recent artifacts';
    return;
  }
  listEl.innerHTML = '<span class="inspect-warn">Loading...</span>';
  listEl.style.display = 'block';
  btn.textContent = 'Hide recent artifacts';
  try {
    const res = await fetch('/api/artifacts/recent');
    const data = await res.json();
    const artifacts = data.artifacts || [];
    if (!artifacts.length) {
      listEl.innerHTML = '<span class="inspect-warn">No artifacts found.</span>';
      return;
    }
    listEl.innerHTML = artifacts.map(function(a) {
      const id = escapeHtml(a.artifact_id || '');
      const created = escapeHtml((a.created_at || '').replace('T', ' ').slice(0, 16));
      const type = escapeHtml(a.type || '—');
      const status = a.lineage_status || 'unknown';
      const statusClass = ['root', 'derived', 'incomplete', 'legacy_unknown'].indexOf(status) === -1 ? '' : status;
      return '<div class="inspect-recent-item" onclick="document.getElementById(\'inspect-id\').value=\'' + id + '\';document.getElementById(\'inspect-go\').click();document.getElementById(\'inspect-recent-btn\').textContent=\'Show recent artifacts\';document.getElementById(\'inspect-recent-list\').style.display=\'none\';">' +
        '<div>' + id + '</div>' +
        '<div class="inspect-recent-meta">' + created + ' · ' + type + '<span class="inspect-recent-status ' + statusClass + '">' + (status === 'unknown' ? '' : ' · ' + status) + '</span></div>' +
        '</div>';
    }).join('');
  } catch(e) {
    listEl.innerHTML = '<span class="inspect-error">Failed to load.</span>';
  }
};
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


def weslr_speak_with_timing(message: str):
    """Get Weslr's response with latency timing for drift signal emission.

    Returns (response_text, duration_seconds, ok).
    """
    import time
    start = time.monotonic()
    ok = True
    try:
        response = run_weslr_cmd(["speak", "--message", message])
    except Exception:
        ok = False
        response = f"I'm Weslr. (Error: {e})" if "e" in dir() else "I'm Weslr."
    duration = time.monotonic() - start
    return response, duration, ok


def load_implementation_state() -> dict:
    if not IMPLEMENTATION_STATE_PATH.exists():
        return {}
    try:
        return json.loads(IMPLEMENTATION_STATE_PATH.read_text())
    except Exception:
        return {}


def save_implementation_state(payload: dict) -> None:
    IMPLEMENTATION_STATE_PATH.write_text(json.dumps(payload, indent=2))


def state_payload(contamination_metadata: dict = None) -> dict:
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
    payload = {"reply": reply or "...", "meta": json.dumps(meta, indent=2), "status": status}
    if contamination_metadata:
        payload["_contamination_metadata"] = contamination_metadata
    return payload


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


def get_current_active_artifact_id() -> Optional[str]:
    """Return the current active artifact ID using real continuity resolution.

    Uses the same thread-aware cascade that Weslr uses for real artifact
    resolution: active thread → registry fallback → None.
    """
    try:
        from weslr.timeline_resolution import resolve_active_artifact_for_user
        result = resolve_active_artifact_for_user("default")
        if result and result.get("resolved_artifact_id"):
            return result["resolved_artifact_id"]
        return None
    except Exception:
        return None


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
            lines.append(f"- {title} - {url}")
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
        if path == "/api/artifact_inspect":
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            req = json.loads(raw or "{}")
            artifact_id = str(req.get("artifact_id") or "").strip()
            if not artifact_id:
                self._json({"error": "artifact_id required"}, 400)
                return
            try:
                from weslr.artifact_store import get_artifact
                from weslr.lineage_inspector import inspect_artifact_lineage
                artifact = get_artifact(artifact_id)
                if artifact is None:
                    self._json({"error": "artifact_not_found"}, 404)
                    return
                # Core artifact data (read-only)
                artifact_out = {
                    "artifact_id": artifact.get("artifact_id"),
                    "type": artifact.get("type"),
                    "created_at": artifact.get("created_at"),
                    "source": artifact.get("source"),
                    "context": artifact.get("context", {}),
                }
                # Lineage inspection (read-only, reuses existing module)
                lineage_insp = inspect_artifact_lineage(artifact, thread_ids=artifact.get("thread_ids"))
                # Continuity: thread membership (read from artifact, no traversal)
                thread_ids = artifact.get("thread_ids") or []
                continuity = {
                    "in_active_thread": len(thread_ids) > 0,
                    "thread_ids": thread_ids,
                }
                self._json({
                    "artifact": artifact_out,
                    "lineage_inspection": lineage_insp.to_dict(),
                    "continuity": continuity,
                })
            except Exception as e:
                self._json({"error": str(e)}, 500)
            return
        if path == "/api/current_artifact":
            try:
                artifact_id = get_current_active_artifact_id()
                self._json({"active_artifact_id": artifact_id})
            except Exception as e:
                self._json({"active_artifact_id": None, "error": str(e)}, 500)
            return
        if path == "/api/artifacts/recent":
            try:
                from weslr.artifact_store import list_artifacts
                artifacts = list_artifacts(limit=20)
                # Return minimal safe fields + lineage status
                result = []
                for a in artifacts:
                    artifact_id = a.get("artifact_id")
                    if not artifact_id:
                        continue
                    # Get full artifact for lineage classification
                    try:
                        from weslr.artifact_store import get_artifact
                        full = get_artifact(artifact_id) or {}
                        from weslr.lineage_inspector import inspect_artifact_lineage
                        insp = inspect_artifact_lineage(full, thread_ids=full.get("thread_ids"))
                        lineage_status = insp.lineage_status
                    except Exception:
                        lineage_status = "unknown"
                    result.append({
                        "artifact_id": artifact_id,
                        "created_at": a.get("created_at"),
                        "type": a.get("type"),
                        "lineage_status": lineage_status,
                    })
                self._json({"artifacts": result})
            except Exception as e:
                self._json({"artifacts": [], "error": str(e)}, 500)
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
            contamination = None
            
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

            # Weslr capability commands (operator-only)
            elif message.lower().strip().startswith("capability"):
                query = message.lower().strip()
                # Parse capability command - extract subcommand and args
                # Format: "capability <subcommand> [--id <id>] [--query <q>] [--json]"
                # Also supports: "capability search query" (query after search)
                # For create: "capability create --title <t> --type <type> --summary <s> --why <w> --improvement <i>"
                parts = query.split()

                if len(parts) < 2:
                    immediate_reply = "Usage: capability <list|show|search|accept|deny|snooze|archive|stats>"
                else:
                    subcommand = parts[1]
                    capability_args = ["capability", subcommand]

                    # Handle simple formats for stats and list (no flags needed)
                    if subcommand in ["stats", "list"] and len(parts) == 2:
                        # "capability stats" or "capability list" - no args needed
                        pass
                    elif subcommand == "show" and len(parts) >= 3 and not parts[2].startswith("--"):
                        # "capability show <id>" - get id as next arg
                        capability_args.extend(["--id", parts[2]])
                    elif subcommand == "search" and len(parts) >= 3 and not parts[2].startswith("--"):
                        # "capability search query" - query is all parts after search
                        capability_args.extend(["--query", " ".join(parts[2:])])
                    elif subcommand in ["deny", "snooze", "archive"] and len(parts) >= 3 and not parts[2].startswith("--"):
                        # "capability deny <id> [hours]" or "capability <cmd> <id>"
                        capability_args.extend(["--id", parts[2]])
                        if len(parts) >= 4 and parts[3].isdigit():
                            capability_args.extend(["--hours", parts[3]])
                    elif subcommand == "accept" and len(parts) >= 3 and not parts[2].startswith("--"):
                        capability_args.extend(["--id", parts[2]])
                    elif subcommand == "create" and len(parts) >= 2:
                        # Create requires --flags, so just pass through
                        pass
                    # Additional argument parsing
                    elif "--query" in parts:
                        idx = parts.index("--query")
                        if idx + 1 < len(parts):
                            capability_args.extend(["--query", parts[idx + 1]])

                    # Handle other arguments
                    if "--id" in parts:
                        idx = parts.index("--id")
                        if idx + 1 < len(parts):
                            capability_args.extend(["--id", parts[idx + 1]])
                    if "--hours" in parts:
                        idx = parts.index("--hours")
                        if idx + 1 < len(parts):
                            capability_args.extend(["--hours", parts[idx + 1]])
                    if "--json" in parts:
                        capability_args.append("--json")
                    if "--limit" in parts:
                        idx = parts.index("--limit")
                        if idx + 1 < len(parts):
                            capability_args.extend(["--limit", parts[idx + 1]])
                    if "--offset" in parts:
                        idx = parts.index("--offset")
                        if idx + 1 < len(parts):
                            capability_args.extend(["--offset", parts[idx + 1]])
                    if "--title" in parts:
                        idx = parts.index("--title")
                        if idx + 1 < len(parts):
                            capability_args.extend(["--title", parts[idx + 1]])
                    if "--type" in parts:
                        idx = parts.index("--type")
                        if idx + 1 < len(parts):
                            capability_args.extend(["--type", parts[idx + 1]])
                    if "--summary" in parts:
                        idx = parts.index("--summary")
                        if idx + 1 < len(parts):
                            capability_args.extend(["--summary", parts[idx + 1]])
                    if "--why" in parts:
                        idx = parts.index("--why")
                        if idx + 1 < len(parts):
                            capability_args.extend(["--why", parts[idx + 1]])
                    if "--improvement" in parts:
                        idx = parts.index("--improvement")
                        if idx + 1 < len(parts):
                            capability_args.extend(["--improvement", parts[idx + 1]])
                    if "--confidence" in parts:
                        idx = parts.index("--confidence")
                        if idx + 1 < len(parts):
                            capability_args.extend(["--confidence", parts[idx + 1]])
                    if "--tags" in parts:
                        idx = parts.index("--tags")
                        # Get all remaining parts as tags
                        tags = parts[idx + 1:]
                        if tags:
                            capability_args.append("--tags")
                            capability_args.extend(tags)
                    try:
                        immediate_reply = run_weslr_cmd(capability_args)
                    except Exception as e:
                        immediate_reply = f"Error: {e}"
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
                immediate_reply = "Yes - if implementation is allowed, I should stop restating the plan and start applying one concrete fix."
            elif message_asks_for_code_suggestions(message):
                immediate_reply = synthesize_code_change_reply()

            # Default: use canonical dialogue pipeline (CONVERSATION_CANON_INTEGRATION_PHASE1)
            else:
                try:
                    from dialogue import handle_direct_message
                    canon_result = handle_direct_message(message)
                    immediate_reply = canon_result.get("reply", "")
                    status_note = canon_result.get("meta", "")
                    if status_note:
                        status_note = f" [{status_note}]"
                    # Extract contamination metadata for UI display (advisory only)
                    contamination = canon_result.get("_contamination_metadata")
                except Exception as e:
                    immediate_reply = f"I'm Weslr. (Error: {e})"
                    status_note = ""
                    contamination = None
                try:
                    run_cmd([PYTHON, "main.py", "human-exchange", "human", message, "--response", immediate_reply])
                except Exception:
                    pass

            # Capture observational signals from dialogue pipeline
            _lineage_insp = None
            _ctx_sel_v1 = None
            _boundary_hints = None
            try:
                if 'canon_result' in dir() and canon_result is not None:
                    _lineage_insp = canon_result.get("_lineage_inspection")
                    _ctx_sel_v1 = canon_result.get("_context_selection_v1")
                    _boundary_hints = canon_result.get("_boundary_hints")
            except Exception:
                pass

            # Final response
            data = state_payload(contamination_metadata=contamination)
            if requested_completion_notice and load_implementation_state().get("status") == "completed":
                data["reply"] = f"Finished: {load_implementation_state().get('summary') or load_implementation_state().get('task') or 'implementation step completed.'}"
            elif immediate_reply:
                data["reply"] = immediate_reply
            data["status"] = "Message processed."
            if _lineage_insp is not None:
                data["_lineage_inspection"] = _lineage_insp
            if _ctx_sel_v1 is not None:
                data["_context_selection_v1"] = _ctx_sel_v1
            if _boundary_hints is not None:
                data["_boundary_hints"] = _boundary_hints
            self._json(data)
        except Exception as e:
            self._json({"reply": str(e), "meta": "", "status": "Send failed."}, 500)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8081), Handler)
    print("Weslr chat at http://127.0.0.1:8081")
    server.serve_forever()
