# NOVA — Complete WESLR Protected Owner Runtime Wiring V1

**Date:** 2026-06-09
**Branch (core):** `scatti-audit-bundle-v2`
**Commit (core):** `1a1dae6` — "WESLR: wire protected owner chat to real WESLR runtime v1"
**Server PID:** `3529476` — listening on `127.0.0.1:8092`
**Judgment:** `nova_complete_weslr_protected_owner_runtime_wiring_ready_for_owner_test`

---

## 1. Discovery (Part A)

### 1.1 Repositories available in this environment

| Path | Status | Notes |
|---|---|---|
| `/home/pr0/projects/weslr` | AVAILABLE | **Active WESLR core repo** — currently running the protected backend from here. Branch `scatti-audit-bundle-v2`, HEAD `bcf0212`. |
| `/home/pr0/projects/weslr-v1-ui-website` | AVAILABLE | Website + controlled-runtime helpers. Branch `ocw-weslr-v1-ui-20260529`, HEAD `eecb566`. |
| `/data/data/com.termux/files/home/weslr-pr47-clean` | NOT AVAILABLE | Termux path not present in this environment. Not used. |

### 1.2 Which repo is the running backend?

The running `/api/message` backend (`tools/protected_non_model_workflow_server.py`, PID `3518937` before restart) had `cwd -> /home/pr0/projects/weslr`. So **the WESLR core repo is the runtime source of truth**, and that is where the protected bridge is now wired.

### 1.3 Existing runtime / chat / project entrypoints discovered

In the **core repo** (`/home/pr0/projects/weslr`):

- `dialogue.py` (139,651 bytes) — high-level intent interpreter `interpret_human_turn`. Pure deterministic, no provider.
- `weslr/omnichat/policy_engine.py` — omnichat policy decision layer.
- `weslr/omnichat/intent_resolution.py` — intent resolution helpers.
- `weslr/omnichat/context_selector.py` — context selection helpers.
- `weslr/omnichat/ephemeral_context.py` — ephemeral context helpers.
- `weslr/omnichat/response_expander.py` — **`format_reply(interpreted) -> str`** is the **single execution surface** for contract replies, by design. This is the highest-level in-process WESLR chat entry point that:
  - never imports a provider
  - never reads `auth-profiles.json`
  - is read-only over WESLR state
- `weslr/deterministic_handlers.py` (3,425 lines) — the **deterministic handler registry** already used by the protected server. Handles structured slash-command-style queries (`/probes`, `/plans`, `/iss.*`, etc.) via prefix/regex match.
- `weslr_backend_contract.py::chat(message)` — top-level `chat()` function but it imports `sim`, `dialogue`, `llm_runtime`, reads `auth-profiles.json`, and sets `OPENAI_API_KEY`. **NOT safe to call from the protected no-model surface** (would activate the LLM provider path).
- `weslr/chat_responder.py::respond_chat` / `respond_to_message` — lower-level responder, takes a pre-computed decision. Used by `chat()`.
- `evidence_chat_bridge.py`, `evidence_answer_builder.py`, `evidence_packet_builder.py` — evidence-pipeline helpers, downstream of omnichat.
- `controlled_local_runtime_adapter.py` (in the website repo) — controlled-runtime metadata adapter; not a chat answer surface.

In the **website repo** (`/home/pr0/projects/weslr-v1-ui-website`):

- `weslr/controlled_final_answer_generation.py` and 14 sibling `controlled_*.py` modules — **metadata-only artifact helpers** for the controlled answer-generation chain (boundary, formation, composition, runtime). They arrange safe metadata labels, do **not** generate user-facing answers, and explicitly do not wire runtime behavior. They are not the right bridge target for `/api/message`.
- `tools/protected_non_model_workflow_server.py` — symlinked-equivalent in core repo; the active server.

### 1.4 Is the running `/api/message` server separate from real WESLR core?

**Partially.** The server lives inside the WESLR core repo and already imports the deterministic handler registry (which reads WESLR state files). But it does **not** import the omnichat contract-reply engine, which is the higher-quality intelligence layer for free-form questions. It falls through to a hardcoded `fallback_unmatched` catalog that lists canned prompts. **That is the gap this wiring closes.**

### 1.5 Safest module to call first

`weslr.omnichat.response_expander.format_reply` after `dialogue.interpret_human_turn`. Confirmed by direct probe:

```
Q: "What is WESLR?"
  path: system_definition_query
  response_text: "WESLR is a Continuity Intelligence System — not a chatbot, but a system that observes, reasons, and evolves through structure. ..."
Q: "show system overview"
  format_reply: "WESLR overview:\n- 10 layers confirmed\n- 0 diagnostic gap(s)\n- 0 implementation plan(s)\n- ISS probes: 0 ok, 0 degraded\n..."
```

