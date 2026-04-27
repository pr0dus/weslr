# ISS Integration Plan
Source: `weslr/iss/capability_scan.md`
Date: 2026-04-26

---

## 1. ISS Responsible Scope (Keep)

### Probe Execution
- `probe_exec.py` runs commands, captures stdout/stderr/exit
- Normalizes raw subprocess output into structured probe results
- No business logic — only command execution and raw signal capture

### Raw Signal Normalization
- Convert subprocess exit codes, stdout/stderr content into typed signals
- `Permission denied` → BROKEN signal
- Empty output → DEGRADED signal
- Normal output → OK signal
- Pure transformation, no inference

### Domain-Specific Status Mapping
- Map raw signals to domain status taxonomy (OK/DEGRADED/BROKEN)
- Deterministic — no speculation, no LLM
- Status thresholds defined per-domain (exec uses 3-class; other domains may differ)

### ISS Must NOT Own
- Storage (delegate to AuditLedgerEngine)
- Proposal lifecycle (delegate to SuggestionBox)
- Capability gating (delegate to CapabilityBoundaryEngine)
- Execution eligibility (delegate to ProofGateEngine)
- Safety checks (delegate to SafetyGateway)
- Human-readable reporting beyond raw signal output

---

## 2. Reuse Existing Weslr Systems

| System | ISS Integration Point | Method |
|---|---|---|
| `AuditLedgerEngine` | Record probe results | `record_*()` methods (record_proposal_created, etc.) or extend with probe-specific event type |
| `weslr/observability.AuditEvent` | Emit probe lifecycle events | `AuditEvent` objects via observability pipeline |
| `SuggestionBox` | ISS recommendations become proposals | `submit_request()` with ISS findings as structured request |
| `CapabilityBoundaryEngine` | Gate probe execution | `check_capability()` called before probe runs |
| `ProofGateEngine` | Block ISS actions requiring operator approval | `get_execution_eligibility()` before any write action |
| `SafetyGateway` | Sanity-check ISS output before routing | `check_output()` before issuing recommendation |

---

## 3. Deprecate / Convert

### `memory/iss_records.jsonl` — DEPRECATE
- Standalone JSONL logging duplicates `AuditLedgerEngine`
- **Action:** Stop writing to `iss_records.jsonl`
- **Instead:** Route through `AuditLedgerEngine.record_proposal_created()` or extend with `record_probe_result()` event type

### Standalone report-only flow — CONVERT
- `report.py` currently prints text and exits; no downstream consumer
- **Action:** `report.py` must emit via `AuditEvent` through observability.py
- Do not print text as final output — text is for operator review, not the system

### Duplicate evaluator logic — CONSOLIDATE where possible
- `WeslrAssessment._calculate_fit_score()` and `ConsciousnessDetector` have classification logic that could parameterize ISS evaluator
- **Action:** Do not rewrite; instead ensure ISS evaluator output is consumable by existing `WeslrAssessment` input interface
- ISS probe result → `WeslrAssessment.assess_request()` pathway should be valid

---

## 4. Next Safe Implementation Step

**Create: `weslr/iss/adapter.py`**

Responsibilities:
1. Accept evaluator output (the structured dict from `evaluator.py`)
2. Transform into `AuditLedgerEngine`-compatible event format
3. Call `AuditLedgerEngine.record_*()` or equivalent
4. Emit `AuditEvent` via observability pipeline
5. Gate probe execution via `CapabilityBoundaryEngine.check_capability()` before running probe

Constraints:
- Do NOT build proposal layer yet
- Do NOT connect to SuggestionBox yet
- Do NOT touch ProofGateEngine or SafetyGateway yet
- Scope is only: probe → adapter → AuditLedger + observability

Success criteria:
- `python3 weslr/iss/probe_exec.py | python3 weslr/iss/evaluator.py | python3 weslr/iss/adapter.py` produces a ledger entry
- `AuditLedgerEngine` query confirms the probe result was recorded
- No new files created outside `weslr/iss/`

After adapter is stable and validated:
- Then connect to SuggestionBox for recommendation layer
- Then integrate CapabilityBoundaryEngine for probe gating
- Then add ProofGateEngine for execution eligibility