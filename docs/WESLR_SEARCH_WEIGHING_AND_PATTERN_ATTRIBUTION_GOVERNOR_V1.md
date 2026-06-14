# WESLR Search Weighing And Pattern Attribution Governor V1

## 1. Governor definition
**Name:** `search_weighing_pattern_attribution_governor_v1`

A metadata-only, review-only governance layer that decides what WESLR should search for next, why it matters, whether search is allowed, which existing helper should handle it, and what artifact should be produced.

## 2. Core principle
The governor does not discover truth.
It ranks candidate search/work directions and routes them into governed artifacts, evidence plans, disconfirmation plans, or blocked states.

## 3. Self-model
The governor maintains a structured operational self-model of WESLR state.

### Self-model fields
- known implemented helpers
- known missing helpers
- available tools
- unavailable tools
- blocked environments
- completed artifacts
- blocked artifacts
- reviewed artifacts
- domains already tested
- domains not yet tested
- known weak signal patterns
- known strong signal patterns
- owner goals
- owner approval gates
- current source boundary
- current evidence authority
- current runtime authority
- current confidence limits
- current next-lane queue

This is not consciousness, not AGI, and not self-awareness as a public claim.
It is structured state accounting.

## 4. Decision questions
The governor answers:
- Why search?
- Where search?
- When search?
- What search class?
- What source boundary?
- What artifact family?
- What disconfirmation value?
- What is unsafe?
- What requires owner approval?
- What should be delayed?
- What existing helper should be used?

## 5. Weighing dimensions
At minimum, the governor weighs:
- unresolvedness
- anomaly strength
- metadata signal strength
- disconfirmation value
- evidence availability
- source authority availability
- ontology sufficiency
- cross-domain bridge potential
- artifact usefulness
- product/workflow potential
- owner relevance
- implementation readiness
- environment readiness
- safety risk
- overclaim risk
- private-data risk
- novelty-without-hype
- cost/token/tool budget
- review burden

## 6. Possible decisions
The governor may recommend:
- do not search
- wait for owner approval
- repair environment first
- run metadata-only locator
- create source-selection plan
- create unexplained signal artifact
- create artifact forward work plan
- create OER no-op record
- create ontology expansion request
- route to cross-domain scout
- route to candidate-prep exclusion
- route to candidate-prep only if narrow criteria met
- block by safety
- review existing artifact first
- implement missing helper first

## 7. Pattern attribution
Pattern attribution is review-only.
A source pattern may resemble another experiment/domain structurally, but WESLR must not claim same cause or same mechanism.

### `pattern_attribution_packet`
- `source_pattern_id`
- `source_domain`
- `target_domain_or_experiment`
- `shared_structure`
- `key_differences`
- `possible_mechanism_overlap`
- `missing_evidence`
- `disconfirmation_tests`
- `analogy_strength`
- `confidence_posture`
- `blocked_claims`
- `next_safe_step`
- `owner_review_required`
- `final_judgment`

### Attribution rules
- compare structure, not truth status
- compare signal shape, not mechanism certainty
- compare route utility, not discovery authority
- keep disconfirmation-first posture
- do not collapse analogy into evidence

## 8. Attribution examples
Each example is review-only and blocks same-mechanism, proof, discovery, public science, accepted-evidence, and accepted-candidate claims.

### Example A: pulsar replay pattern → long-period radio transient comparison
- shared structure: periodic/recurring signal shape
- key differences: domain, instrumentation, and provenance constraints
- possible mechanism overlap: bounded, uncertain
- next safe step: review-only comparison artifact

### Example B: pulsar timing/repeatability pattern → general unexplained signal artifact
- shared structure: repeatability with unresolved remainder
- key differences: source authority and artifact purpose
- possible mechanism overlap: weak, not claimed
- next safe step: unexplained signal artifact

### Example C: FRB grouping problem → classification-fracture artifact
- shared structure: clustering ambiguity and label fracture
- key differences: domain and available disconfirmation tests
- possible mechanism overlap: possibly only at metadata level
- next safe step: artifact forward work plan or classification-fracture review

### Example D: grid oscillation / energy-system coordination → synchronization pattern comparison
- shared structure: oscillation, coordination, phase-like misalignment
- key differences: physical substrate and operational constraints
- possible mechanism overlap: not asserted
- next safe step: governed comparison artifact

### Example E: language/protocol emergence → communication-structure artifact
- shared structure: emergent structure in message flow
- key differences: semantics, population, and control surface
- possible mechanism overlap: speculative only
- next safe step: review artifact or source-selection plan

