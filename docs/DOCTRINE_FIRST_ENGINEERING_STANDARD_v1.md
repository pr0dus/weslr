# DOCTRINE_FIRST_ENGINEERING_STANDARD_v1

## Purpose
Major WESLR layers must be doctrine-first: define contracts and boundaries before implementation. This prevents ad-hoc drift, reduces rework, and keeps safety, continuity, and governance aligned with architecture.

## Applicability (doctrine-first required)
- Memory and continuity layers (identity, partitioning, promotion/forgetting, consolidation)
- Identity and role/permission models
- Capability intake and routing
- Self-improvement / self-assessment flows
- Plugins/adapters that cross trust boundaries
- Scientific/analysis layers that influence decisions
- Front-door/ingress contracts (status/recap/delta, chat vs status modes)

## Standard Workflow
1) Doctrine/contract: write the contract doc first (scope, boundaries, partitioning, anti-leakage, expected outputs).
2) Minimal safe implementation: build the smallest slice that honors the contract (no scope creep).
3) Validation doctrine/guard tests: add targeted tests/validation aligned to the contract (intent gating, partitioning, mode behaviors).
4) Checkpoint / lane-safe commit: commit per lane in clean worktrees, respecting ownership and workflow execution contract.

## Lightweight Exceptions
- Minor UI copy changes or parameter tweaks that do not alter architecture/governance/continuity.
- One-off diagnostics or logging tweaks (kept scoped and reverted if temporary).
- Emergency patches that restore service without changing doctrine (follow up with doctrine/test if persistent).

## Status
- Standard defined here; no code changes in this doc.
