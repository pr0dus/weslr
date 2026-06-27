# WESLR MICRO-THEORY LEDGER ACTIVATION GATE V1

## Status
Design/report only. Local-only. Bounded exploratory posture. No implementation, no executable schemas, no runtime solver work, no solver patching, no provider/model calls, no public ARC/Kaggle ingestion, no benchmark/public claims, no learned scorer implementation, no final-answer generation, no `.weslr` writes, no push preparation, and no push.

## 1. Executive summary
`activation_gate_design_valid_but_needs_mock_trial`

The activation gate is a lightweight pre-ledger triage layer that decides which pressure families should wake up before a full ledger pass.

It is needed because the ledger has now shown real protective value under ablation and adversarial mocks, but its ceremony cost is visibly rising. The gate is meant to reduce needless pressure-family activation while preserving the catches that actually kept Micro-Theory safe.

## 2. Problem statement
Current state:
- the ledger held under adversarial tests
- the ledger does real protective work
- but the ledger is heavy
- not all pressure categories should fire in every trace
- ceremony risk is now the main design problem before any schema lane

Without a gate, the system risks either:
- paying too much interpretive overhead on simple traces, or
- responding by collapsing categories too early and losing protective precision

## 3. Activation gate concept
The activation gate is:
- pre-ledger triage
- a pressure-family activator
- a ceremony reducer
- a fail-open safety layer

It is not:
- a scorer
- a solver
- an implementation
- a final-answer mechanism

Its job is not to decide the output. Its job is to decide which interpretive families must be present so the later ledger can stay proportionate without becoming blind.

## 4. Always-on minimal checks
These must always run before any compact ledger is allowed:

- solver-visible / evaluator-only boundary check
- synthetic / public-data boundary check
- train backward / test forward discipline check
- target / action / representation certainty check
- rival grammar possibility check
- counterfactual stability smell check
- safe-failure availability check
- scorer-boundary check

Why always-on:
These are the minimal anti-self-deception checks. If any of them are skipped, a compact ledger can become unsafe even when no obvious pressure family looks active.

## 5. Pressure-family activation signals

### role stability pressure
- activation signal: same functional target persists under visible appearance change
- dormancy condition: no evidence that role continuity matters beyond direct object identity
- fail-open trigger: visible feature changes while target remains behaviorally stable
- example: role/color inversion
- ceremony risk if always activated: moderate
- safety risk if skipped: medium

### relation stability pressure
- activation signal: selection depends on spatial/structural relation rather than raw object token
- dormancy condition: one object is uniquely targeted without relational ambiguity
- fail-open trigger: multiple objects become distinguishable only through relation
- example: role/color inversion, rival grammar mocks
- ceremony risk if always activated: moderate
- safety risk if skipped: high

### absence pressure
- activation signal: output responds to an expected-but-missing member
- dormancy condition: all causal targets are visibly present
- fail-open trigger: repair/completion language appears necessary
- example: absence/exception
- ceremony risk if always activated: high
- safety risk if skipped: high

### exception pressure
- activation signal: one object violates the broader pattern or is lawfully excluded
- dormancy condition: no meaningful violator or outlier affects interpretation
- fail-open trigger: candidate grammar depends on singling out a non-member or protected exception
- example: absence/exception, contradiction-resolution
- ceremony risk if always activated: moderate
- safety risk if skipped: medium

### contradiction / precedence pressure
- activation signal: two real pressures conflict and one must outrank the other
- dormancy condition: no genuine rule conflict appears
- fail-open trigger: a candidate output is vetoed by another equally real pressure
- example: contradiction-resolution
- ceremony risk if always activated: high
- safety risk if skipped: high

### negative-evidence pressure
- activation signal: what did not happen is part of the explanation
- dormancy condition: non-transformation evidence is not doing interpretive work
- fail-open trigger: a weaker grammar would change something that stayed untouched
- example: absence/exception, contradiction-resolution
- ceremony risk if always activated: high
- safety risk if skipped: medium

### distractor-rejection pressure
- activation signal: a visually tempting object must be explicitly ruled out
- dormancy condition: no plausible distractor competes for causality
- fail-open trigger: baseline grammar would otherwise drift to salience-led targeting
- example: role/color inversion, absence/exception
- ceremony risk if always activated: moderate
- safety risk if skipped: medium

### non-change pressure
- activation signal: preserved regions or objects are themselves explanatory
- dormancy condition: untouched structure does not constrain interpretation
- fail-open trigger: candidate grammar predicts extra change or cannot explain stability
- example: absence/exception, contradiction-resolution
- ceremony risk if always activated: high
- safety risk if skipped: medium

