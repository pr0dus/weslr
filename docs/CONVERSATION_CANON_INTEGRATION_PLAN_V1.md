# CONVERSATION_CANON_INTEGRATION_PLAN_V1.md

**Status:** Design — not implemented
**Author:** Weslr self-inspection
**Date:** 2026-04-21
**Authoritative Context:** human-expression inspection result, docs/WESLR_CANONICAL_SELF_MODEL_V1.md, canonical self-improvement spine, surface integration model, thread/relevance/suggestion/artifact/bridge canons

---

## PURPOSE

A new conversation layer would be a third parallel system on top of the two already existing (main dialogue pipeline + speak/chat_ui). That is doctrinally weaker, not stronger:

- Parallel systems accumulate divergence over time
- Governance becomes harder to apply across 3 channels instead of 1
- Maintenance cost grows without adding capability
- Operator sees three different response styles for the same input

Integration into existing canonical paths is doctrinally stronger because it:

- Uses existing tested surfaces instead of building new ones
- Centralizes governance on one path instead of fragmenting it
- Builds on proven infrastructure (dialogue.py, language modules, ExplanationSession)
- Preserves all existing capability while closing the gaps

The goal is not a new conversation engine. The goal is one coherent conversational flow using what already exists.

---

## CURRENT CANONICAL PATH

### Primary Path (must use)

`dialogue.build_communicator_message_payload()` → signal classification → need routing → handler functions → language modules → outward message

This is the single authoritative path for all human communication.

### Handler functions in dialogue.py

| Function | Need type handled |
|---|---|
| `_artifact_fallback_answer()` | evidence / safety / governance / term-clarification / plain-language |
| `_artifact_proposal_answer()` | proposal intent with research_context |
| `_artifact_proposal_answer_from_question()` | proposal intent without research_context |
| `synthesize_concept_or_self_reply()` | concept_explanation / self_report |
| `_teach_artifact()` | artifact teaching (beginner/student/technical/seminar) |
| `generate_from_self_state()` | self-state driven outward message |

### Language modules (languages/en.py, languages/de.py)

All outward messages pass through language modules for translation and phrasing.

### Adaptive presentation layer (weslr/explanation_responder.py)

`ExplanationSession` applies presentation knobs (depth, technicality, pacing, directness, structure_looseness, uncertainty_plain) without changing truth or governance.

---

## PARALLEL / NON-CANONICAL PATHS

### chat_ui.py → speak.py (MUST BE INTEGRATED)

`chat_ui.py` exposes a web chat UI. On message, it calls `weslr_cli.handle_speak()` which runs `commands/speak.py` as a subprocess. `speak.py` produces responses from hardcoded pattern matching, not from `dialogue.py`.

This is a second conversation channel that bypasses the canonical path entirely.

**Problem:** Same input to web UI produces different output than same input to the main system.

**Solution:** Route chat_ui through `dialogue.build_communicator_message_payload()` instead of through `speak.py`.

### commands/speak.py (MUST BE DEPRECATED as primary chat path)

Standalone CLI chat with hardcoded tax Q&A patterns. Not integrated with need routing. Its responses come from local pattern matching, not from the canonical dialogue pipeline.

**Note:** Tax knowledge functions (`answer_entfernungspauschale_question`, `search_weslr_web`) in `speak.py` should be preserved as callable utilities. The chat wrapper around them is what must be redirected.

### weslr/cognitive_dialogue.py (MUST BE WIRED or DEPRECATED)

Structs for inadequacy explanation and operator response handling exist but are not wired into the main flow or the proposal workflow.

**Decision needed before Phase 1:** Wire it into dialogue.py/proposal workflow, or mark as experimental and exclude from canonical path.

---

## MINIMAL INTEGRATION PRIORITIES

### Priority 1 — Unify chat_ui with dialogue.py

