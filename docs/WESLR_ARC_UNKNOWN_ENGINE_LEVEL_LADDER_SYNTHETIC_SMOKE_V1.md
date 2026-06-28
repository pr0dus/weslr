# WESLR ARC UNKNOWN ENGINE LEVEL LADDER SYNTHETIC SMOKE V1

## Recovery status
This document is a **recovered / reconstructed current-branch smoke artifact**.

- Current branch recovery: **yes**
- Original cited commit `98eed788b2a76ba2b41276ea41fc45c5694fa456` present locally: **no**
- Proven historical provenance for an original prior smoke doc: **no**
- Values below are reconstructed from current branch code, current local smoke execution, existing committed smoke-metrics docs, and owner receipts where explicitly noted

This is not represented as the original missing `98eed...` smoke artifact.

## Recovered smoke command
```bash
python -c "import sys; sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean'); from weslr.arc_style_synthetic_solver_suite import run_arc_style_synthetic_solver_suite_v1; print(run_arc_style_synthetic_solver_suite_v1())"
```

## Current-branch recovered smoke summary
Recovered from current local branch execution:
- Generated ladder levels: **12**
- Attempted tasks: **36**
- Top-2 packets evaluated: **48**
- Task exact count: **31**
- Task exact rate: **31 / 36 = 0.8611111111111112**
- Packet exact count: **41**
- Packet exact rate: **41 / 48 = 0.8541666666666666**
- Packet partial count: **3**
- Packet unsupported count: **4**
- Failed count: **0**
- Skipped count: **0**
- Threshold basis: **`task_exact_rate`**
- Internal 85% signal on current branch: **above threshold**

## Frontier note
Owner-provided receipt value, carried forward only as recovered-from-receipt context:
- Trusted frontier: **`reflect_object_horizontal_or_vertical` at Tier 1**

This frontier statement is preserved as a receipt-based recovery note, not as a newly proven historical provenance claim.

## Original ambiguity note
The earlier smoke framing was ambiguous because packet-level exact counts can exceed attempted task counts:
- Attempted tasks are task-level counts
- Top-2 exacts are packet-level counts
- Therefore `41 exact packets > 36 attempted tasks` is possible without contradiction

The current branch now exposes both task-level and packet-level metrics so the distinction is explicit.

## Boundary statement
- Internal synthetic-only ARC-style work: **yes**
- Public ARC data used: **no**
- Kaggle data used: **no**
- Official scoring claimed: **no**
- ARC-AGI-1 performance claimed: **no**
- ARC-AGI-2 performance claimed: **no**
- Kaggle readiness claimed: **no**

## Provenance note
This is recovered/current-branch documentation produced after the original referenced smoke artifact was found missing from local history. It documents the current valid branch state only and does not claim exact original historical provenance.
