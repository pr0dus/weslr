# SYSTEM_SCHEMATIC_AND_CAPABILITY_MAP_V1
**Version:** 1.0 — 2026-04-16
**Branch:** `weslr/canonical-clean-signals`
**Status:** Canonical

---

## PURPOSE

A complete architectural map of WESLR as it exists today: what each layer does, where data lives, how pieces connect, and what exists vs. what is still missing.

This document is the single source of truth for understanding the system layout. All future work must reference this map before adding new modules or surfaces.

---

## SECTION 1 — WHAT IS WESLR?

WESLR is an **entity intelligence platform with governed self-assessment and institutional continuity**.

It is not a chatbot. It maintains a persistent identity across sessions, tracks its own drift, enforces governance contracts, manages operator relationships over time, and exposes machine-readable state so satellite UIs can interact with it.

**Core properties:**
- Governed: it can propose changes to itself, but the operator approves or denies
- Self-assessing: it continuously monitors latency, bootstrap state, governance quality, and drift
- Institution-aware: it understands roles, timelines, and trust levels
- Continuously alive: it persists state to disk between restarts
- Multi-surface: canonical runtime serves HTTP; satellite UIs connect over LAN or tailnet

---

## SECTION 2 — LAYERED ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         WESLR — CANONICAL RUNTIME                            │
│                   python3 main.py serve :: port 8080                          │
│                      (ThreadingHTTPServer)                                     │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌───────────────────────────┼────────────────────────────────────┐
         │                           │                                     │
         ▼                           ▼                                     ▼
  ┌──────────────┐          ┌───────────────┐                  ┌──────────────┐
  │ HTTP ROUTES  │          │  CLI COMMANDS │                  │ PROVIDER     │
  │ ChatHandler  │          │ cmd_serve     │                  │ LAYER        │
  │ (main.py)    │          │ cmd_weslr_state               │ llm_runtime  │
  └──────┬───────┘          └───────────────┘                  └──────┬───────┘
         │                                                        │
         │  All HTTP endpoints are defined here                     │ Model calls
         │  ThreadPoolExecutor (max_workers=1) gates /chat          │
         │  Semaphore(4) further limits concurrent chats            ▼
         ▼                                                   ┌──────────────┐
