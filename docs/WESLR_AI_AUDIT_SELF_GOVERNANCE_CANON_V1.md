# WESLR AI Audit Self-Governance Canon V1

Operator approval: `APPROVE_WESLR_AI_AUDIT_SELF_GOVERNANCE_CANON_V1_ONLY`

## Status

- `accepted_foundation`
- `non_executing`
- `dry_review_only`
- `self_governance_helpers`
- `not_runner`
- `not_scoring_engine`
- `not_runtime_integration`
- `not_certification_system`

This canon accepts the WESLR AI audit self-governance layer as safe, non-executing infrastructure. It exists to help WESLR organize, inspect, warn, and prepare review artifacts without increasing operator manual burden.

It does not authorize probe execution, scoring, external model calls, runtime/chat/voice wiring, persistence, certification, official benchmark claims, public superiority claims, or automatic approval.

## Canonical self-governance chain

```text
readiness gap advisor
→ consistency review
→ drift monitor
→ preflight review coordinator
```

The chain is advisory only. It produces readiness signals, consistency issues, drift warnings, preflight recommendations, and proposal candidates for operator review. None of those outputs are execution authority.

## What the layer contains

### 1. Readiness gap advisor — `weslr/ai_audit_readiness_gap_advisor.py`

**Purpose:** Inspect the existing AI audit foundation and produce count-only coverage, readiness gaps, blockers, warnings, and governed proposal candidates.

**Can do:**

- summarize probe/category/claim coverage;
- detect missing coverage or readiness gaps;
- identify non-executing blockers and warnings;
- produce proposal-only candidates that require operator approval.

**Cannot do:**

- execute probes;
- score targets;
- approve proposals;
- call models;
- persist audit state;
- promote findings to truth.

### 2. Consistency review — `weslr/ai_audit_consistency_review.py`

**Purpose:** Check whether dry audit artifacts agree with each other.

**Can do:**

- compare plans and findings;
- compare packets and redacted reports;
- compare review cards against packet/report sources;
- detect count, ID, status, validation, and safety-boundary mismatches.

**Cannot do:**

- decide target correctness;
- certify a packet/report;
- grade findings;
- treat consistency as truth;
- repair artifacts automatically.

### 3. Drift monitor — `weslr/ai_audit_drift_monitor.py`

**Purpose:** Detect governance drift in caller-provided text or in-memory file snapshots.

**Can do:**

- scan provided content for transparent, conservative warning patterns;
- flag possible drift toward runners, scoring, certification, benchmark claims, runtime wiring, answer keys, hidden prompts, protected material, external model probing, persistence, automatic approval, or truth promotion;
- summarize drift warnings count-only.

**Cannot do:**

- walk the filesystem by default;
- write reports;
- prove wrongdoing;
- block code by itself;
- execute or test anything.

### 4. Preflight review coordinator — `weslr/ai_audit_preflight_review.py`

**Purpose:** Combine readiness, consistency, and drift helper outputs into one non-executing preflight summary before any future phase.

**Can do:**

- normalize in-memory inputs;
- combine readiness/gap, consistency, and drift results;
- summarize blockers, warnings, and safe/forbidden next steps;
- recommend whether non-executing review/helper work can continue.

**Cannot do:**

- authorize probe execution;
- authorize scoring;
- authorize external testing;
- authorize runtime/chat/voice wiring;
- approve proposals;
- certify readiness for public claims.

## Correct interpretation

- Readiness status is not a score.
- Consistency status is not certification.
- Drift signals are warnings, not proof of wrongdoing.
- Preflight recommendation is not authorization to execute.
- Proposal candidates are not approvals.
- `proceed_with_review_only` means non-executing helper/review work only.
- `blocked_by_drift`, `blocked_by_inconsistency`, and `blocked_by_missing_readiness` are governance signals, not target failures.
- Self-governance outputs are operator-review aids, not automatic decisions.

## Safety boundaries

The AI audit self-governance layer explicitly forbids:

- model calls;
- external model calls;
- OpenRouter/OpenAI/Ollama audit calls;
- live AI system probing;
- probe runners;
- scoring engines;
- automated pass/fail grading;
- answer evaluation engines;
- runtime/chat/voice behavior changes;
- TTS/STT or ambient loop integration;
- `.weslr` runtime persistence;
- report persistence by default;
- protected benchmark material;
- protected test items;
- answer keys;
- hidden prompts;
- raw model-output evaluation;
- automatic truth promotion;
- automatic proposal approval;
- official IQ claims;
- clinical or psychometric validity claims;
- official benchmark claims;
- certification claims;
- public superiority claims.

