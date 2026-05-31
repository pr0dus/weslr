# WESLR Broad Topic Ontology Layer V1

## SECTION 1 — Executive canon

WESLR must not rely on a finite hand-written list of domains to support broad owner research conversation.

Instead, WESLR should classify topics through a layered ontology:
- meta-domain
- domain family
- subdomain traits
- intent
- novelty
- evidence need
- risk posture
- response route
- behavior-pack candidate

This does not create AGI readiness.
This does not create public chat readiness.
This does not remove boundaries.
It strengthens generalization and reduces brittle domain enumeration.

## SECTION 2 — Current flat domain limitation

Current intake in `weslr/broad_topic_domain_intake.py` is useful, but the domain set is still mostly flat:
- `technical_research`
- `privacy_sensitive_technology`
- `industrial_automation`
- `legal_privacy`
- `materials_discovery`
- `energy_systems`
- `robotics`
- `software_product`
- `website_public_launch`
- `language_vocabulary`
- `owner_workflow`
- `unknown_domain`

Why this is not enough:
- it misses philosophy, theory of mind, cognitive science, AI subfields, psychology, neuroscience
- it misses life sciences, medicine, social sciences, economics, education, and security
- new domains will always appear
- `unknown_domain` is safe, but weak
- future domains like metamaterials or new sensing technologies need trait-based classification, not endless list growth

So the problem is not just “more domains.” The problem is “better axes.”

## SECTION 3 — Proposed layered ontology model

Use these fields together:

1. `meta_domain`
2. `domain_family`
3. `subdomain_traits`
4. `object_of_study`
5. `owner_intent`
6. `novelty_level`
7. `evidence_class`
8. `risk_class`
9. `sensitivity_class`
10. `response_route_family`
11. `behavior_pack_candidate_labels`

Design rule:
- meta-domain gives the top-level conceptual bucket
- domain family gives the working classification
- traits describe how the topic behaves
- object-of-study says what the topic is about
- intent says why the owner asked
- novelty says how likely current knowledge is to be incomplete
- evidence class says what support is needed before stronger claims
- risk/sensitivity say what boundary posture is required
- response route says how WESLR should respond
- candidate labels say what improvement lane it should seed

## SECTION 4 — Meta-domain families

### `mind_intelligence_consciousness`
Covers: cognition, reasoning, agency, consciousness, theory of mind, psychology, neuroscience, philosophy of mind.
- Evidence needs: conceptual definitions, literature, careful boundary review
- Likely risks: overclaiming, anthropomorphism, public claim sensitivity
- Possible behavior packs: cognition, unknown-term discovery, answer-shape, research planning

### `technical_engineering`
Covers: software, hardware, systems, networks, sensing, devices, automation, architecture.
- Evidence needs: technical literature, implementation constraints, validation
- Likely risks: safety, abuse potential, deployment mistakes
- Possible behavior packs: prototype planning, boundary, evidence mapping, domain research

### `physical_sciences`
Covers: physics, chemistry, materials, metamaterials, signals, waves.
- Evidence needs: technical literature, experimental validation
- Likely risks: high uncertainty, frontier claims, lab-dependence
- Possible behavior packs: research planning, evidence mapper, prototype-path planning

### `life_health`
Covers: biology, medicine, health research, care workflows, clinical-adjacent topics.
- Evidence needs: clinical validation, safety validation, regulatory sources
- Likely risks: medical claim sensitivity, harm risk, regulated-domain constraints
- Possible behavior packs: health boundary, evidence mapper, claim restraint

### `society_law_governance`
Covers: law, privacy, policy, regulation, institutions, social systems.
- Evidence needs: legal/regulatory sources, policy sources, context-specific review
- Likely risks: legal sensitivity, privacy sensitivity, public claim sensitivity
- Possible behavior packs: privacy boundary, governance review, policy research

### `formal_reasoning`
Covers: math, logic, proof, systems of inference, formal analysis.
- Evidence needs: definitions, formal structure, proof obligations
- Likely risks: false certainty, incorrect abstraction, hidden assumptions
- Possible behavior packs: reasoning guidance, evidence mapping, clarification

### `product_business`
Covers: product strategy, market fit, launch, pricing, operations, workflow.
- Evidence needs: market validation, user context, product constraints
- Likely risks: public launch claims, business overreach, strategy hallucination
- Possible behavior packs: owner workflow, product planning, launch review

