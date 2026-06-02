# WESLR Context Compression and Reranking Boundary V1

## 1. Executive doctrine

**WESLR Context Compression and Reranking Boundary V1** defines how later systems may select, order, compress, summarize, drop, caveat, or defer context before answer assembly.

Context compression is **relevance preservation under limited space**.
Reranking is **ordering evidence/candidates for review**.

Neither grants truth authority.
A context item being ranked highly does **not** mean it is true, public-safe, current, or action-authorized.

## 2. Boundary position

Pipeline:

RAG routing
→ document access / PII boundary
→ Source Evidence Graph
→ NAIE
→ inline citation / claim grounding
→ context compression / reranking boundary
→ final answer assembly later
→ daemon compact verdict later

This design does not assemble answers.

## 3. Why this is needed

This boundary exists because:

- retrieved or graph-linked evidence may exceed answer context limits
- long contexts can bury important evidence
- stale or access-blocked evidence must not be promoted by compression
- contradictions must not be compressed away
- unsupported claims must remain visible
- citations need claim-level context preservation
- final answer assembly needs bounded, ranked, compressed evidence packets

## 4. Context unit types

Future context unit types:

- `claim_context`
- `source_summary_context`
- `citation_context`
- `document_summary_context`
- `chunk_summary_context`
- `memory_summary_context`
- `artifact_provenance_context`
- `signal_metadata_context`
- `forecast_context`
- `scenario_context`
- `forecast_error_context`
- `naie_inference_context`
- `daemon_verdict_context`
- `unknown_context`

## 5. Compression modes

Future compression modes:

- `no_compression`
- `metadata_only`
- `summary_only`
- `claim_preserving_summary`
- `citation_preserving_summary`
- `contradiction_preserving_summary`
- `freshness_preserving_summary`
- `privacy_preserving_summary`
- `hash_reference_only`
- `drop_blocked_context`
- `defer_due_missing_context`
- `unknown_compression_mode`

## 6. Reranking modes

Future reranking modes:

- `source_freshness_first`
- `claim_relevance_first`
- `citation_readiness_first`
- `access_allowed_first`
- `contradiction_visibility_first`
- `owner_priority_first`
- `safety_risk_first`
- `public_claim_safety_first`
- `no_reranking`
- `unknown_reranking_mode`

## 7. Context packet shape

Future packet fields:

- `context_packet_id`
- `query_summary`
- `context_units`
- `selected_context_units`
- `dropped_context_units`
- `blocked_context_units`
- `compression_mode`
- `reranking_mode`
- `selection_reason`
- `dropped_reason_summary`
- `contradictions_preserved`
- `unsupported_claims_preserved`
- `citation_refs_preserved`
- `freshness_refs_preserved`
- `access_restrictions_preserved`
- `privacy_restrictions_preserved`
- `poison_flags_preserved`
- `lost_in_middle_risk`
- `context_budget_status`
- `recommended_next_check`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 8. Selection rules

- never compress away contradictions
- never compress away access restrictions
- never compress away poison status
- never compress away freshness caveats
- never promote private evidence into public context
- never summarize secrets/tokens; block them
- preserve citation refs when citations are required
- preserve unsupported-claim markers
- preserve owner-priority gaps
- prefer summary-only for sensitive/private sources
- use hash/reference-only mode for highly sensitive sources
- if context budget is insufficient, defer or ask clarification instead of fabricating

## 9. Lost-in-the-middle mitigation

- important claim/evidence pairs should stay near the answer assembly boundary
- contradictory evidence should remain visible
- source freshness and access status should travel with compressed units
- high-risk caveats should not sit only in low-visibility context
- stale or unsupported evidence should not be silently dropped if it changes the answer

## 10. Relationship to Document Access / PII

Use document access packets to decide:

- raw content allowed or blocked
- summary-only required
- public citation blocked
- vectorization/indexing blocked
- private evidence restrictions
- secrets/tokens blocked

## 11. Relationship to RAG Query Routing

RAG routing selects the evidence path.
Context compression selects and compresses allowed context from that path.

This boundary does not retrieve.

## 12. Relationship to Source Evidence Graph

Use graph nodes/edges to preserve:

- supports
- contradicts
- invalidates
- citation refs
- access restrictions
- freshness metadata
- public-claim readiness

## 13. Relationship to Inline Citation / Claim Grounding

Grounding requires claim/evidence/citation refs to survive compression.

Rules:

- citation-ready claims must keep evidence refs
- unsupported claims must stay marked
- contradicted claims must keep contradiction marker
- stale claims must keep caveat marker

## 14. Relationship to NAIE

NAIE may use compressed context only if:

- constraints are preserved
- contradictions are preserved
- missing inputs are preserved
- rejection reasons are preserved

Compression must not make NAIE think the graph is complete.

## 15. Relationship to Live Daemon

Daemon receives only compact verdicts:

- `context_ready`
- `context_blocked`
- `context_deferred`
- `access_blocked`
- `privacy_blocked`
- `contradiction_present`
- `unsupported_present`

Daemon must not receive:

- raw context
- raw chunks
- private source text
- full graph
- model prompts

## 16. Initial examples

Future example set should include:

1. Fresh supported claim selected with citation ref preserved.
2. Stale source compressed with freshness caveat preserved.
3. Contradictory sources both retained.
4. Access-restricted source dropped from public context.
5. Poison-quarantined source blocked from context.
6. Private project memory compressed as summary-only.
7. API key context blocked, not summarized.
8. Energy signal context ranked by freshness and deadline relevance.
9. Public claim context blocked because maturity not public_safe.
10. Long context budget exceeded, ask clarification instead of fabricating.

## 17. Future helper design

Recommended future helper:

`weslr/context_compression_reranking_boundary.py`

Future APIs:

- `build_context_compression_packet_v1(...)`
- `select_context_units_v1(packet)`
- `compress_context_units_v1(packet)`
- `rank_context_units_v1(packet)`
- `validate_context_compression_packet_v1(packet)`
- `summarize_context_compression_packet_v1(packet)`
- `to_context_compression_json_safe_v1(value)`
- `build_initial_context_compression_examples_v1()`

## 18. Future implementation strategy

Recommended phases:

1. metadata-only context packet builder
2. synthetic examples
3. validation helper
4. context unit selector
5. contradiction-preserving compression
6. citation-preserving compression
7. access/privacy-preserving compression
8. simple metadata reranking
9. Self-RAG evidence loop design
10. final answer assembly boundary design later

## 19. Boundaries and non-claims

This design does not implement compression.
It does not implement reranking.
It does not retrieve documents.
It does not call models/providers.
It does not create vector indexes.
It does not assemble final answers.
It does not write memory.
It does not write `.weslr`.
It does not authorize public claims.
It does not claim hallucination elimination, proof, truth, AGI, consciousness, sentience, Turing success, security certification, public readiness, or production readiness.

## 20. Recommended next lane

Recommended next lane:
`DESIGN_WESLR_SELF_RAG_EVIDENCE_LOOP_BOUNDARY_V1`

Preserve:
`IMPLEMENT_WESLR_CONTEXT_COMPRESSION_AND_RERANKING_BOUNDARY_V1`

## 21. Final judgment

Recommended judgment:
`context_compression_reranking_design_ready_for_self_rag_evidence_loop_design`