### output-shape pressure
- activation signal: output form itself is contested or informative beyond target choice
- dormancy condition: action form is obvious once target/action are fixed
- fail-open trigger: multiple output structures remain plausible
- example: target/action trap, rival grammar cases
- ceremony risk if always activated: moderate
- safety risk if skipped: medium

### target-location pressure
- activation signal: multiple candidate targets survive unless explicitly separated
- dormancy condition: exactly one target is plainly forced
- fail-open trigger: target ambiguity remains after train interpretation
- example: nearly all nontrivial mocks
- ceremony risk if always activated: low
- safety risk if skipped: high

### action-type pressure
- activation signal: target may be clear while action remains unresolved
- dormancy condition: operation class is uniquely earned
- fail-open trigger: fill vs mark vs preserve or analogous alternatives remain live
- example: absence/exception, target/action split trap
- ceremony risk if always activated: low
- safety risk if skipped: high

### color / appearance bait pressure
- activation signal: surface appearance looks causal but may be incidental
- dormancy condition: appearance is stably causal and not challenged
- fail-open trigger: hue/shape/appearance shifts while role logic persists
- example: role/color inversion
- ceremony risk if always activated: moderate
- safety risk if skipped: medium

### coordinate-overfit pressure
- activation signal: grammar appears to memorize absolute position or offset
- dormancy condition: coordinates are not carrying suspicious explanatory load
- fail-open trigger: rotated/shifted counterfactual would likely break the grammar
- example: train-output overfit adversarial mock
- ceremony risk if always activated: moderate
- safety risk if skipped: high

### concept-bloat pressure
- activation signal: grammar invents too many private concepts for limited evidence
- dormancy condition: vocabulary stays compact and reused
- fail-open trigger: one-off roles or ad hoc packets multiply to save train fit
- example: some rival-grammar and overfit cases
- ceremony risk if always activated: moderate
- safety risk if skipped: medium

### rival-grammar pressure
- activation signal: two compact grammars survive with different test projections
- dormancy condition: one grammar is genuinely disambiguated by train
- fail-open trigger: rejected-output audit cannot eliminate a plausible rival
- example: ambiguity/rival grammar, ablation mock, adversarial Mock A
- ceremony risk if always activated: low
- safety risk if skipped: very high

### counterfactual stability pressure
- activation signal: small lawful variation could break the preferred grammar
- dormancy condition: no meaningful counterfactual fragility is visible
- fail-open trigger: a one-step counterfactual would immediately separate grammars or expose brittle fit
- example: ablation mock, adversarial Mocks A and B
- ceremony risk if always activated: moderate
- safety risk if skipped: very high

## 6. Gate modes
- `compact_ledger`
  - always-on checks plus 1–2 activated pressure families
- `focused_ledger`
  - always-on checks plus several clearly activated pressure families
- `full_ledger`
  - used when rival grammars, contradictions, overfit risk, or multi-axis ambiguity are present
- `safe_failure_review`
  - used when the gate itself is uncertain, boundary risk appears, or compactness would suppress abstention

## 7. Fail-open rules
The gate must escalate to fuller ledger review when:
- rival grammar is plausible
- target/action/representation certainty disagree
- counterfactual stability is weak
- train examples support multiple grammars
- preferred grammar ignores a visible feature
- rejected-output audit is incomplete but rival output is plausible
- contradiction / precedence appears
- evaluator-only contamination risk exists
- public-data boundary uncertainty exists
- safe failure would be blocked by compact mode

## 8. Existing mock mapping

### A. Original four synthetic trace mocks
- role/color inversion
  - likely gate mode: `focused_ledger`
  - activated: role stability, relation stability, target-location, color/appearance bait, distractor-rejection
  - dormant: absence, contradiction, output-shape, most overfit families
  - protective catch preserved: yes
  - ceremony reduced: yes

- absence/exception
  - likely gate mode: `focused_ledger`
  - activated: absence, exception, target-location, action-type, non-change, negative-evidence
  - dormant: contradiction unless a real veto appears, coordinate-overfit, color-bait
  - protective catch preserved: yes
  - ceremony reduced: somewhat

- ambiguity/rival grammar safe failure
  - likely gate mode: `full_ledger`
  - activated: rival-grammar, target-location, action-type, output-shape, counterfactual stability
  - dormant: distractor, absence, contradiction unless a real veto appears
  - protective catch preserved: yes
  - ceremony reduced: only slightly

- contradiction-resolution
  - likely gate mode: `full_ledger`
  - activated: contradiction/precedence, exception, non-change, negative-evidence, target-location, action-type
  - dormant: color-bait, coordinate-overfit
  - protective catch preserved: yes
  - ceremony reduced: moderately

