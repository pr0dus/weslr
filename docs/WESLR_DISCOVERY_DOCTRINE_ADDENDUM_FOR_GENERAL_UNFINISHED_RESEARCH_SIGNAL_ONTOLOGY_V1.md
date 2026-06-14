# WESLR Discovery Doctrine Addendum for General Unfinished Research Signal Ontology V1

**Date:** 2026-06-14
**Lane:** Addendum to `DESIGN_WESLR_RF_WIFI_FLOORPLAN_SOURCE_CLASS_AND_SCOUT_SIGNAL_HINT_REPAIR_V1` (which produced the prior design at `2e788030`).
**Worktree:** `/home/pr0/projects/weslr-run-first-live-searxng-sample-20260613`
**Branch:** `run-first-live-searxng-sample-20260613`
**HEAD at start:** `2e788030`
**Prior design artifact (extended, not replaced):** `docs/WESLR_GENERAL_UNFINISHED_RESEARCH_DIRECTION_SIGNAL_ONTOLOGY_AND_SCOUT_HINT_REPAIR_V1.md`
**Status:** **Addendum-only.** No code change. No implementation. No new true run. No live SearXNG. No web / provider / model call. No `.weslr` IO. No runtime / chat / UI / voice edit. No accepted evidence, no accepted candidate, no proposal payload, no final answer. No public-readiness, AGI, consciousness, sentience, proof, discovery, official benchmark, competition-winning, public-science, or product-readiness claim.

---

## 0. Why this addendum exists

The prior design (`2e788030`) is a **broad metadata-only signal ontology and scout-hint repair plan** for unfinished-research-direction detection. It is correct as far as it goes, but its title and its central "WiFi / RF / floor-plan true run" example may lead a reader to misread it as **"a fix for the WiFi sensing scope gap"** or **"an ordinary research search engine."**

The owner's intent (verbatim from this dispatch, §Owner intent) is broader:

> *"WESLR should become a governed discovery engine for unfinished possibilities. WESLR should search across research papers, technical reports, patents, standards, old projects, failed experiments, fringe claims, unsolved mathematics, unresolved theories, unknown communication systems, emerging languages, abandoned engineering paths, cross-domain analogies, and ideas that may have stopped because technology, sensors, compute, materials, economics, or domain overlap were not ready yet. WiFi/RF/floor-plan sensing is only a calibration case."*

This addendum therefore **articulates the deeper doctrine** that the prior design instantiates, and **extends** the prior design with **5 new discovery layers** the prior design did not cover. The addendum does not replace any section of the prior design; it is a **layered extension**. Where the prior design and the addendum overlap, the addendum is the stricter / broader reading.

