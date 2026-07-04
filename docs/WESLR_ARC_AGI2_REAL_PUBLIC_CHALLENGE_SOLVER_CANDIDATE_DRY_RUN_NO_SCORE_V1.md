# WESLR ARC-AGI2 Real Public Challenge Solver Candidate Dry Run No-Score V1

## Provenance / start state
- Repository: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`
- Start HEAD: `e904c42290ddd7d9fb309ed8c6f0074651f56ac3`
- End HEAD: `bb77b29ee5c0f351afa3344f7760fffca1c74a96`
- Commit status: committed in this lane
- Actual preflight HEAD: `e904c42290ddd7d9fb309ed8c6f0074651f56ac3`

## Source bundle
- Source path: `/data/data/com.termux/files/home/arc-agi2-public-source/arc-prize-2026-arc-agi-2.zip`
- Checksum algorithm: `sha256`
- Checksum value: `d00746ef4e06a515ad53bde4dff276dc8ef5a26829a0ebeafc8cf8ba6371abaa`
- Checksum match: `true`
- Manifest phase: `public_challenge_solver_candidate_dry_run_no_scoring`

## Challenge/input files used
- `arc-agi_evaluation_challenges.json`
- `arc-agi_test_challenges.json`
- `arc-agi_training_challenges.json`

## Solution-file handling
- Solution files opened: `no`
- Official/public ARC solution data parsed: `no`

## Challenge/input counts
- `arc-agi_evaluation_challenges.json`: `120` tasks / `172` test inputs
- `arc-agi_test_challenges.json`: `240` tasks / `259` test inputs
- `arc-agi_training_challenges.json`: `1000` tasks / `1076` test inputs
- Total challenge tasks parsed: `1360`
- Total test inputs parsed: `259`

## Candidate artifact
- Candidate artifact path: `/data/data/com.termux/files/home/arc-agi2-public-source/solver_candidate_dry_run_v1/solver_candidates_no_scoring.json`
- Candidate artifact written: `yes`
- Candidate artifact outside git repos: `yes`
- Exactly-two-output validation: `pass`
- Artifact validation: `pass`

## Frozen solver/candidate hash result
- Hash guard: `pass`
- Frozen files unchanged:
  - `weslr/arc_agi2_public_challenge_solver_candidate_runner.py`
  - `weslr/arc_agi2_submission_contract.py`
  - `weslr/arc_primitive_sequence_grid_reconstruction.py`
  - `weslr/arc_style_grid_solver_dry_run.py`

## Redaction / leakage audit
- Redaction result: `pass`
- Leakage audit: `pass`
  - raw grids logged: `false`
  - solution values logged: `false`
  - reference leakage logged: `false`
  - solution files opened: `false`
  - solver run: `true`
  - candidate generation: `true`
  - scoring: `false`
  - submission: `false`

## Official/public ARC handling
- Official/public ARC data committed: `no`
- Official/public ARC data touched/read: `yes`
- Official/public ARC challenge data parsed: `yes`
- Official/public ARC solution data parsed: `no`
- Solver run on official/public challenge data: `yes`
- Candidate generation on official/public challenge data: `yes`
- Scoring official/public data: `no`
- Kaggle submission made: `no`
- Official percentage: `none/0`

## Readiness verdict
- `real_public_challenge_solver_candidate_dry_run_no_score_passed_ready_for_owner_decision_on_local_score_check`

## Recommended next lane
- Controlled local score-check boundary, still without Kaggle submission or official score claims.
