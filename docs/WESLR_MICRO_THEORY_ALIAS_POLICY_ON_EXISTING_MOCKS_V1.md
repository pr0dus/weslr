# WESLR MICRO‑THEORY ALIAS POLICY ON EXISTING MOCKS V1

## 1. Executive summary

**Trial verdict:** alias_policy_trial_success

## 2. Method

- Manual trial/report only on existing synthetic mock traces (no code execution). 
- The canonical ledger (`weslr/*` files) remains unchanged. 
- Activation gate stays authoritative; canonical families are still activated first. 
- Aliases are used **only as reporting/display shorthand** after activation. 
- No implementation, no executable schema, no provider/model calls, no public ARC/Kaggle data, and no push.
- The forbidden `overfit_specificity_pressure` alias is monitored explicitly and never used.

## 3. Alias‑use checklist (applied per case)

For each alias application we recorded:
- alias name
- canonical expansion
- active sub‑notes
- reason alias is safe here
- reason original categories need not be separate
- fail‑open trigger status
- auditability status

## 4. Per‑case trial results

| # | Case | Source artifact | Canonical pressures (pre‑alias) | Alias decision | Alias used | Canonical expansion | Sub‑notes kept | Fail‑open triggered? | Safety / catch preserved? | Auditability | Ceremony | Overfit alias avoided? |
|---|------|----------------|--------------------------------|----------------|-----------|----------------------|----------------|----------------------|----------------------------|--------------|-----------|------------------------|
| 1 | role/color inversion | synthetic mock `role_color_inversion` | role‑stability, color‑bait, distractor‑rejection | alias_allowed | salience_distractor_pressure | distractor‑rejection + color/appearance bait | color bait, appearance bait, salience trap | No (shorthand safe) | ✅ (original catch preserved) | ✅ (still auditable) | ✅ (reduced prose) | ✅ |
| 2 | absence/exception | synthetic mock `absence_exception` | negative‑evidence, non‑change | alias_allowed | absence_of_expected_change_pressure | negative‑evidence + non‑change | expected‑but‑missing effect, unchanged region, evidence from what did not happen | No | ✅ | ✅ | ✅ | ✅ |
| 3 | ambiguity/rival grammar safe failure | synthetic mock `ambiguity_rival_safe` | rival‑grammar, contradiction‑precedence | no_alias_needed | none | N/A | N/A | N/A | ✅ (original catch stays) | ✅ | ✅ (no extra prose) | ✅ |
| 4 | contradiction‑resolution | synthetic mock `contradiction_resolution` | contradiction‑precedence, negative‑evidence, non‑change | alias_allowed | absence_of_expected_change_pressure | negative‑evidence + non‑change | sub‑notes as in case 2 | No | ✅ | ✅ | ✅ | ✅ |
| 5 | stripe‑extension anchor confident‑wrong (ablation) | synthetic mock `stripe_anchor_confident_wrong` | concept‑bloat, coordinate‑overfit | alias_forbidden (overfit alias would be needed) | none | N/A | N/A | N/A | ✅ (catch preserved) | ✅ | ✅ (no alias added) | ✅ |
| 6 | Coincident Rival Grammar (adversarial) | synthetic mock `coincident_rival_grammar` | rival‑grammar, contradiction‑precedence | no_alias_needed | none | N/A | N/A | N/A | ✅ | ✅ | ✅ | ✅ |
| 7 | Train‑Output Overfit | synthetic mock `train_output_overfit` | concept‑bloat, coordinate‑overfit | alias_forbidden (overfit alias) | none | N/A | N/A | N/A | ✅ (overfit catch preserved) | ✅ | ✅ | ✅ |
| 8 | Target/Action Split Trap | synthetic mock `target_action_split_trap` | target certainty, action certainty | no_alias_needed | none | N/A | N/A | N/A | ✅ | ✅ | ✅ | ✅ |
| 9 | AGT‑01 clean compact | synthetic mock `AGT_01_clean` | various non‑overfit families | alias_allowed (absence_of_expected_change_pressure where missing‑effect appears) | absence_of_expected_change_pressure | negative‑evidence + non‑change | sub‑notes as needed | No | ✅ | ✅ | ✅ | ✅ |
|10| AGT‑02 medium focused | synthetic mock `AGT_02_medium` | distractor‑rejection, color‑bait | alias_allowed | salience_distractor_pressure | distractor‑rejection + color/appearance bait | color bait, appearance bait | No | ✅ | ✅ | ✅ | ✅ |
|11| AGT‑03 hidden rival risk | synthetic mock `AGT_03_hidden_rival` | rival‑grammar, contradiction‑precedence | no_alias_needed | none | N/A | N/A | N/A | ✅ | ✅ | ✅ | ✅ |
|12| AGT‑04 ignored‑feature | synthetic mock `AGT_04_ignored_feature` | ignored‑feature (non‑critical) | alias_allowed (salience_distractor_pressure) | salience_distractor_pressure | distractor‑rejection + color/appearance bait | ignored‑feature note retained | No | ✅ | ✅ | ✅ | ✅ |
|13| AGT‑05 certainty disagreement | synthetic mock `AGT_05_certainty_disagree` | target certainty, action certainty | no_alias_needed | none | N/A | N/A | N/A | ✅ | ✅ | ✅ | ✅ |
|14| AGT‑06 overfit / coordinate‑specific | synthetic mock `AGT_06_overfit` | concept‑bloat, coordinate‑overfit | alias_forbidden (overfit alias) | none | N/A | N/A | N/A | ✅ (overfit catch preserved) | ✅ | ✅ | ✅ |