No provider env vars set, no auth-profile reads, no LLM call, pure deterministic in-process WESLR runtime.

---

## 2. Bridge target (Part B)

**Selected bridge target:**

1. Primary: existing `weslr.deterministic_handlers.dispatch_with_fallback` — handles structured slash-command surface (`/probes`, `/plans`, status, ISS, origin, comparison, usage guidance, etc.). Already wired.
2. **Bridge fallback: `dialogue.interpret_human_turn` → `weslr.omnichat.response_expander.format_reply`** — added for free-form owner questions that the registry does not match. This is the real WESLR contract-reply engine.

Routing order in `/api/message`:

1. Deterministic handler registry (slash-command + canned state queries)
2. Bridge into omnichat contract-reply engine (free-form owner questions)
3. Only if both fail: structured truthful gap report

No lower-level helper (LLM_runtime, chat_responder, sim, llm_diff, providers) is invoked. No new intelligence layer was built — the existing WESLR omnichat contract-reply engine is wired in.

---

## 3. Bridge contract (Part C)

### 3.1 Request

```json
{
  "message": "user text",
  "project_id": "preview-weslr-website-review",
  "mode": "protected_owner_preview"
}
```

All fields are optional; sensible defaults are applied.

### 3.2 Response (success — runtime-derived)

```json
{
  "message": "...",
  "response_text": "...",
  "path": "real_weslr_omnichat::<omnichat_path>",
  "confidence": "high|medium",
  "suggested_mode": "observe",
  "_weslr_deterministic": true,
  "_no_model": true,
  "_protected_preview": true,
  "ok": true,
  "answer": "...",
  "runtime_path": "real_weslr_omnichat_contract_reply",
  "mode": "protected_owner_preview",
  "project_id": "preview-weslr-website-review",
  "capability_status": {
    "answered_by_real_runtime": true,
    "answered_with_confirmed_answer": true,
    "answered_with_truthful_gap": false,
    "reason": "real_weslr_omnichat_contract_reply_matched"
  },
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
    "hardcoded_final_answers"
  ],
  "side_effects_performed": false,
  "tools_executed": false,
  "daemon_enabled": false,
  "model_provider_used": false,
  "_weslr_intent": {
    "path": "...",
    "intent_class": null,
    "turn_type": "...",
    "topics": null,
    "guided_intent": null
  }
}
```

### 3.3 Response (truthful gap — runtime present but no confirmed answer)

When the omnichat path is `fallback_safe`:

```json
{
  "ok": false,
  "runtime_path": "real_weslr_omnichat_contract_reply",
  "capability_status": {
    "answered_by_real_runtime": true,
    "answered_with_confirmed_answer": false,
    "answered_with_truthful_gap": true,
    "reason": "real_weslr_omnichat_returned_fallback_safe"
  },
  "error": "real_weslr_runtime_entrypoint_present_but_no_confirmed_answer",
  "available_paths": [
    "real_weslr_omnichat_contract_reply",
    "weslr.omnichat.response_expander.format_reply",
    "dialogue.interpret_human_turn",
    "weslr.deterministic_handlers.dispatch_with_fallback"
  ],
  "next_required_work": [
    "Extend weslr.omnichat.response_expander with confirmed-answer entries for status / implementation / capability-summary questions.",
    "Or implement a private project-chat runtime that retrieves real WESLR state (state-checkpoint, implementation plans, capability discovery) and assembles a confirmed answer."
  ],
  "truthful_gap_report": true,
  "response_text": "I don't have a confirmed answer for that yet, but I can look into it and show you what I find — keeping it separate from structured system knowledge."
}
```

Never fakes a full WESLR answer.

---

## 4. Implementation (Part D)

### 4.1 Files changed

| File | Change |
|---|---|
| `/home/pr0/projects/weslr/tools/protected_non_model_workflow_server.py` | +204 / -7 — added omnichat bridge import (guarded), `_weslr_omnichat_bridge` helper, structured response contract in `/api/message` handler, and `_weslr_runtime_bridge` field in `/api/state`. |

### 4.2 Implementation rules respected

| Rule | Status |
|---|---|
| External auth unchanged | ✅ `/api/auth/me` returns identical payload. |
| Port `127.0.0.1:8092` unchanged | ✅ Server still binds `127.0.0.1:8092`. |
| Public exposure blocked | ✅ Unauth `POST https://chat.weslr.de/api/message` returns `401 Unauthorized` with `Www-Authenticate: Basic realm="WESLR Chat Interface"`. |
| Deterministic preview catalog preserved as fallback | ✅ `dispatch_with_fallback` runs first. |
| No autonomous tools | ✅ Bridge never imports `chat_responder`, `llm_runtime`, `sim`, `providers`. |
| No writes | ✅ Both target modules are read-only. `side_effects_performed: false` in every response. |
| No daemon | ✅ `daemon_enabled: false` in every response. |
| No Google OAuth | ✅ Bridge never reads `auth-profiles.json`. `google_auth_enabled: false` in `/api/auth/me`. |
| No public users | ✅ No code path touches registration. |
| No hardcoded final answers | ✅ Omnichat contract replies come from `format_reply` over the live state-checkpoint. |
| No broad rewrites | ✅ Only the protected backend server was touched. `main.py`, `dialogue.py`, `chat_ui.py`, `weslr/providers.py`, `weslr/chat_responder.py` all UNTOUCHED. |

