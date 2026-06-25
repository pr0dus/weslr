# WESLR ARC Residual Gap Internal Engine Pressure V1

## 1. State summary

Synthetic solver state snapshot:

- Before primitive expansion: `14 / 6 / 28 / 0`
- After primitive expansion: `14 / 30 / 4 / 0`
- After partial-to-exact repair: `41 / 3 / 4 / 0`
- Validation mismatch reduction: `30 -> 3`
- Unsupported remains: `4`
- Candidate generation gap remains: `2`

Interpretation:

- Primitive coverage improved materially.
- Candidate repair worked strongly.
- The current residual state is no longer dominated by missing executors.
- The remaining gaps are now concentrated in exactness, unsupported honesty, and generalization proof.

## 2. Internal engine availability

### Documented diagnostic / architecture helpers that exist

These are the relevant documented surfaces I could verify in the repo/docs, without inventing new APIs:

- `docs/WESLR_UNKNOWN_ENGINE_BOUNDARY_V1.md`
- `docs/WESLR_INTERNAL_CORPUS_TO_ADVISOR_REVIEW_ADAPTER_DESIGN_V1.md`
- `docs/WESLR_ADVISOR_REVIEW_QUEUE_ADAPTER_DESIGN_V1.md`
- `docs/WESLR_BENCHMARK_REASONING_ENGINE_V1.md`
- `docs/WESLR_BENCHMARK_REASONING_ENGINE_CHECKPOINT_V1.md`
- `docs/WESLR_ARC_STYLE_GRID_SOLVER_ADAPTER_DESIGN_V1.md`
- `weslr/arc_style_grid_schema_helpers.py`
- `weslr/arc_style_grid_adapter_phase2.py`
- `weslr/arc_style_grid_solver_dry_run.py`
- `weslr/arc_style_synthetic_task_generators.py`
- `weslr/arc_style_synthetic_solver_suite.py`
- `weslr/arc_agi2_submission_contract.py`

### Applicable to this residual-gap pass

- ARC schema helpers
- ARC phase-2 adapter
- ARC dry-run solver
- ARC synthetic task generators
- ARC synthetic solver suite
- ARC submission contract validation
- UNKNOWN ENGINE boundary doc as a diagnostic boundary reminder only

### Not appropriate for this lane

- Provider/model/API calls
- ChatResponder / respond_chat execution
- Runtime wiring
- `.weslr` IO
- Public benchmark submission paths
- Kaggle adapter work
- Final-answer authority
- Solver-authority claims from UNKNOWN ENGINE

Important: I did not find an implemented UNKNOWN ENGINE solver helper. The available material is design/boundary documentation, not a runtime solver authority.

## 3. Residual friction assimilation

Current friction labels for the residual state:

- residual partial families
- remaining reflect unsupported
- candidate_generation_gap persistence
- synthetic-suite saturation risk
- primitive-family overfitting risk
- missing held-out compositional evaluation
- missing bounded program composition search
- missing typed primitive signatures
- missing top-2 program diversity pressure
- no public-data readiness yet

Operational reading:

- The suite is now strong enough that the remaining failures look like narrow structural gaps rather than broad capability absence.
- That also increases overfitting risk: known-family success can rise while generalization stays unproven.

## 4. Gap hypotheses

Working hypotheses for the residual gap:

- `complete_symmetry` needs stronger symmetry-axis/region inference
- `object_count_to_pattern` needs better count-to-output-shape mapping
- `reflect_object_horizontal_or_vertical` needs stable axis selection or quarantine
- current solver may be overfitting hand-authored synthetic families
- current synthetic suite is too small to justify public ARC contact
- no depth-2/3 primitive composition search yet
- no held-out random/compositional generator yet
- no objective evidence that improvements generalize beyond known families

## 5. Options compared

### A. Finish residual family repair first

Pros:
- Might raise exact count a bit more on the current suite.
- Could reduce visible residual friction immediately.

Cons:
- Risks polishing the known suite instead of proving generalization.
- Does not address missing compositional proof.
- Could deepen family-template overfitting.

### B. Design bounded compositional program search first

Pros:
- Addresses the real next-layer missing capability.
- Creates a principled path for depth-2/3 composition.
- Better fit for proving solver generalization.

Cons:
- Requires careful design boundaries and typed primitive signatures.
- May not immediately raise current suite exactness.

### C. Implement held-out/random compositional synthetic generator first

Pros:
- Separates implementation families from evaluation families.
- Produces a real generalization test.
- Helps expose overfitting quickly.

Cons:
- Best paired with a bounded search design; alone it may only diagnose failure.
- Needs a clean split from generator templates used by implementation.

### D. Run internal-engine pressure only and stop

Pros:
- Safe.
- Low risk.
- Clarifies next lane without overcommitting.

Cons:
- Does not produce the next architecture layer.
- Leaves the solver plateau untested on held-out composition.

### E. Touch public ARC/Kaggle data next

Pros:
- None that justify the boundary breach here.

Cons:
- Unsafe for this state.
- Would overstep the current synthetic-only evidence boundary.
- No held-out synthetic proof yet.

## 6. Recommended decision

### Primary next lane

`DESIGN_ARC_STYLE_COMPOSITIONAL_PROGRAM_SEARCH_AND_HELDOUT_SYNTHETIC_EVALUATION_V1`

Reason:

The known-family solver is now strong enough to justify stepping beyond the 12-family synthetic suite. Finishing the remaining 3 partial + 4 unsupported cases may be useful, but it risks optimizing the known templates instead of proving generalization. The bigger need is a bounded composition/search design plus a held-out synthetic evaluation split.

### Fallback lane

`IMPLEMENT_ARC_STYLE_RESIDUAL_FAMILY_REPAIR_V1`

Use this only if the pressure review concludes the residual families are unstable enough to poison the next evaluation layer.

## 7. Decision criteria

Recommended objective criteria for choosing between the primary and fallback lanes:

- Exact on the current known-family suite should stay at least `41`
- Residual unsupported should remain honestly classified
- Held-out compositional suite must be separated from generator templates used for implementation
- Per-family exact distribution must be reported
- Depth-2/3 composition search must improve held-out exact rate, not only known-family exact rate
- Top-2 packets must stay valid
- No leakage
- Deterministic run stability
- No public ARC data until synthetic held-out proof exists

## 8. Non-goals

Explicitly not in scope for this lane:

- UNKNOWN ENGINE is not a solver authority
- no AGI claim
- no Kaggle-ready claim
- no benchmark score claim
- no public ARC data ingestion
- no provider/model calls
- no implementation in this lane

## 9. Final note

This pass is diagnostic/report-only. It records residual pressure and recommends the next architecture step without changing solver behavior.
