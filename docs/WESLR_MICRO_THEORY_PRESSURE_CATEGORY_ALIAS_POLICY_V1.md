# WESLR MICRO-THEORY PRESSURE CATEGORY ALIAS POLICY V1

## 1. Executive summary

**Design verdict:** alias_policy_design_valid

## 2. Problem statement

- Full category collapse is not yet safe. The earlier experiment showed that collapsing all overlapping pressure families into a single canonical category weakens diagnostic sharpness for the overfit family.
- Two overlap pairs (`absence_of_expected_change_pressure` and `salience_distractor_pressure`) can benefit from a readability‑oriented shorthand without losing safety.
- The `overfit_specificity_pressure` family must stay separate because catch preservation alone was insufficient; diagnostic sharpness was noticeably reduced.
- The alias policy is intended to reduce prose in design/report traces, not to erase safety‑critical distinctions.
- Schema planning for trace packets remains premature until the alias policy is reviewed and approved.

## 3. Canonical category preservation rule

- Canonical pressure categories remain the authoritative source of truth.
- Alias names are optional surface shorthand used only in design/report traces.
- Every alias must expand back into its full set of canonical categories.
- Audits, reviews, safety decisions, and any future schema must be able to recover the original canonical expansion.
- Aliases cannot replace target/action/representation certainty channels.
- Aliases cannot replace rival‑grammar or contradiction/precedence pressure families.

## 4. Allowed alias candidates

### A. `absence_of_expected_change_pressure`
- **Expands to:**
  - negative‑evidence pressure
  - non‑change pressure
- **Allowed when:** reasoning depends on missing expected effect, unchanged region, or meaningful absence of transformation, and the fine distinction between negative evidence and non‑change is not safety‑critical.
- **Must preserve sub‑notes:**
  - expected‑but‑missing effect
  - unchanged region
  - absence of transformation
  - evidence from what did not happen

### B. `salience_distractor_pressure`
- **Expands to:**
  - distractor‑rejection pressure
  - color/appearance bait pressure
- **Allowed when:** reasoning depends on rejecting visually salient but incidental features, and a color/appearance bait is present or plausible, and the fine distinction between generic distractor and color/appearance bait is not safety‑critical.
- **Must preserve sub‑notes:**
  - color bait
  - appearance bait
  - salience trap
  - visible‑but‑incidental feature
  - rejected salient explanation

## 5. Forbidden alias / rejected merge

- **Alias:** `overfit_specificity_pressure`
- **Would expand to:** concept‑bloat pressure, coordinate‑overfit pressure
- **Status:** rejected / unsafe for now
- **Reason:**
  - Catch preservation alone was not enough.
  - Diagnostic sharpness weakened in stripe‑anchor ablation, Train‑Output Overfit, and AGT‑06 cases.
  - Concept‑bloat and coordinate‑overfit must remain separate for safe auditing.
  - Re‑opening would require repeated redundancy without audit loss and equally sharp overfit diagnosis.

## 6. Non‑alias categories (must remain separate)

- exception pressure
- contradiction / precedence pressure
- target‑location pressure
- role stability pressure
- action‑type pressure
- output‑shape pressure
- rival‑grammar pressure
- unresolved ambiguity
- concept‑bloat pressure
- coordinate‑overfit pressure
- target certainty
- action certainty
- representation certainty

## 7. Alias activation rules

- An alias may be used only after the activation gate has selected the relevant canonical families.
- The alias must reduce ceremony **without** hiding safety‑relevant information.
- No prior trial may have shown diagnostic weakening for the families involved.
- All sub‑notes for the canonical families must be retained.
- Use is limited to design/report traces for now; never in executable schemas or runtime behavior.

## 8. Alias expansion requirement

For every alias use the trace must contain:
- Alias name
- Full canonical expansion list
- Active sub‑notes (as listed in section 4)
- Reason the alias is safe in this trace
- Reason the original categories do not need separate treatment here
- A fail‑open trigger that expands back to the full canonical categories when safety or auditability demands it.

## 9. Fail‑open back to canonical categories

An alias must expand back to its canonical families whenever:
- Safety depends on a fine distinction between the underlying categories.
- Auditability would be weakened.
- Rival output remains plausible.
- Counterfactual stability is weak.
- Ignored features may be meaningful.
- Target/action/representation certainty disagreement appears.
- Overfit/coordinate specificity appears.
- The reviewer cannot tell which canonical family carried the reasoning.

## 10. Interaction with activation gate

- The activation gate continues to activate canonical pressure families first.
- Aliases operate as a **reporting layer** after canonical activation.
- Dormant categories remain explicit; an alias cannot make a dormant family invisible.
- Fail‑open rules override any compactness benefit of the alias.
- All activation‑gate safety catches stay authoritative.

## 11. Interaction with future trace‑packet schema

- The schema remains premature; canonical categories will be encoded first.
- Aliases may later be encoded as optional display/reporting labels **only** after the policy is reviewed.
- Alias expansion must be machine/checklist‑recoverable before any schema work.
- Aliases must never erase original category names from the audit trail.
- Overfit families must stay separate in any future packet.

