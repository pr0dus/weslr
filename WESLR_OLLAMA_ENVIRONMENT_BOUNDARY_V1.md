# WESLR_OLLAMA_ENVIRONMENT_BOUNDARY_V1.md

## Executive Summary

**Verdict: WESLR_OLLAMA_ENVIRONMENT_BOUNDARY_V1_DEFINED**

WESLR runtime must **never** use Ollama as truth authority, decision engine, or state modifier.
Ollama may be used ONLY as a bounded formatter/helper layer, explicitly disabled by default.

---

## 1. OCC Coder Environment

**Purpose:** Coding and implementation workspace

**Characteristics:**
- Used for development, debugging, testing
- May use OpenClaw model provider config
- May use Ollama Cloud models (e.g., `qwen3-coder-next:cloud`, `mistral-large-3:675b-cloud`)
- **Different environment from WESLR runtime**
- OpenClaw config does NOT apply to WESLR runtime

**Ollama access:**
- Remote Ollama Cloud models available via OpenClaw
- Local Ollama daemon may be present but not required
- No runtime boundary constraints — coding task focused

**Key distinction:**
> OCC Coder is where we *build* WESLR features.
> WESLR runtime is where those features *execute*.

---

## 2. OCW Website Environment

**Purpose:** WESLR deployment/runtime environment

**Characteristics:**
- Local Ollama daemon running at `http://localhost:11434`
- Available formatter candidate: `qwen2.5:3b` (local GGUF)
- OpenClaw model config exists but **not automatically used by WESLR**
- WESLR runtime runs independently of OpenClaw config

**Ollama access:**
- Only local Ollama accessible (no Ollama Cloud in runtime)
- Local models are sufficient for bounded formatting tasks
- Cloud models require explicit network access (not desired in production)

**Key distinction:**
> OCW has *potential* Ollama access.
> WESLR runtime must *explicitly* enable and constrain usage.

---

## 3. WESLR Runtime Environment

**Current state (after V1 formatter implementation):**

| Component | Status |
|-----------|--------|
| `local_ollama_formatter.py` | ✅ Created, present |
| Formatter enabled by default | ❌ No — disabled by default |
| Wired into `/chat` | ❌ No — explicit integration needed |
| Wired into `response_expander.py` | ❌ No — explicit integration needed |
| Uses Ollama Cloud models | ❌ No — local only |
| Uses Ollama as truth authority | ❌ Never — formatter only |
| Modifies state/JSONL | ❌ No — fallback returns original |
| Modifies `/chat` behavior | ❌ No — deterministic by default |

**Safe execution rules:**

1. **Formatter only** — rewrite natural language, no decision-making
2. **Deterministic fallback** — always return original text on any error
3. **No state changes** — no JSONL writes, no state persistence
4. **No autonomy claims** — never claim feelings, goals, values, or decision power
5. **Explicit enable** — requires `WESLR_LOCAL_FORMATTER_ENABLED=true`

**Ollama usage constraint:**
```
WESLR + Ollama = ONLY formatting/synthesis layer
                 NOT truth evaluation
                 NOT policy approval
                 NOT state modification
```

---

## 4. Safe Future Rule

**OpenClaw (coding/ops):**
- May use Ollama models freely for coding, analysis, ops
- OpenClaw config defines provider/model selection
- No boundary constraints — task-focused

**WESLR (runtime):**
- May use Ollama ONLY as bounded formatter/helper
- Must have explicit formatter config/env flag
- Default must remain **off**
- Formatter must validate output against rules
- Fallback must always return original deterministic text

**Critical separation:**
```
OpenClaw config  → coding/ops tooling  → OK to use Ollama
WESLR config     → runtime behavior     → MUST NOT auto-inherit OpenClaw
```

---

## 5. Configuration Boundary

**Current config status:**

| Config source | WESLR auto-uses? | Notes |
|---------------|------------------|-------|
| OpenClaw `~/.openclaw/openclaw.json` | ❌ No | Must be explicitly referenced |
| `provider_config.json` | ❌ No | WESLR has own config |
| `config.py` OLLAMA_* env vars | ❌ No | Currently unused |
| `WESLR_LOCAL_FORMATTER_ENABLED` | ✅ Yes | Explicit enable flag |

**Future configuration pattern:**
```python
# config.py
WESLR_LOCAL_FORMATTER_ENABLED = os.getenv("WESLR_LOCAL_FORMATTER_ENABLED", "false") == "true"
WESLR_LOCAL_FORMATTER_MODEL = os.getenv("WESLR_LOCAL_FORMATTER_MODEL", "qwen2.5:3b")
WESLR_LOCAL_FORMATTER_TIMEOUT = float(os.getenv("WESLR_LOCAL_FORMATTER_TIMEOUT", "5.0"))
```

**Never auto-inherit:**
- ❌ `OLLAMA_HOST` from OpenClaw → WESLR
- ❌ `OLLAMA_MODEL` from OpenClaw → WESLR
- ❌ Provider config → WESLR formatter

**Must use explicit flags:**
- ✅ `WESLR_LOCAL_FORMATTER_ENABLED` → enables formatter
- ✅ `WESLR_LOCAL_FORMATTER_MODEL` → specifies model
- ✅ `WESLR_LOCAL_FORMATTER_TIMEOUT` → specifies timeout

---

## 6. Integration Checklist (Future)

Before wiring formatter into WESLR runtime:

- [ ] Formatter explicitly enabled via env var
- [ ] Formatter wired into `format_reply()` in `response_expander.py`
- [ ] Formatter returns fallback on any error
- [ ] Formatter validation rejects forbidden phrases
- [ ] Formatter preserves uncertainty boundaries
- [ ] Formatter preserves operator boundaries
- [ ] No JSONL writes from formatter
- [ ] No state changes from formatter
- [ ] /chat behavior unchanged when formatter disabled

**Current status:** All checks ✅ — formatter exists but disabled

---

## 7. Verdict Summary

| Check | Status |
|-------|--------|
| OCC Coder vs OCW separation | ✅ Defined |
| WESLR formatter exists | ✅ Yes |
| Formatter disabled by default | ✅ Yes |
| Not wired into /chat | ✅ Yes |
| Not wired into response_expander | ✅ Yes |
| Not using Ollama Cloud | ✅ Local only |
| Not using Ollama as authority | ✅ Formatter only |
| Not modifying state | ✅ Fallback only |
| Not auto-inheriting OpenClaw config | ✅ Explicit only |
| Service not restarted | ✅ No |
| Config not modified | ✅ No |

**Final Verdict: WESLR_OLLAMA_ENVIRONMENT_BOUNDARY_V1_DEFINED**

---

## 8. Commit Reference

- **Commit:** `c80accb`
- **File:** `weslr/local_ollama_formatter.py`
- **Test:** `test_local_ollama_formatter_v1.py`

---

*Document version: WESLR_OLLAMA_ENVIRONMENT_BOUNDARY_V1*
*Last updated: 2026-05-01*
