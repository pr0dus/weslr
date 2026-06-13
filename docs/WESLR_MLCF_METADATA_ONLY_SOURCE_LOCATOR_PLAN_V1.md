# WESLR MLCF Metadata-Only Source Locator Plan V1

## 1. Purpose
Define the source locator layer as:
- a source-finding planner
- metadata-only
- pre-ingestion
- non-authoritative
- operator-reviewable
- unable to claim evidence or truth

This layer may identify candidate locators only. It does not fetch, ingest, summarize, retain, or authorize source content.

## 2. Source locator pipeline
Science direction
→ source-selection evidence plan
→ authorized ingestion boundary preparation
→ metadata-only source locator plan
→ candidate locator records
→ source-class / authority guess
→ operator review
→ authorized metadata-only source summary lane
→ evidence-intake packet
→ MLCF ledger assignment
→ calibration axes
→ cross-domain candidate helper
→ pressure/probe

## 3. SearXNG role
SearXNG is a candidate source locator and search-result metadata provider.
It is not:
- evidence
- truth source
- ingestion authority
- public claim authority
- a raw-page store
- a bypass around operator review

Future SearXNG output must stay metadata-only and may include:
- query used
- result title
- result URL
- result domain
- snippet if policy allows
- source-class guess
- authority-level guess
- evidence-role guess
- relevance reason
- access/license risk
- freshness risk
- blocked/allowed locator status

## 4. GitHub role
GitHub is:
- an implementation evidence locator
- a candidate-signal source
- useful for repositories, code, datasets, tooling, and benchmarks

GitHub is not:
- authoritative science evidence alone
- enough without official standards, papers, datasets, or measurements

## 5. Official/public source locator classes

### official_standard
- Allowed locator metadata: title, issuer, version, date, URL/identifier, scope, domain fit, authority guess, evidence-role guess, access/license risk, freshness risk
- Forbidden locator metadata: raw content, copied clauses, unreviewed claims of authority, ingestion hints
- Authority level: official_primary
- Evidence role: definition_or_standard, constraint_source
- Likely query style: official standard name, RF/WiFi standard, vendor-neutral spec, protocol name
- Quality checks: issuer authenticity, version, scope, normative language
- Freshness checks: current revision, errata, supersession
- Access/license checks: public availability, reuse conditions
- Privacy checks: no personal data, no private notes, no raw excerpts
- Blocked conditions: paywall/unauthorized access, hidden source, raw retention request
- Next safe step: operator review

### official_government_or_agency_data
- Allowed locator metadata: dataset title, agency, region, date, URL/identifier, collection method, authority guess, evidence-role guess, access risk, freshness risk
- Forbidden locator metadata: raw records, row-level content, retained downloads
- Authority level: official_primary
- Evidence role: measurement_data, domain_context
- Likely query style: agency data portal, public sensing dataset, national lab archive, spectrum/RF measurement program
- Quality checks: collection method, provenance, declared limitations
- Freshness checks: publication date, update cadence, release version
- Access/license checks: public access terms, usage rights, attribution
- Privacy checks: personal/location sensitivity, reidentification risk
- Blocked conditions: restricted access, private portal, raw download without approval
- Next safe step: operator review

### official_vendor_documentation
- Allowed locator metadata: product/doc title, vendor, version, URL, supported features, authority guess, evidence-role guess
- Forbidden locator metadata: copied manuals, unapproved excerpts, private docs
- Authority level: official_primary
- Evidence role: implementation_reference, constraint_source
- Likely query style: vendor RF stack docs, chipset docs, CSI docs, SDK docs
- Quality checks: product/version match, implementation scope, change log
- Freshness checks: current release, firmware/SDK revision
- Access/license checks: public docs vs gated docs, redistribution terms
- Privacy checks: avoid private support content and protected attachments
- Blocked conditions: gated support portal, unauthorized docs, hidden file access
- Next safe step: operator review

