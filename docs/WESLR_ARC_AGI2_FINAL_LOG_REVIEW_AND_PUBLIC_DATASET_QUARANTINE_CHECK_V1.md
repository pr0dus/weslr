# WESLR ARC-AGI2 Final Log Review + Public Dataset Quarantine Check V1

## Metadata

| Field | Value |
|-------|-------|
| Repository | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| Branch | `main` |
| Current HEAD | `8d533d0f1a50a5e0bef06ddd6dadf4391c44dca0` |
| Expected HEAD | `8d533d0f1a50a5e0bef06ddd6dadf4391c44dca0` |
| Preflight match | YES |
| Audit type | Log review + public dataset quarantine check |
| Previous lane | `WESLR_ARC_AGI2_FINAL_DIVERSIFIED_SYNTHETIC_SCORE_REPORT_V1` |

## Part A — Final Log Review

### Log Artifacts

| Artifact | Path | Exists |
|----------|------|--------|
| events.jsonl | `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T202414/events.jsonl` | YES (358,578 bytes) |
| run.log | `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T202414/run.log` | YES (154,124 bytes) |
| summary.json | `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T202414/summary.json` | YES (22,944 bytes) |

### Log Location

Generated logs are outside the WESLR repo at `/data/data/com.termux/files/home/weslr-arc-run-logs/`. They are not committed to git.

### Summary.json Verification

| Field | Report Value | Actual Value | Match |
|-------|-------------|---------------|-------|
| run_id | `arc-synth-20260705T202414` | `arc-synth-20260705T202414` | YES |
| event_count | 936 (report) / 898 (summary) | 898 | Note: report used analyzer count, summary is raw event count |
| dev total_tasks | 105 | 105 | YES |
| dev solved | 84 | 84 | YES |
| dev unsolved | 21 | 21 | YES |
| dev fallback_only | 15 | 15 | YES |
| dev exceptions | 0 | 0 | YES |
| dev malformed | 0 | 0 | YES |
| dev adversarial_pass | 21 | 21 | YES |
| dev adversarial_fail | 0 | 0 | YES |
| dev exact_two_output | PASS | true | YES |
| dev deterministic_replay | PASS | true | YES |
| heldout total_tasks | 159 | 159 | YES |
| heldout solved | 124 | 124 | YES |
| heldout unsolved | 35 | 35 | YES |
| heldout fallback_only | 25 | 25 | YES |
| heldout exceptions | 0 | 0 | YES |
| heldout malformed | 0 | 0 | YES |
| heldout adversarial_pass | 35 | 35 | YES |
| heldout adversarial_fail | 0 | 0 | YES |
| heldout exact_two_output | PASS | true | YES |
| heldout deterministic_replay | PASS | true | YES |
| expected_output_isolation | PASS | true | YES |
| split_disjoint | PASS | true | YES |

### Per-Family Verification (Diversified Families)

| Family | Dev Solved (report) | Dev Solved (actual) | Heldout Solved (report) | Heldout Solved (actual) |
|--------|-------------------|---------------------|------------------------|------------------------|
| `complete_horizontal_symmetry` | 3 | 3 | 3 | 3 |
| `complete_vertical_symmetry` | 3 | 3 | 3 | 3 |
| `extend_line_to_boundary` | 3 | 3 | 3 | 3 |
| `fill_enclosed_hole` | 3 | 3 | 3 | 3 |
| `extract_row_or_column_by_marker` | 3 | 3 | 3 | 3 |
| `copy_object_to_marker` | 3 | 3 | 3 | 3 |
| `remove_distractor_object` | 3 | 3 | 3 | 3 |
| `recolor_by_object_size` | 3 | 3 | 3 | 3 |

### Per-Family Verification (Adversarial Families)

All 7 adversarial families show 0 solved, all tasks in `per_family_failed`:

| Family | Dev Failed | Heldout Failed |
|--------|-----------|----------------|
| `inconsistent_train_examples` | 3 | 5 |
| `ambiguous_multiple_rules` | 3 | 5 |
| `unsupported_primitive_chain` | 3 | 5 |
| `near_match_one_cell` | 3 | 5 |
| `same_palette_wrong_geometry` | 3 | 5 |
| `same_geometry_wrong_recolor` | 3 | 5 |
| `count_tie_ambiguity` | 3 | 5 |

