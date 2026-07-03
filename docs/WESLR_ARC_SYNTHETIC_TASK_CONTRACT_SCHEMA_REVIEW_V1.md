# WESLR ARC Synthetic TaskContract Schema — Review (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `REVIEW_ARC_SYNTHETIC_TASK_CONTRACT_SCHEMA_V1`
**Start HEAD**: `298dcf73c6aec48053ee182b6fe1666b6037446b`
**End HEAD**: `a5296eba93fab5493df2ddf5fe481e0cab218b30`
**Commit**: `yes`
**actual preflight HEAD**: `a5296eba93fab5493df2ddf5fe481e0cab218b30`

## Provenance note

- The implementation report in this tree claims `End HEAD` / `Commit` = `1a707e752127452e50a7d9552b829088f88a7916`.
- The live repo HEAD is `a5296eba93fab5493df2ddf5fe481e0cab218b30`.
- `1a707e75` is the immediate predecessor commit with the same schema/test/code tree; `a5296eba` keeps those code files and updates only the implementation report.
- So the mismatch is report-vs-current-HEAD, not code-vs-HEAD.

## Files verified

- `weslr/arc_task_contract_schema.py`
- `weslr/tests/test_arc_task_contract_schema.py`
- `weslr/arc_task_difficulty_ladder.py`
- `docs/WESLR_ARC_SYNTHETIC_TASK_CONTRACT_SCHEMA_IMPLEMENTATION_V1.md`

## Review result

- Core TaskContract schema: **yes**
- T1–T7 contract validation: **yes**
- T3–T7 internal requirements: **yes**
- T5 non-counting: **yes**
- probe/sentinel non-counting: **yes**
- solver-visible export stripping: **no**
- leakage detector: **yes**
- coverage summary: **partial**
- safety boundaries: **yes**

## Findings

1. `export_solver_visible_task()` does **not** strip `primitive_name` / `primitive_names` if they appear in `solver_visible_view`.
2. `detect_task_contract_leakage()` catches the requested leak classes used in the tests, but the coverage summary only reports aggregate counts; it does not explicitly identify non-counting contracts.

## Validation

- `git diff --check`: PASS
- `python weslr/tests/release_gate_v1.py`: PASS
- `./scripts/weslr_release_check.sh`: PASS
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`: PASS

## Receipt

- Start HEAD / End HEAD / Commit: `298dcf73c6aec48053ee182b6fe1666b6037446b` / `a5296eba93fab5493df2ddf5fe481e0cab218b30` / `yes`
- actual preflight HEAD: `a5296eba93fab5493df2ddf5fe481e0cab218b30`
- provenance verified: yes
- HEAD mismatch explained: yes
- files changed verified: yes
- TaskContract schema verified: yes
- T1–T7 validation verified: yes
- T3–T7 internal requirements verified: yes
- T5 non-counting verified: yes
- probe/sentinel non-counting verified: yes
- solver-visible export stripping verified: no
- leakage detector verified: yes
- coverage summary verified: no
- safety boundaries verified: yes
- validation: PASS
- push avoided: yes
- recommended next lane: tighten solver-visible stripping and make coverage summary explicitly enumerate non-counting contracts
