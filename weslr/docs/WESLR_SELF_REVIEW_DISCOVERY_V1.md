# WESLR Proactive Self-Review Discovery V1

**Date:** 2026-05-04 18:45 GMT+2
**Session:** main:c03c2c7
**Purpose:** Capability discovery and design for WESLR proactive self-review daemon

---

## Goal

Determine whether WESLR now has enough internal structure for the proactive daemon to periodically inspect WESLR's own architecture/state and suggest improvements or gaps safely.

---

## What Exists Currently

### Proactive Daemon (Complete ✅)

| File | Path | Status |
|---|---|---|
| Proactive Daemon Loop | `weslr/proactive_daemon.py` | 199 lines ✅ |
| Manual Start/Stop | `proactive_daemon.py` | `start_proactive_daemon()` / `stop_proactive_daemon()` ✅ |
| Interval Config | `WESLR_PROACTIVE_INTERVAL_MINUTES=60` | env-configured ✅ |
| Deduplication | `_DEDUP_CACHE`, `_DEDUP_MAX=5`, `_DEDUP_TTL=24h` | 24h TTL ✅ |
| Queue Write | `pending_messages_queue` | `medium` priority queue ✅ |
| No automatic self-modification | doctrine safe | ✅ |

### WESLR Doctrine Layers (Accepted ✅)

| Phase | Status | File |
|---|---|---|
| Phase 6 Physical Reasoning | ✅ `accepted_doctrine` | `docs/WESLR_PHASE_6_PHYSICAL_MATH_REASONING_DOCTRINE_V1.md` |
| Phase 7 Hypothesis Workflow | ✅ `accepted_doctrine` | `docs/WESLR_PHASE_7_HYPOTHESIS_WORKFLOW_DOCTRINE_V1.md` |
| Phase 9 Advanced Reasoning | ✅ `accepted_doctrine` | `docs/WESLR_PHASE_9_ADVANCED_REASONING_DOCTRINE_V1.md` |
| Phase 10 Collaboration | ✅ `accepted_doctrine` | `docs/WESLR_PHASE_10_COLLABORATION_DOCTRINE_V1.md` |
| Observation Pipeline | ✅ `checkpoint` | `WESLR_OBSERVATION_CHECKPOINT_V1.md` |
| Proactive Daemon | ✅ `daemon` | `proactive_daemon.py` |

---

## What Is Missing (Design Phase)

| Component | Status | File |
|---|---|---|
| `run_once` mode | ❌ Not implemented | `proactive_daemon.py` |
| Manual tick control | ❌ Not implemented | | daemon only |
| Self-review source adapters | ❌ Not implemented | `self_review_adapter.py` (design) |
| Architecture gap detection | ❌ Not implemented | source adapters needed |
| Phase registry gap detection | ❌ Not implemented | | daemon only |
| Proposal store reader | ⚠️ Partial | `proposal_store.py` (partial) |
| `build_proactive_suggestion()` gap source | ❌ Not implemented | | only |
| Observation Pipeline checkpoint | ⚠️ Partial | | | only |
| Help/README drift detection | ❌ Not implemented | surface only |
| Contract proposal gap source | ❌ Not implemented | | surface only |

---

## SECTION 4 — SELF-REVIEW GAP ANALYSIS

| Question | Current Ability | Design Needed |
|---|---|---|
| Architecture gap detection | ❌ No | ✅ `source_adapters` |
| Unresolved validation gaps | ⚠️ Partial | ✅ Gap store reader |
| Phase registry omission detection | ❌ No | ✅ Phase registry reader |
| Help/README drift detection | ⚠️ Partial | ✅ Surface gap reader |
| Gap suggestion creation | ❌ No | ✅ `gap_detection` |
| Suggestion storage | ⚠️ Partial | ✅ `proposal_store` |
| Operator-only output | ⚠️ ✅ Yes | ✅ `proposal_review_lifecycle` |
| Automatic self-modification | ✅ Safe | ✅ Manual only |

