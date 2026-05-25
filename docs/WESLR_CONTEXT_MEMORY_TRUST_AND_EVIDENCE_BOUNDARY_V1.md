# WESLR Context Memory Trust And Evidence Boundary V1

## Status

- Design label: `DESIGN_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_V1`
- Lane status: design-only
- Scope: context, memory, evidence, provenance, and trust boundary before candidate response formation or real-text conversation testing
- Runtime status: no runtime wiring
- Chat status: no chat/user-facing behavior changes
- Implementation status: no helpers, source files, tests, runners, scoring, judging, provider/model/search/advisor integrations, or `.weslr` IO implemented
- Execution status: no Cognitive Gym, challenge, engine, candidate response formation, conversation, or real-text reasoning execution
- Claim status: no final answers, public/final/proof/open-problem/scientific/official claims, product-readiness claims, benchmark/Turing/intelligence/certification/consciousness claims, or public release claims
- Authority status: no authority grants

This document defines how WESLR should treat context, memory, evidence, provenance, and trust before candidate response formation or real-text conversation testing. It is design-only. It creates no implementation, modifies no runtime path, executes no reasoning engine, calls no provider/model/search/advisor, reads/writes no `.weslr` state, changes no `weslr/chat_responder.py`, creates no final answer, and grants no authority.

## 1. Purpose

WESLR needs a boundary layer that decides which context may influence reasoning, what authority each source has, how evidence is separated from memory and assumptions, and when uncertainty or external validation is required.

The purpose of this boundary is to:

- prevent context and memory from being treated as automatic truth
- preserve source provenance before candidate response formation
- distinguish observed evidence, user-provided facts, explicit memory, inferred memory, repo context, external evidence, and model-generated assumptions
- prevent stale, private, ambiguous, or conflicting context from becoming unsupported public claims
- define trust labels and evidence rules for future helper design
- establish when WESLR should ask for clarification, search, require external evidence, or refuse certainty
- feed future candidate response formation with bounded metadata rather than final answer text
- preserve denied-authority fields and claim-ladder discipline

## 2. Non-Goals

This design does not:

- implement a context/memory/evidence helper
- implement memory retrieval, search, provider calls, or evidence gathering
- implement candidate response formation
- implement final response assembly
- implement or modify `weslr/chat_responder.py`
- execute real-text conversation testing
- read or write `.weslr`
- call providers/models/search/advisors
- create scoring or judging
- create final answers, reply text, answer drafts, or user-facing output
- create public/final/proof/open-problem/scientific/official claims
- certify intelligence, consciousness, Turing-test performance, product readiness, or benchmark readiness
- grant authority for runtime wiring or future implementation

## 3. Relationship To Reasoning Substrate Map

This design follows:

- `docs/WESLR_REASONING_SUBSTRATE_MAP_V1.md`
- `docs/WESLR_REASONING_SUBSTRATE_MAP_REVIEW_V1.md`

The reasoning substrate map identified `context/memory trust + evidence boundary` as the strongest prerequisite before more implementation or real-text conversation testing. It also confirmed that candidate response formation and response-facing authority/claim checkpoints must come after reliable context, memory, evidence, and provenance boundaries.

This document fills that next design slot. It does not replace the broader reasoning substrate map. It narrows one layer: how trusted context and evidence metadata should be shaped before WESLR forms candidate responses.

## 4. Why Separation Is Required Before Real-Text Conversation Testing

Real-text conversation introduces mixed-source material:

- direct user instructions
- quoted or untrusted text
- prior conversation turns
- memory files or long-term records
- repo documentation
- tool outputs
- external sources
- model assumptions

If these are not separated, WESLR may:

- treat quoted content as instruction
- treat stale memory as current fact
- treat inferred memory as user-confirmed truth
- treat repo context as external evidence
- treat model-generated assumptions as observations
- leak private or raw memory into public answers
- smooth over contradictions instead of surfacing them
- cite sources that do not support a claim
- make public/final/official claims without validation

Therefore, context, memory, evidence, provenance, and trust must be separated before candidate response formation and before any shadow real-text conversation testing.

## 5. Context Source Categories

Future helpers should distinguish at least these source categories.

### 5.1 Current User Turn

