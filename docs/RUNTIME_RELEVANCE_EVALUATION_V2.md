# RUNTIME_RELEVANCE_EVALUATION_V2.md
# Artifact-Lifecycle-Based Validation (SatUi-Compatible)

**Status:** DESIGN DRAFT — canonical evaluation workflow
**Date:** 2026-04-21
**Authoritative for:** Runtime relevance evaluation, evaluation artifact generation, and SatUi feedback loop

---

## SECTION 1 — FILES CHANGED

| File | Change |
|------|--------|
| `docs/RUNTIME_RELEVANCE_EVALUATION_V2.md` | **Created** — this document |

No production code files modified. No schema changes. No behavior changes.

---

## SECTION 2 — COMMANDS RUN

None. This pass is documentation-only.

---

## SECTION 3 — PURPOSE

### Why Relevance Must Be Tested Inside Artifact Lifecycle

Single-turn relevance evaluation tests whether `_relevant_interests` is correct for one message in isolation. This is insufficient because:

1. **Relevance is path-dependent.** The same interest keyword in "improve this" and "improve that" may resolve to different artifacts with different relevance implications. A single-turn test cannot capture this.

2. **Artifact context changes relevance over time.** When a user says "improve this" twice, the second occurrence should resolve to a different artifact than the first. Evaluating both in isolation misses whether the system correctly tracks which artifact is active.

3. **Reference resolution affects interest detection.** When "improve this" resolves to a stored artifact, the interest snapshot should reflect the artifact's topic, not just the message's tokens. Testing only the message string ("improve this") misses whether the resolution enriched the interest context correctly.

4. **Ranking stability matters across turns.** A strong interest detected in turn 1 should remain ranked consistently or deliberately change — not silently reset. Multi-turn artifact flows expose whether ranking resets inappropriately.

5. **Noise accumulation surfaces in context.** Repeated "improve this" calls against the same artifact should not accumulate false-positive interests. Evaluating isolated turns cannot detect this accumulation pattern.

### Why Artifact-Shaped Evaluations Are Superior to Pass/Fail Tests

Pass/fail tests are binary: the test passes or the test fails. They are insufficient for relevance evaluation because:

- **Relevance is dimensional.** "The correct interest was ranked #3 instead of #1" is not a pass/fail — it is a ranking quality issue that pass/fail cannot capture.
- **Scoring reveals magnitude.** A score of 2 vs. 1 in restraint indicates different noise levels. Pass/fail collapses both to fail.
- **Diagnostic flags enable root-cause analysis.** A pass/fail test that fails tells you nothing about whether the failure was due to noise (false positive), miss (false negative), drift, or context break. Artifact-shaped evaluations carry diagnostic fields that identify the failure mode.
- **Evaluation artifacts are inspectable in SatUi.** Pass/fail test results are ephemeral. Evaluation artifacts are persisted, labeled, and surfaceable in the satellite UI for operator review and pattern analysis.
- **Evaluation artifacts can be compared over time.** Pass/fail test suites produce isolated snapshots. Evaluation artifacts with timestamps and scenario IDs can be queried to track scoring trends across WESLR versions.

### What This Reveals

| Problem | How It's Revealed |
|---------|-------------------|
| **Drift** | Same scenario scored differently at T1 vs T2 — `drift_flag = True` |
| **Noise** | High `noise_score` — false-positive interests in `_relevant_interests` |
| **Ranking issues** | Strongest interest not ranked first — `ranking_quality < 3` |
| **Context break** | Interest snapshot does not reflect active artifact — `context_break_flag = True` |
| **Miss** | Expected interest absent from snapshot — `miss_score > 0` |
| **Satellite unreadability** | Operator cannot understand why match was made — `explainability < 3` |
| **No active artifact** | Safe message returned — evaluated as edge case (14) |
| **Governance pollution** | Governance keywords trigger false interest matches — `noise_score` elevated |

---

## SECTION 4 — EVALUATION ARTIFACT SHAPE (ENHANCED)

Each evaluation produces a structured artifact stored in `continuity/artifacts/eval/`.

### Full Schema

