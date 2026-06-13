# WESLR MLCF Routing From Live SearXNG Metadata Result Helper V1

**Status:** Design only. This document defines a future helper design. It does not implement routing.

## 1. Purpose

This helper exists to convert a controlled live SearXNG metadata-only result packet into MLCF metadata-only routing packets while preserving source posture, blocking content ingestion, keeping operator review before any later evidence work, and never treating locators as proof or truth.

## 2. Input contract

The future helper accepts only a validated `controlled_live_searxng_metadata_only_result_packet` with:

- `evidence_status = metadata_only_locator_candidates`
- `authority_verdict = external_evidence_unverified`
- `raw_content_retained = False`
- `snippets_retained = False`
- `automatic_truth_write = False`
- no true authority or claim flags
- a finite result list
- a finite blocked list

## 3. Allowed input fields

Only these input fields are allowed:

- query
- title
- URL
- domain
- source engine
- engines
- rank
- score
- published date
- source class hint
- authority guess
- evidence role guess
- relevance reason
- freshness status guess
- access/license status guess
- privacy status guess
- blocked status
- locator ID

## 4. Forbidden input fields

These input fields are explicitly rejected:

- raw HTTP response body
- raw HTML
- full snippets
- page content
- source excerpts
- source summaries
- copied article text
- PDF content
- repository content
- downloaded files
- embeddings
- content hashes
- trusted/accepted evidence verdicts
- candidate membership
- final-answer content
- public claims

## 5. Future public APIs

These are future helper APIs only; no implementation is created in this lane.

- `build_mlcf_route_from_live_searxng_metadata_result_v1(packet, *, route_id=None, operator_role="owner")`
- `validate_mlcf_route_from_live_searxng_metadata_result_request_v1(request)`
- `validate_mlcf_route_from_live_searxng_metadata_result_v1(route_packet)`
- `summarize_mlcf_route_from_live_searxng_metadata_result_v1(route_packet)`
- `to_mlcf_route_from_live_searxng_metadata_result_json_safe_v1(route_packet)`
- `build_initial_mlcf_route_from_live_searxng_metadata_result_examples_v1()`

## 6. Future route packet shape

The future route packet is a metadata-only route packet and should include:

- schema version
- route id
- source result packet id or artifact reference
- query
- operator role
- routing posture
- route status
- kept locator route entries
- blocked overflow summary
- operator review requirements
- denied authority flags
- validation status
- safe summary

## 7. Kept locator route entry shape

Each kept locator route entry should include:

- original rank
- locator id
- title
- URL
- domain
- source engine
- source class posture
- authority posture
- evidence role posture
- freshness posture
- access/license posture
- privacy posture
- route action
- operator review required
- allowed next MLCF stage
- denied authority flags

Required route actions:

- `route_to_locator_metadata_candidate`
- `hold_for_operator_review`
- `block_from_routing`

## 8. Mapping rules

The mapping is deterministic and metadata-only:

- `github_repository` → `community_signal`, implementation/reference posture only
- `public_lab_or_university_artifact` → public/secondary locator metadata, operator review required
- `unknown_authority` + `unknown_authority` → hold for operator review
- `candidate_signal` remains candidate-signal posture only
- no result becomes evidence
- no result becomes truth
- no result becomes accepted evidence
- no result becomes normalized evidence

## 9. Blocked overflow rules

- `result_cap_exceeded` entries remain blocked by default
- overflow entries may be counted only as overflow metadata
- overflow entries may not be routed into MLCF
- overflow entries may not be evidence
- future larger-cap sampling requires separate owner authorization

## 10. Fail-closed validation rules

The future helper uses fail-closed validation rules and must fail closed if:

- input is not a validated live metadata result packet
- `raw_content_retained` is true
- `snippets_retained` is true when snippets are disabled
- raw response body appears
- source content appears
- source summary appears
- trusted or accepted evidence appears
- any authority or claim flag is true
- blocked status is not allowed
- blocked overflow is routed as kept
- query is missing
- locator id is missing
- URL is unsafe
- JSON-safe conversion fails

## 11. Denied authority flags

The route packet must explicitly deny:

- source ingestion authority
- raw retention authority
- final-answer authority
- public-claim authority
- discovery-claim authority
- proof-claim authority
- benchmark-claim authority
- AGI/consciousness/sentience claim authority
- runtime execution authority
- memory mutation authority
- `.weslr` IO authority
- autonomous routing authority
- external action authority
- source fetching authority

## 12. Future test plan

Future tests should cover:

- valid packet with 5 kept locators and 35 blocked overflow rows
- GitHub result maps to community signal only
- public lab/university artifact maps to secondary/public metadata only
- unknown authority holds for operator review
- overflow rows stay blocked
- raw-content flag true fails validation
- snippets-retained true fails when snippets are disabled
- any authority flag true fails validation
- trusted evidence verdict fails validation
- source summary/content field fails validation
- JSON-safe serialization
- denied authority flags remain false
- no `.weslr` IO
- no HTTP call
- no provider/model import

## 13. Future sample lane

The future sample lane should be:

`RUN_WESLR_MLCF_ROUTING_FROM_LIVE_SEARXNG_METADATA_RESULT_HELPER_SAMPLE_V1`

That future sample must:

- use the already-merged result artifact
- make zero live SearXNG calls
- make zero HTTP calls
- fetch zero source URLs
- produce metadata-only routing output
- not ingest or summarize source content
- not create evidence, truth, or claims

## 14. Non-goals

This design does not:

- implement routing
- execute routing
- read source pages
- ingest sources
- summarize sources
- judge source truth
- create evidence
- create normalized evidence
- create candidate membership
- generate final answers
- connect to runtime or public UI
- perform autonomous research

## 15. Success criteria

Success means:

- the future helper can be implemented safely
- the future route packet stays metadata-only
- kept locators are mapped to safe MLCF posture
- blocked overflow remains blocked
- no content enters MLCF
- no evidence, truth, or claim elevation occurs
- operator can review before any next step

## Final note

This document is helper design only. It does not route, ingest, summarize, claim, or validate source truth.
