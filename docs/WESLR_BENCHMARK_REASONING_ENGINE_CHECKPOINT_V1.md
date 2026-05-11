# WESLR Benchmark Reasoning Engine Architecture Checkpoint V1

**Status:** architecture checkpoint  
**Date:** 2026-05-11  
**Scope:** completed reasoning-engine spine and next allowed implementation path  
**Implementation status:** documentation and tests only. No runtime behavior changes.

## 1. Status

WESLR has moved from subject-scorer patching toward a Benchmark Reasoning Engine / Cognitive Orchestration Layer.

The architecture center is no longer subject-specific scorer growth. The architecture center is now a reusable reasoning spine that can host formal logic reasoning, ethics/tradeoff reasoning, and later solver families inside one inspectable structure.

Subject scorers are not central intelligence.

## 2. Completed spine

The completed architecture spine is:

- `ReasoningTask`
- `ReasoningTrace`
- `SolverRegistry`
- `ReasoningArbitrator`

This establishes the core path:

**ReasoningTask → ReasoningTrace → SolverRegistry → ReasoningArbitrator**

## 3. What each piece does

### ReasoningTask

`ReasoningTask` is the common task object.

It carries:

- provenance
- parsed fields
- choices
- blackboard placeholders
- anti-gaming / failure fields

Its role is to represent a reasoning item in a general architecture-friendly form rather than as a subject-specific scorer input.

### ReasoningTrace

`ReasoningTrace` is a DAG-like audit structure.

It carries:

- inference nodes / edges
- warrants
- solver outputs
- conflicts
- legibility / anti-gaming flags

Its role is to preserve a renderable and inspectable reasoning trail without making hidden internal state the authority.

### SolverRegistry

`SolverRegistry` describes solver families.

It provides:

- disabled-by-default descriptors
- safety profiles
- capability matching
- not solver implementation

Its role is architectural declaration only. It does not execute solver behavior.

### ReasoningArbitrator

`ReasoningArbitrator` is the conservative decision layer.

It:

- selects only from safe solver outputs
- blocks disagreement / high conflicts / anti-gaming / legibility failures
- does not evaluate correctness
- does not call solvers

Its role is to decide when a trace is safe enough to permit a bounded selection and when it must refuse selection.

## 4. Why this matters

This matters because it:

- stops subject-specific scorer sprawl
- creates reusable reasoning substrate
- enables formal logic and ethics to become solvers inside one architecture
- makes failures and traces inspectable
- supports official-style eval work without official-score claims

The result is a reasoning architecture that can grow by structured enrichment rather than by isolated patch logic.

## 5. What is still missing

The following are still missing:

- ReasoningTask builder from MCQ adapter item
- Solver interface protocol
- first formal logic solver implementation
- trace population from solver outputs
- arbitrator integration into MCQ adapter
- solver-level failure bridge
- scorecard comparison over reasoning-engine path

These missing pieces define the next approved build path. They do not justify a return to subject-specific scorer patching.

## 6. Next allowed implementation path

The next allowed implementation path is:

A. ReasoningTask builder for official MCQ adapter outputs, data-only/no answer selection  
B. Solver interface protocol  
C. formal logic solver V1, not wired to MCQ yet  
D. solver-to-trace adapter  
E. arbitrator dry-run harness  
F. MCQ adapter opt-in path behind explicit flag  
G. internal subset measurement  
H. failure bridge upgrade to solver-level failures

This path preserves ordering discipline:

- data representation first
- solver interface second
- one real solver before broad rollout
- dry-run arbitration before live adapter wiring
- measurement after the path exists

## 7. Forbidden next steps

The following next steps are forbidden:

- adding more subject scorer patches
- tuning business_ethics or formal_logic item wording
- answer-key memorization
- benchmark-specific phrase rules
- official-score claims
- direct MCQ wiring before dry-run trace harness
- raw benchmark storage by default
- private/opaque solver authority

These are forbidden because they would collapse the architecture back into benchmark-shaped patchwork.

## 8. Safety boundaries

The active safety boundaries remain:

- Cognitive Legibility Boundary
- anti-gaming fields
- official_score false / no official-score claim
- no item-id / answer-key use
- human-readable warrants required
- unresolved high-severity conflicts block selection

The spine is only acceptable if these boundaries remain active at every layer.

## 9. Immediate next recommendation

Immediate next recommendation:

- ReasoningTask builder from MCQ suite item
- it should create a `ReasoningTask` from existing adapter item shape
- it should not select answers
- it should not call solvers
- it should not store raw questions by default
- it should preserve fingerprints/provenance

This is the next clean move because it advances the reasoning-engine path without changing runtime behavior, without adding solver authority, and without reintroducing subject-specific scorer logic.

## Canonical checkpoint decision

WESLR now has a completed architecture spine for the future Benchmark Reasoning Engine / Cognitive Orchestration Layer.

The next allowed work is builder/interface/solver-path preparation inside this spine, not additional scorer patching.
