# Weslr embedded runtime plan

## Purpose

This plan makes `embedded` the preferred real cognition path for Weslr.

The target is:
- model file delivered with Weslr
- runtime delivered with Weslr
- no mandatory separate Ollama-style daemon
- bounded cognition for inner-thought generation and communicator phrasing

## Current state

Already done:
- provider abstraction scaffold exists in `llm_runtime.py`
- optional providers scaffolded:
  - embedded
  - openai/openai-compatible
  - ollama
  - fallback
- current live operation is still fallback because no real backend is active

## Recommended technical choice

### Runtime
Prefer:
- `llama.cpp` compatible runtime
- Python integration via `llama-cpp-python` when possible

### Model format
Prefer:
- GGUF

### Default model path
- `Weslr/models/model.gguf`

## Why this path

- direct embedding fits human's goal better than an external serving daemon
- GGUF has the strongest ecosystem for small local models
- `llama.cpp` is the most practical direct-embed path for this type of project
- bounded inner-thought generation does not require a large model

## Candidate model classes

Evaluate small open instruct-tuned models roughly in the 0.5B–3B range.

Best first candidates:
- Qwen 2.5 small GGUF
- SmolLM2 small GGUF
- TinyLlama-class GGUF

Selection criteria:
- free/open usable license
- small enough for repeated wake cycles
- decent structured-output behavior
- acceptable latency on target hardware
- not expected to do large long-form reasoning

## Chosen first target

The first embedded model target is now fixed as:
- **Qwen2.5-0.5B-Instruct**
- expected GGUF filename:
  - `qwen2.5-0.5b-instruct.gguf`
- expected path:
  - `Weslr/models/qwen2.5-0.5b-instruct.gguf`

Reason:
- free/open
- small enough to be a plausible first bundled language cortex
- better fit for short structured inner-thought generation than ultra-tiny toy models

## Integration phases

### Phase 1 — embedded runtime availability
1. ensure `embedded` provider path in `llm_runtime.py` is the preferred path
2. verify import/runtime availability for `llama-cpp-python`
3. verify model file existence at configured path
4. return clear provider status when model/runtime is missing

### Phase 2 — first live embedded inference
1. load model once through embedded runtime
2. issue one bounded structured thought call
3. verify JSON-like response parsing
4. record result as provider=`embedded`
5. expose success/failure in `llm-status`

### Phase 3 — wake-loop integration verification
1. run short smoke test under `CIRCLEFORGE_LLM_PROVIDER=embedded`
2. verify stored inner thoughts have source=`embedded`
3. verify communicator message includes thought fragments from embedded output
4. confirm fallback is only used when runtime/model truly fails

### Phase 4 — post-backend learning loop
After embedded works, resume:
1. repeated memory-keeper thoughts strengthen shared-thread salience
2. builder thought hints produce staged self-mod proposals
3. communicator learns silence vs speech from thought pressure

## User options preserved

Even with embedded as the preferred path, Weslr should keep these optional paths:

### embedded
- preferred long-term path
- bundled runtime + bundled model

### openai / openai-compatible
- optional hosted inference path
- useful for users who prefer API-backed cognition
- can include OAuth-backed setups as long as Weslr receives a standard API-compatible base URL + token/key path

### ollama
- optional local development path
- useful when a user already has Ollama
- not required for the entity to function

### fallback
- honest degraded mode
- preserves behavior when no live backend exists

## Important discipline

- the model is not the whole identity
- identity remains in substrate state, memory, continuity, threads, drives, and learned structure
- embedded runtime should remain bounded and cheap enough for repeated wake cycles
- do not let backend complexity sprawl through the rest of the codebase

## Immediate next implementation target

Implement **Phase 1 + Phase 2** for the embedded path.
