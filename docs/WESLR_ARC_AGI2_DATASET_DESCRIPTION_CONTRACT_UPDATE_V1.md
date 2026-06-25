# WESLR ARC-AGI-2 Dataset Description Contract Update V1

Start HEAD: `c716d1905acbf59276fabec04818867a1a8c3917`

## Purpose
Record the owner-provided ARC-AGI-2 dataset description as contract guidance before any primitive expansion or future parser work.

## Contract findings from the owner description
- ARC tasks are novel; memorized reasoning templates are not enough.
- The format differs from the prior competition and needs careful handling.
- A test-taker sees train demonstration pairs plus test input grid(s).
- The goal is to construct output grid(s) for the test input grid(s).
- Each test input gets exactly 2 trials/attempts.
- Scoring is exact-match only; only a perfectly matching grid counts.
- Grid contract: rectangular matrix, list-of-lists, integers 0–9 inclusive, minimum 1x1, maximum 30x30.
- Task object contract: `train` and `test`; `train` contains `{input, output}` pairs; `test` contains test input(s).
- File contract includes training challenges/solutions, evaluation challenges/solutions, test challenges, and sample submission.
- The visible test-challenge file may be placeholder data; notebook rerun swaps in the real unseen test challenges.
- Private evaluation is rerun-based with 240 unseen tasks; the rerun file is `arc-agi_test_challenges.json`.
- Most tasks have one test input; a small number have two test inputs.
- Filename spelling may differ between underscore-style and hyphen-style forms; parser policy should be manifest/config-driven until real local files are approved and inspected.

## Implications for WESLR
- Keep exactly-two-attempt validation.
- Preserve multiple-test-input support.
- Enforce grid size/value limits when real dataset parsing is added.
- Add a future challenge/solution parser boundary.
- Add a visible-placeholder-test-file warning.
- Add a no-template-memorization warning.
- Add no-test-output leakage validation.
- Add a future local-only dataset path policy.
- Require future sample_submission validation before any Kaggle-ready claim.
- Do not treat the visible test placeholder as the real private test.
- Do not claim benchmark score from synthetic results.

## Helper compatibility check
Current `weslr/arc_agi2_submission_contract.py` behavior:
- Exactly two attempts per top-2 packet: **yes** (`validate_arc_agi2_top2_attempt_packet_v1` checks `attempt_count_must_be_two`).
- Multiple test inputs supported: **yes** (`build_arc_agi2_submission_task_entry_v1` stores multiple `test_input_packets`, and the synthetic suite already uses this path).
- Grid integer range 0–9 enforced: **no** (the helper checks structure/rectangularity/size, but not a hard 0–9-only value bound).
- Grid size 1x1 to 30x30 enforced: **yes, mostly** (non-empty plus helper width/height bounds prevent empty/oversized grids; `build_arc_style_grid_metadata_v1` caps max size at 30x30).
- Kaggle-ready claim avoided: **yes** (`kaggle_ready` defaults false and validation rejects true).
- Solution/test-output leakage flags avoided: **yes** (`uses_test_output`, `uses_solution_file`, `uses_answer_key`, hidden/private and shortcut flags are normalized/validated).

## Parser policy note
Future ARC dataset parsing should stay manifest/config-driven and local-file approved; do not hardcode one filename spelling until real approved local files are inspected.

## WESLR alignment note
This update is documentation/contract guidance only. It does not authorize dataset ingestion, public sample ingestion, benchmark copying, competition submission, or primitive expansion.
