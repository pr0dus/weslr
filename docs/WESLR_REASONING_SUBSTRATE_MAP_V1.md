# WESLR Reasoning Substrate Map V1

## Status

- Design label: `DESIGN_WESLR_REASONING_SUBSTRATE_MAP_V1`
- Lane status: design-only
- Scope: broader reasoning substrate map before more engine-specific helper implementation
- Runtime status: no runtime wiring
- Chat status: no chat/user-facing behavior changes
- Implementation status: no helpers, source files, tests, runners, scoring, judging, provider/model/search/advisor integrations, or `.weslr` IO implemented
- Execution status: no Cognitive Gym, challenge, engine, conversation, or real-text reasoning execution
- Claim status: no final answers, proof claims, open-problem solution claims, scientific discovery claims, official benchmark/Turing/intelligence/certification/consciousness claims, product-readiness claims, or public release claims
- Authority status: no authority grants

This document maps the reasoning substrate WESLR needs before adding too many more engine-specific helpers or moving toward real-text conversation testing. It is design-only. It creates no implementation, modifies no runtime path, executes no reasoning engine, calls no provider/model/search/advisor, reads/writes no `.weslr` state, changes no `weslr/chat_responder.py`, creates no final answer, and grants no authority.

## 1. Purpose

WESLR's reasoning work has moved from isolated helper families toward a need for an explicit substrate map. The purpose of this map is to show how calibration, contradiction, uncertainty, memory trust, evidence, intent reconstruction, invariant mining, answer formation, and future real-text reasoning conversations should connect without becoming disconnected modules.

The map is intended to:

- identify the substrate layers needed for governed response formation
- show where existing reviewed helpers fit
- prevent engine-specific helper sprawl without integration discipline
- prevent premature runtime/chat wiring
- define which layer should precede real-text conversation testing
- preserve claim-ladder and denied-authority boundaries
- provide lane sequencing choices without automatically authorizing more implementation

## 2. Non-Goals

This design does not:

- implement a reasoning substrate
- implement any helper, engine, runner, test, adapter, artifact, or runtime path
- implement or modify `weslr/chat_responder.py`
- execute Cognitive Gym, CALIBRATION_LEDGER, UNKNOWN_ENGINE, contradiction tools, memory trust tools, answer formation tools, or any conversation test
- call providers/models/search/advisors
- read or write `.weslr`
- create scoring or judging
- generate final answers or reply text
- create proof/open-problem/scientific/official claims
- certify intelligence, consciousness, Turing-test performance, product readiness, or benchmark readiness
- grant authority or permission for runtime wiring
- authorize real user-facing conversation behavior

## 3. Current Implemented / Reviewed Substrate Pieces

### 3.1 Exploratory Problem Work Boundary

`docs/WESLR_EXPLORATORY_PROBLEM_WORK_BOUNDARY_V1.md` defines the general boundary: safety restrictions block unsupported claims, authority escalation, public/final output, runtime overreach, scoring/judging, provider calls, `.weslr` IO, and fake achievements. They do not permanently ban future authorized internal cognition, hypothesis work, invalidation, failed attempts, toy models, counterexample search, correction loops, or bounded exploratory reports.

### 3.2 Cognitive Gym Exploratory Case Protocol

`docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_V1.md` defines the shared metadata/report philosophy for future exploratory engines: observations, hypotheses, candidate structures, attempted approaches, failed paths, invalidation signals, predictions/branch labels, confidence, uncertainty, reveal/outcome, correction, compressed lesson, boundary status, denied authority fields, validation status, and next allowed steps.

### 3.3 Shared Cognitive Gym Exploratory Case Helpers

`weslr/cognitive_gym_exploratory_case.py` is implemented and reviewed as shared helper-only metadata infrastructure. It builds, validates, summarizes, renders safe internal Markdown, and converts exploratory case metadata to JSON-safe structures while preserving validation-before-rendering, blocked metadata behavior, false denied authority fields, and no-runtime/no-output/no-authority boundaries.

### 3.4 CALIBRATION_LEDGER Exploratory Helpers

