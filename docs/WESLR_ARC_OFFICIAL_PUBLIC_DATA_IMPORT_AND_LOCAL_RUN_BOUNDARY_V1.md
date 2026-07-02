# WESLR ARC Official Public-Data Import and Local-Run Boundary (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_OFFICIAL_PUBLIC_DATA_IMPORT_AND_LOCAL_RUN_BOUNDARY_V1`
**Start HEAD**: `f101f04ea72c08f0a658780c0ba57a1269530db2`
**actual preflight HEAD**: `f101f04ea72c08f0a658780c0ba57a1269530db2`
**End HEAD**: pending commit
**Commit**: pending

## Purpose

Define the boundary for the first future official public-data local run without importing, downloading, inspecting, or running official ARC data yet.

## 1) Owner approval checkpoint

### Required approval

Before any official public ARC data is used, the owner must explicitly approve:

- the exact public-data source location,
- the exact source version or snapshot identifier,
- the checksum(s) for the source bundle,
- the intended local phase (`phase_2_public_parse_scorer_validation` or later),
- the intended read-only evaluation scope.

### Required record

Approval must record, at minimum:

- source type,
- source location,
- version or snapshot id,
- checksum,
- approval timestamp or approval reference,
- approved phase.

### Must not be touched before approval

Until approval exists, do not touch:

- any public ARC source bundle path,
- any local official-data cache or extracted directory,
- any future public-data adapter/scorer boundary file meant for live evaluation,
- any runtime/chat/UI/provider path,
- any `.weslr` path.

## 2) Official public-data source protocol

### Allowed source type

A future public-data run may use only a **local, read-only, checksum-verified bundle** that was provisioned by the owner or a trusted release process.

### Forbidden source types

- hidden/private data,
- user-private or cross-user data,
- synthetic fixtures presented as official,
- mixed official/synthetic score inputs,
- network-fetched or browser-scraped ARC data.

### Read-only local bundle rule

The source must be mounted or copied read-only. The run may read from the bundle, but must not mutate it, normalize it in place, or rewrite it.

### Checksum/provenance rule

A future run must verify checksum/provenance before parsing or scoring. Missing checksum is a stop condition.

### No mutation/normalization-in-place rule

Parsing may produce in-memory normalized structures, but the original source bundle must remain unchanged on disk.

## 3) Local run phases

### Phase 2 — public official data parse/scorer validation

Purpose:

- confirm the official bundle parses,
- confirm exact-grid scorer behavior on public official format,
- confirm logs and outputs remain answer-safe,
- do not claim a competition result.

### Phase 3 — local public run

Purpose:

- perform a fully offline local run on approved public data,
- compute local public results,
- preserve exact provenance and auditability.

### Phase 4 — post-run contamination audit

Purpose:

- verify no answer leakage,
- verify no hidden/private data use,
- verify no solver self-modification,
- verify logs contain only safe metadata,
- verify claim boundaries.

### Phase 5 — competition participation design only if gates pass

Purpose:

- design submission workflow only after successful validation and audit,
- no automatic submission authority,
- no live competition participation without a separate approval.

## 4) Public-data adapter boundary

A future public-data adapter may parse official public data, but must enforce:

- exact source checksum/provenance verification,
- no expected-output leakage to solver-visible paths,
- no hidden/private data use,
- no synthetic/official score mixing,
- no solver changes during or after the run unless explicitly labeled as post-run analysis,
- no logs containing expected answers, hidden answers, or latent rules,
- no public-data mutation in place,
- no `.weslr` IO.

The adapter should emit solver-visible input only, with any expected outputs withheld from candidate-generation paths.

## 5) Local scorer boundary

A future official scorer must:

- use exact grid equality,
- preserve exactly-two-output behavior where that format applies,
- keep ARC-AGI-1 and ARC-AGI-2 separated if both are ever used,
- record task IDs, status, timing, and score metadata only,
- never log hidden/private answers,
- never mix official and synthetic results,
- never infer official percentage from toy or parse-only work.

## 6) Offline evaluation boundary

Future local evaluation must run with:

- no internet,
- no web,
- no provider/model calls,
- no tool calls,
- no retrieval,
- no `.weslr` IO,
- no runtime/chat/UI path,
- no solver self-modification during the run.

Any of the above immediately stops the run.

## 7) Claim policy

### After a toy run

May claim only:

- toy-only behavior,
- synthetic/local shape validation,
- `official_percentage_claimable = none/0`.

### After parse-only public-data validation

May claim only:

- parse validation passed,
- checksum/provenance verified,
- no scoring result.

May not claim:

- any official ARC score,
- any competition result,
- any local-public performance percentage.

### After a local public run

May claim only:

- local public run completed,
- exact run scope and provenance,
- score metadata and audit trail.

May not claim:

- competition submission success,
- public ARC leaderboard standing,
- performance outside the approved source and phase.

### After a failed run

May claim only:

- the run failed,
- the stop reason,
- the phase reached.

### After post-run solver modification

May claim only:

- a post-run modification occurred,
- it is explicitly labelled post-run,
- it is excluded from the original run result.

### After competition submission

May claim only after separate approval:

- submission was made,
- submission target and hash/reference,
- no claim beyond the approved scope.

## 8) Required future artifacts

Likely future files/reports:

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

## 9) Stop conditions

Stop the run immediately if any of the following occurs:

- missing checksum,
- unexpected official/private/hidden data,
- answer leakage,
- malformed official format,
- scorer mismatch,
- solver-visible expected output,
- internet/tool/model access,
- dirty protected files,
- changed solver after run,
- `.weslr` access,
- any runtime/chat/UI/provider path access.

## Current repo/report status check

Observed at write time:

- `git status --short --untracked-files=all` shows the unrelated dirty file:
  - `weslr/tests/continuity/governance_scorecards.json`
- `git status --short --untracked-files=all` also shows unrelated untracked docs already present:
  - `docs/WESLR_ARC_SYNTHETIC_TASK_CONTRACT_SCHEMA_REVIEW_V1.md`
  - `weslr/tests/docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_V1.md`
  - `weslr/tests/docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_RESULT_V1.md`
  - `weslr/tests/docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_RUN_RESULT_V1.md`

## Standard footer

Commit note: this report was prepared before final commit. Final commit hash is recorded in the post-commit receipt.
