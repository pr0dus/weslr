# WESLR_EXTERNAL_EVIDENCE_CHAT_V1_LIVE_STAGING_CHECKPOINT

**Date:** 2026-05-01 20:42 CEST
**Verdict:** `WESLR_EXTERNAL_EVIDENCE_CHAT_V1_LIVE_ON_STAGING`

---

## Section 1 — Verdict

**`WESLR_EXTERNAL_EVIDENCE_CHAT_V1_LIVE_ON_STAGING`**

External Evidence Chat V1 is live on staging.weslr.de (deploy/staging/weslr_demo_server.py).

---

## Section 2 — Runtime Reality

### Active Runtime

staging.weslr.de is served by **`deploy/staging/weslr_demo_server.py`**, not `main.py`.

This was a key architectural lesson: `main.py` can have a feature, but if staging uses a separate runtime, that feature is not live on staging until it is wired into the correct file.

### Integration Points

| Runtime | File | Evidence Bridge |
|---------|------|-----------------|
| OCW (live) | `main.py` | ✅ Wired — POST /chat handler |
| Staging | `deploy/staging/weslr_demo_server.py` | ✅ Wired — `do_POST` handler |

### Staging Integration Details

- **File:** `deploy/staging/weslr_demo_server.py`
- **Location:** Inside `do_POST(self)` — after `response = weslr_chat(message)`, before `_capture_signal()`
- **Field naming:** Uses `response.get("reply")` (not `payload.get("message")`) because staging server returns `{"success": ..., "reply": ...}` from `weslr_backend_contract.chat()`
- **Override fields:** `response["reply"]`, `response["path"]`, `response["response_contract"]`, `response["_evidence_metadata"]`
- **Guard:** `try/except` — bridge failure is silent pass, never crashes the request

---

## Section 3 — Live Test Result (OCW Confirmed at 20:39 CEST)

### Before/After Commits

- **Before:** `3e17a36` — generic explanation fallback fix
- **After:** `a50c1e7` — staging demo server evidence bridge wiring

### Service Restart

staging.weslr.de restarted at 20:39 CEST with new commit active.

### Live Query Results

| Query | Result |
|-------|--------|
| `What is entropy?` | `evidence_grounded_answer` — confirmed by `_evidence_metadata.evidence_used=true` |
| `Explain entropy very deeply.` | `evidence_grounded_answer` — confirmed by `source_count=5` |

### Evidence Metadata Captured

```json
{
  "evidence_used": true,
  "authority": "external_evidence_unverified",
  "truth_status": "unverified",
  "automatic_truth_write": false,
  "source_count": 5,
  "source_urls": [...],
  "search_attempted": true
}
```

---

## Section 4 — Guards Preserved (OCW Confirmed)

| Guard | Status |
|-------|--------|
| `What are you?` → `self_identity` | ✅ No evidence used |
| `What can you help me with?` → `capability_help` | ✅ No evidence used |
| self/system questions | ✅ Do not trigger search |
| `WESLR_SEARXNG_ENABLED=true` | ✅ Required for activation |
| SearXNG URL | ✅ `http://localhost:8888` |
| No Ollama | ✅ Confirmed — no LLM calls in bridge |
| No truth writes | ✅ `automatic_truth_write=false` on all outputs |
| No memory writes | ✅ No JSONL writes, no artifact storage |
| Disabled mode | ✅ Falls back silently (no user message yet) |

---

## Section 5 — Architecture Lesson

**`main.py` can have a feature but staging may not use it.**

Runtime identification must precede integration assumption:

1. **Identify the active runtime file** for the target environment before adding features
2. **Staging vs OCW:** staging.weslr.de uses `deploy/staging/weslr_demo_server.py` — a separate HTTP server from the OCW `main.py` Python HTTP server
3. **Both need wiring** — features added to `main.py` are not live on staging until `deploy/staging/weslr_demo_server.py` is also updated
4. **Future live-feature work** must include runtime identification as step 1 before assuming any integration is live

---

## Section 6 — Current Known Limitations

| Limitation | Status |
|------------|--------|
| Evidence remains external and unverified | 🔵 Active — `authority=external_evidence_unverified` |
| Results depend on SearXNG quality | 🔵 Active — no independent ranking layer |
| No source ranking/cross-validation | 🔵 Active — relies on SearXNG result order |
| No follow-up topic memory for "very deep" | 🔵 Active — context reset unless user restates |
| No citations UI polish | 🔵 Active — `_evidence_metadata` present but not surfaced in UI |
| Search-disabled falls back silently | 🔵 Active — no user-facing message when search is off |

---

## Section 7 — Next Possible Steps

Listed for future consideration — not implemented here:

1. **Evidence answer quality scoring** — rank/filter results by quality, not just SearXNG order
2. **Source trust/ranking layer** — weight sources by type (Wikipedia > random blog)
3. **Follow-up topic tracking** — maintain context across multi-turn evidence queries
4. **Citation display polish** — surface `_evidence_metadata.source_urls` in UI cleanly
5. **Search-disabled user message** — tell user why their query returned a fallback
6. **Rate limiting / trusted tester guard** — protect SearXNG from abuse before public rollout

---

## Commit History (Evidence Chat V1)

| Commit | Description |
|--------|-------------|
| `cf97435` | WESLR: add guarded evidence chat bridge v1 |
| `925f2d8` | WESLR: checkpoint evidence chat bridge v1 |
| `9595f6f` | WESLR: allow evidence bridge on confirmed-answer fallback |
| `3e17a36` | WESLR: allow evidence bridge on generic explanation fallback |
| `a50c1e7` | WESLR: wire evidence bridge into staging demo server |

**Total tests across evidence chain:** 129 passed across 6 test files