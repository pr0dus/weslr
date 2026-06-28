# WESLR ARC GENERATIVE BRIDGE V5 REPLAY EMITTER DECISION RULE ADDENDUM 2 V1

## 1. Executive verdict
`arc_generative_bridge_v5_replay_emitter_decision_rule_addendum_2_ready`

## 2. Purpose

Define how to choose generator repair vs assembler repair when candidates are generated but few become deserved.

## 3. Generator Repair Discriminator

Choose `REPAIR_ARC_CONTROLLED_ANSWER_CANDIDATE_GENERATOR_V1` if any dominate:

- Low `candidate_generated_count`
- High `candidate_generation_blocked_count`
- High `unsupported_assumption_blocked_count`
- High `unresolved_rival_blocked_count`
- High `ambiguous_correspondence_blocked_count`
- High `unforced_invariant_blocked_count`
- High `mdl_only_rejected_count`
- Low `construction_trace_complete_count`
- Missing candidate modes for groups that should have paths
- Candidates mostly partial descriptors
- Candidates lack train-supported source constraints

**Interpretation:** Generator is not producing ledger-reviewable, train-grounded candidates.

## 4. Assembler Repair Discriminator

Choose `REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1` if:

- `candidate_generated_count` adequate
- Construction traces complete
- Candidates require ledger review
- Candidates not final answers
- Source constraints train-supported
- Low unsupported assumptions
- Low unresolved rival blocks
- Low ambiguity blocks
- Generator produces structurally eligible candidates
- Assembler still rejects most as not deserved without clear cause

**Interpretation:** Generator produces plausible candidates, but assembler may be too strict or missing deservedness bridge.

## 5. Mixed-Signal Interpretation

Choose `ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1` if:
- Generator weakness and assembler strictness both appear
- Group-level behavior differs strongly
- Exact rate 0 but safety perfect
- No single dominant failure reason

## 6. Null-Result Interpretation

If `task_exact_count = 0` and safety clean:
- NOT success
- NOT regression
- Bridge replay inconclusive on solving
- Analyze missing bridge/failure modes

Do NOT call clean null result failure unless:
- Safety worsens
- Expected candidate coverage absent
- Implementation contradicts replay design

## 7. Middle-Band Definition

If neither the generator-repair discriminator nor assembler-repair discriminator clearly dominates, and no hard safety stop fires, this is the middle band:

- **Generator-health signals are moderate**, not clearly high (no dominant red flags)
- **Assembler-cleanliness signals are moderate**, not clearly clean (eligible candidates exist but rejection rate is neither very high nor very low)
- **Group behavior is consistent** rather than strongly divergent
- **No single discriminator dominates** the decision

**Middle-band recommended lane:** `ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1`

**Middle-band cannot recommend:**
- `DESIGN_ARC_SAFE_ANSWER_EMITTER_BOUNDARY_V1`
- Direct generator repair
- Direct assembler repair

**Middle-band interpretation:**
- A uniformly mediocre replay result is NOT emitter evidence
- It is NOT enough to choose generator repair or assembler repair directly
- It REQUIRES analysis before repair or emitter sequencing
- Preserves neutral/caution stance

**Label:** `no_dominant_discriminator_middle_band = True`

---

Generator repair discriminator: defined
Assembler repair discriminator: defined
Mixed-signal interpretation: defined
Middle-band definition: defined
Null-result interpretation: defined
Final judgment: arc_generative_bridge_v5_replay_emitter_decision_rule_addendum_2_ready