# WESLR Workplace Review Surface V1 — Documentation

> Status: IMPLEMENTED READ-ONLY / NOT WIRED TO CHAT  
> Author: OCC (WESLR governed intelligence)  
> Created: 2026-05-02

---

## Purpose

A single read-only WESLR workplace overview that aggregates:
- pending experiment proposals
- recent project ideas from timeline summaries
- proactive suggestion
- next review actions

It is **not** a task executor. It does not approve, reject, execute, or mutate records.

---

## What It Includes

### Pending Experiment Proposals
Read from `weslr/experiment_proposals.jsonl` (status=pending). Compact view:
`proposal_id`, `type`, `title`, `confidence`, `risk_level`, `requires_operator_approval`, `timeline_id`.

### Recent Ideas
Extracted from recent user timeline summaries using a keyword pattern:
`idea`, `maybe`, `could`, `should`, `experiment`, `project`, `build`, `test`, `try`, `explore`, `investigate`, `design`, `plan`.

Each idea gets an `IDEA-TL-NNN` ID, `read_only_workplace` authority, and a `timeline_id` reference.

### Proactive Suggestion
Delegates to `proactive_suggestions.build_proactive_suggestion()` — one suggestion derived from the most confident timeline theme.

### Next Review Actions
Deterministic, context-sensitive action list:
- "Review N pending experiment proposals" (if any pending)
- "Choose one idea to develop into an experiment" (if any ideas)
- "Consider the proactive suggestion for next steps" (if suggestion available)
- "Continue the latest timeline topic" (fallback)

---

## What It Does NOT Do

- ❌ Approve or reject proposals
- ❌ Execute experiments or actions
- ❌ Mutate JSONL records
- ❌ Store raw prompts
- ❌ Hidden learning
- ❌ Ollama or external service calls
- ❌ /chat integration

---

## Authority

`read_only_workplace` — all ideas and sections carry this authority. Safety flags:
- `automatic_action: false`
- `hidden_learning: false`
- `raw_prompt_stored: false`

---

## Future Extensions

- `/workplace` command integration
- `/projects` view for deeper idea browsing
- Idea-to-experiment conversion workflow
- Operator approval workflow dashboard
- External runner / execution status dashboard
- Continuity section populated from timeline resolution

---

## Usage

```python
from weslr.workplace_review_surface import (
    build_workplace_overview,
    build_workplace_text,
)

overview = build_workplace_overview(
    user_id="arthur",
    proposal_path=None,          # None = default store path
    timeline_base_dir=".weslr/timelines",
)

text = build_workplace_text(overview)
print(text)
```

---

## Files

| File | Purpose |
|---|---|
| `weslr/workplace_review_surface.py` | Main module — 4 functions |
| `weslr/tests/test_workplace_review_surface_v1.py` | 24 unit tests |
