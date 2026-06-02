# WESLR Self-RAG Evidence Loop Boundary V1

## 1. Executive doctrine

**WESLR Self-RAG Evidence Loop Boundary V1** defines how WESLR may later run a bounded evidence loop:
query route → retrieve/lookup candidate evidence → assess grounding → detect missing / contradicted / stale / access-blocked evidence → optionally route again or stop.

Self-RAG is a **bounded evidence improvement loop**, not autonomous truth authority.
A second retrieval pass may improve evidence coverage, but it does **not** prove the answer.

Self-RAG can decide:
- evidence is missing
- evidence is stale
- evidence is contradicted
- evidence is access-blocked
- more evidence is needed
- answer should be downgraded / refused / deferred

Self-RAG must not decide:
- truth
- proof
- public claim approval
- runtime action
- memory promotion
- tool execution

## 2. Boundary position

Pipeline:

RAG query routing
→ document access / PII
→ Source Evidence Graph
→ NAIE
→ inline citation / claim grounding
→ context compression / reranking
→ Self-RAG evidence loop boundary
→ final answer assembly later

This design does not assemble answers.

## 3. Loop stages

Future loop stages:

1. `initial_query_classification`
2. `initial_evidence_path_selection`
3. `evidence_candidate_collection`
4. `access_privacy_poison_check`
5. `source_evidence_graph_update_candidate`
6. `naie_candidate_check`
7. `claim_grounding_assessment`
8. `context_compression_assessment`
9. `gap_detection`
10. `reroute_or_stop_decision`
11. `fallback_or_defer_decision`

## 4. Loop outcomes

Future outcomes:

- `evidence_sufficient`
- `evidence_sufficient_with_caveat`
- `evidence_missing`
- `evidence_stale`
- `evidence_contradicted`
- `evidence_access_blocked`
- `evidence_poison_blocked`
- `evidence_privacy_blocked`
- `more_evidence_needed`
- `ask_clarification`
- `refuse_unsupported`
- `defer_until_retrieval_available`
- `unknown_outcome`

## 5. Loop packet shape

Future packet fields:

- `self_rag_loop_packet_id`
- `query_summary`
- `initial_query_class`
- `initial_routing_target`
- `loop_iteration_count`
- `max_iterations`
- `evidence_candidates`
- `accepted_evidence_refs`
- `rejected_evidence_refs`
- `missing_evidence_summary`
- `contradiction_summary`
- `stale_evidence_summary`
- `access_block_summary`
- `poison_block_summary`
- `privacy_block_summary`
- `grounding_status`
- `citation_readiness`
- `context_budget_status`
- `reroute_recommended`
- `reroute_target`
- `stop_reason`
- `fallback_behavior`
- `recommended_answer_action`
- `recommended_next_check`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 6. Reroute rules

- reroute only if missing evidence is specific
- reroute only within max iteration budget
- reroute must preserve access / privacy / poison constraints
- reroute must not repeat the same failed path endlessly
- if contradiction remains unresolved, preserve contradiction
- if source is stale and no fresh source exists, caveat or defer
- if source is access-blocked, do not bypass privacy
- if citation is required but unavailable, mark unsupported
- if public claim depends on private evidence, refuse public claim

## 7. Stop rules

Stop when:

- evidence sufficient
- max iterations reached
- evidence unavailable
- access / privacy / poison blocks
- contradiction cannot be resolved
- query requires current data but current source unavailable
- public claim remains unsupported
- user clarification needed

## 8. Relationship to RAG Query Routing

RAG routing selects initial and reroute targets.
Self-RAG may ask routing for a new path, but cannot retrieve directly.

## 9. Relationship to Document Access / PII

Document Access / PII is mandatory before evidence can be accepted.
Self-RAG must not bypass:

- `access_blocked`
- `summary_only`
- `vectorization_blocked`
- `public_use_blocked`
- `privacy_blocked`
- secrets / tokens blocked

## 10. Relationship to Source Evidence Graph

