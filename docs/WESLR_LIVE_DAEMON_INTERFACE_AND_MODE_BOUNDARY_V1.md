# WESLR Live Daemon Interface and Mode Boundary V1

## 1. Executive doctrine

**WESLR Live Daemon Interface and Mode Boundary V1** defines the surface/lifecycle/permission boundary for live runtime handling.

The daemon may decide whether WESLR can:
- listen
- speak
- render
- pause
- resume
- route a response
- remain silent

The daemon must **not** decide:
- truth
- proof
- grounding authority
- public claim approval
- tool/action authority
- memory promotion
- behavior-pack promotion
- RAG evidence selection
- NAIE reasoning
- UNKNOWN ENGINE pressure reasoning

**Core rule:** the daemon receives compact verdicts, not raw evidence or reasoning payloads.

---

## 2. Boundary position

Pipeline:

`Chat / voice / ambient request`
→ `daemon permission / mode boundary`
→ `routing / RAG / evidence / NAIE / grounding outside daemon`
→ `compact answer-readiness verdict back to daemon`
→ `daemon allows / suppresses / renders / speaks only`

This means the daemon is a **gate**, not a judge of truth.

---

## 3. L0 / L1 / L2 clarification

There are two meanings and they must stay distinct.

### A. Memory tiers
- **L0** = identity core
- **L1** = operating facts
- **L2** = session state

### B. Runtime/security trust levels
- **L0** = conversational
- **L1** = sensitive
- **L2** = elevated / explicit confirmation

### Rules
- memory tiers do **not** grant action authority
- trust levels do **not** grant truth authority
- future packets must name `memory_tier` separately from `trust_level`
- the daemon may consume either, but must not conflate them

---

## 4. Daemon responsibility

The daemon may own:
- voice/listen/speak state
- mute / unmute
- quiet hours
- text-only state
- ambient loop enablement
- autonomous speaking enablement
- lifecycle / heartbeat
- session readiness
- interruption policy
- route-to-surface decision
- operator pause
- emergency stop
- compact answer-output permission

This is **permission and surface control**, not reasoning authority.

---

## 5. Daemon non-responsibility

The daemon must not own:
- raw memory retrieval
- raw documents
- full Source Evidence Graph
- full NAIE inference packets
- UNKNOWN ENGINE pressure content
- hidden prompts
- protected instructions
- model prompts
- provider calls
- tool execution
- public claim approval
- proof / truth decisions
- behavior-pack promotion
- memory writes

---

## 6. Compact daemon verdict packet

Future daemon verdicts should be metadata-only and compact.

Required fields:
- `daemon_verdict_packet_id`
- `request_id`
- `surface`
- `memory_tier_context_allowed`
- `trust_level_required`
- `current_trust_level`
- `listen_allowed`
- `speak_allowed`
- `render_allowed`
- `reply_allowed`
- `interrupt_allowed`
- `autonomous_speaking_allowed`
- `route`
- `readiness_status`
- `grounding_status`
- `source_access_status`
- `poison_status`
- `privacy_status`
- `action_authority_status`
- `public_claim_status`
- `risk_status`
- `next_gate`
- `reason_summary`
- `raw_payload_allowed`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

---

## 7. Allowed packet values

### Surfaces
- `chat`
- `voice`
- `ambient`
- `proactive`
- `frontier`
- `unknown_surface`

### Routes
- `render_text`
- `speak_voice`
- `silent_store_none`
- `ask_clarification`
- `block_response`
- `defer_response`
- `operator_review_required`

### Readiness
- `ready`
- `ready_with_caveat`
- `not_ready_missing_evidence`
- `not_ready_access_blocked`
- `not_ready_poison_blocked`
- `not_ready_grounding_blocked`
- `not_ready_operator_required`
- `unknown_readiness`

### Risk
- `low`
- `medium`
- `high`
- `blocked`
- `unknown_risk`

### Action authority
- `no_action_authority`
- `proposal_only`
- `owner_required`
- `operator_required`
- `blocked`

---

## 8. RAG relationship

RAG routing must run outside the daemon.

The daemon may receive only compact statuses such as:
- `retrieval_required`
- `retrieval_not_required`
- `evidence_ready`
- `unsupported`
- `access_blocked`
- `poison_blocked`
- `grounding_blocked`

The daemon must not receive:
- raw retrieved documents
- chunks
- citation internals
- private source text
- vector payloads

---

## 9. Source Evidence Graph relationship

The Source Evidence Graph remains outside the daemon.

The daemon may receive:
- `grounding_status`
- `citation_readiness`
- `access_blocked`
- `contradiction_present`
- `unsupported_claim_present`

The daemon must not receive:
- the full graph
- raw claim/source internals
- private source nodes
- raw edge payloads

---

## 10. NAIE / UNKNOWN / Chat relationship

