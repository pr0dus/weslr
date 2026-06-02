# WESLR Source Evidence Graph V1

**Type:** design-only
**Scope:** metadata, provenance, grounding, and relation modeling
**Repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch:** `master`

## 1. Executive doctrine

**WESLR Source Evidence Graph V1** is WESLR’s representation layer for evidence relationships.

It records how sources, claims, artifacts, signals, memory references, forecasts, scenarios, errors, and candidate answers relate.

It is **not** proof authority.
It is **not** truth authority.
It is **not** a vector database.
It is **not** RAG implementation.
It is **not** public-claim authorization.

Core rule: evidence edges support, contradict, depend on, invalidate, or qualify claims — they do not automatically prove them.

---

## 2. Boundary position

Pipeline:

source / memory / signal / artifact / retrieved document
→ Poison Shield
→ source scope / provenance / freshness
→ Source Evidence Graph
→ NAIE inference packet
→ RAG / query routing later
→ citation / claim grounding later
→ final answer assembly later
→ owner/operator approval where needed

---

## 3. Why this is needed

- provenance exists in separate helpers
- NAIE needs graph nodes/edges
- RAG needs source-to-claim mapping
- citations need evidence references
- contradiction resolution needs explicit graph edges
- public claims need lifecycle grounding
- document-to-action needs source authority boundaries
- answer grounding readiness needs claim-level evidence structure

---

## 4. Graph node types

- `source_node`
- `document_node`
- `chunk_node`
- `claim_node`
- `citation_node`
- `artifact_node`
- `signal_node`
- `memory_node`
- `forecast_node`
- `scenario_node`
- `forecast_error_node`
- `capability_node`
- `inference_packet_node`
- `candidate_answer_node`
- `owner_instruction_node`
- `public_claim_node`
- `unknown_node`

---

## 5. Graph edge types

- `supports`
- `contradicts`
- `depends_on`
- `invalidates`
- `qualifies`
- `came_from`
- `cites`
- `summarizes`
- `derived_from`
- `requires_owner_approval`
- `blocked_by`
- `generated_candidate`
- `observed_result`
- `same_source_as`
- `newer_than`
- `older_than`
- `same_claim_as`
- `conflicts_with`
- `requires_freshness_check`
- `requires_access_check`
- `requires_poison_check`

---

## 6. Evidence graph record shape

Fields:
- `evidence_graph_id`
- `graph_version`
- `created_timestamp`
- `scope`
- `source_nodes`
- `claim_nodes`
- `artifact_nodes`
- `signal_nodes`
- `memory_nodes`
- `forecast_nodes`
- `scenario_nodes`
- `error_nodes`
- `capability_nodes`
- `inference_nodes`
- `candidate_answer_nodes`
- `public_claim_nodes`
- `edges`
- `contradiction_summary`
- `unsupported_claims`
- `stale_sources`
- `poison_quarantined_sources`
- `access_restricted_sources`
- `missing_sources`
- `claim_grounding_status`
- `citation_readiness`
- `rag_readiness`
- `public_claim_readiness`
- `recommended_next_check`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

---

## 7. Source node shape

Fields:
- `source_id`
- `source_type`
- `source_name`
- `source_scope`
- `source_reference`
- `created_timestamp`
- `retrieved_timestamp`
- `reported_timestamp`
- `freshness_status`
- `quality_status`
- `poison_shield_status`
- `access_level`
- `privacy_sensitivity`
- `owner_authorized`
- `operator_authorized`
- `raw_content_stored`
- `summary_only`
- `safe_metadata`

---

## 8. Claim node shape

Fields:
- `claim_id`
- `claim_text_summary`
- `claim_type`
- `claim_scope`
- `claim_status`
- `supporting_sources`
- `contradicting_sources`
- `citation_refs`
- `freshness_required`
- `public_claim_sensitive`
- `requires_owner_approval`
- `unsupported_reason`
- `safe_metadata`

Claim statuses:
- `supported`
- `partially_supported`
- `contradicted`
- `unsupported`
- `stale_support`
- `access_restricted`
- `poison_quarantined`
- `unknown_status`