```json
{
  "evaluation_id": "eval-<timestamp>-<seq>",
  "created_at": "<ISO timestamp>",
  "scenario_id": "sat-001",
  "scenario_title": "Artifact Generation → Relevance Snapshot",
  "session_id": "default",
  "artifact_id": null,

  "resolved_reference_phrase": null,

  "input_message": "improve the hypothesis",

  "prior_context": {
    "turn_index": 2,
    "topic_summary": "Governance quality analysis",
    "active_artifact_id": "art-123456-1",
    "prior_interests": ["governance", "quality"]
  },

  "resolved_artifact_content": null,

  "relevant_interests_snapshot": {
    "interests": [
      {"interest": "governance", "score": 0.82, "source": "keyword", "trigger": "governance"},
      {"interest": "quality", "score": 0.71, "source": "keyword", "trigger": "quality"},
      {"interest": "causality", "score": 0.41, "source": "context", "trigger": "hypothesis"}
    ],
    "top_interest": "governance",
    "interest_count": 3,
    "primary_confidence": 0.82
  },

  "response_source": "artifact_proposal",

  "artifact_lifecycle_stage": "generation",

  "evaluation": {
    "expected_interest_behavior": "governance and quality should appear as top interests; ranking should reflect governance > quality",
    "actual_behavior_summary": "governance ranked first (0.82), quality second (0.71). Hypothesis-derived interest 'causality' also present. Ranking matches expectation."
  },

  "scores": {
    "accuracy": 5,
    "restraint": 4,
    "ranking_quality": 4,
    "explainability": 4,
    "runtime_usefulness": 4,
    "satellite_readability": 5
  },

  "diagnostics": {
    "noise_score": 0.15,
    "miss_score": 0.0,
    "drift_flag": false,
    "context_break_flag": false,
    "false_positive_interests": [],
    "missed_interests": []
  },

  "notes": "Strong match. Hypothesis-derived interest (causality) is a valid context injection, not noise.",

  "recommended_followup": null,

  "eval_meta": {
    "evaluated_by": "runtime_eval_runner",
    "eval_version": "v2",
    "source_module": "relevance_surface.py",
    "weslr_version": "<current git hash or version>"
  }
}
```

### Field Semantics

#### Identity Fields

| Field | Type | Purpose |
|-------|------|---------|
| `evaluation_id` | `str` | Unique ID, format `eval-<ts>-<seq>` |
| `created_at` | `str` | ISO timestamp |
| `scenario_id` | `str` | Scenario identifier from scenario catalog |
| `scenario_title` | `str` | Human-readable scenario name |
| `session_id` | `str` | Session used for evaluation |
| `artifact_id` | `str \| null` | Active artifact at evaluation time |

#### Input Context

| Field | Type | Purpose |
|-------|------|---------|
| `resolved_reference_phrase` | `str \| null` | Which reference phrase was matched (e.g., `"improve this"`) |
| `input_message` | `str` | The user's raw message |
| `prior_context` | `dict` | Turn index, topic summary, active artifact ID, prior interests |
| `resolved_artifact_content` | `str \| null` | Content of resolved artifact (if reference resolution was involved) |

#### Interest Snapshot

| Field | Type | Purpose |
|-------|------|---------|
| `relevant_interests_snapshot` | `dict` | Exact snapshot of `_relevant_interests` at evaluation time |
| `response_source` | `str` | Routing label (e.g., `"artifact_proposal"`, `"direct_answer"`) |
| `artifact_lifecycle_stage` | `str` | One of: `generation`, `reference`, `revision`, `explanation`, `baseline` |

#### Evaluation

| Field | Type | Purpose |
|-------|------|---------|
| `evaluation.expected_interest_behavior` | `str` | What the evaluator expected the interest system to do |
| `evaluation.actual_behavior_summary` | `str` | What actually happened — concrete, not generic |

#### Scores (1–5)

