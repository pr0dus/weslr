# WESLR MICRO-THEORY PRESSURE CATEGORY ALIAS POLICY REVIEW V1

## 1. Executive verdict

**alias_policy_valid_ready_for_mock_trial**

## 2. Integrity review

- This lane is **review/report only**. No code execution, no ledger modification, no executable schema creation, and no runtime changes.
- The canonical ledger (`weslr/*` files) remains untouched.
- No solver‑visible or evaluator‑only boundaries are altered.
- Push preparation and push are both avoided.

## 3. Canonical preservation review

The policy **clearly preserves**:
- **Canonical pressure categories** as the authoritative source of truth.
- **Alias expansion** back to the full set of canonical categories is mandatory for every alias use.
- **Audit recoverability**: any audit, safety decision, or future schema can reconstruct the original canonical expansion from the trace.
- **Safety‑decision recoverability**: safety analyses can always expand an alias back to the underlying categories.
- **Future‑schema recoverability**: the policy mandates machine‑checklist‑recoverable expansion before any schema work.
- **Separation of certainty channels**: target/action/representation certainty families are never replaced by an alias.
- **Rival‑grammar and contradiction/precedence families** remain distinct and cannot be collapsed into an alias.

## 4. Allowed alias review – `absence_of_expected_change_pressure`

- **Clarity**: The alias name directly reflects the semantic intent – a missing expected effect or unchanged region.
- **Canonical expansion** is explicitly listed as:
  - negative‑evidence pressure
  - non‑change pressure
- **Sub‑notes** (expected‑but‑missing effect, unchanged region, absence of transformation, evidence from what did not happen) are required to be retained in any trace using the alias.
- **Allowed‑use conditions** are strict: the fine distinction between negative‑evidence and non‑change must *not* be safety‑critical for the particular reasoning.
- **Fail‑open rules** require expanding back whenever safety depends on that fine distinction, auditability would be weakened, or any of the listed conditions appear.
- **Trial recommendation**: the alias is suitable for a mock‑trial on existing micro‑theory mock traces to confirm that the fail‑open behaviour works as intended.

## 5. Allowed alias review – `salience_distractor_pressure`

- **Clarity**: The alias captures the combined notion of generic distractor pressure and visual‑bait pressure.
- **Canonical expansion** is explicitly listed as:
  - distractor‑rejection pressure
  - color/appearance bait pressure
- **Sub‑note protection**: the alias must retain sub‑notes on color bait, appearance bait, salience trap, visible‑but‑incidental feature, and rejected salient explanation.
- **Ignored‑feature cases** remain safe because the alias does not hide the distinction between generic distractor and color‑bait when those are relevant.
- **Allowed‑use conditions**: only when the fine distinction between generic distractor and color‑bait is not safety‑critical.
- **Fail‑open rules** are as strong as for the previous alias.
- **Trial recommendation**: also suitable for a mock‑trial on existing traces to ensure the fail‑open path restores the full canonical families.

## 6. Forbidden alias review – `overfit_specificity_pressure`

- **Rejection clarity**: The policy explicitly marks this alias as **rejected/unsafe**.
- **Protection of concept‑bloat and coordinate‑overfit**: Both families remain separate; no alias can merge them.
- **Alias‑return prevention**: the policy blocks any future alias that would expand to these families, even under a different name, because the explicit rejection entry is checked by the release‑gate.
- **Future reopening conditions** are strict: would require repeated redundancy without audit loss and demonstrably unchanged diagnostic sharpness for overfit cases.
- **Preservation of concerns**: the earlier identified weaknesses (stripe‑anchor ablation, Train‑Output Overfit, AGT‑06) stay documented and unmitigated by any alias.

## 7. Non‑alias category review

All listed non‑alias pressure families remain **separate** and untouched by the alias policy:
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

## 8. Activation‑gate interaction review

- **Canonical families** are still activated first by the activation gate.
- **Aliases** act only as a **reporting layer** after activation; they never replace or hide dormant families.
- **Dormant categories** remain explicit in the trace; an alias cannot make them invisible.
- **Fail‑open rules** always override any compactness benefit of an alias.
- **Activation‑gate safety catches** remain authoritative and unchanged.

## 9. Schema interaction review

- The **future schema** remains **premature**; it will encode canonical categories first.
- **Aliases** may later be optional display/label fields *only after* this policy is reviewed and approved.
- **Alias expansion** must stay **machine/checklist recoverable** before any schema work.
- **Original category names** must persist in the audit trail.
- **Overfit families** must stay separate in any future packet.

## 10. Risk review

- **Hidden‑merge risk**: mitigated by explicit rejection of overfit alias and required fail‑open expansion.
- **Safety‑relevant distinction hiding**: mitigated by strict allowed‑use conditions and fail‑open triggers.
- **Auditability weakening**: mitigated by mandatory expansion back when any safety or audit need arises.
- **Premature schema temptation**: policy explicitly blocks schema work until after review.
- **Reviewer forgetting expansion**: documented fail‑open rule and explicit requirement to list canonical expansion in every trace.
- **Overfit alias re‑appearance**: blocked by explicit rejection entry and release‑gate exact‑path allowance.
- **Activation‑gate compactness**: unchanged; aliases cannot suppress dormant families.
- **Safe‑failure justification**: preserved by keeping canonical families authoritative.

## 11. Recommended next safe local follow‑up

**RUN_MICRO_THEORY_ALIAS_POLICY_ON_EXISTING_MOCKS_V1** – the policy is sound and ready to be exercised on existing mock traces before any schema planning.

## 12. Hand‑off update (post‑artifact)

```
- Current verified WESLR HEAD: 617804ebfbd6bac94aca689be16338d1f6a22196
- Last pushed remote milestone HEAD: 4e92ed3b2d1043e80e27568990a5c4ae8add7119
- Current local unpushed commit: 617804ebfbd6bac94aca689be16338d1f6a22196
- Latest completed local lane: "REVIEW_MICRO_THEORY_PRESSURE_CATEGORY_ALIAS_POLICY_V1"
- Current local status: "alias_policy_valid_ready_for_mock_trial"
- Current local executive verdict: "alias_policy_valid_ready_for_mock_trial"
- Current next local WESLR lane: "RUN_MICRO_THEORY_ALIAS_POLICY_ON_EXISTING_MOCKS_V1"
- Push policy: "no routine pushes until Kaggle intake/test milestone or Nova need"
```