**State: C — No self-review support yet, only generic proactive hints.**

---

## SECTION 5 — SAFE SELF-REVIEW MODEL

### What the Daemon May Do ✅

| Action | Safe Read |
|---|---|
| Read doctrine | `WESLR_DOCTRINE_REGISTRY_V1.md` ✅ |
| Read observation checkpoint | `WESLR_OBSERVATION_CHECKPOINT_V1.md` ✅ |
| Read proposal review records | `contract_proposal_review_log.jsonl` ✅ |
| Read validation gaps | `contract_insufficiency_log.jsonl` ✅ |
| Read signal observatory | `observatory.jsonl` ✅ |
| Read phase registry | `phase_registry.jsonl` ✅ |
| Read proposal store | `proposal_store.jsonl` ✅ |
| **Detect gaps** | phase gaps, stale doctrine, unresolved proposals ✅ |
| **Suggest next actions** | suggestions only ✅ |
| **Write pending messages** | `pending_messages.jsonl` only ✅ |

### What the Daemon May NOT Do ❌

| Action | Reason |
|---|---|
| Edit code | Violation of WESLR doctrine |
| Edit doctrine files | Violation of WESLR doctrine |
| Auto-commit | Violation of WESLR governance |
| Auto-push | Violation of WESLR governance |
| Change contracts | Violation of WESLR governance |
| Change memory/truth | Violation of WESLR doctrine |
| Approve proposals | Operator-only action |
| Notify public users without configuration | Violation of WESLR doctrine |
| Run shell commands automatically | Violation of WESLR doctrine |

**Safe rule:**
```
WESLR may observe, detect, and propose.
WESLR may NOT silently mutate, execute, or self-code.
```

---

## SECTION 6 — SAFE SELF-REVIEW INPUT SOURCES

| Source | Path | Safe Read | Useful for Self-Review |
|---|---|---|---|
| Doctrine Registry | `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md` | ✅ | ✅ Gap detection phase doctrine |
| Observation Checkpoint | `weslr/docs/WESLR_OBSERVATION_CHECKPOINT_V1.md` | ✅ | ✅ Gap observation pipeline |
| Phase 6 Physical Reasoning | `docs/WESLR_PHASE_6_PHYSICAL_MATH_REASONING_DOCTRINE_V1.md` | ✅ | ✅ Physics validation gaps |
| Phase 7 Hypothesis Workflow | `docs/WESLR_PHASE_7_HYPOTHESIS_WORKFLOW_DOCTRINE_V1.md` | ✅ | ✅ Experiment proposal gaps |
| Phase 9 Advanced Reasoning | `docs/WESLR_PHASE_9_ADVANCED_REASONING_DOCTRINE_V1.md` | ✅ | ✅ Meta-learning gaps |
| Phase 10 Collaboration | `docs/WESLR_PHASE_10_COLLABORATION_DOCTRINE_V1.md` | ✅ | ✅ Workspace gaps |
| Contract Proposal Review Log | `weslr/contract_proposal_review_log.jsonl` | ✅ | ✅ Proposal gap detection |
| Proposal Store | `weslr/contract_proposal_review_log.jsonl` | ✅ | ✅ Proposal gap detection |
| Observatory Signals | `weslr/observatory.jsonl` | ✅ | ✅ Observation pipeline gaps |
| Decision Support | `weslr/decision_support.py` | ✅ | ✅ Decision gap detection |
| Reminder Handler | `weslr/reminder_handler.py` | ✅ | ✅ Alert gap detection |

---

## SECTION 7 — WHAT IS MISSING (Design Phase)

### Components Needed (Design Only)

