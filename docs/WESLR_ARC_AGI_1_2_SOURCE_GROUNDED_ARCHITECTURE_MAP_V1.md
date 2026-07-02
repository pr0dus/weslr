# WESLR ARC-AGI-1/ARC-AGI-2 Source-Grounded Architecture Map (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_AGI_1_2_SOURCE_GROUNDED_ARCHITECTURE_MAP_V1`
**Start HEAD**: `bc974ad91d656ac133e2e8f16086658feb9349b8`
**actual preflight HEAD**: `bc974ad91d656ac133e2e8f16086658feb9349b8`
**End HEAD**: pending commit
**Commit**: pending

## Purpose

Source-grounded architecture map for ARC-AGI-1 and ARC-AGI-2, based on official/public documentation only. No official task JSON files were opened, no datasets were downloaded, no tasks were run, and no hidden/private data was inspected.

## Source inventory

| Source class | URL / path | Observed date/version | Doc or dataset-bearing | Dataset files opened? | Notes |
|---|---|---:|---|---|---|
| ARC guide / shared format | `https://arcprize.org/guide/1` | fetched `2026-07-02T21:41:37Z` | documentation page | no | Shared ARC-AGI task-format guide; gives common task structure and test/scoring guidance |
| ARC-AGI-1 benchmark page | `https://arcprize.org/arc-agi/1` | fetched `2026-07-02T21:41:37Z` | documentation page | no | ARC-AGI-1 historical overview and dataset counts |
| ARC-AGI-2 benchmark page | `https://arcprize.org/arc-agi/2` | fetched `2026-07-02T21:41:37Z` | documentation page | no | ARC-AGI-2 benchmark overview, calibrated public/semi-private/private sets |
| ARC-AGI-2 competition page | `https://arcprize.org/competitions/2026/arc-agi-2` | fetched `2026-07-02T21:41:37Z` | documentation page | no | 2026 competition rules, submission format, exactly-two-output scoring, no internet during evaluation |
| ARC Prize testing policy | `https://arcprize.org/policy` | fetched `2026-07-02T21:41:37Z` | documentation page | no | Evaluation/public-vs-private policy, open-source benchmarking repo, verified leaderboard notes |

## Citation / provenance table

| Claim area | Source(s) | Provenance note |
|---|---|---|
| ARC-AGI task format is shared across 1 and 2 | `guide/1` | States ARC-AGI-1 and ARC-AGI-2 share the same structure and that tasks are JSON grids |
| ARC-AGI-1 historical role | `arc-agi/1`, `guide/1` | ARC-AGI-1 is the original 2019 benchmark and the recommended starting point in the guide |
| ARC-AGI-2 current competition role | `arc-agi/2`, `competitions/2026/arc-agi-2` | ARC-AGI-2 is the 2026 competition track and the benchmark used by the competition page |
| Exact-two-output scoring | `competitions/2026/arc-agi-2` | Explicitly requires predicting exactly 2 outputs per test input grid |
| Public/private/semi-private splits | `arc-agi/1`, `arc-agi/2`, `policy` | Both benchmark pages and the policy page describe public, semi-private, and private task tiers |
| Evaluation security and no-internet posture | `competitions/2026/arc-agi-2`, `policy` | Competition page says no internet access during evaluation; policy page explains secure testing and private sets |

## ARC-AGI-1 architecture summary

Observed from sources:

- ARC-AGI-1 is the original 2019 benchmark.
- It is the benchmark the guide recommends first for getting started before moving to ARC-AGI-2.
- The page describes 800 tasks total, split into:
  - 400 training tasks
  - 400 public evaluation tasks
  - 100 semi-private evaluation tasks
  - 100 private evaluation tasks
- Tasks are grid-based reasoning problems stored as JSON.
- A successful submission is a pixel-perfect description of the final task output.
- The guide states ARC-AGI-1 and ARC-AGI-2 share the same task structure.
- Public evaluation is for development/testing; do not leak evaluation tasks into the algorithm.

Architecture reading for WESLR:

- ARC-AGI-1 is the baseline / archive / getting-started benchmark for this year, not the active competition lane.
- It still matters as a shared-format benchmark and as the starting point for local development.
- Exact-match scoring is the core rule; pixel-perfect output is required.

## ARC-AGI-2 architecture summary

Observed from sources:

- ARC-AGI-2 is the 2026 competition track.
- The benchmark is designed to stress-test state-of-the-art reasoning systems.
- Dataset structure is calibrated and split into:
  - 1000 public training tasks
  - 120 public evaluation tasks
  - 120 semi-private evaluation tasks
  - 120 private evaluation tasks