### `language_communication`
Covers: wording, meaning, vocabulary, teaching, translation, discourse.
- Evidence needs: conceptual definitions, user context, examples
- Likely risks: ambiguity, tone mismatch, overgeneralization
- Possible behavior packs: language discovery, response-shape, teaching pack

### `creative_culture`
Covers: design, art, writing, media, storytelling, culture.
- Evidence needs: preference context, examples, audience fit
- Likely risks: style mismatch, tone mismatch, originality claims
- Possible behavior packs: creative response-shape, reusable-response guidance

### `security_safety`
Covers: misuse, defense, abuse resistance, operational risk, threat analysis.
- Evidence needs: safety validation, abuse modeling, boundary review
- Likely risks: dual use, harmful instructions, escalation
- Possible behavior packs: safety boundary, refusal, risk review

### `environment_energy`
Covers: energy systems, climate, power, grid, sustainability, environment.
- Evidence needs: technical literature, systems constraints, validation
- Likely risks: deployment safety, policy sensitivity, public claims
- Possible behavior packs: evidence mapper, prototype planning, boundary

### `unknown_open_domain`
Covers: topics that do not fit a stable known bucket yet.
- Evidence needs: conceptual definition first
- Likely risks: unknown risk, unknown evidence, brittle assumptions
- Possible behavior packs: unknown-term discovery, clarification, research planning

## SECTION 5 — Domain family expansion

Recommended expansion of domain families:

### AI / cognition
- `ai_systems`
- `machine_learning`
- `llm_systems`
- `agentic_systems`
- `ai_safety_governance`
- `cognitive_architecture`
- `theory_of_mind`
- `philosophy_of_mind`
- `cognitive_science`
- `psychology`
- `neuroscience`

### Science / engineering
- `materials_discovery`
- `metamaterials`
- `physics`
- `chemistry`
- `biology_life_sciences`
- `medicine_health_research`
- `robotics`
- `hardware_electronics`
- `privacy_sensitive_technology`
- `industrial_automation`
- `energy_systems`

### Society / law / business
- `legal_privacy`
- `policy_governance`
- `economics_business_strategy`
- `education_learning`
- `social_systems`
- `website_public_launch`
- `software_product`

### General
- `language_vocabulary`
- `creative_design`
- `owner_workflow`
- `unknown_domain`

Recommendation: treat this as an extensible family layer, not a closed taxonomy.

## SECTION 6 — Subdomain trait system

Traits can combine across domains.

Examples:
- `frontier_research`
- `emerging_technology`
- `privacy_sensitive`
- `safety_critical`
- `medical_claim_adjacent`
- `human_subject_involved`
- `physical_world_deployment`
- `regulated_domain`
- `theoretical_concept`
- `experimental_validation_needed`
- `prototype_possible`
- `evidence_sparse`
- `high_uncertainty`
- `multi_domain`
- `abuse_potential`
- `beneficial_assistive_use`

Traits should influence:
- evidence need
- boundary review
- response mode
- candidate pack formation

A topic may have many traits at once.

## SECTION 7 — Object-of-study axis

This axis says what the topic is about:
- `human_mind`
- `machine_intelligence`
- `materials`
- `signals_waves`
- `energy_power`
- `living_systems`
- `legal_rights`
- `social_behavior`
- `software_system`
- `physical_device`
- `business_process`
- `language_meaning`
- `unknown_object`

This helps separate “what it is” from “how risky it is” and “how to respond.”

## SECTION 8 — Evidence class axis

Evidence classes:
- `conceptual_definition`
- `technical_literature_needed`
- `experimental_validation_needed`
- `legal_regulatory_sources_needed`
- `safety_validation_needed`
- `clinical_validation_needed`
- `market_validation_needed`
- `user_context_needed`
- `unknown_evidence_needed`

Rule:
- higher uncertainty or higher risk should push the response toward more evidence, not more confidence.

## SECTION 9 — Risk and sensitivity axis

Risk/sensitivity classes:
- `low_risk_conceptual`
- `privacy_sensitive`
- `safety_critical`
- `medical_or_health_sensitive`
- `legal_regulatory_sensitive`
- `dual_use_or_abuse_potential`
- `public_claim_sensitive`
- `unknown_risk`

