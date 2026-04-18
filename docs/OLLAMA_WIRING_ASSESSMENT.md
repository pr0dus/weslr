# Ollama Wiring Assessment — 2026-04-18

## Can Ollama be wired as WESLR's LLM? YES — with one config fix.

### What works

- Ollama daemon is running on `http://127.0.0.1:11434` ✅
- Model `qwen2.5:0.5b-instruct` is loaded and responding ✅
- `/api/chat` works correctly with `qwen2.5:0.5b-instruct` ✅
- OllamaProvider in `weslr/providers.py` is already written and registered ✅
- Provider config persisted at `provider_config.json` with `provider=ollama` ✅
- `get_provider('ollama')` returns a live OllamaProvider instance ✅

### The problem — model name mismatch

| Setting | Value | Problem |
|---|---|---|
| `provider_config.json` → `model` | `"default"` | Ollama has no model called "default" → `/api/generate` 404 |
| `config.py` → `WESLR_LLM_MODEL` | `"qwen2.5-0.5b-instruct-q5_k_m"` | This is a GGUF filename, not an Ollama model name |
| `config.py` → `OLLAMA_MODEL` | `"qwen2.5:3b"` | Not installed in Ollama |
| Available Ollama models | `qwen2.5:0.5b-instruct`, `qwen3-coder-next:cloud` | Only these are live |

`OllamaProvider.generate()` uses `self.config.model_name`. When `model_name="default"`, Ollama returns 404.

### The fix

Update `provider_config.json` to use the correct model name, then re-test.