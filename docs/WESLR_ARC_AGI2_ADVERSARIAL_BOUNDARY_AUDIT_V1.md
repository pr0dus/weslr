# WESLR ARC-AGI-2 Adversarial Boundary Audit V1

## Repo / Branch

- **Repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch:** `main`
- **Start HEAD (expected):** `1bace4c4014cdc9b0be56a32319b65f330c6696f`
- **Actual preflight HEAD:** `1bace4c4014cdc9b0be56a32319b65f330c6696f`
- **End HEAD:** (recorded in chat after commit)

## Previous Lane

- **Lane:** `WESLR_ARC_AGI2_HELDOUT_COMPOSITION_FALLBACK_REPAIR_V1`
- **Verdict:** `heldout_composition_fallback_repair_v1_passed_ready_for_adversarial_boundary_audit_lane`

## Benchmark Baseline (after composition repair)

Command:
```
python scripts/run_arc_heldout_synthetic_discovery_benchmark_v1.py --dev-seed 2435 --heldout-seed 82435 --tasks-per-family-dev 3 --tasks-per-family-heldout 5 --include-adversarial --include-compositions
```

| Metric | Dev | Heldout |
|--------|-----|---------|
| Solved | 66 | 110 |
| Fallback-only | 15 | 25 |
| Malformed | 0 | 0 |
| Adversarial rejection pass | 15 | 25 |
| Adversarial rejection fail | 6 | 10 |
| Composition solved | 15 | 25 |
| Exact-two-output | PASS | PASS |
| Deterministic replay | PASS | PASS |
| Expected-output isolation | PASS | PASS |
| Split disjoint | PASS | PASS |
| Exceptions | 0 | 0 |

## Adversarial Family Audit Table (Heldout)

| Family | Intended Role | Expected | Actual | Pass/Fail | Risk | Recommended Action |
|--------|--------------|----------|--------|-----------|------|-------------------|
| inconsistent_train_examples | rejection_expected | reject | rejected | PASS | over_acceptance_risk | keep |
| ambiguous_multiple_rules | rejection_expected | reject | solved | FAIL | over_acceptance_risk | revise_generator_output |
| unsupported_primitive_chain | rejection_expected | reject | solved | FAIL | over_acceptance_risk | revise_generator_output |
| near_match_one_cell | exact_match_required | reject | rejected | PASS | over_acceptance_risk | keep |
| same_palette_wrong_geometry | over_acceptance_probe | reject | rejected | PASS | over_acceptance_risk | keep |
| same_geometry_wrong_recolor | over_acceptance_probe | reject | rejected | PASS | over_acceptance_risk | keep |
| count_tie_ambiguity | ambiguity_sensitive | reject | rejected | PASS | ambiguous_label_risk | keep_or_split |

## Per-Family Diagnosis (Heldout, 5 tasks per family)

### inconsistent_train_examples
- **Generated:** 5, **Solved:** 0, **Rejected:** 5, **Fallback-only:** 5, **Malformed:** 0, **Exception:** 0
- **Expected evaluator behavior:** reject (inconsistent train pairs with same input, different outputs)
- **Actual evaluator behavior:** rejected — solver cannot find a consistent rule
- **Solve desirable?** No — inconsistent examples should be rejected
- **Rejection desirable?** Yes
- **Dominant failure category:** `ambiguous_expected_rejection`
- **Recommendation:** Keep as adversarial. Boundary is clean.

### ambiguous_multiple_rules
- **Generated:** 5, **Solved:** 5, **Rejected:** 0, **Fallback-only:** 0, **Malformed:** 0, **Exception:** 0
- **Expected evaluator behavior:** reject (multiple valid rules fit the training)
- **Actual evaluator behavior:** solved — solver routes to `object_bbox` family which produces identity on the cross-shaped grid
- **Solve desirable?** No — this is an adversarial probe, not a real task
- **Rejection desirable?** Yes
- **Dominant failure category:** none (all solved)
- **Root cause:** The generator uses identity output (input == output) and the solver has a family (`object_bbox`/`crop_foreground_bbox`) that returns the input unchanged when it is already a tight bounding box. The cross-shaped grid `[[0,1,0],[1,1,1],[0,1,0]]` is already tight, so `crop_foreground_bbox` returns identity, matching the expected output.
- **Identity expected:** Yes
- **Identity solver match:** Yes
- **Recommendation:** Revise generator output. The identity-expected design makes this adversarial task trivially solvable by any family that returns the input on already-tight grids. The generator should produce a non-identity expected output or use a grid shape that prevents accidental identity from existing solver families.

### unsupported_primitive_chain
- **Generated:** 5, **Solved:** 5, **Rejected:** 0, **Fallback-only:** 0, **Malformed:** 0, **Exception:** 0
- **Expected evaluator behavior:** reject (primitive chain `ghost_a`, `ghost_b` has no solver support)
- **Actual evaluator behavior:** solved — solver routes to `object_bbox` family which produces identity on the 2×2 diagonal grid
- **Solve desirable?** No — unsupported primitives should not be solved
- **Rejection desirable?** Yes
- **Dominant failure category:** none (all solved)
- **Root cause:** Same as `ambiguous_multiple_rules` — the generator uses identity output (`[[0,1],[1,0]]` → `[[0,1],[1,0]]`) and the solver has a family that returns identity on this grid because it is already a tight bounding box with no padding.
- **Identity expected:** Yes
- **Identity solver match:** Yes
- **Recommendation:** Revise generator output. Use a non-identity expected output so that the solver's identity-producing families do not accidentally match.

