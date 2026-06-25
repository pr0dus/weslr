# WESLR ARC Prize 2025 Kaggle Data Contract Alignment V1

## Status
Design only. No Kaggle data downloaded. No ARC data ingested. No submission adapter implemented.

## Scope
Public Kaggle page reviewed only at:
- `https://www.kaggle.com/competitions/arc-prize-2025/data`

Observed visibility:
- Page is reachable.
- Unauthenticated fetch/browser exposure did **not** reveal a readable dataset table or contract body.
- No protected/login-only content was bypassed.

## Owner-provided screenshot observations
The owner-provided screenshot adds screenshot-derived public metadata only. It does **not** add downloaded data, task examples, grids, answer keys, or solution contents.

### Screenshot-based file manifest
Visible files:
- `arc-agi_evaluation_challenges.json`
- `arc-agi_evaluation_solutions.json`
- `arc-agi_test_challenges.json`
- `arc-agi_training_challenges.json`
- `arc-agi_training_solutions.json`
- `sample_submission.json`

Visible page summary:
- Data Explorer visible
- data size shown as `6.91 MB`
- summary shows `6 files`, `.json`

### Competition-rules / join gate
Visible gate text:
- “To see this data you need to agree to the competition rules.”
- “Join the competition to view the data.”

### Multiple-test-input implication
Visible page text says tasks generally have one test input, but a small number of tasks may require predictions for two test inputs.

### Challenge / solution separation implication
The screenshot shows separate challenge and solution files, which implies the Kaggle contract separates inputs/challenges from solution payloads.

### Sample submission implication
The visible `sample_submission.json` implies a dedicated submission-format file is part of the public contract surface.

### Screenshot-derived boundary statement
- This section is screenshot-derived metadata only.
- No Kaggle data was downloaded or ingested.
- No task examples, grids, answer keys, or solution contents were copied into the repo.

## Visible public contract summary
From the accessible public surface and the owner screenshot, the following was visible:
- competition page exists
- screenshot exposes a file manifest and join gate
- no downloadable dataset contents were accessed
- no submission examples were retrieved beyond the visible sample submission filename

So the contract is still only partially visible: enough to identify the public file manifest and gating, but not enough to confirm exact row/field contents from the page body alone.

## WESLR current ARC-style shape
### Phase 1 schema packet
- `task_id`
- `task_source`
- `train_pairs[]`
- `test_input`
- `grid_format`
- `palette`
- `object_candidates`
- `transformation_candidates`
- `constraint_candidates`
- `candidate_outputs`
- `validation_results`
- `failure_notes`
- `trace`

### Train pair shape
- `pair_id`
- `input_grid`
- `output_grid`
- `notes`
- `input_grid_metadata`
- `output_grid_metadata`
- `validation`

### Phase 2/3 additions
- object candidates
- primitive registry metadata
- candidate validation metadata
- bounded dry-run / stress metadata
- no-score / no-leakage flags

## WESLR compatibility summary
| Kaggle ARC-style need | WESLR status | Notes |
|---|---|---|
| Challenge/task JSON container | Partial | `task_id`, `train_pairs`, `test_input` map well, but WESLR is still synthetic-first and metadata-heavy. |
| Training examples | Partial | `input_grid` / `output_grid` maps cleanly to train pairs, but boundary rules are internal-synthetic only. |
| Test input | Partial | `test_input` maps cleanly as grid metadata, but no public task ingestion yet. |
| Submission attempts / top-N outputs | Missing | WESLR has candidate packets, but not Kaggle submission-row formatting. |
| Train/eval/test/private separation | Partial | WESLR explicitly tracks no-leakage flags, but no Kaggle contract integration layer exists yet. |
| Test-output leakage avoidance | Yes | Dry-run/stress code explicitly marks `uses_test_output = False` and `lookup_table_detected = False`. |