Self-RAG may propose graph updates or lookups, but this design does not write graph state.

Graph edges should expose:

- support
- contradiction
- invalidation
- freshness
- access
- poison
- citation readiness

## 11. Relationship to NAIE

NAIE checks candidates and rejects unsupported authority.
Self-RAG uses NAIE outputs to decide:

- reroute
- ask clarification
- downgrade
- refuse
- preserve branch

## 12. Relationship to Inline Citation / Claim Grounding

Grounding assessment determines whether claims are:

- grounded
- unsupported
- contradicted
- stale
- access-restricted
- poison-quarantined
- citation-ready
- citation-blocked

Self-RAG may reroute only to resolve specific grounding gaps.

## 13. Relationship to Context Compression / Reranking

If evidence exists but context budget fails:

- compress without losing contradictions
- preserve citation refs
- preserve freshness / access / poison flags
- ask clarification or defer if insufficient space

## 14. Relationship to Forecast Error Ledger

Forecast/error history may inform:

- repeated missing evidence pattern
- stale source pattern
- wrong-source pattern
- reroute target suggestion

But no autonomous learning or behavior change.

## 15. Relationship to Live Daemon

Daemon may receive only compact verdicts:

- `evidence_sufficient`
- `evidence_missing`
- `evidence_blocked`
- `contradiction_present`
- `ask_clarification`
- `defer_response`
- `refuse_unsupported`

Daemon must not receive:

- raw evidence candidates
- raw retrieved chunks
- private documents
- graph internals
- prompts
- secrets

## 16. Initial examples

Future example set should include:

1. Evidence sufficient after first pass.
2. Missing citation source triggers one reroute.
3. Stale support triggers fresh-source reroute, then caveat when unavailable.
4. Contradictory evidence preserved, no forced winner.
5. Access-blocked source stops loop.
6. Poison-blocked source stops loop.
7. Public claim unsupported after max iterations, refused.
8. Currentness-sensitive query deferred when no current source exists.
9. Context budget exceeded, compression recommended before answer assembly.
10. Repeated failed reroute path stops to avoid loop.

## 17. Future helper design

Recommended future helper:

`weslr/self_rag_evidence_loop_boundary.py`

Future APIs:

- `build_self_rag_loop_packet_v1(...)`
- `evaluate_self_rag_evidence_state_v1(packet)`
- `select_self_rag_reroute_v1(packet)`
- `validate_self_rag_loop_packet_v1(packet)`
- `summarize_self_rag_loop_packet_v1(packet)`
- `to_self_rag_loop_json_safe_v1(value)`
- `build_initial_self_rag_loop_examples_v1()`

## 18. Future implementation strategy

Recommended phases:

1. metadata-only loop packet builder
2. synthetic examples
3. validation helper
4. evidence-state evaluator
5. reroute selector
6. max-iteration and repeated-path guard
7. context budget handling
8. Batch A closure audit
9. final answer assembly boundary design later

## 19. Boundaries and non-claims

This design does not implement retrieval.
It does not call web/search.
It does not call APIs.
It does not call models/providers.
It does not vectorize documents.
It does not create indexes.
It does not write memory.
It does not write `.weslr`.
It does not assemble final answers.
It does not authorize public claims.
It does not authorize runtime/tool/action behavior.
It does not claim hallucination elimination, proof, truth, AGI, consciousness, sentience, Turing success, security certification, public readiness, or production readiness.

## 20. Recommended next lane

Recommended next lane:
`RUN_WESLR_ADVANCED_AI_CAPABILITY_CHECKLIST_BATCH_A_CLOSURE_AUDIT_V1`

Preserve:
`IMPLEMENT_WESLR_CONTEXT_COMPRESSION_AND_RERANKING_BOUNDARY_V1`
`IMPLEMENT_WESLR_SELF_RAG_EVIDENCE_LOOP_BOUNDARY_V1`

## 21. Final judgment

Recommended judgment:
`self_rag_evidence_loop_design_ready_for_batch_a_closure_audit`
