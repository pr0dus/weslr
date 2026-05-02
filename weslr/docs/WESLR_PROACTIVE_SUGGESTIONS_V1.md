# WESLR_PROACTIVE_SUGGESTIONS_V1

**File:** `weslr/proactive_suggestions.py`
**Test:** `weslr/tests/test_proactive_suggestions_v1.py`
**Status:** `IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT`
**Authority:** `suggestion_only`

---

## Purpose

First safe Jarvis-like proactive suggestion experiment for WESLR.

WESLR generates one optional, helpful next-step suggestion based on recent user timeline summaries and known capability themes. This is **not** unprompted background delivery — it's a read-only suggestion builder that can later be surfaced via chat or voice.

---

## What It Does

- Reads recent user timeline summaries via `load_recent_session_summaries()`
- Classifies each summary's theme (continuity, evidence, capability_discovery, experiment, governance)
- Picks the highest-confidence theme
- Returns one optional, safe next-step suggestion

---

## What It Does NOT Do

- ❌ No unprompted delivery
- ❌ No background loop or cron job
- ❌ No notification or reminder creation
- ❌ No action execution
- ❌ No writes (no JSONL, no memory writes)
- ❌ No Ollama or external calls
- ❌ No hidden learning
- ❌ No raw prompt storage
- ❌ No /chat integration

---

## Core Functions

| Function | Description |
|---|---|
| `classify_timeline_theme(summary_text)` | Detects theme from keywords — returns theme, confidence, matched_terms |
| `build_suggestion_from_theme(theme)` | Maps theme to pre-defined safe suggestion dict |
| `build_proactive_suggestion(user_id, base_dir)` | Main entry point — returns full suggestion result dict |

---

## Theme → Suggestion Map

| Theme | Suggestion | Approval Required |
|---|---|---|
| `continuity` | Test the continuity note bridge | No |
| `evidence` | Run a source-quality check with /evidence | No |
| `capability_discovery` | Explore what WESLR capabilities are available | No |
| `experiment` | Define one small concrete experiment | No |
| `governance` | Review governance boundaries and REPO_GUARD | **Yes** |
| `unknown` | No suggestion returned | — |

---

## Output Schema

```json
{
  "record_type": "proactive_suggestion_v1",
  "user_id": "arthur",
  "suggestion_available": true,
  "suggestion": "You could test the continuity note bridge to confirm WESLR recalls your recent session correctly.",
  "reason": "Your recent sessions involved continuity and memory experiments.",
  "related_capability": "continuity_note_chat_bridge",
  "source": "user_timeline_memory",
  "authority": "suggestion_only",
  "automatic_action": false,
  "operator_approval_required": false,
  "hidden_learning": false,
  "raw_prompt_stored": false
}
```

---

## Rules (Strict)

1. Suggestion always phrased as optional: "You could...", "Would you like to..."
2. Never says "I will do this"
3. Never executes or writes anything
4. `governance` theme sets `operator_approval_required: true`
5. All other metadata fields always `false`

---

## Future Roadmap

- **Chat surfacing**: integrate via `proactive_surface.py` into staging runtime
- **Voice surfacing**: surface suggestions via voice gateway
- **Cooldown**: prevent repeated same suggestion within N hours
- **Operator-only mode**: surface to operator only, not general users
- **Multi-suggestion**: rank and return top-N suggestions

---

## Experiments Not Yet Wired

This module is complete and tested but NOT wired into:
- `/chat` — no automatic suggestion surfacing
- heartbeat — no periodic proactive check
- voice gateway — no voice surfacing
- cron — no scheduled suggestion generation

All future wiring requires explicit operator approval.