# WESLR ARC UNKNOWN ENGINE Level Ladder Design V1

## Status
Design/report only. No level-generator implementation, no solver behavior change, no primitive additions, no fill retry, no depth-3, no public ARC/Kaggle ingestion, no runtime wiring, no `.weslr` writes, and no public-score claim.

## 1. Game mechanism definition

UNKNOWN ENGINE is designed as a game-like ARC-style level ladder for independent synthetic transfer testing.

- player: the frozen ARC-style solver / current WESLR method
- level: one synthetic ARC-style task-family instance generated under bounded train-inferable rules
- win: exact solve under train-only evidence
- partial: near-solve with mismatch diagnosis preserved
- fail: unsupported, invalid, or no safe candidate
- level-up: increase abstraction pressure after repeated exact success
- strange-level unlock: introduce harder ambiguity, distractor pressure, or relation-shift pressure after stable success at the current tier
- stop condition: identify a stable failure frontier where the same pressure class keeps breaking the frozen solver without evidence that simple variation will restore exactness

The mechanism is intentionally not a second static held-out set. It is a controlled ladder that keeps asking: what kind of unknown would defeat the frozen solver next?

## 2. Short-horizon future-pressure idea

UNKNOWN ENGINE does not predict the future magically. It forecasts short-horizon failure modes by generating controlled synthetic pressure levels that are likely to expose the next weakness before any external evaluation does. The point is not prophecy. The point is to create bounded synthetic novelty that reveals the likely next break class, classify that break, and stop the solver from being patched mid-evaluation.

## 3. Hardness and strangeness axes

### Hardness axes
- composition depth
- abstraction distance
- distractor density
- ambiguity level
- relation dependency
- negative evidence dependency
- output-shape uncertainty
- object identity drift
- rule-switching pressure
- train/held-out variation distance
- misleading local regularity
- exception handling
- sparse evidence pressure
- cross-example consistency pressure

### Strangeness axes
- unfamiliar object-role remapping
- decoy regularity that looks easier than the real rule
- partial occlusion with recoverable identity
- local symmetry that conflicts with global relation logic
- causal feature vs incidental feature inversion
- rule-selection based on absence rather than presence
- output construction triggered by role semantics rather than direct color mimicry
- train-pair consistency that resolves ambiguity only across multiple examples

## 4. Level tiers

### Tier 0 — calibration / sanity levels
- what changes: only mild transfer from frozen solved patterns into nearby but not identical instances
- what stays train-inferable: all rules remain obvious from individual train pairs
- expected frozen-solver failure mode: very low failure rate; any failure suggests regression or packet hygiene issues
- level-up trigger: stable exact success across multiple seeds and minor variations
- stop trigger: unexpected invalid/unsupported or repeated exact collapse
- evidence recorded: exact/partial/unsupported/invalid, packet validity, mismatch categories, seed stability

### Tier 1 — transfer levels
- what changes: same broad reasoning ingredients, but different object placements, palettes, and relation layouts
- what stays train-inferable: the governing rule still appears directly in train examples
- expected frozen-solver failure mode: local overfitting to known layouts or incidental train cues
- level-up trigger: repeated exact success across family variants
- stop trigger: repeated partial with same mismatch category under small variations
- evidence recorded: per-family transfer hit rate, mismatch locality, overfit indicators

### Tier 2 — abstraction-pressure levels
- what changes: train evidence requires one more abstraction step, such as role identification, relation selection, or output-grammar choice
- what stays train-inferable: train pairs still contain enough evidence for a principled solver without hidden data
- expected frozen-solver failure mode: correct local transformation but wrong role binding or wrong output selection
- level-up trigger: stable exact plus low mismatch volatility under variations
- stop trigger: stable failure frontier around one abstraction class
- evidence recorded: abstraction class, chosen hypothesis family, first-failure frontier

### Tier 3 — strange-but-train-inferable levels
- what changes: introduce novelty that feels odd but is still justified by train-only evidence
- what stays train-inferable: ambiguity is resolvable through cross-example consistency, not hidden answers
- expected frozen-solver failure mode: solver locks onto the most familiar local cue and misses the stranger but correct global rule
- level-up trigger: solver demonstrates tolerance to novelty without unsupported spikes
- stop trigger: repeated partial/unsupported on one strangeness axis
- evidence recorded: novelty class, decoy influence, confidence-collapse signature

