# WESLR Interaction Control Plane Grounding Audit V1

**Version:** 1.0
**Status:** AUDIT — inspection only, no implementation
**Date:** 2026-04-30

---

## Section 1 — Current Chat Flow Map

```
browser UI (index.html)
  → POST /chat { "message": "..." }
    → deploy/staging/weslr_demo_server.py
        WeslrDemoHandler.do_POST()
          → weslr_chat(message)                   [weslr_backend_contract.chat()]
              1. interpret_human_turn(message)    [interpretation.py]
                  - rate limit check
                  - write handler guard (public_demo_readonly)
                  - dispatch_deterministic_handler() [deterministic_handlers.py]
                      → matched: expand_response() [response_expander.py]
                        → decide_response_policy() [policy_engine.py]
                      → not matched: _build_safe_response(path="fallback_safe")
                        → expand_response() [response_expander.py]
                  - returns: {path, response_text, confidence, topics, ...}

              2. [ENTRY FIX] if response_text.startswith("Hi — I'm WESLR")
                  → short-circuit, return {success, reply=response_text,
                       intent=interpreted, source="deterministic_entry"}

              3. build_communicator_message_payload()  [dialogue.py]
                  - latest_human = {message, topics, turn_type, reply_shape, likely_need}
                  - _compute_context_selection() → "uncertain" for short vague inputs
                  - _compute_boundary_hints() → "unknown"
                  - [SIGNAL OVERRIDE] if turn_type NOT IN (question/greeting/confusion/repair)
                      AND _ctx_sel == uncertain AND len < 30
                      → reply_shape = "signal_uncertainty_strong"
                      → message overwritten with uncertainty_strong_response
                  - _get_language_module().get_response() → message string
                  - returns: {message, inner_thought: {source, summary}}

              4. reply = result["message"]
              5. return {success, reply, intent, source}

          → _capture_signal()                      [website_signal_integration.py]
              → capture_website_signal()
              → classify_public_signal()            [user_signal_intake.py]
              → build_public_signal_record()        [user_signal_intake.py]
              → validate_public_signal_record()     [public_signal_store.py]
              → append_public_signal_record()       [public_signal_store.py]
              → public_signals.jsonl (append-only, write-once)

          → JSON response to browser (reply only, no internal structures)
```

**Where response_text becomes reply:**
- `expand_response()` in `response_expander.py` sets `response["response_text"]` for all paths
- Entry greeting: `response["response_text"] = _entry_greeting()` — then overwritten by `build_communicator_message_payload` if not short-circuited
- Fallback: `response["response_text"] = _fallback_guidance()` — then potentially overwritten by signal uncertainty override in `build_communicator_message_payload`
- `reply` is extracted as `result.get("message")` from `build_communicator_message_payload` output

**Where path/source/intent are set:**
- `path`: set by `dispatch_deterministic_handler` (matched handler) or `"fallback_safe"` (no match) or `"blocked_write"` (write guard)
- `intent`: returned dict from `interpret_human_turn` — includes `path`, `topics`, `response_text`, `confidence`
- `source`: from `result["inner_thought"]["source"]` (dialogue.py), or `"deterministic_entry"` (short-circuit)

---

## Section 2 — Existing OmniChat Layer Map

The L1/L2/L3/L4 naming appears only in `policy_engine.py` comments describing expansion layer intent — it is **not a functional layer system in the code**.

**Actual layers that exist:**

| Layer | File | Role |
|-------|------|------|
| Intent dispatch | `deterministic_handlers.py` | Routes input to registered handler by trigger prefix |
| Policy decision | `policy_engine.py` `decide_response_policy()` | Sets `final_response_type`, `expansion_layers`, `depth_level`, `evidence_mode_offered` |
| Response expansion | `response_expander.py` `expand_response()` | Applies response text, guidance, graph context, knowledge view |
| Context selection | `context_selector.py` `select_context_for_graph_query()` | Graph traversal for evidence, max_depth=2, max 20 connections |
| Signal uncertainty | `dialogue.py` `build_communicator_message_payload()` | Overrides reply_shape to `signal_uncertainty_strong` when conditions met |