Rules:
- Chat Engine may ask the daemon whether output can be rendered/spoken.
- NAIE may produce readiness/blocked verdicts outside the daemon.
- UNKNOWN ENGINE may produce friction/uncertainty verdicts outside the daemon.
- the daemon does not run NAIE or UNKNOWN
- the daemon does not decide final truth
- the daemon only gates surfaces and runtime permission

---

## 11. Inline citation / grounding relationship

Grounding remains outside the daemon.

The daemon may receive:
- `grounded`
- `partially_grounded`
- `unsupported`
- `contradicted`
- `stale_support`
- `access_restricted`
- `poison_quarantined`

The daemon should use these only to decide whether to:
- speak
- render with caveat
- ask clarification
- block/defer

---

## 12. Action/tool/device boundary

The daemon may enforce a global action-disabled state.

The daemon must not grant action authority.

Action/tool/device execution requires:
- a separate executor boundary
- owner/operator approval
- explicit trust level
- a compact action verdict

---

## 13. Voice-specific safeguards

- voice output must be stricter than text when unsupported
- unsupported or contradicted claims should not be spoken as confident facts
- high-risk outputs should prefer text or operator review
- quiet hours and mute always override speak permission
- autonomous speaking requires stricter readiness than user-requested reply

---

## 14. Ambient / proactive / frontier safeguards

- ambient/proactive/frontier daemons may create proposals or notifications only when enabled
- no raw private evidence in daemon messages
- no public claims
- no autonomous tool execution
- no autonomous memory promotion
- no autonomous behavior-pack promotion
- operator review for elevated/sensitive outputs

---

## 15. Packet validation rules

Future daemon verdict packets must fail if:
- `raw_payload_allowed` is true
- `runtime_authority` is true
- `writes_state` is true
- `model_provider_used` is true
- `public_claim_allowed` is true
- `proof_claim_allowed` is true
- `learning_claimed` is true
- action authority is granted directly
- hidden prompt / raw private / secret fields appear
- AGI / consciousness / Turing / certification / public-readiness claims appear
- `memory_tier` is used as `trust_level` or vice versa

---

## 16. Future helper design

Recommended future helper:

`weslr/live_daemon_interface_mode_boundary.py`

Future APIs:
- `build_live_daemon_verdict_packet_v1(...)`
- `validate_live_daemon_verdict_packet_v1(packet)`
- `summarize_live_daemon_verdict_packet_v1(packet)`
- `to_live_daemon_verdict_json_safe_v1(value)`
- `build_initial_live_daemon_interface_examples_v1()`

---

## 17. Future implementation strategy

Recommended phases:
1. metadata-only verdict packet helper
2. synthetic examples
3. validation helper
4. summary renderer
5. relation to RAG / grounding / NAIE verdicts
6. later read-only integration audit
7. only later runtime wiring, if approved

---

## 18. Boundaries and non-claims

This design does not:
- modify daemon code
- authorize voice
- authorize autonomous speaking
- authorize runtime/chat integration
- implement RAG
- expose memory or documents
- call models/providers
- write `.weslr`
- control tools/devices
- authorize public claims
- claim public readiness, AGI, consciousness, sentience, Turing success, proof, truth, certification, or production readiness

---

## 19. Recommended next lane

Recommended next lane:

`IMPLEMENT_WESLR_LIVE_DAEMON_INTERFACE_AND_MODE_BOUNDARY_V1`

Then return to:

`DESIGN_WESLR_DOCUMENT_ACCESS_CONTROL_AND_PII_SCRUBBING_BOUNDARY_V1`

---

## 20. Final judgment

**Recommended judgment:** `live_daemon_interface_mode_boundary_design_ready_for_metadata_helper_implementation`

---

## Final report

- **repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`
- **branch:** `master`
- **start HEAD:** `9690c3ee5cff03cdfda5050d4b44e5b4dc78cf8f`
- **end HEAD:** `9690c3ee5cff03cdfda5050d4b44e5b4dc78cf8f` (design-only, no code changes)
- **commit hash:** not yet created
- **doc created:** `docs/WESLR_LIVE_DAEMON_INTERFACE_AND_MODE_BOUNDARY_V1.md`
- **key design capture:** daemon is a compact verdict boundary for surface/lifecycle/permission only; routing, grounding, RAG, NAIE, and truth remain outside it
- **validation results:** pending
- **protected files untouched:** `weslr/chat_responder.py`, `weslr/main.py`, `dialogue.py`, `chat_ui.py` (no edits made)
- **final judgment:** `live_daemon_interface_mode_boundary_design_ready_for_metadata_helper_implementation`
- **recommended next lane:** `IMPLEMENT_WESLR_LIVE_DAEMON_INTERFACE_AND_MODE_BOUNDARY_V1`
