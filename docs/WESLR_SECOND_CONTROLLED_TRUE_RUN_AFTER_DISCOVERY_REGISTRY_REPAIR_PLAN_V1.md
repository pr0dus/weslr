# WESLR Second Controlled True Run After Discovery Registry Repair Plan V1

## 1. Purpose
Design the second controlled true run to verify the repaired discovery-registry pipeline end-to-end without source ingestion.

## 2. Current readiness state
- Discovery ontology registry/constants: repaired and reviewed
- Ontology expansion request builder: repaired and reviewed
- MLCF routing enum alignment: repaired and reviewed
- Cross-domain scout signal expansion: repaired and reviewed
- Scout-to-MLCF integration ontology-expansion route: repaired and reviewed
- Candidate-preparation compatibility repair: repaired and reviewed
- Ready for a controlled metadata-only true run design

## 3. Source artifacts reviewed
- `docs/WESLR_CANDIDATE_PREPARATION_COMPATIBILITY_REPAIR_REVIEW_V1.md`
- `docs/WESLR_CANDIDATE_PREPARATION_COMPATIBILITY_REPAIR_PLAN_V1.md`
- `weslr/cross_domain_scout_to_mlcf_candidate_preparation.py`
- `weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py`

## 4. Selected primary domain and justification
**Primary domain:** `materials`

**Why:** it is a good fit for dormant mechanisms, failed synthesis constraints, benchmark gaps, and disconfirmation-first metadata planning without requiring WiFi/RF framing or public claims.

## 5. Selected backup domain and justification
**Backup domain:** `energy_systems`

**Why:** it offers clean metadata-only search space around grid-storage, curtailment, thermal-storage, and negative-price coordination gaps while staying away from medical/public-health risk and proof-style framing.

## 6. Query candidates
Metadata-only query candidates for the primary domain:
1. `materials dormant mechanism benchmark gap`
2. `materials failed synthesis constraint disconfirmation first`
3. `materials replication gap unfinished research`
4. `materials technology blocked direction cross domain transfer`
5. `materials measurement gap operator review metadata`

Backup-domain query candidates:
1. `energy systems curtailment coordination gap metadata`
2. `energy systems thermal storage benchmark gap disconfirmation`
3. `energy systems negative price coordination unfinished research`
4. `energy systems grid storage dormant direction metadata`

## 7. Metadata-only collection boundary
Allowed collection:
- title
- URL
- domain / host
- source class estimate
- source metadata summary already present in search-result metadata

Forbidden collection:
- source page content
- PDF content
- dataset content
- GitHub repository content
- full text
- retained snippets as evidence
- raw HTML
- private content

## 8. Packet path
1. metadata locator result
2. MLCF routing
3. cross-domain scout
4. scout-to-MLCF integration
5. ontology expansion request builder if applicable
6. candidate-preparation only if eligible
7. report artifact

## 9. Expected safe outputs
- safe source-selection plan
- cross-domain scout packet
- ontology-insufficient expansion request
- disconfirmation-first packet
- operator-review packet
- blocked-by-safety packet
- candidate-preparation packet only if narrow criteria are safely met

## 10. Forbidden outputs
- accepted evidence
- accepted candidate
- public discovery claim
- proof claim
- final answer
- runtime behavior change
- memory mutation
- project mutation
- `.weslr` IO
- provider/model call
- source ingestion
- autonomous ontology expansion
- ontology self-modification claim

## 11. Ontology-insufficient test plan
Explicitly verify rejection of:
- `ontology_insufficient_signal`
- `ontology_insufficient_for_domain`
- `route_to_ontology_expansion_request`
- ontology-expansion handoff packets
- full ontology expansion request packets

Expect clear blocked labels and a safe next step.

## 12. Expansion request test plan
If the run reaches ontology expansion, it must remain metadata-only and not auto-apply ontology changes.
Verify that expansion request creation stays review-gated and does not become candidate-preparation eligible.

## 13. Candidate-preparation eligibility test plan
Only allow candidate-preparation if all narrow conditions hold:
- safe selected route
- safe signal type
- required disconfirmation-first fields
- denied authorities all false
- no raw source content
- no unsafe public/proof/final-answer language
- no ontology-insufficient marker
- no extraordinary/fringe promotion
- no future-work/language/artifact-proposal promotion

## 14. Extraordinary/fringe quarantine test plan
If triggered, keep extraordinary/fringe signals review-only or quarantine-only in this lane. Do not promote them into candidate-preparation.

## 15. Language/protocol review-only test plan
If triggered, keep language/protocol signals structure/review-only. Do not promote them into candidate-preparation.

## 16. Future-work/job-transformation test plan
If triggered, keep future-work / job-transformation signals review-only. Do not promote them into candidate-preparation.

## 17. Disconfirmation-first test plan
Require explicit disconfirming-evidence or pressure-test fields before any candidate-like routing can proceed.

## 18. Denied-authority validation plan
Verify denied-authority flags remain false in valid packets and that any true denied authority fails closed.

## 19. No-retention validation plan
Verify no raw source content, snippets, HTML, PDF text, dataset content, or copied article text is retained as evidence.

## 20. Future result artifact path
Defined, not created:
- `docs/WESLR_SECOND_CONTROLLED_TRUE_RUN_AFTER_DISCOVERY_REGISTRY_REPAIR_RESULT_V1.md`

## 21. Validation commands for the future run
- `python3 -m pytest weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py`
- `python3 -m pytest weslr/tests/test_cross_domain_scout_to_mlcf_integration_v1.py`
- `python3 -m pytest weslr/tests/test_cross_domain_open_problem_discovery_scout_v1.py`
- `python3 -m pytest weslr/tests/test_mlcf_routing_from_live_searxng_metadata_result_v1.py`
- `python3 -m pytest weslr/tests/test_ontology_expansion_request_builder_v1.py`
- `python3 -m pytest weslr/tests/test_unfinished_research_discovery_constants_v1.py`
- `python3 -m pytest weslr/tests/test_unfinished_research_discovery_registry_v1.py`

## 22. Owner/operator approval gate
The future run requires owner/operator approval before any live metadata-locator or search-step execution.

## 23. Risk assessment
Main risks:
- accidental promotion of ontology-insufficient inputs
- false-positive claim-language blocking
- silent raw-content retention
- drift from metadata-only boundaries

Mitigation:
- explicit blocked labels
- narrow route eligibility
- no source ingestion
- no retained snippets
- no auto-application of ontology

## 24. Recommended next lane
`RUN_WESLR_SECOND_CONTROLLED_TRUE_RUN_AFTER_DISCOVERY_REGISTRY_REPAIR_V1`

## 25. Final judgment
`second_controlled_true_run_after_discovery_registry_repair_plan_ready_for_owner_approval`
