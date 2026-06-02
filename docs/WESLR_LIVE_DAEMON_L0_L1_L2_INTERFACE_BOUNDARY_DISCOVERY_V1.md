# WESLR Live Daemon L0/L1/L2 Interface Boundary Discovery V1

## 1. Executive summary

**What daemon exists?**
Not one monolith — three runtime surfaces matter here:
- `weslr/voice_gateway.py` — live WS voice gateway, started from `main.py` in serve mode.
- `weslr/voice_layer/run_ambient.py` + `weslr/voice_layer/ambient_loop.py` — ambient voice loop with `--daemon` and continuous tick modes.
- `weslr/proactive_daemon.py` and `weslr/frontier_daemon.py` — background daemon threads, opt-in / env-gated.

**What files define it?**
- `weslr/voice_gateway.py`
- `weslr/voice_layer/run_ambient.py`
- `weslr/voice_layer/ambient_loop.py`
- `weslr/voice_layer/voice_config.py`
- `weslr/voice_layer/cli_voice.py`
- `weslr/proactive_daemon.py`
- `weslr/frontier_daemon.py`
- runtime wiring in `main.py` (`cmd_serve`) and `dialogue.py` (`build_communicator_message_payload`)

**What are L0/L1/L2?**
The repo uses L0/L1/L2 in **two different ways**:
1. **Memory tiers** (`sim.py`, `docs/REPO_HYGIENE_STANDARD_V1.md`):
   - L0 = identity core
   - L1 = operating facts
   - L2 = session state
2. **Security/runtime trust levels** (`weslr/security.py`, `docs/SYSTEM_SCHEMATIC_AND_CAPABILITY_MAP_V1.md`):
   - L0 = conversational
   - L1 = sensitive
   - L2 = elevated

**What flags exist?**
- Voice permission flags: `voice_enabled`, `audio_playback_enabled`, `autonomous_speaking_enabled`, `ambient_loop_enabled`, `text_only`, `muted_until`, `quiet_hours_enabled`, `quiet_hours_start`, `quiet_hours_end`, `selected_engine`, `relationship_learning_enabled`, `adaptive_greeting_enabled`, `cooldown_minutes`, `first_arrival_greeting_enabled`, `departure_acknowledgment_enabled`, `playback_backend`, `playback_volume`.
- CLI/runtime flags: `--once`, `--text-only`, `--status`, `--voice-off`, `--voice-on`, `--mute`, `--daemon`, `--tick-interval`, `--debug`; voice gateway `--port`, `--host`, `--weslr-http-port`; voice CLI commands `status/on/off/mute/unmute/text-only/autonomous/quiet-hours/engine/cooldown`.
- Daemon env flags: `WESLR_PROACTIVE_DAEMON_ENABLED`, `WESLR_PROACTIVE_INTERVAL_MINUTES`, `WESLR_OPERATOR_ID`, `WESLR_FRONTIER_DAEMON_ENABLED`, `WESLR_FRONTIER_INTERVAL_HOURS`, `WESLR_FRONTIER_MAX_CANDIDATES`, `WESLR_FRONTIER_BREAKTHROUGH_MIN`, `WESLR_FRONTIER_NOVELTY_CHECKS`.
- No explicit `can_speak`, `can_hear`, `can_listen`, `can_reply`, `can_interrupt` symbols were found.

**Is it currently runtime-critical?**
- For core `/chat`: not critical.
- For voice/ambient serve modes: yes, runtime-facing and active.
- `main.py` launches `voice_gateway.py` as a subprocess in serve mode, so the voice gateway is live-path infrastructure.

**Is it safe to integrate with current metadata-helper stack?**
- **Not yet for direct/raw integration.**
- **Yes only for compact verdict packets** (readiness, permission, grounding, route, risk). Raw evidence, private memory, and model/runtime authority should stay outside the daemon boundary.

---

## 2. Daemon inventory

### Daemon files
- `weslr/voice_gateway.py`
- `weslr/voice_layer/ambient_loop.py`
- `weslr/voice_layer/run_ambient.py`
- `weslr/proactive_daemon.py`
- `weslr/frontier_daemon.py`

### Config / state files
- `~/.weslr/voice_config.json`
- `.weslr/memory_tiers/l0_identity.json`
- `.weslr/memory_tiers/l1_operating.json`
- `.weslr/memory_tiers/l2_session.json`
- `.weslr/timelines/<timeline_id>/events.jsonl`
- `.weslr/pending_messages.jsonl`
- `.weslr/daemon_frontier.json`

### Docs
- `docs/REPO_HYGIENE_STANDARD_V1.md`
- `docs/SYSTEM_SCHEMATIC_AND_CAPABILITY_MAP_V1.md`
- `docs/CAPABILITY_WIRING_MAP_v1.md`
- `weslr/docs/WESLR_JARVIS_GAP_ASSESSMENT.md`
- `weslr/voice_layer/README.md`
- `docs/CURRENT_RUNTIME_STATE_SNAPSHOT_v1.md`
- `docs/WESLR_JARVIS_ROADMAP_V1.md`
- `docs/LIVE_BEHAVIOUR.md`
- `docs/ORDINARY_TASK_CONTEXT.md`