### Metadata Safety Check

Searched events.jsonl for forbidden terms:

| Term | Occurrences | Classification |
|------|-------------|----------------|
| `raw_grid` | 0 | — |
| `raw_grids` | 0 | — |
| `train_grid` | 0 | — |
| `test_grid` | 0 | — |
| `expected_output` | 3 | Harmless audit labels: `expected_output_isolation_check` (event type), `run_summary` (phase), `run_finished` (phase). No actual grid data. |
| `expected_output_grid` | 0 | — |
| `expected_outputs` | 0 | — |
| `solution_grid` | 0 | — |
| `answer_key` | 0 | — |
| `public_solution` | 0 | — |

**Result**: No forbidden metadata leakage. All 3 `expected_output` occurrences are legitimate audit/report labels, not data leakage.

### Integrity Check Summary

| Check | Status |
|-------|--------|
| events.jsonl exists | PASS |
| run.log exists | PASS |
| summary.json exists | PASS |
| Generated logs not committed | PASS |
| Analyzer result clean | PASS |
| Event count matches report | PASS (898 raw, 936 analyzer) |
| Split summaries match report | PASS |
| Final score matches report | PASS (208/264 = 78.8%) |
| Adversarial rejection count matches | PASS (56) |
| No exceptions | PASS (0) |
| No malformed outputs | PASS (0) |
| Exact-two-output | PASS |
| Deterministic replay | PASS |
| Expected-output isolation | PASS |
| Leakage audit | PASS |
| Unsafe metadata count | 0 |
| expected_output leakage | 0 |
| raw_grid leakage | 0 |

## Part B — Public Dataset Quarantine Check

### Public Dataset Location

| Field | Value |
|-------|-------|
| Path | `/data/data/com.termux/files/home/arc-agi2-public-source/arc-prize-2026-arc-agi-2.zip` |
| File size | 498,708 bytes |
| SHA256 | `d00746ef4e06a515ad53bde4dff276dc8ef5a26829a0ebeafc8cf8ba6371abaa` |
| Expected SHA256 | `d00746ef4e06a515ad53bde4dff276dc8ef5a26829a0ebeafc8cf8ba6371abaa` |
| SHA256 match | YES |
| Outside WESLR repo | YES |
| Untracked by git | YES (outside repo) |

### Quarantine Status

| Check | Status |
|-------|--------|
| Public dataset outside repo | YES |
| Public dataset untracked by git | YES |
| Public-source artifacts inside repo | NO (only metadata/config/docs about public ARC, no actual task data) |
| Recent synthetic lanes touched public-source paths | NO |
| Generated logs mention public ARC paths | NO |
| Public dataset read in this audit | NO (only SHA256 and file size checked) |
| Public task contents read | NO |
| Public scoring occurred | NO |
| Kaggle submission occurred | NO |

## Part C — Git Cleanliness

| Check | Status |
|-------|--------|
| Current HEAD | `8d533d0f1a50a5e0bef06ddd6dadf4391c44dca0` |
| Dirty tracked files | 0 (clean) |
| Untracked files | `docs/WESLR_ARC_AGI2_TASK_FEATURE_SIGNATURE_EXTRACTOR_V1.md` (unrelated, pre-existing) |
| `git diff --check` | PASS (clean) |
| Release gate | PASS |
| Release check | PASS |
| Health check (source-repo) | PASS (6/6 mandatory) |
| Generated logs committed | NO |
| Public dataset inside repo | NO |
| Public dataset read in this audit | NO |
| Public scoring occurred | NO |
| Kaggle submission occurred | NO |

## Readiness Verdict

```
final_log_review_public_dataset_quarantine_check_v1_passed
```

**Reasoning:**
- Final logs validate cleanly against the score report
- All integrity checks pass (exact-two-output, deterministic replay, expected-output isolation, leakage audit)
- Generated logs are outside git
- Public dataset remains outside the repo with matching SHA256
- No public ARC task contents were read
- No public scoring occurred
- No Kaggle submission occurred
- All validation checks pass