Route web chat messages through `dialogue.build_communicator_message_payload()` instead of `speak.py`. Preserve the HTTP API contract (reply + meta + status) but swap the backend.

This eliminates the parallel channel without changing what operators see.

### Priority 2 — Minimal conversation session state

Add a small in-memory store in `dialogue.py` for session-level conversation context:

- `recent_turns`: last N (message, response) pairs — for multi-turn memory
- `current_topic`: string — for topic drift detection
- `explanation_level`: string (beginner/student/technical/seminar) — persists across turns
- `detected_preferences`: dict — concise, technical, etc.

This does not require new storage files. It is session-scoped only. It enables "as I mentioned earlier..." and topic continuity without a new system.

### Priority 3 — Clarification request behavior

In `interpret_human_turn()`, add detection for ambiguous input:

- "what do you mean" / "I don't understand" / incomplete question / multiple interpretations possible

When detected, route to a handler that produces one clarifying question instead of an answer. This fills the gap in the inspection's Section 5 item 2.

This does not change any artifact, proposal, or governance behavior. It only adds a new response mode for ambiguous input.

### Priority 4 — Correction acknowledgment behavior

In `interpret_human_turn()`, detect correction patterns:

- "actually" / "I meant" / "no, that's wrong" / "not X, Y"

When detected, prepend a brief acknowledgment ("Got it — working from the corrected version") before processing the corrected input. This fills inspection Section 5 item 3.

No state change, no governance change, no routing change. Only acknowledgment text.

### Priority 5 — Topic continuity via thread tracker

When topic drift is detected, call `thread_tracker.create_thread()` for the previous topic automatically (operator_triggered=True). When operator returns to a previous topic, surface prior thread items as context.

This uses existing canonical storage (thread_tracker) without creating new infrastructure.

### Priority 6 — Connect ExplanationSession to conversation state

After each operator response, scan for confusion signals (immediate "what do you mean" / "I don't follow") or boredom signals (short responses, topic shifts). Adjust `ExplanationSession` depth knob accordingly for the next response.

This is wiring existing knobs to conversation feedback, not a new surface.

### Priority 7 — Proposal refinement loop

Extend `handle_chat_intent()` in `self_improvement_chat.py` to accept refinement input:

- "make this clearer" / "what if we tried X" / "can you simplify the risk section"

Instead of only approve/deny/apply, add a `refine` intent that passes operator input back to the proposal for modification before final decision.

### Priority 8 — Operator preference persistence

Store detected preferences (concise, technical, verbose, language) in `communicator_self.json` instead of only in-memory. On session start, load preferences and apply them to `ExplanationSession` before first response.

This requires a write on session end and a read on session start. All existing storage infrastructure.

---

## WHAT MUST STAY PRESERVED

The following are canonical and must not be modified, degraded, or bypassed by this integration:

- **Artifact system** — all artifact creation, evaluation, scoring, and explanation surfaces
- **Proposal system** — create / review / approve / deny / apply workflow with governance
- **Thread tracker** — storage layer, thread creation, item linking
- **Relevance surface** — read-only advisory scoring; does not influence routing
- **Suggestion surfaces** — suggestion_box, suggestion_bridge, surface_to_spine_bridge
- **Self-improvement spine** — observation → proposal → review → approval → apply → evidence logging
- **Governance rules** — all ExecutionGate checks, operator-only actions, approval requirements
- **Existing dialogue capabilities** — all 6 need types and their handlers in dialogue.py
- **Language modules** — translation and outward message generation
- **ExplanationSession** — presentation adaptation; truth and governance preserved

---

## WHAT MUST NOT HAPPEN

Explicitly forbidden by this design:

