# WESLR Jarvis Gap Assessment

*Assesses WESLR's current implementation against the goal of behaving like Jarvis (Iron Man) — a voice-driven, context-aware, proactive assistant.*

*Version: Expanded with doctrine, signal pipelines, artifact taxonomy, and proactivity infrastructure.*

---

## BATCH 1 — Voice I/O + Persistent Context

### 1. Voice I/O

**Status: 🚧 Partial — Shim implemented, real STT engine not connected**

| Component | Status | Location | Notes |
|---|---|---|---|
| Voice gateway (WebSocket) | ✅ | `weslr/voice_gateway.py` (516 lines) | Phase 1A shim. Listens on configurable host:port. Accepts browser audio over WebSocket. |
| STT transcription | 🚧 | `voice_gateway.py` — `stt_transcribe()` | Shim mode: text injection. Comment says "replace with whisper.cpp, openai-whisper, or Groq Whisper". Not yet replaced. |
| TTS | 🚧 | Web Speech API (browser-native) | `voice_gateway.py` comment says TTS is client-side via browser. Server-side TTS not implemented. |
| Wake word detection | ❌ | — | No wake word engine. Voice gateway starts manually via CLI or subprocess. |
| Streaming audio capture | 🚧 | Browser → WebSocket | Implemented in Phase 1A shim. Binary audio frames flow from browser to gateway. |

**Jarvis comparison:** Real Jarvis has dedicated wake word ("Jarvis") + always-on microphone. WESLR's voice gateway is activated manually and accepts pre-processed audio — it's closer to a walkie-talkie than a hands-free assistant.

**What would make it Jarvis-like:**
- Wake word engine (e.g., Porcupine, Precise版) with activation threshold
- Continuous audio capture loop (not WebSocket burst)
- Server-side TTS (e.g., Coqui, XTTS) so voice works cross-platform

---

### 2. Persistent Context Across Sessions

**Status: 🚧 Partial — Infrastructure exists, human-specific memory not fully wired**

| Component | Status | Location | Notes |
|---|---|---|---|
| Operator registry | ✅ | `continuity/operators.py` | Tracks operator metadata, lifecycle, session history. But no per-operator memory store. |
| Operator insight timeline | ✅ | `operator_insight_timeline.py` | Records operator signal patterns, insight summaries per operator over time. |
| Operator case window summary | ✅ | `operator_case_window_summary.py` | Aggregates operator context windows into summary docs. |
| Session continuity | ✅ | `session_continuity.py` | Persists session context across reconnects. |
| Continuity consolidation | ✅ | `continuity_consolidation.py` | Merges active capsule + thread state + operator context into unified continuity payload. |
| Human memory store | ❌ | — | No `human_memories/` directory, no `session_summaries/` loaded on next interaction. The `operator_insight_timeline` captures what the system observed about the operator, not what the operator told it. |
| Cross-session memory loading | 🚧 | Partial | `continuity/` directory has `active_thread_registry.json`, `history.json`, `snapshots/`. Thread-level context persists. Operator-level memory (preferences, earlier conversations, stated facts) is not explicitly loaded into the context window on new sessions. |

**Jarvis comparison:** Jarvis remembers Tony Stark's preferences, past projects, emotional state across days. WESLR has the infrastructure (operator timeline, case comparison, insight consolidation) but no explicit "human memory" retrieval step that fires on session start.

**What would make it Jarvis-like:**
- A `human_memories/<operator_id>.json` store — facts, preferences, past requests
- A session-start loader that injects relevant human memories into context
- A CLI command to query/write human memories (`weslr memory --human --recall "user prefers metric units"`)

---

*Batch 2 pending: Proactive Suggestions + Artifact Taxonomy*

---

## BATCH 2 — Proactive Suggestions + Artifact Taxonomy

### 3. Proactive Suggestions

**Status: 🚧 Partial — Signal infrastructure exists, proactive surfacing not implemented**