Definition: the latest user-provided request, instruction, problem statement, or clarification.

Default trust: high for intent/request metadata, bounded for factual claims.

Rules:

- Treat as the primary source of task intent unless it conflicts with safety, authority, or higher-priority context.
- Separate user instructions from quoted/untrusted material inside the turn.
- User-stated facts may be used as user-provided claims, not automatically as verified external evidence.

### 5.2 Conversation History

Definition: previous dialogue turns in the active conversation/session.

Default trust: medium for local continuity, lower when stale, ambiguous, contradicted, or from untrusted quoted content.

Rules:

- Use for continuity and disambiguation.
- Do not treat as durable truth unless confirmed by explicit memory, repo state, or external evidence.
- Mark conflicts with the current user turn.

### 5.3 Uploaded / User-Provided Material

Definition: files, pasted text, images, PDFs, datasets, logs, or other material provided by the user.

Default trust: medium-high for what the material contains; variable for whether the content is true.

Rules:

- Preserve file/source labels and extraction limitations.
- Treat content as user-provided material, not independently verified evidence unless validated.
- Handle sensitive/private material with boundary labels before any public answer claim.

### 5.4 Explicit Memory

Definition: facts, preferences, project records, decisions, or instructions intentionally stored as memory or context records.

Default trust: medium for relevance and continuity; not automatic truth.

Rules:

- Memory is relevance input, not automatic truth.
- Explicit memory can guide what to inspect, ask, or verify.
- Stale memory needs uncertainty and may require refresh.
- Sensitive/private memory requires boundary handling and channel-appropriate use.

### 5.5 Inferred Memory

Definition: inferred preferences, patterns, assumptions, or reconstructed state not explicitly provided as a durable fact by the user.

Default trust: low-medium.

Rules:

- Inferred memory must be lower authority than explicit user-provided facts.
- Mark as inferred, not observed.
- Do not use inferred memory as basis for public/final factual claims.
- Ask clarification when inferred memory is important and uncertain.

### 5.6 Repo / Context Docs

Definition: repository files, project documentation, AGENTS/IDENTITY/context files, design docs, review docs, tests, source files, and commit metadata.

Default trust: high for repo-local state when directly inspected; medium for intended design/claims inside docs.

Rules:

- Direct file inspection is evidence of file contents, not automatic proof that the design is correct or implemented.
- Distinguish design docs, review docs, implementation files, tests, release gates, and runtime behavior.
- Do not infer runtime authorization from documentation unless an explicit reviewed lane grants it.

### 5.7 External Evidence

Definition: search results, official docs, websites, papers, APIs, external databases, or third-party references.

Default trust: variable; requires source quality and freshness labels.

Rules:

- External evidence must include provenance labels.
- Search snippets alone should not be treated as verified evidence for high-stakes claims.
- Official/vendor/primary sources are higher trust than secondary commentary.
- External evidence may be required for current-world facts, scientific/legal/medical/public claims, or claims outside repo context.

### 5.8 Model-Generated Assumptions

Definition: assumptions, guesses, completions, inferred facts, synthesized explanations, or proposed causal links generated by a model.

Default trust: low until checked against evidence.

Rules:

- Model-generated assumptions are hypotheses, not observations.
- They must not become citations, provenance, public claims, or factual certainty.
- They may guide questions, candidate structures, or verification plans.

## 6. Trust Levels

Future helpers should use explicit trust levels. Suggested labels:

| Trust label | Meaning | Allowed use |
|---|---|---|
| `direct_observation_high_trust` | Directly inspected local file/tool/output state | May support internal factual statements about inspected state, still with provenance |
| `explicit_user_claim` | Current user directly states something | May support user-intent and user-provided-fact metadata; not external verification |
| `user_provided_material` | Content provided by user/upload/file | May support source-content observations with provenance; truth may need validation |
| `repo_context_observed` | Directly inspected repo/context file content | May support repo-state observations; not runtime authority by itself |
| `external_primary_evidence` | Official/primary external source | May support factual claims when fresh and relevant, subject to domain risk |
| `external_secondary_evidence` | Secondary source or commentary | Lower support; often needs corroboration |
| `conversation_continuity` | Active-session prior turns | Supports continuity, not durable truth by itself |
| `explicit_memory_relevance` | Stored explicit memory | Supports relevance and continuity; needs freshness/uncertainty |
| `inferred_memory_low_authority` | Inferred stored context or pattern | Only hypothesis/relevance; ask or verify before depending on it |
| `model_assumption_unverified` | Model-generated assumption | Cannot support factual claims without evidence |
| `conflicted_or_stale` | Source conflicts or may be outdated | Must be marked uncertain or resolved before claims |
| `blocked_private_or_sensitive` | Sensitive/private content boundary applies | Must not leak raw content or be used publicly without authorization |

