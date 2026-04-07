# WESLR Architecture Contract

Internal architecture anchor for implementation continuity.

**Version:** 1.0.0  
**Last Updated:** 2026-04-07  
**Current Sealed Commit:** `3a31b1b2cbfebb9e86bb905de2ca2735f51e44fb` (v69)

---

## 1. WESLR Identity

WESLR is a **high-trust adaptive intelligence platform** designed for multi-node operation.

### Core Identity Principles

| Principle | Description |
|-----------|-------------|
| **Deterministic Trusted Core** | All execution governed by explicit state machines and validation rules |
| **Adaptive Intelligence Layer** | Domain-adaptive reasoning that identifies, transfers, and applies domain constraints |
| **Model-Assisted, Not Model-Dependent** | Fallback chains with deterministic fallback logic when model unavailable |
| **Governing Growth** | Progressive capability expansion with explicit gate validation |

### Non-Goals (Explicitly Out of Scope)

- **No autonomous execution** — all execution requires explicit envelope lifecycle
- **No scheduler/task engine** — no background workers, cron, or timers
- **No distributed consensus** — no voting, leader election, or consensus protocols
- **No telemetry backend** — observability export hooks only, no external service
- **No product runtime expansion** — operator workflow only, no external product binding

---

## 2. Current Sealed Architecture Stack (v61-v69)

### Layer Sequence

| Version | Name | Purpose | Status |
|---------|------|---------|--------|
| v61 | Remote Action Proposal | Safe proposal/gate/escalate without execution | ✅ Sealed |
| v62 | Controlled Execution Envelope | Approval-gated, trust-first execution wrapper | ✅ Sealed |
| v63 | Remote Execution Receipt | Acknowledgment protocol for execution completion | ✅ Sealed |
| v64 | Distributed Execution Integration | Unified flow across v61-v63 | ✅ Sealed |
| v65 | Remote Node Handshake | Formal handshake/session establishment | ✅ Sealed |
| v66 | Handshake-Execution Integration | Handshake validation before envelope creation | ✅ Sealed |
| v67 | Execution Timeout / Deadline Propagation | Deadline tracking and breach handling | ✅ Sealed |
| v68 | Distributed Execution Telemetry | Passive observability for flow events | ✅ Sealed |
| v69 | Distributed Telemetry Export Hooks | Structured export for operator-readable observability | ✅ Sealed |

### Flow Lifecycle

```
Proposal → Handshake → Envelope → Gates → Dispatch → Receipt → Completion
   ↓         ↓            ↓          ↓          ↓         ↓         ↓
Submit  Request     Create    Evaluate   Send     Receive   Complete
```

### Correlation Continuity

Every stage maintains correlation via:
- `flow_id` — end-to-end flow identifier
- `request_id` — execution envelope identifier
- `handshake_id` — node handshake identifier
- `deadline_id` — timeout tracking identifier

---

## 3. Core Architectural Rules

### Mandatory Rules (All Layers)

| Rule | Description | Enforced By |
|------|-------------|-------------|
| **Additive Only** | New layers must not break existing behavior | Backward compatibility tests |
| **Reversible** | Single file removal must cleanly remove layer | Unit test coverage |
| **Trust-First** | Trust/health validation before any execution | TrustHealthGate in each layer |
| **No Uncontrolled Remote Execution** | All execution requires explicit envelope lifecycle | ExecutionGates in envelope layer |
| **No Scheduler/Task Engine** | No background workers, cron, or timers | Operator workflow enforcement |
| **No TIA/C#** | No third-party integrations or C# code | REPO_GUARD.md |

### Governance Rules

| Rule | Description |
|------|-------------|
| **Repo Truth Authoritative** | Git state is the single source of truth |
| **Tests Protect Doctrine** | Tests validate intended behavior, not implementation accidents |
| **Operator Workflow Only** | All operations are operator-initiated, no autonomous execution |

---

## 4. Distributed Architecture Boundaries

### What Current Stack Supports