`weslr/calibration_ledger_exploratory_helpers.py` is implemented and reviewed as the first one-family-only engine-specific helper layer. It maps calibration metadata into the shared Cognitive Gym exploratory case shape and exposes:

- `build_calibration_ledger_exploratory_case_v1`
- `validate_calibration_ledger_exploratory_case_v1`
- `summarize_calibration_ledger_exploratory_case_v1`
- `render_calibration_ledger_exploratory_case_markdown_v1`
- `to_calibration_ledger_exploratory_case_json_safe_v1`

It remains helper-only, metadata-only, `CALIBRATION_LEDGER`-only, deterministic, import-safe, side-effect-free, in-memory, validation-before-rendering, JSON-safe, and blocked-metadata preserving.

### 3.5 UNKNOWN ENGINE / Result Artifact Lineage

UNKNOWN ENGINE helpers and result artifact helpers exist as internal metadata/review structures. They are useful as precedent for strict denied-authority fields, JSON-safe conversion, safe Markdown, result artifacts, and boundary review chains, but they are not runtime execution, prediction authority, future-certainty authority, final-answer output, or official evaluation evidence.

## 4. Where CALIBRATION_LEDGER Fits

`CALIBRATION_LEDGER` is the uncertainty-feedback layer. It should not decide answers. It should not score outputs. It should not judge intelligence. It should record bounded calibration metadata around predicted branch labels, confidence labels, uncertainty labels, observed outcome labels, mismatch labels, correction labels, compressed lesson labels, and calibration status.

In the substrate, `CALIBRATION_LEDGER` sits after hypothesis/branch formation and after reveal/outcome availability. It helps WESLR learn from mismatch without turning that learning into public claims or runtime authority.

Its relationship to other layers:

- receives branch/confidence/uncertainty labels from candidate reasoning layers
- receives reveal/outcome labels only when a bounded lane provides them
- emits correction and compressed lesson metadata
- informs future confidence discipline
- does not generate final responses
- does not evaluate official performance
- does not authorize conversation wiring

## 5. Proposed Reasoning Substrate Layers

### 5.1 Input Interpretation Layer

Purpose: turn incoming task/user/problem material into safe internal intent and problem metadata.

Responsibilities:

- identify task type, requested output, constraints, and safety boundaries
- distinguish user intent from quoted/untrusted content
- preserve input provenance labels
- identify when input is insufficient, unsafe, private, protected, or outside authorization

Status: partially designed elsewhere through response formation and exploratory case protocol concepts; not yet a unified substrate implementation.

Must precede real-text conversation testing: yes. WESLR cannot reason well over live text without reliable input interpretation and untrusted-content boundaries.

### 5.2 Context And Memory Trust Layer

Purpose: decide what contextual/memory material may influence reasoning and with what trust label.

Responsibilities:

- distinguish long-term memory, recent context, repo context, user-provided claims, tool observations, and untrusted quoted content
- attach provenance and freshness labels
- mark conflicts, stale context, and missing context
- prevent private memory leakage into wrong channels

Status: conceptually present in OCC context and memory discipline; missing as explicit WESLR reasoning substrate helper family.

Useful future helper: `MEMORY_TRUST_ENGINE`, because real-text conversation testing requires context reliability before answer formation.

### 5.3 Evidence / Provenance Boundary Layer

Purpose: separate observations from hypotheses, claims, inferred state, and authority.

Responsibilities:

- record what was directly observed
- record source/provenance labels
- prevent provider/search/advisor outputs from being treated as authorized truth unless the lane allows them
- preserve evidence boundaries before response formation

Status: partially present in exploratory case protocol and UNKNOWN ENGINE artifact lineage; missing as a dedicated response-facing substrate map.

Useful future helper: evidence/provenance adapter before real-text response testing.

### 5.4 Uncertainty And Calibration Layer

Purpose: represent uncertainty and learn from mismatch without converting confidence into authority.

Responsibilities:

- attach confidence labels and uncertainty labels
- record predicted branch labels
- record observed outcome labels
- record mismatch/correction/lesson labels
- update internal calibration metadata in future authorized lanes