| Component | Path | Status |
|---|---|---|
| `run_once` mode | `weslr/proactive_daemon.py` | ❌ Not implemented |
| Manual tick control | `daemon.py` | ❌ Not implemented |
| Self-review source adapter | `weslr/self_review_adapter.py` (design) | ❌ Not implemented |
| Architecture gap detection | `self_review_adapter.py` | ❌ Not implemented |
| Phase registry gap detection | `self_review_adapter.py` | ❌ Not implemented |
| Proposal store reader | `self_review_adapter.py` | ⚠️ Partial |
| Gap suggestion generator | `self_review_suggestion.py` (design) | ❌ Not implemented |
| Proposal review lifecycle | `lifecycle_proposal_review.py` (design) | ❌ Not implemented |
| Help drift detector | `help_drift_detector.py` (design) | ❌ Not implemented |
| Surface gap detector | `surface_gap_detector.py` (design) | ❌ Not implemented |

### Proposed Design Files (Do Not Implement Yet)

| File | Purpose |
|---|---|
| `weslr/self_review_adapter.py` | Source adapter: reads doctrine/phase registry/observation checkpoint → gap detection |
| `weslr/self_review_suggestion.py` | Gap suggestion generator: reads proposal store + observatory → suggestion |
| `weslr/tests/test_self_review_daemon_v1.py` | Unit tests for self-review daemon |
| `docs/WESLR_SELF_REVIEW_ADAPTER_V1.md` | Design doc for self-review adapter |

### Missing Components (Design Phase Only)

| Component | Status |
|---|---|
| `run_once` mode | ❌ Not implemented |
| Self-review source adapters | ❌ Not implemented |
| Architecture gap detection | ❌ Not implemented |
| Gap suggestion creation | ❌ Not implemented |
| Proposal store reader | ⚠️ Partial |
| Manual tick control | ❌ Not implemented |

---

## SECTION 8 — SAFE SELF-REVIEW MODEL RULES

### What the Daemon May Do ✅

```
1. Read doctrine registry (WESLR_DOCTRINE_REGISTRY_V1.md)
2. Read observation checkpoint (WESLR_OBSERVATION_CHECKPOINT_V1.md)
3. Read proposal review records (contract_proposal_review_log.jsonl)
4. Read validation gap records (contract_insufficiency_log.jsonl)
5. Read signal observatory (observatory.jsonl)
6. Detect phase gaps, stale doctrine, unresolved proposals
7. Suggest next actions via proposals
8. Write pending operator messages or suggestion records
```

### What the Daemon May NOT Do ❌

```
1. Do NOT edit code automatically
2. Do NOT edit doctrine files
3. Do NOT auto-commit or auto-push
4. Do NOT change contracts automatically
5. Do NOT change memory/truth automatically
6. Do NOT approve proposals automatically
7. Do NOT notify public users without operator configuration
8. Do NOT run shell commands unless explicitly invoked
```

---

## SECTION 9 — RECOMMENDED NEXT STEPS (Design Phase Only)

### Immediate Design Needed (Do Not Implement Yet)

| Step | Action | Purpose |
|---|---|---|
| **1** | `run_once` mode design | Manual tick for daemon review |
| **2** | Source adapter design | Architecture gap detection source |
| **3** | Phase registry reader design | Phase gap detection source |
| **4** | Proposal store reader design | Proposal gap detection source |
| **5** | Validation gap reader design | Gap detection source |
| **6** | Suggestion writer design | Suggestion proposal output |

### Recommended Next Implementation (Manual First)

**Option B — Add self-review source adapter first (after A)**

| Step | Action | Purpose |
|---|---|---|
| A | Wire manual daemon control first | Safe first step |
| B | Add source adapters to `proactive_daemon.py` | Gap detection only |
| C | Add proposal review lifecycle | Proposal suggestions |
| D | Add help drift detector | Help/README surface gap |
| E | Add surface gap detector | Help/README drift |

### Why B Over A?

If the daemon **has no source adapters** yet, wiring manual control (`A`) without source adapters means the daemon runs but **produces generic proactive hints only** — not useful self-review gap suggestions.

