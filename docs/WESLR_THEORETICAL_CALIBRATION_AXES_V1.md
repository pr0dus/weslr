# WESLR Theoretical Calibration Axes V1

## 1. Purpose
A theoretical calibration axis maps a theory family to a specific WESLR failure mode so the theory is only useful when it improves calibration for that failure mode.

Core question:
- What failure mode does this calibrate?

## 2. Design rule
A theory is useful for WESLR only if it clearly states:
- the failure mode it calibrates
- the calibration question it answers
- the safe internal use
- the forbidden misuse
- the expected next-step effect

The framework must stay metadata-only, deterministic, and authority-safe.

## 3. Axis field model
Each axis uses these fields:
- `axis_id`
- `theory_family`
- `calibrated_failure_mode`
- `calibration_question`
- `safe_internal_use`
- `forbidden_misuse`
- `next_step_effect`
- `example_application`
- `authority_status`
- `safe_metadata`

## 4. Theoretical calibration axes

### A. Reverse Calibration / Backcasting
- `axis_id`: `reverse_calibration_backcasting`
- `theory_family`: `reverse_calibration`
- `calibrated_failure_mode`: `calibrate_everything`
- `calibration_question`: What earlier signal phase justifies the next step without collapsing everything into calibration?
- `safe_internal_use`: Back-map from known outcomes to earlier signal phases and step selection.
- `forbidden_misuse`: Treating backcasting as discovery, proof, or prediction authority.
- `next_step_effect`: Encourages `probe`, `pressure_test`, `calibrate`, `archive`, or `blocked_by_safety` only when the evidence earns it.
- `example_application`: Explain why a known-outcome trace starts with probe rather than immediate calibration.

### B. Adversarial / GAN Calibration
- `axis_id`: `adversarial_gan_calibration`
- `theory_family`: `adversarial_pressure`
- `calibrated_failure_mode`: `creative_but_unpressuretested_candidate`
- `calibration_question`: Does the candidate survive critique, counterexample pressure, and adversarial selection?
- `safe_internal_use`: Stress-test candidates before promoting them.
- `forbidden_misuse`: Public claim escalation, runtime adversarial deployment, or unsafe optimization pressure.
- `next_step_effect`: Moves weak candidates toward `pressure_test` or `needs_repair`.
- `example_application`: Reject an elegant idea that fails under small adversarial probes.

### C. Gödel / Incompleteness Calibration
- `axis_id`: `godel_incompleteness_calibration`
- `theory_family`: `incompleteness`
- `calibrated_failure_mode`: `fake_certainty_inside_incomplete_system`
- `calibration_question`: Where does the system need humility because not everything can be resolved internally?
- `safe_internal_use`: Mark irreducible limits and avoid pretending closure exists.
- `forbidden_misuse`: Using incompleteness to justify public uncertainty theater or permanent paralysis.
- `next_step_effect`: Can shift to `watch`, `operator_review`, or `needs_repair` when certainty is unjustified.
- `example_application`: Recognize a boundary where the model cannot prove what it is being asked to prove.

### D. Popper / Falsification Calibration
- `axis_id`: `popper_falsification_calibration`
- `theory_family`: `falsification`
- `calibrated_failure_mode`: `unfalsifiable_direction`
- `calibration_question`: What observation would make the direction fail?
- `safe_internal_use`: Force explicit disconfirming signals and tests.
- `forbidden_misuse`: Pretending an unfalsifiable idea is evidence-backed.
- `next_step_effect`: Moves from speculative direction into `probe` or `pressure_test`.
- `example_application`: Require a disconfirming signal before accepting a new explanation.

