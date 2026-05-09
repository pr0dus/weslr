# WESLR Green-Zone Intelligence Refinement V1

Date: 2026-05-09
Status: doctrine / implementation boundary — no new runtime implementation
Scope: existing refinement, consolidation, and daemon loops; repeated low-risk WESLR intelligence refinement without per-change operator approval

## Purpose

This document defines the green-zone intelligence refinement doctrine for WESLR.

Important: this document does **not** create a new competing loop. WESLR already has refinement/consolidation/daemon-style machinery in its architecture and roadmap. This document defines the authority boundary for that existing machinery: what it may improve repeatedly without operator approval, and where it must stop.

WESLR should become more intelligent through repeated internal refinement. That refinement should not require operator approval every time when it stays inside bounded cognition and does not expand authority, external effects, secrets, data access, deployment behavior, billing behavior, or governance power.

## Existing loop / daemon first

Implementation must first inspect and reuse existing WESLR mechanisms before adding anything new.

Expected existing/related concepts include:

- observation loop
- consolidation loop
- refinement loop
- green-zone auto-refinement
- cognitive/behavioral weights
- daemon/background sweeps
- outcome tracking
- cooldowns
- proposal/escalation paths for yellow/red changes

Rule:

```text
Do not create a second intelligence-refinement system if an existing loop or daemon can be extended safely.
```

Preferred implementation path:

```text
existing observations / outcomes
  → existing consolidation/refinement loop or daemon
  → green-zone classifier
  → bounded refinement update
  → log
  → measure
  → rollback if worse
```

## Core principle

```text
WESLR may self-improve freely inside bounded cognition, but must not silently expand authority.
```

Another formulation:

```text
Deep intelligence belongs in the green zone when it improves interpretation, relevance, reasoning quality, context selection, and response formation without increasing authority or external effect.
```

## Why this is not normal LLM fine-tuning

LLM fine-tuning usually changes hidden neural weights.

WESLR green-zone refinement changes explicit, inspectable system behavior.

```text
LLM fine-tuning:
examples/errors → hidden model weight changes → changed behavior

WESLR green-zone refinement:
observations/outcomes → explicit refinement records/weights/rankings → changed behavior
```

WESLR refinement must remain visible enough to inspect, test, measure, and roll back.

## Green-zone refinement may run repeatedly

Green-zone intelligence refinement may run as often as useful when it stays inside its boundaries.

It does not need a separate operator proposal for every small adjustment.

Allowed cadence examples:

- after a user interaction
- after a batch of public-demo interactions
- after repeated confusion signals
- after repeated fallback answers
- after response quality measurements
- after context-efficiency benchmark runs
- after a safe offline evaluation batch
- during an existing daemon/consolidation sweep

## What green-zone refinement may improve automatically

Allowed automatic refinements include:

- intent classification weights
- answer phrasing preferences
- response structure selection
- context selection and compression
- memory relevance scoring
- evidence ranking
- retrieval ordering
- fallback clarity
- confusion detection sensitivity
- repeated-mistake detection
- compact context packet selection
- example-prompt ordering
- public-demo FAQ answer wording within approved scope
- routing confidence thresholds inside safe bounds
- user-facing explanation clarity
- internal quality scoring heuristics

## Examples of green-zone refinement

### Example 1 — answer too generic

Observation:

```text
User asks how WESLR differs from normal agents. Answer is generic and lists capabilities.
```

Green refinement:

```text
Increase preference for structural comparison: normal agents answer/act; WESLR preserves continuity, memory, evidence, proposals, and approval boundaries.
```

No operator approval required.

### Example 2 — repeated confusion

Observation:

```text
Multiple users ask what governed memory means after reading the same explanation.
```

Green refinement:

```text
Prefer shorter explanation with concrete memory scopes and one example.
```

No operator approval required.

### Example 3 — context efficiency

Observation:

```text
Agent-assisted tasks repeatedly receive more context than needed.
```

Green refinement:

```text
Adjust context packet ranking to prioritize active task, constraints, and last decisions over older background notes.
```

No operator approval required.

## What green-zone refinement must not do

Green-zone refinement must not:

- grant new data access
- change tenant ownership rules
- change memory access permissions
- enable file upload
- enable API-key workflows
- expose secrets
- deploy code
- execute commands
- publish claims
- spend money
- call external APIs without allowed mode
- modify production infrastructure
- change billing behavior
- change operator/admin roles
- bypass governance gates
- silently write important memory outside allowed memory policy
- change security boundaries
- change public product claims beyond approved wording scope