### B. Ablation confident-wrong mock
- stripe-extension anchor marker
  - likely gate mode: `full_ledger`
  - activated: rival-grammar, target-location, action-type, counterfactual stability, coordinate-overfit
  - dormant: absence, contradiction, distractor, non-change
  - protective catch preserved: yes
  - ceremony reduced: yes

### C. Adversarial bidirectional mocks
- Coincident Rival Grammar
  - likely gate mode: `full_ledger`
  - activated: rival-grammar, relation stability, target-location, counterfactual stability
  - dormant: absence, contradiction, distractor, non-change
  - protective catch preserved: yes
  - ceremony reduced: yes

- Train-Output Overfit
  - likely gate mode: `full_ledger`
  - activated: coordinate-overfit, counterfactual stability, rival-grammar, concept-bloat
  - dormant: absence, contradiction, distractor, non-change
  - protective catch preserved: yes
  - ceremony reduced: yes

- Target/Action Split Trap
  - likely gate mode: `focused_ledger`
  - activated: target-location, action-type, rival-grammar, output-shape
  - dormant: contradiction, absence, coordinate-overfit, distractor
  - protective catch preserved: yes
  - ceremony reduced: yes

## 9. Protective-catch preservation
The gate should preserve these proven catches:
- ablation mock: live rival grammar + weak counterfactual stability must fail open to fuller review
- adversarial Mock A: compression must not become inevitability while rival grammar survives
- adversarial Mock B: coordinate-overfit and weak counterfactual stability must stay active
- adversarial Mock C: target/action split must never collapse into one confidence channel

If any future compact mode suppresses those catches, the gate design has failed.

## 10. Ceremony reduction assessment
Where ceremony is reduced:
- inactive pressure families stay dormant by default
- simple traces avoid full-ledger burden
- overlap families matter less when neither one is activated

Which categories become dormant most often:
- contradiction / precedence
- absence
- distractor-rejection
- color/appearance bait
- negative-evidence
- non-change

Do overlap issues matter less with gating?
- negative-evidence/non-change: yes
- distractor-rejection/color-bait: yes
- concept-bloat/coordinate-overfit: somewhat, but less than the others

Should category collapse still wait?
- yes
- gating should be tested before collapse, because some overlap pain may vanish once dormant families stop auto-appearing

## 11. Interaction with future collapsed-category experiment
Activation gate comes before category collapse because:
- we do not yet know whether overlap is structural or just over-activation noise
- gating can reveal which families are truly co-active in practice

Likely later merge candidates remain:
- negative-evidence + non-change
- distractor-rejection + color/appearance bait
- perhaps concept-bloat + coordinate-overfit only if testing shows repeated redundancy

Categories that should stay separate for now:
- rival-grammar
- target-location
- action-type
- contradiction/precedence
- counterfactual stability

## 12. Interaction with future trace packet schema
Schema remains premature because:
- the gate itself has not yet been tested against prior mocks
- we do not yet know whether activation decisions are stable enough to formalize

What the gate must prove before schema:
- ceremony reduction without protective-catch loss
- stable mode selection across repeated mock families
- reliable fail-open behavior

Should a future packet encode activation decisions?
- yes, probably as explicit gate outputs

Should dormant categories be absent or explicitly marked dormant?
- explicit dormant marking is safer for auditability in design artifacts

Should always-on checks be mandatory packet fields?
- yes

## 13. Risk review
- gate skips a necessary pressure family: high risk if signals are too strict
- gate becomes a shortcut scorer: medium risk if mode labels drift into confidence labels
- gate hides uncertainty: high risk unless fail-open rules are strong
- gate over-trusts preferred grammar: high risk unless rival-grammar and visible-feature checks stay always-on or near-always-on
- gate reduces auditability too much: medium risk
- gate fails closed too often: medium risk
- gate fails open too often, preserving ceremony: medium risk
- gate complicates schema later: moderate, but still preferable to premature schema now

## 14. Recommended next safe local follow-up
`RUN_MICRO_THEORY_ACTIVATION_GATE_ON_EXISTING_MOCKS_V1`

Reason:
The design is clear enough to manually test against the already-built mock family, and that is the smallest meaningful proof step before review-only or schema work.

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
Activation gate design is valid.

Micro-Theory direction should continue.

Activation gate should be manually tested next.

Pressure-category collapse remains premature.

Trace packet schema remains premature.

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
- manual gate application reduces ceremony on existing mocks
- proven adversarial catches are preserved
- fail-open rules trigger exactly when they should
- only after that should review or schema questions advance
