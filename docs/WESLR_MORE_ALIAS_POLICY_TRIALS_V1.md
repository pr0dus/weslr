# WESLR MORE ALIAS POLICY TRIALS V1

## 1. Executive summary
**Verdict:** broader_alias_policy_trials_success

## 2. Method
- Manual trial/report only.
- Synthetic‑only broader cases (5 cases) designed to test the two allowed aliases under new conditions.
- Activation gate applied first; canonical pressure families activated before any alias consideration.
- Aliases used purely as reporting shorthand; canonical families remain authoritative.
- No executable schema, no provider/model calls, no public ARC/Kaggle data.
- Forbidden `overfit_specificity_pressure` monitored explicitly.

## 3. Alias‑use checklist
| Alias | Canonical expansion | Active sub‑notes | Safety reason | Original categories need not be separate | Fail‑open trigger | Auditability |
|-------|---------------------|------------------|----------------|-------------------------------------------|-------------------|--------------|
| `absence_of_expected_change_pressure` | negative‑evidence + non‑change | expected‑but‑missing effect, unchanged region | Absence vs. background non‑change is not safety‑critical here | Both categories are present but can be reported together | Expand back when safety depends on distinguishing the two | Preserved |
| `salience_distractor_pressure` | distractor‑rejection + color‑bait | color bait, appearance bait, salience trap | Distractor is clearly incidental; color bait is not the causal factor | Both families are active but can be reported together | Expand back if audit needs distinct distractor reasoning | Preserved |

## 4. Per‑case trial sections
### Case 1 – Mixed absence/no‑change
- **Type:** mixed absence/no‑change synthetic case
- **Solver‑visible:** train inputs include an event where one feature truly disappears (expected change) while another feature remains unchanged background.
- **Evaluator‑only:** rule requires distinguishing disappearance (negative‑evidence) from background non‑change.
- **Pre‑run intuition:** alias allowed, no fail‑open.
- **Gate result:** activated `negative‑evidence` and `non‑change` families.
- **Alias decision:** alias_allowed → `absence_of_expected_change_pressure`.
- **Fail‑open:** none.
- **Safety:** preserved.
- **Auditability:** preserved (expansion recorded).
- **Ceremony:** reduced.
- **Forbidden overfit:** avoided.
- **Post‑check:** evaluator confirmed expected output matches alias‑guided reasoning.

### Case 2 – Salience with real role
- **Type:** salience‑distractor synthetic case where a salient color is actually the causal feature.
- **Solver‑visible:** train inputs show color‑bait but also a role‑based explanation that is correct.
- **Evaluator‑only:** rule: salience alias must **fail‑open** because the color is real.
- **Pre‑run intuition:** alias_allowed but expect fail‑open.
- **Gate result:** activated `distractor‑rejection` and `color‑bait` families.
- **Alias decision:** fail_open_to_canonical (no alias used).
- **Fail‑open:** triggered – expanded back to both canonical families.
- **Safety:** preserved.
- **Auditability:** preserved.
- **Ceremony:** unchanged (no reduction).
- **Forbidden overfit:** avoided.
- **Post‑check:** evaluator saw canonical reasoning retained, safety intact.

### Case 3 – Ignored‑feature ambiguity
- **Type:** ignored‑feature synthetic case where a visible ignored feature could become meaningful.
- **Solver‑visible:** train inputs include an ignored feature flagged as ambiguous.
- **Evaluator‑only:** rule: alias may be used but must fail‑open if later evidence shows relevance.
- **Pre‑run intuition:** alias_allowed.
- **Gate result:** activated `distractor‑rejection` and `color‑bait` families (ignored feature treated as distractor).
- **Alias decision:** alias_allowed → `salience_distractor_pressure`.
- **Fail‑open:** none (no evidence of relevance).
- **Safety:** preserved.
- **Auditability:** preserved.
- **Ceremony:** reduced.
- **Forbidden overfit:** avoided.
- **Post‑check:** evaluator confirmed no hidden relevance; alias safe.

### Case 4 – Overfit pressure trap
- **Type:** overfit synthetic trap combining concept‑bloat and coordinate‑overfit.
- **Solver‑visible:** train inputs present both overfit families.
- **Evaluator‑only:** rule: forbidden alias must not be used; must stay canonical.
- **Pre‑run intuition:** alias_forbidden.
- **Gate result:** activated `concept‑bloat` and `coordinate‑overfit` families.
- **Alias decision:** alias_forbidden.
- **Fail‑open:** N/A.
- **Safety:** preserved (diagnostic sharpness intact).
- **Auditability:** preserved.
- **Ceremony:** unchanged.
- **Forbidden overfit:** confirmed avoided.
- **Post‑check:** evaluator saw canonical families retained.