| Capability | Status | Notes |
|------------|--------|-------|
| Proposal/Gating | ✅ | v61: proposals, rejections, approvals, re-escalation |
| Handshake | ✅ | v65: node identity, trust, health, protocol compatibility |
| Execution Envelope | ✅ | v62: approval-gated, rollback-aware, traceable |
| Receipt/Acknowledgment | ✅ | v63: dispatch, completion, failure, rollback receipts |
| Deadline/Timeout | ✅ | v67: deadline tracking, breach handling, automatic rollback |
| Telemetry | ✅ | v68: passive event emission, correlation by IDs |
| Export Hooks | ✅ | v69: snapshot, flow trace, metrics, diagnostics |

### Explicitly Out of Scope

| Capability | Reason | Alternative |
|------------|--------|-------------|
| Distributed Consensus | No voting, leader election, or consensus | Operator workflow decision |
| Scheduler/Task Engine | No background workers, cron, timers | Operator-initiated workflow |
| Telemetry Backend | No external service, only export hooks | Operator ingests exported JSON |
| Dashboard/UI | No visualization layer | Operator-readable JSON/text |
| Product Runtime Expansion | No external product binding | WESLR operator workflow only |

---

## 5. Current Remaining Bottleneck Families

### Active Bottlenecks (WESLR Core Layer)

| Bottleneck | Status | Description |
|------------|--------|-------------|
| Scientific Knowledge Assimilation Expansion | Active | Expand knowledge assimilation capabilities |
| Distributed Multi-Node Deployment | Active | Enable true multi-node distributed operation |
| Real World External Orchestration | Active | External system integration patterns |
| Cross Instance Continuity Sync | Active | Continuity synchronization across instances |

### Archived/External Bottlenecks

| Scope | Items |
|-------|-------|
| TIA | None |
| Industrial Slice | None |

---

## 6. Implementation Workflow Contract

### Phase 1: Planning (Pre-Implementation)

1. **Repo Verification**
   - Verify `pwd` matches authoritative workspace
   - Confirm `git rev-parse --show-toplevel` matches repo root
   - Check `git branch --show-current` and `git rev-parse HEAD`
   - Run `git status --short` to confirm working tree state

2. **File Plan**
   - Identify required file(s) for new layer
   - Confirm naming convention (`weslr/<layer>.py`)
   - Confirm test naming convention (`weslr/test_<layer>.py`)

3. **Implementation Scope**
   - Define class structure with docstrings
   - Define data models (dataclasses, enums)
   - Define public interfaces (methods, exports)
   - Define audit trace points
   - Define telemetry event types

4. **Test Plan**
   - Model tests (`Test<Layer>Model`)
   - Behavior tests (`Test<Layer>Behavior`)
   - Integration tests (`Test<Layer>Integration`)
   - Backward compatibility tests (`Test<Layer>BackwardCompatibility`)

### Phase 2: Completion (Post-Implementation)

1. **Test Execution**
   - Run all new tests: `python -m unittest weslr.test_<layer> -v`
   - Run all existing tests: `python -m unittest weslr.test_<existing> -v`
   - Verify 100% pass rate for all tests

2. **Exact Files Changed**
   - Report exact file paths
   - Report line counts added/modified

3. **Exact Tests Run/Results**
   - Report test count
   - Report pass/fail rate
   - Report specific failures if any

4. **Exact Full Commit Hash**
   - Commit message must include test summary
   - Report exact commit hash from `git rev-parse HEAD`

5. **Scope Confirmation**
   - Confirm WESLR scope only
   - Confirm no TIA/C#
   - Confirm additive only
   - Confirm no scheduler/task engine

### Clean Scope Requirement

- **All files must be tracked in git**
- **No uncommitted changes allowed**
- **No untracked files allowed** (except operator workflow artifacts)
- **All new layers must have corresponding test files**

### Seal Requirements

Commit only after all of:

1. ✅ All behavior tests pass
2. ✅ All integration tests pass
3. ✅ All backward compatibility tests pass
4. ✅ Git status clean (no untracked files, no uncommitted changes)
5. ✅ Commit hash from authoritative repo root
6. ✅ Layer documentation in ARCHITECTURE.md updated

---

*WESLR Architecture Contract v1.0.0*
