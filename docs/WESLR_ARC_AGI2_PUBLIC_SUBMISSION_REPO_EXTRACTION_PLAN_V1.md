# WESLR ARC-AGI-2 Public Submission Repo Extraction Plan V1

## 1. Current source state
- Repository: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Actual preflight HEAD: `3dd6954d733f0640ee56609cd79942923653a3f7`
- Previous dummy implementation commit: `3dd6954d733f0640ee56609cd79942923653a3f7`
- Dummy implementation report: present in workspace, still uncommitted
  - `docs/WESLR_ARC_OFFICIAL_PUBLIC_PARSE_SCORER_SURFACE_DUMMY_IMPLEMENTATION_V1.md`
- Official/public ARC data untouched: yes
- Official percentage remains: none/0

## 2. Public-vs-private rule
- Do not publish the whole WESLR repo.
- Publish only the reproducible ARC-AGI-2 submission package.
- If the submitted notebook imports or depends on any WESLR module, that module is part of the method and must be included/open-sourced in the package.
- Private-only dependencies are not acceptable for a reproducible prize-eligible submission.

## 3. Candidate public repo name
Candidates:
- `weslr-arc-agi2-submission`
- `weslr-arc-prize-2026`
- `weslr-arc-agi2-kaggle`

Recommended:
- `weslr-arc-agi2-submission`

Reason: narrow, explicit, and accurately describes a Kaggle-ready competition package without overclaiming scope.

## 4. Public repo contents
Proposed public repo layout:

- `README.md`
- `LICENSE`
- `NOTICE.md`
- `submission.ipynb`
- `requirements.txt`
- `src/`
  - `src/weslr_arc_solver/`
    - `__init__.py`
    - `adapter.py`
    - `emitter.py`
    - `scorer.py`
    - `solver.py`
    - `grid.py`
    - `schema.py`
    - `public_gate.py`
    - `redaction.py`
- `tests/`
  - `tests/fixtures/dummy_no_data/`
  - `tests/test_*.py`
- `docs/`
  - `docs/METHOD.md`
  - `docs/REPRODUCIBILITY.md`
  - `docs/NO_INTERNET_EVALUATION.md`
  - `docs/PRIVATE_EXCLUSION_CHECKLIST.md`

Optional:
- `scripts/` for local smoke tests and packaging helpers
- `pyproject.toml` if the package is built as an installable wheel

## 5. File extraction inventory
Likely needed WESLR source files:

| WESLR file | Suggested treatment | Why |
|---|---|---|
| `weslr/arc_agi2_submission_contract.py` | include after public cleanup | Core top-2 submission contract and validation shapes |
| `weslr/arc_primitive_sequence_grid_reconstruction.py` | include after public cleanup | Reusable grid reconstruction primitive |
| `weslr/arc_style_grid_schema_helpers.py` | include after public cleanup | Grid/schema helpers likely reused in public solver code |
| `weslr/arc_task_contract_schema.py` | include after public cleanup | Task/grid contract normalization support |
| `weslr/arc_official_contamination_boundary.py` | include as-is | Useful boundary guard if it stays metadata-only and cleanup is small |
| `weslr/arc_official_public_data_approval_gate.py` | include after public cleanup | Approval/manifest gate is part of the public boundary plan |
| `weslr/arc_official_public_data_adapter.py` | include after public cleanup | Public dummy adapter shape and future source-bundle boundary |
| `weslr/arc_official_public_data_emitter.py` | include after public cleanup | Two-output emitter shape |
| `weslr/arc_official_public_data_scorer.py` | include after public cleanup | Exact-equality scorer shape |
| `weslr/arc_official_public_data_harness.py` | rewrite standalone | Current harness is WESLR-specific; public repo should be leaner |
| `weslr/arc_official_public_data_report_redactor.py` | include after public cleanup | Report redaction is part of reproducibility/anti-leakage |
| `weslr/tests/fixtures/arc_official_public_dummy_no_data_v1.json` | include as-is | Safe synthetic smoke fixture |
| `weslr/tests/test_arc_official_public_data_adapter.py` | include after public cleanup | Useful as public regression test shape |
| `weslr/tests/test_arc_official_public_data_emitter.py` | include after public cleanup | Public emitter regression test shape |
| `weslr/tests/test_arc_official_public_data_scorer.py` | include after public cleanup | Public scorer regression test shape |
| `weslr/tests/test_arc_official_public_data_harness.py` | include after public cleanup | Public harness regression test shape |
| `weslr/tests/test_arc_official_public_data_report_redactor.py` | include after public cleanup | Public redaction regression test shape |
| `weslr/arc_style_grid_solver_dry_run.py` | rewrite standalone | Likely contains broad internal scaffolding; public package should isolate only necessary solver logic |
| `weslr/arc_synthetic_official_shape_blind_runner.py` | exclude private/internal | Internal synthetic runner, not needed for public submission package |
| `weslr/arc_synthetic_official_shape_blind_cli.py` | exclude private/internal | Internal CLI wrapper, not Kaggle submission code |
| `weslr/arc_synthetic_official_shape_frozen_solver_challenge.py` | exclude private/internal | Internal challenge harness, not public package method |

## 6. Must-exclude inventory
Do not include in the public repo:
- private WESLR governance/design docs unrelated to the package
- OpenClaw / OCC / Nova instructions, handoffs, memory files, and agent context
- `.weslr` data and any runtime state
- website/private deployment material
- secrets, tokens, auth configs, account-specific files
- user-specific absolute paths or workspace-specific assumptions
- unrelated WESLR product code
- official/public ARC data bundles
- hidden/private data
- experimental reports that make unsupported official-score or public-score claims
- `__pycache__` / compiled artifacts / local build debris

## 7. Kaggle notebook shape
Notebook behavior:
- load Kaggle-provided input files from Kaggle paths only when running in Kaggle
- run with no internet
- import only bundled source code from the public package
- emit exactly two outputs per ARC-AGI-2 test input if the competition format requires it
- write submission output in the exact Kaggle-required format
- avoid ChatGPT/OCC/model/provider/API calls entirely during evaluation
- no manual repair after execution starts
- fail closed if expected Kaggle paths or package modules are missing

## 8. Reproducibility policy
- Exact source baseline: `3dd6954d733f0640ee56609cd79942923653a3f7`
- Public package should carry a code-hash manifest for the exported tree
- Dependency list should be pinned and minimal
- Include a no-internet local smoke test command
- Include a dummy/no-data local smoke test
- Any public-data local run is optional and only after separate owner approval
- Notebook and package should be reproducible from the public repo alone

## 9. Open-source timing policy
- The repo may remain private during packaging
- Make the repo public before any prize-eligible Kaggle submission or public performance claim
- Do not claim an official score until a Kaggle/public run result exists
- Re-check current Kaggle/ARC rules immediately before final submission

## 10. Risk checklist
- private code accidentally included
- solver depends on private WESLR modules
- notebook uses internet or API calls
- public repo is missing code needed to reproduce the submission
- official ARC data accidentally committed
- unsupported claims in README or docs
- license ambiguity
- Kaggle input path mismatch
- runtime limit exceeded
- dummy/no-data fixtures accidentally treated as competition evidence

## 11. Recommended next lane
- Create a local export staging directory only, then map the public package tree against the WESLR source inventory before any GitHub repo creation.
