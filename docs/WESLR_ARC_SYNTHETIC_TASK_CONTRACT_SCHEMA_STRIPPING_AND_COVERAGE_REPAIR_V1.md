# WESLR ARC Synthetic TaskContract Schema — Stripping and Coverage Repair (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `REPAIR_ARC_SYNTHETIC_TASK_CONTRACT_SCHEMA_STRIPPING_AND_COVERAGE_V1`
**Start HEAD**: `a5296eba93fab5493df2ddf5fe481e0cab218b30`
**actual preflight HEAD**: `a5296eba93fab5493df2ddf5fe481e0cab218b30`
**End HEAD**: pending commit
**Commit**: pending

## Repair result

- solver-visible export stripping repaired: yes
- stripping tests added: yes
- leakage detector tightened: yes
- coverage summary repaired: yes
- non-counting task enumeration implemented: yes
- probe/sentinel enumeration implemented: yes
- T5 enumeration implemented: yes
- T7 unresolved enumeration implemented: yes
- existing validation still passes: yes
- safety boundaries preserved: yes
- unrelated dirty files left uncommitted: yes
- push avoided: yes

## Files changed

- `weslr/arc_task_contract_schema.py`
- `weslr/tests/test_arc_task_contract_schema.py`
- `docs/WESLR_ARC_SYNTHETIC_TASK_CONTRACT_SCHEMA_STRIPPING_AND_COVERAGE_REPAIR_V1.md`

## Validation

- `python -m py_compile weslr/arc_task_contract_schema.py weslr/arc_task_difficulty_ladder.py weslr/tests/test_arc_task_contract_schema.py`: PASS
- `python -m pytest -q weslr/tests/test_arc_task_contract_schema.py`: PASS
- `python -m pytest -q weslr/tests/test_arc_task_difficulty_ladder.py`: PASS
- `python weslr/tests/release_gate_v1.py`: PASS
- `./scripts/weslr_release_check.sh`: PASS
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`: PASS
- `git diff --check`: PASS

## Notes

- Solver-visible export now strips the requested internal task-language and oracle fields recursively and returns only public solver-visible fields.
- Leakage detection now covers task-level, primitive-name, operation-sequence, confidence-policy, rival-grammar, insufficiency-reason, expected-output, and oracle metadata leakage.
- Coverage summary now enumerates non-counting, probe, sentinel, T5 primitive-insufficiency, and T7 unresolved contract IDs.