### Tests
- `weslr/tests/test_voice_session_routing_v1.py`
- `weslr/tests/test_proactive_daemon_v1.py`
- `weslr/tests/test_ambient_voice_*`
- `weslr/tests/test_voice_provenance_*`

### Imports / entrypoints
- `main.py` → `cmd_serve()` starts `weslr/voice_gateway.py` subprocess.
- `voice_gateway.py` → `start_voice_gateway()`, `stop_voice_gateway()`, WS entrypoint.
- `run_ambient.py` → CLI entrypoint for ambient loop / daemon mode.
- `cli_voice.py` → voice config control CLI.
- `proactive_daemon.py` / `frontier_daemon.py` → `start_*`, `stop_*`.
- `dialogue.py` → `build_communicator_message_payload(...)` consumes L0/L1/L2 memory tiers.
- `sim.py` → `load_tier()` / `load_communicator_self()`.

### Runtime state paths observed safely
- `.weslr/memory_tiers/l0_identity.json`
- `.weslr/memory_tiers/l1_operating.json`
- `.weslr/memory_tiers/l2_session.json`
- `.weslr/timelines/<timeline_id>/events.jsonl`
- `.weslr/pending_messages.jsonl`
- `.weslr/daemon_frontier.json`
- `~/.weslr/voice_config.json`

---

## 3. L0/L1/L2 semantics

### A) Memory-tier meaning
From `sim.py:load_tier()` and `docs/REPO_HYGIENE_STANDARD_V1.md`:
- **L0** = identity core (`identity_anchor`, `core_drives`, operator identity/role).
- **L1** = operating facts (`affect`, `narrative`, `intent`, `governance`).
- **L2** = session state (`identity_state`, `continuity`).

**Allowed operations per tier**
- **L0**: identity bootstrap and stable self-description.
- **L1**: operating-state enrichment, preferences, intent, governance cues.
- **L2**: session continuity / turn-local state.

**Behavior**
- These are **payload/context tiers**, not authority tiers.
- They should inform response assembly, not grant permission.

### B) Trust-level meaning
From `weslr/security.py` and `docs/SYSTEM_SCHEMATIC_AND_CAPABILITY_MAP_V1.md`:
- **L0** = conversational / normal chat.
- **L1** = sensitive / contextual acknowledgment.
- **L2** = elevated / explicit in-session confirmation.

**Allowed operations per level**
- **L0**: chat/query/self-report.
- **L1**: preference/profile updates.
- **L2**: message send / document share / other confirmed actions.

**Behavior**
- These are **capability/security modes**, not truth modes.
- They gate action authority, not claim correctness.

### C) Speak/hear/listen mapping
- **Speak**: governed by `voice_enabled`, `text_only`, `muted_until`, `quiet_hours_enabled`, `autonomous_speaking_enabled`, `ambient_loop_enabled`, and the surface decision pipeline.
- **Hear/listen**: not explicit `can_hear` / `can_listen` flags; voice input is bounded by WebSocket session, transcript messages, and optional browser STT shim.
- **Listen** is therefore a transport/session behavior, not a separate trust level.

---

## 4. Current flag inventory

### Voice permission / behavior flags
- `voice_enabled`
- `audio_playback_enabled`
- `autonomous_speaking_enabled`
- `ambient_loop_enabled`
- `text_only`
- `muted_until`
- `quiet_hours_enabled`
- `quiet_hours_start`
- `quiet_hours_end`
- `selected_engine`
- `relationship_learning_enabled`
- `adaptive_greeting_enabled`
- `cooldown_minutes`
- `first_arrival_greeting_enabled`
- `departure_acknowledgment_enabled`
- `playback_backend`
- `playback_volume`

### Ambient/runtime CLI flags
- `--once`
- `--text-only`
- `--status`
- `--voice-off`
- `--voice-on`
- `--mute`
- `--daemon`
- `--tick-interval`
- `--debug`

### Voice gateway flags
- `--port`
- `--host`
- `--weslr-http-port`

### Voice CLI commands
- `status`
- `on`
- `off`
- `mute`
- `unmute`
- `text-only`
- `autonomous`
- `quiet-hours`
- `engine`
- `cooldown`

### Daemon env toggles
- `WESLR_PROACTIVE_DAEMON_ENABLED`
- `WESLR_PROACTIVE_INTERVAL_MINUTES`
- `WESLR_OPERATOR_ID`
- `WESLR_FRONTIER_DAEMON_ENABLED`
- `WESLR_FRONTIER_INTERVAL_HOURS`
- `WESLR_FRONTIER_MAX_CANDIDATES`
- `WESLR_FRONTIER_BREAKTHROUGH_MIN`
- `WESLR_FRONTIER_NOVELTY_CHECKS`

### Missing explicit flags
- `can_speak` — not found
- `can_hear` — not found
- `can_listen` — not found
- `can_reply` — not found
- `can_interrupt` — not found