| Score | 5 (Excellent) | 3 (Acceptable) | 1 (Broken) |
|-------|-------------|----------------|-----------|
| `accuracy` | Correct interests detected, none missing | Minor miss or false positive | Wrong interests or missing critical ones |
| `restraint` | No false positives at all | Few false positives | Significant noise from unrelated tokens |
| `ranking_quality` | Strongest interest clearly ranked first | Top interest correct but close rankings | Wrong interest ranked first |
| `explainability` | Operator immediately understands every match | Some matches require tracing | Cannot understand why interest was matched |
| `runtime_usefulness` | Interests would directly help a decision | Interests partially useful | Interests would mislead decisions |
| `satellite_readability` | Card in SatUi immediately readable | Usable with minor effort | Confusing or requires digging |

#### Diagnostics

| Field | Semantics |
|-------|----------|
| `noise_score` | Fraction of interests that are false positives (0.0–1.0) |
| `miss_score` | Fraction of expected interests that were missed (0.0–1.0) |
| `drift_flag` | `true` if same scenario scored ≥1 point differently vs. prior run |
| `context_break_flag` | `true` if interests do not reflect resolved artifact context |
| `false_positive_interests` | List of interest names that are noise |
| `missed_interests` | List of expected interest names that were absent |

---

## SECTION 5 — SCENARIO CATALOG (UPGRADED)

15 scenarios across 4 classes.

### A. Single-Turn Baseline (5 scenarios)

| ID | Title | Input | Expected Behavior | Lifecycle Stage |
|----|-------|-------|-------------------|-----------------|
| **sat-001** | Direct single-interest match | "What is the governance quality?" | `governance` in top interests | `baseline` |
| **sat-002** | No-interest normal conversation | "What time is it in Berlin?" | No strong interest match; low noise | `baseline` |
| **sat-003** | False-positive trap | "I want to improve the governance and quality of my essay" | Only actual interest `governance` should be matched; `essay` and `improve` should NOT become interests | `baseline` |
| **sat-004** | High-specificity domain input | "Explain the drift detection threshold calibration for cognitive adequacy" | `cognitive_adequacy` and `drift` detected as top interests | `baseline` |
| **sat-005** | Vague input | "Tell me about something interesting" | No strong false positives; restraint score ≥ 3 | `baseline` |

### B. Multi-Turn Context (4 scenarios)

| ID | Title | Input | Prior Context | Expected Behavior | Lifecycle Stage |
|----|-------|-------|---------------|-------------------|-----------------|
| **sat-006** | Repeated-topic continuity | "improve this" | Turn 1 same message resolved to `art-A`; Turn 2 in same session | Same artifact resolved; same top interests; stability maintained | `reference` |
| **sat-007** | Topic shift detection | "What is the weather in Munich?" | Prior turns about governance quality | Interests should shift to `weather`/`munich`; prior `governance` interest should not persist | `baseline` (shift) |
| **sat-008** | Competing strong interests ranking stress | "Improve governance quality and cognitive adequacy" | All three interests are valid keywords | Ranking should reflect which is strongest; governance and quality likely tied; cognitive_adequacy below | `baseline` |
| **sat-009** | Context carryover failure case | "And what about the next experiment?" | Prior context has no artifact, prior message about hypothesis | Should not inherit unrelated prior interests; restraint maintained | `baseline` |

### C. Artifact Lifecycle (4 scenarios) — *Critical*

| ID | Title | Input | Prior Context | Expected Behavior | Lifecycle Stage |
|----|-------|-------|---------------|-------------------|-----------------|
| **sat-010** | Artifact generation → relevance snapshot | "improve the hypothesis" (no prior artifact) | None | Artifact generated and saved; `_relevant_interests` reflects hypothesis topic | `generation` |
| **sat-011** | "improve this" → reference resolution → relevance stability | "improve this" | Active artifact from sat-010 present | Resolves to sat-010 artifact; interests should reflect artifact content, not original message tokens | `reference` |
| **sat-012** | "explain this" → relevance persistence across explanation | "explain this" | Active artifact from sat-010 present | Resolves to same artifact; explanation should use artifact content; interests should remain consistent | `explanation` |
| **sat-013** | "give me another version" → relevance drift check | "give me another version" | Active artifact from sat-010 present | New artifact generated (version 2); interests should be same or reflect request for alternative; `drift_flag` checked against sat-010 | `revision` |