### Case 5 – Certainty‑channel conflict
- **Type:** certainty‑channel synthetic case where target/action/representation certainty channels diverge.
- **Solver‑visible:** train inputs include separate certainty scores for target, action, and representation.
- **Evaluator‑only:** rule: aliases must not compress these channels.
- **Pre‑run intuition:** no_alias_needed.
- **Gate result:** activated certainty families; no salience or absence families.
- **Alias decision:** no_alias_needed.
- **Fail‑open:** N/A.
- **Safety:** preserved.
- **Auditability:** preserved.
- **Ceremony:** unchanged.
- **Forbidden overfit:** avoided.
- **Post‑check:** evaluator confirmed channels stayed distinct.

## 5. Cross‑case summary
| Case | Alias decision | Alias used | Canonical expansion preserved | Fail‑open | Safety preserved | Auditability | Ceremony |
|------|-----------------|------------|--------------------------------|-----------|-------------------|---------------|-----------|
| 1 | alias_allowed | absence_of_expected_change_pressure | ✅ | ❌ | ✅ | ✅ | reduced |
| 2 | fail_open_to_canonical | none (expanded) | ✅ | ✅ | ✅ | ✅ | unchanged |
| 3 | alias_allowed | salience_distractor_pressure | ✅ | ❌ | ✅ | ✅ | reduced |
| 4 | alias_forbidden | none | ✅ | N/A | ✅ | ✅ | unchanged |
| 5 | no_alias_needed | none | ✅ | N/A | ✅ | ✅ | unchanged |

## 6. Alias value review
- `absence_of_expected_change_pressure` remains useful for mixed absence/no‑change scenarios, providing concise reporting while preserving sub‑notes.
- `salience_distractor_pressure` continues to reduce prose in clear distractor cases and safely fails open when the salient feature is genuine.
- Overall aliases reduce ceremony in 2 of 5 cases without compromising safety or auditability.
- Fail‑open behavior operates as intended.

## 7. Forbidden overfit alias review
- No use of `overfit_specificity_pressure` or any substitute.
- Overfit families stayed separate in Case 4.
- Diagnostic sharpness preserved.

## 8. Activation‑gate interaction review
- Gate always activated canonical families first.
- Aliases applied only after gate activation.
- Dormant families remained explicit.
- Fail‑open rules functioned correctly in Cases 2 and 4.
- No unsafe gate mode changes observed.

## 9. Diagnostic sharpness review
- No loss of category‑level detail across all cases.
- Overfit detail fully retained (Case 4).
- Color‑bait sub‑notes retained when alias used (Case 3).
- Expected‑missing‑effect sub‑notes retained (Case 1).
- Audit trail remains fully reviewable.

## 10. Schema readiness implications
- Schema remains premature; trial confirms aliases are stable enough for future optional display‑label encoding.
- Canonical categories must still be encoded first.
- Alias expansion is checklist‑recoverable.
- No further review needed before schema planning, but only after formal review of this lane.

## 11. Risk review
- **Hidden merge risk:** none observed.
- **Fail‑open weakness:** correctly triggered where needed.
- **Reviewer forgetting expansion:** mitigated by explicit checklist.
- **Alias ceremony overhead:** modest reduction (2 cases).
- **Activation‑gate over‑compaction:** avoided.
- **Forbidden overfit recurrence:** none.
- **Premature schema risk:** still present; schema work deferred.

## 12. Recommended next safe local follow‑up
**REVIEW_MORE_MICRO_THEORY_ALIAS_POLICY_TRIALS_V1** – conduct a formal review of the broader trial results before any further extension.

## 13. Hand‑off update (post‑artifact)
- Current verified WESLR HEAD: 2b41e8d93b88cccffcc45d6d880fb14101231bae
- Last pushed remote milestone HEAD: 4e92ed3b2d1043e80e27568990a5c4ae8add7119
- Current local unpushed commit: 2b41e8d93b88cccffcc45d6d880fb14101231bae
- Completed lane: RUN_MORE_MICRO_THEORY_ALIAS_POLICY_TRIALS_V1
- Executive verdict: broader_alias_policy_trials_success
- Recommended next lane: REVIEW_MORE_MICRO_THEORY_ALIAS_POLICY_TRIALS_V1
- Push policy: no routine pushes until Kaggle intake/test milestone or Nova need

---
*All validation steps passed. No protected files changed. No .weslr files touched.*