These classes should affect boundary posture, explanation depth, and whether a planning path is allowed.

## SECTION 10 — Example classifications

### 1. WiFi/RF sensing for self-care
- meta-domain: `technical_engineering` + `life_health` + `society_law_governance`
- domain: `privacy_sensitive_technology`
- traits: `human_subject_involved`, `privacy_sensitive`, `beneficial_assistive_use`, `medical_claim_adjacent`
- evidence: technical literature + legal/privacy + validation
- route: privacy boundary + research planner

### 2. Metamaterials
- meta-domain: `physical_sciences` + `technical_engineering`
- domain: `metamaterials` / `materials_discovery`
- traits: `frontier_research`, `experimental_validation_needed`, `high_uncertainty`
- evidence: technical literature + experimental validation
- route: research planner + evidence mapper

### 3. Theory of mind
- meta-domain: `mind_intelligence_consciousness`
- domain: `theory_of_mind` / `philosophy_of_mind` / `cognitive_science`
- traits: `theoretical_concept`, `multi_domain`, `high_uncertainty`
- evidence: conceptual definitions + cognitive science literature
- route: research planner; no consciousness overclaim

### 4. AI agent architecture
- meta-domain: `mind_intelligence_consciousness` + `technical_engineering`
- domain: `ai_systems` / `agentic_systems` / `cognitive_architecture`
- traits: `emerging_technology`, `safety_sensitive`, `public_claim_sensitive`
- evidence: technical literature + safety evaluation
- route: research planner + safety governance boundary

### 5. Medical software
- meta-domain: `life_health` + `technical_engineering` + `society_law_governance`
- domain: `medicine_health_research` / `software_product`
- traits: `medical_claim_adjacent`, `regulated_domain`, `safety_critical`
- evidence: clinical / regulatory / validation
- route: medical claim boundary + evidence mapper

## SECTION 11 — Relationship to existing helpers

This ontology should feed:
- `broad_topic_domain_intake.py`
- `research_conversation_planner.py`
- `privacy_sensitive_technology_boundary.py`
- future `new_domain_evidence_mapper.py`
- future `prototype_path_planner.py`
- future `domain_behavior_pack_candidate_builder.py`
- behavior pack registry
- friction pattern miner
- replay suite builder

Flow direction:
- ontology classifies
- intake summarizes
- planner chooses response shape
- boundary helper constrains unsafe areas
- evidence mapper explains what is missing
- pack builder turns repeated friction into candidate pack metadata

## SECTION 12 — Recommended implementation options

### Option A
Extend `broad_topic_domain_intake.py` directly with ontology fields.

### Option B
Create a separate helper:
`weslr/broad_topic_ontology.py`

Recommended:
- create the separate helper first
- keep intake focused on classification entrypoint
- let planner, evidence mapper, boundary, and behavior pack helpers consume the ontology later

Reason:
- avoids bloating intake helper
- allows reuse across multiple downstream helpers
- avoids endless domain-list edits
- makes the trait model stable before wiring

## SECTION 13 — Implementation sequence

Recommended sequence:

1. `IMPLEMENT_WESLR_BROAD_TOPIC_ONTOLOGY_V1`
2. `REVISE_WESLR_BROAD_TOPIC_DOMAIN_INTAKE_WITH_ONTOLOGY_V1`
3. `REVISE_WESLR_RESEARCH_CONVERSATION_PLANNER_WITH_ONTOLOGY_V1`
4. `IMPLEMENT_WESLR_BROAD_TOPIC_FRICTION_SEED_CASES_V1`
5. then continue evidence mapper / prototype planner / behavior-pack candidate builder

## SECTION 14 — Boundaries

Confirmed:
- design only
- no runtime changes
- no chat route changes
- no model/provider/search/advisor calls
- no `.weslr` writes
- no raw private data
- no public claims
- no AGI / consciousness / sentience / Turing / certification claims
- no protected runtime files touched

Protected files to keep untouched:
- `weslr/chat_responder.py`
- `weslr/main.py`
- `dialogue.py`
- `chat_ui.py`

## SECTION 15 — Final judgment

`broad_topic_ontology_layer_design_ready_for_implementation`
