# COGNITIVE_ADEQUACY_GUARDED_INTEGRATION_v1

**Scope:** Planning-only for guarded integration of the runtime cognitive adequacy evaluator. No wiring or activation in this step.

## SECTION 1 — PURPOSE
Consult the adequacy evaluator to flag inadequate internal proposal/reasoning quality and emit governed improvement proposals — never to auto-activate or change cognition.

## SECTION 2 — ALLOWED INTEGRATION POINTS (FUTURE, GUARDED)
- Post-proposal evaluation: run after proposals are generated to assess adequacy and emit proposal-only outputs.
- Periodic background review: bounded, operator-visible scans over recent proposals/loops.
- Operator-triggered review: on-demand check initiated by operator/owner.
- Offline checkpoint review: assess saved checkpoints/batches without affecting live paths.

## SECTION 3 — FORBIDDEN INTEGRATION POINTS (NOW)
- Direct live action routing or execution gating.
- Autonomous generation-rule changes or cognition changes.
- Automatic path switching or self-modifying loops.
- Uncontrolled integration into live loops or front-door flows.

## SECTION 4 — OUTPUT HANDLING
- Proposal-only outputs, governed, role-gated.
- Lineage-recorded (use proposal lineage view); no silent effects.
- Operator-reviewable; activation requires explicit approval.
- No UI/control changes implied; read/surface only.

## SECTION 5 — NEXT STEP
- If integration is desired, propose a specific guarded call site (one of the allowed points) with explicit approval and keep harness as acceptance gate.
