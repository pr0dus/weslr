# WESLR MICRO-THEORY COLLAPSED PRESSURE CATEGORY EXPERIMENT REVIEW V1

## Status
Review/report only. Local-only. Bounded exploratory posture. Canonical ledger unchanged. No implementation, no executable schemas, no runtime solver work, no solver patching, no provider/model calls, no public ARC/Kaggle ingestion, no benchmark/public claims, no learned scorer implementation, no final-answer generation, no `.weslr` writes, no push preparation, and no push.

## 1. Executive verdict
`collapse_experiment_valid_first_two_later_overfit_rejected`

The collapsed-category experiment is valid.

It supports carrying forward the first two merged families only as later candidates, not as canonical merges now. It also supports rejecting the overfit merge in its current form, because catch preservation alone was not enough: diagnostic sharpness degraded in the exact cases where the project most needs precise failure language.

## 2. Experiment integrity review
- experiment was manual/design-only: yes
- synthetic-only cases: yes
- canonical ledger unchanged: yes
- activation gate kept in play: yes
- no implementation/schema/runtime/provider/public-data work: yes
- solver-visible/evaluator-only boundary preserved: yes

Assessment:
The experiment stayed within the correct epistemic boundary. It was a representational simplification test, not an implementation shortcut, and that makes the result trustworthy enough to use for design steering.

## 3. Family review: `absence_of_expected_change_pressure`
### safety preservation
Strong.
No reviewed case indicated lost safety when negative-evidence and non-change were read together under one experimental umbrella.

### auditability preservation
Mostly preserved.
The review input did not show a meaningful loss of explanation quality in the tested cases. In contradiction-resolution and absence/exception, the real diagnostic center remained elsewhere, so combining these two signals did not blur the main safety story.

### ceremony reduction
Real but moderate.
This merge reduces overlap prose where both “what did not happen” and “what stayed protected” were traveling together anyway.

### cases supporting merge
- absence/exception
- contradiction-resolution
- AGT-01 (with caution)

### cases cautioning against merge
- AGT-01 suggests the merged family can sound slightly heavier than a plain non-change reading when the case is trivially no-op

### should it become...
- canonical merge now: no
- future alias candidate: yes
- future merge candidate after more trials: yes
- rejected: no

Conclusion:
`absence_of_expected_change_pressure` survives as a future alias candidate and a future merge candidate after more trials.

## 4. Family review: `salience_distractor_pressure`
### safety preservation
Strong.
The key salience-trap cases kept their catches.

### auditability preservation
Mostly preserved.
The review input shows a small loss in subtyping detail—bait versus distractor is not always named separately—but no meaningful safety loss appeared in the tested cases.

### ceremony reduction
Real.
This merge gave the cleanest prose benefit in the overlap-heavy salience cases.

### role/color inversion behavior
Good.
The merged family still clearly carried the burden of demoting appearance-based explanation.

### ignored-feature behavior
Good with caution.
AGT-04 still fail-opened correctly, but the merged family is slightly less specific about whether the issue is raw appearance bait or broader competing-object salience.

### whether color/appearance bait still needs any special sub-note
Yes, probably as a sub-note or expandable explanation later if aliases are adopted. The merged label is fine as a top-level shorthand, but appearance bait remains a useful sub-distinction.

### should it become...
- canonical merge now: no
- future alias candidate: yes
- future merge candidate after more trials: yes
- rejected: no

Conclusion:
`salience_distractor_pressure` is a viable future alias candidate and a plausible later merge candidate, but it should preserve an optional appearance-bait sub-note.

## 5. Family review: `overfit_specificity_pressure`
### why catch preservation was not enough
Because the overfit family’s job is not only to catch failure, but to explain which kind of brittle failure is occurring. Losing that distinction weakens future design decisions even if the final abstention still happens.

### where diagnostic sharpness weakened
- stripe-anchor ablation
- Train-Output Overfit
- AGT-06 coordinate-specific overfit case

### Train-Output Overfit result
This was the clearest rejection signal. The merged family blurred together:
- private concept inflation
- coordinate anchoring

Those are related, but not interchangeable. The original split explained why the candidate grammar was bad in two different ways.

### AGT-06 coordinate-specific result
Also clearly negative for merge. The coordinate-specific brittleness remained catchable, but less directly inspectable once collapsed.

### whether concept-bloat and coordinate-overfit should stay separate
Yes.
They should remain separate for now.

### whether this merge should be rejected or deferred
Rejected for now as a merge.
Not merely deferred neutrally.

### what kind of future evidence would be needed to reopen it
- cases showing repeated redundancy between the two families without audit loss
- evidence that one family can be safely represented as a sub-note of the other
- proof that overfit diagnosis remains equally sharp under collapse

Conclusion:
`overfit_specificity_pressure` should remain separate and is currently best treated as `reject_merge` / `unsafe_to_merge`.