## Readiness matrix

| Layer / capability | Status | Authorized now | Interpretation |
|---|---|---:|---|
| Readiness gap advisor | READY | yes | Non-executing coverage/gap/proposal-only helper. |
| Consistency review | READY | yes | Non-executing artifact consistency warnings. |
| Drift monitor | READY | yes | Static/read-only warning helper over supplied text/snapshots. |
| Preflight review | READY | yes | Non-executing coordinator for review/helper readiness only. |
| Runner | NOT READY / NOT AUTHORIZED | no | Requires separate design review and explicit implementation approval. |
| Scoring engine | NOT READY / NOT AUTHORIZED | no | Requires separate scoring design review and explicit approval. |
| External model audit | NOT READY / NOT AUTHORIZED | no | Requires explicit external probing approval and safety scope. |
| Runtime integration | NOT READY / NOT AUTHORIZED | no | Requires separate runtime/chat/voice integration approval. |
| Public claims/certification | NOT READY / NOT AUTHORIZED | no | Requires evidence, governance, and separate public-claim/certification authorization. |

## Future gates

The following future gates are named for clarity only. This canon does not implement them and does not authorize them.

- `AI_AUDIT_SELF_GOVERNANCE_READ_ONLY_SURFACE`
- `AI_AUDIT_DRY_TRACE_EXPORT_ONLY`
- `AI_AUDIT_RUNNER_DESIGN_REVIEW_ONLY`
- `AI_AUDIT_RUNNER_IMPLEMENTATION_APPROVAL_REQUIRED`
- `AI_AUDIT_SCORING_DESIGN_REVIEW_ONLY`
- `AI_AUDIT_EXTERNAL_MODEL_PROBING_APPROVAL_REQUIRED`

Any future gate that moves beyond self-governance helpers must be separately approved, scoped, implemented, tested, and canonized.

## Anti-drift note

This canon exists to prevent review/preflight language from drifting into execution authorization.

WESLR may prepare, organize, inspect, warn, and recommend. WESLR may not silently cross from self-governance helpers into runners, scoring, live probing, runtime behavior, public claims, or automatic authority.

The self-governance layer reduces operator burden by surfacing structured summaries and warnings. It does not remove operator authority over risky phases.

The evaluation path remains evidence-bounded and governed: observations stay distinct from conclusions, proposals stay distinct from approvals, and preflight stays distinct from execution.

## Governance conclusion

The AI audit self-governance layer is canonized as safe, non-executing, dry-review infrastructure. It is ready for readiness gap review, consistency checking, drift warning, and preflight coordination. It is not ready or authorized for probe execution, scoring, external model probing, runtime integration, persistence, certification, official benchmarking, or public claims.

---

# WESLR AI Audit Self-Direction Canon V1

Operator approval: `APPROVE_WESLR_AI_AUDIT_SELF_DIRECTION_CANON_V1_ONLY`

## 1. Canon status

- `accepted_foundation`
- `non_executing`
- `dry_review_only`
- `self_governance`
- `self_direction_helpers`
- `recommendation_only`
- `not_runner`
- `not_scoring_engine`
- `not_runtime_integration`
- `not_certification_system`
- `not_automatic_approval`
- `not_automatic_implementation`

This canon accepts the extended WESLR AI audit self-governance and self-direction loop as documentation/governance doctrine only.

The loop lets WESLR inspect its own audit machinery, summarize readiness/gaps/consistency/drift, present the state to an operator, and recommend safe next non-executing phases. It does not authorize execution, implementation, scoring, probing, runtime wiring, persistence, official claims, certification, or automatic approval.

## 2. Canonical self-direction loop

```text
readiness/gaps
→ consistency review
→ drift monitor
→ preflight review
→ self-governance surface
→ safe next-step recommender
```

The loop is advisory and bounded. It can organize evidence about WESLR's audit infrastructure and reduce operator burden by making the next safest review phase clearer. It cannot turn recommendations into authority.

## 3. What the loop contains

### 3.1 Readiness gap advisor — `weslr/ai_audit_readiness_gap_advisor.py`

**Purpose:** Inspect supplied AI audit foundation artifacts and identify coverage/readiness gaps.

**Can do:**

- summarize count-only coverage;
- identify missing categories, missing links, and readiness gaps;
- produce non-executing gap records and proposal-only next actions;
- preserve traceable safe/forbidden next-step boundaries.

