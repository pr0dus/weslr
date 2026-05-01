# WESLR Capability Registry + Router V1 Checkpoint

**Date:** 2026-05-01
**Commit:** `1c4f963`
**Verdict:** WESLR_CAPABILITY_REGISTRY_ROUTER_V1_IMPLEMENTED_READ_ONLY

---

## Files

| Role | File |
|------|------|
| Registry data | `weslr/capability_registry.json` |
| Registry module | `weslr/capability_registry.py` |
| Router module | `weslr/capability_router.py` |

---

## Test Results

| Test Suite | Result |
|------------|--------|
| `weslr/tests/test_capability_registry_v1.py` | ✅ 38 passed |
| `weslr/tests/test_capability_router_v1.py` | ✅ 33 passed |

---

## Registry Entries (10 total)

| capability_id | category | label | status | authority | automatic_change |
|---------------|----------|-------|--------|-----------|-----------------|
| system.identity | system/state | System Identity | live | deterministic | false |
| system.capabilities | commands/help | Capability Help | live | deterministic | false |
| evidence.search | evidence/search/sources | Evidence Search | live_on_staging | external_evidence_unverified | false |
| evidence.sources | evidence/search/sources | Source Attribution | partial | external_evidence_unverified | false |
| system.state | system/state | System State | read_only | read_only | false |
| operator.attention | operator/attention/review | Operator Attention | read_only | attention_only | false |
| governance.boundaries | governance/safety | Governance Boundaries | read_only | read_only | false |
| analysis.composite | system/state | Composite Analysis | read_only | analysis_only | false |
| experiments.plan | experiments/learning | Experiment Planning | spec_only | proposal_only | false |
| projects.plan | projects/planning | Project Planning | partial | planning_only | false |

---

## Authority Boundary

- **Registry:** READ-ONLY — no writes, no suggestions, no LLM calls
- **Router:** ROUTING_ONLY — classifies messages into capability IDs, does not execute
- **automatic_change:** `false` on all entries and routing results

---

## Integration Status

- ❌ NOT wired into `/chat`
- ❌ NO execution (router is a self-map and classifier, not an executor)
- ❌ NO JSONL writes
- ❌ NO Ollama / LLM calls

---

## Note

Capability Router V1 is a **self-map and routing classifier**, not an executor.
It reads the registry and maps user messages to capability IDs — it does not run capabilities.

---

## What This Enables

- Capability Welcome Surface V1 (next step)
- Capability Suggestions (future)
- `/help` and `/capabilities` command surface (future)
- WESLR can answer "what can you do?" from registry data, not hard-coded lists