### E. Bayesian Calibration
- `axis_id`: `bayesian_calibration`
- `theory_family`: `bayesian_update`
- `calibrated_failure_mode`: `confidence_does_not_move_or_moves_too_fast`
- `calibration_question`: Does evidence move confidence at the right speed?
- `safe_internal_use`: Update belief posture proportionally to evidence.
- `forbidden_misuse`: Treating Bayesian language as a guarantee of truth or authority.
- `next_step_effect`: Supports `calibrate`, `watch`, or `pressure_test` depending on evidence density.
- `example_application`: Slow confidence when evidence is thin; accelerate only when evidence repeats.

### F. Signal Detection Calibration
- `axis_id`: `signal_detection_calibration`
- `theory_family`: `signal_detection`
- `calibrated_failure_mode`: `noise_as_signal_or_signal_as_noise`
- `calibration_question`: Is this a true signal, a false positive, or a false negative?
- `safe_internal_use`: Balance sensitivity and specificity.
- `forbidden_misuse`: Rebranding noise as evidence or evidence as noise to fit a preferred story.
- `next_step_effect`: Directs `probe`, `pressure_test`, or `watch` based on false-positive/false-negative risk.
- `example_application`: Keep a repeating pattern in view without declaring it real too early.

### G. Control Theory / Cybernetic Calibration
- `axis_id`: `cybernetic_control_calibration`
- `theory_family`: `control_theory`
- `calibrated_failure_mode`: `endless_calibration_loop_or_overreaction`
- `calibration_question`: Is the loop correcting smoothly or oscillating, stalling, or overreacting?
- `safe_internal_use`: Tune loop gain, timing, and damping.
- `forbidden_misuse`: Turning calibration into self-excusing recursion or unsafe feedback escalation.
- `next_step_effect`: Can shift to `watch`, `needs_repair`, or `archive` when loop control is the issue.
- `example_application`: Stop an overactive correction loop from amplifying itself.

### H. Information Theory / Compression Calibration
- `axis_id`: `information_theory_compression_calibration`
- `theory_family`: `information_theory`
- `calibrated_failure_mode`: `pattern_without_explanatory_gain`
- `calibration_question`: Does the explanation compress observations better than the raw pattern list?
- `safe_internal_use`: Test whether an explanation actually reduces complexity.
- `forbidden_misuse`: Claiming compression as truth or proof.
- `next_step_effect`: Pushes toward `calibrate`, `archive`, or `needs_repair` depending on explanatory gain.
- `example_application`: Reject a pattern that is memorable but not explanatory.

### I. Causal / Counterfactual Calibration
- `axis_id`: `causal_counterfactual_calibration`
- `theory_family`: `causal_inference`
- `calibrated_failure_mode`: `correlation_claimed_as_cause`
- `calibration_question`: What would change under a counterfactual intervention?
- `safe_internal_use`: Separate cause from co-occurrence.
- `forbidden_misuse`: Promoting causal claims without intervention logic.
- `next_step_effect`: Nudges toward `pressure_test` or `operator_review` when causality is unclear.
- `example_application`: Distinguish a correlated signal from an actual driver.

### J. Game Theory / Incentive Calibration
- `axis_id`: `game_theory_incentive_calibration`
- `theory_family`: `game_theory`
- `calibrated_failure_mode`: `belief_distorted_by_strategy_or_incentives`
- `calibration_question`: Is the observed behavior shaped by incentives rather than the underlying fact?
- `safe_internal_use`: Detect strategic distortion and adversarial pressure.
- `forbidden_misuse`: Assuming incentives are irrelevant or using game theory to justify manipulation.
- `next_step_effect`: Can move to `pressure_test`, `operator_review`, or `blocked_by_safety`.
- `example_application`: Treat a claim differently when the speaker benefits from distortion.

### K. Evolutionary Calibration
- `axis_id`: `evolutionary_calibration`
- `theory_family`: `evolutionary_selection`
- `calibrated_failure_mode`: `weak_candidates_never_evolve_or_never_die`
- `calibration_question`: Are variants being selected, retired, and improved at the right rate?
- `safe_internal_use`: Manage variation, selection, and pruning of candidates.
- `forbidden_misuse`: Turning evolution language into justification for unbounded churn or permanent retention.
- `next_step_effect`: Helps choose `watch`, `archive`, `pressure_test`, or `needs_repair`.
- `example_application`: Let weak candidates die while preserving promising variants.

