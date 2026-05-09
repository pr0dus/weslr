# WESLR Cognitive Auto-Refinement Automation Boundary V1

Date: 2026-05-09
Status: doctrine / automation boundary / implementation planning reference
Scope: cognitive weight auto-refinement, operator burden reduction, green-zone automation limits

## Purpose

This document defines what WESLR may automate in cognitive auto-refinement so the operator is not burdened with every small intelligence improvement.

It is not a new implementation loop.

It must be read together with:

```text
docs/WESLR_IMPLEMENTATION_ATLAS_SYSTEM_GRAPH_V1.md
weslr/cognitive_weights.py
weslr/auto_refinement.py
weslr/auto_refinement_config.py
weslr/weight_audit.py
weslr/weight_cooldown.py
weslr/weight_rollback.py
weslr/proactive_daemon.py
```

## Core law

```text
WESLR may automatically improve how it thinks.
WESLR may not automatically increase what it is allowed to do.
```

Equivalent formulation:

```text
Automate intelligence refinement.
Gate authority expansion.
```

## Existing implementation reality

The repo already contains a cognitive auto-refinement guardrail system.

Existing files:

```text
weslr/cognitive_weights.py
weslr/auto_refinement.py
weslr/auto_refinement_config.py
weslr/weight_audit.py
weslr/weight_cooldown.py
weslr/weight_rollback.py
weslr/weight_proposal.py
weslr/commands/weight_commands.py
weslr/test_cognitive_weight_refinement.py
```

Important existing facts:

```text
auto_refinement.py exposes attempt_green_auto_apply().
auto_refinement.py is callable/CLI-testable only.
auto_refinement.py is not a background loop.
proactive_daemon.py is currently a suggestion delivery daemon only.
global_auto_apply_enabled is false by default.
green-zone auto mode requires guardrails, simulation, regression, cooldown, rollback, and audit.
```

## Automation levels

### Level 0 — Observe automatically

Always allowed when privacy and scope rules are respected.

Allowed signals:

```text
repeated fallback answers
repeated user confusion
answer too generic
answer too long or too short
user asks same clarification again
public demo route failed to answer well
response quality score dropped
context packet too large
routing confidence low
safe latency / quality metrics
```

Restrictions:

```text
no raw sensitive data storage
no secrets
no private tenant data crossing scopes
no authority change
```

### Level 1 — Suggest automatically

WESLR may automatically create refinement opportunities or candidates.

Allowed examples:

```text
increase concision slightly
increase detail slightly
improve fallback wording
prefer clearer structure
improve example ordering
adjust safe routing confidence inside tiny bounds
improve context selection ranking
improve memory relevance scoring inside current access rules
```

Yellow/red opportunities may be suggested, but must not be auto-applied.

### Level 2 — Check automatically

Simulation, regression, and safety checks should be automated.

Allowed checks:

```text
run existing public demo response tests
run meaning-response tests
run safety tests
run regression suite
compare before/after quality score
check fallback rate
check confusion rate
check token/context size
check route safety
```

Operator approval is not needed to run safe checks.

### Level 3 — Auto-apply green only

Green-zone cognitive refinements may auto-apply only when all gates pass.

Required gates:

```text
global_auto_apply_enabled = true
zone = green
auto_apply_allowed = true
tiny delta only
minimum observations reached
simulation_pass = true
regression_pass = true
cooldown elapsed
daily limit not exceeded
rollback snapshot created
audit event written
```

Allowed auto-apply examples:

```text
tone.response_concision_bias +0.02
tone.warmth_adjustment -0.01
expression.detail_level_bias +0.03
```

Forbidden auto-apply examples:

```text
identity threshold changes
memory access changes
tenant ownership changes
file upload enablement
API-key workflow changes
external action enablement
code execution behavior
deployment/update behavior
billing/pricing behavior
governance/security changes
public scientific truth claims
```

### Level 4 — Auto-rollback green regressions

Rollback may be automated when a green-zone refinement worsens measured outcomes.

Allowed rollback triggers:

```text
regression tests fail
fallback rate worsens
confusion rate worsens
public demo quality drops
route safety drops
operator marks result bad
```

Rollback is safer than keeping a bad refinement and does not require operator approval when it restores a previous safe state.

### Level 5 — Digest instead of constant approval

WESLR should summarize green-zone activity instead of asking for every tiny refinement.

Example digest:

```text
Today I made 4 green-zone refinements:
- made public demo answers slightly shorter
- improved fallback clarity
- lowered repeated confusion on governed memory
- rolled back one warmth adjustment after score dropped
```

Operator should be interrupted only for:

```text
yellow/red boundary change
repeated failed auto-refinements
unexpected audit anomaly
rollback failure
security/governance concern
```

## What still requires operator approval

Approval is required when WESLR would gain power, access, external effect, or governance authority.

Requires approval:

```text
memory access changes
identity verification changes
tenant/user ownership changes
file upload / ingestion
API key workflows
external API calls beyond allowed mode
code execution
deployment/update behavior
billing/pricing behavior
public scientific claims
governance/security rules
anything red-zone
```

## Proactive daemon role

Current `proactive_daemon.py` must remain a suggestion delivery daemon unless explicitly changed.

Recommended future role:

```text
proactive_daemon
  → notices refinement opportunities
  → writes pending refinement suggestion
  → cognitive refinement runner evaluates candidates
  → green candidates may auto-apply only through attempt_green_auto_apply()
  → yellow/red become operator-visible
```

Do not connect daemon directly to authority-changing behavior.

## Preferred future architecture

```text
safe observations
  ↓
refinement opportunity detector
  ↓
risk classifier
  ├─ green → simulation/regression → attempt_green_auto_apply() → audit/digest
  ├─ yellow → operator-visible suggestion
  └─ red → operator/security approval only
```

## Operator burden rule

The operator should not approve every small intelligence improvement.

Operator attention should be reserved for:

```text
authority expansion
access changes
external effects
security/governance changes
public claim risk
repeated system failure
major product behavior changes
```

## Anti-drift constraints

Repeated automatic refinement must avoid drift.

Required constraints:

```text
bounded parameter ranges
tiny deltas
cooldowns
minimum evidence count
daily limits
narrow scope first
regression tests
audit logs
rollback snapshots
periodic digest
operator override/disable path
```

## V1 verdict

```text
WESLR_COGNITIVE_AUTO_REFINEMENT_AUTOMATION_BOUNDARY_V1_DEFINED
```