**Expansion layer usage (from policy_engine.py):**
```python
# All policies return:
"expansion_layers": ["L1", "L2", "L4"]
# L3 is never assigned by any policy — implied/missing
```

**What L1/L2/L4 actually mean in the code:**
- `L1`, `L2`, `L4` are present as **policy metadata labels only** — they describe intended expansion behavior
- They are **never read by `expand_response()`** to conditionally apply different logic
- The three values are identical for all policy types — no conditional L-layer logic exists

**Missing layers:**
- L3 is never defined or applied — it is implied but absent
- No `context_selector` layer that feeds into policy decisions (it exists but is never called in the chat path)
- No frame/interaction-type classification layer before handler dispatch
- No layer that sets `turn_type` in `interpret_human_turn` return dict for the private_dev/local_demo path

---

## Section 3 — Current Routing Capability Table

| Class | Trigger | File | Path label | Deterministic | LLM | Public-safe |
|-------|---------|------|------------|---------------|-----|-------------|
| Entry/greeting | `"hey", "hi", "hello", "hallo", "yo", "sup", "start", "help"` | `response_expander.py` | `fallback_safe` → entry | Yes | No | Yes |
| System definition | `"what is weslr", "why was weslr created"` | `deterministic_handlers.py` | `system_definition_query` | Yes | No | Yes |
| Operator overview | `"show system overview"` | `deterministic_handlers.py` | `operator_overview` | Yes | No | Operator only |
| ISS probe registry | `"show iss probes"` | `deterministic_handlers.py` | `ISS_probe_registry_query` | Yes | No | Operator only |
| Diagnostics | `"show diagnostics"` | `deterministic_handlers.py` | `ISS_query_all` | Yes | No | Operator only |
| Proposals | `"show proposals"` | `deterministic_handlers.py` | `proposal_trace_query` | Yes | No | Operator only |
| Implementation plans | `"show plans"` | `deterministic_handlers.py` | `implementation_plan_query` | Yes | No | Operator only |
| Evidence/graph | `"show connections"` | `deterministic_handlers.py` | `graph_query` | Yes | No | Yes |
| Blocked write | Any write trigger in public_demo_readonly | `interpretation.py` | `blocked_write` | Yes | No | Yes |
| Rate limited | Over limit in public_demo_readonly | `interpretation.py` | `rate_limited` | Yes | No | Yes |
| Uncertainty/fallback | No handler matched | `interpretation.py` | `fallback_safe` | Yes | No | Yes |
| Evidence offer | `fallback_safe` + not entry phrase | `response_expander.py` | `fallback` (via `expand_response`) | Yes | No | Yes |

**No other handler classes exist in `deterministic_handlers.py`.** Inputs like "I want to learn to code", "can you help me build X", "explain Y" all fall to `fallback_safe`.

---

## Section 4 — Human Request Gap Analysis

**Why inputs like "I want to learn to code", "help me understand X", "can you explain Y" fall into fallback:**

**Immediate bug (pre-existing, partially fixed):**
- `interpret_human_turn` returns `latest_human` via `weslr_backend_contract.chat` with `turn_type: interpreted.get("turn_type", "question")` — but `interpret_human_turn` **never sets `turn_type` in its return dict** for the private_dev/local_demo path (section 3/3)
- Therefore `turn_type` defaults to `"question"` in `latest_human`
- In `build_communicator_message_payload`, the signal uncertainty override fires because:
  - `turn_type = "question"` (the default, not the actual type)
  - `_compute_context_selection("I want to learn to code")` → `"uncertain"` (no keywords)
  - `_compute_boundary_hints` → `["unknown"]`
  - Message is short (24 chars)
  - Result: `reply_shape = "signal_uncertainty_strong"` → message overwritten

**Root structural cause:**
- The system has **no help/intent frame** in `deterministic_handlers.py`
- Verbs like "learn", "understand", "explain", "help me", "can you help" have no trigger entries
- These inputs are functional conversational turns, not questions, not greetings, not system commands
- They represent a genuine user intent that deserves a real response, not an evidence offer or uncertainty signal