| Component | Status | Location | Notes |
|---|---|---|---|
| Signal classification (AAI alerts) | ✅ | `signal_alerting.py` | Classifies signals into A1–A4 tiers with alert/no-alert decisions. Handles private_dev, public_demo_readonly, public_demo modes. |
| Capability suggestion engine | ✅ | `capability_suggestion.py` | Scores and ranks capability gaps. References `proposal_trace.jsonl` for signal boosts. |
| Suggestion box (continuity) | ✅ | `continuity/suggestion_box/` | Tracks capability requests and continuity state. `requests.json` has submitted requests from early pilot. `continuity.json` holds session continuity signals. But: these are only consulted on-request, not surfaced proactively. |
| Proactive suggestion delivery | ❌ | — | No background daemon surfaces suggestions to the operator unprompted. No cron job, no heartbeat check that evaluates suggestion_box and delivers recommendations. |
| AAI alert → proactive route | 🚧 | Partial | `signal_alerting.py` classifies alerts and can trigger severity signals. But there's no path from an AAI alert to an proactive message to the operator. The output of `classify_signal_alert` is a result object — it doesn't cause action. |
| Composite analysis → suggestion | 🚧 | Partial | `composite_analysis_stack.py` runs multi-signal analysis. It can detect patterns across signals. But the output feeds governance review, not proactive operator outreach. |
| Insufficiency patterns → proactive | 🚧 | Partial | `contract_insufficiency_log.jsonl` and `contract_insufficiency_detector.py` log where WESLR's contracts fail. `insufficiency_handoff` and `inadequacy_intake` route these for operator attention. But this is reactive — operator has to ask. |

**Jarvis comparison:** Jarvis doesn't wait to be asked. He notices patterns, infers needs, and speaks up. WESLR's signal pipeline can *detect* patterns (AAI alerts, composite analysis, insufficiency logs) but has no *delivery mechanism* that surfaces them proactively without a user message.

**What would make it Jarvis-like:**
- A proactive heartbeat: every N minutes, check `suggestion_box/continuity.json`, `contract_insufficiency_log.jsonl`, `proposal_trace.jsonl` and surface anything above a threshold
- A "proactive surface" module that formats and delivers suggestions as a chat message or notification
- A CLI flag: `weslr --proactive` that activates this mode

---

### 4. Artifact Taxonomy — What Each JSONL Is For

**Status: ✅ Implemented — Four distinct artifacts with clear purposes**

| Artifact | Location | Purpose | Record Types |
|---|---|---|---|
| `proposal_trace.jsonl` | `weslr/proposal_trace.jsonl` | Audit trail of all governance proposals: created, accepted, rejected, withdrawn. Used by `capability_suggestion.py` for signal boosting. | `proposal_created`, `proposal_accepted`, `proposal_rejected`, `proposal_withdrawn` |
| `contract_observations.jsonl` | `weslr/contract_observations.jsonl` | Records every response contract matched against actual user turns. Used to observe contract drift, reply shape accuracy. | `contract_observation_v1` |
| `public_signals.jsonl` | `weslr/public_signals.jsonl` | Anonymous signal fingerprints from public website interactions. Used to infer global demand signal without storing PII. | `public_signal_v1` |
| `iss_diagnostic_records.jsonl` | `memory/iss_records.jsonl` | ISS (Insufficient Signal Surface) diagnostic events — moments when WESLR detected its own evidence surface was insufficient. | ISS diagnostic events |
| `operator_feedback_log.jsonl` | `weslr/operator_feedback_log.jsonl` | Operator (human) feedback entries — correction signals, preference signals, governance overrides. | Operator feedback entries |
| `contract_insufficiency_log.jsonl` | `weslr/contract_insufficiency_log.jsonl` | Moments when WESLR's response contracts failed to match the operator's actual need. Used for contract improvement. | Insufficiency events |

**Clarification on `proposal_trace.jsonl` vs `contract_observations.jsonl`:**
- `proposal_trace` = governance layer output (what was proposed, scored, and decided)
- `contract_observations` = dialogue layer output (which response contract matched, what reply shape was used)

**Clarification on `public_signals.jsonl` vs `iss_diagnostic_records.jsonl`:**
- `public_signals` = passive observation of anonymous public users
- `iss_diagnostic_records` = active self-detection of WESLR's own internal inadequacy

