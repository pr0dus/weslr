# WESLR General Unfinished Research Discovery Implementation Sequence V1

## 1. Purpose
Define a safe staged implementation sequence for WESLR’s governed unfinished-research discovery architecture.

## 2. Owner intent
Convert the doctrine/protocol chain into staged coding lanes that preserve safety, reviewability, and rollbackability.

## 3. Current readiness state
- Ontology expansion doctrine complete and valid.
- Ontology expansion protocol complete and valid.
- Review chain complete and valid.
- Next step is planning implementation sequence only.

## 4. Source artifacts reviewed
- `docs/WESLR_GENERAL_UNFINISHED_RESEARCH_DIRECTION_SIGNAL_ONTOLOGY_AND_SCOUT_HINT_REPAIR_V1.md`
- `docs/WESLR_DISCOVERY_DOCTRINE_ADDENDUM_FOR_GENERAL_UNFINISHED_RESEARCH_SIGNAL_ONTOLOGY_V1.md`
- `docs/WESLR_DISCOVERY_DOCTRINE_ADDENDUM_UPDATE_FOR_GENERAL_UNFINISHED_RESEARCH_SIGNAL_ONTOLOGY_REVIEW_V1.md`
- `docs/WESLR_DISCOVERY_DOCTRINE_ONTOLOGY_EXPANSION_PRINCIPLE_EXTENSION_REVIEW_V1.md`
- `docs/WESLR_ONTOLOGY_EXPANSION_PROTOCOL_V1.md`
- `docs/WESLR_ONTOLOGY_EXPANSION_PROTOCOL_REVIEW_V1.md`

## 5. Implementation principles
- Metadata first.
- No source ingestion unless later authorized.
- No accepted evidence or accepted candidates during planning lanes.
- No public claims.
- No `.weslr` IO.
- No runtime/chat/UI/voice wiring in the planning lanes.
- Keep protected runtime files untouched.
- Prefer narrow lanes with reviewable deltas.
- Use exact-file release-gate allowances only if absolutely necessary.

## 6. Non-goals
- No implementation code in this artifact.
- No true run.
- No live SearXNG.
- No provider/model calls.
- No paper/PDF/dataset/patent/repo/source-page fetching.
- No source ingestion.
- No accepted evidence.
- No accepted candidates.
- No proposal payload promotion.
- No final answers.
- No public discovery/proof/AGI/consciousness/sentience/benchmark/product-readiness claims.

## 7. Protected files
Must remain untouched unless separately approved:
- `weslr/chat_responder.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`
- `weslr/main.py` if present
- `.weslr/*`

## 8. Proposed staged implementation sequence

### Stage 0 — baseline inventory
Inventory current helper modules, tests, enums, source classes, evidence roles, routes, denied-authority flags, and release-gate allowances.
- No code change.
- Output: inventory doc and mapping notes only.

### Stage 1 — shared registry / constants design implementation
Create a metadata-only registry/helper for domain families, signal types, source classes, evidence roles, routes, disconfirming-evidence classes, operator tokens, artifact types, forbidden discovery meanings, and safe discovery meanings.
- No runtime wiring.
- No source access.
- Tests first or same-lane tests required.

### Stage 2 — source-class and evidence-role normalization
Repair enum mismatch between metadata boundary and MLCF routing.
Ensure safe metadata roles are consistently accepted.
- No evidence acceptance.
- No candidate preparation yet unless route permits.

### Stage 3 — ontology-insufficient protocol implementation
Add `ontology_insufficient_signal`, `ontology_insufficient_for_domain`, `route_to_ontology_expansion_request`, `safe_metadata_summary.sufficient_power`, and `ONTOLOGY_EXPANSION_REQUEST_CONFIRMED`.
Block candidate-preparation from ontology-insufficient signals.
Produce operator-review expansion request packet.

### Stage 4 — scout signal-family expansion
Implement unfinished-work, dormant, technology-blocked, cross-domain, anomaly, measurement-gap, formal-unsolved, fringe-edge, future-work, language/protocol, artifact proposal, and disconfirmation-first signal hints.
- Metadata-only.
- No public claims.
- No accepted candidates.

### Stage 5 — integration helper routing
Route to source-selection plan, cross-domain scout, operator review, disconfirming review, extraordinary-claim quarantine, ontology expansion request, archive low-value signal, and blocked-by-safety.
Keep candidate-preparation route narrow.

