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
