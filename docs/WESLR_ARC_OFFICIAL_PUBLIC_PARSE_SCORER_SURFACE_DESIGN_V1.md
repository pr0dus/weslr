# WESLR ARC Official Public Parse/Scorer Surface Design V1

## 1. Provenance / start state
- Repository: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Actual preflight HEAD: `11a30ffab0645a13b059590b54371461edc770e1`
- End HEAD (verified preflight): `11a30ffab0645a13b059590b54371461edc770e1`
- Commit status: committed in this lane
- Previous blind mock result: `blind_mock_ready_for_public_parse_scorer_design`
- Previous blind mock score: `240/240` solver exact; trivial baseline `20/240`
- Previous blind reflect score: `20/20`
- Previous blind rotate score: `20/20`
- Previous blind malformed/timeout/error: `0/0/0`
- Official/public ARC data untouched: yes
- Official percentage: none/0
- Note: the earlier blind report body that still showed `End HEAD: a120b50b062d38cfd6cb7b3f113199d2e82c267a` is stale pre-commit text; this design lane records the verified actual preflight HEAD above.

## 2. Surface overview
Future official/public evaluation should be split into:
- approval manifest gate
- source bundle verifier
- adapter
- blind solver-visible packet builder
- two-output emitter
- scorer
- run harness
- report writer
- contamination/leakage audit

## 3. Approval dependency
No future official/public parse/scorer lane may run unless all are true:
- owner approval manifest exists
- approval manifest passes the gate
- source location is recorded
- source version or snapshot is recorded
- checksum is recorded
- source bundle is read-only
- offline/no-network requirement is enabled
- no hidden/private data is included
- approved phase is recorded

## 4. Adapter boundary
The future adapter should:
- parse only approved local read-only public source bundles
- never mutate source files
- verify checksum/provenance before parse
- separate solver-visible input from scorer-only reference data
- produce anonymous task ids for solver-visible paths
- avoid source filenames when they might reveal answer/status information
- keep ARC-AGI-1 and ARC-AGI-2 separated

## 5. Solver-visible packet contract
Allowed in future official/public solver-visible packets:
- anonymized task id
- train input grids
- train output grids
- test input grids
- generic required-output-count metadata if needed
- format metadata that does not leak answers or rules

Forbidden in future official/public solver-visible packets:
- expected test outputs
- scorer references
- family labels
- source split labels implying answer access
- hidden/private markers
- semantically risky official filenames
- latent rule labels
- answer descriptors
- post-parse target summaries

## 6. Emitter boundary
The future emitter should:
- emit exactly two candidate outputs per test input for ARC-AGI-2-style runs
- preserve malformed-output handling
- never repair candidates using hidden answers
- support ARC-AGI-1 separately if needed without assuming the two-output rule applies there

## 7. Scorer boundary
The future scorer should:
- use exact grid equality only
- score task = 1 if any allowed candidate exactly matches the scorer-only reference
- score task = 0 otherwise
- never log hidden expected outputs
- never expose reference grids in exceptions
- never write reference grids into public reports
- record only metadata-safe scoring results

## 8. Logging and redaction policy
- Synthetic reports may contain synthetic references if intentionally marked.
- Official/public reports must not contain expected outputs or hidden reference grids.
- Official/public reports must be metadata-only.

Allowed report fields:
- task count
- parse status
- format status
- candidate count status
- exact-two-output compliance
- score metadata
- timing
- checksum/provenance
- anonymized task ids
- aggregate score
- error labels

Forbidden report fields:
- expected outputs
- hidden answers
- scorer reference grids
- latent task rules
- solution explanations derived from hidden answers
- public/private hidden markers that create leakage
- original task JSON dumps
- train/test examples copied from official data

## 9. Offline/no-internet execution model
This design preserves:
- no OCC
- no ChatGPT/model/provider/API help
- no web lookup
- no retrieval
- no tool calls
- no manual answer repair after command start
- all solver/scorer/adapter code exists locally before execution
- one local command can run unattended when future implementation is authorized

## 10. Future command shape
Reserved future command names only:
- `./run arc-public-parse-check`
- `./run arc-public-score-check`
- `./run arc-public-local-run`

This lane does not authorize those commands yet.

## 11. Dummy/no-data fixture policy
Any example fixture in this lane must be:
- dummy only
- not copied from ARC
- not shaped to mimic a known public ARC task
- clearly marked synthetic/no-data
- safe for tests
- not score-claimable

## 12. Stop conditions for future implementation
Future implementation must stop if:
- approval manifest is missing or invalid
- checksum is missing or mismatched
- source is not read-only
- source bundle includes hidden/private data
- any official expected output reaches solver-visible path
- any official expected output reaches logs or reports
- malformed official format is found
- scorer mismatch occurs
- internet/tool/model/provider/retrieval access is required
- `.weslr` access is attempted
- runtime/chat/UI/provider files are touched
- solver self-modifies during run
- synthetic and official results are mixed

## 13. Future file proposal
Proposed file surface only:
- `weslr/arc_official_public_data_adapter.py`
- `weslr/arc_official_public_data_scorer.py`
- `weslr/arc_official_public_data_emitter.py`
- `weslr/arc_official_public_data_harness.py`
- `weslr/arc_official_public_data_report_redactor.py`
- `weslr/tests/test_arc_official_public_data_adapter.py`
- `weslr/tests/test_arc_official_public_data_scorer.py`
- `weslr/tests/test_arc_official_public_data_emitter.py`
- `weslr/tests/test_arc_official_public_data_harness.py`
- `weslr/tests/test_arc_official_public_data_report_redactor.py`
- `docs/WESLR_ARC_OFFICIAL_PUBLIC_PARSE_SCORER_SURFACE_DESIGN_V1.md`

## 14. Required report
This document is the required design report for:
`docs/WESLR_ARC_OFFICIAL_PUBLIC_PARSE_SCORER_SURFACE_DESIGN_V1.md`

It records the scope, boundaries, and future interface only.
It does not authorize official data use.

## Recommended next lane
If and only if approval is later granted, the next lane should implement the source-bundle verifier and adapter boundary first, with the scorer kept scorer-only and redaction enforced before any official/public run.
