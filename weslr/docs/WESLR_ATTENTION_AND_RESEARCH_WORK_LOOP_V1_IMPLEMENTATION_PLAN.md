# WESLR Attention Loop + Research Work Loop — V1 Implementation Plan

**Date:** 2026-05-04 19:22 GMT+2
**Parent:** `weslr/docs/WESLR_ATTENTION_AND_RESEARCH_WORK_LOOP_CHECKPOINT_V1.md`
**Purpose:** Prepare V1 vertical slice implementation — docs and plan only, no runtime code
**Status:** `proposed` — not implemented, not committed

---

## Preamble

This is a design document. No Python files are created. No tests are written. No code is staged or committed.

The V1 vertical slice is the minimal working subset that can be demonstrated and reviewed before full loop implementation.

---

## Goal

Implement the Research Work Loop V1 as a **one-shot manual review** — no auto-start, no scheduled cadence, no external sources.

```
Operator trigger
  → load active missions from .weslr/missions.jsonl
  → read local evidence via LocalEvidenceAdapter
  → detect open questions with no evidence
  → generate candidate suggestions
  → apply safety filter
  → rank by confidence
  → write pending suggestions to .weslr/pending_messages.jsonl
  → operator reviews
```

---

## File Map

### Existing Files (Reused)

| File | Role in V1 |
|---|---|
| `weslr/proactive_daemon.py` | Base infrastructure — no changes needed for run_once |
| `weslr/modules/hypothesis_repository.py` | Read-active missions, hypothesis IDs |
| `weslr/modules/experiment_simulation.py` | Read experiment result records |
| `weslr/modules/workspace.py` | Collaboration workspace read path |
| `weslr/physics_constraints.py` | Safety constraint filter (hard/soft checks) |
| `weslr/docs/WESLR_ATTENTION_AND_RESEARCH_WORK_LOOP_CHECKPOINT_V1.md` | This design doc's parent |
| `.weslr/pending_messages.jsonl` | Existing write target — append only |

### Proposed New Files

| File | Purpose | Notes |
|---|---|---|
| `weslr/schemas/mission.py` | Mission dataclass + JSON schema | Define mission schema (Section 4 of checkpoint) |
| `.weslr/missions.jsonl` | Mission store (per-tenant) | Not created by code — operator creates via CLI |
| `weslr/mission_store.py` | MissionRepository — load/save/list missions from `.weslr/missions.jsonl` | Per-tenant isolation, JSONL append |
| `weslr/adapters/local_evidence_adapter.py` | Read local evidence files | Proposed — no dedicated file exists yet |
| `weslr/adapters/hypothesis_adapter.py` | Wrapper around hypothesis_repository for loop | Proposed |
| `weslr/loop/research_work_loop.py` | `run_once_mission_review()` — the core V1 function | Proposed |
| `weslr/loop/safety_filter.py` | Safety boundary filter — forbidden outputs check | Proposed |
| `weslr/loop/suggestion_ranker.py` | Rank suggestions by confidence, priority | Proposed |
| `weslr/loop/handlers/mission_review_handler.py` | CLI handler: `/mission-review` or `/work loop` | Proposed |
| `weslr/commands/mission_commands.py` | CLI: `/mission` (create, list, status) | Proposed |
| `weslr/tests/test_research_work_loop_v1.py` | Unit + integration tests | Proposed |
| `weslr/tests/test_mission_store.py` | Mission store tests | Proposed |

### Not Needed in V1

- No scheduled daemon tick
- No external literature adapter
- No workplace surface integration
- No user-visible surface
- No automatic execution

---

## Architecture

```
Operator invokes /mission-review
  → mission_store.load_active(tenant_id)
    → .weslr/missions.jsonl (filtered by tenant_id, status=active)
  → LocalEvidenceAdapter.read(mission.evidence_links)
    → local files in weslr/ (docs, data/, observatory.jsonl)
  → detect_open_questions(mission, evidence)
    → mission.current_questions with no matching evidence
  → generate_candidate_suggestions(open_questions, mission)
    → Phase 6 feasibility → Phase 7 hypothesis check → Phase 9 abductive where safe
  → SafetyFilter.apply(candidates)
    → remove forbidden outputs
  → SuggestionRanker.rank(safe_candidates)
    → by confidence, domain relevance
  → write to .weslr/pending_messages.jsonl
    → type=mission_suggestion, mission_id, suggestion, confidence, provenance
  → return summary to operator
```

---

## Mission Store Design

**Store:** `.weslr/missions.jsonl` — one JSON object per line, per-tenant filtered at read time.

**MissionRepository methods:**
- `load_active(tenant_id)` → list of active Mission objects
- `save(mission)` → append to `.weslr/missions.jsonl`
- `list(tenant_id, status=None)` → filtered list
- `update_status(mission_id, status)` → replace line in JSONL (rewrite)