The addendum is **design-only**. No implementation, no code change, no new true run, no live search. The implementation is a separate lane requiring its own owner authorization, and the second true run (per the owner's §5 below) is a separate lane that follows the implementation.

---

## 1. The doctrine: WESLR as a governed discovery engine for unfinished possibilities

WESLR is **not** an ordinary research search engine. An ordinary research search engine returns the most-cited papers, the most-recent results, or the most-popular answers to a question. That is **retrieval**.

WESLR is a **governed discovery engine for unfinished possibilities**. Its central object is **the unfinished, the dormant, the abandoned, the cross-domain, the technology-blocked, the measurement-gapped, the formal-unsolved, the anomaly, the contradiction, the replication-gap, the time-revisit-able, the domain-convergence-able, the workforce-impacting, the language-or-protocol-discoverable, and the fringe-or-extraordinary-claim** — surfaced as **metadata-only locator candidates** that an operator must review before any promotion.

The doctrine has 6 pillars:

1. **Metadata-only by construction.** WESLR never fetches, ingests, summarizes, paraphrases, embeds, hashes, or synthesizes source content. The boundary retains the 19-field per-row allow-list. The scout, integration, and candidate-preparation helpers retain only metadata. The doctrine's output is **a list of locator candidates** with structured fields, not **a narrative summary** of any source.

2. **Skeptical-by-default for extraordinary claims.** WESLR classifies fringe / edge / strange / not-yet-understood domains as `extraordinary_claim_signal` and routes them to `route_to_extraordinary_claim_quarantine`. Promotion is blocked. The operator must type `EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED` to override. The default summary uses `unknown / likely false / needs evidence` language. **WESLR inspects strange ideas without becoming gullible.**

3. **Operator-controlled promotion.** WESLR never elevates a locator to evidence, an accepted candidate, a proposal, or a final answer. Every packet in the chain is operator-review-required. The operator is the **only** promotion authority. Even if all eligibility rules pass, the operator must explicitly promote.

4. **Generalization over keyword overfitting.** WESLR's signal derivation is **per-domain-family-parameterized** via a registry. The WiFi / RF / floor-plan case is one entry in the registry, not the structure of the registry itself. Adding a new domain family is a registry update, not a code change.

5. **Safety-by-default for the 5 implementation points the owner preserved** (per §3 below).

6. **Discovery-doctrine-broad** for the 5 new layers the owner added in this dispatch (per §6–§10 below).

The doctrine is **non-claiming by construction**. WESLR does not claim discovery, proof, breakthrough, AGI, consciousness, sentience, public-readiness, product-readiness, or competitive result. WESLR surfaces **locator candidates** for the operator to review. The operator's review is the only place where a promotion, a public statement, or a downstream action originates.

---

## 2. Doctrinal scope: what WESLR is and is not

WESLR is:

- A **metadata-only locator engine** that surfaces unfinished / dormant / cross-domain / technology-blocked / measurement-gapped / formal-unsolved / anomaly / replication-gap / time-revisit-able / domain-convergence-able / workforce-impacting / language-protocol-discoverable / fringe-or-extraordinary-claim candidates.
- A **governed discovery engine** that classifies candidates skeptically, requires operator review, and refuses to promote without explicit authorization.
- A **registry-driven ontology** that generalizes across domain families and adds new domain families by registry update, not code change.
- A **safety-by-default classifier** that quarantines extraordinary claims and applies operator-review-confirmation tokens.

WESLR is **not**:

- An ordinary research search engine. (WESLR does not return most-cited, most-recent, or most-popular.)
- A discovery engine that produces truths, proofs, or breakthroughs. (WESLR does not produce truth.)
- A public claim engine. (WESLR does not produce public claims.)
- An autonomous promoter. (WESLR does not promote without the operator.)
- A general AGI, consciousness, sentience, or product-readiness claim. (WESLR explicitly disavows these.)
- A market hype generator. (WESLR's future-workforce-impact layer is a `future_workforce_impact_hypothesis`, not a market forecast.)
- A code change in this lane. (This is a design addendum, not implementation.)

---

## 3. The 5 prior implementation points the owner preserved

The owner's dispatch §"Keep these 5 implementation points from the prior assistant summary" preserves the prior design's 5 concrete implementation lanes. The addendum re-states them, with the deeper doctrine framing added:

1. **Registry layer** — domain families, signal families, source classes, evidence roles. The registry is a config file (e.g. `weslr/domain_family_registry_v1.json`), not a code change. Each entry has the shape in the prior design §5.3: `domain_family`, `synonyms`, `signal_family_detection_cues`, `source_class_keywords`, `open_access_domains`, `paywalled_domains`. The registry is the source of truth; the helpers read from it.

2. **Routing repair** — fix the per-row enum allow-list mismatch so metadata can pass safely through the route helper. The MLCF routing helper's `_validate_entry_fields` is extended to accept the full 16-value `evidence_role_guess` enum (per the prior design §7). This is the **central** fix from the prior design — it unblocks the chain for the WiFi / RF / floor-plan topic specifically and generalizes the allow-list to any future domain family.

3. **Scout signal repair** — detect unfinished / dormant / cross-domain / technology-blocked / anomaly / measurement-benchmark-gap / formal-unsolved / extraordinary-claim signals via the registry's per-domain-family `signal_family_detection_cues`. The scout's keyword-based signal derivation becomes **per-domain-family-parameterized**.

4. **Extraordinary-claim quarantine** — keep fringe claims visible but blocked and skeptical. The `extraordinary_claim_signal` family is a quarantine class. Promotion is blocked. The operator must type `EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED` to override. The default summary uses `unknown / likely false / needs evidence` language. **WESLR inspects strange ideas without becoming gullible.**

5. **Second true run** — test broad discovery behavior after the design/repair, not only WiFi. The second true run is on a different domain family (e.g. energy systems, materials, biology / medicine, mathematics, physics / quantum, AI / cognition, or language / communication). The run is the **calibration** of the new registry / routing / scout / extraordinary-claim-quarantine changes. The first true run (`aab12606`, WiFi / RF / floor-plan) was the calibration of the prior design. The second true run is the calibration of the addendum's broader doctrine.

These 5 points are **non-negotiable**. The addendum extends the design; it does not weaken the prior design's commitments.

---

## 4. Doctrinal invariants (preserved from the prior design, restated with the doctrine framing)

The prior design's invariants (per §22 Boundaries) are restated here with the doctrine framing:

- **Metadata-only** — no source content is fetched, ingested, summarized, paraphrased, or hashed. The boundary's 19-field per-row allow-list is the maximum retained content.
- **Loopback-only** — SearXNG is local-only (loopback). No non-loopback URL.
- **No provider / model call** — no LLM, no Ollama, no OpenAI, no Anthropic, no Gemini, no OpenRouter, no model provider, no simulated provider.
- **No `.weslr` IO** — no read, no write, no config-touch of `/home/pr0/.weslr/`.
- **No runtime / chat / UI / voice wiring** — no call to the omnichat contract-reply engine, the chat responder, the chat UI, the dialogue module, the main module, the LLM runtime, the protected chat backend on `:8092`, the public `weslr.de` site, the protected chat `chat.weslr.de`.
- **No public claims** — no public-readiness, AGI, consciousness, sentience, proof, discovery, official benchmark, competition-winning, or public-science claim.
- **No destructive operations** — no file delete, no worktree create/delete, no branch create/delete, no reset, no rebase, no merge, no stash, no force push, no destructive git operation.
- **No cron-fired / autonomous-fired** — no cron, no systemd timer, no heartbeat, no growth session, no morning session, no evening session, no autonomous run, no scheduled work, no outreach, no email pipeline, no social / business lane, no Telegram outbound, no public WebSocket.
- **Design-only in this lane** — no code change in this lane. The registry, the per-domain-family keyword bags, the per-source-class allow-list extension, the per-evidence-role enum allow-list extension in the MLCF routing helper, and the per-route allow-list extension in the candidate-preparation helper are all **implementation work**, deferred to a separate lane.

The doctrine framing is: **WESLR is a metadata-only locator engine. WESLR is not a knowledge engine, a discovery engine that produces truths, a public claim engine, an autonomous promoter, or a market hype generator.**

---

## 5. Doctrinal discovery layers (the 5 new layers the owner added in this dispatch)

The prior design's 8 signal families (§5.1) cover the **classic** unfinished-research-direction signals. The owner's 5 new layers add the **broader** discovery-doctrine signals. The addendum is a **layered extension** of the prior design; the 5 new layers are **additional**, not replacements.

The 5 new layers are:

- **§6 Fringe-edge science layer** (this addendum)
- **§7 Time-revisit layer** (this addendum)
- **§8 Domain-convergence layer** (this addendum)
- **§9 Future-work / job-transformation layer** (this addendum)
- **§10 Language/protocol discovery layer** (this addendum)

Each layer is described below with its detection cues, derived signal type (added to the closed enum from prior design §5.2), follow-up route (added to the closed enum from prior design §8), disconfirming-evidence class (added to the closed enum from prior design §17), extraordinary-claim flag, and example search-query patterns.

### 5.1 Closed-enum additions

The following enum values are added to the prior design's closed enums:

**Signal types** (added to the 8-value `signal_type` enum from prior design §5.2):

```
fringe_edge_science_signal
time_revisit_signal
domain_convergence_signal
future_workforce_impact_signal
language_protocol_discovery_signal
```

**Safety routes** (added to the 8-value `selected_route` enum from prior design §8):

```
route_to_fringe_edge_science_quarantine
route_to_time_revisit_source_selection
route_to_domain_convergence_scout
route_to_future_workforce_impact_hypothesis
route_to_language_protocol_discovery
```

**Disconfirming-evidence classes** (added to the 12-value enum from prior design §17):

```
physics_established_violation_check_required
fraud_scam_risk_check_required
capability_delta_verification_required
convergence_validation_required
workforce_impact_hypothesis_check_required
language_protocol_teachability_check_required
```

These 16 new enum values are **additive only**; no existing value is removed or changed. The closed-enum discipline (prior design §5.2, §8, §17) is preserved: any value outside the closed enum is rejected at the helper's request validator.

### 5.2 Marker conventions

The 5 new layers introduce 5 new `evidence_role_guess` markers (per the prior design §7's 16-value closed enum, which is now extended to 21 values):

```
fringe_edge_science_signal
time_revisit_signal
domain_convergence_signal
future_workforce_impact_signal
language_protocol_discovery_signal
```

The marker is set on the locator's `evidence_role_guess` field by the boundary's `_derive_evidence_role` when the locator's title / url / domain matches the registry's per-domain-family `signal_family_detection_cues` for the corresponding new signal type.

The marker is **not** an authority assertion. It is a **classification**. The locator is a candidate; the operator reviews it.

---

## 6. Fringe-edge science layer

WESLR may inspect fringe, edge, strange, or not-yet-understood domains, but must classify them skeptically.

### 6.1 Detection cues (per the registry)

The registry's `fringe_edge_science_signal` detection cues include (non-exhaustive, owner-extensible):

```
free energy
over-unity
water engine
reactionless drive
perpetual motion
cold fusion
anomalous material behavior
unconventional biological effect
unconventional cognitive effect
speculative physics
speculative quantum
speculative information
not-yet-understood
fringe
edge science
paradigm shift (in the rhetoric-of-claim sense, not the technical sense)
```

The detection cues are **per-domain-family**. The `physics_speculative` domain family has the `speculative physics / quantum / information` cues. The `materials_anomalous` domain family has the `anomalous material behavior` cues. The `biology_unconventional` domain family has the `unconventional biological effect` cues. The default `general` family has all of the above.

### 6.2 Derived signal type

`fringe_edge_science_signal`

### 6.3 Follow-up route

`route_to_fringe_edge_science_quarantine`

### 6.4 Disconfirming-evidence classes required

The candidate-preparation helper's `validate_request` requires the integration packet's `disconfirming_evidence_map` to include **all** of:

- `thermodynamics_check_required` (the first and second law of thermodynamics must not be violated)
- `energy_conservation_check_required` (energy must not be created or destroyed)
- `peer_replication_required` (independent lab must reproduce the result)
- `physics_established_violation_check_required` (the claim must be checked against the established physics of the day)
- `fraud_scam_risk_check_required` (the claim must be checked for fraud / scam / patent-noise risk)
- `legal_safety_check_required` (the claim must be checked for legal and safety implications, e.g. regulatory compliance for medical / energy / communications claims)
- `independent_measurement_required` (the claim must be checked against an independent measurement)

If any of these 7 disconfirming-evidence classes is missing, the request is rejected with `blocked_labels: ["fringe_edge_science_missing_disconfirming_check"]`.

### 6.5 Extraordinary-claim flag

`True` (always). The `fringe_edge_science_signal` family is treated as a **subclass** of the `extraordinary_claim_signal` family for the purpose of the extraordinary-claim classifier (§10 of the prior design, extended in this addendum). The 7 disconfirming-evidence classes in §6.4 are a **superset** of the 4 disconfirming-evidence classes in prior design §10 (`thermodynamics_check_required`, `energy_conservation_check_required`, `peer_replication_required`, `legal_safety_check_required`). The integration helper's `_route_analysis` prefers `route_to_extraordinary_claim_quarantine` for any packet that contains one or more `fringe_edge_science_signal` entries. The candidate-preparation helper's `validate_request` rejects `route_to_fringe_edge_claim_quarantine` (and `route_to_extraordinary_claim_quarantine`) with `blocked_labels: ["extraordinary_claim_route_not_eligible"]`.

### 6.6 Rules (per the owner's dispatch §6)

1. **Never treat as discovered truth.** The candidate-preparation helper's `validate_packet` rejects any packet whose `summary` / `review` / `notes` fields contain any of `we are agi`, `agi achieved`, `consciousness confirmed`, `sentience confirmed`, `publicly claimable`, `we prove`, `we discover`, `we have shown`, `we have proven`, `official conclusion`, `final answer`, `state-of-the-art`, `state of the art`, `benchmark-winning`, `competition-winning`, `best in class`, `paradigm shift` (in the rhetoric-of-claim sense), `solved theory`, `new physics`, `over-unity verified`, `free energy demonstrated`, `perpetual motion verified`, `reactionless drive verified`, `cold fusion reproduced`. The rejection is `blocked_labels: ["fringe_edge_science_claim_too_strong"]`.
2. **Route to fringe-edge science quarantine** (which is a stricter version of the prior design's `route_to_extraordinary_claim_quarantine`).
3. **Require thermodynamic, energy-conservation, replication, fraud / scam-risk, safety, and independent-measurement checks.** (See §6.4.)
4. **Preserve `unknown / likely false / needs evidence` language.** The candidate-preparation helper's `validate_packet` requires the produced packet to include `unknown`, `likely false`, `needs evidence`, or `unverified` in the `summary` / `review` / `notes` fields. If absent, the packet is rejected with `blocked_labels: ["fringe_edge_science_summary_language_too_strong"]`.
5. **Operator review required.** The candidate-preparation helper's `validate_request` requires `operator_review_required: True`. For `fringe_edge_science_signal` entries, the operator review must be **explicit** with the `EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED` token.

### 6.7 Default summary

The default summary for a `fringe_edge_science_signal` entry is:

```
unverified fringe-edge science claim; needs thermodynamic / energy-conservation /
peer-replication / physics-established-violation / fraud-scam-risk / legal-safety /
independent-measurement evidence; blocked from candidate preparation; operator review
required with EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED token; preserved as a known
fringe-edge candidate signal; not a public claim.
```

### 6.8 Example search queries (per-domain-family)

For the `physics_speculative` domain family, the registry includes (non-exhaustive):

```
fringe physics claim replication
over-unity device independent measurement
cold fusion independent reproduction
reactionless drive replication status
```

For the `materials_anomalous` domain family:

```
anomalous material behavior replication
unexplained material effect independent measurement
low-energy nuclear reaction replication
```

For the `biology_unconventional` domain family:

```
unconventional biological effect replication
unexplained cognitive effect independent measurement
homeopathy clinical trial replication
```

### 6.9 Examples

- *Locator:* `https://www.nature.com/articles/s41586-019-1234-5` — title: "Anomalous heat generation in a palladium-deuteride system under specific conditions". `evidence_role_guess: fringe_edge_science_signal`. Disposition: `route_to_fringe_edge_science_quarantine`. The integration packet is retained for the operator. The candidate-preparation packet is **not built**. The default summary uses `unknown / likely false / needs evidence` language.

- *Locator:* `https://www.sciencedirect.com/science/article/pii/S0038110120301234` — title: "Empirical evidence for a reactionless drive in a magnetic rotor configuration". `evidence_role_guess: fringe_edge_science_signal`. Disposition: same. The `physics_established_violation_check_required` is mandatory; the default summary flags the Newton's-third-law violation explicitly.

---

## 7. Time-revisit layer

WESLR should detect old ideas that may become newly testable because time changed the constraints.

### 7.1 Detection cues (per the registry)

The registry's `time_revisit_signal` detection cues include (non-exhaustive, owner-extensible):

```
abandoned because measurement was impossible
limited by sensors
limited by compute
limited by materials
limited by fabrication
limited by energy density
limited by data availability
limited by control systems
limited by simulation fidelity
may be revisitable with modern tools
modern sensors may enable re-measurement
modern compute may enable re-analysis
modern materials may enable re-fabrication
modern data availability may enable re-discovery
modern energy storage may enable re-experiment
modern control systems may enable re-implementation
modern simulation fidelity may enable re-modeling
economics changed
regulations changed
domain overlap later
```

The detection cues are **per-domain-family**. The `rf_sensing_indoor_propagation` family has the WiFi / RF / floor-plan case (the prior design's calibration case). The `physics_speculative` family has the `old theory not revisited with modern instrumentation` cue. The `materials_anomalous` family has the `abandoned because measurement was impossible` cue.

### 7.2 Derived signal type

`time_revisit_signal`

### 7.3 Marker

`revisit_due_to_changed_capability` (per the owner's dispatch §7)

### 7.4 Follow-up route

`route_to_time_revisit_source_selection`

### 7.5 Disconfirming-evidence classes required

The candidate-preparation helper's `validate_request` requires the integration packet's `disconfirming_evidence_map` to include:

- `modern_re_measurement_required` (the locator's "old" finding must be re-measured with modern tools)
- `capability_delta_verification_required` (the locator's claim that "modern X enables re-Y" must be verified — is modern X actually a quantitative change? is the re-Y actually a re-measurement of the original claim? is the original claim actually testable with modern X?)
- `recent_survey_required` (a recent survey of the field must be retrieved, but **not via WESLR**; the operator is responsible for retrieving recent surveys and pasting the URL into the integration packet's `recent_survey_url` field; WESLR does not fetch the survey itself)
- `operator_review_required`

If any of these 4 disconfirming-evidence classes is missing, the request is rejected with `blocked_labels: ["time_revisit_missing_disconfirming_check"]`.

### 7.6 Extraordinary-claim flag

`False` (default). The `time_revisit_signal` family is **not** extraordinary by default. **However**, if the locator's title / url / domain also matches any of the `fringe_edge_science_signal` detection cues, the locator is **also** classified as `fringe_edge_science_signal`, and the fringe-edge rules apply.

### 7.7 Rules (per the owner's dispatch §7)

1. **Detect the capability delta.** The integration packet's `time_revisit_packet.capability_delta` field is required to enumerate the specific capabilities that changed (e.g. "sensors improved: from 1-megapixel CCD to 100-megapixel CMOS"; "compute improved: from 1-TFLOP CPU to 1000-TFLOP GPU"; "materials improved: from bulk silicon to 7-nm FinFET"; etc.). The enum of capability classes is: `sensors`, `compute`, `materials`, `fabrication`, `energy_storage`, `energy_density`, `data_availability`, `control_systems`, `simulation_fidelity`, `economics`, `regulations`, `domain_overlap`.
2. **Detect the original constraint.** The integration packet's `time_revisit_packet.original_constraint` field is required to enumerate the specific constraint that blocked the original work (e.g. "measurement was impossible in 1995 because X"). The enum of constraint classes is: `measurement_impossible`, `compute_insufficient`, `materials_insufficient`, `fabrication_insufficient`, `energy_density_insufficient`, `data_unavailable`, `control_systems_insufficient`, `simulation_fidelity_insufficient`, `economics_blocked`, `regulations_blocked`, `domains_not_overlapping`.
3. **Match the capability delta to the original constraint.** The integration helper's `validate_packet` requires `capability_delta_class` to be a `supersedes(original_constraint_class)` relation. The registry's `time_revisit_signal_capability_supersession_map` defines the mapping. If no supersession relation exists, the locator is rejected as `time_revisit_supersession_not_established`.
4. **Require modern re-measurement.** The disconfirming-evidence class `modern_re_measurement_required` is mandatory. The operator must supply a `modern_re_measurement_plan` field in the integration packet, describing the specific re-measurement that would be performed. WESLR does not perform the re-measurement; the operator is responsible.
5. **No "the original was correct" claim.** The candidate-preparation helper's content-scan rule catches any of `the original was correct`, `was right all along`, `now confirmed`, `validated by modern tools`, `re-measured and confirmed`, `re-discovered`, `re-resurrected`, `now solved`, `now works`. **If any match, the request is rejected** with `blocked_labels: ["time_revisit_claim_too_strong"]`. The default summary uses `unknown / likely false / needs evidence / needs modern re-measurement` language.

### 7.8 Default summary

The default summary for a `time_revisit_signal` entry is:

```
time-revisit candidate; original work was constrained by {original_constraint_class};
modern capabilities in {capability_delta_class} may enable re-measurement; needs
capability-supersession verification; needs modern re-measurement plan; needs recent
survey; blocked from candidate preparation; operator review required; not a public
claim.
```

### 7.9 Example search queries (per-domain-family)

For the `rf_sensing_indoor_propagation` family, the prior design already includes the 3 WiFi / RF queries. The addendum adds (non-exhaustive):

```
multipath modeling 1990s abandoned revisited
old CSI technique modern WiFi sensors re-measurement
pre-2010 indoor propagation model modern re-validation
```

For the `physics_speculative` family:

```
old quantum gravity approach revisited modern instrumentation
abandoned unified field theory modern re-examination
pre-2000 string theory prediction modern re-test
```

For the `materials_anomalous` family:

```
old metallic glass plastic deformation revisited modern electron microscopy
abandoned high-temperature superconductor revisited modern re-fabrication
pre-2010 anomalous material behavior modern re-measurement
```

### 7.10 Examples

- *Locator:* `https://arxiv.org/abs/cond-mat/9501234` — title: "Limitations of pre-1995 multipath modeling in indoor environments". `evidence_role_guess: time_revisit_signal`. `capability_delta_class: sensors`, `original_constraint_class: measurement_impossible`. The integration helper's `validate_packet` requires `capability_delta_class` to supersede `original_constraint_class`. The supersession holds (modern WiFi sensors can resolve multipath components at 1-ns resolution; the 1995 model assumed 100-ns resolution). The locator is retained for the operator. The candidate-preparation packet is **not built** until the operator supplies a `modern_re_measurement_plan`.

- *Locator:* `https://www.sciencedirect.com/science/article/pii/S0921452618304567` — title: "Pre-2010 abandoned approach to high-temperature superconductivity: a retrospective". `evidence_role_guess: time_revisit_signal`. `capability_delta_class: fabrication`, `original_constraint_class: fabrication_insufficient`. The supersession holds (modern fabrication can produce samples that were impossible in 2005). The locator is retained. The candidate-preparation packet is **not built** until the operator supplies a `modern_re_measurement_plan`.

---

## 8. Domain-convergence layer

WESLR should look for cases where two or more domains can evolve into a new domain together.

### 8.1 Detection cues (per the registry)

The registry's `domain_convergence_signal` detection cues include (non-exhaustive, owner-extensible):

```
signal processing + biology
material scattering + indoor sensing
language protocols + AI cognition
mathematics + physics + computation
energy systems + control theory
neuroscience + communication systems
robotics + materials + sensing
cross-domain convergence
domain overlap later
domains that did not overlap before
new domain emerging from old domains
```

The detection cues are **per-domain-family-pair**. The registry has a separate `domain_convergence_pairs` section that enumerates the explicit pairs (e.g. `rf_sensing_indoor_propagation + materials_mechanics_soft_matter` is a recognized pair; the owner's calibration case is exactly this pair).

### 8.2 Derived signal type

`domain_convergence_signal`

### 8.3 Marker

`cross_domain_convergence_candidate` (per the owner's dispatch §8)

### 8.4 Follow-up route

`route_to_domain_convergence_scout`

### 8.5 Disconfirming-evidence classes required

The candidate-preparation helper's `validate_request` requires the integration packet's `disconfirming_evidence_map` to include:

- `cross_domain_validation_required` (the convergence must be validated in **both** domains independently)
- `convergence_validation_required` (the convergence must be validated at the **interface** between the two domains, e.g. by a third domain that already bridges them)
- `operator_review_required`

If any of these 3 disconfirming-evidence classes is missing, the request is rejected with `blocked_labels: ["domain_convergence_missing_disconfirming_check"]`.

### 8.6 Extraordinary-claim flag

`False` (default). The `domain_convergence_signal` family is **not** extraordinary by default. **However**, if the locator's title / url / domain also matches any of the `fringe_edge_science_signal` detection cues, the locator is **also** classified as `fringe_edge_science_signal`, and the fringe-edge rules apply.

### 8.7 Rules (per the owner's dispatch §8)

1. **Identify the two (or more) domains explicitly.** The integration packet's `domain_convergence_packet.domain_a` and `domain_a.class` and `domain_a.role` and `domain_b.class` and `domain_b.role` fields are required. The `domain_a.class` and `domain_b.class` are enum values from the closed `domain_family` enum (per the prior design §5.3). The `domain_a.role` and `domain_b.role` are enum values from the closed `domain_role` enum: `signaling_source`, `signaling_target`, `mathematical_bridge`, `experimental_bridge`, `computational_bridge`, `methodological_bridge`, `conceptual_bridge`. If any field is missing, the request is rejected.
2. **Identify the convergence mechanism.** The integration packet's `domain_convergence_packet.convergence_mechanism` field is required, with enum values: `shared_mathematical_structure`, `shared_experimental_technique`, `shared_computational_technique`, `shared_methodology`, `shared_phenomenon`, `shared_concept`, `shared_instrument`. The enum values are non-exhaustive; the registry can add more.
3. **Identify the convergence evidence.** The integration packet's `domain_convergence_packet.convergence_evidence` field is required, with a non-empty list of citation-class locators (each is a 19-field metadata-locator record from a separate SearXNG query, or a curated reference). The list must have at least 2 entries; if less than 2, the request is rejected with `blocked_labels: ["domain_convergence_insufficient_evidence"]`.
4. **Validate in both domains.** The disconfirming-evidence class `cross_domain_validation_required` is mandatory. The operator must supply a `cross_domain_validation_plan` field in the integration packet, describing the specific validation that would be performed in **both** domains. **WESLR does not perform the validation.** The operator is responsible.
5. **No "this works in another field" claim.** The candidate-preparation helper's content-scan rule catches any of `works in`, `applies to`, `transfers to`, `extends to`, `solves in another field`, `cross-domain magic`, `the X method solves Y in any field`. **If any match, the request is rejected** with `blocked_labels: ["domain_convergence_claim_too_strong"]`. The default summary uses `unknown / needs cross-domain validation / needs interface validation` language.

### 8.8 Default summary

The default summary for a `domain_convergence_signal` entry is:

```
cross-domain convergence candidate between {domain_a_class} and {domain_b_class};
convergence mechanism: {convergence_mechanism}; convergence evidence:
{convergence_evidence_count} citations; needs cross-domain validation in both
domains; needs interface validation; blocked from candidate preparation; operator
review required; not a public claim.
```

### 8.9 Example search queries (per-domain-family-pair)

For the `(rf_sensing_indoor_propagation, materials_mechanics_soft_matter)` pair, the prior design's calibration case is exactly this pair. The addendum adds (non-exhaustive):

```
material scattering multipath indoor sensing cross-domain convergence
electromagnetic acoustic analogy convergence
```

For the `(mathematics_foundations_unsolved, physics_quantum_foundations, computation_theory)` triple:

```
mathematics physics computation triple convergence
formal unsolved problem quantum interpretation
```

For the `(energy_systems_storage_conversion, control_theory_foundations)` pair:

```
energy storage control theory convergence
battery dynamics feedback control
```

### 8.10 Examples

- *Locator:* `https://arxiv.org/abs/2304.12345` — title: "Acoustic-electromagnetic analogy for indoor multipath modeling: a cross-domain convergence". `evidence_role_guess: domain_convergence_signal`. `domain_a.class: rf_sensing_indoor_propagation`, `domain_b.class: materials_mechanics_soft_matter`, `convergence_mechanism: shared_mathematical_structure`. The integration helper's `validate_packet` requires the convergence to be validated in both domains. The locator is retained for the operator. The candidate-preparation packet is **not built** until the operator supplies a `cross_domain_validation_plan` and at least 2 convergence-evidence citations.

---

## 9. Future-work / job-transformation layer

WESLR should track how candidate discoveries might change work. The owner expects WESLR to reason about:

- jobs that disappear
- jobs that appear
- new skills that become necessary
- new artifacts / tools that humans need
- new teaching modules
- future professions
- new forms of human-AI collaboration

### 9.1 Detection cues (per the registry)

The registry's `future_workforce_impact_signal` detection cues include (non-exhaustive, owner-extensible):

```
workforce impact
job transformation
job displacement
job creation
new skills required
new artifacts required
new teaching modules
future professions
human-AI collaboration
human-AI teaming
human-AI co-working
human-AI co-creation
labor market impact
```

The detection cues are **per-domain-family**. The `ai_cognition_unsupervised` family has the `human-AI collaboration` / `human-AI teaming` cues (this is the most likely domain for future-workforce-impact signals). The `language_communication_evolution` family has the `new teaching modules` / `new artifacts required` cues. The `energy_systems_storage_conversion` family has the `job displacement` / `job creation` cues.

### 9.2 Derived signal type

`future_workforce_impact_signal`

### 9.3 Marker

`future_workforce_impact_hypothesis` (per the owner's dispatch §9)

### 9.4 Follow-up route

`route_to_future_workforce_impact_hypothesis`

### 9.5 Disconfirming-evidence classes required

The candidate-preparation helper's `validate_request` requires the integration packet's `disconfirming_evidence_map` to include:

- `workforce_impact_hypothesis_check_required` (the hypothesis must be checked against established labor-economics research; the operator is responsible for retrieving labor-economics surveys and pasting the URL into the integration packet's `labor_economics_survey_url` field; WESLR does not fetch the survey itself)
- `operator_review_required`

If any of these 2 disconfirming-evidence classes is missing, the request is rejected with `blocked_labels: ["future_workforce_impact_missing_disconfirming_check"]`.

### 9.6 Extraordinary-claim flag

`False` (default). The `future_workforce_impact_signal` family is **not** extraordinary by default. **However**, if the locator's title / url / domain also matches any of the `fringe_edge_science_signal` detection cues (e.g. `ai will replace all humans` or `agi will end work`), the locator is **also** classified as `fringe_edge_science_signal`, and the fringe-edge rules apply.

### 9.7 Rules (per the owner's dispatch §9)

1. **Identify the affected job classes explicitly.** The integration packet's `future_workforce_packet.affected_job_classes` field is required, with a non-empty list of job-class entries. Each entry has `job_class` (e.g. `radiologist`, `translator`, `truck_driver`, `customer_service_representative`, `paralegal`, `software_engineer`, `data_analyst`, `researcher`, `teacher`, `nurse`, etc.), `direction` (enum: `disappears`, `appears`, `transforms`), and `evidence_strength` (enum: `weak_signal`, `moderate_signal`, `strong_signal`, `established_trend`).
2. **Identify the new skills, artifacts, teaching modules, professions, and collaboration modes explicitly.** The integration packet's `future_workforce_packet.new_skills` / `new_artifacts` / `new_teaching_modules` / `new_professions` / `new_collaboration_modes` fields are required, each with a non-empty list of entries. The enum values for each list are non-exhaustive; the registry can add more.
3. **Hypothesis, not forecast.** The candidate-preparation helper's content-scan rule catches any of `will replace`, `will eliminate`, `will create`, `will transform`, `forecast`, `predicts`, `inevitable`, `guaranteed`. **If any match, the request is rejected** with `blocked_labels: ["future_workforce_impact_forecast_too_strong"]`. The default summary uses `unknown / needs labor-economics survey / needs evidence` language.
4. **Not market hype.** The candidate-preparation helper's content-scan rule also catches `market opportunity`, `TAM`, `SAM`, `SOM`, `billion-dollar market`, `trillion-dollar market`, `disruptive`, `next big thing`, `gold rush`. **If any match, the request is rejected** with `blocked_labels: ["future_workforce_impact_market_hype"]`. The default summary is explicitly **a hypothesis, not a market forecast**.
5. **No AGI / consciousness / sentience claim.** The candidate-preparation helper's content-scan rule catches any of `agi will`, `consciousness will`, `sentience will`, `general intelligence will`, `human-level will`. **If any match, the request is rejected** with `blocked_labels: ["future_workforce_impact_agi_claim"]`. The default summary explicitly disavows these.

### 9.8 Default summary

The default summary for a `future_workforce_impact_signal` entry is:

```
future-workforce-impact hypothesis; affected job classes: {affected_job_classes};
new skills: {new_skills_count}; new artifacts: {new_artifacts_count}; new
teaching modules: {new_teaching_modules_count}; new professions:
{new_professions_count}; new collaboration modes: {new_collaboration_modes_count};
needs labor-economics survey; hypothesis, not forecast; not a market hype; not an
AGI / consciousness / sentience claim; blocked from candidate preparation; operator
review required; not a public claim.
```

### 9.9 Example search queries (per-domain-family)

For the `ai_cognition_unsupervised` family:

```
workforce impact AI replacement jobs
human-AI collaboration new professions
new skills required AI era teaching modules
```

For the `language_communication_evolution` family:

```
language AI translation jobs transformation
new teaching modules language AI
```

For the `energy_systems_storage_conversion` family:

```
energy storage workforce job displacement
battery technician new skills required
```

### 9.10 Examples

- *Locator:* `https://arxiv.org/abs/2305.67890` — title: "Workforce impact of AI-assisted radiology: a 2024 survey". `evidence_role_guess: future_workforce_impact_signal`. The integration packet's `affected_job_classes` is `[{"job_class": "radiologist", "direction": "transforms", "evidence_strength": "moderate_signal"}]`. The locator is retained for the operator. The candidate-preparation packet is **not built** until the operator supplies a `labor_economics_survey_url`. The default summary is a **hypothesis, not a forecast**.

- *Locator:* `https://www.nature.com/articles/s41586-024-12345-6` — title: "Human-AI teaming in scientific research: emerging collaboration patterns". `evidence_role_guess: future_workforce_impact_signal`. The integration packet's `new_collaboration_modes` is `["human-AI co-design", "human-AI co-experiment", "human-AI co-validation"]`. The locator is retained. The default summary uses hypothesis-language.

---

## 10. Language/protocol discovery layer

WESLR should discover and propose new teachable language/protocol structures. The owner's dispatch §10 was truncated, but the headline principle is clear: **WESLR should discover and propose new teachable language / protocol structures** for new domains or for new cross-domain interfaces.

The addendum's interpretation is conservative: **WESLR's language/protocol discovery layer is a metadata-only locator layer that surfaces candidate language/protocol structures, not a generative design engine**. WESLR does not generate new languages or protocols. WESLR surfaces existing-but-underused languages, protocols, or communication structures as candidates for the operator to review.

### 10.1 Detection cues (per the registry)

The registry's `language_protocol_discovery_signal` detection cues include (non-exhaustive, owner-extensible):

```
new language
new protocol
emerging language
emerging protocol
unknown communication system
machine-to-machine protocol
human-to-machine protocol
inter-domain protocol
cross-domain communication
teaching language
teaching protocol
onboarding protocol
specification language
domain-specific language
```

The detection cues are **per-domain-family**. The `ai_cognition_unsupervised` family has the `domain-specific language` / `machine-to-machine protocol` cues. The `language_communication_evolution` family has the `emerging language` / `teaching language` / `teaching protocol` cues. The `rf_sensing_indoor_propagation` family has the `inter-domain protocol` / `specification language` cues (e.g. IEEE 802.11, ITU-T, 3GPP specifications).

### 10.2 Derived signal type

`language_protocol_discovery_signal`

### 10.3 Follow-up route

`route_to_language_protocol_discovery`

### 10.4 Disconfirming-evidence classes required

The candidate-preparation helper's `validate_request` requires the integration packet's `disconfirming_evidence_map` to include:

- `language_protocol_teachability_check_required` (the candidate language/protocol must be checked for **teachability** — can a human or a machine learn it within a reasonable time? — and for **expressivity** — can it express the relevant concepts? — and for **interoperability** — does it interop with existing languages/protocols?)
- `operator_review_required`

If any of these 2 disconfirming-evidence classes is missing, the request is rejected with `blocked_labels: ["language_protocol_discovery_missing_disconfirming_check"]`.

### 10.5 Extraordinary-claim flag

`False` (default). The `language_protocol_discovery_signal` family is **not** extraordinary by default. **However**, if the locator's title / url / domain also matches any of the `fringe_edge_science_signal` detection cues (e.g. `universal language`, `universal protocol`, `unified communication`), the locator is **also** classified as `fringe_edge_science_signal`, and the fringe-edge rules apply.

### 10.6 Rules (per the owner's dispatch §10, conservative interpretation)

1. **Identify the candidate language/protocol explicitly.** The integration packet's `language_protocol_discovery_packet.candidate_language_protocol` field is required, with `name` (string), `version` (string, may be empty), `domain_family_class` (enum from the closed `domain_family` enum), `scope` (enum: `inter_machine`, `intra_machine`, `inter_human`, `intra_human`, `human_machine`, `inter_domain`, `intra_domain`).
2. **Identify the teachability evidence.** The integration packet's `language_protocol_discovery_packet.teachability_evidence` field is required, with a non-empty list of citation-class locators (each is a 19-field metadata-locator record from a separate SearXNG query, or a curated reference). The list must have at least 2 entries; if less than 2, the request is rejected with `blocked_labels: ["language_protocol_discovery_insufficient_teachability_evidence"]`.
3. **Identify the expressivity evidence.** The integration packet's `language_protocol_discovery_packet.expressivity_evidence` field is required, with a non-empty list of citation-class locators. The list must have at least 1 entry. **If empty, the request is rejected** with `blocked_labels: ["language_protocol_discovery_missing_expressivity_evidence"]`.
4. **Identify the interoperability evidence.** The integration packet's `language_protocol_discovery_packet.interoperability_evidence` field is required, with a non-empty list of citation-class locators. The list must have at least 1 entry. **If empty, the request is rejected** with `blocked_labels: ["language_protocol_discovery_missing_interoperability_evidence"]`.
5. **No "universal language" or "universal protocol" claim.** The candidate-preparation helper's content-scan rule catches any of `universal language`, `universal protocol`, `unified communication`, `one language to rule them all`, `language-of-the-future`, `protocol-of-the-future`. **If any match, the request is rejected** with `blocked_labels: ["language_protocol_discovery_universal_claim"]`. The default summary uses `unknown / needs teachability check / needs expressivity check / needs interoperability check` language.
6. **No "WESLR generates languages/protocols" claim.** WESLR is a **locator engine**, not a **generative design engine**. WESLR does not produce new languages or protocols. WESLR surfaces existing-but-underused candidates. The candidate-preparation helper's content-scan rule catches any of `WESLR designs`, `WESLR generates`, `WESLR creates`, `WESLR invents`, `WESLR produces`. **If any match, the request is rejected** with `blocked_labels: ["language_protocol_discovery_generative_claim"]`.

### 10.7 Default summary

The default summary for a `language_protocol_discovery_signal` entry is:

```
language / protocol discovery candidate; candidate: {candidate_name} (version
{version}, domain {domain_family_class}, scope {scope}); teachability evidence:
{teachability_evidence_count} citations; expressivity evidence:
{expressivity_evidence_count} citations; interoperability evidence:
{interoperability_evidence_count} citations; needs teachability check, expressivity
check, interoperability check; not a universal language / universal protocol claim;
not a WESLR-generates-languages claim; blocked from candidate preparation;
operator review required; not a public claim.
```

### 10.8 Example search queries (per-domain-family)

For the `ai_cognition_unsupervised` family:

```
domain-specific language AI reasoning
machine-to-machine protocol autonomous agents
specification language neural network architecture
```

For the `language_communication_evolution` family:

```
emerging language documentation teachability
teaching protocol onboarding effectiveness
```

For the `rf_sensing_indoor_propagation` family:

```
IEEE 802.11 specification language
3GPP protocol expressivity teachability
ITU-T recommendation interoperability
```

### 10.9 Examples

- *Locator:* `https://www.ieee.org/standard/802_11-2020.html` — title: "IEEE Standard for Information technology — Telecommunications and information exchange between systems — Local and metropolitan area networks — Specific requirements; Part 11: Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications". `evidence_role_guess: language_protocol_discovery_signal`. `candidate_language_protocol.name: "IEEE 802.11"`, `version: "2020"`, `domain_family_class: rf_sensing_indoor_propagation`, `scope: inter_machine`. The integration helper's `validate_packet` requires teachability / expressivity / interoperability evidence. The locator is retained for the operator. The candidate-preparation packet is **not built** until the operator supplies the evidence.

- *Locator:* `https://www.w3.org/TR/2024/REC-rdf12-concepts-20240206/` — title: "RDF 1.2 Concepts and Abstract Syntax". `evidence_role_guess: language_protocol_discovery_signal`. `candidate_language_protocol.name: "RDF 1.2"`, `version: "2024-02-06"`, `domain_family_class: language_communication_evolution`, `scope: inter_machine`. The locator is retained.

### 10.10 Note on the conservative interpretation

The owner's dispatch §10 was truncated at "This includes:" and did not give the full list of rules or examples. The addendum's interpretation is **conservative**: WESLR surfaces existing-but-underused languages and protocols as locator candidates; WESLR does not generate new ones; WESLR does not claim universality; WESLR does not become a language/protocol design engine. The owner can extend the addendum with additional rules in a follow-up addendum if the conservative interpretation is too narrow.

---

## 11. Doctrinal invariants (addendum-specific, additive to §4)

The addendum preserves all 9 invariants from §4 and adds 3 more:

- **Metadata-only** (preserved from prior design) — no source content fetch / ingest / summary / hash.
- **Loopback-only** (preserved) — SearXNG is local-only.
- **No provider / model call** (preserved) — no LLM, no Ollama, no OpenAI, no Anthropic, no Gemini, no OpenRouter, no model provider, no simulated provider.
- **No `.weslr` IO** (preserved) — no read, no write, no config-touch of `/home/pr0/.weslr/`.
- **No runtime / chat / UI / voice wiring** (preserved) — no omnichat, no chat responder, no chat UI, no dialogue, no main, no LLM runtime, no protected chat backend on `:8092`, no public `weslr.de` site, no protected chat `chat.weslr.de`.
- **No public claims** (preserved) — no public-readiness, AGI, consciousness, sentience, proof, discovery, official benchmark, competition-winning, or public-science claim.
- **No destructive operations** (preserved) — no file delete, no worktree create/delete, no branch create/delete, no reset, no rebase, no merge, no stash, no force push.
- **No cron-fired / autonomous-fired** (preserved) — no cron, no systemd timer, no heartbeat, no growth session, no morning session, no evening session, no autonomous run, no scheduled work, no outreach, no email pipeline, no social / business lane, no Telegram outbound, no public WebSocket.
- **Design-only in this lane** (preserved) — no code change in this lane. The addendum is a design artifact, not an implementation.

**Addendum-specific invariants (3 new):**

- **No market hype** — the future-workforce-impact layer is a `future_workforce_impact_hypothesis`, not a market forecast. Any of `market opportunity`, `TAM`, `SAM`, `SOM`, `billion-dollar market`, `trillion-dollar market`, `disruptive`, `next big thing`, `gold rush` causes immediate rejection (§9.7 rule 4).
- **No universal language / universal protocol claim** — the language-protocol-discovery layer is a locator layer, not a generative design engine. Any of `universal language`, `universal protocol`, `unified communication`, `one language to rule them all`, `language-of-the-future`, `protocol-of-the-future` causes immediate rejection (§10.6 rule 5).
- **No WESLR-generates-languages / WESLR-generates-protocols claim** — WESLR is a **locator engine**, not a **generative design engine**. Any of `WESLR designs`, `WESLR generates`, `WESLR creates`, `WESLR invents`, `WESLR produces` causes immediate rejection (§10.6 rule 6).

The 3 new invariants are **strict additive** to the 9 preserved invariants. Together they form the doctrine's **12 invariants**.

---

## 12. Doctrinal non-claims (addendum-specific, additive to prior design §21)

The addendum's explicit non-claims, additive to the prior design's 13 explicit non-claims:

14. WESLR is a **discovery engine for unfinished possibilities** in the sense of a **metadata-only locator engine for operator review**, not in the sense of a **knowledge engine that produces truths**. WESLR does not claim to discover, prove, or solve anything. WESLR surfaces **locator candidates** for the operator to review.

15. WESLR is **not an ordinary research search engine**. WESLR does not return most-cited, most-recent, or most-popular. WESLR surfaces unfinished / dormant / cross-domain / technology-blocked / measurement-gapped / formal-unsolved / anomaly / replication-gap / time-revisit-able / domain-convergence-able / workforce-impacting / language-protocol-discoverable / fringe-or-extraordinary-claim candidates — the **opposite** of the most-cited, most-recent, or most-popular.

16. WESLR is **not a market hype generator**. The future-workforce-impact layer is a `future_workforce_impact_hypothesis`, not a market forecast. WESLR does not produce TAM, SAM, SOM, billion-dollar-market, trillion-dollar-market, disruptive, next-big-thing, or gold-rush claims.

17. WESLR is **not a language / protocol design engine**. WESLR surfaces existing-but-underused languages and protocols as locator candidates. WESLR does not generate new languages or protocols. WESLR does not claim universality of any language or protocol.

18. WESLR is **not a fringe-claim verifier**. WESLR classifies fringe / edge / strange / not-yet-understood domains as `extraordinary_claim_signal` and routes them to `route_to_fringe_edge_science_quarantine`. WESLR does not verify, validate, or confirm fringe claims. WESLR inspects strange ideas without becoming gullible.

19. WESLR is **not a job-loss forecaster**. WESLR's future-workforce-impact layer is a hypothesis, not a forecast. WESLR does not predict which jobs will disappear, which jobs will appear, or when. WESLR surfaces hypotheses for the operator to review.

20. WESLR is **not a workforce re-skilling engine**. WESLR surfaces new-skills, new-artifacts, new-teaching-modules, new-professions, and new-collaboration-modes hypotheses for the operator to review. WESLR does not design re-skilling curricula, design teaching modules, or design artifacts. WESLR surfaces hypotheses.

21. WESLR is **not a domain-convergence engine**. WESLR surfaces cross-domain convergence candidates for the operator to review. WESLR does not perform cross-domain validation, cross-domain translation, or cross-domain bridging. WESLR surfaces candidates.

22. WESLR is **not a time-revisit engine**. WESLR surfaces time-revisit candidates for the operator to review. WESLR does not perform modern re-measurement, modern re-fabrication, or modern re-analysis. WESLR surfaces candidates.

23. WESLR is **not a universal-solver engine**. WESLR's discovery-doctrine is **metadata-only**, **operator-review-required**, **safety-by-default**, **skeptical-by-default**, and **non-claiming**. WESLR does not solve millennium-prize problems, prove open theorems, verify P ≠ NP, solve the quantum measurement problem, or produce any other universal-truth claim.

The addendum's explicit non-claims are **strict additive** to the prior design's 13 explicit non-claims. Together they form the doctrine's **23 explicit non-claims**.

---

## 13. Doctrinal operator-review requirements (addendum-specific)

The operator-review requirements are preserved from the prior design §18, with 2 addendum-specific additions:

- The operator's review of an `extraordinary_claim_signal` entry requires the `EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED` token (§10 of prior design).
- **The operator's review of a `fringe_edge_science_signal` entry requires the same `EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED` token**, because the `fringe_edge_science_signal` family is a subclass of the `extraordinary_claim_signal` family for the purpose of the operator-review-confirmation-token mechanism (§6.5 of this addendum).
- **The operator's review of a `future_workforce_impact_signal` entry requires a `FUTURE_WORKFORCE_IMPACT_HYPOTHESIS_CONFIRMED` token** — a new token specific to the future-workforce-impact layer. The candidate-preparation helper's `validate_request` checks the token is present and correct for any packet that contains one or more `future_workforce_impact_signal` entries. **If the token is missing or wrong, the request is rejected** with `blocked_labels: ["future_workforce_impact_hypothesis_not_confirmed"]**. The default token value is `FUTURE_WORKFORCE_IMPACT_HYPOTHESIS_CONFIRMED` (case-sensitive). The operator may type any non-empty string for the token, but the string must match the expected token exactly. **This is the design's principal defense against operator-fatigue mistakes on future-workforce-impact claims.**

- **The operator's review of a `language_protocol_discovery_signal` entry requires a `LANGUAGE_PROTOCOL_DISCOVERY_CONFIRMED` token**. The candidate-preparation helper's `validate_request` checks the token is present and correct. **If missing or wrong, the request is rejected** with `blocked_labels: ["language_protocol_discovery_not_confirmed"]**.

- **The operator's review of `time_revisit_signal` and `domain_convergence_signal` entries does not require a specific token** beyond the default `operator_review_required: True`. These layers are not extraordinary by default, and the operator's review is the standard operator-review (inspect the packet, write a new search query, write a new design, or override the safety verdict with a documented operator-side action). The standard operator-review is sufficient.

The 3 new tokens (`EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED`, `FUTURE_WORKFORCE_IMPACT_HYPOTHESIS_CONFIRMED`, `LANGUAGE_PROTOCOL_DISCOVERY_CONFIRMED`) are **additive** to the prior design's operator-review mechanism. The prior design's standard `operator_review_required: True` mechanism is preserved and is the **default** for all packets.

---

## 14. Doctrinal validation plan (addendum-specific)

The addendum's claims are validated by the same 8-command validation suite the prior design ran:

1. `git diff --check` — exit 0
2. `python3 weslr/tests/release_gate_v1.py` — `WESLR_RELEASE_GATE_V1_OK` (after the gate edit for the addendum doc)
3. `bash scripts/weslr_release_check.sh` — `WESLR_RELEASE_CHECK_OK` + `SELF_TEST: PASS`
4. The 4 pytest invocations (boundary, scout, integration, candidate-preparation) — **151 tests pass** (unchanged from the prior design, since the addendum does not implement code)
5. The 4 protected files (md5 byte-identical to `origin/master`)

The addendum's **claims** are validated by the implementation lane (separate), not by this lane. The implementation lane will:

- Run a true run on a non-WiFi domain family (e.g. energy systems, biology / medicine, or mathematics) to verify the registry-driven approach generalizes.
- Verify the 5 new layers' detection cues, follow-up routes, disconfirming-evidence classes, and operator-review-confirmation tokens work end-to-end.
- Verify the 5 new signal types are correctly emitted by the boundary, correctly routed by the integration helper, and correctly rejected (or accepted) by the candidate-preparation helper.
- Verify the 3 new safety routes (`route_to_fringe_edge_science_quarantine`, `route_to_time_revisit_source_selection`, `route_to_domain_convergence_scout`, `route_to_future_workforce_impact_hypothesis`, `route_to_language_protocol_discovery`) are correctly integrated into the chain.
- Verify the 3 new operator-review-confirmation tokens are correctly required by the candidate-preparation helper.
- Verify the doctrine's 12 invariants and 23 explicit non-claims are all preserved in the implementation.

---

## 15. Doctrinal next-recommended-lane

The next recommended lane is **`REVIEW_WESLR_DISCOVERY_DOCTRINE_ADDENDUM_FOR_GENERAL_UNFINISHED_RESEARCH_SIGNAL_ONTOLOGY_V1`** (the owner can rename if desired). The owner reviews this addendum, then decides whether to:

- Authorize the **implementation lane** (separate) that creates the domain-family registry, the 5 new layer detection cues, the 5 new safety routes, the 6 new disconfirming-evidence classes, the 3 new operator-review-confirmation tokens, and the 5 new signal types. The implementation is a non-trivial change to 4 helper modules (boundary, MLCF routing, integration, candidate-preparation) and the introduction of a new config file (the registry). It should be a single coordinated lane or a small set of well-scoped sub-lanes, each with its own owner authorization.

- Authorize the **second true run** (per the owner's §5 prior implementation point). The second true run is on a non-WiFi domain family (e.g. energy systems, materials, biology / medicine, mathematics, physics / quantum, AI / cognition, or language / communication) to verify the registry-driven approach generalizes. The second true run is a separate lane that follows the implementation.

- Or choose to **not authorize** the implementation, in which case the next lane is `PUSH_WESLR_RF_WIFI_FLOORPLAN_DESIGN_AND_REVIEW_AND_ADDENDUM_BRANCH_TO_GITHUB` — a no-op push of the current branch to the remote for archival review. The owner did not authorize pushing in the current dispatch; this is offered as a possible next-lane option, not a recommendation to push without authorization.

---

## 16. Final judgment

**`general_unfinished_research_signal_ontology_design_ready_for_review`**

The addendum does not change the prior design's final judgment. The addendum is a **layered extension** of the prior design; the prior design is still ready for review, and the addendum is also ready for review. The combined design (prior design + addendum) is the doctrine: **WESLR as a governed discovery engine for unfinished possibilities**.

Reasoning:
- The addendum is **general** (5 new layers generalizing across 8 example domains, not overfit to WiFi sensing).
- The addendum is **metadata-only** (no source content fetch / ingest / summary / hash; the boundary's 19-field per-row allow-list is the maximum retained content).
- The addendum is **safe-by-default** (every packet is operator-review-required; the candidate-preparation helper's `validate_request` enforces 8 eligibility rules + 5 extraordinary-claim rules + 3 addendum-specific token requirements; the chain's 6 + 5 = 11 routes other than `route_to_candidate_preparation` are blocked from candidate-preparation).
- The addendum is **skeptical-by-default for extraordinary claims** (the `fringe_edge_science_signal` family is a subclass of `extraordinary_claim_signal`; the operator must type `EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED` to override; the default summary uses `unknown / likely false / needs evidence` language).
- The addendum is **non-claiming** (no AGI, no consciousness, no sentience, no discovery, no proof, no solved-theory, no official benchmark, no competition-winning, no public-science, no product-readiness, no market hype, no universal language / protocol claim, no WESLR-generates-languages / protocols claim; the addendum explicitly enumerates 10 new non-claims, additive to the prior design's 13, for 23 total).
- The addendum is **non-implementing** (this is a design addendum, not an implementation; no code change in this lane).
- The addendum preserves all 9 invariants from the prior design and adds 3 new invariants (no market hype, no universal language / protocol claim, no WESLR-generates-languages / protocols claim), for 12 total.
- The addendum preserves all 5 prior implementation points (registry layer, routing repair, scout signal repair, extraordinary-claim quarantine, second true run) and adds 5 new layers (fringe-edge science, time-revisit, domain-convergence, future-workforce-impact, language-protocol discovery), for 10 total.
- The addendum honors all the owner's pre-conditions: no implementation, no new true run, no live SearXNG, no web / provider / model call, no `.weslr` IO, no runtime / chat / UI / voice edit, no accepted evidence, no accepted candidate, no proposal payload, no final answer.
- The addendum is **complete** (16 sections, all 5 new layers addressed with detection cues, derived signal type, follow-up route, disconfirming-evidence classes, extraordinary-claim flag, rules, default summary, example search queries, and examples; 3 addendum-specific invariants; 10 addendum-specific non-claims; 3 new operator-review-confirmation tokens; validation plan; next recommended lane; final judgment).
- The addendum's pre-conditions are met: preflight passed (repo root, branch, HEAD, 0 modified tracked files, no in-progress merge/rebase/cherry-pick), 4 protected files are byte-identical to `origin/master`, `weslr/main.py` is N/A.
- The addendum's validation is the same 8-command suite the prior design passed: py_compile exit 0, 4 pytest invocations (151 tests passed), git diff --check exit 0, release_gate OK, weslr_release_check OK + SELF_TEST PASS.

The design + addendum is ready for the owner's review. Implementation is a separate lane.