### Tier 4 — adversarial curriculum levels
- what changes: generate neighbor levels around observed partials and unsupported failures to probe robustness without patching
- what stays train-inferable: each adversarial level is still principled and reconstructible from train evidence
- expected frozen-solver failure mode: unstable success that collapses under tiny relation or distractor changes
- level-up trigger: stable success across adversarial neighbors
- stop trigger: overfit frontier detected or repeated mismatch category saturation
- evidence recorded: local variation map, collapse radius, first repeated failure frontier, neighbor sensitivity

### Tier 5 — frontier-probe levels
- what changes: maximize bounded novelty near the edge of what remains inferable, using multiple pressure axes at once
- what stays train-inferable: train evidence must still support one principled solution path
- expected frozen-solver failure mode: unsupported or structurally partial behavior concentrated in a new unknown class
- level-up trigger: none required; this tier is for locating the stable edge
- stop trigger: a reproducible failure frontier is established with sufficient evidence to recommend a new bounded design lane
- evidence recorded: frontier label, likely next missing mechanism, reproducibility, intervention recommendation

## 5. Independent level families

These families do not reuse or rename the prior frozen held-out families.

### 1. relation_selected_recolor
- hardness axis: relation dependency
- strangeness axis: role selection by inter-object relation
- intended abstraction: recolor only the object chosen by a relation rule
- why previous solver may fail: it may recolor the salient object, not the relationally correct object
- why it remains train-inferable: train pairs show which relation selects the transformed target
- leakage risks: family-name hints, object-count shortcuts
- generator constraints: at least two candidate objects; relation must be disambiguated in train pairs
- pass/fail metric: exact target selection and recolor
- how it can level up: add distractor objects with similar local features

### 2. distractor_consistency_selector
- hardness axis: cross-example consistency pressure
- strangeness axis: true target stays stable while distractors vary
- intended abstraction: choose the consistent target across train pairs
- why previous solver may fail: it may overfit the most visually prominent object in one pair
- why it remains train-inferable: only one object role stays causally stable across train examples
- leakage risks: task-id shortcut or fixed-position bias
- generator constraints: distractors must rotate across train examples while the target role remains consistent
- pass/fail metric: whether the selected object role is consistent and correct
- how it can level up: increase distractor density and visual similarity

### 3. negative_space_object_inference
- hardness axis: negative evidence dependency
- strangeness axis: output chosen by what is absent, not what is present
- intended abstraction: infer the missing or excluded object from surrounding constraints
- why previous solver may fail: it is biased toward positive-feature transformations
- why it remains train-inferable: train pairs reveal a repeated exclusion pattern
- leakage risks: hidden-output leakage through template shape
- generator constraints: absence signal must be uniquely recoverable from train examples
- pass/fail metric: correct inferred object and placement
- how it can level up: combine absence cue with distractor noise

### 4. decoy_pattern_suppression
- hardness axis: misleading local regularity
- strangeness axis: visually regular decoy competes with weaker true rule
- intended abstraction: suppress the decoy and preserve the causal pattern
- why previous solver may fail: it may optimize for the easiest local repetition
- why it remains train-inferable: train pairs show the decoy breaking while the causal pattern survives
- leakage risks: generator accidentally always makes one pattern larger
- generator constraints: decoy must be plausible but not dominant by a trivial heuristic
- pass/fail metric: retention of true pattern, suppression of decoy
- how it can level up: vary decoy strength while preserving train identifiability

### 5. corrupted_example_shape_grammar
- hardness axis: sparse evidence pressure
- strangeness axis: one train pair is corrupted but recoverable by consistency
- intended abstraction: infer the grammar from the consistent pairs and quarantine the corrupted one
- why previous solver may fail: it may average over the corrupted example or reject the family entirely
- why it remains train-inferable: the consistent train pairs outvote the corrupted one in a principled way
- leakage risks: hidden annotation of the corrupted pair
- generator constraints: corruption must be detectable via cross-example inconsistency only
- pass/fail metric: recovered grammar continuation
- how it can level up: weaken the corruption signal and increase grammar complexity

