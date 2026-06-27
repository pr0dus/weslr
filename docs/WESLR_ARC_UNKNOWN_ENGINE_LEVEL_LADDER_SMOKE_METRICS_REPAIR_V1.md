# ARC UNKNOWN ENGINE LEVEL LADDER SMOKE METRICS REPAIR V1

**Executive verdict**: `arc_unknown_engine_smoke_metrics_repaired`

## Problem fixed
The original synthetic smoke report mixed task‑level and packet‑level counts, causing the confusing statement that *exact solves (41) > attempted levels (36)*. The cause was that "exact solves" counted **packets** (top‑2 candidates) while "attempted levels" counted **tasks**. This made the metric ambiguous for downstream decisions.

## Metric schema (added fields)
- **Task‑level aggregates**: `task_exact_count`, `task_partial_count`, `task_unsupported_count`, `task_failed_count`.
- **Rates**: `task_exact_rate`, `task_partial_rate`, `task_unsupported_rate`, `packet_exact_rate`, `packet_partial_rate`, `packet_unsupported_rate`.
- **Thresholds**: `internal_threshold` (0.85), `threshold_basis` ("task_exact_rate"), `internal_pass_85` (boolean), `level_hardening_allowed` (boolean), `level_hardening_reason` (placeholder).
- **Frontier placeholders**: `hardest_exact_tier`, `hardest_partial_tier`, `first_stable_failure_frontier`, `remaining_partial_families`, `remaining_blocker_families`, `remaining_unsupported_families`, `next_recommended_pressure_family`.
- **Boundary flags**: `synthetic_only`, `public_arc_used`, `kaggle_used`, `benchmark_claim_safe`.

All existing fields remain unchanged.

## Threshold rule
- Primary pass/fail metric is **task_exact_rate**.
- `internal_pass_85` is true iff `task_exact_rate >= 0.85`.
- Level hardening (`level_hardening_allowed`) is enabled only when `internal_pass_85` is true.
- Packet‑level `packet_exact_rate` is retained for diagnostics only and does not affect the threshold.

## Test summary
New test suite `weslr/tests/test_arc_unknown_engine_level_ladder_smoke_metrics_v1.py` validates:
1. Correct computation of `packet_exact_rate`.
2. Correct computation of `task_exact_rate` and alignment with `internal_pass_85` and `level_hardening_allowed`.
3. Consistency of boundary flags (`synthetic_only`, `public_arc_used`, `kaggle_used`, `benchmark_claim_safe`).
All tests pass (3 / 3).

## Recommended next safe local follow‑up
**A** – `REVIEW_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SMOKE_METRICS_V1` – to confirm the repaired metrics and consider any further analysis.

---
*All work is internal‑synthetic only, no public ARC/Kaggle data, no benchmark claims, and no protected files were modified.*