### public_research_paper
- Allowed locator metadata: title, authors, venue, year, DOI/arXiv/URL, abstract-level identifiers, authority guess, evidence-role guess
- Forbidden locator metadata: full text retention, unapproved extracted claims, private annotations
- Authority level: public_primary
- Evidence role: prior_art, replication_target
- Likely query style: RF sensing paper, indoor localization paper, CSI motion detection paper, material scattering paper
- Quality checks: venue, method, peer-review status, citations, dataset linkage
- Freshness checks: publication year, preprint vs final, later corrections
- Access/license checks: open access status, repository policy, reuse terms
- Privacy checks: no retained annotations containing private data
- Blocked conditions: paywalled access without approval, raw PDF retention, library bypassing
- Next safe step: operator review

### public_dataset
- Allowed locator metadata: dataset name, host, modality, sample type, label type, URL/identifier, authority guess, evidence-role guess
- Forbidden locator metadata: downloaded files, sample rows, retained raw measurements
- Authority level: public_primary
- Evidence role: measurement_data, replication_target
- Likely query style: indoor RF dataset, WiFi sensing dataset, CSI dataset, localization benchmark dataset
- Quality checks: collection setup, modality fit, labels, domain match
- Freshness checks: release version, update date, deprecation status
- Access/license checks: download terms, redistribution, attribution, academic use limits
- Privacy checks: human subject data, location traces, device identifiers
- Blocked conditions: unauthorized downloads, raw retention, secret/private datasets
- Next safe step: operator review

### github_repository
- Allowed locator metadata: repo name, owner, URL, stars/forks only if needed, release tags, README title, inferred scope, authority guess
- Forbidden locator metadata: cloned content, raw code retention, secret tokens, private issues, unapproved scraping
- Authority level: implementation_evidence
- Evidence role: implementation_reference, candidate_signal
- Likely query style: WiFi sensing implementation, CSI processing repo, indoor mapping code, RF localization benchmark repo
- Quality checks: commit history, release tags, issue/PR signal, reproducibility hints
- Freshness checks: latest release, active maintenance, recent commits
- Access/license checks: repo license, API/clone limits, public/private status
- Privacy checks: no private repos, no secrets, no personal data retention
- Blocked conditions: GitHub call not approved, private repo, raw content retention, GitHub-only official-evidence claim
- Next safe step: operator review

### public_lab_or_university_artifact
- Allowed locator metadata: lab/university name, artifact title, URL/identifier, lab context, authority guess, evidence-role guess
- Forbidden locator metadata: raw attachment retention, private lab notes, inaccessible materials
- Authority level: public_secondary
- Evidence role: measurement_data, replication_target
- Likely query style: lab archive, thesis supplement, university repository, course/research artifact
- Quality checks: institutional provenance, artifact type, method fit
- Freshness checks: artifact date, revision history, thesis/publication linkage
- Access/license checks: repository terms, reuse policy, open-access status
- Privacy checks: student privacy, lab-internal notes, personal data
- Blocked conditions: private lab storage, gated artifacts, unapproved downloads
- Next safe step: operator review

### public_benchmark_or_test_suite
- Allowed locator metadata: benchmark/test name, host, URL/identifier, scenario type, authority guess, evidence-role guess
- Forbidden locator metadata: raw benchmark outputs, hidden test vectors, retained run logs
- Authority level: public_secondary
- Evidence role: counterexample_source, replication_target
- Likely query style: RF sensing benchmark, indoor localization suite, CSI evaluation benchmark, floor-plan evaluation benchmark
- Quality checks: protocol clarity, metric fit, scenario coverage
- Freshness checks: suite version, recent maintenance, deprecations
- Access/license checks: benchmark rules, usage restrictions, output sharing terms
- Privacy checks: no retained participant data or private evaluation outputs
- Blocked conditions: private benchmark access, hidden test data, unapproved result storage
- Next safe step: operator review

## 6. Query planning rules
Future WESLR should form safe search queries that are narrow, source-class aware, and metadata-only.

Rules:
- Search by evidence need, not by conclusion.
- Prefer official/primary sources before community or implementation sources.
- Keep query families separate by source class.
- Do not request raw content, full text, downloads, or repo cloning in locator mode.
- Treat snippets as metadata only, not evidence.
- Record access/license and freshness risk for every candidate.
- Never convert a locator guess into a claim.