### 6. relational_color_binding
- hardness axis: abstraction distance
- strangeness axis: colors encode roles, not identities
- intended abstraction: bind output color to relation role rather than source object color
- why previous solver may fail: it may map literal colors instead of roles
- why it remains train-inferable: train pairs show color-role reassignment across different concrete palettes
- leakage risks: palette-order shortcuts
- generator constraints: role-color mapping must vary in surface form while staying semantically stable
- pass/fail metric: correct role-based color assignment
- how it can level up: introduce extra irrelevant colors

### 7. occluded_identity_preservation
- hardness axis: object identity drift
- strangeness axis: partial occlusion across train/held-out examples
- intended abstraction: preserve object identity through occlusion and recover the correct transform target
- why previous solver may fail: it may treat the occluded object as a new object
- why it remains train-inferable: train pairs show stable identity cues despite occlusion
- leakage risks: direct shape templates that expose the answer
- generator constraints: identity cues must be sufficient but not trivial
- pass/fail metric: transform the correct occluded identity
- how it can level up: vary occlusion position and distractor overlap

### 8. relation_driven_canvas_resize
- hardness axis: output-shape uncertainty
- strangeness axis: output size depends on a relation, not count alone
- intended abstraction: resize canvas according to a structural relation rule
- why previous solver may fail: it may bind output size to count or bounding box only
- why it remains train-inferable: train pairs show relation-conditioned size changes
- leakage risks: fixed-size leakage by family template
- generator constraints: count-only heuristics must fail on train pairs
- pass/fail metric: correct output dimensions and content placement
- how it can level up: combine resize with relation-based anchoring

### 9. context_switched_transform
- hardness axis: rule-switching pressure
- strangeness axis: local context selects one of two valid transforms
- intended abstraction: infer which transform branch is active from context markers
- why previous solver may fail: it may apply the dominant rule globally
- why it remains train-inferable: train pairs reveal both branches and the trigger feature
- leakage risks: one branch appearing only once without sufficient support
- generator constraints: both branches must be evidenced in train data
- pass/fail metric: correct branch selection and transform execution
- how it can level up: make trigger features subtler while still principled

### 10. exception_condition_symmetry
- hardness axis: exception handling
- strangeness axis: symmetry rule with one lawful exception
- intended abstraction: apply symmetry except for the object that meets the exception condition
- why previous solver may fail: it may enforce the symmetry universally
- why it remains train-inferable: train pairs show the same exception rule across different layouts
- leakage risks: exception tied to one fixed location only
- generator constraints: exception must be semantic, not positional accident
- pass/fail metric: correct symmetric transform with preserved exception
- how it can level up: vary exception manifestation across train pairs

### 11. rule_violation_targeting
- hardness axis: negative evidence dependency
- strangeness axis: transform only the object that breaks a latent rule
- intended abstraction: infer the shared rule and identify the violating object
- why previous solver may fail: it may transform all objects or the largest object
- why it remains train-inferable: train pairs reveal the valid pattern and the singled-out violator
- leakage risks: always choosing a unique color or size cue
- generator constraints: the violation must be structural, not reducible to a single surface feature
- pass/fail metric: isolate and transform only the violating object
- how it can level up: add multiple near-violations

### 12. constraint_ring_completion
- hardness axis: sparse evidence pressure
- strangeness axis: infer a missing object from surrounding relational constraints
- intended abstraction: reconstruct a missing role from neighborhood rules
- why previous solver may fail: it may copy visible objects without inferring the missing role
- why it remains train-inferable: train pairs reveal the neighborhood constraint pattern
- leakage risks: answer shape hardcoded by ring size
- generator constraints: surrounding constraints must identify one valid completion
- pass/fail metric: correct inferred completion object
- how it can level up: distort the ring while preserving the rule

### 13. role_map_not_color_map
- hardness axis: abstraction distance
- strangeness axis: object roles stay stable while literal colors permute
- intended abstraction: map semantic roles rather than colors or positions
- why previous solver may fail: it may preserve direct color correspondences
- why it remains train-inferable: train pairs permute colors while keeping role actions constant
- leakage risks: one role color accidentally constant across all pairs
- generator constraints: enforce color permutation across train examples
- pass/fail metric: correct role-action mapping under new palette
- how it can level up: add extra non-role objects with similar colors

