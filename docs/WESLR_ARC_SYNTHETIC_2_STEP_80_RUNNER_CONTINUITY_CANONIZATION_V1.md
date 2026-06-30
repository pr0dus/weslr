# WESLR ARC Synthetic 2‑Step 80 Runner Continuity Canonization V1

- **Dispatch**: `CANONIZE_CURRENT_ARC_SYNTHETIC_2_STEP_80_RUNNER_FOR_CONTINUITY_CHECKS_V1`
- **Repo**: `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch**: `occ-discovery-doctrine-implementation-20260613`
- **Start HEAD**: `73dd411cec20da10301c6d6b763d93f3fdd93a25`

## Purpose

Provide a stable, callable continuity check for the ARC synthetic 2‑step 80‑runner.  The check verifies that the runner:

1. Exists as the function `run_arc_style_synthetic_2_step_80_pilot_diagnostic_v1`.
2. Returns a combined‑80 result of **`76 exact / 4 partial / 0 unsupported / 0 failed`**.
3. Preserves the original 40 baseline (**`39 exact / 1 partial / 0 unsupported / 0 failed`**).
4. Represents **80 candidate rows** (`represented_candidate_rows == 80`).
5. Has **no unsupported** rows (`unsupported == 0`).
6. Preserves leakage‑boundary flags (no `uses_answer_key`, `uses_solution_file`, `uses_test_output_for_candidate_generation`).
7. Tracks the known stress‑residual (`accepted_stress_residual_count == 1`).

These invariants must hold for any future lane that depends on the 80‑runner.  The test suite includes a dedicated continuity test (`test_arc_style_synthetic_2_step_80_continuity_v1.py`).

## Invariants (asserted by the continuity test)

| Metric | Expected |
|--------|----------|
| `original_40_result` | `{ "exact": 39, "partial": 1, "unsupported": 0, "failed": 0 }` |
| `combined_80_result` | `{ "exact": 76, "partial": 4, "unsupported": 0, "failed": 0 }` |
| `represented_candidate_rows` | `80` |
| `unsupported` (derived) | `0` |
| `accepted_stress_residual_count` | `1` |
| Leakage flags (`uses_answer_key`, `uses_solution_file`, `uses_test_output_for_candidate_generation`) | `False` |

## JSON‑safe summary export

The runner already returns a JSON‑serializable dictionary containing the above fields (`original_40_result`, `combined_80_result`, `represented_candidate_rows`, `accepted_stress_residual_count`, and leakage flags).  No additional export code is required.

## Future regression detection

Any change that alters the above values will cause the continuity test to fail, alerting developers to unintended modifications.

## Recommendations

- Keep this document under version control as the canonical reference for the 80‑runner.
- Do not modify the runner implementation unless a new lane explicitly authorizes a change.
- Use the continuity test as a quick sanity‑check before merging any lane that may impact the runner.