### Example F: false-assumption claim → disconfirmation-first artifact
- shared structure: a claim that fails when checked against constraints
- key differences: domain and evidence class
- possible mechanism overlap: irrelevant to decision
- next safe step: disconfirmation-first artifact

## 9. Relationship to existing modules
The governor uses, but does not replace:

- **Expectation-Deviation Engine**: detects mismatch/deviation
- **MLCF**: enforces evidence, authority, routing, and ledger boundaries
- **Cross-Domain Scout**: explores cross-domain signal candidates
- **Ontology Expansion Request Builder**: handles insufficient ontology
- **OER No-Op Record Builder**: handles sufficient ontology / no expansion needed
- **Candidate-Preparation Helpers**: receive only narrow eligible routes
- **Unexplained Signal Artifact Helpers**: package unexplained/unfinished patterns as governed artifacts
- **Artifact Forward Work Plan Helpers**: produce the next safe work plan
- **Capability Maturity Registry**: determines whether WESLR is mature enough to attempt a lane
- **Context Compression / Reranking**: ranks candidate directions and keeps context bounded
- **UNKNOWN ENGINE**: handles unknowns as bounded review objects, not truth claims

## 10. Safe input modes
Allowed:
- existing artifact metadata
- metadata-only locator results
- manually described signal
- known-science replay case metadata
- approved synthetic signal
- approved local experiment metadata
- helper summaries
- review artifacts
- blocked result artifacts

Blocked by default:
- raw private data
- `.weslr` content
- source full text
- PDFs
- raw HTML
- snippets as evidence
- unapproved datasets
- private logs
- runtime traces
- hidden prompts
- final-answer text as evidence

## 11. Safe output modes
Allowed:
- search weighing packet
- pattern attribution packet
- routing recommendation
- blocked state
- source-selection plan recommendation
- unexplained signal artifact recommendation
- artifact forward work plan recommendation
- OER/no-op recommendation
- owner decision request

Forbidden:
- accepted evidence
- accepted candidate
- final answer
- public claim
- proof claim
- discovery-of-truth claim
- autonomous source ingestion
- provider/model call
- runtime wiring
- memory mutation
- `.weslr` IO
- ontology auto-application
- self-modification
- product-readiness claim

## 12. Future helper implementation
Proposed files:
- `weslr/search_weighing_pattern_attribution_governor.py`
- `weslr/tests/test_search_weighing_pattern_attribution_governor_v1.py`

Expected APIs:
- `build_search_weighing_governor_packet_v1`
- `validate_search_weighing_governor_packet_v1`
- `rank_search_direction_candidates_v1`
- `build_pattern_attribution_packet_v1`
- `validate_pattern_attribution_packet_v1`
- `summarize_search_weighing_governor_packet_v1`
- `render_search_weighing_governor_markdown_v1`
- `to_search_weighing_governor_json_safe_v1`
- `build_initial_search_weighing_governor_examples_v1`

## 13. Initial future examples
- blocked third true run: choose environment repair before rerun
- materials run: choose OER no-op and richer metadata signal follow-up
- pulsar replay: choose known-science replay artifact
- long-period radio transient: choose unexplained signal artifact
- energy-system coordination gap: choose practical/product-work artifact path
- unsafe overclaiming signal: block
- weak metadata: route to richer signal item / source-selection plan, not candidate

## 14. Current-blocker usefulness
The governor would:
- choose SearXNG repair before rerunning the third true run
- rank OER no-op builder and richer metadata signal item shape as safe no-SearXNG implementation lanes
- avoid wasting run budget when environment readiness is false
- help WESLR decide what to search tomorrow and why

## 15. Validation expectations
Future validator must fail closed on:
- missing required fields
- true authority flags
- source ingestion authority
- provider/model/runtime authority
- `.weslr` content
- private/raw/source content
- final-answer authority
- accepted evidence/candidate claims
- proof/discovery/public-science claims
- AGI/consciousness/sentience claims
- self-modification/autonomous ontology claims
- empty blocked claims
- empty owner-review requirement
- empty disconfirmation tests for attribution packets
- pattern attribution claiming same mechanism without evidence

## 16. Recommended next lane
`REVIEW_WESLR_SEARCH_WEIGHING_AND_PATTERN_ATTRIBUTION_GOVERNOR_V1`

## 17. Final judgment
`search_weighing_pattern_attribution_governor_design_ready_for_review`