Trust labels are metadata only. They are not scores, judge decisions, official evaluation evidence, public proof, or runtime authority.

## 7. Evidence / Provenance Rules

Future helpers should preserve these evidence/provenance rules:

1. Every meaningful factual claim candidate must have a provenance label.
2. Observed file/tool state must identify the source path, command/tool family, timestamp/commit when relevant, and whether the observation is direct or inferred.
3. User-provided claims must remain labeled as user-provided unless independently verified.
4. Memory must be labeled as memory, not direct evidence of current reality.
5. Inferred memory must be labeled as inferred and lower authority than explicit user-provided facts.
6. External evidence must record source type, freshness, and whether it is primary or secondary.
7. Model-generated assumptions must never be used as citations or source provenance.
8. Missing provenance must block certainty and may block candidate response formation for high-stakes claims.
9. Conflicting provenance must be preserved, not silently merged.
10. Safe public claims require sufficient evidence plus the appropriate authorization level.

## 8. Memory Use Rules

### 8.1 Memory Is Relevance Input, Not Automatic Truth

Memory can suggest what matters, what to inspect, what the user prefers, or what prior decisions existed. It does not by itself prove current repo state, current world facts, implementation status, legal/scientific truth, or runtime authorization.

### 8.2 Stale Memory Needs Uncertainty

Memory must carry freshness or uncertainty labels when time-sensitive. Stale memory should route to verification, clarification, or cautious wording rather than certainty.

### 8.3 Sensitive / Private Memory Requires Boundary Handling

Sensitive/private memory must not be copied into public answers or wrong channels. Future helpers should mark:

- `sensitive_memory_present`
- `private_context_boundary_required`
- `raw_content_not_public`
- `summary_only_allowed`
- `requires_user_authorization_for_disclosure`

### 8.4 Inferred Memory Has Lower Authority

Inferred memory must be treated as hypothesis or preference signal. It must be lower authority than explicit user-provided facts, direct observations, and reviewed repo state. If important to the answer, it should trigger clarification or verification.

## 9. Context Conflict Handling

When sources conflict, future helpers should:

1. Preserve both source labels and the conflict label.
2. Prefer current direct observations over stale memory for mutable facts.
3. Prefer explicit current user correction over inferred memory.
4. Prefer primary external evidence over secondary commentary for external facts.
5. Treat repo implementation files/tests as stronger evidence of implementation than design docs.
6. Treat design/review docs as stronger evidence of intended boundary than implementation status.
7. Avoid resolving conflicts by unsupported assertion.
8. Ask for clarification or require verification when the conflict affects the requested output.

Suggested conflict labels:

- `current_user_vs_memory_conflict`
- `repo_observation_vs_memory_conflict`
- `design_doc_vs_implementation_conflict`
- `external_source_conflict`
- `conversation_history_conflict`
- `stale_context_conflict`
- `private_context_conflict`

## 10. When To Ask For Clarification

WESLR should ask for clarification when:

- user intent is ambiguous and materially affects the response
- a requested action depends on unstated authorization
- inferred memory would be necessary but uncertain
- context sources conflict and no safe default exists
- private/sensitive context might need disclosure
- the scope could cross runtime, public claim, provider/search, `.weslr`, or authority boundaries
- the user asks for current factual certainty but only stale or memory-based context is available

Clarification should be narrow and decision-oriented.

## 11. When To Search Or Require External Evidence

External evidence or search should be required or recommended when:

