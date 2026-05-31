# WESLR Broad Topic Research Conversation Process V1

## SECTION 1 — Executive canon

WESLR needs a broad-topic research conversation process so an owner can ask about unfamiliar domains and receive a bounded, useful, research-oriented answer instead of generic clarification or unsafe certainty.

This is not broad AGI readiness.
This is not public chat readiness.
This is not model/provider dependency.
This is a governed domain-intake and research-planning process.

## SECTION 2 — Current readiness baseline

Source: `docs/WESLR_BROAD_TOPIC_RESEARCH_CONVERSATION_READINESS_V1.md`

### What exists now
- unknown / friction-shaped prompt detection
- bounded uncertainty handling
- clarifying-question paths
- capability, identity, boundary, evidence-needed, planning, and discovery response building blocks
- friction capture, replay, and pattern mining
- internal behavior-pack formation for repeated failure patterns

### What is missing
- a first-class broad-domain intake classifier
- a full research conversation lifecycle
- a research/development planner for unfamiliar topics
- a new-domain evidence mapper
- a privacy/safety/legal boundary layer for new-tech exploration
- a repeatable path from broad-topic friction to behavior-pack candidates
- a unified owner-facing workflow for broad-topic research conversations

### Why route review remains premature
The stack is still a set of narrow helpers and catalogs, not a complete broad-topic research conversation workflow. It can support pieces of the journey, but it does not yet consistently intake, plan, bound, and render unfamiliar-domain conversations end-to-end.

### Why domain intake is the next missing layer
Domain intake is the hinge between raw owner prompts and safe research planning. Without it, WESLR cannot reliably classify novelty, intent, evidence needs, and risk posture before choosing a response mode.

## SECTION 3 — Broad-topic conversation lifecycle

1. receive owner topic/request
2. classify domain/topic family
3. detect novelty/unfamiliarity
4. detect intent:
   - learn/explain
   - research
   - build/prototype
   - evaluate feasibility
   - safety/legal/privacy review
   - commercial/product strategy
   - troubleshooting
5. separate knowns, unknowns, assumptions
6. map evidence requirements
7. map safety/privacy/legal/ethical boundaries
8. choose response mode:
   - direct bounded overview
   - research plan
   - prototype path
   - evidence request
   - clarification
   - refusal/boundary
   - behavior-pack candidate
9. generate candidate response plan
10. self-check fit and risk
11. render bounded answer
12. capture friction if weak
13. create or update domain behavior-pack candidate if repeated

## SECTION 4 — Domain intake design

Future helper: `weslr/broad_topic_domain_intake.py`

### Purpose
Classify new broad topics into metadata categories.

### Inputs
- safe topic descriptor
- prompt labels
- owner intent labels
- risk hints
- known/unknown hints
- existing behavior pack references

### Outputs
- domain family
- novelty level
- owner intent
- evidence need level
- risk level
- recommended next process stage
- candidate behavior-pack labels

### Domain families
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

### Novelty levels
- `known_existing_pack`
- `adjacent_to_existing_pack`
- `unfamiliar_but_researchable`
- `high_uncertainty`
- `blocked_or_sensitive`

## SECTION 5 — Research conversation planner design

Future helper: `weslr/research_conversation_planner.py`

### Purpose
Turn a domain-intake result into a safe research/development conversation plan.

### Plan types
- `explain_topic`
- `map_research_questions`
- `feasibility_review`
- `prototype_path_high_level`
- `evidence_collection_plan`
- `risk_boundary_review`
- `product_development_plan`
- `behavior_pack_seed_plan`

### Must include
- knowns
- unknowns
- assumptions
- evidence needed
- safe next step
- questions to ask owner
- boundary warnings
- prototype phase outline
- friction capture triggers

## SECTION 6 — Privacy-sensitive technology boundary design

Future helper: `weslr/privacy_sensitive_technology_boundary.py`

### Purpose
Detect and bound topics involving:
- surveillance
- tracking persons
- biometrics
- location inference
- workplace monitoring
- home monitoring
- minors/vulnerable people
- covert sensing
- security/abuse risk
- legal/privacy consent issues

### Expected behavior for WiFi/RF sensing style topics
- flag privacy/surveillance/legal boundaries
- ask whether use is consent-based and lawful
- separate research exploration from deployment
- avoid covert surveillance instructions
- stay high-level unless lawful/consent/evidence context is clear

## SECTION 7 — Evidence mapper design

Future helper: `weslr/new_domain_evidence_mapper.py`

### Purpose
Define what evidence WESLR needs before making stronger claims in a new domain.

### Evidence categories
- definitions/terminology
- technical literature
- legal/regulatory sources
- safety constraints
- hardware/software requirements
- datasets/benchmarks
- prototype validation criteria
- uncertainty gaps

### Must not
- fetch sources automatically
- pretend current knowledge
- store raw private content
- create official claims

## SECTION 8 — Prototype path planner design