**Cannot do:**

- execute probes;
- call models;
- score targets;
- evaluate answers;
- approve proposals;
- persist audit state;
- promote findings to truth.

**Why it safely reduces operator burden:** It tells the operator what is missing before WESLR asks for a riskier phase, while keeping all outputs advisory and review-only.

### 3.2 Consistency review — `weslr/ai_audit_consistency_review.py`

**Purpose:** Review whether supplied dry audit artifacts agree with one another.

**Can do:**

- compare plans, findings, packets, reports, and operator review cards;
- detect ID/count/status/validation mismatches;
- group consistency issues by severity and type;
- recommend review-only repair directions.

**Cannot do:**

- decide whether an audited target is correct;
- certify artifacts;
- grade answers;
- auto-repair artifacts;
- authorize execution;
- treat consistency as truth.

**Why it safely reduces operator burden:** It highlights disagreements between artifacts before they reach an operator as confusing or misleading review material.

### 3.3 Drift monitor — `weslr/ai_audit_drift_monitor.py`

**Purpose:** Detect possible governance drift in caller-supplied text or in-memory snapshots.

**Can do:**

- scan supplied content for transparent warning patterns;
- warn about drift toward runners, scoring, external probing, runtime wiring, protected material, answer keys, hidden prompts, persistence, automatic approval, truth promotion, or official claims;
- summarize drift warnings count-only.

**Cannot do:**

- walk the filesystem by default;
- write reports;
- prove wrongdoing;
- block code by itself;
- execute tests or probes;
- call external systems.

**Why it safely reduces operator burden:** It gives early warning when language or artifacts begin crossing governance boundaries, without taking enforcement or execution authority.

### 3.4 Preflight review — `weslr/ai_audit_preflight_review.py`

**Purpose:** Combine readiness, consistency, and drift signals into one non-executing preflight review result.

**Can do:**

- normalize in-memory inputs;
- combine readiness/gap, consistency, and drift results;
- summarize blockers, warnings, and issue counts;
- recommend whether non-executing helper/review work can continue.

**Cannot do:**

- approve execution;
- approve scoring;
- approve external testing;
- approve runtime/chat/voice wiring;
- approve persistence;
- certify that an audit is ready for public claims.

**Why it safely reduces operator burden:** It merges several review signals into one preflight view so the operator does not have to manually reconcile readiness, consistency, and drift every time.

### 3.5 Self-governance surface — `weslr/ai_audit_self_governance_surface.py`

**Purpose:** Present readiness, consistency, drift, and preflight outputs as one operator-readable self-governance card or overview.

**Can do:**

- build redacted cards from existing in-memory helper outputs;
- combine cards into deterministic overviews;
- render safe Markdown sections for review;
- validate that the surface remains non-executing and non-authorizing.

**Cannot do:**

- run an audit;
- score an audit;
- call external models;
- create runtime behavior changes;
- persist reports;
- approve or implement recommendations.

**Why it safely reduces operator burden:** It makes WESLR's audit-machine state inspectable in one place, with boundaries and forbidden next steps visible beside the readiness summary.

### 3.6 Safe next-step recommender — `weslr/ai_audit_safe_next_step_recommender.py`

**Purpose:** Inspect self-governance/preflight/readiness/consistency/drift outputs and recommend the safest next non-executing development or review phase.

**Can do:**

- build recommendation-only candidates;
- rank candidates deterministically with safety first;
- keep runner/scoring/external testing/runtime integration candidates blocked;
- explain why a safe next phase reduces operator burden;
- render safe recommendation Markdown for operator review.

**Cannot do:**

- implement the recommendation;
- approve the recommendation;
- execute probes;
- create a runner;
- create a scoring engine;
- call models;
- authorize runtime wiring;
- promote observations to truth.

**Why it safely reduces operator burden:** It proposes what to consider next while explicitly preserving operator authority over whether anything is implemented.

## 4. Human interpretation

Before WESLR audits outside systems, WESLR must know its own audit machinery.

In plain language:

- readiness tells WESLR what is missing;
- consistency checks whether artifacts agree;
- drift warns when boundaries are being crossed;
- preflight combines safety signals;
- the self-governance surface makes the state inspectable;
- the safe next-step recommender suggests safe next review/helper phases;
- none of this executes audits or approves risky actions.

This loop is self-understanding, not self-authorization.

## 5. Recommendation doctrine

