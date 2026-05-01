# WESLR External Evidence Pipeline V1 — Implementation Checkpoint

**Date:** 2026-05-01
**Verdict:** `WESLR_EXTERNAL_EVIDENCE_PIPELINE_V1_IMPLEMENTED_DISABLED_READ_ONLY`

---

## Components

### 1. Evidence Needed Detector V1

- **File:** `weslr/evidence_needed_detector.py`
- **Tests:** `test_evidence_needed_detector_v1.py` — 27 passed
- **Status:** IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT
- **Authority:** `classification_only`
- **Functions:** `classify_evidence_need()`, `build_evidence_needed_response()`
- **Need types:** definition_request, open_knowledge, source_request, lookup_request, latest_information
- **No search adapter yet:** Detects evidence need but does not perform web search
- **No /chat integration:** Standalone classifier, not yet routed from /chat
- **No Ollama:** No LLM calls
- **No JSONL writes:** Read-only classification only

### 2. SearXNG Search Adapter V1

- **File:** `weslr/searxng_search_adapter.py`
- **Tests:** `test_searxng_search_adapter_v1.py` — 26 passed
- **Status:** IMPLEMENTED DISABLED-BY-DEFAULT / NOT WIRED TO CHAT
- **Authority:** `external_evidence_unverified`
- **Functions:** `is_searxng_enabled()`, `get_searxng_base_url()`, `build_search_url()`, `normalize_searxng_result()`, `search_searxng()`
- **Enable with:** `WESLR_SEARXNG_ENABLED=true`
- **Default URL:** `http://localhost:8888` (override with `WESLR_SEARXNG_URL`)
- **No truth writes:** Results are evidence only, never written to state
- **No /chat integration:** Standalone adapter, not yet routed from /chat
- **No Ollama:** No LLM calls
- **No JSONL writes:** Read-only adapter, no file writes

### 3. Evidence Packet Builder V1

- **File:** `weslr/evidence_packet_builder.py`
- **Tests:** `test_evidence_packet_builder_v1.py` — 20 passed
- **Status:** IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT
- **Authority:** `external_evidence_unverified`
- **Truth status:** `unverified`
- **Functions:** `build_evidence_packet()`, `summarize_evidence_packet()`
- **Input:** `searxng_search_response_v1` (ok=true, at least one result)
- **Output:** `external_evidence_packet_v1` with results truncated and unsafe fields stripped
- **Max content length:** 2000 chars per result
- **Safe fields only:** title, url, content, source, authority
- **No truth writes:** `automatic_truth_write=false` on all packets
- **No /chat integration:** Standalone builder, not yet routed from /chat
- **No Ollama:** No LLM calls
- **No JSONL writes:** Read-only builder, no file writes

### 4. Evidence Answer Builder V1

- **File:** `weslr/evidence_answer_builder.py`
- **Tests:** `test_evidence_answer_builder_v1.py` — 23 passed
- **Status:** IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT
- **Authority:** `external_evidence_unverified`
- **Truth status:** `unverified`
- **Functions:** `build_evidence_answer()`, `build_no_evidence_answer()`
- **Input:** `external_evidence_packet_v1` (safe_for_answer_builder=true, at least one result)
- **Output:** `external_evidence_answer_v1` with cautious user-facing answer draft
- **Depths:** brief (2-3 sentences), normal (concise paragraph + sources), deep (multi-part)
- **Boundary wording:** Always includes "Based on external search results — not stored WESLR truth"
- **No invented facts:** Uses only title/content/url from packet, no fabrication
- **No truth writes:** `automatic_truth_write=false` on all answers
- **No /chat integration:** Standalone builder, not yet routed from /chat
- **No Ollama:** No LLM calls
- **No JSONL writes:** Read-only builder, no file writes

### 5. External Evidence Pipeline V1

- **File:** `weslr/evidence_pipeline.py`
- **Tests:** `test_evidence_pipeline_v1.py` — 14 passed
- **Commit:** `b6e1b54`
- **Status:** IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT
- **Authority:** `external_evidence_unverified`
- **Truth status:** `unverified`
- **Functions:** `run_evidence_pipeline()`
- **Pipeline:** Evidence Needed Detector → SearXNG Search Adapter → Evidence Packet Builder → Evidence Answer Builder
- **Search disabled by default:** `WESLR_SEARXNG_ENABLED=true` required to activate
- **No truth writes:** `automatic_truth_write=false` on all pipeline outputs
- **No /chat integration:** Standalone orchestrator, not yet routed from /chat
- **No Ollama:** No LLM calls
- **No JSONL writes:** Read-only pipeline, no file writes

---

## Current Behavior

### Search disabled result for "What is entropy?"

```
run_evidence_pipeline("What is entropy?")

→ reason: "search_disabled"
→ search_attempted: False
→ answer.answer: "External search is not enabled. I don't have external evidence to draw from."
→ answer.safe_for_user: True
```

### Mocked enabled search result for "What is entropy?"

```
run_evidence_pipeline("What is entropy?", depth="normal")

→ reason: "ok"
→ search_attempted: True
→ answer.answer: "Based on external search results for "What is entropy?" — not stored WESLR truth: In thermodynamics, entropy is a thermodynamic property defined for thermodynamic systems. Other sources include: Entropy (information theory)."
→ answer.source_count: 2
→ answer.safe_for_user: True
```

---

## Constraints Enforced

| Constraint | Status |
|------------|--------|
| No /chat integration | ✅ Standalone only |
| No JSONL writes | ✅ Read-only pipeline |
| No truth writes | ✅ `automatic_truth_write=false` on all outputs |
| No memory writes | ✅ No writes of any kind |
| No Ollama | ✅ No LLM calls anywhere |
| No live web calls in tests | ✅ All search mocked |
| Search disabled by default | ✅ `WESLR_SEARXNG_ENABLED=true` required |
| Default SearXNG URL | ✅ `http://localhost:8888` |

---

## Test Summary

| Component | Tests | Passed |
|-----------|-------|--------|
| Evidence Needed Detector V1 | test_evidence_needed_detector_v1.py | 27 |
| SearXNG Search Adapter V1 | test_searxng_search_adapter_v1.py | 26 |
| Evidence Packet Builder V1 | test_evidence_packet_builder_v1.py | 20 |
| Evidence Answer Builder V1 | test_evidence_answer_builder_v1.py | 23 |
| External Evidence Pipeline V1 | test_evidence_pipeline_v1.py | 14 |
| **Total** | | **110** |

---

## Verdict

**`WESLR_EXTERNAL_EVIDENCE_PIPELINE_V1_IMPLEMENTED_DISABLED_READ_ONLY`**

All five components implemented and tested. Pipeline is read-only, disabled-by-default, and not wired into `/chat`. No truth claims, no JSONL writes, no Ollama, no live web calls in tests.