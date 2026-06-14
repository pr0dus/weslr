# WESLR Third Controlled True Run On Non-Materials Domain Plan V1

## 1. Purpose
Plan a third controlled true run that tests whether the repaired metadata pipeline generalizes beyond WiFi/RF and materials, using a non-materials domain while preserving the no-ingestion boundary.

## 2. Current readiness state
- Second controlled true run is complete, reviewed, fetched, and validated in Termux.
- Pipeline boundaries held: metadata-only collection, MLCF routing, scout, and candidate-prep gating.
- Readiness is for a planned run only; no execution is authorized here.

## 3. Source artifacts reviewed
- `docs/WESLR_SECOND_CONTROLLED_TRUE_RUN_AFTER_DISCOVERY_REGISTRY_REPAIR_RESULT_V1.md`
- `docs/WESLR_SECOND_CONTROLLED_TRUE_RUN_AFTER_DISCOVERY_REGISTRY_REPAIR_RESULT_REVIEW_V1.md`
- `weslr/tests/release_gate_v1.py`
- `weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py`
- `weslr/tests/test_cross_domain_scout_to_mlcf_integration_v1.py`
- `weslr/tests/test_cross_domain_open_problem_discovery_scout_v1.py`
- `weslr/tests/test_mlcf_routing_from_live_searxng_metadata_result_v1.py`
- `weslr/tests/test_ontology_expansion_request_builder_v1.py`
- `weslr/tests/test_unfinished_research_discovery_constants_v1.py`
- `weslr/tests/test_unfinished_research_discovery_registry_v1.py`

## 4. Lessons from the second controlled true run
- Metadata-only records were sufficient to keep the pipeline safe.
- Scout buckets were sparse because signal items were too generic.
- Candidate-prep was correctly excluded when the route was wrong or weak.
- OER/no-op OER handling should remain available but only when ontology is sufficient or insufficient.
- The next run should improve metadata richness without crossing ingestion boundaries.

## 5. Selected primary domain: "energy_systems"
Use energy systems as the main third-run domain.

## 6. Selected backup domain: "language_communication"
Use language communication only if the primary domain is blocked or too weak.

## 7. Why "energy_systems" is a useful third-run domain
- Exercises technology-blocked directions.
- Surfaces coordination gaps and curtailment/storage gaps.
- Tests measurement and benchmark gaps.
- Produces time-revisit and domain-convergence signals.
- Can reveal future-workforce-impact and artifact-generation candidates.
- Supports disconfirmation-first routing without requiring source ingestion.

## 8. Why "language_communication" is a useful backup
- Good for protocol and review-only posture.
- May expose ontology-insufficient cases if categories are too weak.
- Can test artifact-generation boundaries safely.
- Avoids universal-language or broad-comprehension claims.

## 9. Third-run query candidates
Primary draft queries:
1. grid curtailment storage coordination gap review
2. thermal storage demand response unresolved measurement benchmark
3. distributed energy flexibility market coordination failure review
4. renewable curtailment negative price storage technology blocked
5. virtual power plant interoperability standards gap review

Backup draft queries:
1. communication protocol discovery structure translation gaps
2. constructed language machine translation protocol limitation
3. semantic interoperability unresolved benchmark gap
4. cross domain communication protocol standardization failure
5. language protocol emergence measurement gap review

## 10. Metadata-only collection boundary
Future run may collect only:
- title
- URL
- domain/host
- query used
- source-class estimate
- metadata-only summary if already present in local result metadata

Future run must not collect:
- page content
- PDF content
- dataset content
- GitHub repository content
- patent/source document content
- full text
- retained snippets as evidence
- raw HTML
- private content

## 11. Richer metadata-only signal item strategy
Convert each search result into a richer metadata-only signal item without reading source content.

Allowed fields:
- neutralized title label
- host/domain
- URL path-level metadata
- query-derived signal hint
- source-class estimate
- domain family
- likely signal family
- missing evidence type
- disconfirmation need
- safe next review step
- blocked authority flags

Forbidden fields:
- source page text
- snippets as evidence
- copied abstracts
- copied paper text
- raw HTML
- final-answer text
- proof/discovery claims
- accepted evidence/candidate flags

## 12. Packet path
1. local SearXNG metadata locator
2. metadata-only locator records
3. MLCF routing
4. cross-domain scout
5. scout-to-MLCF integration
6. ontology expansion request builder if ontology-insufficient appears
7. candidate-preparation only if route and safety criteria are met
8. result artifact

## 13. Expected safe outputs
- metadata locator result
- safe source-selection posture
- MLCF route packet
- cross-domain scout packet
- operator-review packet
- blocked-by-safety packet
- ontology-insufficient request if applicable
- no-op OER/audit record if ontology is sufficient
- candidate-preparation exclusion if route is wrong or weak
- narrow candidate-preparation packet only if criteria are safely met

## 14. Forbidden outputs
- accepted evidence
- accepted candidate
- public discovery claim
- proof claim
- final answer
- runtime behavior change
- memory mutation
- project mutation except committed result artifact
- `.weslr` IO
- provider/model call
- source ingestion
- autonomous ontology expansion
- ontology self-modification claim
- benchmark/intelligence/certification claims
- public-science/product-readiness claims

## 15. Ontology-insufficient test plan
If the domain cannot be mapped cleanly into existing buckets, the run should surface ontology-insufficient metadata and request review rather than widening scope.

## 16. OER / no-op OER handling plan
- If ontology is sufficient: record a no-op OER/audit posture.
- If ontology is insufficient: emit a bounded ontology-expansion request.
- In neither case should ontology self-modification happen automatically.

## 17. Candidate-preparation eligibility test plan
Candidate-preparation may proceed only when:
- route is narrow and correct
- safety flags are satisfied
- evidence remains metadata-only
- disconfirmation needs are explicit
- no acceptance language appears

## 18. Time-revisit signal test plan
Look for metadata indicating delayed follow-up, seasonality, maintenance cycles, storage buildouts, policy timing, or deferred deployment windows.

## 19. Technology-blocked signal test plan
Look for metadata that indicates an implementation path exists but is blocked by hardware, grid constraints, interoperability, or regulatory interfaces.

## 20. Measurement/benchmark-gap signal test plan
Look for gaps around metrics, benchmark absence, verification limitations, and unclear comparators.

## 21. Domain-convergence signal test plan
Look for cases where energy systems intersects with markets, storage, planning, operations, standards, or coordination layers.

## 22. Future-workforce-impact signal test plan
Look for metadata indicating staffing, operator burden, maintenance, training, or labor-shift implications.

## 23. Artifact-generation candidate test plan
Track only whether a result suggests an artifact should be proposed later; do not create the artifact in this run.

## 24. Disconfirmation-first test plan
Each signal item should ask what would falsify the direction before treating it as promising.

## 25. Denied-authority validation plan
Validate that the run does not claim accepted evidence, final answers, or authority to widen scope.

## 26. No-retention validation plan
Validate that no raw content, snippets as evidence, or retained source text are kept.

## 27. Expected result artifact path
`docs/WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_RESULT_V1.md`

## 28. Validation commands for future run
- `git diff --check`
- `python3 weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`
- optional regression tests listed by operator for scout, integration, candidate-prep, MLCF routing, OER, constants, and registry coverage

## 29. Owner/operator approval gate
The actual third controlled true run requires explicit owner/operator approval before any execution.

## 30. Risk assessment
Main risk: generic metadata may again produce sparse scout buckets. Mitigation: stronger query framing and richer metadata-only signal item construction.

## 31. Recommended next lane
`RUN_WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_V1`

## 32. Final judgment
This plan is ready for owner approval.