## 6. Non-collapse confirmation
These remain separate:
- exception vs contradiction/precedence: confirmed separate
- target-location vs role stability: confirmed separate
- action-type vs output-shape: confirmed separate
- rival-grammar vs unresolved ambiguity: confirmed separate
- target/action/representation certainty channels: confirmed separate

## 7. Protective-catch review
- role/color inversion salience rejection: preserved
- absence/exception expected-missing-change reasoning: preserved
- ambiguity/rival grammar safe failure: preserved
- contradiction-resolution precedence handling: preserved
- stripe-anchor live rival grammar and weak counterfactual stability catch: preserved
- Coincident Rival Grammar fake-inevitability block: preserved
- Train-Output Overfit overfit catch: preserved, but less sharply diagnosed under collapsed overfit family
- Target/Action Split Trap false full-prediction block: preserved
- AGT-04 ignored-feature fail-open: preserved
- AGT-06 coordinate-specific overfit diagnosis: preserved, but weakened

## 8. Diagnostic sharpness review
### where auditability improved
- overlap-heavy absence/non-change cases became tidier
- overlap-heavy salience cases became tidier

### where auditability stayed the same
- rival-grammar-driven cases
- certainty-disagreement cases
- contradiction-centered cases where the overlap families were secondary

### where auditability weakened
- overfit-specific cases
- anchor-sensitive ablation reasoning

### whether weaker auditability is acceptable for first two merges
Yes, within limits.
For the first two merges, the loss is small enough that alias-style reuse remains plausible.

### why weaker auditability is not acceptable for overfit merge
Because the entire design question in those cases is often: “what exact kind of brittle overfit is happening?” A blurrier answer there is a real regression, not just stylistic simplification.

## 9. Activation-gate interaction review
- activation gate reduces urgency of canonical merges: yes
- collapse plus gating helped beyond gating alone: somewhat
- explicit dormant categories remain useful: yes
- future gate should support collapsed aliases without losing original category names: yes, if aliases are ever adopted
- gate mode distribution changed materially: no

Assessment:
The gate already removed much of the pressure to merge categories aggressively. That means future simplification can be more conservative and more alias-oriented.

## 10. Category decision table
- `absence_of_expected_change_pressure` → `candidate_alias_later`
- `salience_distractor_pressure` → `candidate_alias_later`
- `overfit_specificity_pressure` → `unsafe_to_merge`

## 11. Schema readiness review
- whether schema remains premature: yes
- whether future schema should encode canonical categories only: yes, for now
- whether future schema may support aliases: yes, later
- whether alias support should preserve original category expansion: yes
- what must happen before schema planning is allowed:
  - alias policy must be clarified
  - overfit family separation must remain protected
  - at least one more positive review cycle should confirm that alias-level simplification does not hide safety structure

## 12. Risk review
- false simplification risk: real if aliases are mistaken for true category collapse
- loss of diagnostic sharpness: acceptable for first two only in limited alias form; unacceptable for overfit merge
- overfit-specificity vagueness: high
- salience category becoming too broad: moderate but manageable
- absence/non-change losing useful distinction: low-to-moderate but manageable
- premature schema risk: high
- whether any future merge could damage safe failure: yes, especially if overfit collapse were adopted carelessly

## 13. Recommended next safe local follow-up
`DESIGN_MICRO_THEORY_PRESSURE_CATEGORY_ALIAS_POLICY_V1`

Reason:
The review result is strong enough to define how future aliasing could work without authorizing canonical merge. That is the narrowest useful next design step.

## 14. Update WESLR_CURRENT_HANDOFF.md after artifact completion
This artifact should move the local lane state to:
- completed lane: `REVIEW_MICRO_THEORY_COLLAPSED_PRESSURE_CATEGORY_EXPERIMENT_V1`
- next lane: `DESIGN_MICRO_THEORY_PRESSURE_CATEGORY_ALIAS_POLICY_V1`

## 15. Explicitly forbidden next moves
Remain forbidden:
- runtime solver implementation
- executable ledger implementation
- executable schema implementation
- ChatResponder integration
- provider/model calls
- learned scorer implementation
- final-answer generation
- behavior-pack promotion
- public ARC/Kaggle evaluation
- public score claim
- Kaggle intake/test
- public ARC ingestion
- depth-3 as workaround
- primitive patching under this design
- push preparation
- push

## 16. Final recommendation
The collapsed-category experiment was valid.

Two merged families survive only as later candidates:
- `absence_of_expected_change_pressure`
- `salience_distractor_pressure`

One merged family is rejected as unsafe to merge now:
- `overfit_specificity_pressure`

Activation gate remains valid.

Micro-Theory direction should continue.

Schema planning is still premature.

What remains blocked:
- runtime solver implementation
- executable ledger implementation
- executable schema implementation
- provider/model calls
- public ARC/Kaggle intake/test
- public claims
- learned scorer implementation
- final-answer generation
- behavior-pack promotion
- push preparation
- push

What success should look like next:
- alias policy cleanly defines how shorthand names may exist without deleting canonical distinctions
- overfit families remain explicitly separated
- future simplification stays reversible and audit-friendly