**Classification gap:**
- `interpret_human_turn` calls `dispatch_deterministic_handler` first — if no handler matches, it goes straight to `_build_safe_response` fallback
- There is **no pre-classification step** that could route "I want to learn X" to a help/explanation path before falling back
- The `classify_human_turn()` function exists but is **only called inside `build_communicator_message_payload`**, not in the initial interpretation flow

**Backend override issue:**
- Even when `expand_response` correctly produces a structured response (e.g., evidence offer from fallback guidance), `build_communicator_message_payload` can overwrite it with `signal_uncertainty_strong_response`
- This is the same root cause as the entry greeting bug — `turn_type` is not properly propagated from `interpret_human_turn`

---

## Section 5 — Recommended Interaction Control Plane Fit

**Where it fits in the existing architecture:**

```
Input
  → [EXISTING] public/safety boundary (write handlers, rate limit in interpretation.py)
  → [NEW] interaction frame detection [BEFORE dispatch, in interpretation.py]
  → [EXISTING] deterministic handler dispatch [deterministic_handlers.py]
  → [EXISTING] policy_engine + expand_response [omnichat layer]
  → [EXISTING] backend reply construction [weslr_backend_contract → dialogue.py]
  → [EXISTING] signal capture [website_signal_integration.py]
```

**Recommended frame set (fits existing structure):**

| Frame | Detection | Response contract | Handler path |
|-------|-----------|-----------------|-------------|
| `entry` | `_is_entry_phrase()` in `response_expander.py` | `_entry_greeting()` | `deterministic_entry` (short-circuit) |
| `system` | Trigger prefix in `deterministic_handlers.py` | Structured answer | `system_definition_query`, etc. |
| `explanation` | New: messages starting with "explain", "what is", "how does" | Structured answer + evidence offer | New: `explanation_query` |
| `exploration` | New: messages with topic nouns without action verbs | Evidence/graph offer | New: `exploration_query` |
| `task_help` | New: "I want to", "help me", "can you help me build", "teach me" | Structured help offer | New: `task_help_query` |
| `evidence_seeking` | New: "show me evidence", "what did you find" | Evidence response | `graph_query` (existing) |
| `restricted` | Write handlers + blocked_write path | Blocked message | `blocked_write` (existing) |
| `unknown` | No match | Evidence offer or uncertainty | `fallback_safe` (existing) |

**Implementation location:**
- Frame detection: add `_classify_interaction_frame()` in `interpretation.py`, call before `dispatch_deterministic_handler`
- Set `turn_type` and `reply_shape` in `interpret_human_turn` return dict for all paths (fills the current propagation gap)
- New deterministic handlers for `explanation_query`, `task_help_query` in `deterministic_handlers.py`
- Response text for new frames: natural paragraphs in `response_expander.py` `_CAPABILITY_MAP`
- The `turn_type` field is the correct carrier — it already controls the signal uncertainty override in `build_communicator_message_payload`

**What does NOT fit this architecture:**
- Value inference / pressure patterns — these belong to the observation pipeline, not the chat path
- LLM-based classification — `interpret_human_turn` and handlers are purely deterministic
- Prompt mutation — forbidden by WESLR_TIMELINE_SESSION_BOUNDARY_V1

---

## Section 6 — Evolvability Boundaries

**What can evolve later safely:**
- Response contract parameters (wording of guidance paragraphs)
- Frame confidence thresholds (can add probabilistic scoring later)
- New suggested frames via handler registration
- Fallback-to-frame routing improvements (handler additions)
- Evidence/graph depth parameters
- Capability descriptions in `_CAPABILITY_MAP`

**What must NOT evolve automatically:**
- Safety boundaries (`_FORBIDDEN_FIELDS`, write handler guards)
- Public mode rules (read-only enforcement in `interpretation.py`)
- Write permissions (controlled by `_is_public_demo_readonly()`)
- Prompt mutation (WESLR_TIMELINE_SESSION_BOUNDARY_V1 hard constraint)
- Signal storage rules (append-only, no feedback loops)
- Value inference (WESLR_VALUE_EMERGENCE_DOCTRINE_V1 — Layer 4 only, operator-authorized)
- `turn_type = "greeting"` shortcut logic (must remain deterministic)