┌─────────────────────────────────────────────────────┐       │  LLM         │
│                   OPERATOR LAYER (Layer 1)          │       │  PROVIDERS   │
│  operator_profile.json  ←  POST /onboarding          │       │              │
│  communicator_self.json ←  tick/clock, bootstrap     │       │ ollama       │
│  session_state.json     ←  session_continuity.py    │       │ openai       │
│  .weslr_initialized     ←  POST /api/initialize     │       │ anthropic    │
│                                                     │       │ embedded     │
│  Lifecycle states:                                  │       │ fallback     │
│    bootstrap_required → establishing → established  │       └──────────────┘
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│                 ROLE LAYER (Layer 2)                │
│  institution.py                                      │
│                                                     │
│  - RoleTimeline schema (role_id, institution_id,    │
│    current_occupant, role_owner, clearance_level)    │
│  - RoleStatus: ACTIVE / VACANT / ARCHIVED           │
│  - Deny-by-default: humans must be authorized       │
│  - NOT YET: vacancy replacement, delegation chains  │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              GOVERNANCE + SECURITY LAYER            │
│                                                     │
│  security.py              SS-TDE trust + clearance  │
│    TrustLevel enum        CONVERSATIONAL→CRITICAL   │
│    ClearanceToken         time-bounded, action-scoped│
│    verified_completion()   enforcement entry point   │
│    audit log              all HIGH_RISK events      │
│                                                     │
│  drift_emitter.py         Fail-open signal emission │
│    emit_latency_signal()                           │
│    emit_bootstrap_signal()                         │
│    emit_override_signal()                           │
│    emit_counterproposed_signal()                    │
│    emit_ignored_signal()                            │
│    emit_snoozed_signal()                            │
│    emit_reflection_signal()                         │
│    All wrapped in try/except Exception: pass         │
│                                                     │
│  change_proposals.py     ExecutionGate + proposals  │
│    ExecutionGate.review_proposal()                  │
│    create / approve / deny / counterpropose         │
│    _record_drift() fail-open                        │
│                                                     │
│  governance_health.py    Self-assessment surface    │
│    get_weslr_state_summary() → 10-key dict         │
│    _get_trust_posture()   bootstrap truth (durable) │
│    _get_health_posture()  reflection, signal health │
│    _get_continuity_posture()                        │
│    _get_institutional_posture()                     │
│    _get_drift_posture()                             │
│                                                     │
│  execution_telemetry.py   Rolling signal window     │
│    _DRIFT_WINDOW_SECS = 172800 (48h)               │
│    _MAX_SIGNALS = 1000                              │
│    _REFLECTIONS = []                                │
│    drift signals + reflection storage              │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│               MEMORY + CONTINUITY LAYER             │
│                                                     │
│  sim.py                   Main memory engine        │
│    MemoryLayer            layered memory (episodic, │
│                           working, procedural,      │
│                           semantic)                 │
│    identity_core          persistent identity dict  │
│    communicator_self      lifecycle + continuity     │
│    continuity_anchors     timeline stability anchors│
│    perform_tick()         increments session_count   │
│    record_human_exchange()                         │
│                                                     │
│  communicator_config.py  Operator profile + config  │
│    load_operator_profile()                          │
│    update_operator_profile()                        │
│    derive_lifecycle_state() → bootstrap_required /  │
│                              establishing /         │
│                              established           │
│                                                     │
│  bootstrap.py             Bootstrap lifecycle       │
│    new_pending_bootstrap()                         │
│    complete_bootstrap()  → writes to communicator_   │
│                            self.json (durable!)     │
│    timeline_id            persistent human ID        │
│    _BOOTSTRAP_BY_TIMELINE (in-process, per-runtime)│
│                                                     │
│  session_continuity.py    Per-session transport state│
│    session_id, session_count, session_history       │
│    (legacy — use communicator_self for truth)       │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│                   SELF-MODEL LAYER                  │
│                                                     │
│  SOUL.md                   Identity contract        │
│  IDENTITY.md               Who WESLR is              │
│  USER.md                   Operator preferences      │
│  AGENTS.md                 Workspace conventions      │
│  HEARTBEAT.md              Periodic task checklist   │
│                                                     │
│  weslr/self_model.py       Self-improvement engine   │
│    create_proposal()                                │
│    list_proposals()                                 │
│    approve_proposal() / deny_proposal()             │
│    apply_proposal()                                 │
└─────────────────────────────────────────────────────┘
```

---

## SECTION 3 — HTTP ENDPOINTS (Canonical Runtime)

All endpoints are served by `ChatHandler` in `main.py` via `python3 main.py serve`.

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/` | GET | Open | Front door HTML |
| `/onboarding` | GET | Open | HTML onboarding form |
| `/onboarding` | POST | Open | Record answers + attempt auto-initialize |
| `/operator` | GET | Open | HTML operator dashboard |
| `/chat` | POST | SS-TDE L3 | Main conversational interface |
| `/api/state` | GET | Open | Full self-summary (10 keys) |
| `/api/first-run` | GET | Open | `{first_run, profile_exists, initialized}` |
| `/api/onboarding` | GET | Open | Lifecycle + profile + `initialized` flag |
| `POST /api/initialize` | POST | Open | Contract-gated init marker creation |
| `/api/clearance/verify` | POST | Open | SS-TDE token issuance |
| `/artifact-review` | POST | Open | Governance artifact review |
| `/category/update` | POST | Open | Category management |
| `/pack/decision` | POST | Open | Pack outcome recording |
| `/api/health` | GET | Open | **MISSING** — should return `{healthy, uptime_s, version}` |

### Initialization Contract (for `/api/initialize` and onboarding auto-init)

All 4 conditions must pass:

1. **Operator profile name exists** — `profile.name` is non-empty
2. **Lifecycle state ≠ `bootstrap_required`** — `derive_lifecycle_state()` returns a state other than `bootstrap_required`
3. **State summary works** — `get_weslr_state_summary()` returns without fatal error
4. **Bootstrap timeline exists** — `communicator_self.json` → `bootstrap.timeline_id` is non-empty

If all pass → `.weslr_initialized` marker created (idempotent: no-op if already exists).
If any fail → blocked with `reasons: [...]`, onboarding still succeeds independently.

---

## SECTION 4 — CLI COMMANDS