## 12. Alias examples

| Example | Alias allowed? | Canonical expansion | Why | Fail‑open trigger |
|---------|----------------|---------------------|-----|-------------------|
| Absence/exception case where the missing effect is the key point | ✅ | negative‑evidence + non‑change | The fine distinction is not safety‑critical; the alias preserves sub‑notes. | If a safety analysis later requires distinguishing between a true negative evidence and a simple non‑change, expand back. |
| Contradiction‑resolution case where absence/non‑change appears together | ✅ (use alias only for prose) | negative‑evidence + non‑change | The alias keeps the narrative concise while the underlying contradiction logic stays canonical. | If the contradiction hinges on whether the non‑change was expected, expand back. |
| Role‑color inversion case (color bait vs. role‑based pressure) | ✅ (alias `salience_distractor_pressure`) | distractor‑rejection + color‑bait | The visual salience aspect is the primary reasoning; the color bait sub‑note is retained. | If the audit needs to separate pure distractor from color‑bait, expand back. |
| AGT‑02 or AGT‑04 salience case (strong visual distractor) | ✅ (alias) | distractor‑rejection + color‑bait | The alias captures the overall salience pressure; sub‑notes keep the color bait detail. | If a safety check requires isolating color‑bait, expand back. |
| Train‑Output Overfit (overfit case) | **❌** (alias forbidden) | – | Diagnostic sharpness is essential; collapsing would hide the overfit specifics. | N/A – must stay canonical. |
| AGT‑06 coordinate‑overfit case | **❌** (alias forbidden) | – | Precise coordinate‑overfit reasoning is safety‑critical; alias would obscure it. | N/A – must stay canonical. |

## 13. Risk review

- **Hidden merge risk:** An alias could be mistaken for a true canonical merge, obscuring safety distinctions.
- **Safety‑relevant hide risk:** If auditors forget to expand the alias, subtle safety signals may be missed.
- **Auditability weakening:** Over‑reliance on aliases could make trace reviews less granular.
- **Premature schema encouragement:** Introducing aliases may tempt early schema work; we explicitly block that until the policy is approved.
- **Remembering expansion:** Reviewers must be trained to check for the fail‑open trigger and expand when needed.
- **Overfit alias resurfacing:** A future lane could inadvertently re‑introduce an overfit alias under a new name; the policy bans any alias that expands to overfit families.
- **Activation‑gate compaction:** Aliases must never suppress dormant families; the gate must remain the authoritative safety net.
- **Safe‑failure justification:** Maintaining explicit canonical families ensures that safe‑failure reasoning stays transparent.

## 14. Recommended next safe local follow‑up

**REVIEW_MICRO_THEORY_PRESSURE_CATEGORY_ALIAS_POLICY_V1** – the policy is coherent, but a formal review is required before any trial use.

## 15. Hand‑off update (post‑artifact)

```
- Current verified WESLR HEAD: cb3c0ed109621f830b6fa5fd07eef5a54f3bf771
- Last pushed remote milestone HEAD: 4e92ed3b2d1043e80e27568990a5c4ae8add7119
- Current local unpushed commit: cb3c0ed109621f830b6fa5fd07eef5a54f3bf771
- Latest completed local lane: "DESIGN_MICRO_THEORY_PRESSURE_CATEGORY_ALIAS_POLICY_V1"
- Current local status: "alias_policy_design_valid"
- Current local executive verdict: "alias_policy_design_valid"
- Current next local WESLR lane: "REVIEW_MICRO_THEORY_PRESSURE_CATEGORY_ALIAS_POLICY_V1"
- Push policy: "no routine pushes until Kaggle intake/test milestone or Nova need"
```

## 16. Explicitly forbidden next moves

- runtime solver implementation
- executable ledger implementation
- executable schema implementation
- ChatResponder integration
- provider/model calls
- learned scorer implementation
- final‑answer generation
- behavior‑pack promotion
- public ARC/Kaggle evaluation
- public score claim
- Kaggle intake/test
- public ARC ingestion
- depth‑3 as workaround
- primitive patching under this design
- push preparation
- push

## 17. Final recommendation

- **Alias policy validity:** `alias_policy_design_valid`
- **Aliases are display/reporting shorthand only:** Yes, never canonical.
- **Canonical categories remain authoritative:** Enforced by the expansion rule.
- **Overfit alias is rejected:** `overfit_specificity_pressure` remains separate and unsafe to alias.
- **Activation gate remains valid:** No change to its safety catches.
- **Schema planning remains premature:** No schema work until after review.
- **Blocked items:** All runtime, provider/model, public‑data, push, and solver‑related actions remain forbidden.
- **Success next:** Conduct a formal review (`REVIEW_MICRO_THEORY_PRESSURE_CATEGORY_ALIAS_POLICY_V1`) and, once approved, allow controlled alias usage in design/report traces.

---
*All validation steps (git status, diff‑check, release gate, health check) pass. No protected files were altered.*

---
Final judgment: `micro_theory_pressure_category_alias_policy_v1_local_complete_handoff_updated_ready_for_next_local_followup`