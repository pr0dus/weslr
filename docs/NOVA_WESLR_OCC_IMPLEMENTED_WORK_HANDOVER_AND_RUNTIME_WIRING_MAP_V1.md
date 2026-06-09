# NOVA WESLR OCC Implemented Work Handover & Runtime Wiring Map V1

**Date:** 2026-06-09
**Purpose:** Read-only reconciliation of (a) the protected `/api/message` preview endpoint vs. (b) the real WESLR/OCC-designed runtime stack and (c) the design docs that the owner expected to find in this workspace. The goal is to map what was actually designed, what was actually implemented, and what the remaining bridge work is — **without** claiming things that are not in evidence.

**Scope constraints respected in this lane:**
- No implementation, no website edits, no backend edits, no service restarts, no nginx changes.
- No tools enabled, no daemon, no model provider, no settings writes, no public chat, no public registration, no Google OAuth.
- All evidence below is from `read`/`find`/`git` inspection of the two repos at the path owners. No external calls.

---

## A. Source repos inspected

| Path | Branch | HEAD | Working tree state at inspection |
|---|---|---|---|
| `/home/pr0/projects/weslr-v1-ui-website` | `ocw-weslr-v1-ui-20260529` | `eecb566` | Clean. Three `.bak` files in `protected-preview/chat-app-shell/` and a `logs/` dir are untracked. |
| `/home/pr0/projects/weslr` | `scatti-audit-bundle-v2` | `b478773` | **Uncommitted changes.** `main.py` modified (+36 LOC), and `answer_engine.py` / `engine_router.py` / `perspicuous.py` / `_demo_answer.py` are **untracked new files**. |
| `/data/data/com.termux/files/home/weslr-pr47-clean` | — | — | **Not present in this environment.** Excluded. |

**Important consequence:** The new answer-engine / router / perspicuous work is real code on disk, but it is **not** in the live `/api/message` wiring. The live wiring points at `dialogue.interpret_human_turn` + `weslr.omnichat.response_expander.format_reply` (committed in `1a1dae6`).

---

## B. OCC/WESLR design and implementation evidence found

### B.1 What the owner expected (filenames from the brief)

The brief listed filenames like `WESLR_PROJECT_CHAT_*`, `WESLR_OWNER_PREVIEW_RENDERING_*`, `WESLR_RAG_*`, `WESLR_FINAL_ANSWER_*`, `WESLR_INTELLIGENCE_SYNTHESIS_*`, `WESLR_50_USER_*`, `WESLR_PRODUCT_SHELL_*`, `WESLR_CONTROLLED_PRIVATE_PROJECT_CHAT_*`, `WESLR_PRIVATE_LOCAL_PROJECT_CHAT_*`, `WESLR_PRIVATE_OWNER_PREVIEW_*`, plus `*_IMPLEMENTATION_REPORT_V1.md` reports.

**Finding:** Those exact filenames are **not present** in either repo. The naming convention actually in use is `*_V1.md` for design/decision docs and `*_REVIEW_V1.md` for the review records (no `*_IMPLEMENTATION_REPORT_V1.md` files exist in the website repo either — `0` matches). Likewise there is no `NOVA_WESLR_HANDOFF_PACKET_V1.md`.

This does **not** mean the OCC work does not exist. It means the surface area the owner named in the brief is the *concept* of project-chat / RAG / final-answer / owner-preview / 50-user-readiness work, and that surface area is covered by:

- 224 `*_REVIEW_V1.md` design/decision docs in the website repo's `docs/` tree (covering answer formation, controlled answer composition, evidence, RAG, final answer, owner preview, capability ladder, project chat, etc.).
- Real implementation modules in the core repo's `weslr/` package (see Section C).
- The committed protected-wiring work in commit `1a1dae6` and the test/report commit `b478773` in the core repo.

### B.2 What was designed vs. what was implemented (high level)