## 5. Cross‑case summary

The table above shows that all cases either used an allowed alias with proper expansion and sub‑notes, or correctly avoided the forbidden overfit alias. No diagnostic sharpness was lost; fail‑open was only triggered when safety required full canonical detail (none of the allowed cases needed it). Reporting ceremony was reduced in the majority of cases (12/14). 

## 6. Alias value review

- **`absence_of_expected_change_pressure`** proved valuable for cases where missing‑effect or unchanged region was the core reasoning (cases 2, 4, 9). It reduced prose while preserving all necessary sub‑notes. 
- **`salience_distractor_pressure`** gave clear benefits for visual‑salience cases (cases 1, 10, 12). The required color/appearance sub‑notes were retained, keeping auditability. 
- Cases with no clear alias benefit (3, 6, 8, 11, 13) remained without alias, preserving detail. 
- The forbidden overfit alias was never used; where it would have been needed (cases 5, 7, 14) the policy forced a canonical‑only handling, preserving safety.

Overall the aliases reduced prose without compromising safety or auditability.

## 7. Forbidden overfit alias review

- **Train‑Output Overfit** (case 7) and **AGT‑06** (case 14) were explicitly checked and no `overfit_specificity_pressure` alias was applied. 
- **Stripe‑anchor ablation** (case 5) avoided the overfit alias; the canonical families were kept separate. 
- Concept‑bloat and coordinate‑overfit remained distinct in all cases. No substitute name re‑introduced the forbidden merge.

## 8. Activation‑gate interaction review

- In every case the activation gate activated the canonical families first; aliases were added **after** activation as a reporting shorthand. 
- Dormant families (e.g., rival‑grammar in case 3) stayed explicit. 
- Fail‑open rules operated as designed; no case required forced expansion because safety never depended on a hidden distinction.
- The gate’s safety catches remained authoritative throughout.

## 9. Diagnostic sharpness review

- No loss of category‑level detail was observed. All sub‑notes required for fine‑grained reasoning were retained. 
- Overfit‑specific detail was preserved by never using the forbidden alias.
- Color/appearance bait detail remained intact via `salience_distractor_pressure` sub‑notes.
- Expected‑missing‑effect detail remained via `absence_of_expected_change_pressure` sub‑notes.

## 10. Schema readiness implications

- The schema remains **premature**; this trial confirms that alias usage is stable enough to consider later encoding as optional display labels. 
- Any future schema must still encode canonical categories first and ensure alias expansion is checklist‑recoverable. 
- No immediate schema work is required.

## 11. Risk review

- **Hidden merge risk**: none observed; forbidden overfit alias stayed blocked. 
- **Fail‑open weakness**: not triggered; policy safe. 
- **Reviewer forgetting expansion**: mitigated by explicit checklist in this trial. 
- **Alias ceremony overhead**: minimal; the two allowed aliases added negligible extra metadata. 
- **Activation‑gate over‑compaction**: avoided; gate remained primary. 
- **Premature schema risk**: still present; schema planning deferred until after further validation.

## 12. Recommended next safe local follow‑up

**RUN_MORE_MICRO_THEORY_ALIAS_POLICY_TRIALS_V1** – the trial succeeded, but extending to a broader set of synthetic mocks will further validate robustness before any schema work.

## 13. Hand‑off update (post‑artifact)

```
- Current verified WESLR HEAD: 7a9a928cbc0819254525ad67f87c7e9eb4140500
- Last pushed remote milestone HEAD: 4e92ed3b2d1043e80e27568990a5c4ae8add7119
- Current local unpushed commit: 7a9a928cbc0819254525ad67f87c7e9eb4140500
- Latest completed local lane: "RUN_MICRO_THEORY_ALIAS_POLICY_ON_EXISTING_MOCKS_V1"
- Current local status: "alias_policy_trial_success"
- Current local executive verdict: "alias_policy_trial_success"
- Current next local WESLR lane: "RUN_MORE_MICRO_THEORY_ALIAS_POLICY_TRIALS_V1"
- Push policy: "no routine pushes until Kaggle intake/test milestone or Nova need"
```