## Schema gaps
- No Kaggle manifest parser contract layer yet
- No canonical ARC competition JSON parser for public tasks
- No Kaggle challenge-vs-solution separation model
- No Kaggle evaluation-vs-test separation model
- No multiple-test-input support model
- No sample-submission parser
- No submission row serializer
- No top-N / multiple-attempt packet serializer
- No file naming contract layer
- No local-only dataset placement policy layer
- No no-commit dataset policy layer
- No public sample ingestion gate yet

## Submission-output gaps
WESLR does **not** yet have:
- Kaggle submission file builder
- candidate-to-row flattening
- top-N attempt serialization
- per-task attempt cap enforcement aligned to Kaggle format
- output deduplication / ranking contract
- competition upload adapter

## No-leakage boundary
This design must keep these rules explicit:
- no raw dataset retention in repo
- no commit of public ARC examples
- no hidden/private benchmark ingestion
- no answer-key leakage
- no evaluation-output reuse as training signal
- no test-output selection for candidate generation
- no task-ID/notes lookup-table candidate selection
- no Kaggle solution leakage into task-side artifacts
- no challenge/solution merge into a single runtime payload

## Local-only dataset placement rule
If public ARC data is ever used later:
- store it outside git-tracked source files
- keep it in a local-only, ignored working directory
- do not copy dataset payloads into docs, tests, or committed artifacts
- do not persist downloaded public benchmark files in repo history
- keep Kaggle challenge files and Kaggle solution files in separate local-only paths

## No-commit dataset rule
- never commit Kaggle data files
- never commit public ARC sample files
- never commit labels, answers, or evaluation keys
- never commit extracted benchmark examples into docs/tests as if they were source material
- never commit Kaggle challenge/solution contents into source artifacts

## Future approval gates
### Public sample ingestion gate
Require explicit approval before any public ARC sample ingestion, with a documented local-only storage rule.

### Kaggle submission adapter gate
Require explicit approval before any submission-format adapter or upload workflow is implemented.

## Recommended future adapter functions
Documented only for later work:
- `parse_arc_prize_2025_manifest_v1`
- `parse_arc_prize_2025_challenges_file_v1`
- `parse_arc_prize_2025_solutions_file_v1`
- `parse_arc_prize_2025_sample_submission_v1`
- `map_arc_prize_2025_task_to_weslr_packet_v1`
- `build_arc_prize_2025_submission_attempts_v1`
- `validate_arc_prize_2025_no_solution_leakage_v1`
- `enforce_arc_prize_2025_local_dataset_policy_v1`

## WESLR-to-Kaggle mapping
### Good fit
- `task_id` -> Kaggle task identifier
- `train_pairs` -> training examples
- `test_input` -> test input grid(s)
- `candidate_outputs` -> future submission attempts
- `failure_notes` / `trace` -> internal diagnostics only

### Gaps
- Kaggle-format submission rows are not yet modeled
- Kaggle public/eval/private split is not yet modeled explicitly
- challenge-vs-solution separation is not modeled as a first-class boundary
- multiple-test-input support is not modeled explicitly
- top-N candidate output ranking is internal only
- multiple-attempt serialization is not modeled explicitly
- no contract-safe serializer for upload-ready files exists

## Recommendation
Do **not** start public ARC sample ingestion now.

Recommended sequence:
1. finish this Kaggle contract boundary design
2. implement a schema-only Kaggle-format adapter
3. add a synthetic task-family generator that mirrors Kaggle shape
4. only then request approval for public sample ingestion
5. only after that consider a submission adapter

## Should Phase 4 start now?
No.

Phase 4 should wait until:
- Kaggle contract details are fully modeled
- schema-only adapter boundaries are reviewed
- synthetic task-family coverage is broadened
- no-leakage controls are proven on local synthetic data first

## Final note
This alignment pass says WESLR’s current ARC-style schema is structurally close enough for task/train/test modeling, but still too synthetic and metadata-bound to jump directly into public ARC ingestion or submission wiring.