| Command | File | Purpose |
|---|---|---|
| `python3 main.py serve` | main.py | Canonical HTTP server (port 8080) |
| `python3 main.py weslr-state` | main.py | Human-readable self-summary |
| `python3 -m weslr bootstrap` | weslr/bootstrap.py | Bootstrap subcommands |
| `capability archive <id>` | commands/capability.py | Archive governance proposal |
| `capability snooze <id>` | commands/capability.py | Snooze governance proposal |

---

## SECTION 5 — DATA PERSISTENCE MAP

| File | What it stores | Durable? |
|---|---|---|
| `communicator_self.json` | Identity core, continuity state, **bootstrap.timeline_id + status**, lifecycle | **YES** — JSON file |
| `operator_profile.json` | Onboarding answers (name, role, preferences, adaptation level, etc.) | **YES** |
| `session_state.json` | Per-session transport state (session_count, sessions list) | **YES** |
| `session_history.json` | Historical session log | **YES** |
| `.weslr_initialized` | Marker file created when initialization contract is satisfied | **YES** |
| `_DRIFT_SIGNALS` | In-process rolling window of drift signals | **NO** — lost on restart |
| `_REFLECTIONS` | In-process reflection storage | **NO** — lost on restart |
| `_BOOTSTRAP_RECORDS` | Per-process bootstrap records | **NO** — not persisted |
| `_BOOTSTRAP_BY_TIMELINE` | Per-process completed bootstrap index | **NO** — not persisted |
| `world.db` | SQLite concept graph | **YES** |
| `*.json` (artifacts) | Governance artifacts, proposals, audit events | **YES** |

**Key invariant:** Bootstrap truth for HTTP-layer checks must come from `communicator_self.json` (durable), NOT from in-process memory.

---

## SECTION 6 — MODULE CAPABILITY INVENTORY

| Module | Canonical? | Purpose |
|---|---|---|
| `main.py` | ✅ | HTTP server, routes, CLI entry |
| `llm_runtime.py` | ✅ | Provider abstraction (5 modes) |
| `sim.py` | ✅ | Memory engine, identity, tick/clock |
| `communicator_config.py` | ✅ | Profile, lifecycle derivation |
| `bootstrap.py` | ✅ | Bootstrap lifecycle, timeline_id |
| `security.py` | ✅ | SS-TDE trust levels, clearance tokens |
| `institution.py` | ✅ | Role timelines, Layer 2 governance |
| `governance_health.py` | ✅ | Self-assessment summary surface |
| `change_proposals.py` | ✅ | ExecutionGate, proposal lifecycle |
| `drift_emitter.py` | ✅ | Fail-open signal emitters |
| `execution_telemetry.py` | ✅ | Rolling signal window |
| `pilot_signal_logger.py` | ✅ | Operator signal logger |
| `weslr_main.py` | ⚠️ legacy | Old CLI entry, mostly superseded |
| `session_continuity.py` | ⚠️ legacy | Per-session state, use with caution |
| `chat_ui.py` | ❌ | Standalone shell, NOT the canonical server |

---

## SECTION 7 — EXECUTION FLOW: `/chat` Request

```
HTTP POST /chat
    │
    ▼
ChatHandler.do_POST()
    │
    ├─ Validate content-length, parse JSON
    │
    ├─ Extract: message, session_id, actor_id, trust_level
    │
    ├─ Semaphore.acquire()  ← limits to 4 concurrent
    │
    ├─ _CHAT_EXECUTOR.submit()
    │       │
    │       ├─ classify_action("chat:message") → CONVERSATIONAL (L0)
    │       │       OR HIGH_RISK (L3) if trust_level is absent
    │       │
    │       ├─ If L3: verified_completion() → SS-TDE token check
    │       │       └─ fail → 403 response
    │       │
    │       ├─ Build communicator_message via sim.build_communicator_message()
    │       │
    │       ├─ Provider call: llm_runtime.generate_chat()
    │       │
    │       ├─ Emit drift signals (fail-open, all wrapped in try/except)
    │       │
    │       └─ Return: {ok, message, topics, unresolved}
    │
    ├─ Semaphore.release()
    │
    ▼
HTTP 200 { ... } or 403/500
```

---

## SECTION 8 — BOOTSTRAP + INITIALIZATION FLOW

