# CircleForge LLM integration

CircleForge now has a provider abstraction for cognition backends.

## Goal

Support multiple cognition backends through one adapter layer:
- **embedded** runtime bundled with CircleForge code and model files
- **ollama** as optional external local API
- **openai-compatible** APIs, including OpenAI/OAuth-style setups
- **fallback** when no live model is available

## Recommended default direction

The preferred long-term path is **embedded**.

That means:
- runtime shipped with CircleForge
- model file shipped with CircleForge
- no mandatory separate model daemon
- direct inference inside CircleForge process/runtime layer

## Current first embedded target

The first concrete embedded target is now:
- **model family:** Qwen2.5
- **size:** 0.5B
- **variant:** Instruct
- **format:** GGUF
- **default model name:** `Qwen2.5-0.5B-Instruct`
- **default expected filename:** `qwen2.5-0.5b-instruct.gguf`
- **default expected path:** `CircleForge/models/qwen2.5-0.5b-instruct.gguf`

## Providers

### 1. embedded
Best match for the project goal.

Recommended shape:
- GGUF model file
- `llama.cpp` / `llama-cpp-python`
- model path under:
  - `CircleForge/models/`

Suggested candidate classes:
- Qwen 2.5 small GGUF
- SmolLM2 small GGUF
- TinyLlama-class GGUF

### 2. ollama
Optional local API backend.
Good for development/testing, but not the desired final dependency.

### 3. openai-compatible
Optional remote API backend.
Can be used when the user prefers hosted inference.
Examples:
- OpenAI-compatible endpoints
- OpenRouter-style compatible providers
- OAuth-backed hosted setup if exposed as standard API key/base URL to CircleForge

### 4. fallback
Used when no live backend is available.
This preserves function without pretending true model cognition is active.

## Config direction

CircleForge should support env/config like:
- `CIRCLEFORGE_LLM_PROVIDER=embedded|ollama|openai|fallback`
- `CIRCLEFORGE_LLM_MODEL=<model-name>`
- `CIRCLEFORGE_EMBEDDED_MODEL_PATH=<path-to-gguf>`
- `OPENAI_BASE_URL=<url>`
- `OPENAI_API_KEY=<secret>`
- existing Ollama host config for optional use

## Why this matters

This keeps the rest of CircleForge independent from backend choice.
The entity should ask for:
- inner thought
- phrasing
- self-mod hint

It should not care whether the answer came from:
- embedded runtime
- ollama
- hosted API
- fallback

## Immediate next use

1. wire all current thought generation through the provider abstraction
2. expose provider status in CLI/dashboard
3. verify fallback vs live status honestly
4. later add a bundled embedded model and test real non-fallback cognition
