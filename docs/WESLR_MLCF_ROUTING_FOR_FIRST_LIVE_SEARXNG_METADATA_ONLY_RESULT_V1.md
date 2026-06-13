# WESLR MLCF Routing For First Live SearXNG Metadata-Only Result V1

**Status:** Design only. This document defines a future route from the reviewed live result artifact into the existing MLCF metadata chain. It does not execute routing.

## 1. Purpose

Design a future metadata-only routing path for the already-recorded live result artifact:

`docs/WESLR_FIRST_CONTROLLED_LIVE_SEARXNG_METADATA_ONLY_SAMPLE_RESULT_V1.md`

This lane must not create evidence, summaries of source content, trusted verdicts, or any runtime/public integration.

## 2. Intended future chain

`controlled_live_searxng_metadata_only_result_packet`
→ `mlcf_metadata_only_source_locator_record`
→ `mlcf_source_locator_organization_review_packet`
→ `mlcf_authorized_metadata_only_source_summary`
→ `mlcf_evidence_intake_packet_from_metadata_summary`
→ `mlcf_normalized_evidence_packet_from_intake_preparation`

Each step is future-only. The present lane designs the route and its gates.

## 3. Allowed fields into MLCF

Only metadata fields may enter the future route:

- query
- title
- URL
- domain
- source engine
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

## 4. Forbidden fields

Never route any of the following:

- raw HTTP response body
- raw HTML
- full snippets
- page content
- source excerpts
- source summaries
- embeddings
- content hashes
- copied article text
- PDF content
- repository content
- downloaded files
- accepted evidence verdicts
- trusted evidence verdicts
- candidate membership claims
- final-answer claims
- public claims

## 5. Kept-locator routing posture

The 5 kept locators from the live result remain locator metadata only.

- unknown authority locators remain review-only
- `github_repository` remains `community_signal`
- `public_lab_or_university_artifact` remains secondary/public locator metadata
- no locator becomes evidence by itself
- no locator becomes proof
- no locator becomes accepted truth

## 6. Blocked-overflow routing posture

The 35 blocked overflow entries remain blocked as `result_cap_exceeded`.

- do not route blocked overflow into MLCF by default
- count them only as overflow metadata
- allow future owner-approved larger-cap samples to review them
- never treat blocked overflow as evidence

## 7. Routing gates

Future routing must pass all of these gates:

- result packet validation gate
- source locator metadata allowlist gate
- blocked-entry exclusion gate
- no-raw-content gate
- no-snippet gate
- no-ingestion gate
- no-claim gate
- operator-review gate
- JSON-safe packet gate
- provenance/traceability gate
- rollback/no-write gate

## 8. Mapping rules

Future mapping must be metadata-only:

- live result query → MLCF locator query context
- title → locator title
- URL → locator URL
- domain → locator domain
- source engine → locator source engine
- rank → locator rank
- score → locator score
- published date → locator published date
- source class hint → MLCF source-class posture
- authority guess → MLCF authority posture
- freshness status guess → MLCF freshness posture
- access/license status guess → MLCF access posture
- privacy status guess → MLCF privacy posture
- evidence role guess → candidate-signal posture only
- blocked status → block-state metadata only
- locator ID → stable locator identifier

## 9. Blocked conditions

The future router must block or hold for operator review if:

- source class is unknown and authority is unknown
- URL domain appears private, loopback, credential-bearing, login-only, personal-data platform, tracking-only, malware-like, or otherwise unsafe
- title or URL is too long
- result exceeds cap
- snippet policy is disabled but snippet content appears
- raw response body appears
- any authority flag is true
- any claim language appears
- any trusted/accepted evidence verdict appears
- any MLCF stage tries to ingest source content

## 10. Expected future helper shape

Possible future helpers:

- `weslr/mlcf_routing_from_live_searxng_metadata_result.py`
- `weslr/tests/test_mlcf_routing_from_live_searxng_metadata_result_v1.py`

These are design suggestions only.

## 11. Future sample lane

The next future lane should be:

`RUN_WESLR_MLCF_ROUTING_FOR_FIRST_LIVE_SEARXNG_METADATA_ONLY_RESULT_SAMPLE_V1`

That future lane should use the existing result artifact on disk. It must not make another live SearXNG call.

## 12. Success criteria

Success means:

- the live result can be converted into MLCF locator metadata packets
- no source content enters MLCF
- no evidence claim is created
- no accepted/trusted verdict is created
- GitHub remains community/implementation signal only
- unknown sources remain review-only
- overflow stays blocked
- output remains JSON-safe and metadata-only
- operator can inspect the route before any further action

## 13. Denied authority fields

Explicitly deny:

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

## 14. Final note

This document is route design only. It does not route, ingest, summarize, claim, or validate source truth.