---

*Batch 3 pending: Action Execution + Doctrinal Boundaries + Proactivity Infrastructure*

---

## BATCH 3 — Action Execution + Doctrinal Boundaries + Proactivity Infrastructure

### 5. Action Execution

**Status: 🚧 Partial — Proposal/approval infrastructure exists, execution blocked by doctrine**

| Component | Status | Location | Notes |
|---|---|---|---|
| Remote action proposal model | ✅ | `remote_action_proposal.py` (61 lines) | Canonical proposal model for remote actions between WESLR nodes. Proposal/gate/escalate only — no execution. |
| Controlled execution envelope | ✅ | `controlled_execution_envelope.py` (830 lines) | Full lifecycle: proposal status, rejection reasons, trust/health gates, proof safety hooks, escalation paths, audit trace. |
| Remote governance awareness | ✅ | `remote_governance_awareness.py` | Nodes can track governance state of other nodes. |
| Remote execution receipt | ✅ | `remote_execution_receipt.py` | Receipt tracking for remote action results. |
| Execution gate (operator) | 🚧 | `governance_surface.py` | Proposals go through the governance surface for operator review. But: `REPO_GUARD.md` explicitly forbids unverified execution. |
| **Actual shell/system execution** | ❌ | — | WESLR proposes actions, the operator approves, but WESLR itself does not run shell commands. That's the operator's job after approval. |

**Jarvis comparison:** Jarvis executes. He runs systems, deploys code, analyzes data, controls devices. WESLR's architecture explicitly prevents self-execution — it can propose, recommend, and explain, but the operator pulls the trigger. This is by design (`REPO_GUARD.md`), not a gap.

**📜 Doctrine says:** Actions require operator approval. WESLR models proposals, it doesn't execute them. This is intentional — Jarvis-like execution is not the goal for a governed system. Mark as "allowed but not implemented" — the governance model supports it, but the operator must approve before any action runs.

---

### 6. Doctrinal Boundaries (What WESLR Is Allowed to Do)

**Status: ✅ Documented — Clear boundaries, no ambiguity**

From `REPO_GUARD.md` and `INFINITY_HANDOFF.md`:

| Rule | Status |
|---|---|
| **Scope**: WESLR Python files in `weslr/` | ✅ Active |
| **Excluded scopes**: TIA, collector, industrial_slice, product_runtime_expansion | ✅ Blocked |
| **Pre-edit checks**: git status, branch, active scope verification | ✅ Required |
| **No unverified execution**: Actions require operator approval via governance surface | ✅ Enforced |
| **No routing to excluded scopes** | ✅ Blocked |
| **No partial seals**: exact commit hash required for completion | ✅ Enforced |
| **Repo truth rules**: no repo drift, no hidden scope expansion | ✅ Active |

**WESLR action authority:**
- ✅ Model and propose actions
- ✅ Surface recommendations and suggestions
- ✅ Explain reasoning and trade-offs
- ✅ Execute on explicit operator approval (via CLI, chat, or governance surface)
- ❌ Self-execute without operator confirmation
- ❌ Modify TIA / collector / industrial_slice / product_runtime_expansion

**Jarvis comparison:** Tony Stark's Jarvis has full system access and executes at will. WESLR's operator (pr0dus) is the authority. WESLR is a recommending system, not an executing one. This is intentional governance, not a gap.

---

### 7. Proactivity Infrastructure — What's a Daemon vs. On-Request

**Status: 🚧 Partial — Core infrastructure exists, proactive daemon not active**