---

## 5. What should go through daemon

- Voice/listen/speak state
- Lifecycle state
- Session readiness
- Wake/sleep/interrupt state
- Runtime health
- Operator pause / mute state
- Answer-output permission
- Surface-routing metadata
- Compact authority verdicts only

**Recommended packet shape**
- `request_id`
- `mode_level`
- `route`
- `readiness`
- `listen_allowed`
- `speak_allowed`
- `grounding_status`
- `source_access_status`
- `action_authority_status`
- `risk_status`
- `next_gate`

---

## 6. What should NOT go through daemon

- Raw retrieved documents
- Raw private memory
- Full Source Evidence Graph content
- NAIE internal inference details
- UNKNOWN ENGINE internal pressure details
- Hidden prompts
- Protected instructions
- Model prompts
- Secrets/tokens
- Tool execution authority
- Public claim approval
- Behavior-pack promotion authority

---

## 7. Metadata packet boundary

The daemon boundary should only carry compact verdicts, not source payloads.

**Allowed packet examples**
- mode / tier
- readiness verdict
- speak/hear permission
- grounding state
- access-block state
- action-block state
- next approved gate

**Forbidden packet contents**
- raw source text
- full retrieval results
- private logs
- internal chain-of-thought / hidden inference
- live provider/model markers
- operator secrets

---

## 8. Relationship to RAG

RAG routing should **not** run inside the daemon.

Daemon may receive only verdicts such as:
- `retrieval_required`
- `retrieval_blocked`
- `evidence_ready`
- `unsupported`
- `access_blocked`
- `poison_blocked`

RAG remains a pre-answer routing/evidence selection layer, not daemon authority.

---

## 9. Relationship to NAIE / UNKNOWN / Chat Engine

- Chat Engine may ask daemon whether it may **speak/render**.
- NAIE should not live in daemon.
- UNKNOWN ENGINE should not live in daemon.
- Daemon should not decide truth.
- Daemon gates surfaces and runtime permission only.

---

## 10. Relationship to action/tool/device control

- Daemon may enforce a global action-disabled state.
- Daemon must **not** grant action authority.
- Action authority requires a separate executor boundary and owner/operator approval.

---

## 11. Risks

- Daemon becomes hidden central authority
- Raw private data crosses daemon boundary
- RAG evidence leaks into runtime flags/logs
- L0/L1/L2 ambiguity causes policy drift
- Speak/hear flags bypass answer readiness
- Runtime mode gets confused with truth/claim authority
- Voice surface speaks unsupported claims aloud

---

## 12. Recommended boundary

Create:
`DESIGN_WESLR_LIVE_DAEMON_INTERFACE_AND_MODE_BOUNDARY_V1`

Reason: the daemon surface is active, runtime-facing, and already influences voice/session routing; it needs an explicit interface contract before any deeper integration.

---

## 13. Recommended next lane

**Recommended:** `DESIGN_WESLR_LIVE_DAEMON_INTERFACE_AND_MODE_BOUNDARY_V1`

---

## 14. Boundaries and non-claims

- No daemon changes were implemented.
- No runtime authority was authorized.
- No RAG integration was added.
- No voice/speech authority was added.
- No action/tool/device authority was added.
- No models/providers were called.
- No secrets/private logs were exposed.
- No public-readiness claim is being made.

---

## 15. Final judgment

`live_daemon_l0_l1_l2_discovery_ready_for_interface_boundary_design`

---

## Final report

- **repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`
- **branch:** `master`
- **start HEAD:** `b84508c6e0373a1cb216cbc903e94d1ce23cf756`
- **end HEAD:** `b84508c6e0373a1cb216cbc903e94d1ce23cf756` (no code changes)
- **commit hash:** not created yet
- **report created:** `docs/WESLR_LIVE_DAEMON_L0_L1_L2_INTERFACE_BOUNDARY_DISCOVERY_V1.md`
- **daemon files found:** `weslr/voice_gateway.py`, `weslr/voice_layer/ambient_loop.py`, `weslr/voice_layer/run_ambient.py`, `weslr/voice_layer/voice_config.py`, `weslr/voice_layer/cli_voice.py`, `weslr/proactive_daemon.py`, `weslr/frontier_daemon.py`
- **L0/L1/L2 meaning:** memory tiers (identity / operating / session) plus separate trust levels (conversational / sensitive / elevated)
- **flags found:** voice permission flags, ambient CLI flags, voice gateway flags, daemon env toggles
- **what should go through daemon:** compact verdicts only
- **what should not:** raw docs, private memory, full graph, prompts, secrets, tool authority, public claim approval
- **recommended next lane:** `DESIGN_WESLR_LIVE_DAEMON_INTERFACE_AND_MODE_BOUNDARY_V1`
- **validation results:** pending
- **protected files untouched:** `weslr/chat_responder.py`, `weslr/main.py`, `dialogue.py`, `chat_ui.py` (no edits made)
- **final judgment:** `live_daemon_l0_l1_l2_discovery_ready_for_interface_boundary_design`