### D. Edge / Failure Cases (2 scenarios)

| ID | Title | Input | Expected Behavior | Lifecycle Stage |
|----|-------|-------|-------------------|-----------------|
| **sat-014** | Reference phrase with NO active artifact | "improve this" | No active artifact in session; safe message returned; evaluation recorded as edge case with `context_break_flag = True` | `reference` (edge) |
| **sat-015** | Governance-heavy message | "I approve the governance proposal and request execution via the governed execution gate" | Governance keywords should NOT produce interest matches; restraint score must be 5; `noise_score = 0.0` | `baseline` (edge) |

---

## SECTION 6 — SCORING / JUDGMENT RUBRIC

### Per-Score Definitions

#### Accuracy (Correct Interest Detection)

| Score | Meaning |
|-------|---------|
| **5** | All expected interests present; no unexpected interests |
| **4** | All expected interests present; 1 unexpected interest (minor noise) |
| **3** | Most expected interests present (≥70%); some noise or miss |
| **2** | Some expected interests present (≥40%); significant noise or miss |
| **1** | Wrong interests detected or critical expected interest missing |

#### Restraint (No False Positives)

| Score | Meaning |
|-------|---------|
| **5** | Zero false-positive interests |
| **4** | 1 false-positive interest |
| **3** | 2 false-positive interests |
| **2** | 3 false-positive interests |
| **1** | ≥4 false-positive interests or governance keywords triggering matches |

#### Ranking Quality

| Score | Meaning |
|-------|---------|
| **5** | Strongest interest clearly ranked #1 with large margin |
| **4** | Strongest interest ranked #1 but margin is small |
| **3** | Top interest correct but ranking order has minor issues |
| **2** | Wrong interest ranked #1; correct one is #2–#3 |
| **1** | Correct interest ranked #4 or lower |

#### Explainability

| Score | Meaning |
|-------|---------|
| **5** | Every interest match has a clear, traceable trigger |
| **4** | Most matches traceable; 1–2 require tracing |
| **3** | Some matches obvious; others need effort to understand |
| **2** | Several matches cannot be explained without source code |
| **1** | Cannot understand why any interest was matched |

#### Runtime Usefulness

| Score | Meaning |
|-------|---------|
| **5** | Interests would directly and correctly inform a decision |
| **4** | Interests mostly useful; 1–2 would not help |
| **3** | Mixed: some interests useful, others irrelevant or misleading |
| **2** | Most interests would not help the actual decision |
| **1** | Interests would actively mislead decisions |

#### Satellite Readability

| Score | Meaning |
|-------|---------|
| **5** | Card immediately clear: scores visible, flags obvious, notes readable |
| **4** | Card readable with minor scrolling |
| **3** | Card requires expanding to see full evaluation |
| **2** | Card confusing; requires operator effort to interpret |
| **1** | Card cannot be parsed without reading raw JSON |

### Score Band Summary

| Band | Label | Action |
|------|-------|--------|
| 5 | Excellent | No action needed |
| 4 | Good | Accept, monitor |
| 3 | Acceptable | Note for next review cycle |
| 2 | Concerning | Investigate within current sprint |
| 1 | Broken | Priority fix in current sprint |

### Composite Score

A composite `overall_score` is the **unweighted mean** of the 6 dimension scores, rounded to 1 decimal. This is for display only — it does not drive routing or decisions.

---

## SECTION 7 — SATELLITE UI FEEDBACK MODEL

### Evaluation Card (Primary View)

Each evaluation artifact is surfaced as a card in SatUi:

```
┌─────────────────────────────────────────────────────┐
│ [sat-011] "improve this" — Reference Resolution     │
│ Artifact: art-1776800100-1 │ Session: default        │
│ Stage: reference    │ Overall: 4.2 / 5              │
├─────────────────────────────────────────────────────┤
│ Relevant Interests (snapshot):                      │
│   1. governance      0.82  [keyword: governance]      │
│   2. quality        0.71  [keyword: quality]         │
│   3. causality      0.41  [context: hypothesis]      │
├─────────────────────────────────────────────────────┤
│ Scores:                                              │
│   accuracy ██████ 5  restraint █████ 4               │
│   ranking  █████ 4  explainability ████ 4           │
│   runtime  █████ 4  satellite ██████ 5                │
├─────────────────────────────────────────────────────┤
│ ⚠️ drift_flag: false    ⚠️ noise_score: 0.15         │
│ Notes: Strong match. Causality is valid context.     │
└─────────────────────────────────────────────────────┘
```

