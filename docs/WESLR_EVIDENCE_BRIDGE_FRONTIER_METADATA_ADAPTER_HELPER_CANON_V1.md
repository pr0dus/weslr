# WESLR Evidence Bridge Frontier Metadata Adapter Helper Canon V1

APPROVE_WESLR_EVIDENCE_BRIDGE_FRONTIER_METADATA_ADAPTER_HELPER_CANON_V1_ONLY

evidence_bridge_frontier_metadata_adapter_helpers

## 1. Canon Status

The evidence bridge Frontier metadata adapter helpers are canonized as:

- helper_ready
- metadata_alignment_ready
- provenance_metadata_ready
- non_executing
- non_runtime_wired
- non_searching
- non_authoritative
- redacted_count_only

They are not:

- runtime-wired
- search-ready
- answer-authority-ready
- source-registry-ready
- certification-ready

They are metadata helper surfaces only. They do not authorize runtime output replacement, search execution, source authority, scoring, certification, or provenance registry writes.

## 2. Helper Chain

Implemented helper module:

- `weslr/evidence_bridge_frontier_metadata.py`

Implemented helpers:

- `build_frontier_evidence_bridge_alignment_v1`
- `validate_frontier_evidence_bridge_alignment_v1`
- `build_output_provenance_for_evidence_bridge_v1`
- `validate_output_provenance_for_evidence_bridge_v1`
- `to_frontier_evidence_bridge_metadata_json_safe_v1`
- `summarize_frontier_evidence_bridge_alignment_v1`
- `render_frontier_evidence_bridge_alignment_markdown_v1`

Focused test module:

- `weslr/tests/test_evidence_bridge_frontier_metadata_v1.py`

## 3. Existing Bridge Reuse

The adapter reuses the existing evidence bridge metadata shape. It does not duplicate or replace:

- `evidence_needed_detector`
- `evidence_pipeline`
- `evidence_packet_builder`
- `evidence_answer_builder`
- `evidence_chat_bridge`
- `maybe_answer_with_evidence`
- `output_provenance` schema
- `provenance_source_registry` schema

The adapter does not create a new evidence detector, new evidence pipeline, new answer builder, new evidence bridge, or new provenance layer.

## 4. Architecture Rule

Canon architecture rule:

- `main.py` `/chat` and staging remain the only current layers allowed to replace fallback/generic chat output with evidence bridge output.
- `chat_responder.py` remains search-free.
- Frontier limited/ordinary slices do not trigger search.
- Frontier metadata must not claim evidence was used unless existing `_evidence_metadata.evidence_used == true`.
- The adapter is not live-wired yet.

Any later wiring must be metadata-only unless separately approved by doctrine, tests, release gate, and owner review.

## 5. Plain-Language Meaning

The adapter translates existing evidence bridge metadata into a Frontier-compatible, redacted metadata shape.

It does not search.
It does not answer.
It does not call a model.
It does not call an advisor.
It does not prove truth.
It does not write memory, truth, queue, or provenance registry state.
It does not make sources authoritative.
It does not change runtime behavior.

## 6. Mapping Rules

Safe mapping rules:

- `evidence_used` mirrors input metadata.
- `authority` copies a safe scalar, usually `external_evidence_unverified`.
- `truth_status` must remain `unverified`.
- `automatic_truth_write` is always `false`.
- `source_count` is count-only.
- `source_urls_present` is boolean-only.
- `source_urls` are not copied into alignment metadata.
- raw source text is not copied.
- `source_classes` remains empty unless a later approved derivation-only rule exists.
- `model_calls = false`.
- `advisor_calls = false`.
- `memory_writes = false`.
- `truth_writes = false`.
- `raw_text_stored = false`.
- `safe_to_wire_runtime = false`.

No raw private text, raw source text, source URLs, hidden prompts, protected material, answer keys, benchmark items, official score claims, certification claims, or invented source IDs may be introduced into the alignment object.

## 7. Output Provenance Rule

Output provenance from this helper is metadata-only.

Required posture:

- `generated_by` is `evidence_chat_bridge`.
- `source_modules` are existing evidence modules only.
- `truth_class` is `unverified`.
- `authority_level` is `unknown` because no approved external-evidence authority enum exists yet.
- `llm_assisted = false`.
- `advisor_assisted = false`.
- `memory_write_performed = false`.
- `queue_write_performed = false`.
- `runtime_action_performed = false`.

The output provenance helper does not register sources, elevate source authority, persist provenance entries, or mutate runtime behavior.

## 8. Classification Summary Hardening Rule

`classification_summary.reason` must remain classifier-internal explanatory metadata only.

It must not contain:

- raw user prompts
- raw source text
- protected material
- answer keys
- hidden prompts
- private text
- benchmark items
- official score/IQ/certification claims

If any future classifier begins embedding raw prompt/source text in `reason`, this adapter must redact or omit that field before runtime metadata wiring.

## 9. Source Class Rule

`source_classes` must remain empty unless a later approved implementation derives classes strictly from safe packet/source metadata with tests.

Rules:

- no invented source classes
- no invented source IDs
- no source registry writes
- no source authority elevation
- no live source registration

The provenance source registry remains schema/helper-level unless separately approved.

## 10. Known Hardening Notes

Non-blocking future hardening:

- Add a dedicated regression for `evidence_used=false`.
- Consider stricter boolean parsing instead of truthy string handling.
- Expand validation if future `source_classes` are introduced.
- Consider authority enum extension only through separate approval.

These notes do not block helper canonization because the current helper surface is not runtime-wired and current evidence bridge metadata emits safe booleans and classifier-internal reasons.

## 11. Allowed Next Steps

Allowed next steps:

- review this canon
- add `evidence_used=false` regression test
- refine boolean parsing
- design metadata-only outer `/chat` wiring
- design output provenance metadata wiring
- later source display polish

## 12. Blocked Next Steps

Blocked unless separately approved:

- wire search into `chat_responder.py`
- trigger search from Frontier limited/ordinary slices
- create a new evidence pipeline
- create a new evidence bridge
- write provenance registry entries
- elevate source authority
- invent source IDs/classes
- call models/advisors
- score/certify/benchmark
- runtime replacement

## 13. Anti-Drift Rule

Any future change that interprets these helpers as search execution, runtime answer authority, source authority, registry write authority, evidence pipeline replacement, official evaluation, scoring, certification, or model/advisor authority violates this canon unless separately approved by doctrine, tests, release gate, and owner review.

## 14. Canon Safety Markers

The following markers are intentional release-gate anchors:

- helper_ready
- metadata_alignment_ready
- provenance_metadata_ready
- non_executing
- non_runtime_wired
- non_searching
- non_authoritative
- redacted_count_only
- not_runtime_wired
- not_search_ready
- not_answer_authority_ready
- not_source_registry_ready
- not_certification_ready
- model_calls = false
- advisor_call_allowed = false
- safe_to_wire_runtime = false
- registry_writes = false