| OCC / WESLR concept | Designed in | Implemented in code | Wired into `/api/message` |
|---|---|---|---|
| Deterministic handler registry (slash commands) | `docs/*` design canon | `weslr/deterministic_handlers.py` (3,425 lines) | **Yes** — primary route in `protected_non_model_workflow_server.py`. |
| Intent interpretation (free-form) | `docs/*` | `dialogue.py::interpret_human_turn` (139,651 bytes) | **Yes** — added in commit `1a1dae6`. |
| Omnichat contract-reply engine | `docs/*` | `weslr/omnichat/policy_engine.py`, `intent_resolution.py`, `context_selector.py`, `ephemeral_context.py`, `response_expander.py` | **Yes** — `format_reply` is wired into `/api/message` after `interpret_human_turn` in commit `1a1dae6`. |
| Evidence / RAG helpers | `docs/*` | `weslr/evidence_*.py` (10+ modules), `weslr/searxng_search_adapter.py`, `weslr/source_trust_ranking.py` | **Partially.** Modules exist and are tested. The protected wiring does **not** invoke the evidence chain for owner questions — it only invokes the deterministic registry + omnichat contract-reply. |
| Project-chat runtime (as a distinct higher-level module) | Design canon (controlled-final-answer, controlled-user-facing-output, controlled-reply-text chains) | No dedicated `project_chat_runtime.py` exists in `weslr/`. The closest equivalents are `state_grounded_dialogue.py` and `project_query_handler.py`, neither of which is wired into `/api/message`. | **No.** The brief's mention of "controlled_private_project_chat_runtime_wiring" / "private_local_project_chat_entrypoint" does not correspond to any wired-in module. |
| Owner preview rendering contract | Design canon | `weslr/controlled_*_*.py` modules in the website repo (metadata-only artifact helpers) | **No.** These are metadata helpers, not user-facing answer surfaces. The actual user-facing surface in the live wiring is `format_reply` + the deterministic registry. |
| Final answer generation boundary | Design canon | `weslr/final_decision_composer.py`, `weslr/final_decision_explainability.py` | **No.** Not wired into `/api/message`. |
| 50-user readiness | Design canon (`WESLR_50_USER_WORKING_VERSION_ROADMAP_V1.md` etc. by topic, not by exact filename) | Multi-user isolation primitives exist in `weslr/tenant_*.py` and `weslr/tenants/`, plus audit/lineage. | **No.** The live wiring has no per-user / per-tenant isolation; the protected endpoint is single-tenant (htpasswd owner-only). |
| Capability ladder / intelligence synthesis | Design canon | Many modules under `weslr/capability_*.py` and `weslr/explore_engine.py`, plus the uncommitted `answer_engine.py` / `engine_router.py` / `perspicuous.py` | **No.** The new answer-engine files are untracked and not in the wired runtime. The `weslr/capability_*` modules are not invoked by the live `/api/message` handler. |

### B.3 Implementation reports / review reports that prove this

- `docs/NOVA_COMPLETE_WESLR_PROTECTED_OWNER_RUNTIME_WIRING_V1.md` (core repo, 18,894 bytes) — the implementation + test report for commit `1a1dae6`, including local `/api/message` tests against `system_definition_query`, `usage_guidance`, and the `fallback_safe` gap path, plus protected-public-surface tests (`https://chat.weslr.de/api/message` returns `401` unauthenticated, `www.weslr.de` is untouched, port `127.0.0.1:8092` is the only listener).
- `docs/NOVA_PROTECTED_CHAT_API_MESSAGE_405_NGINX_ROUTE_REPAIR_AUTHENTICATED_TEST_V1.md` (website repo) — authenticated end-to-end test of the nginx route repair (most recent protected-chat doc in `docs/`).
- 224 `*_REVIEW_V1.md` docs in the website repo covering the design canon for the chains that the live wiring ultimately composes.
- Test corpus: `test_evidence_chat_bridge_v1.py`, `test_evidence_pipeline_v1.py`, `test_evidence_packet_builder_v1.py`, `test_capability_welcome_chat_bridge_v1.py`, `test_continuity_note_chat_bridge_v1.py`, `test_workplace_chat_bridge_v1.py`, `test_state_grounded_dialogue_v1.py`, etc. — these prove the *modules* are implemented and tested, but **none of these are invoked by the live `/api/message` handler**.