### 14. ambiguity_resolved_by_pair_consistency
- hardness axis: ambiguity level
- strangeness axis: multiple candidate outputs exist locally, but only one is consistent across train pairs
- intended abstraction: resolve ambiguity by cross-example consistency instead of local preference
- why previous solver may fail: it may commit to the nearest local heuristic
- why it remains train-inferable: train pairs eliminate all but one globally consistent interpretation
- leakage risks: accidentally exposing the chosen candidate in packet metadata
- generator constraints: local ambiguity must be real, but train-level resolution must be unique
- pass/fail metric: globally consistent candidate chosen
- how it can level up: increase candidate similarity while preserving unique consistency

### 15. causal_feature_isolation
- hardness axis: misleading local regularity
- strangeness axis: incidental feature is stronger visually than the causal feature
- intended abstraction: separate causal feature from incidental feature
- why previous solver may fail: it may latch onto the visually dominant incidental feature
- why it remains train-inferable: train pairs vary incidental features while causal feature remains stable
- leakage risks: causal feature accidentally constant in an obvious location
- generator constraints: incidental features must vary enough to be rejected by a principled solver
- pass/fail metric: correct causal feature selection and transform
- how it can level up: make incidental features more coherent and tempting

## 6. Dynamic curriculum rule

UNKNOWN ENGINE chooses the next level using a bounded curriculum controller.

- if exact success repeats, increase strangeness within the same hardness neighborhood first
- if partial repeats, classify mismatch category and generate neighbor levels around that mismatch
- if unsupported appears, generate minimal repro levels that isolate the unsupported mechanism
- if invalid appears, generate boundary/validation diagnostics rather than harder levels
- if success collapses under small variation, mark an overfit frontier
- if performance stays stable across controlled variations, unlock the next tier

The ladder is not reward-maximizing. It is frontier-finding.

## 7. Failure forecasting output

UNKNOWN ENGINE should emit a bounded metadata report with at least:
- `forecast_run_id`
- `tier`
- `level_family_id`
- `pressure_axes`
- `frozen_solver_result` (`exact|partial|unsupported|invalid`)
- `likely_next_failure_family`
- `failure_cause`
- `evidence_from_played_levels`
- `confidence_level` (`low|medium|high`)
- `recommended_bounded_intervention`
- `recommendation_mode` (`freeze|continue_level_generation|open_new_design_lane`)
- `non_claim_safe`
- `synthetic_only`

## 8. Anti-cheat / anti-overfitting rules

Required:
- no solver-visible answer keys
- no held-out outputs in solver packet
- no family names as solver hints
- no direct task IDs as hints
- no public ARC/Kaggle examples
- no benchmark grids/solutions
- no hardcoded solution templates
- no generator tuned to make solver look good
- no generator tuned to unfairly make solver look bad
- train examples must contain enough evidence for a principled solver

Additional discipline:
- evaluation packets must preserve ambiguity honestly
- generator metadata used for scoring must remain outside solver-visible packets
- level family labels are for evaluator/reporting use only

## 9. Evaluation protocol

The frozen solver must play first, unchanged.

For every played level record:
- exact / partial / unsupported / invalid
- mismatch category
- per-tier success
- per-family success
- first failure frontier
- repeated failure frontier
- level-up path
- strangeness tolerance
- overfit indicators

Protocol:
1. select starting tier and family
2. generate bounded synthetic train/test level
3. run the frozen solver unchanged
4. classify outcome and mismatch
5. update ladder state
6. decide whether to vary, level up, or stop
7. produce a bounded forecast report

## 10. Public boundary

This is internal synthetic pressure testing, not public ARC performance, not official scoring, not Kaggle readiness, and not a benchmark result.

## 11. Recommended next lane

If this design is valid: `IMPLEMENT_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_GENERATOR_V1`

Fallback if the design is too broad: `NARROW_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_TO_TIERS_0_2_V1`

Not recommended from this design:
- solver patching before frozen baseline
- depth-3
- fill retry
- public ARC run
- Kaggle submission
- public score claim

## 12. Final judgment

`arc_unknown_engine_level_ladder_design_ready_for_review_and_generator_scoping`