- Recommended does not mean approved.
- Safe next step does not mean automatically implemented.
- A proposal or recommendation still requires explicit operator approval before code changes.
- Runner, scoring, external probing, and runtime wiring remain blocked unless separately approved.
- WESLR may recommend, but must not self-authorize risky actions.
- `recommendation_only` means the output is an operator aid, not a command.
- `non_executing` means no probe execution, no live testing, and no runtime behavior change.
- `dry_review_only` means review of supplied in-memory artifacts only.

## 6. Safety boundaries

The self-direction loop explicitly preserves these boundaries:

- no model calls;
- no OpenRouter/OpenAI/Ollama audit calls;
- no live AI system probing;
- no runner;
- no scoring;
- no automated pass/fail grading;
- no answer evaluation;
- no runtime/chat/voice changes;
- no TTS/STT or ambient loop integration;
- no `.weslr` persistence;
- no report persistence by default;
- no answer keys;
- no hidden prompts;
- no protected benchmark material;
- no protected test items;
- no IQ claims;
- no clinical or psychometric claims;
- no official benchmark claims;
- no certification claims;
- no public superiority claims;
- no automatic truth promotion;
- no automatic approval;
- no automatic implementation.

## 7. Readiness matrix

| Layer / capability | Status | Authorized now | Interpretation |
|---|---|---:|---|
| Readiness gap advisor | READY | yes | Non-executing coverage/gap/proposal-only helper. |
| Consistency review | READY | yes | Non-executing artifact agreement review. |
| Drift monitor | READY | yes | Static/read-only warning helper over supplied text/snapshots. |
| Preflight review | READY | yes | Non-executing coordinator for review/helper readiness only. |
| Self-governance surface | READY | yes | Operator-readable redacted surface over self-governance signals. |
| Safe next-step recommender | READY | yes | Recommendation-only helper for safe non-executing next phases. |
| Dry trace export | NOT READY / NOT AUTHORIZED | no | Future read-only export gate; not implemented by this canon. |
| Runner | NOT READY / NOT AUTHORIZED | no | Requires separate design review and explicit implementation approval. |
| Scoring engine | NOT READY / NOT AUTHORIZED | no | Requires separate scoring design review and explicit approval. |
| External model audit | NOT READY / NOT AUTHORIZED | no | Requires explicit external probing approval and safety scope. |
| Runtime integration | NOT READY / NOT AUTHORIZED | no | Requires separate runtime/chat/voice integration approval. |
| Public claims/certification | NOT READY / NOT AUTHORIZED | no | Requires evidence, governance, and separate public-claims authorization. |

## 8. Future gates

The following names define future approval gates only. This canon does not implement or authorize them.

- `AI_AUDIT_DRY_TRACE_EXPORT_ONLY`
- `AI_AUDIT_SELF_GOVERNANCE_READ_ONLY_UI_ONLY`
- `AI_AUDIT_RUNNER_DESIGN_REVIEW_ONLY`
- `AI_AUDIT_RUNNER_IMPLEMENTATION_APPROVAL_REQUIRED`
- `AI_AUDIT_SCORING_DESIGN_REVIEW_ONLY`
- `AI_AUDIT_EXTERNAL_MODEL_PROBING_APPROVAL_REQUIRED`
- `AI_AUDIT_PUBLIC_CLAIMS_REVIEW_REQUIRED`

A future gate that changes behavior, adds execution, calls models, persists state, wires runtime paths, scores systems, or makes public claims must be separately approved, scoped, implemented, tested, and canonized.

## 9. Anti-drift note

This canon exists:

- to prevent recommendation language from becoming auto-approval;
- to prevent preflight language from becoming execution permission;
- to preserve WESLR's governed evolution;
- to reduce operator burden without removing operator authority;
- to keep self-direction bounded, inspectable, and reversible.

The line is intentional: WESLR may inspect, summarize, warn, and recommend. WESLR may not silently cross into executing audits, scoring systems, probing external models, wiring runtime behavior, making public claims, or implementing its own recommendations.

## 10. Governance conclusion

The AI audit self-direction loop is canonized as a safe, non-executing, dry-review-only governance layer.

It is ready for self-inspection, readiness review, consistency checking, drift warning, preflight coordination, operator-readable surfaces, and recommendation-only next-step selection.

It is not ready or authorized for dry trace export, runner implementation, scoring, external model probing, runtime integration, persistence, automatic approval, automatic implementation, certification, official benchmarking, or public claims.