## Escalation to yellow/red

A refinement must leave green zone and require review when it would affect:

| Area | Required zone |
|---|---|
| memory access or ownership | yellow/red |
| external API calls | yellow unless explicitly allowed |
| file upload / file ingestion | yellow/red |
| code execution | red unless sandboxed and approved |
| deployment / update behavior | red |
| secrets / API keys | red |
| public scientific claims | yellow/red |
| billing / pricing behavior | red |
| tenant/user roles | red |
| governance boundaries | red |

## Data allowed for green-zone refinement

Allowed input signals:

- response quality labels
- explicit user confusion signals
- repeated fallback counts
- anonymized public-demo interaction categories
- test/benchmark results
- operator-approved evaluation datasets
- non-sensitive timing/latency metrics
- context packet success/failure metrics
- safe click/use signals from demo UI

Not allowed without separate policy:

- raw private user data
- secrets
- credentials
- customer documents
- sensitive personal data
- unpublished scientific claims as facts
- private tenant memory outside its scope

## Logging requirement

Green-zone refinement does not need operator approval, but it must leave an inspectable trace.

Minimum record fields:

```text
refinement_id
created_at
source_signal
refinement_type
old_value
new_value
scope
risk_zone = green
expected_effect
measurement_target
rollback_available = true
```

## Measurement requirement

A green-zone refinement should have a measurable target when possible.

Examples:

- lower fallback rate
- lower repeated confusion rate
- better response quality score
- fewer repeated context explanations
- improved task success
- lower input context tokens for same task class
- improved answer specificity
- improved public-demo completion rate

## Rollback requirement

Every green-zone refinement must be reversible.

Rollback may be implemented as:

- restore previous weight
- disable learned preference
- revert wording variant
- reset routing threshold
- archive failed refinement
- mark signal source as unreliable

## Repeated refinement rule

Green-zone refinement may run many times.

But repeated refinement must avoid drift.

Required anti-drift constraints:

- bounded parameter ranges
- cooldown per refinement type
- no uncontrolled compounding
- minimum evidence threshold for persistent changes
- rollback on quality regression
- isolation by scope where possible

## Scope model

Refinements may be scoped to:

- public demo
- individual user
- project
- team
- institution
- material research lane
- agent/API integration lane
- global default

Default rule:

```text
Prefer narrow scope first; promote to wider scope only after repeated success.
```

## Public demo refinement

Public demo green-zone refinement may improve:

- explanation wording
- safe intent routing
- example prompt order
- fallback clarity
- WESLR-vs-agent explanation
- hosted/private deployment explanation
- pricing/trial phrasing within approved facts

It must not enable:

- memory writes
- file upload
- operator panel
- deployment controls
- private routes
- external provider calls

## Relationship to operator proposals

Operator proposals are not required for normal green-zone intelligence refinement.

Operator proposals are still required for yellow/red changes.

In short:

```text
Do not use proposals for every tiny cognitive improvement.
Use proposals when WESLR would gain power, access, external effect, or governance authority.
```

## Relationship to deep intelligence

Deep intelligence is not only more model tokens or bigger prompts.

For WESLR, deep intelligence means:

- better interpretation of user intent
- better use of memory and context
- better distinction between facts, hypotheses, and proposals
- better prioritization of relevant evidence
- better adaptation to repeated interaction patterns
- better understanding of what not to do
- better ability to continue long-running work without re-explaining everything

These are green-zone when they remain internal, bounded, reversible, and non-authority-expanding.

## Implementation instruction

Before coding this doctrine, the implementation task must begin with repo discovery:

```text
Find the existing refinement/consolidation/daemon loop.
Report exact files and functions.
Extend the existing path if possible.
Do not add a parallel loop unless no existing path can safely support this doctrine.
```

## V1 decisions

```text
1. Green-zone intelligence refinement can run repeatedly without per-change operator approval.
2. Green-zone refinement may improve cognition, relevance, context selection, response quality, and interpretation.
3. Green-zone refinement must not expand authority, data access, external effects, secrets, deployment behavior, billing, or governance boundaries.
4. Green-zone refinement must be logged, measurable where possible, bounded, and reversible.
5. Narrow scope is preferred before global promotion.
6. Yellow/red changes still require review or approval.
7. Existing refinement/consolidation/daemon machinery must be reused or extended before creating any new loop.
```

## V1 verdict

```text
WESLR_GREEN_ZONE_INTELLIGENCE_REFINEMENT_V1_DEFINED
```