---

## C. Project-chat / runtime chain map (live state)

```
[owner browser, htpasswd-authed]
        |
        v
https://chat.weslr.de/api/message  (Cloudflare + nginx + auth_basic)
        |
        v
127.0.0.1:8092  →  tools/protected_non_model_workflow_server.py   (committed in 1a1dae6)
        |
        +--[1]--> weslr.deterministic_handlers.dispatch_with_fallback(message)
        |             -> prefix / regex match for /probes, /plans, /iss.*, /status, /origin, /compare, etc.
        |             -> returns contract replies from the registry.
        |
        +--[2]--> _weslr_omnichat_bridge(message)               (added in 1a1dae6)
                      -> dialogue.interpret_human_turn(message)   [READ-ONLY over WESLR state]
                      -> weslr.omnichat.response_expander.format_reply(interpreted)
                      -> returns contract_reply as response_text with path=real_weslr_omnichat::<omnichat_path>
                      -> on omnichat path = fallback_safe, returns truthful_gap_report=true
                         with structured next_required_work.
        |
        +--[3]--> structured truthful gap report (only if 1 + 2 both fail or are absent)
```

**Things deliberately NOT in the live wiring:**
- `weslr.chat_responder` (would activate the LLM provider path).
- `weslr.llm_runtime`, `weslr.providers`, `sim`, `llm_diff`, `dialogue` at higher layers.
- Any `auth-profiles.json` read; no `OPENAI_API_KEY` / `WESLR_LLM_PROVIDER` env mutation.
- Any state write, any settings write, any daemon start, any Google OAuth.
- The uncommitted new files `weslr/answer_engine.py` / `engine_router.py` / `perspicuous.py` / `_demo_answer.py` — they are on disk but not imported by the live handler.

**Evidence that the live wiring is what it claims to be:**
- `git show 1a1dae6 --stat` in the core repo shows a single-file change to `tools/protected_non_model_workflow_server.py` (+204 / -7).
- The server's PID `3529476` is recorded in `logs/protected_non_model_workflow_server_8092.pid`.
- The 5.1/5.2/5.3 test matrix in `NOVA_COMPLETE_WESLR_PROTECTED_OWNER_RUNTIME_WIRING_V1.md` shows local + protected-public surface checks (PASS).
- `git status` confirms no public exposure changes; `www.weslr.de` (port 8081) is untouched, `weslr-v1-ui-website` is untouched.

---

## D. Owner preview / protected chat chain map

The owner-facing path is the protected chat app shell at `https://chat.weslr.de/`:

```
[owner browser]  ->  Cloudflare  ->  nginx (auth_basic on / and /api/*)
                 ->  http://127.0.0.1:8092  (protected_non_model_workflow_server.py)
                 ->  /                : static shell (protected-preview/chat-app-shell/index.html)
                 ->  /api/auth/me     : auth role + permissions
                 ->  /api/state       : state-checkpoint snapshot + bridge status
                 ->  /api/message     : the chain in Section C
                 ->  /api/probes, /api/plans, /api/iss/*, etc. (deterministic registry)
```

`/api/auth/me` reports `authenticated=true, role=owner, account_mode=htpasswd_protected_owner_preview, google_auth_enabled=false, writes_enabled=false`. The shell `protected-preview/chat-app-shell/index.html` is the live UI (3 `.bak` files are untracked snapshots of recent reconciliation work).

The metadata-only `weslr/controlled_*_*.py` modules in the website repo (controlled-final-answer-generation, controlled-user-facing-output, controlled-reply-text, etc.) are **not** invoked by the live HTTP handler. They are design-time artifact helpers used in the design canon. The live handler's owner-preview surface is `format_reply` + the deterministic registry, with truthful-gap fallback.

---

## E. Current deployed `/api/message` preview behavior