| Component | Running Mode | Location | Notes |
|---|---|---|---|
| Governance surface | On-request | `governance_surface.py` | Activated when a proposal needs review. Not a background daemon. |
| Signal alerting | On-request | `signal_alerting.py` | Classifies signals when called. Not a polling daemon. |
| Capability suggestion | On-request | `capability_suggestion.py` | Runs when capability gap detection fires. Not continuous. |
| Composite analysis stack | On-request | `composite_analysis_stack.py` | Activated per request or when a composite signal is detected. |
| Heartbeat | Daemon (OpenClaw managed) | `HEARTBEAT.md` | OpenClaw triggers heartbeat every ~30min. WESLR can add tasks to `HEARTBEAT.md` to be checked on each beat. This is the existing proactivity hook. |
| Cron jobs | Daemon (OpenClaw managed) | `cron` tool | OpenClaw cron can schedule recurring tasks. WESLR can register jobs here. |
| Evidence pipeline | On-request | `evidence_pipeline.py` | Activated per message/turn. Not a background processor. |
| Session continuity | On-request | `continuity.py` | Loads context on session start. Not a continuous background process. |
| Operator insight timeline | Background-write | `operator_insight_timeline.py` | Writes operator observations continuously as side-effect of conversations. But no proactive read/surface loop. |

**What runs continuously:**
- OpenClaw heartbeat (every ~30 min — can be configured)
- Session context persistence (file-based, on write)
- Operator insight timeline (appended on every interaction)

**What doesn't run continuously:**
- Proactive suggestion surfacing (no cron, no heartbeat task that evaluates suggestion_box)
- Capability gap auto-detection (event-triggered, not scheduled)
- AAI alert → operator notification (signal classified but not delivered proactively)

**Jarvis comparison:** Jarvis runs continuously, monitoring systems and surfacing insights without being asked. WESLR's daemon infrastructure is OpenClaw's heartbeat + cron — it's adequate for periodic tasks, but there's no active "surveillance" loop that monitors the system state and decides to speak up unprompted.

---

*Batch 4 pending: Summary Table + Roadmap Priorities*
---

## BATCH 4 — Summary Table + Roadmap Priorities

### Per-Area Verdict Summary

| # | Area | Status | Verdict | Key Gap |
|---|---|---|---|---|
| 1 | Voice I/O | 🚧 Partial | Shim implemented, real STT/TTS not connected | Wake word, continuous audio, server-side TTS |
| 2 | Persistent context | 🚧 Partial | Infrastructure exists, human memory not loaded | `human_memories/` store + session-start loader |
| 3 | Proactive suggestions | 🚧 Partial | Signal pipeline works, delivery mechanism missing | Proactive heartbeat + surface module |
| 4 | Artifact taxonomy | ✅ Done | Four distinct JSONL artifacts, clearly scoped | None |
| 5 | Action execution | 🚧 Partial | Governance proposal exists, execution blocked by doctrine | Allowed by doctrine but not operator-enabled |
| 6 | Doctrinal boundaries | ✅ Done | REPO_GUARD fully documents scope rules | None |
| 7 | Proactivity infrastructure | 🚧 Partial | OpenClaw heartbeat/cron available, no active surveillance loop | Proactive daemon + surface layer |

---

### Roadmap Priorities (Jarvis-like Jar)

**Priority 1 — Voice I/O completion** (highest Jarvis-factor impact)
- Replace `voice_gateway.py` STT shim with Whisper.cpp or Groq Whisper API
- Add server-side TTS (Coqui/XTTS) for cross-platform voice
- Implement wake word detection (Porcupine or Precise版)

**Priority 2 — Human Memory Store** (persistent context)
- Create `human_memories/<operator_id>.json` store
- Build session-start loader that injects human memories into context
- Add `weslr memory --human --recall` CLI command

**Priority 3 — Proactive Suggestion Surface** (Jarvis-like behavior)
- Add proactive check to `HEARTBEAT.md`: evaluate `suggestion_box/continuity.json`, `contract_insufficiency_log.jsonl` on each heartbeat
- Build `proactive_surface.py` that formats suggestions as chat messages
- Register a cron job for periodic system-health proactive outreach

**Priority 4 — Action Execution (operator-approved)**
- `controlled_execution_envelope.py` is ready for operator-approved execution
- Add a "dry run" mode: operator can preview what would happen before approving
- Connect to OpenClaw's `exec` tool for actual command execution on approval

---

*Assessment complete. All four batches delivered. Document at `WESLR_JARVIS_GAP_ASSESSMENT.md`.*