Example query families for the RF/material/floor-plan candidate:
- official WiFi / RF standards
- indoor RF propagation datasets
- WiFi sensing public datasets
- CSI-based motion detection papers
- RF multipath indoor mapping research
- material scattering RF reflection papers
- floor-plan constrained localization papers
- public GitHub implementations of WiFi sensing or CSI processing
- benchmark datasets for indoor localization or RF sensing

## 7. Candidate locator record shape
Future metadata-only locator records should use this shape:

```json
{
  "schema_version": "mlcf_metadata_only_source_locator_record_v1",
  "locator_id": "string",
  "science_direction_id": "string",
  "query_family": "string",
  "source_class": "official_standard | official_government_or_agency_data | official_vendor_documentation | public_research_paper | public_dataset | github_repository | public_lab_or_university_artifact | public_benchmark_or_test_suite",
  "candidate_title": "string",
  "candidate_url_or_identifier": "string",
  "candidate_domain": "string",
  "authority_level_guess": "official_primary | public_primary | public_secondary | implementation_evidence | community_signal | owner_context | internal_context | unknown_authority | blocked",
  "evidence_role_guess": "definition_or_standard | measurement_data | implementation_reference | prior_art | candidate_signal | counterexample_source | replication_target | constraint_source | domain_context | safety_boundary_context | not_authoritative_context",
  "relevance_reason": "string",
  "freshness_status": "current | recent | stale | unknown",
  "access_license_status": "open | permissioned | restricted | blocked | unknown",
  "privacy_status": "low | medium | high | unknown",
  "operator_review_need": "string",
  "allowed_next_step": "string",
  "blocked_conditions": ["string"],
  "authority_status": {
    "source_ingestion_authorized": false,
    "raw_retention_authorized": false,
    "web_call_authority": false,
    "github_call_authority": false,
    "public_claim_authorized": false,
    "final_answer_authority": false,
    "discovery_claim_authorized": false,
    "proof_claim_authorized": false,
    "agi_claim_authorized": false,
    "benchmark_claim_authorized": false,
    "public_science_claim_authorized": false
  },
  "safe_metadata": {
    "metadata_only": true,
    "json_safe": true,
    "non_public": true,
    "no_raw_content": true,
    "no_ingestion": true,
    "no_claims": true
  }
}
```

## 8. Authority and safety model
All authority flags remain false:
- source ingestion authorized: false
- raw retention: false
- web call authority: false
- GitHub call authority: false
- public claim: false
- final answer authority: false
- discovery/proof/AGI/benchmark/public-science claim: false

## 9. Fail-closed rules
The future locator helper must fail closed on:
- private/hidden/protected sources
- paywalled sources requiring unauthorized access
- raw page retention
- source content ingestion
- web/GitHub call authorization without operator approval
- public claim language
- discovery/proof/benchmark/AGI/public-science language
- GitHub-only official-evidence claim
- community-only science evidence claim
- missing source class
- missing authority guess
- missing evidence role
- missing access/license status
- missing freshness status
- cross-user leakage
- `.weslr` IO implication

## 10. Future implementation recommendation
Recommended next helper:
- `IMPLEMENT_WESLR_MLCF_METADATA_ONLY_SOURCE_LOCATOR_RECORD_HELPER_V1`

That helper should create and validate locator records only.
It must not call SearXNG yet.

After that:
- `IMPLEMENT_WESLR_MLCF_SEARXNG_SOURCE_LOCATOR_ADAPTER_BOUNDARY_V1`

That later lane may define a SearXNG adapter boundary, but still no automatic ingestion.

## Validation
- git diff --check
- python3 weslr/tests/release_gate_v1.py
- bash scripts/weslr_release_check.sh

## Protected files
Remain unchanged:
- `weslr/chat_responder.py`
- `weslr/main.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`

## Final judgment
mlcf_metadata_only_source_locator_plan_valid_ready_for_locator_record_helper