---

## Section 7 — Minimal Safe Implementation Plan

**Do not implement. This is the proposal only.**

**Smallest safe next step — fill the `turn_type` propagation gap:**

| Item | Detail |
|------|--------|
| **Why** | `interpret_human_turn` never sets `turn_type` in its return dict for the private_dev/local_demo path. This causes `build_communicator_message_payload` to always use the default `"question"`, firing the signal uncertainty override incorrectly on fallback responses. |
| **Files to modify** | `interpretation.py` |
| **Change** | In `_build_safe_response()`, add `turn_type` and `reply_shape` fields to the returned dict. For `path=fallback_safe`: `turn_type="confusion"`, `reply_shape="answer_directly"`. This prevents signal uncertainty from firing on fallback (since `turn_type` will be `"confusion"`, which IS in the exclusion list). |
| **Tests** | `test_backend_entry_chat_path_v1.py` already covers entry. Add: `chat("I want to learn to code")` → reply contains evidence offer, not uncertainty. `chat("explain WESLR")` → not uncertainty. |
| **Migration risk** | Low — adds fields to existing return dict, no behavior removed |
| **Rollback** | Single-line revert in `interpretation.py` |
| **Preserves current behavior** | Yes — entry greeting is already short-circuit. Other handlers unchanged. |

**Second safe step — add task_help frame:**

| Item | Detail |
|------|--------|
| **Files to modify** | `deterministic_handlers.py` (register new triggers), `response_expander.py` (`_CAPABILITY_MAP` entry) |
| **Change** | Add trigger entries for `"I want to ", "help me ", "teach me "`, `"can you help me"` → path `task_help_query` |
| **Tests** | New test file: `test_task_help_frame_v1.py` |
| **Migration risk** | Low — purely additive, no existing behavior changed |
| **Rollback** | Remove trigger entries from `deterministic_handlers.py` |

---

## Section 8 — Risks / Blockers

| Risk | Severity | Mitigation |
|------|----------|------------|
| `turn_type` propagation gap causes signal uncertainty to fire on legitimate help responses | High — user-visible bad responses | Fix `interpretation.py` `_build_safe_response` to include `turn_type` |
| No classification layer before dispatch — all unrecognized inputs go to fallback | Medium — limits evolvability | Add `_classify_interaction_frame()` before dispatch, but only after `turn_type` propagation is fixed |
| `expand_response` entry check happens in `response_expander.py` but entry short-circuit is in `weslr_backend_contract` — two different locations | Low — already working but fragile | Consolidate entry detection into `interpret_human_turn` return dict via `turn_type="greeting"` |
| L3 layer never implemented — `policy_engine` always returns `L1/L2/L4` | Informational — no current bug, but means the layer system is incomplete | Design L3 purpose before implementing |
| `context_selector.py` exists but is never called in the chat path | Informational — graph context not yet integrated into chat | Require explicit handler trigger to activate, not automatic |

---

## Section 9 — Verdict

**WESLR_INTERACTION_CONTROL_PLANE_GROUNDING_AUDIT_COMPLETE**

The existing architecture has a solid foundation: deterministic handlers, policy engine, response expander, and signal capture are all in place. The primary gap is **not missing infrastructure** — it is **missing `turn_type` propagation** from `interpret_human_turn`, which causes the signal uncertainty override in `build_communicator_message_payload` to fire incorrectly on fallback responses.

The Interaction Control Plane concept fits naturally into the existing flow: interaction frames map cleanly onto `turn_type` values, frame detection belongs before handler dispatch in `interpretation.py`, and the existing policy/expander stack handles response construction. No new layers are required — the existing L1/L2/L4 naming in `policy_engine` is cosmetic only.

The evolvability boundary is well-defined: safety boundaries, write permissions, prompt mutation, and signal storage rules are off-limits for automatic evolution. Everything else can grow incrementally via handler registration and response text updates.