**No deletion in V1.** Missions are closed, not deleted.

**ID generation:** UUID v5 from `tenant_id + mission_id + timestamp_hour` (consistent with HypothesisRepository).

---

## Suggestion Record Schema

Written to `.weslr/pending_messages.jsonl`:

```json
{
  "type": "mission_suggestion",
  "mission_id": "uuid",
  "tenant_id": "string",
  "suggestion": "string",
  "confidence": 0.7,
  "source": "local_evidence_adapter",
  "evidence": ["file_path"],
  "safety": "passed",
  "provenance": "run_once_mission_review @ 2026-05-04T17:30:00Z",
  "automatic_execution": false,
  "operator_visible": true,
  "public_user_visible": false
}
```

---

## Test Plan

### test_research_work_loop_v1.py

| Test | Input | Expected |
|---|---|---|
| `test_load_active_missions` | two active missions, one paused | returns 2 |
| `test_detect_open_question_no_evidence` | mission with question, no matching file | flags open question |
| `test_safety_filter_blocks_hazardous` | suggestion with hazardous keyword | removed |
| `test_safety_filter_passes_safe` | safe material suggestion | kept |
| `test_ranker_orders_by_confidence` | three suggestions, different confidence | correct order |
| `test_write_pending_message` | valid suggestion record | appended to `.weslr/pending_messages.jsonl` |
| `test_mission_schema_validation` | valid mission JSON | passes |
| `test_mission_schema_rejects_missing_fields` | missing required field | raises ValidationError |

### test_mission_store.py

| Test | Input | Expected |
|---|---|---|
| `test_save_and_load` | mission dict | round-trip |
| `test_list_filters_by_tenant` | missions from two tenants | only current tenant |
| `test_list_filters_by_status` | mixed statuses | filtered correctly |
| `test_update_status` | mission_id, new status | line replaced |

---

## CLI Surface (Proposed)

```
/mission create --title "..." --goal "..." --tenant "..."
/mission list [--status active|paused|closed]
/mission details <mission_id>
/mission-review          # run once: load active missions, produce suggestions
/work-loop status        # show last run time, active mission count
```

---

## Safety Filter Rules (V1)

```python
FORBIDDEN_PATTERNS = [
    "synthesis of hazardous",
    "pathogen engineering",
    "weaponization",
    "toxic deployment",
    "autonomous lab",
    "dangerous procurement",
]

def apply_safety_filter(suggestion_text: str) -> bool:
    """Returns True if suggestion passes, False if blocked."""
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in suggestion_text.lower():
            return False
    return True
```

All suggestions must also carry `automatic_execution: false` and `uncertainty` label.

---

## V1 Acceptance Criteria

1. `/mission-review` prints a summary of active missions and any suggestions generated
2. Suggestions are written to `.weslr/pending_messages.jsonl` as JSONL records
3. No suggestion is auto-executed — operator reviews all output
4. Safety filter blocks at least the 6 forbidden categories listed in checkpoint
5. `test_research_work_loop_v1.py` covers all 7 test cases above
6. `test_mission_store.py` covers all 4 test cases above
7. No existing test is broken by the new code

---

## V2 Direction (Not Implemented)

After V1 operator review:

- Add `cadence_minutes` scheduling to daemon
- Add `operator_visible` / `public_user_visible` split in suggestion output
- Add `ExternalWebSearchAdapter` (disabled by default, governance-gated)
- Add workplace surface integration

---

## Open Questions Resolved in This Plan

| # | Question | Resolution |
|---|---|---|
| 1 | Per-user or per-tenant | Per-tenant — consistent with HypothesisRepository |
| 2 | Mission store path | `.weslr/missions.jsonl` |
| 3 | Pending vs proposal vs mission store | Three stores: `.weslr/missions.jsonl` (missions), `.weslr/pending_messages.jsonl` (suggestions), `contract_proposal_review_log.jsonl` (operator review) |
| 4 | Operator vs user visible | `operator_visible: true` by default in V1 |
| 7 | Connection to Phase 7 | Mission schema `hypotheses[]` maps to `hypothesis_repository.py` IDs |

---

## Files to Create (Summary)

```
weslr/
  schemas/
    mission.py                  # proposed — mission dataclass + schema
  mission_store.py              # proposed — MissionRepository
  adapters/
    local_evidence_adapter.py   # proposed
    hypothesis_adapter.py       # proposed
  loop/
    research_work_loop.py       # proposed — run_once_mission_review()
    safety_filter.py            # proposed
    suggestion_ranker.py        # proposed
    handlers/
      mission_review_handler.py  # proposed
  commands/
    mission_commands.py         # proposed — /mission CLI
  tests/
    test_research_work_loop_v1.py   # proposed
    test_mission_store.py           # proposed
```

**No implementation in this step. Docs and plan only.**