# WESLR ARC Official-Format Toy Local Scorer — Implementation (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `IMPLEMENT_ARC_OFFICIAL_FORMAT_TOY_LOCAL_SCORER_V1`
**Start HEAD**: `6ba360b125c6472336101d1770a2c384159378af`
**actual preflight HEAD**: `6ba360b125c6472336101d1770a2c384159378af`
**End HEAD**: pending commit
**Commit**: pending

## Result

- toy scorer implemented: yes
- tests implemented: yes
- toy fixtures only: yes
- official data untouched: yes
- exact grid equality verified: yes
- exactly-two-candidate scoring verified: yes
- aggregate toy percentage implemented: yes
- synthetic-as-official claim rejected: yes
- official percentage claimable remains none/0: yes

## Files

- `weslr/arc_official_format_toy_scorer.py`
- `weslr/tests/test_arc_official_format_toy_scorer.py`
- `docs/WESLR_ARC_OFFICIAL_FORMAT_TOY_LOCAL_SCORER_IMPLEMENTATION_V1.md`

## Behavior

- exact grid equality only, with strict shape and cell-type checks
- exactly two candidate outputs required per test input
- task solved if either candidate matches the expected output
- task failed if neither candidate matches
- malformed / missing / extra candidate sets are rejected
- per-test scoring metadata is returned
- aggregate toy scoring is returned across task runs
- contamination-boundary integration is enforced in `phase_1_toy_fixture_adapter`
- `toy_only` and `not_official_score` are set on score outputs
- solver-visible bundles stay stripped of `expected_output`
- official data class and hidden/private data remain rejected in the toy scorer phase
- synthetic toy scores cannot be claimed as official ARC performance

## Validation

- `python -m py_compile weslr/arc_official_format_toy_scorer.py weslr/tests/test_arc_official_format_toy_scorer.py weslr/arc_official_format_toy_adapter.py weslr/arc_official_contamination_boundary.py`: PASS
- `python -m pytest -q weslr/tests/test_arc_official_format_toy_scorer.py weslr/tests/test_arc_official_format_toy_adapter.py weslr/tests/test_arc_official_contamination_boundary.py`: PASS
- `python weslr/tests/release_gate_v1.py`: PASS
- `./scripts/weslr_release_check.sh`: PASS
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`: PASS
- `git diff --check`: PASS

## Current repo/report status check

Observed at write time:

- `git status --short --untracked-files=no` shows the unrelated modified files:
  - `docs/WESLR_REPORT_RECEIPT_COMMIT_PROVENANCE_PROTOCOL_V1.md`
  - `weslr/tests/continuity/governance_scorecards.json`
- untracked unrelated docs remain untouched.

## Receipt

- Start HEAD / End HEAD / Commit: `6ba360b125c6472336101d1770a2c384159378af` / `6ba360b125c6472336101d1770a2c384159378af` / `no`
- actual preflight HEAD: `6ba360b125c6472336101d1770a2c384159378af`
- toy scorer implemented: yes
- tests implemented: yes
- toy fixtures only: yes
- official data untouched: yes
- exact grid equality verified: yes
- exactly-two-candidate scoring verified: yes
- aggregate toy percentage implemented: yes
- synthetic-as-official claim rejected: yes
- official percentage claimable remains none/0: yes
- validation: PASS
- unrelated dirty files left uncommitted: yes
- push avoided: yes
- recommended next lane: `Separate cleanup lane for the modified provenance protocol report`

Commit note: this report was prepared before final commit. Final commit hash is recorded in the post-commit receipt.
