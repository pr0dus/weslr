# WESLR Discovery Report — 2026-05-04

**Pass:** WESLR_DISCOVERY_PASS_V1
**Scope:** Contract observation, insufficiency detection, proposal bridge, workplace chat bridge, public signal capture, JSONL archiver, experiment proposals, deterministic handlers

---

## SECTION 1 — REPO SAFETY CHECK

- **pwd:** `/data/data/com.termux/files/home/.openclaw/workspace`
- **git root:** `/data/data/com.termux/files/home/.openclaw/workspace` ✅
- **branch:** `main`
- **latest commit:** `8d902ccd8226eb1a0a108c2a09b3fa209baaf0f5` (feat(workflow): implement Phase 7 unified hypothesis & experiment workflow)
- **working tree:** **dirty**
  - `memory/2026-05-03-kesterite-pv-test.md` (modified)
  - `weslr/deterministic_handlers.py` (modified, +63 lines from HEAD)
  - 20+ untracked Phase 10 files

---

## SECTION 2 — RECENT CHANGE INVENTORY

### A. Contract observation / insufficiency / proposal pipeline

| File | Status |
|------|--------|
| `weslr/contract_observation.py` | stable |
| `weslr/contract_observations.jsonl` (live data) | active |
| `weslr/contract_insufficiency_detector.py` | stable |
| `weslr/contract_insufficiency_log.jsonl` (live data) | active |
| `weslr/contract_improvement_proposal_bridge.py` | stable |
| `weslr/contract_proposal_review_log.jsonl` (live data) | active |
| `weslr/tests/test_contract_observation_v1.py` (419 lines) | stable |
| `weslr/tests/test_contract_insufficiency_detector_v1.py` (393 lines) | stable |
| `weslr/tests/test_contract_improvement_proposal_bridge_v1.py` (545 lines) | stable |

### B. Workplace / review surface / chat bridge

| File | Status |
|------|--------|
| `weslr/workplace_chat_bridge.py` (201 lines) | stable |
| `weslr/workplace_review_surface.py` (271 lines) | stable |
| `weslr/review_interface.py` (222 lines) | stable |
| `weslr/tests/test_workplace_chat_bridge_v1.py` | stable |

### C. Public signal capture

| File | Status |
|------|--------|
| `weslr/public_signal_store.py` (210 lines) | stable |
| `weslr/public_signals.jsonl` (live data) | active |
| `weslr/tests/test_public_signal_store_v1.py` (320 lines) | stable |

### D. JSONL archiver

| File | Status |
|------|--------|
| `weslr/jsonl_archiver.py` | stable |
| `weslr/tests/test_jsonl_archiver_v1.py` (338 lines) | stable |

### E. Experiment proposals / proactive suggestions / timeline memory

| File | Status |
|------|--------|
| `weslr/user_timeline_memory.py` | stable |
| `weslr/proactive_suggestions.py` | stable |
| `weslr/experiment_proposal_generator.py` | stable |

### F. ISS (Intelligent Support System)

| File | Status |
|------|--------|
| `weslr/iss/__init__.py`, `probe_registry.py`, `probe_planning.py`, `diagnostic_records.py`, `probe_execution.py` | stable |

### G. Deterministic handlers (dirty — modified from HEAD)

| File | Status |
|------|--------|
| `weslr/deterministic_handlers.py` (+63 lines from HEAD, 30+ handlers) | **experimental** |

### H. Phase 10 collaboration (untracked)

| File | Status |
|------|--------|
| `weslr/modules/workspace.py`, `explanation_generator.py` | untracked |
| `weslr/jupyter_kernel_stub.py` | untracked |
| `weslr/commands/collaboration_commands.py`, `advanced_commands.py` | untracked |
| `weslr/tests/test_collaboration.py` (37 tests, all passing) | untracked |
| `weslr/modules/abductive_reasoner.py`, `meta_analyst.py`, `transfer_analogy.py` | untracked |
| `weslr/tests/test_advanced_reasoning.py` | untracked |

---

## SECTION 3 — BEHAVIOR MAP

### Contract pipeline flow

1. `/chat` request → `contract_observation.py:observe_contract_outcome()` → appends to `contract_observations.jsonl`
   - Fields: `reply_shape`, `interaction_frame`, `turn_type`, `response_path`, `signal_type`
   - Privacy: `raw_prompt_stored: false`, `pii_stored: false`, `behavior_change_allowed: false`

2. `contract_insufficiency_detector.py` reads sliding window of 50 observations
   - Detects stable patterns (≥50% same pattern, stable across ≥3 checks)
   - Sets `proposal_ready: True` → writes to `contract_insufficiency_log.jsonl`

3. `contract_improvement_proposal_bridge.py` reads proposal-ready records
   - Deduplicates by `(pattern_type, contract, response_path, stable_across_checks)`
   - Generates `CP-{date}-{n}` ID → appends to `contract_proposal_review_log.jsonl`
   - Status: `pending_review`, `automatic_change: false`

4. **Nothing in this pipeline ever changes behavior.** All observation files are append-only.

### Workplace flow

