# RUNTIME_RELEVANCE_EVAL_ARTIFACTS_V1.md

**Version:** 1.0
**Date:** 2026-04-21
**Status:** DESIGN — do not implement without operator review
**Scope:** Runtime relevance evaluation as inspectable artifact-shaped records

---

## SECTION 1 — PURPOSE

### Why runtime relevance should be evaluated as artifacts

`relevance_surface` was activated as advisory metadata — `_relevant_interests` is attached to every response payload. This is the first integration of a dormant compression node into the execution path. The question now is not whether it works in isolation (unit tests cover that), but whether it produces **genuinely useful signals** in real runtime conditions.

Plain pass/fail tests answer "does it return the right data shape?" They cannot answer:
- Is the scoring accurate for ambiguous real inputs?
- Does restraint work correctly on normal conversation?
- Are top-ranked interests actually what an operator would expect?
- Is the relevance metadata noisy or helpful?
- Does it make sense to surface this to the satellite UI?

Evaluation artifacts answer these questions by making each case **inspectable, annotatable, and comparable over time**. An artifact captures:
- the exact input that triggered relevance scoring
- the actual `_relevant_interests` produced
- a structured judgment of whether that output was useful
- the operator's or system's reasoning about quality

### Why this is better than plain pass/fail tests

Pass/fail tests assert correctness against known expectations. Runtime relevance against real operator messages has no fixed correct answer — it is inherently judgment-based. Artifacts let evaluators:
- Record that an interest was correctly surfaced (or not)
- Flag false positives with a note explaining why
- Capture ambiguity cases that no rule could resolve
- Track patterns over time (e.g., "governance inputs consistently return noise")
- Provide concrete evidence for future scoring refinements without changing scoring logic

---

## SECTION 2 — EVALUATION ARTIFACT SHAPE

```json
{
  "artifact_type": "runtime_relevance_eval",
  "version": "1.0",
  "scenario_id": "rr-YYYY-MM-DD-NNN",
  "timestamp": "ISO8601",
  "generated_by": "manual | satellite_ui | scheduled_cron",
  "locked": false,

  "input": {
    "message": "exact user message text",
    "topics": ["topic1", "topic2"],
    "turn_type": "greeting | question | statement | ...",
    "prior_context": "optional one-line summary of prior turns"
  },

  "prior_interests_snapshot": {
    "count": 3,
    "ids": ["int001", "int002", "int003"]
  },

  "actual": {
    "_relevant_interests": [
      {
        "id": "int001",
        "name": "governance_quality",
        "display_name": "Governance Quality",
        "score": 5,
        "match_reasons": ["matched tag: governance", "query text contains tag: governance"]
      }
    ],
    "count_returned": 1
  },

  "assessment": {
    "accuracy": "correct | partial | incorrect | not_applicable",
    "accuracy_note": "free-text explanation",

    "restraint": "correct_restraint | over_eager | missed",
    "restraint_note": "free-text explanation",

    "ranking_quality": "good | acceptable | poor | not_applicable",
    "ranking_note": "free-text explanation",

    "explainability": "clear | ambiguous | confusing",
    "explainability_note": "free-text explanation",

    "runtime_usefulness": "useful | neutral | noise",
    "runtime_usefulness_note": "free-text explanation",

    "satellite_readability": "clear | requires_context | unclear",
    "satellite_readability_note": "free-text explanation"
  },

  "scores": {
    "usefulness_score": 1-5,
    "noise_score": 1-5,
    "ranking_score": 1-5,
    "explainability_score": 1-5,
    "overall_score": 1-5
  },

  "flags": {
    "false_positive": false,
    "false_negative": false,
    "ranking_error": false,
    "explainability_gap": false,
    "值得关注": false,
    "escalate_to_governance": false
  },

  "recommended_followup": {
    "action": "none | adjust_scoring | add_interest | remove_interest | investigate | escalate",
    "target": "interest_id or null",
    "note": "why this followup is recommended"
  },

  "eval_notes": [
    {
      "by": "operator | weslr | system",
      "text": "free-text note",
      "timestamp": "ISO8601"
    }
  ]
}
```

**Field semantics:**
- `scenario_id`: monotonically increasing, date-stamped. Format `rr-2026-04-21-001`
- `locked`: if `true`, the record must not be modified — marks reviewed/accepted evaluations
- `prior_interests_snapshot`: captures the interests registry state at evaluation time — needed because interests can change between evaluation and review
- `scores`: each 1–5, where 5 is best. `noise_score` is inverted (1 = very noisy, 5 = perfectly restrained)
- `flags`: boolean markers for specific issues. `值得关注` ("worth paying attention to") marks cases needing governance review
- `recommended_followup`: advisory only — no automatic action in v1