1. **No new conversation engine** — do not create a new conversational AI / chat module
2. **No bypassing dialogue.py** — all human communication must pass through the canonical path
3. **No third parallel UI/chat path** — chat_ui integration replaces the path, it does not add another
4. **No weakening of governance** — integration must not reduce operator approval requirements
5. **No degradation of artifact/proposal/suggestion functionality** — these are load-bearing for the system
6. **No automatic interest creation** — conversation context does not auto-create interests
7. **No automatic thread creation without operator trigger** — threads are created with operator_triggered=True
8. **No automatic proposal generation from conversation** — proposals come from the established proposal workflow only
9. **No changes to existing API contracts** — chat_ui integration preserves the existing HTTP API shape

---

## RECOMMENDED IMPLEMENTATION ORDER

### Phase 1 — Unify chat_ui (reversible, low risk)
- Route `chat_ui.py` → `dialogue.build_communicator_message_payload()` instead of `speak.py`
- Preserve HTTP API contract (reply + meta + status)
- Preserve tax knowledge utilities by calling them from dialogue.py handlers
- If broken: revert chat_ui to call speak.py as before

### Phase 2 — Minimal session state in dialogue.py (reversible, low risk)
- Add in-memory session context store (recent_turns, current_topic, explanation_level)
- Wire current_topic into thread_tracker auto-creation on topic drift
- If broken: session context is empty, system falls back to single-turn behavior

### Phase 3 — Clarification request behavior (reversible, moderate risk)
- Add ambiguous input detection in `interpret_human_turn()`
- Add clarification handler in dialogue.py
- Does not affect artifact/proposal/relevance surfaces
- If broken: clarification not triggered, normal answer flow continues

### Phase 4 — Correction acknowledgment behavior (reversible, low risk)
- Add correction pattern detection in `interpret_human_turn()`
- Prepend acknowledgment before normal processing
- If broken: acknowledgment not shown, normal flow continues

### Phase 5 — Connect ExplanationSession to conversation state (reversible, low risk)
- After each response, scan operator message for confusion/boredom signals
- Adjust depth knob for next response
- If broken: knob stays at previous value, no cascade failure

### Phase 6 — Proposal refinement loop (reversible, moderate risk)
- Extend `handle_chat_intent()` to handle refine intent
- Pass refinement to proposal for modification before decision
- If broken: refine intent falls back to deny, original proposal unchanged

### Phase 7 — Operator preference persistence (reversible, moderate risk)
- Write detected preferences to `communicator_self.json` on session end
- Read and apply on session start
- If broken: preferences not loaded, default ExplanationSession behavior

---

## FIRST IMPLEMENTATION SLICE

### Recommended: Phase 1 — Unify chat_ui with dialogue.py

**Justification:** This is the safest possible first slice because:

1. **Visible improvement with no new capability** — operators get canonical responses from web UI immediately
2. **Easy rollback** — one line change in chat_ui.py routes back to speak.py
3. **No new state** — no new files, no new storage, no new variables
4. **Isolated** — does not touch artifact system, proposal system, governance, or any other surface
5. **Confirms the pattern** — if this integration works cleanly, it validates that the other phases will too

**Implementation:**

In `chat_ui.py`, replace:

```python
from weslr_cli import weslr_speak
response = weslr_speak(message)
```

With:

```python
from dialogue import build_communicator_message_payload
from sim import load_communicator_state, load_communicator_self

state = load_communicator_state()
self_state = load_communicator_self()
result = build_communicator_message_payload(message, state, self_state)
response = result.get("message", {}).get("content", str(result))
```

Preserve `meta` and `status` response fields from the result dict.

Tax knowledge functions (`answer_entfernungspauschale_question`, `search_weslr_web`) are preserved by adding them as handlers in `dialogue.py` alongside the existing need-type handlers.

---

## STOP LINE

**Confirmed:**
- Design documentation only — no production code changes
- No behavior changes to any live system
- No new files created in weslr/, commands/, or dialogue.py
- No modifications to artifact, proposal, governance, or suggestion surfaces
- No test execution
- No state modifications
- No deployment actions

*This document exists to record the design decision. Implementation requires a separate authorization.*