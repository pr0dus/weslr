# WESLR Evidence Chat Bridge V1 — Implementation Checkpoint

**Date:** 2026-05-01
**Verdict:** `WESLR_EVIDENCE_CHAT_BRIDGE_V1_IMPLEMENTED_GUARDED_ENV_GATED`

---

## Summary

Evidence Chat Bridge V1 wires the external evidence pipeline into `/chat` through a small, bounded, guarded injection point in `main.py`. Search is controlled by the `WESLR_SEARXNG_ENABLED` environment variable and only activates on clearly-identified fallback responses.

---

## Implementation Details

### Module

- **File:** `weslr/evidence_chat_bridge.py`
- **Tests:** `test_evidence_chat_bridge_v1.py` — 19 passed
- **Function:** `maybe_answer_with_evidence(message, current_message) -> dict | None`

### Integration Point

**Location:** `main.py` — POST `/chat` handler, after payload is built and adaptive hints are applied, before `self.send_response(200)`.

```python
# ── Evidence Chat Bridge (Tier-A safe injection) ──────────────────
# Only activates when: search enabled, evidence_needed=true,
# current response is fallback/template, message is not self/system.
try:
    from weslr.evidence_chat_bridge import maybe_answer_with_evidence
    _bridge_result = maybe_answer_with_evidence(message, payload.get("message"))
    if _bridge_result:
        payload["message"] = _bridge_result["message"]
        payload["path"] = _bridge_result["path"]
        payload["response_contract"] = _bridge_result.get("response_contract")
        payload["_evidence_metadata"] = _bridge_result["evidence_metadata"]
except Exception:
    pass
```

### Evidence Chain Tests

| Component | Test File | Result |
|-----------|-----------|--------|
| External Evidence Pipeline V1 | test_evidence_pipeline_v1.py | 14 passed |
| Evidence Answer Builder V1 | test_evidence_answer_builder_v1.py | 23 passed |
| Evidence Packet Builder V1 | test_evidence_packet_builder_v1.py | 20 passed |
| SearXNG Search Adapter V1 | test_searxng_search_adapter_v1.py | 26 passed |
| Evidence Needed Detector V1 | test_evidence_needed_detector_v1.py | 27 passed |
| Evidence Chat Bridge V1 | test_evidence_chat_bridge_v1.py | 19 passed |
| **Total** | | **129 passed** |

---

## Activation Guards

All four must be true for the bridge to activate:

1. **`evidence_needed=true`** — from `classify_evidence_need(message)`
2. **`WESLR_SEARXNG_ENABLED=true`** — SearXNG adapter is enabled
3. **Message is NOT a self/system question** — questions like "what are you?", "what is WESLR?", "how do you work?" do not trigger search
4. **Current response contains a fallback signal** — only overrides responses that contain fallback templates like `"my current best answer is that..."`

### Self/System Patterns (never searched)

```
what are you, who are you, what is weslr, what's weslr,
how do you work, how are you, what can you do, what's your purpose,
describe yourself, tell me about yourself, are you conscious,
do you feel, are you aware
```

---

## Output Structure

When the bridge activates, it injects into `payload`:

```python
{
    "message": "...",                    # evidence-grounded answer text
    "path": "evidence_grounded_answer",  # routing path identifier
    "response_contract": "uncertainty_boundary",
    "_evidence_metadata": {
        "evidence_used": True,
        "authority": "external_evidence_unverified",
        "truth_status": "unverified",
        "automatic_truth_write": False,
        "source_count": 1,
        "source_urls": ["https://en.wikipedia.org/wiki/Entropy_(physics)"],
        "search_attempted": True,
        "classification": {...},
    }
}
```

---

## Constraints Enforced

| Constraint | Status |
|------------|--------|
| No JSONL writes | ✅ Read-only bridge |
| No memory writes | ✅ No artifact storage |
| No Ollama | ✅ No LLM calls in bridge |
| Search env-gated | ✅ `WESLR_SEARXNG_ENABLED=true` required |
| No /chat auto-override | ✅ Only activates on fallback template responses |
| Self/system questions protected | ✅ Never triggers search |
| deterministic self/system routes unchanged | ✅ All existing handlers run before bridge |

---

## Search Disabled Behavior

When `WESLR_SEARXNG_ENABLED=false` (default):
- Bridge returns `None` for all queries
- Current fallback message is NOT overridden
- No user-visible message is shown about search being disabled
- **Known limitation:** Could be improved with a clear "search is not enabled" message in a future iteration

---

## Not Yet Live-Tested

- ✅ Unit tests pass (129 total across evidence chain)
- ✅ `test_natural_self_conversation_v1.py` passes (8 checks)
- ✅ `self_test.py` passes
- ❌ Not yet live-tested via actual `/chat` call with `WESLR_SEARXNG_ENABLED=true` on OCW

---

## Verdict

**`WESLR_EVIDENCE_CHAT_BRIDGE_V1_IMPLEMENTED_GUARDED_ENV_GATED`**

Five-component evidence chain now accessible from `/chat` under guarded conditions. OCW can pull and live-test when ready.