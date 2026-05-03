# WESLR_JARVIS_ROADMAP_V1.md

**Author:** OCC (self-assessment + code verification)
**Date:** 2026-05-03
**Status:** Active — operator review required

---

## Part 1 — What WESLR Claims Is Implemented

Self-reported via internal analysis modules:

| Capability | WESLR's Claim | Source |
|---|---|---|
| Composite analysis | Live — 4 sources, 240 public signals, 31 contract observations | `build_composite_summary()` |
| Artificial Analysis Index (AAI) | Live — 309 items across levels 0–3 | `build_attention_summary()` |
| Fact extraction & storage | Live — 10 deterministic patterns, append/load functions | Phase 1 commit `047e173` |
| Project registry | Live — `register_project`, `list_projects`, `set_active_project` | Phase 2 commit `047e173` |
| Relational query arbiter | Live — routes `relational_query` to `fact_engine` layer | Phase 3 commit `f9fd0c9` |
| Fact query bridge | Live — `query_facts`, `load_facts`, scoped by project | `fact_query_bridge.py` |
| Entity timeline memory | Live — per-entity event timelines, keyword scanning | Commit `2020933` |
| Proactive suggestions | Live — theme detection from recent summaries, read-only | `proactive_suggestions.py` |
| Experiment proposal generator | Live — dry-run mode, wired to workplace bridge | Commit `3a78247` |
| Workplace chat bridge | Live — `/workplace`, pending experiments, ideas | `workplace_chat_bridge.py` |
| State-grounded dialogue | Live — but only for pre-classified question types | `state_grounded_dialogue.py` |
| Voice I/O (gateway) | Phase 1A shim — STT via whisper.cpp, TTS via browser Web Speech API | `voice_gateway.py` |
| Continuous voice session | Live — WebSocket, per-turn logging | `voice_gateway.py` |
| Evidence pipeline | Live — search insight proposals, governed approval | `evidence_pipeline.py` |
| Contract observation | Live — 31 observations logged | AAI composite |

### State-Grounded Dialogue — What It Does NOT Answer

WESLR's `state_grounded_dialogue.py` only responds to pre-classified patterns:
- `implemented_reality` / `what is implemented`
- `attention_summary` / `what needs attention`
- `composite_summary` / `what does composite say`
- `architecture_boundary` / `what is your architecture`
- `unsafe_automation` / `what should not be automated`
- `pending_reviews` / `what is blocking`

**It returns "not a recognized state question" for every Jarvis-capability question asked in the prompt:**
- "What voice I/O capabilities are implemented?" → ❌ not recognized
- "What persistent memory exists across sessions?" → ❌ not recognized
- "What proactive suggestion delivery mechanisms are live?" → ❌ not recognized
- "What action stubs (reminders, todo) are implemented?" → ❌ not recognized
- "What temporal+relational query capabilities exist?" → ❌ not recognized
- "What semantic similarity for node matching is active?" → ❌ not recognized

This is itself a gap — the self-introspection surface is incomplete.

---

## Part 2 — Code Verification: What Is Actually Missing

### Voice I/O

| Component | Status | Notes |
|---|---|---|
| STT (whisper.cpp) | **Installed** ✅ | Binary: `/data/data/com.termux/files/home/whisper.cpp/build/bin/whisper-cli` |
| STT model (ggml-base) | **Installed** ✅ | Model: `/data/data/com.termux/files/home/whisper.cpp/models/ggml-base.bin` |
| TTS (server-side) | **Missing** ❌ | Only browser Web Speech API — no server-side TTS |
| Voice output handler (`voice_output.py`) | **Missing** ❌ | No dedicated module |
| TTS handler (`tts_handler.py`) | **Missing** ❌ | No dedicated module |
| Voice session persistence | **Shim** ⚠️ | `timeline_id` hardcoded to `tl_default`; no multi-user session routing |
| Proactive voice delivery | **Missing** ❌ | No mechanism to speak without a user turn |

### Persistent Memory Across Sessions

| Component | Status | Notes |
|---|---|---|
| Session memory (daily notes) | **Live** ✅ | `memory/YYYY-MM-DD.md` files |
| Long-term memory (MEMORY.md) | **Live** ✅ | Curated memories, loaded in main session |
| Entity timeline memory | **Live** ✅ | `entity_timeline_memory.py`, per-entity `.weslr/timelines/` |
| User timeline memory | **Live** ✅ | `user_timeline_memory.py`, session summaries |
| Cross-session continuity module | **Live** ✅ | `continuity.py`, `continuity_consolidation.py` |
| Continuity note chat bridge | **Live** ✅ | `continuity_note_chat_bridge.py` |
| **Memory persistence across voice sessions** | **Gap** ⚠️ | Voice gateway hardcodes `tl_default`; no per-user timeline routing |

### Proactive Suggestion Delivery

| Component | Status | Notes |
|---|---|---|
| Suggestion generation (theme-based) | **Live** ✅ | `proactive_suggestions.py` |
| Workplace bridge integration | **Live** ✅ | Suggestion section in workplace response |
| Experiment proposal generator | **Live** ✅ | Dry-run, wired to workplace bridge |
| **Proactive daemon** (`proactive_deamon.py`) | **Missing** ❌ | No background suggestion delivery loop |
| **Cron/scheduled suggestion delivery** | **Missing** ❌ | No `cron_handler.py` |
| **Notification delivery** | **Missing** ❌ | No `notification_delivery.py` |
| **Operator-initiated proactive push** | **Missing** ❌ | Suggestions only appear when user asks `/workplace` |

### Action Stubs (Reminders, Todos)