```
Operator completes onboarding
    │
    ▼
POST /onboarding
    │
    ├─ record_human_exchange(phase="onboarding", ...)
    │
    ├─ update_operator_profile(answers)
    │       └─ writes operator_profile.json
    │
    ├─ [NEW] Attempt initialize
    │       ├─ Check: profile.name exists ✅
    │       ├─ Check: lifecycle != bootstrap_required
    │       │       └─ reads communicator_self.continuity.session_count
    │       ├─ Check: get_weslr_state_summary() works ✅
    │       └─ Check: communicator_self.bootstrap.timeline_id exists
    │               └─ Bootstrap must be COMPLETED first!
    │
    ├─ If all pass: write .weslr_initialized marker
    │
    └─ Response: {ok, recorded, initialization: {initialized, created_now, blocked, reasons}}
```

Bootstrap completion is a **separate step** from onboarding. The operator must complete bootstrap (trusted device + secret words) before `POST /api/initialize` or the auto-init in `/onboarding` will pass.

---

## SECTION 9 — TRUST LEVELS (SS-TDE)

| Level | Name | Requirement | Used for |
|---|---|---|---|
| L0 | CONVERSATIONAL | None | Normal chat |
| L1 | SENSITIVE | Contextual acknowledgment | Preferences, profile updates |
| L2 | ELEVATED | Explicit in-session confirmation | Message send, document share |
| L3 | HIGH_RISK | Trusted device + challenge/response + time-bounded token | Delete, external API calls |
| L4 | CRITICAL | Multi-party verification + audit | Database wipe, revoke all |

---

## SECTION 10 — LIFECYCLE STATES

Derived by `derive_lifecycle_state()` in `communicator_config.py`:

| State | Condition |
|---|---|
| `bootstrap_required` | No profile name, or `session_count ≤ 2` |
| `establishing` | `session_count 3–14` |
| `established` | `session_count ≥ 15` OR `memory_bonds ≥ 0.5` OR `unfinished ≥ 3` |

Lifecycle state is stored in `communicator_self.json` → `continuity.lifecycle_state` and recalculated on each read.

---

## SECTION 11 — DEPLOYMENT TOPOLOGIES

### Single-machine (current)
```
localhost:8080
```
Operator and WESLR on same machine. All endpoints open to local processes.

### Home/server mode (recommended for Pi)
```
python3 main.py serve --host 0.0.0.0 --port 8080
systemd: weslr.service (not yet written)
tailscale: expose via gateway.remote.url
```
WESLR on Pi, operator accesses over LAN. Satellite UIs on other machines connect via `http://pi:8080`.

### LAN multi-device mode
```
Pi runs WESLR at 192.168.1.x:8080
Phone/laptop run thin HTTP clients
Operator dashboard: http://192.168.1.x:8080/operator
Chat: POST http://192.168.1.x:8080/chat
State: GET http://192.168.1.x:8080/api/state
```

### Future satellite mode
```
WESLR brain (Pi) ──HTTPS──> Satellite UIs (phone, laptop, watch)
                              │
                              └─ Thin HTTP clients, no WESLR code needed
```

---

## SECTION 12 — MISSING PIECES (Known Gaps)

| Gap | Priority | Notes |
|---|---|---|
| `GET /api/health` endpoint | High | Uptime + version for monitoring |
| systemd unit file | High | Auto-restart, log management |
| State backup/restore | Medium | USB/NAS backup of JSON files |
| `init-operator` / `init-bootstrap` CLI | Medium | Guided first-run setup |
| `session_count` → `interaction_count` rename | Low | Maintainability only, no runtime bug |
| Trusted device UI/flow | Medium | SS-TDE L3 requires this for full security |
| Vacancy replacement workflow | Low | Layer 3 institution feature |
| Satellite UI kit | Low | Thin HTTP client reference impl |

---

## SECTION 13 — CURRENT BRANCH + COMMIT STATE

**Branch:** `weslr/canonical-clean-signals`
**HEAD:** `68557e1` — "runtime: add initialized field to GET /api/onboarding status response"

Recent commits (canonical slices only):
```
68557e1  runtime: add initialized field to GET /api/onboarding status response
33bc7b2  runtime: autowire onboarding completion into canonical initialize flow
3294aff  runtime: expose bootstrap trust posture in canonical state api
35e97fb  runtime: persist bootstrap truth for canonical initialization
3063edb  runtime: add GET /api/state endpoint to cmd_serve
ec7a537  runtime: add GET /onboarding to canonical cmd_serve ChatHandler
2a54633  runtime: lock canonical server — weslr-start.sh uses main.py serve
```

**Canonical server is `python3 main.py serve`** — `chat_ui.py` is a standalone shell, NOT used in production.