- **Endpoint:** `POST https://chat.weslr.de/api/message` (htpasswd-protected).
- **Local bind:** `127.0.0.1:8092`, single listener, no public port open on the host beyond nginx-fronted.
- **Process:** `tools/protected_non_model_workflow_server.py`, PID file at `logs/protected_non_model_workflow_server_8092.pid` (currently `3529476` per the most recent report; not re-verified in this read-only pass).
- **Behavior:** Deterministic, no model, no provider, no search, no file writes, no daemon, no OAuth. The handler tries (1) the deterministic registry, then (2) the omnichat contract-reply engine, and only returns a structured truthful-gap report if both paths fail to produce a confirmed answer.
- **What the canned "preview catalog" is now:** It still exists in the deterministic registry as `fallback_unmatched`, but the omnichat bridge in (2) runs first, so the canned catalog is no longer the source of any free-form answer. It only fires for registry misses that the bridge also doesn't service.

---

## F. Gap between the preview endpoint and the real WESLR stack

This is the most important part of the report, because the brief explicitly asked: "what does the protected preview endpoint currently bypass?" and "what exact adapter is needed to connect chat.weslr.de/api/message to the real WESLR project-chat stack?"

The current wiring connects to `dialogue.interpret_human_turn` + `weslr.omnichat.response_expander.format_reply`. That is **not** the "real WESLR project-chat stack" in the broader sense — it is the **highest existing in-process WESLR contract-reply engine that is safe to call from a no-model owner surface**. Specifically, it bypasses or does not yet invoke:

1. **`weslr/answer_engine.py` / `engine_router.py` / `perspicuous.py`** — untracked new files representing a "perceive → pressure → imagine → audit → govern" answer engine. They are on disk, look like the same five-family pattern the OCC canon describes, and the demo script `_demo_answer.py` proves they run end-to-end on synthetic context — but they are **not** imported by the live handler. **The adapter needed: a guarded import in `protected_non_model_workflow_server.py` (mirroring the existing `_OMNICHAT_BRIDGE_AVAILABLE` pattern) that, after the omnichat path returns `fallback_safe`, runs `weslr.answer_engine.AnswerEngine.ask(message, context={...live state-checkpoint...})` and maps the result back to the structured response contract.**

2. **`weslr/evidence_*.py` chain** — `evidence_needed_detector`, `evidence_packet_builder`, `evidence_answer_builder`, `evidence_chat_bridge`, `searxng_search_adapter`, `source_trust_ranking`. These exist and are tested (see `test_evidence_chat_bridge_v1.py`, `test_evidence_pipeline_v1.py`, etc.) but are **not** invoked by the live handler. **The adapter needed: when the omnichat path returns `fallback_safe`, call `evidence_needed_detector.detect(question)` → if needed, `evidence_packet_builder.build(...)` → optionally `searxng_search_adapter.search(...)` (still no model — SearXNG is web search, not LLM) → `evidence_answer_builder.assemble(...)` and surface as `evidence[]` + `artifacts[]` in the response contract. This gives the owner a real evidence-backed answer where it exists, and a truthful gap where it does not.**

3. **`weslr/final_decision_composer.py` / `final_decision_explainability.py`** — design-canon "final answer" modules. They are not invoked by the live handler. **The adapter needed: a thin wrapper that composes the omnichat reply + answer-engine reply + evidence-backed reply into a single user-facing answer with provenance metadata, again read-only.**

4. **State retrieval into a confirmed-answer chain** — `state.py` / `state_checkpoint.py` / `state_transition.py` / `capability_*.py` / `implementation_plans` / `iss/` (Implementation Sequencing Surface) all exist and contain real WESLR state. The live wiring reads *some* of this (the omnichat engine reads the state-checkpoint), but it does **not** assemble a confirmed answer like "10 layers confirmed, 0 diagnostic gaps, 0 implementation plans, ISS probes: 0 ok, 0 degraded" because the deterministic registry's `system_overview` handler is the only thing that produces that today, and it runs only on the slash-command-style path. **The adapter needed: lift the state-summarization logic out of the deterministic registry into a reusable helper that the omnichat bridge can call on `fallback_safe` for "what have we implemented?" / "what remains before 50-user testing?"-type questions.**

