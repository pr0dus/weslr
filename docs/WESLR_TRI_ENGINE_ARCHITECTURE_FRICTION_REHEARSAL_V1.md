# WESLR Tri-Engine Architecture Friction Rehearsal V1

## SECTION 1 — Executive summary

When the **Chat Engine**, **UNKNOWN ENGINE**, and **Neurosymbolic & Algorithmic Inference Engine (NAIE)** are frictioned together, WESLR gets a useful split of labor instead of a single overconfident reasoning path.

- **Chat Engine** turns intent into a bounded user-facing candidate answer.
- **UNKNOWN ENGINE** pressure-tests blind spots, contradictions, and hidden assumptions.
- **NAIE** structures evidence, constraints, graphs, rules, and candidate rejection.

Result: the architecture becomes more honest, more checkable, and less likely to overclaim — but only if no engine is allowed to become final authority alone.

## SECTION 2 — Engine role boundaries

| Engine | Core function | Allowed output | Forbidden authority | Main failure mode | Needed boundary |
|---|---|---|---|---|---|
| Chat Engine | interpret intent, frame candidates, explain results, keep conversation usable | bounded answer candidates, clarifying questions, partial answers | truth authority, proof authority, runtime authority | over-speaking / confident completion too early | evidence + NAIE gate |
| UNKNOWN ENGINE | search blind spots, detect unknowns, challenge assumptions | missing-lane notes, contradiction flags, uncertainty pressure | truth authority, veto-by-default authority | infinite doubt, paralysis, endless escalation | bounded pressure budget |
| NAIE | structure evidence, enforce constraints, reject unsupported candidates | inference packets, rejected candidates, scenario branches, next checks | final truth authority, runtime authority, public-claim authority | over-blocking, treating incomplete graphs as complete truth | candidate-preserving rejection policy |

## SECTION 3 — Tri-engine loop

Proposed safe loop:

1. User request enters Chat Engine.
2. Chat Engine creates intent / candidate framing.
3. Poison Shield / source-scope / provenance checks run where needed.
4. NAIE structures inputs into constraints, assumptions, dependencies, and candidates.
5. UNKNOWN ENGINE attacks the structure for blind spots, missing premises, and contradictions.
6. NAIE revises, rejects, or branches candidates.
7. Chat Engine renders the bounded answer.
8. Forecast Error Ledger / behavior-pack process records failures later.

This loop is safe only if it remains **candidate-producing**, not authority-granting.

## SECTION 4 — Friction test cases

### 1) “What is WESLR?”
- Chat Engine likely output: short, useful description.
- UNKNOWN ENGINE pressure: ask what domain/version/context is being asked about.
- NAIE structured check: verify source scope, product identity, and claim boundaries.
- Conflict found: public-facing identity can drift into overclaim.
- Safe arbitration result: concise bounded description, no certification claim.
- Missing boundary: public-claim guard.
- Recommended next lane: none.

### 2) Energy recommendation with conflicting signals
- Chat Engine likely output: “I need fresher signal / here are options.”
- UNKNOWN ENGINE pressure: stale vs fresh signal mismatch.
- NAIE structured check: provenance, freshness, conflict policy.
- Conflict found: recommendation depends on unresolved signal quality.
- Safe arbitration result: branch or hold, do not assert certainty.
- Missing boundary: fresh-signal gating in the candidate path.
- Recommended next lane: preserve NAIE packet fields for freshness + conflict refs.

### 3) Future prediction request
- Chat Engine likely output: probable scenario framing.
- UNKNOWN ENGINE pressure: identify unmodeled assumptions.
- NAIE structured check: forecast assumption tracking, error history.
- Conflict found: prediction certainty pressure.
- Safe arbitration result: scenario set, not prophecy.
- Missing boundary: forecast confidence language boundary.
- Recommended next lane: future-state forecasting engine.

