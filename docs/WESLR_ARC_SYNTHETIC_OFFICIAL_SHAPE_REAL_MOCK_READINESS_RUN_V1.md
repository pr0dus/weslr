# WESLR ARC Synthetic Official-Shape Real Mock Readiness Run V1

- Repository: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `4e37fed3e6b55b558fdaf3af067a910378d0ac63`
- End HEAD: `346b31ab78428a5f39046fb15ec5d13bcc590116`
- Mock scope: synthetic ARC-style held-out tasks, offline exact-match scoring, exactly-two-output ARC-AGI-2-style packets, solver-visible/train-only path, scorer-only hidden references
- Synthetic-only statement: yes; no official/public ARC data was touched
- Official percentage: none/0
- Official/public data touched: no

## Seeds and batch manifest
- Seed list: `[101, 202, 303]`
- Batch 0 seed `101`: tasks=8, families=['border_frame', 'extract_largest_object', 'copy_grid', 'complete_symmetry'], score=8, solver=8, baseline=2, exact-two=True
- Batch 1 seed `202`: tasks=8, families=['line_completion', 'move_single_object', 'fill_region', 'object_count_to_pattern'], score=8, solver=8, baseline=0, exact-two=True
- Batch 2 seed `303`: tasks=8, families=['reflect_object_horizontal_or_vertical', 'remove_background_noise', 'rotate_object_90', 'recolor_symbol'], score=4, solver=4, baseline=0, exact-two=True

## Aggregate results
- Tasks: 24
- Batch count: 3
- Task score (top-2 exact-match): 20/24
- Solver exact: 20/24
- Trivial baseline exact: 2/24
- Malformed: 0, timeout: 0, error: 0
- Batch score variance: 1.885618
- Exact-two-output compliance: [True, True, True]

## Family manifest / per-family score
- border_frame: count=2, solver_exact=2, baseline_exact=0, task_score=2
- complete_symmetry: count=2, solver_exact=2, baseline_exact=0, task_score=2
- copy_grid: count=2, solver_exact=2, baseline_exact=2, task_score=2
- extract_largest_object: count=2, solver_exact=2, baseline_exact=0, task_score=2
- fill_region: count=2, solver_exact=2, baseline_exact=0, task_score=2
- line_completion: count=2, solver_exact=2, baseline_exact=0, task_score=2
- move_single_object: count=2, solver_exact=2, baseline_exact=0, task_score=2
- object_count_to_pattern: count=2, solver_exact=2, baseline_exact=0, task_score=2
- recolor_symbol: count=2, solver_exact=2, baseline_exact=0, task_score=2
- reflect_object_horizontal_or_vertical: count=2, solver_exact=0, baseline_exact=0, task_score=0
- remove_background_noise: count=2, solver_exact=2, baseline_exact=0, task_score=2
- rotate_object_90: count=2, solver_exact=0, baseline_exact=0, task_score=0

## Audit
- Leakage audit: {'expected_output_leakage': False, 'synthetic_official_mixing': False, 'official_data_touched': False, 'public_data_touched': False, 'internet_used': False, 'provider_used': False, 'retrieval_used': False, 'tool_calls_used': False, 'protected_runtime_chat_ui_changed': False}
- Bundle validation: {'valid': True, 'blocked_reason_labels': []}
- No internet/provider/retrieval/tool calls in the mock run: yes
- Protected runtime/chat/UI files changed: no

## Verdict
- Readiness verdict: `mock_ready_for_public_parse_scorer_design`
- Recommended next lane: design the exact public-parse scorer surface on top of the synthetic official-shape packet contract, without touching official ARC data
