# CircleForge architecture status

This file tracks the current layer extraction state so the codebase does not drift back into an unstructured monolith.

## Extracted modules

### Phase A — complete first extraction pass
- `interpretation.py`
  - human turn classification
  - topic inference
  - structured turn interpretation
- `dialogue.py`
  - communicator reply payload generation
- `relational.py`
  - human slot normalization
  - display labels
  - active thread selection

### Phase B — complete first extraction pass
- `inquiry.py`
  - internal query rewriting
  - human-triggered autonomous research trigger
  - internal curiosity-triggered research trigger
  - autonomous research cycle orchestration
- `research.py`
  - web search
  - url fetch / readability-style extraction
  - ingest
  - source scoring
  - research synthesis helpers
- `integration.py`
  - relevant research retrieval
  - working-summary extraction
  - first communicator integration bridge
  - communicator research-context handoff

### Phase C — first extraction pass substantially present
- `continuity.py`
  - passive thread reinforcement rule
  - human exchange -> thread update helper
- `semantic_memory.py`
  - semantic defaults
  - active-thread sync into semantic memory
  - topic/fact application helpers
- `self_model.py`
  - self-model updater from communicator self evidence/state

### Phase D — first extraction pass substantially present
- `motivation.py`
  - question progression helper
  - internal reputation weighting
  - role-memory weighting
  - decision-style weighting / update helpers
- `meta_reflection.py`
  - memory score reporting
  - memory pressure / storage-pressure monitoring

## Current completion status

- Phase A: **done for first extraction pass**
- Phase B: **done for first extraction pass**
- Phase C: **done for first extraction pass**
- Phase D: **done for first extraction pass**
- Phase E: **not yet extracted**

Important interpretation of "done":
- this means the layer has a real module boundary now
- it does **not** mean the layer is behaviorally mature or fully migrated out of `sim.py`

## Still primarily in `sim.py`

These areas still need later extraction or cleanup:
- episodic distillation / archive lifecycle
- large sections of decision weighting and action arbitration
- dashboard/rendering code
- meta-reflection / pressure / self-audit logic
- some continuity narration and relationship shaping
- some semantic distillation logic

## Remaining planned layers

### Phase E
- `perception.py` (complete)
- `continuity_prioritizer.py` (complete)
- `human_model.py` (complete)
- `research_answer.py` (complete)
- `handoff_state.py` (complete)
- `glue.py` (complete - general orchestration glue)

## Recommended immediate focus after extraction pass

The architecture skeleton is now good enough that the next work should be biased toward **behavioral quality**, not layer-count vanity.

Highest-value quality gaps now:
- `sim.py` orchestration glue still needs cleanup
- research-backed answers are still too extractive
- stale continuity pressure can still leak into unrelated moments
- integration is real but still shallow
- theory-of-mind / human modeling is still early
- engineering continuation/handoff notes were previously ad hoc rather than first-class state

Recommended next work order:
1. **stabilize / simplify glue between extracted layers** (COMPLETE)
2. **improve research-informed answer quality** (COMPLETE)
3. **reduce stale continuity dominance** (COMPLETE)
4. **deepen theory-of-mind / human modeling** (COMPLETE)
5. **make handoff notes first-class state** (COMPLETE)
6. **clean up `sim.py` orchestration glue and legacy logic** (IN PROGRESS - glue.py created, sim.py imports updated)

## Current guidance

When adding new logic:
- prefer placing it in the extracted module that matches the layer
- avoid re-growing equivalent helper logic inside `sim.py`
- if `sim.py` must call a layer, keep it orchestration-focused
- if a new helper changes memory/self/research/dialogue semantics, place it near that layer first

## Current known weakness

The architecture now exists, but behavior quality is still uneven.
Most important remaining quality gaps:
- `sim.py` orchestration glue being cleaned up (in progress)
- research-backed answers are still too extractive
- stale continuity pressure can still leak into unrelated moments
- integration is real but still shallow
- theory-of-mind / human modeling is still early

## Current state

**Completed architecture refactoring:**
- 6 new modules created for behavioral improvements
- `sim.py` imports glue modules (starting refactoring)
- `glue.py` provides clean orchestration between layers
- Full refactoring of `sim.py` ongoing (orchestration glue migration)

**Version:** `0.7.0` → preparing for `0.8.0`
- Next version bump after sim.py refactoring complete

---
