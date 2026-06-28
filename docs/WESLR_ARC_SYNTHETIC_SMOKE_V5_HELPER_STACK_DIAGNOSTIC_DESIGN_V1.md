# WESLR ARC SYNTHETIC SMOKE V5 HELPER STACK DIAGNOSTIC DESIGN V1

## 1. Executive verdict
`arc_synthetic_smoke_v5_helper_stack_diagnostic_design_ready`

## 2. V5 Purpose

Measure whether the completed helper stack improves WESLR's handling of the V4 failure frontier:

- rival grammar ambiguity
- beautiful wrong rules
- composed transforms
- negative evidence absence
- helper traps
- object-role correspondence failures
- invariant/symmetry ambiguity
- MDL simplicity without deservedness
- promotion-gate safety

## 3. Task Suite

8 groups × 6 tasks = 48 total tasks

| Group | Purpose | Tasks |
|-------|---------|-------|
| v4_rival_grammar_replay_6 | Replay V4 rival grammar failures | 6 |
| v4_beautiful_wrong_rule_replay_6 | Replay V4 beautiful wrong rule failures | 6 |
| v4_composed_transform_replay_6 | Replay V4 composed transform failures | 6 |
| v4_negative_evidence_replay_6 | Replay V4 negative evidence failures | 6 |
| v4_helper_trap_replay_6 | Replay V4 helper trap failures | 6 |
| object_graph_correspondence_6 | Test object-role mapping ambiguity | 6 |
| invariant_symmetry_ambiguity_6 | Test invariant/symmetry ambiguity | 6 |
| mdl_simplicity_trap_6 | Test MDL simplicity without deservedness | 6 |

## 4. Comparison Logic

### Baseline vs Helper-Stack Comparison

For each task, record:
- **baseline solver status**: What the frozen solver produces without helper input
- **helper-stack diagnostic status**: What the helper stack reports as diagnostic
- **final ledger status**: Whether ledger grants deservedness
- **comparison outcome**:
  - Did helper stack improve the result?
  - Did helper stack block an undeserved answer?
  - Did helper stack produce only safe failure?
  - Did any helper improperly raise confidence?

### Metrics Categories

#### Task-Level Metrics
- `attempted_tasks`: Number of tasks attempted
- `task_exact_count`: Exact matches
- `task_exact_rate`: Exact rate
- `task_partial_count`: Partial matches
- `task_unsupported_count`: Unsupported but correct
- `task_failed_count`: Failures
- `safe_failure_count`: Safe failures
- `overconfident_wrong_count`: Wrong and confident
- `deserved_answer_count`: Answers that earned ledger deservedness
- `undeserved_answer_blocked_count`: Blocked by helper stack

#### Helper-Stack Usage Metrics
- `constraint_helper_used_count`: Helper 3 invoked
- `divergence_helper_used_count`: Helper 4 invoked
- `invariant_symmetry_helper_used_count`: Helper 5 invoked
- `mdl_helper_used_count`: Helper 6 invoked
- `object_graph_helper_used_count`: Helper 8 invoked
- `retry_loop_used_count`: Helper 2 invoked
- `relation_first_helper_used_count`: Helper 1 invoked
- `promotion_gate_used_count`: Helper 7 invoked

#### Frontier Metrics
- `rival_grammar_resolved_count`: Train evidence resolved rival grammar
- `rival_grammar_preserved_count`: Multiple grammars preserved
- `beautiful_wrong_rule_blocked_count`: Helper blocked elegant wrong rule
- `helper_trap_blocked_count`: Helper blocked trap
- `object_mapping_ambiguity_detected_count`: Helper detected ambiguous mapping
- `invariant_ambiguity_detected_count`: Helper detected ambiguous invariant
- `mdl_simpler_but_not_forced_count`: Simpler grammar not forced by train
- `safe_failure_recommended_count`: Safe failure recommended

## 5. V5 Interpretation Guidelines

### Good Outcomes (Discipline)
- Overconfident wrong remains 0 or decreases
- Helper traps are blocked
- Beautiful wrong rules are blocked
- Ambiguity produces safe failure
- Object correspondence ambiguity is detected
- MDL simplicity does not create deservedness
- Rival grammars preserved unless train evidence resolves them
- Safe failure discipline maintained or improved

### Bad Outcomes (Guessing or Laundering)
- Exact rate improves by guessing
- Helper output becomes final evidence
- Safe failure is weakened
- Overconfident wrong increases
- Object match or symmetry creates deservedness
- MDL compression crowns a winner
- Promotion gate auto-promotes anything

## 6. Hard Boundaries

- **Local only**: No external data sources
- **Diagnostic only**: Helpers do not generate final answers
- **No runtime wiring**: Helpers remain unwired from live solver
- **No public claims**: No ARC/Kaggle/leaderboard claims
- **No evidence laundering**: Helper outputs cannot become train evidence
- **Safe failure preserved**: Cannot weaken safe-failure discipline
- **Ledger preserved**: Final answer authority remains with ledger

## 7. Design Summary

| Property | Value |
|----------|-------|
| Task groups | 8 |
| Task count | 48 |
| Baseline comparison | Yes |
| Helper-stack diagnostic | Yes |
| Task metrics | 10 |
| Helper usage metrics | 8 |
| Frontier metrics | 8 |
| Safety interpretation | Yes |
| Failure interpretation | Yes |

## 8. Next Steps

If validation passes:
- Commit the design locally
- Proceed to `IMPLEMENT_ARC_SYNTHETIC_SMOKE_V5_HELPER_STACK_DIAGNOSTIC_V1`

---

V5 task groups defined: yes (8 groups)
V5 task count: 48 (8×6)
Baseline vs helper-stack comparison defined: yes
Metrics defined: yes (10 task + 8 usage + 8 frontier = 26 metrics)
Ledger/deservedness model defined: yes
Safety interpretation defined: yes
Runtime wiring avoided: yes
Public ARC claims avoided: yes
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_synthetic_smoke_v5_helper_stack_diagnostic_design_ready