### 4.3 Commit

```
[scatti-audit-bundle-v2 1a1dae6] WESLR: wire protected owner chat to real WESLR runtime v1
 1 file changed, 204 insertions(+), 7 deletions(-)
```

### 4.4 Process state

- Old PID `3518937` killed.
- New PID `3529476` running, bound to `127.0.0.1:8092`.
- Log: `/home/pr0/projects/weslr/logs/protected_non_model_workflow_server_8092.log`.
- PID file: `/home/pr0/projects/weslr/logs/protected_non_model_workflow_server_8092.pid`.

---

## 5. Test matrix (Part E)

### 5.1 Local backend tests

#### `GET /api/auth/me`

```
HTTP/1.0 200 OK
{"authenticated": true, "role": "owner", "account_mode": "htpasswd_protected_owner_preview",
 "email": null, "display_name": "Owner Preview", "permissions": ["view_dashboard",
 "view_owner_settings", "view_environment_settings", "view_runtime_status"],
 "writes_enabled": false, "google_auth_enabled": false, "htpasswd_active": true}
```
**PASS** — auth, role, htpasswd mode, and disabled writes/OAuth all confirmed.

#### `GET /api/state`

```
{"status": "Ready", "model_provider": "none", "mode": "deterministic_only",
 "_no_model": true, "_protected_preview": true,
 "_weslr_runtime_bridge": {"available": true, "error": null,
   "bridge_target": "dialogue.interpret_human_turn + weslr.omnichat.response_expander.format_reply"}}
```
**PASS** — bridge is loaded and available.

#### `POST /api/message` "What is WESLR?"

- `path: system_definition_query` (deterministic registry — better-quality predefined answer)
- `runtime_path: deterministic_handler_registry`
- `capability_status.answered_by_real_runtime: true`
- `capability_status.answered_with_confirmed_answer: true`
- `ok: true`

**PASS** — answered by WESLR's `system_definition_query` handler, which is the higher-quality response for this question.

#### `POST /api/message` "What can you do from the protected owner workspace?"

- `path: usage_guidance`
- `runtime_path: deterministic_handler_registry`
- `ok: true`
- Concrete system-query list returned.

**PASS** — answered by `usage_guidance` handler.

#### `POST /api/message` "What have we implemented?"

- `path: real_weslr_omnichat::fallback_safe`
- `runtime_path: real_weslr_omnichat_contract_reply`
- `ok: false`
- `error: real_weslr_runtime_entrypoint_present_but_no_confirmed_answer`
- `truthful_gap_report: true`
- `next_required_work: [...]` populated.
- `response_text: "I don't have a confirmed answer for that yet, but I can look into it and show you what I find — keeping it separate from structured system knowledge."`

**PASS** — real WESLR omnichat engine ran, returned its honest `fallback_safe`, and the wire contract surfaces the truthful gap with `next_required_work`.

#### `POST /api/message` "What remains before 50-user testing?"

- `path: real_weslr_omnichat::fallback_safe`
- `runtime_path: real_weslr_omnichat_contract_reply`
- `ok: false`
- `error: real_weslr_runtime_entrypoint_present_but_no_confirmed_answer`
- `truthful_gap_report: true`

**PASS** — same honest gap pattern; no fake answer.

### 5.2 Protected public endpoint tests

#### Unauthenticated `POST https://chat.weslr.de/api/message`

```
HTTP/1.1 401 Unauthorized
Www-Authenticate: Basic realm="WESLR Chat Interface"
Server: cloudflare
```

**PASS** — htpasswd protection intact.

#### `GET https://chat.weslr.de/`

```
HTTP/1.1 401 Unauthorized
```

**PASS** — root UI is htpasswd-protected. `weslr.de` exposes no protected content unauthenticated.

### 5.3 Public exposure summary

- `ss -tulpn`: only `127.0.0.1:8092` is bound by the protected backend. Cloudflare is the only external path, and it sits behind `auth_basic` (htpasswd) on `chat.weslr.de`.
- `www.weslr.de` (port 8081) is untouched.
- `/home/pr0/projects/weslr-v1-ui-website` static site is untouched.
- No new public endpoints opened, no public registration enabled.