---

## SECTION 3 — SCENARIO CATALOG

Each scenario has a `scenario_id`, a description, an example input, expected interest behavior, and what the evaluation tests.

---

**RR-001 — Direct single-interest match**
- **Input:** "I want to discuss governance quality in my project."
- **Topics:** `["governance", "quality"]`
- **Expected:** Governance Quality interest returned with high score; tags match + text match
- **Tests:** scoring accuracy, explainability, ranking quality

---

**RR-002 — No-interest normal conversation**
- **Input:** "thanks" or "okay" or "makes sense"
- **Topics:** `[]`
- **Expected:** Empty `_relevant_interests` — restraint correct, no false positive
- **Tests:** restraint (correct over-eager detection), noise_score

---

**RR-003 — Ambiguous dual-interest case**
- **Input:** "governance and quality are both important for the system"
- **Topics:** `["governance", "quality"]`
- **Expected:** Two interests returned; ranking should reflect which has stronger tag/text match
- **Tests:** ranking quality when two interests are equally plausible

---

**RR-004 — Repeated-topic continuity case**
- **Input:** "let's continue talking about governance quality"
- **Topics:** `["governance"]`
- **Prior:** Same topic was discussed in prior turns
- **Expected:** Governance Quality returned; recency bonus applies; ranking unchanged by recurrence count (which is 0 in v1)
- **Tests:** stability across repeated mentions; that recurrence count does not inflate score in v1

---

**RR-005 — Topic-shift case**
- **Input:** "now let's shift to discussing the tax report structure"
- **Topics:** `["tax", "reporting"]`
- **Prior:** Prior topics were governance-related
- **Expected:** Old interest not returned; new tax-related interest returned if it exists
- **Tests:** relevance_surface does not carry forward stale interests; shift is detected

---

**RR-006 — Artifact-quality discussion case**
- **Input:** "what is the confidence of this artifact"
- **Topics:** `["artifact", "confidence"]`
- **Expected:** If an "artifact quality" or "artifact confidence" interest exists, returned; otherwise empty
- **Tests:** relevance_surface behavior on artifact-reflexive inputs (which are handled by separate artifact routing in dialogue.py)

---

**RR-007 — Governance-related message**
- **Input:** "the governance framework needs review for the next cycle"
- **Topics:** `["governance", "review"]`
- **Expected:** Governance Quality returned; governance-related match reasons present
- **Tests:** governance topic correctly surfaces governance interest; scoring for longer messages

---

**RR-008 — False-positive trap**
- **Input:** "I want to file a complaint about the service"
- **Topics:** `["governance"]`
- **Prior:** Operator has a "governance quality" interest registered
- **Expected:** Empty or low-score — "complaint" does not match governance quality; restraint expected
- **Tests:** false-positive detection; that governance is not triggered by unrelated adjacent topics

---

**RR-009 — High-specificity domain case**
- **Input:** "the tax treatment of the Entfernungspauschale for commuting over 20km needs clarification"
- **Topics:** `["tax", "steuer"]`
- **Expected:** Tax-related interest returned if one exists; match reasons from tag or name match
- **Tests:** high-specificity input handled without noise; tag-based matching works on domain terms

---

**RR-010 — Vague input case**
- **Input:** "something about the thing we were looking at"
- **Topics:** `[]`
- **Expected:** Empty `_relevant_interests` — insufficient signal for any match
- **Tests:** restraint on vague inputs; recency bonus does not create false relevance

---

**RR-011 — Multi-turn contextual case**
- **Input:** "yes, that second one" (referring to a prior response)
- **Topics:** `[]`
- **Prior:** Context established in prior turns about a specific topic
- **Expected:** Either context-resolved interest or empty; anaphora should not inflate scores
- **Tests:** relevance_surface is not confused by deictic references; context is not a scoring signal

---

**RR-012 — Competing strong interests case**
- **Input:** "governance quality and tax reporting are both concerns"
- **Topics:** `["governance", "tax"]`
- **Expected:** Two interests returned; both with high scores; ranking is tie-broken by recency
- **Tests:** multiple strong interests do not cancel each other; ranking is stable

---

