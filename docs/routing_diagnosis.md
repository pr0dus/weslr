# WESLR Routing Diagnosis — Meaning Vector Integration

**Date:** 2026-05-07
**Status:** Resolved

---

## Problem

Clear relational/memory messages — "I am new here", "do you know me?", "what do you remember?" — were falling into `signal_uncertainty_strong` and returning the generic fallback:

```
"Couldn't form a response on the task at hand."
```

The meaning-vector response obligation layer existed in `dialogue.py` Part 4 but was never being reached for chat-mode messages.

---

## Root Cause

The chat-mode ingress path was:

```
local_bridge.py --text "message"
  → ingress_adapter.route_request(raw)
    → handle_request(normalized, persona=, domain=)
      → respond_chat(message, chat_context, chat_hints)
        → _model_chat_response(message)
          → generate_chat(message, context)
            → FallbackProvider.generate()
              → "Couldn't form a response on the task at hand."
```

`dialogue.py` Part 4 meaning-vector logic (lines 2281–2297) only activates when `reply_shape in ("signal_uncertainty", "signal_uncertainty_strong")`. But for chat-mode requests, `handle_request` dispatches directly to `respond_chat()` — it never reaches the reply_shape classification logic in `dialogue.py`.

**Structural gap:** `dialogue.py` is the canonical WESLR communicator layer, but chat-mode requests from `local_bridge` short-circuit through `handle_request → respond_chat` and completely bypass the meaning-vector Part 4 integration point.

---

## Resolution

Added meaning-vector integration at the last safe choke point before LLM-dependent generation:

**File:** `weslr/chat_responder.py`
**Location:** `respond_chat()` method, just before the call to `_model_chat_response()`
**Change:** 24-line insertion that tries the meaning-vector path before falling through to model-backed generation.

```python
# ── Meaning-vector response obligation ───────────────────────────────
try:
    from weslr.linguistic_meaning import analyze_meaning
    from weslr.response_obligation import determine_response_obligation
    from weslr.meaning_state_context import gather_meaning_state
    from weslr.meaning_response import form_meaning_response

    test_metadata = {}
    mv = analyze_meaning(message)
    ob = determine_response_obligation(mv, {}, test_metadata, None)
    if ob.confidence >= 0.45 and ob.obligation_type != "fallback_uncertainty":
        ctx = gather_meaning_state(ob, {}, test_metadata, None, None)
        result = form_meaning_response(mv, ob, ctx)
        if result and result.confidence >= 0.40:
            reply_meta = {
                "path": f"meaning-vector:{ob.obligation_type}:{result.selected_candidate_type.lower()}",
                "obligation_type": ob.obligation_type,
                "candidate_type": result.selected_candidate_type,
                "llm_used": False,
                "fallback_used": False,
                "source": "meaning_vector_response_obligation",
            }
            return result.content, reply_meta
except Exception:
    pass  # fall through to model-backed path

# Prefer model-backed response; if unavailable, surface error
return self._model_chat_response(message or "")
```

**Activation conditions:**
- `ob.confidence >= 0.45` — meaning signal must be strong enough
- `ob.obligation_type != "fallback_uncertainty"` — must be a genuine obligation
- `result.confidence >= 0.40` — candidate must be grounded enough

If any condition fails, falls through to `_model_chat_response()` → LLM as designed.

---

## Smoke Verification

| Message | Before | After |
|---|---|---|
| `"I am new here"` | "Couldn't form a response..." | "I'm Weslr — an entity intelligence system. I can track identity, memory, and continuity, but right now I don't have a verified identity for you. Introduce yourself and I'll note it." |
| `"have we met before?"` | "Couldn't form a response..." | "I don't have a verified identity for you in this session. I can only work with what I can confirm — right now, I can't confirm who you are yet." |
| `"do you recognize me?"` | "Couldn't form a response..." | "I don't have a verified identity for you in this session..." |
| `"what did we work on last time?"` | "Couldn't form a response..." | "From my side: Memory file: 2026-05-06-weslr-voice-options.md..." |
| `"what kind of system are you?"` | "Couldn't form a response..." | "IDENTITY.md: # IDENTITY.md - Who Am I?..." |

No `signal_uncertainty_strong`. No generic uncertainty. LLM not called for any of these.

---

## New Files Added

| File | Purpose |
|---|---|
| `weslr/linguistic_meaning.py` | Weighted meaning vector from raw text |
| `weslr/response_obligation.py` | Response obligation classifier |
| `weslr/meaning_state_context.py` | Obligation-driven state gathering |
| `weslr/meaning_response.py` | Candidate formation and ranking |
| `weslr/test_meaning_vector_response_obligation.py` | Test suite |

---

## Architecture

```
raw text
  ↓
analyze_meaning()          [linguistic_meaning.py]
  → MeaningVector (speech_act_scores, relational_scores, state_query_scores, ...)
  ↓
determine_response_obligation()  [response_obligation.py]
  → ResponseObligation (obligation_type, required_state, disclosure_level, ...)
  ↓
gather_meaning_state()      [meaning_state_context.py]
  → MeaningStateContext (sender_identity, memory_summary, self_model_summary, ...)
  ↓
form_meaning_response()     [meaning_response.py]
  → MeaningResponseResult (content, candidate_type, confidence, ...)
```

Candidate types: `NEW_CONTACT_ORIENTATION`, `VERIFIED_CONTACT_ORIENTATION`, `IDENTITY_VERIFICATION`, `MEMORY_STATE_REPORT`, `SELF_MODEL_DESCRIPTION`, `CAPABILITY_ORIENTATION`, `CLARIFYING_QUESTION`, `BOUNDED_UNCERTAINTY`