Status: `CALIBRATION_LEDGER` helpers implemented and reviewed as metadata-only.

Should come before real-text conversation testing: yes, but only as metadata discipline. It does not by itself make conversation safe.

### 5.5 Contradiction Detection Layer

Purpose: identify contradictions among input, context, memory, hypotheses, candidate structures, and proposed answer branches.

Responsibilities:

- detect direct contradiction labels
- preserve conflicting evidence/provenance labels
- route contradictions to candidate revision or blocked status
- avoid resolving contradictions by unsupported assertion

Status: not implemented in this substrate. It is a high-value next helper family because contradiction handling is central to reasoning quality.

Useful future helper: `CONTRADICTION_FURNACE`, preferably design first, then helper implementation only after substrate review.

### 5.6 Blindspot Detection Layer

Purpose: identify missing assumptions, unexamined alternatives, unavailable evidence, and hidden uncertainty.

Responsibilities:

- surface missing context and unchecked premise labels
- identify overconfident branch narrowing
- flag untested dependency chains
- feed uncertainty and candidate-response revision

Status: not implemented.

Useful future helper: `BLINDSPOT_ENGINE`, but it should likely come after contradiction/evidence mapping so it has structured inputs.

### 5.7 Invariant / Pattern Mining Layer

Purpose: extract recurring structural patterns and stable constraints across cases without claiming proof or official generalization.

Responsibilities:

- collect candidate invariants
- distinguish pattern labels from proof labels
- mark counterexamples and invalidation signals
- feed candidate response formation with stable-but-not-final structure

Status: not implemented.

Useful future helper: `INVARIANT_MINER`, but it should not precede context/evidence/contradiction layers unless the operator explicitly wants exploratory structure work first.

### 5.8 Intent Reconstruction Layer

Purpose: infer what the user or problem is really asking while preserving uncertainty and avoiding hidden mind-reading authority.

Responsibilities:

- reconstruct likely intent from task/context metadata
- separate explicit request from inferred intent
- mark ambiguity and needed clarification
- prevent final-answer generation when intent is not stable enough

Status: not implemented as substrate helper.

Should come before real-text conversation testing: yes. Real conversation requires intent reconstruction or at least intent-boundary metadata.

Useful future helper: `INTENT_RECONSTRUCTION_ENGINE`, but it needs memory/evidence boundaries first.

### 5.9 Causal Trace / Failure Mode Analysis Layer

Purpose: explain why a reasoning path succeeded, failed, contradicted itself, or produced unsafe output.

Responsibilities:

- record causal path labels
- identify failure mode labels
- distinguish bug, missing context, unsafe input, overclaim, and unsupported leap
- feed correction loops and calibration

Status: not implemented.

Useful future helpers: `CAUSAL_TRACE_ENGINE` and `FAILURE_MODE_SIMULATOR`, after contradiction and calibration are established.

### 5.10 Candidate Response Formation Layer

Purpose: assemble candidate answer structures from interpreted input, trusted context, evidence, uncertainty, contradictions, blindspots, and authority constraints.

Responsibilities:

- produce candidate response metadata, not final user-facing text unless separately authorized
- track assumptions, evidence, missing context, risks, and intended response shape
- route candidate text through authority/claim checks before any safe final assembly

Status: partially represented by controlled reply/answer formation chains, but not unified with the Cognitive Gym reasoning substrate.

Must come before real-text conversation testing: yes. WESLR needs a response-facing candidate formation layer before live or shadow real-text conversation tests.

### 5.11 Authority And Claim Ladder Checks

Purpose: prevent internal metadata from becoming unauthorized public/final/official claims.

Responsibilities:

- enforce the claim ladder: internal observation → internal hypothesis → candidate structure → reviewed candidate → externally checked candidate → validated result → public claim
- preserve false denied authority fields
- block final-answer/proof/open-problem/scientific/official claims without external validation and separate authorization
- prevent benchmark/Turing/intelligence/product/consciousness claims from validation pass alone