- the claim concerns mutable current-world facts
- legal/medical/scientific/financial/public claims are involved
- repo-local context is insufficient for an external-world assertion
- memory or conversation history is stale
- source conflicts cannot be resolved internally
- a public/final/official claim would depend on evidence outside WESLR's repo
- external validation is required by the claim ladder

This design does not authorize provider/model/search/advisor calls. It only defines when a future authorized lane should require them.

## 12. When To Refuse To Claim Certainty

WESLR should refuse certainty when:

- provenance is missing
- the only support is memory, inferred memory, or model assumption
- source conflict remains unresolved
- evidence is stale or secondary for a high-stakes claim
- the claim is public/final/proof/open-problem/scientific/official and lacks external validation
- the claim would imply product readiness, benchmark performance, intelligence certification, Turing success, consciousness evidence, or runtime authority without a reviewed authorization lane

Refusing certainty may still allow a bounded statement such as `based on inspected repo context`, `user-provided claim`, `unverified memory`, `hypothesis`, or `needs external validation`.

## 13. Boundary Between Internal Context And Public Answer Claims

Internal context can guide reasoning. Public answer claims require stricter evidence and authority.

- Internal observation is not public claim.
- Memory relevance is not verified fact.
- Inferred memory is not user confirmation.
- Candidate response metadata is not final answer text.
- Safe Markdown metadata is not user-facing answer prose.
- JSON-safe metadata is not a reply payload.
- Validation pass is not product readiness, official evaluation, proof, or runtime authorization.

Future helpers must preserve the claim ladder:

1. `internal_observation`
2. `internal_hypothesis`
3. `candidate_structure`
4. `reviewed_candidate`
5. `externally_checked_candidate`
6. `validated_result`
7. `public_claim`

WESLR may not skip levels.

## 14. How This Feeds Candidate Response Formation Later

Future candidate response formation should consume context/evidence metadata, not raw unmanaged context.

Expected inputs to later candidate response formation:

- interpreted user intent labels
- allowed context source records
- trust labels
- evidence/provenance records
- memory relevance records
- stale/conflict/uncertainty labels
- private/sensitive boundary labels
- clarification/search/external-validation requirements
- blocked reason labels
- denied authority fields

Candidate response formation should not create final user-facing text until a later separately authorized safe response assembly lane exists.

## 15. Safe Metadata Shape For Future Helpers

Future helper metadata may use a shape like:

```yaml
schema: WESLR_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_V1
boundary_status: design_only
input_context:
  current_user_turn: []
  conversation_history: []
  uploaded_or_user_provided_material: []
  explicit_memory: []
  inferred_memory: []
  repo_context_docs: []
  external_evidence: []
  model_generated_assumptions: []
trust_records:
  - source_id: example_source
    source_category: current_user_turn
    trust_label: explicit_user_claim
    freshness_label: current
    sensitivity_label: non_sensitive
    provenance_label: user_turn
    authority_limit: not_verified_external_evidence
memory_records:
  - memory_id: example_memory
    memory_kind: explicit_memory
    relevance_label: relevant
    freshness_label: unknown_or_stale
    authority_limit: relevance_input_not_truth
    sensitivity_label: boundary_check_required
evidence_records:
  - evidence_id: example_evidence
    source_category: repo_context_docs
    provenance_label: direct_file_observation
    observation_label: file_contains_claim
    claim_support_limit: repo_state_only
conflict_records: []
uncertainty_records: []
clarification_requirements: []
external_evidence_requirements: []
blocked_reason_labels: []
denied_authority_fields:
  runtime_authority: false
  chat_authority: false
  final_answer_authority: false
  proof_claim_authority: false
  open_problem_solved_claim_authority: false
  scientific_claim_authority: false
  official_benchmark_authority: false
  turing_test_claim_authority: false
  intelligence_certification_authority: false
  consciousness_claim_authority: false
  provider_call_authority: false
  search_call_authority: false
  advisor_call_authority: false
  model_call_authority: false
  persistence_authority: false
  scoring_authority: false
  judge_authority: false
  public_release_authority: false
next_allowed_steps: []
```

This shape is illustrative only. It is not implemented and does not authorize helper creation.

## 16. Blocked Behavior

Future lanes must block:

