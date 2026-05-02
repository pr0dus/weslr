# WESLR Experiment Proposal Store V1 — Documentation

> Status: IMPLEMENTED — EXPERIMENTAL / NOT WIRED TO CHAT  
> Author: OCC (WESLR governed intelligence)  
> Created: 2026-05-02

---

## V1 Scope

- **Schema + validation** — `weslr/experiment_proposal_schema.py`
- **Append-only store** — `weslr/experiment_proposal_store.py`
- **Search-insight proposal from timeline themes** — `weslr/experiment_proposal_generator.py`
- **Self-improvement proposals (SI-1 through SI-6)** — same module
- **Capability registry entries** — `experiments.propose` + `experiments.review`
- **Unit tests** — `weslr/tests/test_experiment_proposal_store_v1.py`, `weslr/tests/test_experiment_proposal_generator_v1.py`

---

## Schema

### Record Type: experiment_proposal_v1

All proposals are append-only JSONL records in `weslr/experiment_proposals.jsonl`.

Key fields:

| Field | Values | Notes |
|---|---|---|
| `record_type` | `"experiment_proposal_v1"` | Required |
| `proposal_id` | `EXP-YYYYMMDD-NNN` | Auto-generated |
| `type` | `search_insight` \| `physical_action` \| `simulation_run` \| `self_improvement_suggestion` | Required |
| `execution_status` | `pending` \| `approved` \| `executed` \| `failed` \| `rejected` \| `stale` | Default: `pending` |
| `risk_level` | `low` \| `medium` \| `high` \| `critical` | Required |
| `confidence` | 0.0–1.0 | Required |
| `confidence_reasons` | List[str] | Required — explains confidence score |
| `requires_operator_approval` | `true` | Always true in V1 |
| `automatic_execution` | `false` | Always `false` — no auto-execution |
| `hidden_learning` | `false` | Always `false` — no hidden learning |
| `raw_prompt_stored` | `false` | Always `false` — no raw prompt storage |
| `authority` | `"experiment_proposal_only"` | Required |

### Type-Specific Rules

- **`physical_action`**: always forces `requires_operator_approval=true`, `operator_approval_required=true`, `automatic_execution=false`
- **`self_improvement_suggestion`**: always forces `requires_operator_approval=true`, `operator_approval_required=true`
- **`search_insight`**: V1 generator produces this type from timeline themes only

### Proposal ID Format

```
EXP-YYYYMMDD-NNN
  YYYY = year
  MM = month
  DD = day
  NNN = 3-digit sequential counter, zero-padded, reset each day
```

ID counter is per-process (not persistent). External runner uses the same scheme.

---

## Append-Only Queue

`weslr/experiment_proposals.jsonl` is append-only. Status changes are recorded as separate event types:

- `experiment_proposal_status_update_v1` — status transitions
- `experiment_result_v1` — execution results

This preserves complete audit history. Old lines are never mutated.

### Deduplication

Before appending, the store checks a deduplication key:
```
type | normalized_title | timeline_id | related_capability
```
If a matching proposal already exists, the append is skipped.

---

## Generator

### V1 Behavior

1. **Search-insight from timeline** — reads `user_timeline_memory`, classifies themes via `proactive_suggestions.classify_timeline_theme`, maps evidence/continuity/capability_discovery/governance/experiment themes to a search_insight proposal. Default: `dry_run=True`.

2. **Self-improvement proposals (SI-1 through SI-6)** — deterministic triggers:
   - SI-1: 3 rejected physical_action proposals
   - SI-2: 3 failed results of same type
   - SI-3: 3+ stale pending proposals
   - SI-4: 5+ ignored proactive suggestions
   - SI-5: experiment results not consumed into timeline
   - SI-6: 3+ consecutive low-confidence proposals

3. **No physical_action generation** in V1 generator (schema supports it; generation is out of scope)

4. **No execution** — generator is proposal-only

---

## Safety Guarantees

- `automatic_execution: false` on all proposals
- `raw_prompt_stored: false` on all proposals
- `hidden_learning: false` on all proposals
- No Ollama imports, no external calls
- No modification of existing governance JSONL files
- Physical action and self-improvement always require operator approval
- Forbidden-field validator rejects records with `raw_prompt`, `transcript`, `password`, `token`, etc.

---

## Out of Scope

- ❌ No /chat integration
- ❌ No external runner
- ❌ No automatic proposal generation loop
- ❌ No status update/result event handling
- ❌ No physical action execution
- ❌ No Ollama or external service calls

---

## Usage Example

```python
from weslr.experiment_proposal_generator import (
    build_search_insight_proposal_from_timeline,
    build_self_improvement_proposal,
    generate_experiment_proposals,
)

# dry-run: returns proposal dict without writing
result = build_search_insight_proposal_from_timeline(user_id="arthur", dry_run=True)
print(result["proposal"]["proposal_id"], result["status"])

# self-improvement from SI rule
result = build_self_improvement_proposal(rule_id="SI-1", dry_run=True)
print(result["proposal"]["title"])

# List pending proposals
from weslr.experiment_proposal_store import load_experiment_proposals
pending = load_experiment_proposals(status="pending")
for p in pending:
    print(p["proposal_id"], p["type"], p["title"])
```

---

## Files

| File | Purpose |
|---|---|
| `weslr/experiment_proposal_schema.py` | Schema validation + proposal ID generation |
| `weslr/experiment_proposal_store.py` | Append-only store with read/query API |
| `weslr/experiment_proposal_generator.py` | Proposal generation from timeline + SI rules |
| `weslr/tests/test_experiment_proposal_store_v1.py` | Unit tests for schema + store |
| `weslr/tests/test_experiment_proposal_generator_v1.py` | Unit tests for generator |
| `weslr/capability_registry.json` | Updated with `experiments.propose` + `experiments.review` |