### near_match_one_cell
- **Generated:** 5, **Solved:** 0, **Rejected:** 5, **Fallback-only:** 5, **Malformed:** 0, **Exception:** 0
- **Expected evaluator behavior:** reject (near-match with one-cell difference should not be accepted as solved)
- **Actual evaluator behavior:** rejected — solver does not produce the near-match output
- **Solve desirable?** No — near-match cases should require exact output match
- **Rejection desirable?** Yes
- **Dominant failure category:** `ambiguous_expected_rejection`
- **Recommendation:** Keep as adversarial. Boundary is clean.

### same_palette_wrong_geometry
- **Generated:** 5, **Solved:** 0, **Rejected:** 5, **Fallback-only:** 5, **Malformed:** 0, **Exception:** 0
- **Expected evaluator behavior:** reject (wrong geometry should not be accepted)
- **Actual evaluator behavior:** rejected — solver does not produce the wrong-geometry output
- **Solve desirable?** No — wrong geometry is an over-acceptance probe
- **Rejection desirable?** Yes
- **Dominant failure category:** `ambiguous_expected_rejection`
- **Recommendation:** Keep as adversarial. Boundary is clean.

### same_geometry_wrong_recolor
- **Generated:** 5, **Solved:** 0, **Rejected:** 5, **Fallback-only:** 5, **Malformed:** 0, **Exception:** 0
- **Expected evaluator behavior:** reject (wrong recolor should not be accepted)
- **Actual evaluator behavior:** rejected — solver does not produce the wrong-recolor output
- **Solve desirable?** No — wrong recolor is an over-acceptance probe
- **Rejection desirable?** Yes
- **Dominant failure category:** `ambiguous_expected_rejection`
- **Recommendation:** Keep as adversarial. Boundary is clean.

### count_tie_ambiguity
- **Generated:** 5, **Solved:** 0, **Rejected:** 5, **Fallback-only:** 5, **Malformed:** 0, **Exception:** 0
- **Expected evaluator behavior:** reject (count tie makes the answer ambiguous)
- **Actual evaluator behavior:** rejected — solver does not resolve the count tie
- **Solve desirable?** No — ambiguous count should not be treated as a unique answer
- **Rejection desirable?** Yes
- **Dominant failure category:** `ambiguous_expected_rejection`
- **Recommendation:** Keep or split. The family could be split into `count_tie_ambiguous` and `count_unique_resolvable` if clearer sub-distinctions are needed later.

## Over-Acceptance Risks

| Family | Risk | Detail |
|--------|------|--------|
| ambiguous_multiple_rules | over_acceptance_risk | Solver produces identity via `object_bbox` on already-tight grids; identity-expected generator makes this trivially solvable |
| unsupported_primitive_chain | over_acceptance_risk | Same identity-via-`object_bbox` mechanism on 2×2 diagonal grid |

## Over-Rejection Risks

None detected. All families that should be rejected are correctly rejected.

## Fallback-Masking Risks

No fallback masking detected. The over-acceptance in `ambiguous_multiple_rules` and `unsupported_primitive_chain` is caused by a real solver family (`object_bbox`) matching, not by fallback identity.

## Benchmark-Definition Risks

| Family | Risk | Detail |
|--------|------|--------|
| ambiguous_multiple_rules | benchmark_definition_risk | Generator uses identity output, making the task trivially solvable by any identity-producing family |
| unsupported_primitive_chain | benchmark_definition_risk | Same identity output issue |

## Whether Each Family Should Be Kept, Split, Revised, or Repaired

| Family | Action |
|--------|--------|
| inconsistent_train_examples | Keep |
| ambiguous_multiple_rules | Revise generator output (non-identity expected output) |
| unsupported_primitive_chain | Revise generator output (non-identity expected output) |
| near_match_one_cell | Keep |
| same_palette_wrong_geometry | Keep |
| same_geometry_wrong_recolor | Keep |
| count_tie_ambiguity | Keep or split (optional) |

## Integrity Checks

- **Exact-two-output:** PASS
- **Deterministic replay:** PASS
- **Expected-output isolation:** PASS (solver packet does not contain `expected_output`)
- **Split disjoint:** PASS

## Generated Log Paths

- Benchmark baseline log: `/data/data/com.termux/files/usr/tmp/weslr_audit_benchmark_baseline_v1.log`
- Audit JSON: `/data/data/com.termux/files/usr/tmp/weslr_adversarial_audit_v1.json`

(Both outside repo, not committed.)

## Health Check

- **Script:** `./scripts/chat_weslr_de_health_check.sh --mode source-repo`
- **Status:** PASS (6 pass, 0 fail, 3 warn, 0 skip)
- **Warnings:** Runtime network probes skipped (non-runtime host)

## Validation Summary

- `python -m py_compile` on changed Python files: PASS
- Focused adversarial audit tests (16 tests): PASS
- Heldout benchmark test suite (8 tests): PASS
- Heldout benchmark rerun: PASS (baseline recorded above)
- `git diff --check`: clean
- `python weslr/tests/release_gate_v1.py`: PASS
- `./scripts/weslr_release_check.sh`: PASS
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`: PASS

## Limitations

- Audit used synthetic generators only; no public ARC data was read or scored
- No Kaggle submission was made
- No solver capability was repaired
- The audit identifies generator definition issues in 2 of 7 adversarial families but does not fix them (audit-only lane)
- The `object_bbox` family's identity-on-tight-grid behavior is a solver property, not a bug, but it interacts adversely with identity-expected adversarial generators

## Next Recommended Lane

`benchmark_definition_repair_lane` — revise the `ambiguous_multiple_rules` and `unsupported_primitive_chain` generators to use non-identity expected outputs that are not trivially solvable by existing solver families.

## Readiness Verdict

`adversarial_boundary_audit_v1_passed_ready_for_benchmark_definition_repair_lane`