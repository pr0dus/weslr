# WESLR Broad Topic Research Conversation Readiness V1

## 1 — Executive truth

**Is WESLR ready to chat about almost any new topic?**

Not yet. WESLR has strong building blocks for bounded uncertainty, evidence need, unknown-term handling, planning, and safety boundaries, but it does **not** yet have a complete broad-topic intake / research conversation process that reliably handles new domains end-to-end.

**What can it do now?**
- recognize unknown or friction-shaped prompts
- ask clarifying questions when needed
- preserve uncertainty instead of pretending certainty
- give bounded capability, identity, boundary, evidence-needed, planning, and discovery-oriented answers
- generate friction cases when the response path is weak
- support replay, pattern mining, and internal behavior-pack formation for repeated failures

**What is missing?**
- a dedicated broad-domain intake classifier and conversation lifecycle
- a first-class research/development planner for unfamiliar topics
- a domain-evidence mapper for new technical areas
- a privacy/safety/legal boundary layer specific to new-tech exploration
- a repeatable path from broad-topic friction to domain behavior-pack candidates
- a unified owner-facing broad-topic process for research conversations

**Why is owner route review premature or not premature?**
- **Premature for routing:** yes, because the stack is still composed of narrow helpers and catalogs rather than a broad-topic conversation workflow.
- **Not premature for discovery:** no, because the substrate already shows the right direction and can be mapped into a process design lane.

**What must exist before chat.weslr.de becomes useful for broad owner testing?**
- a broad-topic domain intake layer
- a research conversation planner
- a risk/boundary classifier for privacy, legal, and safety concerns
- safe prototype-path guidance at a high abstraction level
- friction capture/replay for broad-topic failures
- behavior-pack candidate generation for repeated domain friction

## 2 — Current relevant substrates

| File / module / doc | Status | How it helps | Gap |
|---|---|---|---|
| `weslr/unknown_prompt_friction_router.py` | implemented | detects unknown, evidence, continuity, correction, relationship, language, and boundary friction; recommends route/policy | still a friction router, not a broad-domain intake workflow |
| `weslr/response_method_selector.py` | implemented | deterministic selection across identity, capability, unknown, uncertainty, planning, discovery, boundaries | route selection is still fragmentary; no broad-topic domain model |
| `weslr/candidate_response_formation.py` | implemented | forms bounded candidate paths and includes scientific / language discovery routes | still downstream from selector; no intake/planning orchestration |
| `weslr/response_fit_self_check.py` | implemented | checks fit, authority drift, raw leak risk, and response quality pressures | evaluates candidate fit, but does not create broad-domain plans |
| `weslr/no_model_bounded_renderer.py` | implemented | renders bounded responses without model calls | safe renderer, but not a research conversation designer |
| `weslr/answer_method_catalog.py` | implemented | includes evidence-needed, governance escalation, scientific discovery, unknown-engine methods | catalog exists, but domain-specific intake is missing |
| `weslr/answer_shape_catalog.py` | implemented | includes evidence-needed, scientific discovery guidance, language discovery, refusal, plan shapes | shape layer exists, but not broad-topic orchestration |
| `weslr/cognition_case_registry.py` | implemented | provides bounded cases for routing and response formation | still shaped around existing known families |
| `weslr/behavior_pack_registry.py` | implemented | groups identity/unknown/boundary/owner workflow packs with evidence and replay sources | good for packaging, but not enough by itself to intake new domains |
| `weslr/behavior_pack_promotion_policy.py` | implemented | recommends internal promotion only when replay, proof, and boundaries are present | promotion policy exists, but no broad-domain candidate pipeline yet |
| `weslr/friction_case_capture.py` | implemented | captures failures into replayable metadata | broad-topic failures can be captured, but no broad-topic seed generator exists |
| `weslr/friction_pattern_miner.py` | implemented | turns friction into pattern candidates | useful for repeated broad-topic failures, but needs more seed domains |
| `weslr/friction_replay_suite_builder.py` | implemented | expands patterns into neighbor/boundary/control replay suites | strong anti-hardcoding substrate, not broad domain coverage yet |
| `weslr/friction_training_proof_report_run.py` | implemented | internal proof-reporting of governed improvement loops | proof of internal improvement, not broad-topic readiness |
| `weslr/real_answer_quality_observation_helpers.py` | implemented | metadata-only observation boundary for real answer quality | helpful for later broad-topic observation, but not live research routing |
| `weslr/evaluation_matrix_case_registry_helpers.py` | implemented | metadata-only registry for evaluation families and blocked sources | good governance substrate; not a topic-intake engine |
| `weslr/ordinary_reasoning_guidance.py` | implemented | planning, uncertainty, triage, risk, constraint guidance | useful generic reasoning, but not topic-specific intake |
| `weslr/capability_boundary.py` | implemented | science/research, industry, and other capability boundaries | helps with safety posture, not with broad-topic workflow design |
| `weslr/capability_router.py` | implemented | deterministic capability classifier using triggers and context boosts | routing only; not a conversation planner |
| `weslr/capability_discovery/ingestion.py` | implemented | ingest/search substrate for capabilities and topics | discovery substrate exists, but not a user-facing research conversation path |
| `weslr/capability_discovery/seeds.py` | implemented | has research/scientific-oriented discovery seeds | seed support exists, but not a broad-topic owner intake workflow |
| `weslr/chat_responder.py` | implemented | contains evidence-needed and boundary-related response logic | supports safe replies, but still not broad-topic research process design |
| `docs/WESLR_BROAD_TOPIC_RESEARCH_CONVERSATION_READINESS_V1.md` | this doc | maps readiness | identifies the missing process layer |
| `docs/WESLR_FRICTION_TRAINING_PROOF_REPORT_RUN_V1.md` | implemented | internal proof of governed improvement chain | useful evidence, but narrow in scope |
| `docs/WESLR_V101_INTERNAL_LABEL_REVIEW_V1.md` | implemented | internal label review | confirms governed improvement, not broad-topic readiness |

