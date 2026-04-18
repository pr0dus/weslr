# STAGING_DEPLOYMENT.md

## Overview
Private test deployment for Weslr with local GGUF LLM inference via llama-server.

## Ports
- **LLM Server (Embedded)**: `127.0.0.1:18081/v1` (OpenAI-compatible API)
- **Health Check**: `http://127.0.0.1:18081/healthz` (404 - use `health()` function)

## Files Changed
| File | Change |
|------|--------|
| `config.py` | `CIRCLEFORGE_LLM_PROVIDER = "embedded"` (was "ollama") |
| `llm_runtime.py` | Updated `_generate_via_embedded_server()` with structured errors; Added `health()` and `health_endpoint()` |

## Commands to Start

### Start LLM Server
```bash
llama-server \
  -m /data/data/com.termux/files/home/.openclaw/workspace/models/qwen2.5-0.5b-instruct-q5_k_m.gguf \
  --host 127.0.0.1 \
  --port 18081 \
  -c 2048 \
  -n 180 \
  --threads 4
```

### Verify Health
```bash
/data/data/com.termux/files/usr/bin/python3 -c "
from llm_runtime import health
print(health())
"
```

### Test Chat
```bash
curl -s -X POST http://127.0.0.1:18081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-0.5b-instruct-q5_k_m.gguf","messages":[{"role":"user","content":"Hello"}],"temperature":0.7,"max_tokens":50}'
```

## Rollback Steps
If issues arise:
1. Stop server: `pkill -f "llama-server"`
2. Revert config: `CIRCLEFORGE_LLM_PROVIDER = "ollama"` (restore in config.py)
3. Restart application

## Status
- ✅ Local GGUF model operational
- ✅ Provider: `embedded`
- ✅ Health check: `healthy`
- ✅ Latency: ~1400-2100ms (first request slower)
- ✅ Repeated requests stable
- ✅ Model files excluded from git (`models/*.gguf` in .gitignore)

## Known Constraints
- Server must be running before application starts
- First request may be slower due to warmup
- Error handling returns structured JSON with error details