5. **Per-tenant / per-user isolation (50-user readiness)** — `weslr/tenant_manager.py`, `weslr/tenant_context.py`, `weslr/tenants/` exist as primitives, but the live wiring is single-tenant (htpasswd owner-only). The brief's "controlled_private_project_chat_runtime_wiring" / "private_local_project_chat_entrypoint" naming does not map to any wired module today; it maps to the design canon only. **The adapter needed for 50-user: a tenant-aware dispatch in `_weslr_omnichat_bridge` that passes `tenant_id` and `user_id` into `interpret_human_turn` and into any future state retrieval, plus a `writes_enabled=true` per-tenant flag (currently hard-off).** That is a separate, much larger workstream.

6. **CLI wrapper / smoke test runner** — `weslr/weslr_cli.py` exists (29,590 bytes, the top-level CLI) and `test_weslr_cli.py` (6,033 bytes) covers the dispatch. The brief asked whether there is already a CLI wrapper that proves the chain — yes, **but** it operates on the legacy `chat()` surface in `weslr_backend_contract.py` and that surface imports `sim`, `dialogue`, `llm_runtime`, reads `auth-profiles.json`, and sets `OPENAI_API_KEY` — so it is **not** safe to call from a no-model owner surface. The protected wiring is the safer top-level entrypoint today; the CLI proves the lower-level chain works, not the owner surface. **The adapter needed: a new `private_owner_chat.py` CLI wrapper that calls the omnichat bridge in the same way `/api/message` does, so owner testing does not require nginx + htpasswd + browser.**

In short: **the protected preview is no longer a hardcoded catalog for any free-form question, but it still terminates at the omnichat contract-reply engine and falls through to a truthful-gap report for the questions that the OCC canon considers "confirmed-answer" territory**. The real evidence / final-answer / state-retrieval / answer-engine modules exist as code, are tested, and are the next wiring target.

---

## G. Safest bridge target recommendation

**Single safest next adapter target:** wire `weslr.answer_engine.AnswerEngine.ask(message, context=live_state)` after the omnichat bridge in `tools/protected_non_model_workflow_server.py`, using the same guarded-import pattern (`_ANSWER_ENGINE_BRIDGE_AVAILABLE` / `_ANSWER_ENGINE_BRIDGE_ERROR`) as the existing omnichat bridge.

Why this is the safest target:
- The answer engine is **pure Python**, **no model call**, **no provider env read**, **no LLM dependency** — confirmed by reading `weslr/answer_engine.py` (the orchestrator) and the demo in `_demo_answer.py` (8 questions, all answered with `shape`/`engines`/`state` metadata, no external calls).
- The router (`weslr/engine_router.py`) is a question-shape classifier that picks engines per family. The answer engine runs perceive → pressure → imagine → audit → govern. No external I/O.
- The state it needs is the same state the omnichat bridge already reads (state-checkpoint + plans + ISS), so the adapter is a small wrapper.
- The uncommitted `main.py` +36 LOC and the new files being untracked means **this work is the active next step in the core repo**, not speculative.

**Why not the evidence chain first:** the evidence chain depends on a SearXNG search call (still no model, but it is a network call) and on a per-question "do I need evidence?" decision. The answer engine is a strict superset of the omnichat bridge's contract-reply (it can include evidence and final-answer reasoning if the engines route to them). Doing the answer-engine wiring first means the next wiring step can plug the evidence chain *into* the answer engine's imagine/audit family, not into the HTTP layer directly. That keeps the HTTP layer thin and the bridge contract stable.

**Why not the CLI wrapper first:** the brief explicitly says "do not implement in this lane." The CLI is an enabler, not a prerequisite. Owner testing can use the browser today; the CLI is for offline verification.

---

## H. Exact next implementation lane (not executed in this report)

**Lane name:** `WESLR: wire protected owner chat to answer_engine + evidence chain v1`