- unsupported source claims
- invented citations/provenance
- treating memory as verified evidence
- using stale context as current fact
- treating inferred memory as explicit user-provided fact
- treating model-generated assumptions as observations
- treating design docs as implementation evidence
- treating validation pass as product/runtime/official authority
- leaking private/raw/sensitive content
- copying raw private prompts or hidden context into public outputs
- public/final/proof/open-problem/scientific/official claims without validation
- provider/model/search/advisor calls without explicit authorization
- `.weslr` reads/writes without explicit authorization
- scoring/judging without explicit authorization
- runtime/chat wiring or `weslr/chat_responder.py` edits without explicit authorization
- final answer or user-facing output generation from this boundary

## 17. Denied Authority Fields

All denied authority fields remain false:

```yaml
runtime_authority: false
chat_authority: false
final_answer_authority: false
proof_claim_authority: false
open_problem_solved_claim_authority: false
scientific_claim_authority: false
official_benchmark_authority: false
turing_test_claim_authority: false
intelligence_certification_authority: false
consciousness_claim_authority: false
provider_call_authority: false
search_call_authority: false
advisor_call_authority: false
model_call_authority: false
persistence_authority: false
scoring_authority: false
judge_authority: false
public_release_authority: false
```

False denied authority fields are not placeholders for implicit permission. A false value means authority is denied unless a future reviewed lane explicitly grants it.

## 18. Gaps And Risks

No blocking design gap is intentionally left for this boundary. The boundary is sufficient for review as a design artifact.

Known future gaps:

- no helper implementation exists
- no tests exist for future helper metadata
- no candidate response formation substrate exists yet
- no response-facing authority/claim checkpoint exists yet
- no safe final response assembly shadow boundary exists yet
- no real-text conversation testing is authorized

Risks if skipped:

- memory becomes unsupported fact
- private context leaks
- stale context becomes current claim
- source conflicts are hidden
- model assumptions become fake evidence
- candidate responses inherit unsupported provenance
- runtime/chat wiring occurs before authority gates exist

## 19. Future Implementation / Review Sequence

Recommended future sequence, each lane separately authorized:

1. `REVIEW_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_V1`
   - Review this design only.
   - Do not implement helpers, tests, runners, runtime, chat behavior, provider/search/advisor calls, or `.weslr` IO.
2. `AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_V1`
   - Align OCC-facing context if review passes.
3. `DESIGN_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1`
   - Design how interpreted input, trusted context, evidence/provenance, uncertainty, conflicts, and authority limits feed candidate response metadata.
4. `REVIEW_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1`
   - Review before implementation.
5. `DESIGN_AUTHORITY_CLAIM_CHECKPOINT_FOR_RESPONSE_FORMATION_V1`
   - Define response-facing claim and authority checkpoint.
6. `DESIGN_SAFE_FINAL_RESPONSE_ASSEMBLY_SHADOW_BOUNDARY_V1`
   - Only after prior review; still no live runtime wiring.
7. Consider future helper implementation only if separately approved and scoped.

No future step may skip review, provenance, validation, or authority boundaries.

## 20. Direction Check

- **A — continue next narrow helper lane**: viable if the operator deliberately prioritizes one more helper, but not preferred from this boundary. Risk: more helper sprawl before candidate response integration.
- **B — pause/review direction**: viable if the operator wants to reassess whether WESLR should continue architecture design or shift toward another reviewed stream.
- **C — design candidate response formation substrate next**: recommended after this boundary is reviewed and context-aligned. Candidate response formation is the next response-facing layer that should consume context/memory/evidence metadata before safe final response assembly or shadow real-text testing.

## 21. Safety Boundary Summary

This design preserves:

- no runtime/chat wiring
- no `weslr/chat_responder.py` edits
- no helper/source/test implementation
- no provider/model/search/advisor calls
- no `.weslr` IO
- no scoring/judging
- no challenge/engine/conversation execution
- no candidate response formation execution
- no final-answer/reply/user-facing output
- no public/final/proof/open-problem/scientific/official claims
- no product-readiness, benchmark, Turing, intelligence, certification, or consciousness claims
- no public release text
- no authority grants

All future lanes remain separately authorized and reviewed. Validation pass is not runtime authority, answer authority, product readiness, official evaluation, proof, certification, consciousness evidence, or public-claim permission.