---

## 9. Access and privacy model

- document-level access checks
- source privacy sensitivity
- no raw private dumps
- summary-only mode
- cross-user isolation requirement
- no vectorization before policy
- no public claim use without explicit public boundary

---

## 10. Poison Shield relationship

- poisoned sources may remain as quarantined metadata
- poisoned text cannot self-authorize
- hidden instructions become source risk metadata only
- poisoned source cannot support public claims
- candidate answers derived from poisoned sources require quarantine flag

---

## 11. Freshness and contradiction relationship

Use existing:
- signal provenance / freshness
- conflict policy
- forecast error ledger

Rules:
- stale support lowers claim status
- contradictory edges must remain visible
- graph should not silently collapse contradictions
- newer source does not automatically win unless policy supports it

---

## 12. NAIE relationship

NAIE uses the graph for:
- source evidence linking
- contradiction detection
- dependency resolution
- candidate rejection
- missing input discovery
- public claim rejection
- graph traversal

Source Evidence Graph is the representation layer.
NAIE is the reasoning layer.

---

## 13. RAG relationship

Future RAG query routing will use the graph to decide:
- which source types are eligible
- which claims need evidence
- which documents are access-allowed
- which chunks are stale
- which sources contradict
- whether answer grounding is ready

This design does not implement RAG.

---

## 14. Citation and claim grounding relationship

Future citation layer will use:
- claim nodes
- citation nodes
- source nodes
- support / contradict edges
- freshness metadata
- access restrictions

Rules:
- every factual claim should be mappable to evidence or marked unsupported
- citations must not be hallucinated
- citations must not point to access-forbidden sources
- contradiction should be disclosed, not hidden

---

## 15. Public claim lifecycle relationship

Public claims require:
- supported claim status
- public-safe capability maturity
- no contradiction blocker
- no access-restricted private evidence
- owner/operator approval
- public claim lifecycle tracker later

This graph does not authorize public claims.

---

## 16. Initial examples

1. source supports claim with fresh evidence
2. stale source supports claim but freshness warning applies
3. two sources contradict same claim
4. poisoned source is quarantined and cannot support claim
5. access-restricted document cannot be used in public answer
6. artifact provenance supports generated artifact claim
7. signal freshness supports energy forecast claim
8. forecast error invalidates prior forecast assumption
9. NAIE rejects LLM candidate due missing source edge
10. public claim blocked because maturity not public_safe

---

## 17. Future helper design

Future helper:

`weslr/source_evidence_graph.py`

Future APIs:
- `build_source_evidence_node_v1(...)`
- `build_claim_node_v1(...)`
- `build_evidence_edge_v1(...)`
- `build_source_evidence_graph_v1(...)`
- `validate_source_evidence_graph_v1(graph)`
- `summarize_source_evidence_graph_v1(graph)`
- `to_source_evidence_graph_json_safe_v1(value)`
- `build_initial_source_evidence_graph_examples_v1()`

---

## 18. Future implementation strategy

1. metadata-only graph node/edge builder
2. synthetic examples
3. validation helper
4. contradiction summary
5. unsupported claim detector
6. stale-source detector
7. poison/access restriction detector
8. NAIE integration
9. RAG routing boundary design
10. citation / claim grounding design

---

## 19. Boundaries and non-claims

This design does not implement a graph database.
It does not implement RAG.
It does not retrieve documents.
It does not vectorize content.
It does not call models/providers.
It does not call search.
It does not write memory.
It does not write `.weslr`.
It does not authorize public claims.
It does not claim proof, truth, hallucination elimination, security certification, AGI, consciousness, sentience, Turing success, public readiness, or production readiness.

---

## 20. Recommended next lane

`IMPLEMENT_WESLR_SOURCE_EVIDENCE_GRAPH_V1`

Then:
`DESIGN_WESLR_RAG_QUERY_ROUTING_AND_RETRIEVAL_BOUNDARY_V1`

---

## 21. Final judgment

`source_evidence_graph_design_ready_for_metadata_helper_implementation`
