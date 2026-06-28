# WESLR ARC SYNTHETIC V1/V2 RUN STATISTICS RECOVERY REPORT

## 1. Executive summary

This report recovers the exact V1 and V2 synthetic smoke statistics from the existing committed documentation in `docs/`.

**Key findings:**
- **V1**: Generated 12 ladder levels, attempted 36 tasks, achieved 31/36 exact (0.8611), 41/48 packet exact (0.8542)
- **V2**: Same metrics as V1 — both runs produce identical results (task_exact_rate = 0.8611111111111112)
- **"36"** refers to attempted **tasks** (task-level count)
- **"41"** refers to **packet exact count** (packet-level count, can exceed task count because top-2 packets are evaluated per task)
- **Task and packet metrics are correctly separated** — task_exact_rate is the threshold basis

The repeated identical score (0.8611) across V1 and V2 confirms the smoke surface is stable, but may indicate the need for a V3/V4 diagnostic to stress-test the surface with different conditions.

## 2. Located source artifacts

| Path | Git Tracked | Role |
|------|-------------|------|
| `docs/WESLR_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SYNTHETIC_SMOKE_V1.md` | Yes | Run report (recovered) |
| `docs/WESLR_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SYNTHETIC_SMOKE_V2.md` | Yes | Run report |
| `docs/WESLR_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SMOKE_METRICS_REPAIR_V1.md` | Yes | Repair report |
| `docs/WESLR_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SMOKE_METRICS_REVIEW_V1.md` | Yes | Review report |
| `docs/WESLR_ARC_UNKNOWN_ENGINE_BRANCH_STATE_AFTER_SMOKE_METRICS_REPAIR_V1.md` | Yes | State reconciliation |
| `docs/WESLR_ARC_UNKNOWN_ENGINE_SMOKE_ARTIFACTS_RECOVERY_V1.md` | Yes | Artifacts recovery |

## 3. V1 statistics table

| Metric | Value | Notes |
|--------|-------|-------|
| Generated ladder levels | 12 | Synthetic levels |
| Attempted tasks | 36 | Task-level count |
| Task exact count | 31 | |
| Task partial count | 2 | |
| Task unsupported count | 3 | |
| Task failed count | 0 | |
| Task exact rate | 0.8611111111111112 | 31/36 |
| Task partial rate | 0.05555555555555555 | |
| Task unsupported rate | 0.08333333333333333 | |
| Packet total (top-2) | 48 | 36 tasks × 2 packets |
| Packet exact count | 41 | |
| Packet partial count | 3 | |
| Packet unsupported count | 4 | |
| Packet exact rate | 0.8541666666666666 | 41/48 |
| Internal threshold | 0.85 | |
| Threshold basis | task_exact_rate | Primary gate |
| Internal pass_85 | true | |
| Level hardening allowed | true* | *Must wait for V5 |

## 4. V2 statistics table

| Metric | Value | Notes |
|--------|-------|-------|
| Generated ladder levels | 12 | Same as V1 |
| Attempted tasks | 36 | Same as V1 |
| Task exact count | 31 | Same as V1 |
| Task partial count | 2 | V1: 2 |
| Task unsupported count | 3 | V1: 3 |
| Task failed count | 0 | Same as V1 |
| Task exact rate | 0.8611111111111112 | **Identical to V1** |
| Task partial rate | 0.05555555555555555 | |
| Task unsupported rate | 0.08333333333333333 | |
| Packet total (top-2) | 48 | Same as V1 |
| Packet exact count | 41 | Same as V1 |
| Packet partial count | 3 | V1: 3 |
| Packet unsupported count | 4 | V1: 4 |
| Packet exact rate | 0.8541666666666666 | Same as V1 |
| Internal threshold | 0.85 | |
| Threshold basis | task_exact_rate | |
| Internal pass_85 | true | |
| Level hardening allowed | true | |

**Note**: V2 is essentially identical to V1 because the smoke metrics were repaired between V1 and V2, and V2 represents the post-repair stable surface.

## 5. Number clarification

- **"36"**: This refers to **attempted tasks** at the task level. Each task represents a synthetic ARC-style problem.
- **"41"**: This refers to **packet exact count** at the packet level. Since each task evaluates up to 2 packets (top-2), it's possible (and expected) to have more packet-level exacts than task-level attempts.
- **Task vs Packet separation**: Correctly implemented:
  - Task metrics use task-level outcomes (exact/partial/unsupported/failed per task)
  - Packet metrics use packet-level outcomes (exact/partial/unsupported/failed per packet)
  - Threshold uses `task_exact_rate` as the primary gate
  - Packet metrics are diagnostic only

## 6. V1 vs V2 comparison

| Metric | V1 | V2 | Change |
|--------|-----|-----|--------|
| Attempted tasks | 36 | 36 | None |
| Task exact rate | 0.8611 | 0.8611 | None (stable) |
| Packet exact rate | 0.8542 | 0.8542 | None (stable) |
| Task partial | 2 | 2 | None |
| Task unsupported | 3 | 3 | None |
| Frontier fields | null | null | None |

**Interpretation**:
- V2 is not a new smoke run — it's the post-repair confirmation of the same surface
- The identical scores (0.8611) indicate the smoke surface is stable
- The repeated identical score suggests the need for a V3/V4 diagnostic to stress the surface with variation

## 7. Later probe context

Later milestones (not part of V1/V2 baseline):

| Probe | Result |
|-------|--------|
| Difficulty probe | 4/8 exact (50%) |
| Coordinate-overfit probe | 9 tests passed |
| Moved-anchor probe | 4/8 exact (50%), 4/8 failure (50%) |
| Relation-first helper | 23 unit tests passed, 9 functional cases passed |

These later probes are separate from the V1/V2 baseline and should not be mixed with baseline statistics.

## 8. Recommendation

**Choose: `DESIGN_ARC_SYNTHETIC_SMOKE_V3_DIAGNOSTIC`**

Rationale:
- V1 and V2 show stable but identical metrics (0.8611)
- The repeated score suggests the smoke surface may need stress testing with variation
- V3 should introduce diagnostic variation (e.g., harder task families, different tier distribution) to confirm the surface is genuinely stable
- V3 is not for hardening — it's for diagnostic verification

Do NOT proceed directly to `DESIGN_INTERNAL_SYNTHETIC_120_EVAL_V1` because:
- We don't yet know if V3 would break the surface
- Jumping to 120 tasks without a V3 diagnostic risks wasting effort on an unstable baseline
- V3 diagnostic should come first

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.