Status: present as a design doctrine across exploratory problem work, Cognitive Gym, UNKNOWN ENGINE, and CALIBRATION_LEDGER helpers. Needs a response-facing integration checkpoint before real-text conversation testing.

### 5.12 Safe Final Response Assembly Layer

Purpose: convert reviewed candidate response metadata into safe final response text only when authorized.

Responsibilities:

- assemble answer text from validated candidate structures
- preserve uncertainty and caveats
- avoid unsafe raw content and hidden prompts
- enforce channel/privacy constraints
- ensure reply text is not proof/public/official claim unless externally validated and authorized

Status: not authorized here. This map does not wire or implement final response assembly.

Must come before live conversation; for shadow testing, a non-runtime design/review lane should define what safe final response assembly would require.

## 6. What Is Already Designed / Implemented

Already designed/reviewed:

- Exploratory problem work boundary
- Cognitive Gym exploratory case protocol
- Cognitive Gym exploratory case helper design
- First engine-specific exploratory helper boundary
- CALIBRATION_LEDGER exploratory helper design and implementation review
- UNKNOWN ENGINE metadata/result artifact boundaries and helpers
- Several controlled reply/answer formation boundary chains

Already implemented/reviewed as helper-only metadata:

- shared Cognitive Gym exploratory case helpers
- CALIBRATION_LEDGER exploratory helpers
- UNKNOWN ENGINE helper/result-artifact-related metadata helpers

Not authorized by these implementations:

- runtime/chat behavior
- provider/model/search/advisor calls
- `.weslr` IO
- real conversation execution
- scoring/judging
- challenge execution
- final-answer generation
- public/final/official claims
- authority grants

## 7. What Is Missing

Blocking substrate gaps before robust real-text conversation testing:

1. Unified input interpretation boundary for real text.
2. Explicit context and memory trust layer.
3. Evidence/provenance boundary usable by response formation.
4. Contradiction detection over candidate context/evidence.
5. Intent reconstruction with ambiguity handling.
6. Candidate response formation that consumes the above layers.
7. Authority/claim checkpoint immediately before response assembly.
8. Safe final response assembly design for shadow/non-runtime testing.

Non-blocking but important future gaps:

- blindspot detection
- invariant/pattern mining
- causal trace / failure mode analysis
- substrate-level report artifact shape
- integration map between Cognitive Gym metadata and controlled answer formation metadata

## 8. Which Layer Should Come Before Real-Text Conversation Testing

Before real-text conversation testing, WESLR should have at minimum a design/review chain for:

1. input interpretation
2. context and memory trust
3. evidence/provenance boundary
4. candidate response formation
5. authority and claim ladder checks
6. safe final response assembly

If only one layer is selected next, the strongest prerequisite is **context and memory trust plus evidence/provenance boundary**, because real-text reasoning cannot safely interpret or answer without knowing which context is trusted, stale, private, untrusted, quoted, observed, inferred, or missing.

A close second is **candidate response formation substrate design**, because helper work must eventually connect to how WESLR forms answers instead of accumulating isolated metadata modules.

## 9. Useful Next Engine-Specific Helpers

Recommended next helper candidates, if the operator chooses another narrow helper lane later:

1. `CONTRADICTION_FURNACE`
   - Why: contradiction handling is core to reasoning quality and prevents unsupported synthesis.
   - Best after: this substrate map and an evidence/provenance boundary design.

2. `MEMORY_TRUST_ENGINE`
   - Why: real-text conversation depends on safely using memory/context without leakage or stale assumptions.
   - Best after: context/memory trust design, possibly before contradiction helpers.

3. `INTENT_RECONSTRUCTION_ENGINE`
   - Why: conversation quality depends on distinguishing explicit request, inferred intent, ambiguity, and required clarification.
   - Best after: memory/evidence boundaries are mapped.

4. `BLINDSPOT_ENGINE`
   - Why: improves reasoning by finding missing assumptions and untested branches.
   - Best after: contradiction and intent layers provide structured inputs.