| Component | Status | Notes |
|---|---|---|
| `proactive_suggestions.py` | **Live** ✅ | Read-only suggestion, no scheduling |
| `experiment_proposal_store.py` | **Live** ✅ | Stores proposals, requires operator approval |
| `signal_alerting.py` | **Live** ✅ | Alert signals, but not reminder scheduling |
| **Reminder handler** (`reminder_handler.py`) | **Missing** ❌ | No `/remind me in 20 minutes` |
| **Todo handler** (`todo_handler.py`) | **Missing** ❌ | No `/todo add` or task tracking |
| **Cron job scheduling** | **Gap** ⚠️ | OpenClaw `cron` tool exists; no WESLR-native reminder abstraction |
| **Background job persistence** | **Unknown** ❌ | No `weslr_jobs.jsonl` or similar |

### Temporal + Relational Query Capabilities

| Component | Status | Notes |
|---|---|---|
| Fact extraction (temporal patterns) | **Live** ✅ | 10 patterns including `since_X`, `until_Y`, `next_Z` |
| Fact storage | **Live** ✅ | `.weslr/fact_assertions.jsonl` |
| Project-scoped facts | **Live** ✅ | Phase 2 registry + scoping |
| Relational query arbiter | **Live** ✅ | Phase 3 — routes `relational_query` to `fact_engine` |
| Entity timeline memory (temporal events) | **Live** ✅ | Per-entity event timelines |
| **Semantic similarity for node matching** | **Spec-only** ⚠️ | Doctrine P11 exists; `multi_graph_traversal.py` uses deterministic keyword matching only |
| **Graph similarity search** | **Missing** ❌ | No vector embeddings, no ANN index, no semantic search |
| **Temporal reasoning beyond pattern matching** | **Missing** ❌ | Only regex pattern extraction; no date arithmetic, no timeline projection |

### Semantic Similarity for Node Matching

| Component | Status | Notes |
|---|---|---|
| Doctrine P11 | **Added** ✅ | Committed in `dd1117a` |
| `multi_graph_traversal.py` | **Live** ✅ | Keyword-based traversal only |
| Vector/semantic similarity | **Missing** ❌ | No `sentence_transformers`, no embeddings |
| Automatable similarity (doctrine claim) | **Not implemented** ❌ | No similarity function exists in `fact_query_bridge` |

---

## Part 3 — Gap Analysis Table

Sorted by AAI attention level (L3 = most urgent).

| Gap | Effort | Risk | AAI Level | Notes |
|---|---|---|---|---|
| State-grounded questions not recognized | Low | Low | L3 (1 item — pattern weak entry repetition) | Add regex patterns to `state_grounded_dialogue.py`; 15-line change |
| Voice session hardcoded to `tl_default` | Low | Medium | L2 | Voice gateway `timeline_id` needs session/user routing |
| Proactive suggestion daemon (`proactive_deamon.py`) | Medium | Medium | L2 | Background loop; needs governance guard |
| Reminder handler (`reminder_handler.py`) | Medium | Medium | L2 | Operator-facing; requires cron integration |
| Todo handler (`todo_handler.py`) | Medium | Medium | L2 | Same as reminder — shared pattern |
| Server-side TTS (`tts_handler.py`) | Medium | Medium | L2 | TIA context: may want voice output for Windows plugin |
| Semantic similarity / node matching | High | Low | L2 | Doctrine P11 exists; implementation is complex (embeddings, ANN) |
| Multi-user voice session routing | Medium | High | L1 | Timeline collision risk if multiple users |
| Continuous proactive push delivery | High | High | L1 | No notification channel established |
| Graph similarity search (beyond keyword) | High | Low | L1 | Low risk; high effort; low urgency |

---

## Part 4 — Recommended Next Step

**Single smallest highest-feel action:**

### Add reminder handler (`reminder_handler.py`) + wire to state-grounded dialogue

**Why:** The user has an OpenClaw `cron` tool already. A WESLR-native reminder abstraction that wraps the cron tool would let operators say "remind me in 20 minutes" and have WESLR set a timed job — without WESLR running its own background loop. This is low-risk (uses existing infrastructure), high-visibility (user immediately sees value), and small (one new file ~100 lines).

**What it looks like:**
```python
# weslr/reminder_handler.py
# set_reminder(message, delay_minutes, session_id) → creates a cron job
# list_reminders(session_id) → reads from .weslr/reminders.jsonl
# cancel_reminder(reminder_id, session_id) → updates JSONL (archive, not delete)
```

**Governance confirmation:**
- No raw prompt storage ✅
- No hidden learning ✅
- No automatic action without cron trigger ✅
- Uses existing OpenClaw cron infrastructure (no new background loops) ✅
- Read-only state-grounded additions (pattern updates only) ✅

---

## Part 5 — Governance Notes

All constraints from prior sessions remain in force:

| Constraint | Status |
|---|---|
| No raw prompts stored | ✅ Confirmed — `raw_prompt_stored: false` on all new modules |
| No hidden learning | ✅ Confirmed — `hidden_learning: false` on all new modules |
| No automatic writes | ✅ Confirmed — `automatic_action: false` on all new modules |
| No Ollama / execution | ✅ Confirmed — no exec in any Phase 1–3 modules |
| No TIA bridge in public repo | ✅ Confirmed — private repo only |

---

## Appendix — AAI Attention Snapshot

```
Level 0: 31 items (suppressed — noise)
Level 1: 276 items (tracked)
Level 2: 1 item (proposal-ready)
Level 3: 1 item (escalated) — "pattern_weak_entry_repetition"
  → suggest reviewing contract observation logging frequency
```

No Level 4 (critical) items. No safety or governance violations flagged.