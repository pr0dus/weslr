# WESLR Inline Citation and Claim Grounding Layer V1

**Type:** design-only
**Scope:** citation readiness, claim grounding, contradiction handling, unsupported-claim handling
**Repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch:** `master`

## 1. Executive doctrine

**WESLR Inline Citation and Claim Grounding Layer V1** maps answer claims to evidence, citations, contradiction status, freshness status, access status, and unsupported-claim handling.

Core rule:

- citations are evidence links, not proof
- claim grounding is a readiness check, not truth authority

Every factual claim should be one of:

- grounded to eligible evidence
- marked as unsupported
- marked as contradicted
- marked as stale
- marked as access-restricted
- marked as not citation-ready

---

## 2. Boundary position

Pipeline:

user answer candidate
→ RAG query routing boundary
→ Source Evidence Graph
→ NAIE candidate check
→ claim grounding layer
→ final answer assembly later

This design does not assemble final answers.

---

## 3. Claim grounding packet shape

Fields:

- `claim_grounding_packet_id`
- `answer_candidate_id`
- `claim_nodes`
- `source_evidence_refs`
- `citation_refs`
- `grounded_claims`
- `unsupported_claims`
- `contradicted_claims`
- `stale_supported_claims`
- `access_restricted_claims`
- `poison_quarantined_claims`
- `citation_ready_claims`
- `citation_blocked_claims`
- `claim_grounding_status`
- `citation_readiness`
- `public_claim_readiness`
- `recommended_answer_action`
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

## 4. Claim grounding statuses

- `grounded`
- `partially_grounded`
- `unsupported`
- `contradicted`
- `stale_support`
- `access_restricted`
- `poison_quarantined`
- `citation_not_ready`
- `unknown_status`

---

## 5. Citation readiness statuses

- `citation_ready`
- `citation_ready_with_caveat`
- `citation_blocked_access`
- `citation_blocked_poison`
- `citation_blocked_unsupported`
- `citation_blocked_contradicted`
- `citation_blocked_stale`
- `citation_not_required`
- `unknown_citation_status`

---

## 6. Recommended answer actions

- `answer_with_citations`
- `answer_with_caveats`
- `ask_for_source`
- `ask_clarifying_question`
- `remove_unsupported_claim`
- `disclose_contradiction`
- `downgrade_confidence`
- `refuse_public_claim`
- `block_answer`
- `unknown_action`

---

## 7. Grounding rules

1. Do not hallucinate citations.
2. Do not cite inaccessible private sources in public answers.
3. Do not cite poisoned sources as support.
4. Do not hide contradictions.
5. Stale support requires caveat or downgrade.
6. Unsupported claims should be removed, marked, or answered with uncertainty.
7. Source Evidence Graph edges support claims but do not prove truth.
8. Public claims require public-safe capability maturity and owner approval later.

Grounding is a readiness gate, not a truth guarantee.

---

## 8. Source Evidence Graph relationship

Use:

- source nodes
- claim nodes
- citation nodes
- `supports` / `contradicts` / `invalidates` edges
- freshness metadata
- poison/access metadata

The graph is the representation layer. Claim grounding is the answer-readiness layer for claims.

---

## 9. RAG routing relationship

RAG routing decides where evidence should come from.

Claim grounding decides whether retrieved or graph evidence is enough to support answer claims.

Routing selects the evidence path. Grounding evaluates claim readiness.

---

## 10. NAIE relationship

NAIE should reject unsupported candidates before or during grounding.

Claim grounding should expose:

- rejected claims
- missing evidence
- contradictions
- next-checks

NAIE consumes the grounding outcome; it does not override unsupported evidence.

---

## 11. Public claim relationship

Public claims require stricter handling:

- public-safe maturity
- supported claim status
- no access-restricted evidence
- no poison quarantine
- no unresolved contradiction
- owner/operator approval later

This layer does not authorize public claims.

---

## 12. Initial examples

1. Simple grounded factual claim with citation-ready support.
2. Claim supported only by stale source, requiring caveat.
3. Claim contradicted by two sources, requiring disclosure.
4. Unsupported claim removed from answer.
5. Access-restricted source blocks public citation.
6. Poison-quarantined source blocks citation.
7. Energy recommendation claim downgraded due stale signal.
8. LLM candidate claim rejected due no source edge.
9. Public website claim blocked because capability not public_safe.
10. Answer allowed with caveat because citation not required for general reasoning.

---

## 13. Future helper design

Future helper:

`weslr/inline_citation_claim_grounding_layer.py`

Future APIs:

- `build_claim_grounding_packet_v1(...)`
- `evaluate_claim_grounding_v1(packet)`
- `evaluate_citation_readiness_v1(packet)`
- `validate_claim_grounding_packet_v1(packet)`
- `summarize_claim_grounding_packet_v1(packet)`
- `to_claim_grounding_json_safe_v1(value)`
- `build_initial_claim_grounding_examples_v1()`

Future helper posture:

- metadata-only
- deterministic
- fail-closed
- no raw retrieval payloads
- no claim authority
- no public-answer authority

---

## 14. Future implementation strategy

Recommended phases:

1. metadata-only grounding packet builder
2. synthetic examples
3. validation helper
4. unsupported claim detector
5. contradiction / caveat summarizer
6. citation readiness evaluator
7. Source Evidence Graph integration
8. final answer assembly boundary design
9. public claim lifecycle design later

---

## 15. Boundaries and non-claims

This design does not:

- implement citations
- retrieve documents
- call web/search
- call models/providers
- assemble final answers
- write memory
- write `.weslr`
- authorize public claims
- claim hallucination elimination
- claim proof, truth, AGI, consciousness, sentience, Turing success, security certification, public readiness, or production readiness

---

## 16. Recommended next lane

Recommended next lane:

`DESIGN_WESLR_DOCUMENT_ACCESS_CONTROL_AND_PII_SCRUBBING_BOUNDARY_V1`

Preserve:

`IMPLEMENT_WESLR_RAG_QUERY_ROUTING_AND_RETRIEVAL_BOUNDARY_V1`
`IMPLEMENT_WESLR_INLINE_CITATION_AND_CLAIM_GROUNDING_LAYER_V1`

---

## 17. Final judgment

**inline_citation_claim_grounding_design_ready_for_document_access_pii_boundary**
