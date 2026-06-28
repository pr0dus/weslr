# WESLR RELATION-FIRST COMPILER HELPER IMPLEMENTATION V1

## 1. Executive verdict
`relation_first_compiler_helper_implemented`

## 2. Implementation summary
- **Module**: `weslr/relation_first_compiler_helper.py`
- **Public function**: `rewrite_moved_anchor_candidate_rule_v1(candidate_rule: dict) -> dict`
- **Test file**: `weslr/tests/test_relation_first_compiler_helper_v1.py`
- **Helper function**: Pure transformation, no judge/scorer/veto

## 3. Input/output surface

### Input fields (11):
- `rule_id` — Unique identifier
- `family_id` — Source family
- `anchor_coordinate` — {x, y}
- `anchor_identity` — Known anchor identity/role
- `target_offset` — {dx, dy}
- `distractor_at_old_anchor` — Bool
- `ambiguity_signal` — Bool
- `boundary_signal` — Bool
- `anchor_absent` — Bool
- `context` — {task_id, source}

### Output fields (9):
- `rewrite_status` — 5 possible statuses
- `original_coordinate_rule` — Preserved input
- `relational_rule` — Transformed form (or None)
- `residual_dependency` — For partial rewrites
- `fallback_rule` — Original if rewrite fails
- `downstream_candidate_rule` — What downstream receives
- `helper_changed_candidate_rule` — Did transformation occur?
- `safety_reason` — Why rewrite succeeded/failed
- `transform_metadata` — Audit trail

## 4. Rewrite policy implementation
| Status | Trigger | Downstream |
|--------|---------|------------|
| full_relational_rewrite | Family in FULL_REWRITE_FAMILIES + identity available + no blocking signals | relational_rule |
| partial_rewrite_with_residual | Family in PARTIAL_REWRITE_FAMILIES + ambiguity_signal | fallback_rule (both evaluated) |
| coordinate_dependency_irreducible | Family in IRREDUCIBLE_FAMILIES OR boundary_signal | fallback_rule |
| unsafe_to_predict_no_relational_grammar | Family in UNSAFE_FAMILIES OR anchor_absent OR no identity | None |
| not_applicable | Non-moved-anchor family OR missing required fields | fallback_rule |

## 5. Distractor-bait policy resolution
**Explicitly resolved**: `anchor_moved_distractor_at_old_coord` returns `full_relational_rewrite` when:
- `anchor_identity` is available
- `ambiguity_signal` is false
- `boundary_signal` is false
- `anchor_absent` is false

The distractor at old coordinate is explicitly ignored when anchor identity is known.

## 6. Determinism/timestamp policy
- `rewrite_timestamp` is set to `None` in all outputs
- Caller can supply timestamp via input context if needed
- Helper is deterministic: identical input → identical output

## 7. Fail-closed behavior
- Missing required fields (`rule_id`, `anchor_coordinate`, `target_offset`, `family_id`) → `not_applicable`
- No invented anchor identity
- No patched coordinate rule
- Preserves fallback or unsupported state

## 8. Mutation and boundary review
- **No input mutation**: Original preserved in `original_coordinate_rule`
- **No external calls**: Pure function
- **No .weslr**: Confirmed
- **Solver-freeze constants exported**: `SOLVER_BEHAVIOR_CHANGED = False`, `SOLVER_PRIMITIVES_ADDED = False`

## 9. Test summary
- **23 tests passed**
- Tests cover all 5 rewrite statuses + safety + determinism + solver-freeze flags
- All existing tests (moved-anchor, coordinate-overfit, difficulty-probe, smoke-metrics) remain passing

## 10. Recommended next safe local follow-up
`REVIEW_RELATION_FIRST_COMPILER_HELPER_IMPLEMENTATION_V1`

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.