- Public, semi-private, and private sets are calibrated to be roughly equal difficulty.
- The competition page says the objective is to reach 85% accuracy on the private evaluation dataset within Kaggle efficiency limits.
- The competition page requires exactly 2 outputs for every test input grid; if any of the two matches the ground truth exactly, the task scores 1.
- Submission must be through a Kaggle notebook.
- Evaluation has no internet access.
- Hardware and compute limits are announced with the competition launch.
- The competition page requires open sourcing to be eligible for prizes.

Architecture reading for WESLR:

- ARC-AGI-2 is the active competition target this year.
- Its architecture must be treated as a Kaggle-notebook competition pathway with an exact-two-output scoring rule and efficiency constraints.
- The public/semi-private/private split implies a stronger separation between development, leaderboard, and hidden evaluation behavior than ARC-AGI-1.

## Shared architecture components

Shared between ARC-AGI-1 and ARC-AGI-2:

- JSON task structure with `train` / `test` content
- grid-based reasoning inputs and outputs
- exact match / pixel-perfect scoring semantics
- public training data for development
- public evaluation data for local testing
- private/semi-private tiers for leaderboard security and benchmarking discipline
- provenance/security expectations that prevent evaluation leakage

## Differences between ARC-AGI-1 and ARC-AGI-2

| Area | ARC-AGI-1 | ARC-AGI-2 |
|---|---|---|
| Current role this year | Baseline/archive/supporting benchmark | Active 2026 competition track |
| Dataset scale | 800 tasks total in the page summary | 1000 train + 120 public eval + 120 semi-private + 120 private |
| Difficulty framing | Original benchmark from 2019 | Calibrated benchmark for reasoning models |
| Submission style | Pixel-perfect output description | Kaggle notebook submission |
| Output rule | Exact / pixel-perfect final output | Exactly 2 outputs per test grid |
| Efficiency framing | General benchmark development | Explicit efficiency limits and cost framing |
| Leaderboard structure | Historical private eval basis for past competitions | Private eval/private leaderboard in 2026 |

## Unknowns needing owner/source clarification

- Whether ARC-AGI-1 should be treated in WESLR as archive-only or as a live local benchmark target beyond foundational support.
- Whether WESLR should prioritize ARC-AGI-2 only for implementation, or maintain a first-class ARC-AGI-1 path alongside it.
- How to reconcile the competition-page strict no-internet rule with the policy page’s broader verified-submission notes about internet/external APIs.
- Whether any future WESLR local-run path should mirror the Kaggle notebook flow exactly or only the underlying scoring behavior.
- Whether source-provenance/checksum handling is only a WESLR safety requirement or a required part of any owner-approved local source packet.

## WESLR implementation implications

This map should later inform these WESLR files / layers:

- public data adapter
- public scorer
- two-output emitter
- local run harness
- offline runner
- runtime logger
- contamination audit
- claim report
- ARC-AGI-1/ARC-AGI-2 separation layer

Implication notes:

- The adapter must preserve the shared JSON/grid structure but keep ARC-AGI-1 and ARC-AGI-2 paths separated.
- The scorer must support exact equality and task-level scoring, with ARC-AGI-2’s exactly-two-output rule preserved where applicable.
- The emitter must be able to produce the two-output format for ARC-AGI-2 without implying that ARC-AGI-1 uses the same policy unless separately confirmed.
- The logger and claim report must stay metadata-only and never reveal hidden answers or internal task language.
- The contamination audit layer should enforce the public/semi-private/private separation before any future local run.

## Explicit boundary statements

- no official data touched
- official percentage remains none/0

## Owner/source clarification requested next

Please confirm:

- whether ARC-AGI-1 should be modeled as archive/baseline only or as an active local target in WESLR
- whether ARC-AGI-2 is the primary implementation target for the next lane
- whether WESLR should mirror Kaggle notebook submission behavior exactly or only its scoring semantics
- whether the stricter no-internet competition rule or the broader verified-submission policy should drive WESLR defaults for ARC-AGI-2
- whether repository metadata-only inspection is permitted for future source grounding

## Receipt

- Start HEAD / End HEAD / Commit: `bc974ad91d656ac133e2e8f16086658feb9349b8` / `bc974ad91d656ac133e2e8f16086658feb9349b8` / `no`
- actual preflight HEAD: `bc974ad91d656ac133e2e8f16086658feb9349b8`
- source inventory: yes
- citation/provenance table: yes
- ARC-AGI-1 architecture summary: yes
- ARC-AGI-2 architecture summary: yes
- shared architecture components: yes
- differences between ARC-AGI-1 and ARC-AGI-2: yes
- unknowns needing owner/source clarification: yes
- WESLR implementation implications: yes
- no official data touched: yes
- official percentage remains none/0: yes
- recommended next lane: `Await owner direction`
- validation: pending
- unrelated dirty files left uncommitted: yes
- push avoided: yes

Commit note: this report was prepared before final commit. Final commit hash is recorded in the post-commit receipt.