- `workplace_chat_bridge.py` intercepts `/workplace overview` queries
- Aggregates via `workplace_review_surface.py` → experiment proposals + proactive suggestions + timeline context
- `review_interface.py` provides read-only inspection of proposal review log

### Public signal flow

- `public_signal_store.py` appends anonymous operational signals to `public_signals.jsonl`
- Isolated from production truth, never used to change response behavior

### ISS flow

- `iss/probe_registry.py` defines 4 static probes, all `execution_allowed: False`
- `iss/probe_planning.py` creates probe plans (non-executing)
- `iss/diagnostic_records.py` tracks diagnostic records

---

## SECTION 4 — CANON CANDIDATE CLASSIFICATION

### A) Implementation detail
- ISS probe registry (4 probes is an implementation)
- Workplace chat bridge (one routing handler)
- Per-run proposal counter
- Phase 10 collaboration files (scope only)

### B) Architecture checkpoint
- Contract observation → insufficiency → proposal pipeline (observe-without-acting pattern)
- Public signal store isolation principle
- `execution_allowed: false` invariant
- Deterministic handler registry structure

### C) Canon candidate (durable WESLR laws)
- **Passive observation only**: contract_observation.py never stores prompts, PII, or raw user text. Never changes routing or behavior.
- **Append-only observation records**: No observation file is ever truncated, overwritten, or deleted by the pipeline.
- **`behavior_change_allowed: false` on all observation records**: Every observation record explicitly declares this. Non-negotiable.

### D) Open questions
- `_INCLUDE_GENERATED_SUGGESTIONS = True` hardcoded in workplace_chat_bridge.py — no operator toggle
- Review pipeline gap: `pending_review` records exist but nothing reads them to progress
- `deterministic_handlers.py` scope unclear — was handler registry modified intentionally as part of recent work?

### E) Anti-canon
- Per-run proposal ID counter (`CP-{date}-{n}` resets each run)
- Specific insufficiency thresholds (window=50, stability=3, 50% occupancy)
- `BASE_TRUST = 0.70` hardcoded in pubmed handler

---

## SECTION 5 — HARD-CODING / OVERFITTING REVIEW

| File | Item | Status |
|------|------|--------|
| `deterministic_handlers.py` | `pubmed_search`/`arxiv_search` registry says `read_only: True` but actually writes to `.weslr/` | **risky** |
| `deterministic_handlers.py` | `BASE_TRUST = 0.70` hardcoded for PubMed facts | questionable |
| `contract_improvement_proposal_bridge.py` | `_proposal_counter` resets per run, IDs may conflict across runs | questionable |
| `contract_insufficiency_detector.py` | Threshold constants (50/3/50%) hardcoded | questionable |
| `workplace_chat_bridge.py` | `_INCLUDE_GENERATED_SUGGESTIONS = True` no operator control | questionable |
| All observation modules | PII patterns list, execution_allowed=False, append-only | safe |

---

## SECTION 6 — TEST AND VALIDATION MAP

**Safe tests run (67 passed, 0.84s):**

```
weslr/tests/test_contract_observation_v1.py
weslr/tests/test_contract_insufficiency_detector_v1.py
weslr/tests/test_contract_improvement_proposal_bridge_v1.py
weslr/tests/test_public_signal_store_v1.py
weslr/tests/test_jsonl_archiver_v1.py
```

---

## SECTION 7 — DISCOVERY SUMMARY

### What WESLR has become
WESLR is a governed observation and proposal system with:
1. **Contract observation pipeline**: Passive `/chat` observation → pattern detection → operator-reviewable proposals. Zero behavior change.
2. **Public signal capture**: Anonymous signals stored separately, never used to change responses.
3. **ISS**: 4 non-executing probes + diagnostic records.
4. **Deterministic handler dispatch**: 30+ handlers unified under `HANDLER_REGISTRY`.
5. **Workplace surface**: Read-only aggregation for internal review.
6. **Phase 10 collaboration**: Multi-tenant shared hypothesis library + template explanations + Jupyter stub.

### Definitely stable
- Contract pipeline (67 tests passing)
- `execution_allowed: false` invariant
- Append-only observation files
- PII rejection throughout
- Public signal store isolation
- JSONL archiver

### Needs operator decision
1. Review pipeline gap: what happens after review?
2. `_INCLUDE_GENERATED_SUGGESTIONS` — should experiment proposals appear in workplace without toggle?
3. `deterministic_handlers.py` scope and read_only inconsistency (pubmed/arxiv write but declare read-only)
4. `contract_proposal_review_log.jsonl` review workflow undefined

---

## SECTION 8 — RECOMMENDED NEXT STEP

**E) Stop and ask operator because discovery found risk.**

`deterministic_handlers.py` has a structural inconsistency: `pubmed_search` and `arxiv_search` are registered as `read_only: True` but call `append_evidence_packet()` which writes to `.weslr/external_evidence_packets.jsonl` and `fact_assertions.jsonl`. This could cause incorrect safety classification if the registry is used for permission-gated dispatch.

Before canon promotion or further development, the operator needs to confirm:
1. The intended scope of the handler registry
2. Whether pubmed/arxiv should be read-only or write-permissioned
3. What the Phase 10 collaboration files commit scope should be