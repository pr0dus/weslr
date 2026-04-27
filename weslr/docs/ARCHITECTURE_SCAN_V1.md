# WESLR Architecture Scan — V1

## Scope

Workspace: `/data/data/com.termux/files/home/.openclaw/workspace`
Git: main, 78 commits ahead of origin/master

---

## Core Architecture Layers (W1 → C9 + ISS)

| Layer | Name | Commit | Type |
|---|---|---|---|
| W1 | Front Door Deterministic Routing | — | Routing |
| C7 | Proposal Traceability | 3ac3aa2 | Traceability |
| C8 | Implementation Planning (core) | 3c67770 | Planning |
| C8 | C8 Integration (plan after approval) | 5ea0858 | Planning |
| C8Q | Plan Query (read-only) | bdfca09 | Query |
| C9 | Proposal-Decision-Plan Linkage | 73d905b | Linkage |
| ISS_V1 | ISS Diagnostic Records Foundation | c194856 | Diagnostics |
| ISSQ | ISS Diagnostics Query | 9c67cbf | Query |
| ISS_C3 | ISS Gap Visibility in C3 | ce5552d | Bridge |
| C5H | History-Aware Prioritization | 64fe39d | Prioritization |
| ISS_C4 | ISS Gap-Derived Suggestions in C4 | 5873898 | Bridge |
| STATE_CHECKPOINT | Read-Only Architecture Status | ec3c18d | Observability |
| OPERATOR_SURFACE | Unified System Overview | ecd5005 | Surface |

All layers: **read-only / non-executing** unless operator-approved.

---

## ISS Subsystem (V1)

### Components

| File | Purpose |
|---|---|
| `iss/diagnostic_records.py` | `make_probe_result()`, `make_gap_signal()`, `record_iss_diagnostic()`, `load_iss_diagnostics()` |
| `iss/probe_registry.py` | `get_probe_registry()` — 4 declarative probe stubs |
| `iss/probe_planning.py` | `create_probe_plan()` — declarative 4-step plans |
| `iss/probe_execution.py` | `execute_probe_simulated()` — governed simulated execution |
| `iss/iss_diagnostic_records.jsonl` | Append-only diagnostic log |

### Probe Registry (4 probes, all execution_allowed=False)

- `probe.front_door.chat` — routing — /chat deterministic routing
- `probe.trace.proposals` — traceability — proposal_trace.jsonl
- `probe.plans.non_executing` — planning — implementation_plans.jsonl
- `probe.iss.diagnostics` — diagnostics — iss_diagnostic_records.jsonl

### ISS Query Handlers (interpretation.py)

| Trigger | Path |
|---|---|
| `show iss probes` / `show probe registry` / `list probes` / `what can iss check` | `ISS_probe_registry_query` |
| `plan probe <id>` / `how would you check <id>` | `ISS_probe_plan` |
| `execute probe <id>` (no confirm) | `ISS_probe_execution` (requires confirmation) |
| `execute probe <id> confirm` | `ISS_probe_execution` (simulated, writes record) |

---

## Key Data Files

| File | Records | Purpose |
|---|---|---|
| `weslr/proposal_trace.jsonl` | 42 | C7 trace — proposal_created, proposal_decision |
| `weslr/implementation_plans.jsonl` | 5 | C8 plans — non-executing |
| `weslr/iss/iss_diagnostic_records.jsonl` | 3 | ISS diagnostics — probe results + gap signals |
| `weslr/operator_feedback_log.jsonl` | 0 | C5H feedback |
| `weslr_cdi_proposals.jsonl` | — | CDI proposals |
| `weslr_cdi_decisions.jsonl` | — | CDI decisions |

---

## Recent Commit Chain (V1 chain)

```
93259c0 WESLR ISS: add governed simulated probe execution
69794eb WESLR ISS: add non-executing probe planning
ecc161c WESLR ISS: add non-executing probe registry
6530be4 WESLR: fix ISS gap link in plan explanation
9266302 WESLR: add implementation plan explanation link
417cc4c WESLR: support approving ISS intake proposal ids
f0401e1 WESLR ISS: group intake proposal query output
82b93b9 WESLR ISS: add read-only intake proposal query
6ff1020 WESLR ISS: add controlled proposal intake from diagnostics
5135526 WESLR: normalize proposal ids in explanation queries
4550001 WESLR: add operator explanation layer v1
ecd5005 WESLR: add operator system overview surface
ec3c18d WESLR: add read-only architecture state checkpoint
5873898 WESLR ISS: surface gap-derived proposal suggestions (non-binding)
64fe39d WESLR C5: add history-aware prioritization
ce5552d WESLR ISS: bridge diagnostic gaps into C3 visibility
9c67cbf WESLR ISS: add read-only diagnostics query
c194856 WESLR ISS: add non-executing diagnostic record foundation
73d905b WESLR C9: add proposal-decision-plan trace linking
bdfca09 WESLR C8: add read-only implementation plan query
5ea0858 WESLR C8: integrate non-executing planning after approval
3c67770 WESLR C8: add non-executing implementation planning core
3ac3aa2 WESLR C7: integrate proposal traceability
```

---

## Properties

- All WESLR Python files: no automatic execution, no shell commands, no live probe logic
- All `execution_allowed: False` unless operator explicitly approves
- No learning — `learning_enabled: False` throughout
- Operator authority preserved at all layers
- No automatic proposal generation — suggestions only
- ISS gaps surface in C3/C4 but require operator conversion to proposals

---

## Files

```
weslr/
  ARCHITECTURE.md
  RELEASES.md
  docs/CANONICAL_BEHAVIOR_V1.md
  iss/
    diagnostic_records.py      # record + query ISS diagnostics
    probe_registry.py          # get_probe_registry()
    probe_planning.py          # create_probe_plan()
    probe_execution.py          # execute_probe_simulated()
    ISS_INTEGRATION_PLAN.md
    capability_scan.md
  operator_control/
    OPERATOR_COMMANDS.md
    OPERATOR_STATE.md
    REPO_GUARD.md
    SILENT_CONTINUITY_FREEZE.md
    TEST_DOCTRINE.md
    TEST_EXECUTION_RULES.md
  lineage/                     # lineage_inspector.py
  concept_graph/               # concept graph components
```

---

Scan completed: 2026-04-27