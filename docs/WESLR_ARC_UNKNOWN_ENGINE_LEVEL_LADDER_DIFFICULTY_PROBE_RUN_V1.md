# WESLR ARC UNKNOWN ENGINE LEVEL LADDER DIFFICULTY PROBE RUN V1

## 1. Executive verdict
`arc_unknown_engine_difficulty_probe_run_confirmed_frontier_signal`

## 2. Scope and boundary
- **Internal synthetic only** – the probe runs purely on generated synthetic data.
- **No public ARC data** – `public_arc_used = false`.
- **No Kaggle data** – `kaggle_used = false`.
- **No official claims** – `benchmark_claim_safe = false`.
- **Solver unchanged** – `solver_behavior_changed = false`, `solver_primitives_added = false`.
- **Baseline generator unchanged** – `generator_behavior_changed_for_baseline = false`.
- **No .weslr writes** – confirmed by test suite.
- **No external calls** – pure Python execution.

## 3. Command and environment
```
python -c "import sys; sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean'); from weslr.arc_unknown_engine_level_ladder_difficulty_probe import run_arc_unknown_engine_level_ladder_difficulty_probe_v1; print(run_arc_unknown_engine_level_ladder_difficulty_probe_v1())"
```
- Repository: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- HEAD at execution start: `e6aa3a08bc224f28a55f3aa7c292d7ed505236cb`
- Deterministic / reproducible: Yes – no randomness introduced beyond the fixed probe case list.

## 4. Baseline reference
- **Baseline task exact rate**: 0.8611111111111112 (31 / 36)
- **Baseline packet exact rate**: 0.8541666666666666 (41 / 48)
- Baseline metrics are stored under `baseline_reference` and remain unchanged.

## 5. Harder‑probe metrics
- **Attempted tasks**: 8
- **Task exact**: 4 (rate = 0.5)
- **Task partial**: 2 (rate = 0.25)
- **Task unsupported**: 2 (rate = 0.25)
- **Task failed**: 0 (rate = 0.0)
- **Packet exact**: 9 (rate = 0.5625)
- **Packet partial**: 2 (rate = 0.125)
- **Packet unsupported**: 5 (rate = 0.3125)
- **Packet failed**: 0 (rate = 0.0)
- **Interpretation**: task‑level metrics are primary; packet‑level metrics are diagnostic. The overall interpretation string is `meaningful_stress_exposure_with_frontier_signal`.

## 6. Frontier result
- **Hardest exact tier**: 3
- **Hardest partial tier**: 3
- **First stable failure frontier**: Tier 3 (`adversarial_distractor_heavy`) with families `["reflection_plus_translation", "coordinate_overfit_trap"]`.
- **Remaining partial families**: `["reflection_plus_translation", "coordinate_overfit_trap"]`
- **Remaining blocker families**: `["coordinate_overfit_trap", "partial_occlusion", "ambiguous_rival_grammar"]`
- **Remaining unsupported families**: `["partial_occlusion", "ambiguous_rival_grammar"]`
- **Next recommended pressure family**: `coordinate_overfit_trap`

## 7. Interpretation
The harder‑probe exact rate of **50 %** is well below the baseline 85 % gate, indicating the probe is sufficiently harder to expose weakness in the frozen solver. Although the sample size (8 tasks) is modest, the tier‑wise breakdown shows a consistent degradation starting at Tier 3, with both partial and blocker families appearing. This signals a **meaningful stress‑exposure** rather than noise. The presence of `coordinate_overfit_trap` as a blocker family and its selection as the next recommended pressure target is trustworthy: it appears in Tier 3, is flagged as a blocker, and aligns with the design’s intention to probe coordinate‑overfit brittleness.

## 8. Recommended next safe local follow‑up
`DESIGN_COORDINATE_OVERFIT_TRAP_FRONTIER_PROBE_V1`

---
All validation gates passed. No protected files modified. No `.weslr` touched. Push avoided.