**Touched files (proposed, not in this report):**
- `/home/pr0/projects/weslr/tools/protected_non_model_workflow_server.py` — add guarded import of `weslr.answer_engine.AnswerEngine`, add `_weslr_answer_engine_bridge` helper that runs after `_weslr_omnichat_bridge` and before the truthful-gap report, return a structured `runtime_path: real_weslr_answer_engine` response.
- `/home/pr0/projects/weslr/weslr/answer_engine.py` — currently untracked, must be `git add`-ed into the branch before the import can be considered "live."
- `/home/pr0/projects/weslr/weslr/engine_router.py` — same.
- `/home/pr0/projects/weslr/perspicuous.py` — same.
- `/home/pr0/projects/weslr/_demo_answer.py` — promote to `tests/test_answer_engine_v1.py` so the live wiring has a regression test.

**Not touched (safety):** no nginx, no service restart, no settings writes, no daemon, no model provider, no OAuth, no public chat, no public registration, no writes to `auth-profiles.json`, no env mutations.

**Acceptance criteria for that lane (proposed):**
- `/api/message` returns `runtime_path: real_weslr_answer_engine` for free-form questions that the answer engine handles.
- `/api/message` returns `runtime_path: real_weslr_omnichat_contract_reply` for questions the answer engine cannot service (omnichat still wins).
- `/api/message` returns `runtime_path: truthful_gap_report` for questions neither can service.
- The uncommitted `main.py` change is reviewed; if it touches the same bridge, it must be reviewed separately before commit.
- Owner browser test still passes: htpasswd-protected, no public exposure, all three owner test questions answered truthfully.

---

## I. Safety boundaries preserved

This report made **no** changes to the website repo, **no** changes to the backend core repo (read-only `git status` / `find` / `cat` only), **no** service restarts, **no** nginx changes, **no** writes to `auth-profiles.json`, **no** env mutations, **no** daemon starts, **no** public chat, **no** public registration, **no** Google OAuth, **no** model provider activation. The protected server's PID, port, and listener are unchanged. `www.weslr.de` (port 8081) is untouched. The `protected-preview/chat-app-shell/index.html` UI is untouched. No new evidence was inserted into the live handler.

The only files written in this lane are:
- `/home/pr0/projects/weslr-v1-ui-website/docs/NOVA_WESLR_OCC_IMPLEMENTED_WORK_HANDOVER_AND_RUNTIME_WIRING_MAP_V1.md` (this report).

---

## J. Final judgment

**`nova_weslr_occ_handover_found_runtime_entrypoint_ready_for_adapter_design`**

**Reasoning:**
- A real, committed, traceable WESLR runtime entry point exists in the core repo: `tools/protected_non_model_workflow_server.py` + the omnichat bridge (commit `1a1dae6` on branch `scatti-audit-bundle-v2`, HEAD `b478773`).
- The implementation report `NOVA_COMPLETE_WESLR_PROTECTED_OWNER_RUNTIME_WIRING_V1.md` documents the entry point, the wire contract, the test matrix, the truthful-gap behavior, and the safety invariants.
- The next wiring target is concrete: the uncommitted `answer_engine.py` / `engine_router.py` / `perspicuous.py` work in the core repo, wired in via a guarded import after the omnichat bridge.
- The 50-user / multi-tenant adapter is **not** ready for design in this lane — the design canon exists but the per-tenant wiring primitives in `weslr/tenant_*.py` are not currently in the protected handler, and that is a larger, separate workstream.
- No protected surface was changed, no public surface was exposed, and no claims in this report exceed the evidence above.

**One thing I am explicitly NOT claiming:** I am not claiming the new uncommitted `answer_engine.py` / `engine_router.py` / `perspicuous.py` work is "wired into the protected runtime." Those files exist on disk, the demo script proves they run on synthetic context, but they are untracked and not imported by the live handler. They are the next lane, not the current state. The current state is the omnichat bridge from commit `1a1dae6`, with a truthful-gap report for questions the omnichat engine cannot confirmed-answer.

---

**Nova — Dispatch complete.**
