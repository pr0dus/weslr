# COGNITIVE_ADEQUACY_IMPROVEMENT_DOCTRINE_v1

**Scope:** Doctrine-only. No code changes. Defines how WESLR detects inadequacy in its own inner proposal-generation/reasoning process, and how it proposes better patterns under governance. No silent self-modification.

## SECTION 1 — PURPOSE
- Ensure WESLR can recognize when its internal proposal-generation/reasoning is insufficient (too shallow, repetitive, low-value) and surface governed improvement proposals.
- Keep operators in control: detection and proposal only; activation requires approval.

## SECTION 2 — INADEQUACY SIGNALS (detect at minimum)
- Repetitive shallow proposals for the same task class.
- Low proposal usefulness (operators ignore/override frequently).
- Repeated generic outputs lacking task-specific evidence or actionability.
- Recurring low-confidence patterns without improvement across iterations.
- Failure to connect evidence to useful action (evidence cited but no actionable path).
- Insufficient reasoning depth for recurring task classes (e.g., missing decomposition, missing risk/benefit analysis).

## SECTION 3 — ALLOWED RESPONSE
- Detect and log inadequacy signals.
- Analyze and compare alternative reasoning patterns (documented).
- Propose a better internal reasoning pattern as a governed proposal.
- Forbidden: silently altering cognition, silently changing generation rules, or silently activating new reasoning paths.

## SECTION 4 — PROPOSAL SHAPE (cognitive-improvement proposal must include)
- Inadequacy observed (symptom + task class).
- Evidence (examples, metrics, ignored/overridden proposals, low-confidence traces).
- Proposed better inner process (pattern/steps, not implementation yet).
- Expected benefit (why this improves adequacy/usefulness).
- Risk (governance, drift, overreach) and mitigations.
- Approval requirement (who must approve; governance path).

## SECTION 5 — GOVERNANCE
- Route proposals through the Governed Activation & Permission Framework.
- No activation without operator/owner approval; doctrine-first retained.
- Role-gated visibility; approval per existing governance roles.
- Record lineage of cognitive-improvement proposals for audit (proposal lineage view).

## SECTION 6 — NEXT STEP
- Prepare a detection/assessment plan (doctrine-first) that consumes lineage/observability signals to flag inadequacy; seek approval before implementation.
