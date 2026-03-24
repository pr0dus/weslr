# CircleForge architecture status

This file tracks the current layer extraction state so the codebase does not drift back into an unstructured monolith.

## Extracted modules

### Phase A
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

### Phase B
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

### Phase C
- `continuity.py`
  - passive thread reinforcement rule
  - human exchange -> thread update helper
- `semantic_memory.py`
  - semantic defaults
  - active-thread sync into semantic memory
  - topic/fact application helpers
- `self_model.py`
  - self-model updater from communicator self evidence/state

## Still primarily in `sim.py`

These areas still need later extraction or cleanup:
- episodic distillation / archive lifecycle
- large sections of decision weighting and action arbitration
- dashboard/rendering code
- meta-reflection / pressure / self-audit logic
- some continuity narration and relationship shaping
- some semantic distillation logic

## Remaining planned layers

### Phase D
- `motivation.py`
- `meta_reflection.py`

### Phase E
- `perception.py`

## Current guidance

When adding new logic:
- prefer placing it in the extracted module that matches the layer
- avoid re-growing equivalent helper logic inside `sim.py`
- if `sim.py` must call a layer, keep it orchestration-focused
- if a new helper changes memory/self/research/dialogue semantics, place it near that layer first

## Current known weakness

The architecture now exists, but behavior quality is still uneven.
Most important remaining quality gaps:
- research-backed answers are still too extractive
- stale continuity pressure can still leak into unrelated moments
- integration is real but still shallow
- theory-of-mind / human modeling is still early