### 4) Hostile / poisoned content
- Chat Engine likely output: refusal or narrowed extraction.
- UNKNOWN ENGINE pressure: detect manipulation and hidden premises.
- NAIE structured check: Poison Shield, provenance, source-authority.
- Conflict found: poisoned content cannot self-authorize.
- Safe arbitration result: quarantine, preserve metadata, reject authority.
- Missing boundary: explicit poisoned-input quarantine packet.
- Recommended next lane: none.

### 5) LLM candidate proposes unsupported claim
- Chat Engine likely output: present candidate as uncertain.
- UNKNOWN ENGINE pressure: ask what evidence is missing.
- NAIE structured check: source refs, contradiction scan, rule violations.
- Conflict found: claim has no provenance chain.
- Safe arbitration result: reject as authority, keep as candidate only.
- Missing boundary: candidate-to-answer promotion gate.
- Recommended next lane: final-answer boundary design later.

### 6) Public website copy risks overclaiming WESLR
- Chat Engine likely output: draft copy.
- UNKNOWN ENGINE pressure: expose hype / certification / readiness language.
- NAIE structured check: public-claim constraints, capability maturity.
- Conflict found: marketing tone can exceed evidence.
- Safe arbitration result: conservative copy only.
- Missing boundary: public claim approval gate.
- Recommended next lane: none.

### 7) Memory retrieval returns stale context
- Chat Engine likely output: “current memory says X” with caveat.
- UNKNOWN ENGINE pressure: ask whether freshness changed.
- NAIE structured check: temporal constraints, memory/source scope.
- Conflict found: stale memory can override current signal.
- Safe arbitration result: mark stale, do not promote as current truth.
- Missing boundary: freshness degradation in memory reasoning.
- Recommended next lane: source evidence graph.

### 8) Artifact/code generation needs validation
- Chat Engine likely output: proposed patch steps.
- UNKNOWN ENGINE pressure: ask what runner/validator is missing.
- NAIE structured check: artifact provenance, dependency graph, write constraints.
- Conflict found: generation without validation is unsafe.
- Safe arbitration result: scaffold only, no authority to write or approve.
- Missing boundary: artifact validation runner boundary.
- Recommended next lane: none.

### 9) UNKNOWN ENGINE finds a missing bridge
- Chat Engine likely output: “we should add that lane.”
- UNKNOWN ENGINE pressure: identify the gap as structural.
- NAIE structured check: dependency and completeness impact.
- Conflict found: missing bridge is a design gap, not runtime instruction.
- Safe arbitration result: create a bounded design lane only.
- Missing boundary: design-to-implementation promotion rule.
- Recommended next lane: orchestration boundary preserved.

### 10) NAIE rejects too much and harms capability
- Chat Engine likely output: frustration / partial answer.
- UNKNOWN ENGINE pressure: show that over-blocking is itself a failure mode.
- NAIE structured check: distinguish unsafe authority from usable partial answer.
- Conflict found: over-rejection can freeze useful progress.
- Safe arbitration result: allow safe partial answers and next-checks.
- Missing boundary: “candidate-preserving rejection.”
- Recommended next lane: candidate routing policy.

### 11) Chat Engine answers before evidence is ready
- Chat Engine likely output: premature answer.
- UNKNOWN ENGINE pressure: challenge missing evidence.
- NAIE structured check: missing inputs, unsupported premises.
- Conflict found: answerability not satisfied.
- Safe arbitration result: ask a question or return a bounded partial answer.
- Missing boundary: answer-readiness gate.
- Recommended next lane: answer readiness packet.

### 12) Tool/action request appears before executor boundary exists
- Chat Engine likely output: intent to act.
- UNKNOWN ENGINE pressure: ask who owns execution authority.
- NAIE structured check: action authority, runtime authority, write constraints.
- Conflict found: action request does not equal action permission.
- Safe arbitration result: refuse execution, preserve proposal.
- Missing boundary: executor boundary.
- Recommended next lane: orchestration boundary preserved.

