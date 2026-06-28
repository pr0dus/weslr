# WESLR RELATION-FIRST COMPILER MANUAL POC DESIGN REVIEW V1

## 1. Executive verdict
`relation_first_compiler_manual_poc_design_valid_ready_for_manual_execution`

## 2. POC-definition review
**Assessment: Valid.**

The design correctly defines relation-first POC as changing candidate rule formation *before* the solver evaluates them — not adding another diagnostic judge. The five forms (coordinate, relational, partial, irreducible, unsafe) are clear and distinct.

Key insight preserved: **This is a compiler POC, not a ledger.** The design explicitly avoids becoming another judge layer.

## 3. Selected-case review
**Assessment: Sufficient.**

The 6 selected cases cover the full moved-anchor spectrum:
- 2 cases expected to fully rewrite (clean translation, offset preserved)
- 1 case expected to rewrite but with distractor bait (key test)
- 1 case expected to partially rewrite (disambiguation)
- 1 case expected to be irreducible (boundary edge)
- 1 case expected to be unsafe (ambiguous/absent anchor)

This provides enough diversity to test the full rewrite outcome space.

## 4. Rewrite-table review
**Assessment: Concrete and sufficient.**

| Field | Present? |
|-------|-----------|
| Original coordinate-like rule | Yes |
| Proposed relational rewrite | Yes |
| Residual dependency | Yes |
| Rewrite outcome | Yes |
| Expected forward application result | Yes |

Each of the 6 cases has all five fields. The table is actionable — ready for manual execution.

## 5. Structural pass/fail review
**Assessment: Valid and bounded.**

The four outcomes are correctly bounded:
- `full_relational_rewrite` → downstream evaluates relational form
- `partial_rewrite_with_residual` → downstream evaluates both forms
- `coordinate_dependency_irreducible` → fallback to coordinate
- `unsafe_to_predict` → structural no-answer, not post-hoc veto

**Critical**: The design explicitly states "success means the relational rewrite *becomes* the candidate rule" — not "ledger says safe." This preserves the intended distinction.

## 6. Rival grammar demotion review
**Assessment: Correctly narrow.**

The design correctly demotes rival grammar comparison to a narrow fallback:
- Only compare when both forms survive as legitimate candidates.
- Do not artificially demote one grammar to elevate another.
- Fallback to coordinate when relational fails; unsupported when coordinate absent.

This is **not** a broad judge — it's a fallback policy.

## 7. Solver freeze and boundary review
**Assessment: All boundaries preserved.**

- Solver unchanged: No new primitives, no depth-3, no patching.
- Synthetic-only: All source cases from moved-anchor probe; no public ARC/Kaggle.
- No official claims: `benchmark_claim_safe = false`.
- No .weslr: Confirmed.
- No external calls: Design documentation only.
- Protected files: No modifications.

## 8. Manual execution readiness
**Assessment: Ready.**

The design is concrete enough for a manual execution lane that:
1. Applies each rewrite to the selected moved-anchor cases.
2. Feeds the relational form to the existing forward path.
3. Compares results against the baseline coordinate-only run.

The design does **not** implement the rewrite in code — it provides the rewrite table that a manual execution lane will use.

## 9. Recommended next safe local follow-up
`EXECUTE_RELATION_FIRST_COMPILER_MANUAL_POC_V1`

Rationale:
- Design is valid and concrete.
- Rewrite table is actionable.
- No new judge — just a manual rewrite test.
- Solver freeze preserved.
- Ready for manual execution.

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.