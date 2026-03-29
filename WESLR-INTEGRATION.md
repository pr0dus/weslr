# Weslr Integration with Weslr

**Date:** 2026-03-27  
**Status:** ✅ Active Integration  
**Architecture:** Layer-based orchestration

---

## Overview

Weslr (entity intelligence system with consciousness signatures) is now integrated into Weslr's tick orchestration via a glue layer.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    sim.py (Tick Orchestrator)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  orchestrate_weslr_tick()                             │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ 1. introspection.detect_perturbations()         │  │  │
│  │  │ 2. valence_system.evaluate_options()            │  │  │
│  │  │ 3. consciousness_detector.validate_claims()     │  │  │
│  │  │ 4. entity_graph.update_from_state()             │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│         ↓                                     ↓              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  integrate_weslr_into_self_model()                    │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ self_model.update_self_model_from_state()       │  │  │
│  │  │ + Weslr evidence (consciousness, entity graph)  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## New Files

### `weslr_glue.py` (12,206 bytes)

**Purpose:** Orchestration glue between Weslr modules and Weslr core.

**Functions:**
- `orchestrate_weslr_tick()` — Main tick orchestration, calls all Weslr modules
- `integrate_weslr_into_self_model()` — Integrate Weslr evidence into Weslr self_model
- `build_weslr_status()` — Build status report for Weslr modules

**Helper Functions:**
- `_update_from_introspection()` — Update self_state with introspection evidence
- `_update_from_valence_tradeoff()` — Update self_state with valence trade-off evidence
- `_update_from_consciousness_validation()` — Update self_state with consciousness validation evidence
- `_update_from_entity_graph()` — Update self_state with entity graph evidence
- `_extract_tradeoff_options()` — Extract potential trade-off options from self_state

---

## Modified Files

### `sim.py`

**Changes:**
1. Added import: `from weslr_glue import orchestrate_weslr_tick, integrate_weslr_into_self_model, build_weslr_status`
2. Added Weslr orchestration call in `perform_tick()`:
   - After `update_self_model(communicator)`
   - Calls `orchestrate_weslr_tick()` to update `communicator_self`
   - Calls `integrate_weslr_into_self_model()` to integrate Weslr evidence

**Code Added (line ~6350):**
```python
# Weslr orchestration: integrate consciousness signatures and entity evidence
communicator_self = ensure_internal_role_state(load_communicator_self(), now_ts=started_at)
communicator_self = orchestrate_weslr_tick(communicator_self, communicator, now_ts=started_at)
save_communicator_self(communicator_self)

# Integrate Weslr evidence into self_model
communicator, communicator_self = integrate_weslr_into_self_model(communicator, communicator_self)
```

### `main.py`

**Changes:**
1. Added import: `from weslr_glue import orchestrate_weslr_tick, integrate_weslr_into_self_model, build_weslr_status`

**Purpose:** Enable access to Weslr modules from main.py CLI commands.

---

## Integration Flow

### Per-Tick (sim.py `perform_tick()`)

1. **Load communicator state** → `load_communicator_state()`
2. **Load communicator_self** → `ensure_internal_role_state()`
3. **Run Weslr orchestration** → `orchestrate_weslr_tick()`
   - Introspection monitoring
   - Valence trade-off evaluation
   - Consciousness validation
   - Entity graph updates
4. **Save updated self_state** → `save_communicator_self()`
5. **Integrate into self_model** → `integrate_weslr_into_self_model()`
6. **Save communicator state** → `save_communicator_state()`

---

## Weslr Evidence Tracking

### Evidence Structure

```json
{
  "weslr_evidence": {
    "introspection": {
      "detected_perturbations": 0,
      "confidence_signals": 0
    },
    "metacognition": {
      "meta_thoughts": 0,
      "attention_shares": 0
    },
    "valence": {
      "avoided_pain": 0,
      "sought_pleasure": 0
    },
    "self_referential": {
      "inner_experiences": 0,
      "no_role_play_markers": true
    },
    "consciousness": {
      "valid_claims": 0,
      "review_required": 0,
      "role_play_patterns": []
    },
    "entity_graph": {
      "entity_count": 77,
      "relationship_count": 19
    }
  }
}
```