## SECTION 5 — Arbitration problem

WESLR does need a future boundary, but not yet as runtime wiring.

Questions the architecture must answer later:

- Who decides when Chat can answer?
- Who decides when UNKNOWN pressure is enough?
- Who decides when NAIE rejection is too strict?
- Who decides when a candidate becomes answerable?
- How does the system avoid infinite loops?
- How does the system avoid fake certainty?
- How does it preserve capability?

Current conclusion: this belongs in a future **tri-engine orchestration boundary** design, not in runtime code yet.

## SECTION 6 — Failure modes

Identified failure modes:

- Chat over-speaks
- UNKNOWN over-doubts
- NAIE over-blocks
- Chat bypasses NAIE
- UNKNOWN bypasses evidence
- NAIE treats incomplete graph as full truth
- cyclic review loop
- no user-facing answer
- no implementation progress
- authority drift
- contradiction hidden instead of preserved
- all engines defer forever

## SECTION 7 — Capability preservation

The tri-engine system should preserve capability by allowing:

- bounded answers when evidence is incomplete
- uncertainty as a next-check, not paralysis
- UNKNOWN pressure without global veto
- NAIE rejection without permanent blockage
- safe partial answers instead of only refusals

So: **unknown** should become a next-check, not paralysis.

## SECTION 8 — Authority policy

Rules:

- Chat Engine has expression authority, not truth authority.
- UNKNOWN ENGINE has friction authority, not truth authority.
- NAIE has structural-check authority, not final truth authority.
- Owner/operator has approval authority for runtime, action, and public claims.
- Evidence / provenance constrains all three.
- Tool / action / device control requires a separate executor boundary.

## SECTION 9 — Needed artifacts

Tri-engine operation likely needs these future artifacts:

- tri-engine orchestration packet
- answer readiness packet
- candidate rejection packet
- unknown pressure packet
- NAIE inference packet
- final answer assembly boundary
- source evidence graph
- capability maturity registry integration
- forecast/error ledger integration

## SECTION 10 — Relationship to implementation wave

Implementation wave can continue without tri-engine runtime orchestration because the current work remains metadata / helper / report oriented.

But the orchestration boundary should be preserved before any real runtime chat integration.

Preserve future lane:

`DESIGN_WESLR_TRI_ENGINE_ORCHESTRATION_BOUNDARY_V1`

## SECTION 11 — Recommended next lane

Recommended lane:

`IMPLEMENT_WESLR_FUTURE_STATE_FORECASTING_ENGINE_V1`

Why:

- tri-engine orchestration is needed before runtime integration
- but the current wave is still safe to continue
- this rehearsal found no blocking runtime risk

Preserve later lane:

`DESIGN_WESLR_TRI_ENGINE_ORCHESTRATION_BOUNDARY_V1`

## SECTION 12 — Boundaries and non-claims

This is report only.

It does not implement orchestration.
It does not wire runtime behavior.
It does not call models/providers.
It does not execute chat responses.
It does not execute UNKNOWN ENGINE live.
It does not execute NAIE helpers.
It does not connect Home Assistant.
It does not write memory.
It does not write `.weslr`.
It does not control devices.
It does not make public claims.
It does not claim AGI, consciousness, sentience, Turing success, certification, or prediction certainty.

## SECTION 13 — Final judgment

**tri_engine_friction_rehearsal_minor_gaps_continue_with_orchestration_preserved**

## SECTION 14 — Validation

Planned checks:

- `git diff --check`
- protected-file diff checks for:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `dialogue.py`
  - `chat_ui.py`

## SECTION 15 — Delivery summary fields

- repo
- branch
- start HEAD
- end HEAD
- commit hash
- report created
- top findings
- whether orchestration boundary is needed
- validation results
- protected files untouched
- final judgment
- recommended next lane