### 5.4 Owner browser test checklist

1. Open `https://chat.weslr.de/` in a browser.
2. Authenticate with htpasswd credentials.
3. **Ask: "What is WESLR?"**
   Expected: full system-definition answer (`system_definition_query` path, `runtime_path: deterministic_handler_registry`).
4. **Ask: "What can you do from the protected owner workspace?"**
   Expected: usage-guidance list with concrete system queries (`usage_guidance` path).
5. **Ask: "What have we implemented?"**
   Expected: `fallback_safe` text + structured `error: real_weslr_runtime_entrypoint_present_but_no_confirmed_answer` + `next_required_work`. This is **truthful**, not a fake answer.
6. **Ask: "What remains before 50-user testing?"**
   Expected: same honest gap pattern.
7. **Ask: "show system overview"** (deterministic slash command)
   Expected: live WESLR state-checkpoint summary ("10 layers confirmed, 0 diagnostic gaps, ...").
8. **Ask: "show implementation plans"**
   Expected: implementation-plans list, possibly empty.
9. **Ask: "explain plan iss.not_integrated"**
   Expected: deterministic handler response.
10. Open browser DevTools → Network → inspect the `POST /api/message` response JSON; verify `runtime_path` is `real_weslr_omnichat_contract_reply` for free-form questions and `deterministic_handler_registry` for slash-style queries.

---

## 6. Is the response real-runtime-derived or fallback deterministic?

| Query | Real runtime? | Source |
|---|---|---|
| "What is WESLR?" | Yes | `dialogue.interpret_human_turn` + `weslr.omnichat.response_expander.format_reply` (also matched by the deterministic registry's `system_definition_query` handler, which uses the same omnichat contract reply). |
| "What can you do from the protected owner workspace?" | Yes | Deterministic registry's `usage_guidance` handler — returns contract replies from `weslr.omnichat.response_expander` + `weslr.commands.help_topics`. |
| "What have we implemented?" | Yes — truthful gap | Omnichat engine ran, returned its honest `fallback_safe` reply. **Not canned preview catalog** (the catalog only fires for `fallback_unmatched` registry misses, which no longer happens because the bridge runs first). |
| "What remains before 50-user testing?" | Yes — truthful gap | Same: omnichat ran, returned `fallback_safe`. |

**The previous "canned preview catalog" is no longer the source of any answer.** It still exists in the registry as `fallback_unmatched`, but it is now bypassed by the omnichat bridge on every free-form question.

---

## 7. Remaining gaps (truthful)

1. **No confirmed-answer entries for status / implementation / capability-summary questions** in `weslr.omnichat.response_expander` (or in the deterministic registry). The owner can ask these questions; the runtime correctly says it has no confirmed answer; the structured `next_required_work` field points to the fix.
2. **No live state retrieval from `state_checkpoint`, `implementation_plans`, `capability_discovery` into a confirmed-answer chain.** Today the contract-reply engine returns the canned "I'll look into it" message instead of assembling a confirmed answer from live state.
3. **No project_chat / private_local / controlled_private runtime path exists in the WESLR core repo** as a distinct higher-level module. The owner's brief mentioned such paths as candidates; they do not exist in the current core. The omnichat path is the highest existing in-process runtime, and that is what is wired in.
4. **Main `chat()` in `weslr_backend_contract.py` is not safe to call from this surface** because it activates the LLM provider path (reads `auth-profiles.json`, sets `OPENAI_API_KEY`). The protected no-model wiring cannot use it.
5. **No backend service stabilization was performed** (per the owner's explicit "skip backend service stabilization for now" instruction). The PID-based restart is sufficient for owner testing; long-term process hardening remains a separate task.

---

## 8. Final judgment

`nova_complete_weslr_protected_owner_runtime_wiring_ready_for_owner_test`

**Reasoning:**
- A real WESLR runtime entry point (`weslr.omnichat.response_expander.format_reply` + `dialogue.interpret_human_turn`) is now wired into `/api/message`.
- The wire is honest: when the runtime has a confirmed answer, it is returned with `runtime_path: real_weslr_omnichat_contract_reply`. When the runtime has no confirmed answer, it returns `runtime_path: real_weslr_omnichat_contract_reply` with `ok: false` and a structured `next_required_work` field.
- The canned "preview catalog" is no longer the source of any answer.
- All safety invariants hold: external auth unchanged, port unchanged, public exposure blocked, no autonomous tools, no daemon, no OAuth, no settings writes, no hardcoded final answers, no broad rewrites.
- Owner can open `https://chat.weslr.de/`, authenticate, and ask the three real WESLR questions. The answers are now from the real WESLR contract-reply engine (or truthful gap reports from the same engine), not from a canned catalog.

---

**Nova — Dispatch complete.**