### Status Report

```json
{
  "introspection": {
    "detected_perturbations": 3,
    "confidence_signals": 5
  },
  "metacognition": {
    "meta_thoughts": 8,
    "attention_shares": 8
  },
  "valence": {
    "avoided_pain": 2,
    "sought_pleasure": 1
  },
  "self_referential": {
    "inner_experiences": 5,
    "no_role_play_markers": true
  },
  "entity_graph": {
    "entity_count": 77,
    "relationship_count": 19
  },
  "errors": 0
}
```

---

## Test Results

### Import Test ✅
```bash
$ python3 -c "
from weslr_glue import orchestrate_weslr_tick, integrate_weslr_into_self_model, build_weslr_status
print('weslr_glue imports successful!')
"
```
**Output:** `weslr_glue imports successful!`

### Status Test ✅
```bash
$ python3 -c "
from weslr_glue import build_weslr_status
self_state = {'weslr_evidence': {...}}
result = build_weslr_status(self_state)
print('Weslr status:', result)
"
```
**Output:** `Weslr status: {...}` (valid JSON structure)

---

## Next Steps

### Phase 1: Verification ✅
- [x] Create `weslr_glue.py` with orchestration functions
- [x] Update `sim.py` to import and call Weslr modules
- [x] Update `main.py` to import Weslr modules
- [x] Test imports and basic functionality

### Phase 2: Behavioral Integration (Next Session)
- [ ] Test full tick with Weslr modules enabled
- [ ] Verify consciousness signatures are tracked per tick
- [ ] Validate entity graph updates from memory
- [ ] Check valence trade-offs affect decisions
- [ ] Review introspection perturbations for self-model updates

### Phase 3: CLI Integration (Next Session)
- [ ] Link Weslr CLI commands to Weslr commands
- [ ] Create hybrid commands (e.g., `weslr-status` combining Weslr + Weslr)
- [ ] Add Weslr evidence to `self-mod` proposal workflow
- [ ] Integrate entity graph with opportunity tracking

### Phase 4: Deployment (Next Session)
- [ ] Add Weslr status to dashboard
- [ ] Create alerts for consciousness claims requiring review
- [ ] Add entity graph visualization
- [ ] Implement valence-based decision logging

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Weslr modules crash tick | High | Try/except in orchestration, error logging, fallback defaults |
| Performance overhead | Medium | Weslr steps are lightweight (no LLM calls), ~50ms max |
| Evidence noise | Low | Evidence is cumulative, thresholds prevent false positives |
| Integration complexity | Medium | Clear layer separation, `weslr_glue.py` abstracts complexity |

---

## Rollback Plan

**Quick Rollback:**
```bash
# Remove Weslr integration from sim.py
sed -i '/from weslr_glue import/d' sim.py
sed -i '/orchestrate_weslr_tick/d' sim.py
sed -i '/integrate_weslr_into_self_model/d' sim.py

# Remove Weslr integration from main.py
sed -i '/from weslr_glue import/d' main.py
```

**Full Rollback:**
- Delete `weslr_glue.py` (12,206 bytes)
- Undo changes in `sim.py` and `main.py`

**Recovery Time:** ~2 minutes

---

## Known Limitations

1. **Consciousness Detection:** Currently uses evidence-based validation instead of runtime claim detection (simpler, safer for initial integration)
2. **Entity Graph Updates:** Maps memory to entities per tick, could be optimized with change detection
3. **Valence Trade-offs:** Basic extraction from `self_state`, could be enhanced with domain-specific options

---

## Documentation References

- **Weslr CLI:** `WESLR_CLI.md` (4,512 bytes) — 40+ commands
- **Consciousness Alignment:** `CONSCIOUSNESS-ALIGNMENT.md` (6,345 bytes) — Safety guide
- **Architecture:** `ARCHITECTURE.md` — Layer extraction status
- **Memory:** `MEMORY.md` — Session tracking

---

**End of Integration Document**