**RR-013 — Low confidence artifact case**
- **Input:** "I am not sure about the limitations of this artifact"
- **Topics:** `["artifact", "limitations"]`
- **Expected:** Artifact-related interest returned if present; "limitations" is a known artifact-reflexive token
- **Tests:** artifact quality interest correctly surfaced for self-reflexive artifact inputs

---

**RR-014 — Greeting with no signal**
- **Input:** "hi" or "hello"
- **Topics:** `[]`
- **Expected:** Empty `_relevant_interests`; greeting routing fires in dialogue.py; relevance has no opinion
- **Tests:** no interference between greeting routing and relevance computation

---

**RR-015 — Exact interest name match in message**
- **Input:** "let's look at the tax_reporting interest"
- **Topics:** `[]`
- **Expected:** Tax Reporting interest returned because "tax_reporting" (normalized name) appears in message text
- **Tests:** name-in-text matching works for exact interest name; normalized form matching

---

## SECTION 4 — SCORING / JUDGMENT RUBRIC

Each evaluation artifact is judged across 6 dimensions. Each dimension is scored 1–5.

### Accuracy (correctness of returned interests)
- 5: Exact expected interest(s) returned, no extras
- 4: Expected interest(s) returned, minor extra with low score
- 3: Expected interest(s) returned, but with noise extras
- 2: Wrong interest returned, expected not present
- 1: Completely wrong or missing correct interest

### Restraint (correct non-return on low-signal inputs)
- 5: Correctly returned nothing on vague/no-topic input
- 4: Returned nothing, acceptable low-score extras
- 3: Minor over-return on low-signal input
- 2: Significant over-return on low-signal input
- 1: Returned strong interests on greeting/vague input

### Ranking Quality (order of returned interests)
- 5: Best match ranked first, clear ordering
- 4: Correct ordering with minor tie-breaking issues
- 3: Ordering technically correct but non-obvious
- 2: Wrong relative ordering
- 1: Inverted ordering (worst match ranked first)
- N/A: Only one interest returned

### Explainability (clarity of match_reasons)
- 5: Every match reason is specific and actionable
- 4: Reasons are clear with minor ambiguity
- 3: Reasons present but generic or partially unclear
- 2: Reasons present but not informative
- 1: Reasons empty or contradictory

### Runtime Usefulness (value to operator reviewing the metadata)
- 5: Metadata would help operator understand context or prioritize
- 4: Metadata useful with minor noise
- 3: Neutral — metadata neither helps nor hurts
- 2: Metadata is distracting
- 1: Metadata is misleading or confusing

### Satellite Readability (clarity for satellite UI presentation)
- 5: Each returned interest has clear display_name and specific reasons
- 4: Readable with minor formatting issues
- 3: Readable but requires context to interpret
- 2: Hard to interpret without looking up the interest
- 1: Unusable in satellite UI without significant transformation

### Overall Score
Average of the 5 applicable dimensions (excluding N/A). Rounded to nearest 0.5.

- ≥4.5: Excellent
- 3.5–4.4: Good
- 2.5–3.4: Acceptable
- 1.5–2.4: Poor
- <1.5: Critical failure

---

## SECTION 5 — SATELLITE UI FEEDBACK MODEL

### Display requirements

The satellite UI should render each evaluation artifact as a collapsible inspection card:

```
┌─ [RR-2026-04-21-003] Ambiguous dual-interest case ──────────────────────┐
│ SCORE: 4.0 / 5  ●●○○  Acceptable                                          │
│ INPUT: "governance and quality are both important for the system"          │
│                                                                         │
│ RETURNED INTERESTS (2):                                                   │
│  1. Governance Quality       score=5  [matched tag: governance]          │
│  2. Tax Reporting            score=2  [tag in text: quality]             │
│                                                                         │
│ DIMENSIONS:                                                              │
│  Accuracy: 4  │  Restraint: 5  │  Ranking: 4  │  Explainability: 3       │
│  Runtime Use: 4  │  Satellite Read: 4                                    │
│                                                                         │
│ FLAGS: none                                                              │
│ RECOMMENDED FOLLOWUP: none                                                │
│                                                                         │
│ NOTES:                                                                  │
│  operator (2026-04-21T...): ranking tie-break by recency worked but     │
│  the second interest (tax_reporting) is clearly spurious here.          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Interaction model
- **Lock button:** Marks evaluation as reviewed — sets `locked: true`
- **Flag button:** Sets `flags.值得关注: true` — marks for attention
- **Add note:** Appends to `eval_notes` with author + timestamp
- **Recommended followup:** Read-only display — no auto-action in v1

### Aggregated view (batch mode)
Satellite UI should show a summary panel for N evaluations:
- Average overall score
- Flag count (false positives / false negatives)
- Most common dimension weakness
- Cases marked `值得关注`

---

## SECTION 6 — HOW RESULTS FEED BACK TO WESLR

Evaluation artifacts are **inspectable by WESLR** but not actionable in v1. The feedback loop is:

### Read path (WESLR can read)
- WESLR's `self_inspection` module can read the evaluation artifact directory
- `InternalReasoningGraphQuery` can be used to query evaluation artifacts by scenario_id, flag, or score
- Results can be surfaced as `inner_thought` metadata in future responses (optional, not implemented in v1)

### Write path (operator only in v1)
- Evaluation artifacts are written by the satellite UI (operator interaction) or by a scheduled cron runner
- WESLR does not write evaluation artifacts autonomously
- No automatic score update from eval results in v1

### Governance gate
- Any proposed scoring adjustment derived from evaluation results must go through `governance_surface`
- The `recommended_followup` field is the input to governance, not the output

### v1 restriction
WESLR may **read** evaluation artifacts as informational context (e.g., in `self_inspection` or `meta_reflection`). WESLR may **not** use evaluation results to:
- Auto-tune `_score_interest()` weights
- Auto-create or delete interests
- Change routing behavior
- Modify `relevance_surface.py` scoring constants

---

## SECTION 7 — FORBIDDEN DRIFT

The following are explicitly prohibited without a canon update and operator approval:

1. **No automatic score tuning from eval results** — evaluation artifacts must not feed back into `_score_interest()` weights, `RECENCY_*_BONUS`, `TAG_MATCH_BONUS`, or any scoring constant without a governed proposal
2. **No direct runtime authority changes from eval artifacts** — a low `accuracy` score on an evaluation must not trigger a code change without governance review and operator approval
3. **No hidden writes to interest data** — eval artifacts must not cause writes to `interests.json` without explicit operator action
4. **No converting eval artifacts into a parallel decision engine** — evaluation results must not become a secondary routing signal
5. **No automatic interest creation from eval results** — a recommendation of `add_interest` must not be executed automatically; it is an operator-facing signal only
6. **No scoring changes without a new design document** — changing any scoring weight in `relevance_surface.py` requires a new design document, not a hotfix

---

## SECTION 8 — RECOMMENDED FIRST IMPLEMENTATION

### What to build first (smallest safe step)

**1. Evaluation artifact storage layer**
- File: `weslr/runtime_relevance_eval.py`
- Functions: `save_relevance_eval(eval_record)`, `load_relevance_eval(scenario_id)`, `list_relevance_evals(filter=None)`
- Storage: `weslr/runtime_relevance_evals/` directory with one JSON file per scenario
- Additive only — no changes to existing modules

**2. Scenario runner (manual)**
- File: `weslr/run_relevance_evals.py`
- Runs the 15 catalog scenarios against the current `query_relevant_interests()` function
- Reads current `interests.json`, computes `_relevant_interests` for each scenario input, produces evaluation artifact records
- Records are saved but NOT automatically scored — scoring is done by operator review
- Run via: `python -m weslr.run_relevance_evals`

**3. Satellite UI integration**
- Uses existing satellite UI infrastructure to render evaluation artifacts
- Read-only display of evaluation artifacts
- Operator can add notes and lock records
- No automatic actions from the UI

**4. NOT in first implementation:**
- No automated scoring (operator reviews each artifact)
- No feedback to WESLR from eval results
- No scoring constant changes
- No governance integration

### Why this is safe
- Evaluation artifacts are **informational only** — they change nothing about runtime behavior
- `query_relevance_interests()` is not modified — scoring is unchanged
- No routing changes — `_relevant_interests` in payloads remains advisory metadata only
- All writes go to a new isolated storage path — no existing files modified

---

## SECTION 9 — STOP LINE

Confirmed:
- ✅ Documentation only — `RUNTIME_RELEVANCE_EVAL_ARTIFACTS_V1.md` is the output
- ✅ No code changes — design document only
- ✅ No behavior changes — no production code touched
- ✅ No scoring changes proposed in v1
- ✅ No governance changes
- ✅ No automatic feedback loops in v1
- ✅ Evaluation artifacts are inspectable, not authoritative