### Stage 6 — candidate-preparation eligibility repair
Allow candidate-preparation only for valid metadata candidate routes.
Require missing evidence, disconfirming evidence, source classes, and operator review.
Block extraordinary claims unless separately confirmed.
Block ontology-insufficient signals.
Block public/discovery/proof language.

### Stage 7 — artifact proposal packet
Produce artifact proposal candidates only.
No generated artifact as truth.
Support source-selection plan, disconfirmation plan, experiment plan, simulation plan, dataset-to-build plan, benchmark-to-build plan, operator-review card, learning module, concept map, protocol map, future-work map, risk map, and cross-domain bridge map.

### Stage 8 — tests and sample packets
Create unit tests for each helper and negative tests for forbidden claims.
Add JSON-safe serialization tests, no `.weslr` IO tests, no source-fetch tests, no runtime/chat/UI/voice tests, and release-gate tests.

### Stage 9 — second controlled true run design
Plan a later non-WiFi metadata-only true run to test ontology-insufficient detection, expansion request creation, no auto-application, operator-review packet creation, disconfirmation-first packet behavior, and no accepted evidence/public claims.

### Stage 10 — review and consolidation
Implementation review, context alignment, and optional push strategy.
No public/runtime promotion.

## 9. Files likely to be created
Likely new files include:
- `weslr/unfinished_research_discovery_registry.py`
- `weslr/unfinished_research_discovery_constants.py`
- `weslr/ontology_expansion_protocol.py`
- `weslr/ontology_expansion_request_builder.py`
- `weslr/unfinished_research_discovery_sequence_helpers.py`
- `weslr/tests/test_unfinished_research_discovery_registry_v1.py`
- `weslr/tests/test_ontology_expansion_protocol_v1.py`
- `weslr/tests/test_ontology_expansion_request_builder_v1.py`
- `weslr/tests/test_unfinished_research_discovery_sequence_helpers_v1.py`
- stage-specific sample/report docs

## 10. Files likely to be modified
Likely touched files include:
- `weslr/tests/release_gate_v1.py` only if exact-file allowance is required
- metadata/helper modules added in Stage 1 through Stage 7
- corresponding focused tests
- stage-specific documentation artifacts

## 11. Tests likely to be created
Likely tests include:
- registry inventory and enum consistency tests
- ontology-insufficient packet tests
- route restriction tests
- candidate-preparation exclusion tests
- extraordinary-claim quarantine tests
- language/protocol restriction tests
- future-work hype restriction tests
- JSON serialization tests
- no `.weslr` IO tests
- no runtime/chat/UI/voice tests
- release-gate regression tests

## 12. Release-gate strategy
- Prefer no release-gate edits.
- If an exact allowlist is needed, add only the exact file path(s) required.
- No wildcard `docs/` allowances.
- No protected-file weakening.
- Validate each stage with `git diff --check`, `python3 weslr/tests/release_gate_v1.py`, and `bash scripts/weslr_release_check.sh`.

## 13. Rollback strategy
- Keep each stage isolated.
- Commit stage boundaries separately.
- Record previous enum/registry snapshots before any expansion lane.
- Use revert commits rather than destructive history rewriting.
- Preserve no-memory-mutation and no `.weslr` IO constraints.

## 14. Owner approval gates
Required before moving from planning to implementation:
- approve Stage 1 registry/constants lane
- approve Stage 3 ontology-insufficient protocol lane
- approve any code-change-required enum expansion
- approve second controlled true-run design lane
- approve any release-gate relaxation if ever needed

## 15. Risk assessment
Primary risks:
- enum drift between helpers
- accidental candidate-preparation widening
- accidental public-claim wording
- release-gate overreach
- protected-file contamination
- ontology expansion becoming automatic instead of governed

Mitigations:
- metadata-only first
- narrow staged lanes
- explicit blocked routes
- exact-file gate allowances only
- stage-by-stage reviews

## 16. Recommended first coding lane
Stage 0 baseline inventory, followed by Stage 1 shared registry/constants design.

## 17. Second true-run placement
After Stage 3 and Stage 5 are implemented and reviewed, and only after operator approval.
The run remains non-WiFi and metadata-only.

## 18. Validation plan
For each stage:
- `git diff --check`
- `python3 weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`
- focused pytest for the stage’s helpers

## 19. Next recommended lane
`REVIEW_WESLR_GENERAL_UNFINISHED_RESEARCH_DISCOVERY_IMPLEMENTATION_SEQUENCE_V1`

## 20. Final judgment
`unfinished_research_discovery_implementation_sequence_plan_ready_for_review`