### L. Topological / Structure-Preserving Calibration
- `axis_id`: `topological_structure_preserving_calibration`
- `theory_family`: `topology`
- `calibrated_failure_mode`: `fake_analogy`
- `calibration_question`: Does the cross-domain mapping preserve structure or merely sound similar?
- `safe_internal_use`: Test whether a metaphor keeps the right shape under transformation.
- `forbidden_misuse`: Treating analogy as evidence or proof.
- `next_step_effect`: Often moves to `pressure_test`, `needs_repair`, or `operator_review`.
- `example_application`: Reject a cross-domain mapping that breaks when simplified.

### M. Fibonacci / Nonlinear Escalation Schedule Calibration
- `axis_id`: `nonlinear_escalation_schedule_calibration`
- `theory_family`: `nonlinear_timing`
- `calibrated_failure_mode`: `flat_timing_or_infinite_wait`
- `calibration_question`: When should the system recheck, widen, escalate, or archive?
- `safe_internal_use`: Shape timing and escalation without dead loops or premature closure.
- `forbidden_misuse`: Using schedule theory to justify endless waiting or perpetual urgency.
- `next_step_effect`: Balances `probe`, `watch`, `archive`, `operator_review`, and `needs_repair`.
- `example_application`: Recheck at a controlled cadence instead of stalling forever.

## 5. How axes affect next-step labels
- `probe`: Use when the failure mode is still under-observation or the theory says the signal must be tested before stronger action.
- `pressure_test`: Use when the theory says candidate robustness, falsification, causal distinction, or adversarial survival is needed.
- `calibrate`: Use when the failure mode is confidence posture, update speed, or loop tuning—not when every problem is a calibration problem.
- `watch`: Use when evidence is thin, timing matters, or the right move is to wait for a stronger signal without overreacting.
- `archive`: Use when the item is stable, low-value, or already known and the theory does not justify more active work.
- `operator_review`: Use when authority, ambiguity, or policy constraints require human review.
- `blocked_by_safety`: Use when a theory-driven direction crosses into unsafe authority, public claims, or forbidden action.
- `needs_repair`: Use when the theory or metadata is malformed, contradictory, or non-JSON-safe.

## 6. Combined stack effect
A healthy theoretical calibration stack should prevent:
- everything becoming calibrate
- everything becoming discovery
- safe cognition being suppressed
- weak signals being overclaimed
- strong signals being archived too early
- metaphors becoming evidence
- correlation becoming cause
- untestable ideas being promoted
- loops continuing forever
- public authority appearing too early

## 7. Relationship to existing artifacts
- The comparative artifact proves differentiation exists at the bridge layer.
- Reverse calibration explains why differentiated steps are justified.
- Theoretical calibration axes explain what failure modes each calibration type catches.
- Future ingestion should use these axes before producing proposed directions.

## 8. Safety boundaries
Forbidden in this design:
- runtime wiring
- source ingestion
- provider/tool/web calls
- `.weslr` IO
- persistence
- memory/project mutation
- public claims
- final-answer authority
- benchmark/score/proof/AGI/public-science claims
- automatic discovery claims

## 9. Future validation requirements
A future helper must fail closed on:
- missing axis id
- missing theory family
- missing failure mode
- missing calibration question
- invalid next-step effect
- missing forbidden misuse
- unsafe authority flags
- public claim authorization
- final-answer authority
- provider/model/tool/retrieval/web implication
- source ingestion authorization
- runtime authorization
- `.weslr` implication
- `.weslr` read/write implication
- `.weslr` persistence/state implication
- persistence/database implication
- memory/project mutation implication
- hidden/private/protected markers
- non-JSON-safe output
