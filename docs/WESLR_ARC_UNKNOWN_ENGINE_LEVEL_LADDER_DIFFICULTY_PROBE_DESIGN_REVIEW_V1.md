# WESLR ARC UNKNOWN ENGINE LEVEL LADDER DIFFICULTY PROBE DESIGN REVIEW V1

## 1. Executive verdict
`arc_unknown_engine_difficulty_probe_design_valid_ready_for_implementation`

The design is safe, coherent, and narrow enough for a governed implementation lane. It preserves the Smoke V2 baseline, keeps harder-probe results separate, maintains solver freeze, stays synthetic-only, and defines a usable frontier-oriented metric/interpretation policy.

## 2. Baseline preservation review
Assessment: **valid**

- Smoke V2 remains a clean reference baseline.
- The design explicitly preserves baseline metric meaning:
  - `task_exact_rate = 31 / 36 = 0.8611111111111112`
  - `packet_exact_rate = 41 / 48 = 0.8541666666666666`
- Harder-probe results are clearly separated into a distinct difficulty-probe mode.
- The design does not reinterpret harder-probe outcomes as baseline regressions.
- This separation is important and correctly handled.

Answer to core questions 1–2: **yes**.

## 3. Difficulty axes review
Assessment: **valid and synthetic-only**

Each proposed axis is meaningful for internal synthetic pressure testing:

- **multi-step transformation** — good pressure on single-step overconfidence
- **object movement plus color change** — good combined spatial/appearance pressure
- **reflection plus translation** — good relational-composition pressure
- **distractor objects** — good ranking robustness pressure
- **partial occlusion** — good safe-failure pressure under incomplete evidence
- **role reversal** — good source/target-role inference pressure
- **exception case** — good anti-overcompression pressure
- **negative evidence / non-change** — good no-op trap pressure
- **shape count change** — good count-vs-identity pressure
- **symmetry trap** — good false-symmetry pressure
- **coordinate overfit trap** — good anti-absolute-position pressure
- **concept-bloat trap** — good anti-overexplanation pressure
- **composed transformations** — good bounded combination pressure
- **train/test rule shift** — good rival-grammar exposure pressure
- **ambiguous rival grammar** — good safe unsupported / blocker surfacing pressure

These axes remain synthetic-only in the design as written and do not require public ARC/Kaggle data.

Answer to core question 3: **yes**.

## 4. Tiering policy review
Assessment: **coherent and actionable**

- **Tier 0** cleanly preserves easy continuity/sanity.
- **Tier 1** cleanly maps to the current known baseline.
- **Tier 2** is the right first harder step: composed two-pressure levels without solver-depth escalation.
- **Tier 3** correctly adds adversarial/distractor-heavy pressure.
- **Tier 4** correctly reframes ambiguity/safe failure as signal rather than simple miss.
- **Tier 5** correctly defines the UNKNOWN ENGINE frontier layer.

Strengths:
- tier ordering is monotonic in intended pressure
- higher tiers are clearly generator-side only
- tiers are interpretable enough to support family-by-family review later

Minor caution:
- implementation should keep tier definitions concrete enough to avoid overlap between Tier 3 adversarial pressure and Tier 4 ambiguity pressure. That is an implementation clarity detail, not a design blocker.

Answer to core question 4: **yes**.

## 5. Solver freeze review
Assessment: **preserved**

Confirmed in the design:
- no solver changes
- no new solver primitives
- no retry fill repair
- no depth-3 implementation
- no solver patching to pass harder probes

This is one of the strongest parts of the design. The document repeatedly routes pressure increases into generator/probe space instead of solver space.

Answer to core question 5: **yes**.

## 6. Metric policy review
Assessment: **sufficient to expose a real frontier**

The design keeps the correct metric hierarchy:
- task-level metrics are primary
- packet-level metrics are diagnostic

The proposed harder-probe metrics are strong enough for frontier discovery:
- `attempted_task_count`
- `task_exact_count / rate`
- `task_partial_count / rate`
- `task_unsupported_count / rate`
- `packet_exact_count / rate`
- unsupported families
- blocker families
- first stable failure frontier
- hardest exact tier
- next recommended pressure family

Why this is sufficient:
- task-rate identifies performance degradation at the right semantic level
- unsupported/blocker families distinguish inability from mere score drop
- frontier fields create decision-relevant next-step output instead of raw score repetition
- recommended additional tier/family breakdowns are useful and should survive into implementation

Answer to core question 8: **yes**.

## 7. Hardness interpretation review
Assessment: **useful and well-calibrated**

The interpretation policy is practical:
- **>=85%** → probe still too easy; increase difficulty again
- **70–85%** → likely useful frontier zone
- **40–70%** → meaningful stress exposure
- **below 40%** → may be informative or may be over-hard / too ambiguous
- **unsupported/blocker-heavy** → meaningful UNKNOWN ENGINE frontier signal, not automatic failure

This is the right framing. It avoids treating every drop below 85% as failure while still preserving the baseline threshold as the anchor.

Answer to core question 9: **yes**.

## 8. ARC/Kaggle boundary review
Assessment: **clean**

Confirmed:
- no public ARC data
- no Kaggle data
- no official claims
- no Kaggle readiness claim
- no benchmark leakage
- no ARC-AGI-1 / ARC-AGI-2 performance claim pathway introduced by the design

Answer to core questions 6–7: **yes**.

## 9. Implementation-readiness review
Assessment: **safe for a narrow implementation lane**

A narrow implementation lane is safe if it is constrained to:
- generator/probe-only additions
- separate harder mode from baseline mode
- frontier metric/report population
- no solver behavior changes
- no new primitives
- no depth escalation beyond the current freeze doctrine

The design is not too broad because it already excludes solver repair and focuses implementation on bounded synthetic pressure plus reporting.

Answer to core question 10: **yes**.

## 10. Recommended next safe local follow-up
`IMPLEMENT_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_DIFFICULTY_PROBE_V1`

Reason:
- design is valid
- implementation scope can remain narrow
- baseline preservation is clear
- solver freeze is explicitly protected
- the next useful step is to implement the harder synthetic generator/probe runner only, not any solver change