5. `INVARIANT_MINER`
   - Why: useful for pattern discovery and compression, but risky if introduced before evidence/claim boundaries because patterns can be overclaimed.

This design does not authorize any of these helpers. Each would require separate design, review, implementation approval, tests, and context alignment.

## 10. Risks Of Adding Too Many Helpers Without Response Integration

- Helper sprawl: many metadata modules may exist without a coherent path to answer formation.
- Boundary drift: each helper may preserve its local safety rules while the overall system lacks integration checks.
- Redundant concepts: confidence, uncertainty, evidence, correction, and blocked reasons may diverge across helpers.
- False progress: more helpers may look like cognition while not improving WESLR's actual response formation.
- Integration debt: later response wiring becomes harder if helpers do not share a substrate contract.
- Authority confusion: metadata helpers may be mistaken for runtime readiness or answer authority.

Mitigation: pause after a small number of helpers and design the response-facing substrate contract before additional families.

## 11. Risks Of Wiring Conversation Too Early

- Untrusted or quoted text may be treated as instruction.
- Private memory or context may leak into wrong outputs.
- Unvalidated candidate structures may become final answer text.
- Calibration/confidence labels may be mistaken for correctness.
- Contradictions may be smoothed over instead of surfaced.
- Provider/model/search/advisor outputs may be treated as authorized evidence without boundary review.
- `.weslr` IO or runtime state may be introduced before authority gates exist.
- Public/final/official claims may be made without external validation.
- ChatResponder changes may bypass the staged substrate discipline.

Mitigation: use shadow/design/review lanes before runtime wiring; keep `weslr/chat_responder.py` untouched until explicit owner-approved runtime lane with rollback and gated tests.

## 12. Suggested Lane Sequence After This Map

Recommended sequence if the goal is future real-text reasoning conversations:

1. `REVIEW_WESLR_REASONING_SUBSTRATE_MAP_V1`
2. `AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_REASONING_SUBSTRATE_MAP_V1`
3. `DESIGN_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_V1`
4. `REVIEW_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_V1`
5. `DESIGN_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1`
6. `REVIEW_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1`
7. `DESIGN_AUTHORITY_CLAIM_CHECKPOINT_FOR_RESPONSE_FORMATION_V1`
8. `DESIGN_SAFE_FINAL_RESPONSE_ASSEMBLY_SHADOW_BOUNDARY_V1`
9. Only after review: consider controlled shadow real-text conversation tests, still without live runtime wiring.

Alternative sequence if the goal is another narrow helper first:

1. `REVIEW_WESLR_REASONING_SUBSTRATE_MAP_V1`
2. `DESIGN_CONTRADICTION_FURNACE_EXPLORATORY_HELPERS_V1`
3. Review, implement only if separately approved, then context-align.

Recommended sequence from this map: **review this map first, then design context/memory trust plus evidence/provenance boundary before more helper implementation**.

## 13. Direction Check

- **A — continue next narrow helper lane**: viable only if the operator deliberately prioritizes one more helper. Best narrow helper candidate is `CONTRADICTION_FURNACE`; second is `MEMORY_TRUST_ENGINE`. Risk: helper sprawl without response integration.
- **B — pause/review direction**: viable if the operator wants to assess whether WESLR should continue Cognitive Gym substrate work or shift back toward response formation/runtime readiness planning.
- **C — design/update architecture further before implementation**: recommended. The next architecture design should define `DESIGN_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_V1` or a combined substrate contract before additional engine-specific helper implementation.

## 14. Safety Boundary Summary

This map preserves:

- no runtime/chat wiring
- no `weslr/chat_responder.py` edits
- no helper/source/test implementation
- no provider/model/search/advisor calls
- no `.weslr` IO
- no scoring/judging
- no challenge/engine/conversation execution
- no final-answer/reply/user-facing output
- no proof/open-problem/scientific/official claims
- no public release text
- no authority grants

All future lanes remain separately authorized and reviewed. Validation pass is not runtime authority, answer authority, product readiness, official evaluation, proof, certification, consciousness evidence, or public-claim permission.
