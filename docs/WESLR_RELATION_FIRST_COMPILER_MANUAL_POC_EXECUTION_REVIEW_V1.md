# WESLR RELATION-FIRST COMPILER MANUAL POC EXECUTION REVIEW V1

## 1. Executive verdict
`relation_first_compiler_manual_poc_execution_valid_ready_for_helper_design`

## 2. Execution validity review
**Assessment: Valid.**

The 6-case manual execution is coherent and bounded:
- All cases sourced from moved-anchor probe families
- Each case has complete rewrite fields
- Each case has a clear execution verdict
- The approach is manual (no automated execution), which is correct for a POC

## 3. Rewrite outcome review

| Outcome | Count | Assessment |
|---------|-------|------------|
| Full relational rewrite | 3/6 (50%) | **Key result** — directly addresses moved-anchor failure |
| Partial rewrite with residual | 1/6 (17%) | Correctly identifies ambiguity |
| Irreducible coordinate dependency | 1/6 (17%) | Correctly identifies boundary edge case |
| Unsafe to predict | 1/6 (17%) | Correctly identifies ambiguous/absent anchor |

**Key insight**: The 3 fully viable rewrites address exactly the moved-anchor failure mode (old anchor coordinate bait). These are:
1. `poc_translated_target` — clean translation
2. `poc_distractor_bait` — the key bait failure case
3. `poc_offset_constant` — constant offset preservation

## 4. Compiler-path review
**Assessment: Correct path.**

This is a compiler path, not a new ledger/judge:
- The helper transforms coordinate-form rules into relational-form rules
- Success means the relational form *becomes* the candidate rule
- No diagnostic layer is added
- The frozen solver remains unchanged

The manual POC correctly tested whether relation-first rewriting changes candidate rule formation — not whether a judge approves the result.

## 5. Helper scope review
**Assessment: Narrow and bounded.**

A future helper should be constrained to:
- **Scope**: Moved-anchor coordinate-to-relational rewrite only
- **Input**: Coordinate-form rule from moved-anchor detection
- **Output**: Relational-form rule (when viable)
- **Fallback**: Keep original coordinate form when rewrite fails
- **Boundary**: Irreducible and unsafe cases remain in coordinate form
- **Not**: A broad grammar compiler, not solver patching, not a new judge

This keeps the helper narrow and safe.

## 6. Boundary review
**Assessment: All boundaries preserved.**

- **Solver unchanged**: No new primitives, no depth-3, no patching
- **Synthetic-only**: All source cases from moved-anchor probe; no public ARC/Kaggle
- **No official claims**: `benchmark_claim_safe = false`
- **No .weslr**: Confirmed
- **No external calls**: Manual evaluation only
- **Protected files**: No modifications

## 7. Recommended next safe local follow-up
`DESIGN_RELATION_FIRST_COMPILER_HELPER_V1`

Rationale:
- 3/6 full rewrites directly address moved-anchor failure mode
- The approach is bounded to moved-anchor, not a broad grammar compiler
- The helper would transform candidate rules without modifying the solver
- No new judge — just a narrow rewrite helper
- The manual POC has done its job: confirmed the compiler path is viable

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.