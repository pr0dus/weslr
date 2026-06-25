# WESLR ARC Prize 2026 ARC-AGI-2 Rules and Contract Alignment V1

## Status
Design only. No Kaggle data downloaded. No ARC data ingested. No Kaggle adapter implemented. No score claims.

## Source distinction
This alignment is based on distinct public sources:

### ARC Prize 2025 Kaggle data page / screenshot observations
- Kaggle ARC Prize 2025 Data tab screenshot provided by the owner
- screenshot-derived file manifest and competition-rules gate
- no data downloaded or ingested

### ARC Prize 2026 ARC-AGI-2 overview
Public ARC-AGI-2 overview sources visible in this session:
- `https://arcprize.org/arc-agi-2` (redirected to the announcement page)
- `https://arcprize.org/blog/announcing-arc-agi-2-and-arc-prize-2025`
- `https://arcprize.org/blog/arc-agi-2-technical-report`

### ARC Prize 2026 ARC-AGI-2 rules / guide surface
Public guide sources visible in this session:
- `https://arcprize.org/guide`
- `https://arcprize.org/guide/1`
- `https://github.com/arcprize/ARC-AGI-2`

### Kaggle 2026 competition pages
The Kaggle ARC-AGI-2 overview/rules URLs were reachable, but their rendered contract text was not machine-readable in this gateway/browser session. Kaggle-specific submission mechanics therefore remain partially TBD here unless separately verified.

## 2025 screenshot observations
Screenshot-derived public metadata only:

### File manifest
- `arc-agi_evaluation_challenges.json`
- `arc-agi_evaluation_solutions.json`
- `arc-agi_test_challenges.json`
- `arc-agi_training_challenges.json`
- `arc-agi_training_solutions.json`
- `sample_submission.json`

### Visible page summary
- data size shown: `6.91 MB`
- `6 files`
- `.json`

### Gate text
- “To see this data you need to agree to the competition rules.”
- “Join the competition to view the data.”

### Implications from the screenshot
- challenge and solution files are separated
- sample submission is part of the public contract surface
- tasks can have more than one test input in some cases

### Boundary statement
- screenshot-derived metadata only
- no Kaggle data downloaded or ingested
- no task examples, grids, answer keys, or solution contents copied into the repo

## 2026 ARC-AGI-2 overview / rules observations
Public ARC-AGI-2 sources indicate:

### Dataset and task structure
- ARC-AGI-2 keeps the ARC-AGI-1 format
- tasks are JSON with `train` and `test`
- each pair has `input` and `output`
- grids are rectangular matrices of integers 0-9
- public training set: 1000 tasks
- public evaluation set: 120 tasks
- semi-private eval set: 120 tasks on Kaggle
- private eval set: 120 tasks on Kaggle

### Difficulty / calibration
- ARC-AGI-2 tasks were human-calibrated
- every task was solved by at least 2 humans in 2 attempts or less
- public eval / semi-private / private sets are calibrated to similar difficulty

### Attempt / scoring contract
- the benchmark uses pass@2 semantics
- each test input gets exactly 2 attempts in the public ARC-AGI-2 materials
- exact-match is required for correctness

### Guide / viewer note
The static task viewer guide page explains the interactive viewer and says it does not enforce the 2-trial rule in that browser exercise. That viewer note is not the competition contract itself; the benchmark contract still uses pass@2.

### Kaggle-specific rules still TBD in this session
Because the Kaggle rules page was not machine-readable here, the following remain to be verified directly on the Kaggle rules page if needed:
- Kaggle notebook submission requirement, if any
- no-internet / offline execution boundary during evaluation, if any
- open-source / reproducibility eligibility requirements, if any
- hardware / compute constraints, if any
- exact submission filename / packaging rules, if any
- prize / eligibility boundaries, if any

## WESLR adapter implications
WESLR now needs explicit support for:
- challenge file parser
- solution file parser only for allowed local/public training/evaluation validation
- test-input-only packet path
- multiple test inputs per task
- exactly two attempts per test input
- top-2 candidate ranking
- submission JSON serializer
- no-internet / self-contained execution boundary
- local-only dataset path policy
- no-commit dataset policy
- no solution leakage / no test-output leakage policy
- open-source-readiness boundary for any prize-eligible submission

## Gap analysis against current WESLR code
Current relevant modules:
- `weslr/arc_style_grid_schema_helpers.py`
- `weslr/arc_style_grid_adapter_phase2.py`
- `weslr/arc_style_grid_solver_dry_run.py`
- `weslr/arc_style_grid_generalization_stress.py`

Current gaps:
- no Kaggle / ARC-AGI-2 manifest parser yet
- no sample_submission parser yet
- no top-2 attempt packet yet
- no multiple-test-input task packet check yet
- no submission JSON writer yet
- no Kaggle notebook / offline execution contract yet
- no public dataset ingestion gate yet
- no local path policy helper yet
- no challenge-vs-solution boundary model in the adapter layer

Current WESLR shape is still mostly internal-synthetic and metadata-first. The current `test_input` packet path is structurally useful, but it is not yet aligned to ARC-AGI-2 submission mechanics.

## Required future policy surfaces
- local-only dataset placement policy
- no-commit dataset policy
- no solution leakage policy
- no test-output leakage policy
- Kaggle submission gate policy
- Kaggle offline execution gate policy

## Recommended future adapter functions
Documented only for later work:
- `parse_arc_prize_2026_arc_agi_2_challenges_v1`
- `parse_arc_prize_2026_arc_agi_2_solutions_v1`
- `parse_arc_prize_2026_arc_agi_2_sample_submission_v1`
- `map_arc_agi_2_task_to_weslr_packet_v1`
- `build_arc_agi_2_top2_attempt_packet_v1`
- `rank_arc_agi_2_candidate_attempts_top2_v1`
- `serialize_arc_agi_2_submission_json_v1`
- `validate_arc_agi_2_no_solution_leakage_v1`
- `enforce_arc_agi_2_local_dataset_policy_v1`
- `validate_arc_agi_2_offline_execution_contract_v1`

## Recommended next lane
Do **not** jump to public data ingestion yet.

Recommended order:
A. Commit this alignment doc.
B. Implement schema-only ARC-AGI-2 top-2 attempt / submission contract helpers using synthetic data only.
C. Expand synthetic task-family generators.
D. Add controlled local public-data ingestion gate only after approval.
E. Build public sample / evaluation harness.
F. Build Kaggle notebook / submission adapter only after measured local proof.

## Final recommendation
Phase 4 should **not** start yet. The right next move is schema-only alignment plus synthetic top-2 submission modeling, then a reviewed public-data gate later.

## Explicit safety note
This document does not contain downloaded benchmark files, benchmark grids, solutions, or answer keys.