## 3 — New-domain conversation lifecycle

Desired lifecycle:

1. owner asks about a new topic
2. classify the domain/topic
3. detect known / unknown state
4. identify evidence requirements
5. identify safety / privacy / legal / ethical risks
6. choose response mode:
   - direct bounded overview
   - research plan
   - prototype plan
   - evidence request
   - clarification
   - refusal / boundary
7. generate a candidate response
8. self-check fit
9. render answer
10. capture friction if weak
11. create a domain behavior-pack candidate if repeated

What exists now:
- steps 2–9 are partially covered by narrow helper layers
- steps 1 and 10–11 are not yet first-class broad-topic process steps
- the lifecycle is not yet assembled into a single owner-facing pipeline

## 4 — WiFi-sensing example as stress test

Using WiFi sensing only as an example domain:

If asked:
> “I want to develop WiFi sensing that can track people in a house.”

WESLR should:
- recognize this as an unfamiliar RF / WiFi sensing / human sensing topic
- avoid pretending technical certainty
- separate knowns, unknowns, assumptions, and risks
- flag privacy, surveillance, legal, and safety boundaries
- ask whether the use is consent-based and lawful
- separate research exploration from deployment
- propose safe research questions
- propose the evidence needed next
- outline prototype phases only at a high level
- avoid invasive surveillance deployment instructions
- create a friction case if it lacks enough domain knowledge

What it should **not** do:
- assume legality
- assume consent
- provide covert surveillance instructions
- claim operational mastery of the domain without evidence

## 5 — Missing behavior packs

Candidate packs needed for broad owner chat:
- new technology research pack
- privacy-sensitive technology pack
- prototype planning pack
- scientific / technical discovery pack
- domain intake pack
- evidence acquisition pack
- safety / legal boundary pack
- owner research workflow pack

What can be built now:
- owner workflow pack candidate structure
- scientific / discovery-related candidate structure
- privacy / boundary candidate structure
- evidence-needed candidate structure

What needs more evidence:
- domain-specific research packs for real technical topics the owner will actually use
- repeated broad-topic friction examples across multiple domains
- stable intake signals that generalize beyond one example topic

## 6 — Missing implementation helpers

| Helper | Purpose | Reuse | Must not do | Priority |
|---|---|---|---|---|
| `broad_topic_domain_intake.py` | classify broad new topics and novelty level | capability router, unknown friction router, cognition registry | become a live router or model caller | high |
| `research_conversation_planner.py` | generate safe research / prototype / evidence plans | ordinary reasoning guidance, answer shape catalog | claim domain certainty or deploy instructions | high |
| `new_domain_evidence_mapper.py` | map what evidence is needed for unfamiliar domains | evidence-needed helpers, response-fit self-check | read private data or fetch external sources automatically | medium |
| `privacy_sensitive_technology_boundary.py` | enforce privacy / surveillance / legal boundaries | capability boundary, refusal boundary, chat responder boundary logic | issue unsafe deployment advice | high |
| `prototype_path_planner.py` | propose safe high-level prototype phases | planning helpers, scientific discovery guidance | provide invasive implementation details | medium |
| `domain_behavior_pack_candidate_builder.py` | turn repeated broad-topic friction into candidate packs | behavior pack registry/promotion policy, friction miner | auto-promote or auto-route live | medium |
| `broad_topic_friction_seed_cases.py` | seed broad-topic stress cases for replay | friction case capture, replay suite builder | use raw private text or live chat | medium |

## 7 — Readiness threshold for owner chat route

Before routing chat.weslr.de for broad owner testing, WESLR should be able to:
- answer identity / capability / boundary questions reliably
- handle unknown terms cleanly
- create research plans for new domains
- flag privacy / safety / legal risks
- create prototype plans at safe abstraction level
- capture and replay friction from broad-topic failures
- generate behavior-pack candidates from repeated domain friction

Suggested minimum before owner route review:
- the broad-topic intake / planner / boundary helpers exist
- at least a few real broad-topic seed domains have replay coverage
- repeated failure clusters can become candidate packs without manual rewriting

## 8 — Recommended next lane

**Recommended lane:** `DESIGN_WESLR_BROAD_TOPIC_RESEARCH_CONVERSATION_PROCESS_V1`

Why this lane first:
- the missing piece is process design, not just another isolated helper
- the current stack already has many narrow primitives
- the next useful step is to define how intake, planning, boundary checks, friction capture, and pack candidate formation connect
- implementation should follow after the process boundary is fixed

## 9 — Boundaries

Confirmed:
- discovery only
- no code changes
- no runtime changes
- no chat route changes
- no model/provider/search/advisor calls
- no `.weslr` writes
- no raw private data
- no public ISS wording
- no AGI / consciousness / sentience / Turing / certification claims
- protected runtime files untouched

## 10 — Final judgment

**`broad_topic_research_conversation_partial_needs_domain_intake`**