### Batch Comparison View

Operators can view all evaluations for a scenario ID across sessions:

```
Scenario [sat-011] — "improve this" Reference Resolution
Session        │ Artifact        │ Overall │ Drift │ Noise
───────────────┼─────────────────┼─────────┼───────┼──────
default        │ art-1776800100-1│  4.2    │  —    │ 0.15
session-002    │ art-1776800200-1│  4.0    │  ✓    │ 0.20
session-003    │ art-1776800300-1│  3.8    │  ✓    │ 0.25
▲ Drift detected: scores declining across sessions
```

When `drift_flag = True` across sessions, the batch view surfaces the trend.

### Collapsed Summary Row

```
[  ] [sat-011] "improve this"  │ ref=art-1  │ ⬛⬛⬛⬜⬜ 3.8  ⚠️ drift  ⚠️ noise
```

Collapsed by default. Click to expand full card.

### Operator Annotation

Each card supports an annotation field:

```json
{
  "operator_annotation": "Drift confirmed on session-002. Investigation scheduled for next sprint.",
  "annotated_by": "operator",
  "annotated_at": "<ISO timestamp>"
}
```

Annotations are stored in the evaluation artifact and surfaced in batch view.

### Filter Controls

| Filter | Options |
|--------|---------|
| Stage | All / generation / reference / revision / explanation / baseline / edge |
| Score band | All / 5 / 4 / 3 / 2 / 1 |
| Flags | All / Drift / Noise / Context Break / None |
| Scenario ID | All / sat-001 … sat-015 |

---

## SECTION 8 — HOW RESULTS FEED BACK TO WESLR

### Read-Only Loop (WESLR Can Inspect)

WESLR may read evaluation artifacts to build self-understanding:

```
WESLR self-inspection path:
  evaluate_runtime_relevance()   → reads from continuity/artifacts/eval/
    → pattern_analysis()        → identifies noise, drift, ranking patterns
    → get_self_summary()        → includes evaluation pattern summary
    → propose_if_needed()       → generates ChangeProposal only (NOT auto-applied)
```

### What WESLR Can Observe

- Aggregate noise patterns: which interests are frequently false positives
- Drift patterns: which scenarios are scoring inconsistently across sessions
- Ranking issues: which interests are frequently mis-ranked
- Satellite unreadability scores: which evaluation cards are confusing
- Scenario scores: which scenario classes are weakest

### What WESLR Cannot Do

| Forbidden | Reason |
|-----------|--------|
| Auto-modify `_relevant_interests` scoring weights | Would bypass governance; changes behavior without operator review |
| Auto-change routing based on eval results | Would create hidden decision engine |
| Write directly to interest data | Interest data is derived state, not writable by WESLR |
| Suppress or hide poor evaluations | Evaluation artifacts are immutable once written |
| Bypass the ExecutionGate | Any change derived from eval patterns must go through proposal → approve → execute |

### Future Allowed Path (Operator-Gated)

```
1. WESLR detects persistent noise pattern in evaluation artifacts
2. WESLR generates a ChangeProposal:
   - title: "Reduce false positive interest: causality in artifact contexts"
   - rationale: "Evaluation artifacts sat-010 through sat-013 show causality
                 appearing as false positive 40% of the time in artifact lifecycle stages"
   - affected_subsystem: "relevance_surface.py"
   - test_prompts: ["..."]
3. Operator reviews via existing self_improvement_proposal flow
4. If approved: ExecutionGate.execute_proposal_if_approved()
5. New evaluation artifacts confirm improvement
```

**This path requires operator approval at every step. WESLR proposes; the operator decides.**

---

## SECTION 9 — FORBIDDEN DRIFT

The following are explicitly forbidden in any implementation or use of this evaluation system:

1. **No auto-tuning of relevance scoring.** Evaluation results may not be used to automatically adjust `_relevant_interests` weights, keyword lists, or scoring parameters.

2. **No routing changes based on eval results.** Evaluation artifacts do not feed back into routing logic. A poor `ranking_quality` score does not change which routing branch is taken.

3. **No hidden writes to interest data.** Evaluation artifacts are immutable append-only records. They may not be used to overwrite, delete, or suppress interest data.

4. **No second decision engine.** The evaluation system is a read-only diagnostic surface. It may not develop its own recommendation engine, score predictor, or routing modifier.

5. **No bypassing governance.** Any behavior change derived from evaluation patterns must go through the full proposal → approval → execution path. Evaluations do not grant bypass authority.

6. **No silent behavior changes.** If an evaluation reveals a scoring regression (drift_flag = True), the regression must be documented in the evaluation artifact's `notes` and surfaced in SatUi. It may not be silently fixed.

7. **No scoring inflation.** Operators may not adjust scores to make poor evaluations look acceptable. Evaluation artifacts are immutable once written.

8. **No cross-session interest data leakage.** Evaluation results from one session may not be used to modify interest data for another session.

---

## SECTION 10 — RECOMMENDED FIRST IMPLEMENTATION

### Minimal Safe Implementation

**Phase 1: Evaluation Artifact Generator + Read-Only Storage**

1. Create `weslr/relevance_eval_runner.py`
   - Function `run_evaluation_scenario(scenario_id: str, session_id: str) -> dict`
   - Function `run_all_scenarios() -> list[dict]`
   - Each function produces a full evaluation artifact (Section 4 schema)
   - Stores to `continuity/artifacts/eval/<evaluation_id>.json`
   - Index: `continuity/artifacts/eval/index.json`

2. Create `continuity/artifacts/eval/` directory

3. Implement scenario runner for **scenarios sat-001 through sat-005** (Single-Turn Baseline) first
   - These are the simplest to implement and validate
   - They establish the baseline scoring reference

4. Implement SatUi surface for **evaluation cards** (read-only)
   - Cards displayed in SatUi operator panel
   - No write-back from UI to evaluation artifacts

5. Add `scenario_id` and `artifact_lifecycle_stage` to `handle_direct_message()` context

**What NOT to implement in Phase 1:**

- Multi-turn scenarios (sat-006–sat-009) — require session continuity scaffolding
- Artifact lifecycle scenarios (sat-010–sat-013) — require reference resolution + artifact store integration
- Edge scenarios (sat-014, sat-015) — require explicit safe-failure paths
- Scoring changes to `_relevant_interests` or routing
- Automated proposal generation from eval results
- Operator annotation write-back

### Implementation Sequence

```
Phase 1A: Basic eval runner + single-turn scenarios (sat-001–sat-005)
  → Validates artifact shape + storage + scoring interpretation

Phase 1B: Artifact lifecycle scenarios (sat-010–sat-013)
  → Connects to existing artifact_store + reference resolution
  → Validates lifecycle stage tagging

Phase 1C: Multi-turn scenarios (sat-006–sat-009)
  → Tests context carryover and ranking stability

Phase 1D: Edge scenarios (sat-014, sat-015)
  → Validates safe failure modes

Phase 2:  SatUi card surface (read-only)

Phase 3:  Batch comparison view + drift detection

Phase 4:  WESLR inspection path (read-only self-understanding)

Phase 5:  Operator-gated proposal generation from eval patterns
```

---

## SECTION 11 — STOP LINE

**Confirmed:**
- Documentation only ✅
- No production code changes ✅
- No schema changes (design phase) ✅
- No behavior changes ✅
- No routing changes ✅
- No scoring changes ✅
- No governance changes ✅
- New document created: `docs/RUNTIME_RELEVANCE_EVALUATION_V2.md` ✅

**Stop after this pass. No code changes. No behavior changes.**

---

*This document defines the canonical runtime relevance evaluation system. All implementation work must reference this document. The recommended first implementation sequence should be followed in order — Phase 1A before Phase 1B, etc.*