After A, add B (self-review source adapters). The **`run_once` mode`** is the immediate missing piece.

---

## SECTION 10 — SAFE SELF-REVIEW MODEL

### What the Daemon May Do ✅

| Action | Safe Read |
|---|---|
| Read doctrine | `WESLR_DOCTRINE_REGISTRY_V1.md` ✅ |
| Read observation checkpoint | `WESLR_OBSERVATION_CHECKPOINT_V1.md` ✅ |
| Read proposal review records | `contract_proposal_review_log.jsonl` ✅ |
| Read validation gaps | `contract_insufficiency_log.jsonl` ✅ |
| Read signal observatory | `observatory.jsonl` ✅ |
| Read phase registry | `phase_registry.jsonl` ✅ |
| Read proposal store | `proposal_store.jsonl` ✅ |
| **Detect gaps** | phase gaps, stale doctrine, unresolved proposals ✅ |
| **Suggest next actions** | suggestions only ✅ |
| **Write pending messages** | `pending_messages.jsonl` only ✅ |

### What the Daemon May NOT Do ❌

| Action | Reason |
|---|---|
| Edit code | Violation of WESLR doctrine |
| Edit doctrine files | Violation of WESLR doctrine |
| Auto-commit | Violation of WESLR governance |
| Auto-push | Violation of WESLR governance |
| Change contracts | Violation of WESLR doctrine |
| Change memory/truth | Violation of WESLR doctrine |
| Approve proposals | Operator-only action |
| Notify public users without configuration | Violation of WESLR doctrine |
| Run shell commands automatically | Violation of WESLR doctrine |

---

## SECTION 11 — FINAL RECOMMENDATION

| Option | Why |
|---|---|
| **A** | ✅ Safe first step — daemon complete and tested |
| **B** | ✅ After A — source adapters needed for gap detection |
| **C** | ⚠️ Post-B — validation gap store needed |
| **D** | ⚠️ Post-C — proposal review lifecycle needed |
| **E** | ⚠️ Post-D — help drift detector completes architecture |

**Recommended next: B (Add self-review source adapter first) after A.**

**Reasoning:** Manual control (`A`) is safe but insufficient — daemon needs source adapters (`B`) before it can detect gaps. The **`run_once` mode`** is the immediate missing design piece.

---

### Why B Over A?

If the daemon **has no source adapters** yet, wiring manual control (`A`) without source adapters means the daemon runs but **produces generic proactive hints only** — not useful self-review gap suggestions. **`A` before `B` is safe but insufficient.** After A, add B (self-review source adapters).

---

## Design Files Proposed (Do Not Implement Yet) ✅

| File | Purpose |
|---|---|
| `weslr/self_review_adapter.py` | Source adapter: reads doctrine/phase registry/observation checkpoint → gap detection |
| `weslr/self_review_suggestion.py` | Gap suggestion generator: reads proposal store + observatory → suggestion |
| `weslr/tests/test_self_review_daemon_v1.py` | Unit tests for self-review daemon |
| `docs/WESLR_SELF_REVIEW_ADAPTER_V1.md` | Design doc for self-review adapter |

---

## Summary

| Item | Status |
|---|---|
| **WESLR can self-review** | ❌ No — daemon produces only read-only suggestions |
| **Self-review gap detection** | ❌ No — no source adapters |
| **Architecture gap detection** | ❌ No — daemon cannot read `docs/` doctrine yet |
| **Phase registry gap detection** | ❌ No — daemon has no phase registry reader |
| **Gap suggestion creation** | ❌ No — only generic timeline hints |
| **Safe model readiness** | ⚠️ Partial — source adapters needed |
| **Missing components** | ✅ `run_once` · ✅ `source_adapters` · ✅ `proposal_store` reader · ✅ `proposal_review_lifecycle` |
| **Proposed next step** | **B (Add self-review source adapter first)** after A (manual daemon control) |

**Next prompt:** `WESLR_PROACTIVE_SELF_REVIEW_SOURCE_ADAPTER_DISCOVERY_V1` — design the source adapter contracts for gap detection.