Future helper: `weslr/prototype_path_planner.py`

### Purpose
Create safe high-level prototype phases for new technologies.

### Phases
1. define lawful/ethical use case
2. collect evidence and constraints
3. define evaluation metrics
4. choose safe toy/synthetic test environment
5. build non-invasive proof of concept
6. validate limits and failure modes
7. review privacy/legal/security
8. decide whether to continue

### Must not
- provide covert deployment instructions
- bypass consent
- help evade detection
- claim production readiness

## SECTION 9 — Domain behavior-pack candidate builder design

Future helper: `weslr/domain_behavior_pack_candidate_builder.py`

### Purpose
Turn repeated broad-topic friction into candidate behavior packs.

### Inputs
- domain intake packets
- research plans
- boundary packets
- evidence maps
- friction cases
- replay results
- pattern candidates

### Outputs
- behavior-pack candidate metadata
- required replay suite
- proof requirements
- promotion blockers
- owner review requirements

## SECTION 10 — Broad-topic friction seed cases design

Future helper: `weslr/broad_topic_friction_seed_cases.py`

### Purpose
Create safe seed cases across multiple broad topics.

### Initial seed domains
- WiFi/RF sensing privacy-sensitive technology
- industrial automation troubleshooting
- materials discovery feasibility
- legal/privacy policy review
- energy system prototype planning
- language/vocabulary discovery
- software product planning

### For each seed
- safe prompt descriptor
- expected intake family
- expected risk labels
- expected response mode
- expected evidence needs
- expected boundary behavior
- forbidden behavior

## SECTION 11 — Integration with existing WESLR stack

### Reuse
- unknown prompt friction router
- response method selector
- candidate response formation
- response fit self-check
- no-model bounded renderer
- answer method catalog
- answer shape catalog
- cognition case registry
- behavior pack registry
- behavior pack promotion policy
- friction case capture
- friction replay harness
- pattern miner
- replay suite builder
- proof report runner

### Do not duplicate
- boundary logic already present in existing helper layers
- answer-shape catalog semantics
- behavior-pack governance already established
- friction replay and proof-report mechanics

### Future plugin points
- domain intake before response method selection
- research planner after intake and before candidate formation
- boundary helper before final bounded answer choice
- evidence mapper before stronger claims
- prototype planner before any high-level build path
- behavior-pack candidate builder after repeated friction

## SECTION 12 — Owner route readiness gate

`chat.weslr.de` may be reviewed for broad owner testing only when all of the following exist:
- broad topic domain intake implemented
- research conversation planner implemented
- privacy-sensitive boundary helper implemented
- broad-topic seed cases implemented
- replay coverage across several seed domains
- behavior-pack candidate path exists
- no public claims
- no model/provider dependency
- protected runtime files remain untouched unless separately approved

## SECTION 13 — WiFi-sensing stress test

Use the owner’s WiFi-sensing example only as a design stress test.

Do not provide technical implementation details.
Do not make factual/current claims.

Expected WESLR behavior:
- classify as privacy-sensitive technical research
- detect human sensing/tracking risk
- ask consent/lawfulness boundary question if needed
- propose safe research plan
- propose evidence map
- propose high-level prototype phases only
- forbid covert/person-tracking deployment guidance
- capture friction if WESLR lacks domain knowledge

## SECTION 14 — Internal ISS boundary

- ISS remains internal-only framing.
- Public wording must use safer terms.
- Broad-topic work supports controlled general-capability growth internally.
- No AGI/public intelligence claim is created.

## SECTION 15 — Minimal implementation sequence

1. `IMPLEMENT_WESLR_BROAD_TOPIC_DOMAIN_INTAKE_V1`
2. `IMPLEMENT_WESLR_RESEARCH_CONVERSATION_PLANNER_V1`
3. `IMPLEMENT_WESLR_PRIVACY_SENSITIVE_TECH_BOUNDARY_V1`
4. `IMPLEMENT_WESLR_BROAD_TOPIC_FRICTION_SEED_CASES_V1`
5. `IMPLEMENT_WESLR_NEW_DOMAIN_EVIDENCE_MAPPER_V1`
6. `IMPLEMENT_WESLR_PROTOTYPE_PATH_PLANNER_V1`
7. `IMPLEMENT_WESLR_DOMAIN_BEHAVIOR_PACK_CANDIDATE_BUILDER_V1`

### Why domain intake comes first
Domain intake is the gate that determines novelty, intent, evidence needs, and risk posture. Everything else depends on that classification being available before planning, boundary review, and candidate formation.

## SECTION 16 — Boundaries

Confirmed:
- design only
- no runtime changes
- no chat route changes
- no model/provider/search/advisor calls
- no `.weslr` writes
- no raw private data
- no public ISS wording
- no AGI/consciousness/sentience/Turing/certification claims
- no protected runtime files touched

## SECTION 17 — Final judgment

`broad_topic_research_conversation_process_design_ready_for_domain_intake`
