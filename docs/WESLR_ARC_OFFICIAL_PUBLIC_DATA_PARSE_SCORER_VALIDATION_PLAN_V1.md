# WESLR ARC Official Public-Data Parse/Scorer Validation Plan (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_OFFICIAL_PUBLIC_DATA_PARSE_SCORER_VALIDATION_PLAN_V1`
**Start HEAD**: `98e37a85214f96ed778e468b447e8e427df2a27c`
**actual preflight HEAD**: pending validation
**End HEAD**: pending commit
**Commit**: pending

## Purpose

Define the future Phase 2 public official-data parse/scorer validation lane without importing, downloading, inspecting, or running official ARC data yet.

This is a design plan only. It does not authorize implementation, solver changes, competition claims, or official ARC claims.

## 1) Required preconditions

Before Phase 2 may run, all of the following must already exist and pass:

- owner approval manifest exists
- approval manifest passes the approval gate
- source location is recorded
- source version or snapshot is recorded
- checksum is recorded
- local bundle is read-only
- no hidden/private data is allowed
- official percentage claimable remains `none/0` before any local public run

Phase 2 must treat any missing precondition as a stop condition.

## 2) Phase 2 scope

Phase 2 may do only the following:

- parse official public JSON structure
- validate train/test format
- validate grid structure
- validate scorer exact-equality behavior
- validate two-output answer format
- validate safe logs
- produce a parse/scorer validation report only

Phase 2 may not do any of the following:

- no solver run for performance claim
- no competition claim
- no hidden/private data
- no model/provider/tool/web/retrieval calls
- no mutation of the source bundle
- no synthetic/official score mixing

## 3) Future files likely needed

Likely future files for the Phase 2 lane:

- `weslr/arc_official_public_data_adapter.py`
- `weslr/arc_official_public_data_scorer.py`
- `weslr/arc_official_public_data_harness.py`
- `weslr/tests/test_arc_official_public_data_adapter.py`
- `weslr/tests/test_arc_official_public_data_scorer.py`
- `weslr/tests/test_arc_official_public_data_harness.py`
- `docs/WESLR_ARC_OFFICIAL_PUBLIC_DATA_PARSE_AND_SCORE_BOUNDARY_REVIEW_V1.md`
- `docs/WESLR_ARC_OFFICIAL_PUBLIC_DATA_LOCAL_RUN_BOUNDARY_IMPLEMENTATION_V1.md`
- `docs/WESLR_ARC_OFFICIAL_PUBLIC_DATA_POST_RUN_AUDIT_V1.md`
- `docs/WESLR_ARC_OFFICIAL_PUBLIC_DATA_CLAIM_POLICY_V1.md`
- `docs/WESLR_ARC_OFFICIAL_PUBLIC_DATA_PARSE_SCORER_VALIDATION_REPORT_V1.md`
- `weslr/tests/fixtures/arc_official_public_data_manifest_dummy_v1.json`

All fixture examples must be dummy/no-data examples only.

## 4) Scorer validation strategy

Exact grid equality should be validated without leaking expected outputs to solver-visible paths by separating roles:

- adapter side: parse input grid structure and keep expected outputs out of solver-visible channels
- scorer side: compare predicted grids against hidden reference grids in-memory only
- harness side: pass only candidate outputs to the scorer
- report side: record score metadata, not hidden answers

Recommended validation checks:

- grid dimensions match exactly
- each cell value matches exactly
- output count matches the required answer format
- two-output tasks require exactly two submitted outputs where applicable
- hidden reference grids never appear in solver-visible logs, exceptions, or serialized artifacts

The validation design should confirm that exact-equality scoring is implemented as a pure comparison step and not as a solver-visible hint channel.

## 5) Logging strategy

Allowed logs:

- task ID
- parse status
- format status
- timing
- checksum/provenance metadata

Forbidden logs:

- expected outputs in solver-visible logs
- hidden/private answers
- latent rules
- internal task language

Log output should stay metadata-only and report-safe. If a parse or scorer failure occurs, the log should say what failed, not reveal the hidden target.

## 6) Stop conditions

Phase 2 must stop immediately if any of the following occurs:

- manifest missing or invalid
- checksum mismatch
- source not read-only
- hidden/private data detected
- malformed format
- expected-output leakage
- internet/tool/model access
- scorer mismatch
- dirty protected files
- `.weslr` access
- runtime/chat/UI/provider access

Any stop condition should terminate the lane and preserve the failure reason in the report.

## 7) Claim policy

Allowed Phase 2 claim:

- parse/scorer validation only
- no official percentage
- no performance score
- no competition result

Disallowed claims:

- official ARC performance
- leaderboard standing
- competition submission success
- any claim that requires a local public run or post-run audit

The expected public-facing wording for Phase 2 should remain bounded to parse/scorer validation status only.

## 8) Relationship to earlier boundary work

This plan depends on the already-reviewed approval manifest gate and the official public-data import/local-run boundary. It does not weaken those boundaries.

Phase 2 is a future validation lane, not a runtime lane, not a competition lane, and not a solver-authority lane.

## 9) Current status note

At design time:

- official data remains untouched
- official percentage claimable remains `none/0`
- no implementation is authorized by this plan alone

## Receipt

- Start HEAD / End HEAD / Commit: `98e37a85214f96ed778e468b447e8e427df2a27c` / `98e37a85214f96ed778e468b447e8e427df2a27c` / `no`
- actual preflight HEAD: `98e37a85214f96ed778e468b447e8e427df2a27c`
- design report created: yes
- required preconditions defined: yes
- Phase 2 scope defined: yes
- future files listed: yes
- scorer validation strategy defined: yes
- logging strategy defined: yes
- stop conditions defined: yes
- claim policy defined: yes
- official data untouched: yes
- official percentage claimable remains none/0: yes
- validation: pending
- unrelated dirty files left uncommitted: yes
- push avoided: yes
- recommended next lane: `Await owner direction`
