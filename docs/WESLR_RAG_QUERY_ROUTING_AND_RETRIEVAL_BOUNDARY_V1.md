# WESLR RAG Query Routing and Retrieval Boundary V1

**Type:** design-only  
**Scope:** query classification, retrieval selection, access gating, grounding readiness  
**Repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`  
**Branch:** `master`

## 1. Executive doctrine

**WESLR RAG Query Routing and Retrieval Boundary V1** decides which evidence path is appropriate before answering.

Core rule: **retrieval is evidence acquisition, not authority**.

- A retrieved source does not automatically become truth.
- A graph edge does not prove a claim.
- A citation does not make a claim correct.
- An LLM answer without grounding must remain candidate-only.

This boundary selects the evidence path first, then later layers may ground claims, cite sources, or assemble answers.

---

## 2. Boundary position

Pipeline:

user request  
→ intent / claim-need detection  
→ Poison Shield if external/textual source involved  
→ RAG query routing boundary  
→ allowed retrieval path  
→ Source Evidence Graph  
→ NAIE inference  
→ citation / claim grounding later  
→ final answer assembly later

This design only routes. It does not retrieve.

---

## 3. Routing targets

Allowed routing targets:

- `pure_reasoning`
- `memory_retrieval`
- `uploaded_file_retrieval`
- `source_evidence_graph_lookup`
- `artifact_provenance_lookup`
- `signal_metadata_lookup`
- `forecast_error_ledger_lookup`
- `capability_maturity_lookup`
- `future_web_search`
- `future_document_index`
- `clarification_required`
- `unsupported_answer_refusal`
- `blocked_by_access_policy`
- `blocked_by_poison_policy`
- `blocked_by_public_claim_policy`

Routing target meaning:

- `pure_reasoning`: stable/general question can be answered without external evidence.
- `memory_retrieval`: user-specific continuity, if allowed.
- `uploaded_file_retrieval`: answer depends on user-provided files.
- `source_evidence_graph_lookup`: claim needs structured evidence relations.
- `artifact_provenance_lookup`: answer depends on artifact lineage or generation boundary.
- `signal_metadata_lookup`: answer depends on signal provenance/freshness metadata.
- `forecast_error_ledger_lookup`: answer depends on prior forecast error history.
- `capability_maturity_lookup`: answer depends on implementation readiness or capability status.
- `future_web_search`: current external evidence required and later authorized.
- `future_document_index`: later document retrieval/indexing boundary.
- `clarification_required`: scope or source target is ambiguous.
- `unsupported_answer_refusal`: evidence unavailable or answer would be fabricated.
- `blocked_by_access_policy`: source exists but access is not allowed.
- `blocked_by_poison_policy`: source is quarantined or poisoned.
- `blocked_by_public_claim_policy`: private/restricted evidence cannot support public claims.

---

## 4. Query classes

Query classes:

- `general_reasoning_query`
- `personal_memory_query`
- `uploaded_document_query`
- `source_grounded_claim_query`
- `currentness_sensitive_query`
- `technical_documentation_query`
- `legal_or_policy_query`
- `medical_or_safety_query`
- `public_claim_query`
- `energy_signal_query`
- `artifact_or_code_query`
- `unknown_query`

---

## 5. Routing packet shape

Fields:

- `routing_packet_id`
- `query_summary`
- `query_class`
- `requested_claims`
- `requires_grounding`
- `requires_currentness`
- `requires_private_data`
- `requires_user_file_access`
- `requires_web_access`
- `requires_memory_access`
- `requires_source_evidence_graph`
- `allowed_routing_targets`
- `blocked_routing_targets`
- `selected_routing_target`
- `reason_for_selection`
- `access_policy_status`
- `poison_policy_status`
- `privacy_status`
- `source_freshness_requirement`
- `citation_requirement`
- `claim_grounding_requirement`
- `fallback_behavior`
- `recommended_next_check`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

Packet rule: metadata only. No raw answer, no raw source content, no authority transfer.

---

## 6. Routing rules

1. Use `pure_reasoning` only for stable/general questions not requiring evidence.
2. Use `memory_retrieval` only when user-specific continuity is needed and allowed.
3. Use `uploaded_file_retrieval` only when the answer depends on provided files.
4. Use `source_evidence_graph_lookup` when claims need structured evidence relationships.
5. Use `future_web_search` only when currentness or external evidence is required and authorized.
6. Ask clarification when query scope/source target is ambiguous.
7. Refuse or downgrade when evidence is unavailable.
8. Never fabricate citations.
9. Never treat access-forbidden evidence as usable.
10. Never allow poisoned content to authorize retrieval or answer claims.

Routing decides the evidence path before any answer candidate is treated as usable.

---

## 7. Access and privacy

Required checks:

- document-level access check
- source privacy check
- owner authorization
- operator authorization
- private-source restriction
- public-answer restriction
- no raw private text exposure
- no vectorization without policy
- deletion/export implication later

Policy position:

- private evidence may be inspectable only within its allowed boundary.
- restricted evidence cannot be used to produce public answers.
- raw private text should not spill into answer-facing surfaces.
- policy must gate retrieval before grounding.

---

## 8. Currentness and freshness policy

Currentness is required for:

- recent facts
- laws/regulations
- prices
- software versions
- security status
- health/safety guidance
- external market/product claims
- public claims
- energy/grid/weather/price data

Rule:

If currentness is required but no current source is available, the system must caveat, ask for a source, or refuse certainty.

Freshness is a routing constraint, not a post-answer decoration.

---

## 9. Evidence graph relationship

RAG routing should use Source Evidence Graph to determine:

- whether claims have support
- whether support is stale
- whether contradictions exist
- whether sources are access-allowed
- whether poison/access restrictions exist
- whether claim grounding is ready

This boundary relies on the graph as an evidence map. It does not convert graph membership into truth.

---

## 10. NAIE relationship

NAIE should consume routing results to:

- reject unsupported candidate answers
- preserve missing evidence as next-checks
- detect contradictions
- avoid fake certainty
- decide whether scenario branches are needed

Routing is upstream of reasoning quality control. NAIE is the consumer, not the router.

---

## 11. Citation and claim grounding relationship

This boundary does **not** generate citations.

It prepares for:

`DESIGN_WESLR_INLINE_CITATION_AND_CLAIM_GROUNDING_LAYER_V1`

Rules:

- if citation is required but no source exists, mark unsupported
- if source exists but access is restricted, do not cite publicly
- if contradiction exists, disclose conflict later

The boundary only establishes whether grounding is possible and what path it should take.

---

## 12. Fallback behavior

Fallback modes:

- `answer_from_general_reasoning_with_caveat`
- `ask_clarifying_question`
- `request_source_upload`
- `use_existing_graph_only`
- `return_unsupported_claim`
- `refuse_public_claim`
- `block_due_access_policy`
- `block_due_poison_policy`
- `defer_until_retrieval_available`

Fallback rule: if the evidence path is not safe or not available, downgrade instead of inventing certainty.

---

## 13. Initial examples

1. Stable conceptual question → `pure_reasoning`.
2. User asks about uploaded document → `uploaded_file_retrieval`.
3. User asks current law → `future_web_search` or source-required fallback.
4. User asks personal project history → `memory_retrieval` if allowed.
5. Public website claim → `source_evidence_graph_lookup` + maturity check.
6. Energy signal question → `signal_metadata_lookup` or graph lookup.
7. Poisoned document → blocked from answer authority.
8. Access-restricted document → blocked for public answer.
9. Unsupported factual claim → refusal / missing evidence.
10. Contradictory sources → graph contradiction handling.

---

## 14. Future helper design

Future helper:

`weslr/rag_query_routing_boundary.py`

Future APIs:

- `build_rag_query_routing_packet_v1(...)`
- `classify_rag_query_v1(...)`
- `select_rag_routing_target_v1(...)`
- `validate_rag_query_routing_packet_v1(packet)`
- `summarize_rag_query_routing_packet_v1(packet)`
- `to_rag_query_routing_json_safe_v1(value)`
- `build_initial_rag_query_routing_examples_v1()`

Design posture for the future helper:

- metadata-only
- deterministic
- fail-closed
- no raw retrieval payloads
- no claim authority
- no public-answer authority

---

## 15. Future implementation strategy

Recommended phases:

1. metadata-only routing packet builder
2. synthetic examples
3. validation helper
4. query classifier
5. routing selector
6. Source Evidence Graph integration
7. citation / claim grounding design
8. access / PII boundary design
9. retrieval adapter design later
10. runtime retrieval implementation much later

This sequence keeps routing separate from retrieval and grounding.

---

## 16. Boundaries and non-claims

This design does not:

- implement RAG
- retrieve documents
- create vector indexes
- call web/search
- call models/providers
- write memory
- write `.weslr`
- authorize public claims
- claim hallucination elimination
- claim proof, truth, AGI, consciousness, sentience, Turing success, public readiness, security certification, or production readiness

It is a routing boundary only.

---

## 17. Recommended next lane

Recommended next lane:

`DESIGN_WESLR_INLINE_CITATION_AND_CLAIM_GROUNDING_LAYER_V1`

Preserve:

`IMPLEMENT_WESLR_RAG_QUERY_ROUTING_AND_RETRIEVAL_BOUNDARY_V1`

---

## 18. Final judgment

**rag_query_routing_retrieval_boundary_design_ready_for_inline_citation_claim_grounding_design**
