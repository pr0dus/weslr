# CircleForge Self-Modification

## Purpose

This document defines how CircleForge entities should eventually inspect and modify their own local machinery safely.

Self-modification is important because a richer world should allow an entity to notice:
- a missing capability
- a fragile subprocess
- a weak helper module
- repeated wasted effort
- an interface mismatch

and respond by improving its own means.

This must be done without turning the system into opaque autonomy theatre.

---

## Core principle

Self-modification should be:
- local
- inspectable
- attributable
- reversible
- rate-limited
- testable
- operator-visible

If those conditions are not met, it should not happen automatically.

---

## What counts as self-modification

Examples:
- replacing a weak helper module
- generating a wrapper around a recurring subprocess
- adding a parser for repeated output formats
- creating a local protocol file for stable handoffs
- splitting a large helper into smaller pieces
- attaching a local test/check to a fragile tool
- retiring a useless component

Non-examples:
- arbitrary repo-wide rewrites with no reasoning
- silent mutation of core behavior with no audit trail
- irreversible destructive edits without checkpointing

---

## Modification targets

### Tier 1 — Safe local targets
Can eventually be modified with lighter safeguards:
- agent-local helper modules
- agent-local wrappers
- local utility scripts
- local formatting helpers
- private notes/specs

### Tier 2 — Shared but bounded targets
Require stronger checks:
- shared tools
- public protocols
- project-local infrastructure files
- reusable modules used by multiple agents

### Tier 3 — Sensitive core targets
Require explicit proposal/review by default:
- `main.py`
- `sim.py`
- `agent_runtime.py`
- world model definitions
- scoring logic
- operator control surfaces
- safety/rollback infrastructure

---

## Self-modification pipeline

## 1. Detect pressure
A modification should start from pressure such as:
- repeated failure
- repeated friction
- repeated manual workaround
- repeated dependency on another agent for the same task
- low signal quality from a subprocess
- repeated mismatch between intention and output

## 2. Form a proposal
Proposal should answer:
- what is broken or missing?
- what object/path is affected?
- what change is proposed?
- why is it expected to help?
- what are the risks?
- how can success be measured?

## 3. Create checkpoint
Before applying the change:
- snapshot or backup affected files
- record proposal id
- record baseline metrics/state

## 4. Apply in bounded scope
Apply only to the intended files/objects.
No open-ended cascading rewrite.

## 5. Test or validate
At minimum:
- syntax validity
- file existence
- expected output shape

Preferably also:
- compare before/after behavior
- rerun failing scenario
- record whether friction reduced

## 6. Record outcome
Store:
- success/failure
- observed effect
- rollback info
- whether change should remain private or become shared

---

## Proposal object shape

Recommended future `SelfModificationProposal` fields:
- `id`
- `agent_id`
- `created_at`
- `target_path` or `target_object`
- `scope` — private | shared | core
- `pressure_source`
- `problem_summary`
- `proposed_change`
- `expected_benefit`
- `risk_level`
- `checkpoint_ref`
- `status` — proposed | approved | applied | validated | reverted | rejected
- `validation_notes`

---

## Trigger conditions

Good trigger candidates:
- same failure 3+ times
- same workaround 3+ times
- same missing parsing/format need 3+ times
- repeated subprocess timeout or output confusion
- repeated human correction around the same module

Bad trigger candidates:
- random novelty for its own sake
- cosmetic churn
- broad architectural rewrite from one weak signal

---

## Safety classes

### Class A — auto-apply possible later
- private helper generation
- local wrappers
- local summaries
- non-critical parsers

### Class B — guarded apply
- shared utilities
- protocol changes
- project modules with dependencies

### Class C — proposal only
- core sim files
- world model changes
- safety/rollback logic
- dashboard/server control surface changes

---

## Reversibility rules

Every self-modification should have:
- clear before state
- clear after state
- rollback reference
- identifiable author agent
- reason for change

If rollback is not straightforward, the change is too risky for autonomous application.

---

## How subprocess awareness fits in

A major source of self-modification pressure should come from subprocess experience.

Agents should eventually track:
- command used
- duration
- success/failure
- output usefulness
- parse difficulty
- downstream effect

That enables thoughts like:
- this command is valuable but noisy → build parser
- this command is fragile → build wrapper
- this process times out often → simplify input
- this tool returns useful data but awkward structure → normalize output

That is a realistic path to self-improvement.

---

## Private-first rule

Most self-modification should begin private.
Only after repeated usefulness should it graduate to:
- shared tool
- public protocol
- core capability

This prevents the world from filling with premature abstractions.

---

## Operator visibility

The operator dashboard should eventually expose:
- pending self-modification proposals
- recently applied self-modifications
- validations and reversions
- pressure sources behind proposals
- promoted shared capabilities

This keeps the system legible and trustworthy.

---

## What success looks like

A successful self-modifying CircleForge world is not one where agents rewrite everything.

It is one where they reliably do small, meaningful things like:
- create a better wrapper
- reduce repeated effort
- stabilize useful local tools
- improve handoffs
- repair brittle interfaces
- evolve conventions from use

That is enough to become genuinely interesting.

---

## Bottom line

Self-modification should be treated as:
- capability refinement
- infrastructure adaptation
- friction reduction
- tool evolution

not as spectacle.

The valuable version is careful, local, logged, and cumulative.
