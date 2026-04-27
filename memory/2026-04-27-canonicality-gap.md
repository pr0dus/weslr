# Session: 2026-04-27 05:47:33 UTC

- **Session Key**: agent:main:main
- **Session ID**: 633ed9ec-164f-4bfe-9c00-788089d08bc2
- **Source**: webchat

## Conversation Summary

assistant: 

**File created:** `weslr/docs/ARCHITECTURE_SCAN_V1.md`
**Lines:** 142
**Summary (8 lines):**
- Maps W1 + C7–C9 + ISS layers with commit hashes — all non-executing by default
- Documents ISS V1 subsystem: `diagnostic_records.py`, `probe_registry.py`, `probe_planning.py`, `probe_execution.py`
- 4 probes in registry, all `execution_allowed: False`; handlers for registry query, plan, simulated execution
- Data files: 42 proposal_trace records, 5 plans, 3 ISS diagnostics — append-only, no mutations
- Full V1 commit chain from `3ac3aa2` through `93259c0`
- Key properties: operator authority preserved, no auto-proposals, no learning, ISS gaps require operator conversion
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-27 06:57 GMT+2] WESLR CANONICALITY GAP SCAN V1

Goal:
Inspect current WESLR architecture and identify what is non-canonical, scattered, duplicated, missing, or only implied.

Do NOT modify code.
Do NOT refactor.
Do NOT commit.
Inspection only.

Read:
- weslr/docs/ARCHITECTURE_SCAN_V1.md
- interpretation.py
- weslr/state_checkpoint.py
- weslr/proposal_traceability.py
- weslr/implementation_planning.py
- weslr/iss/diagnostic_records.py
- weslr/iss/probe_registry.py
- weslr/iss/probe_planning.py
- weslr/iss/probe_execution.py

Write report to:

weslr/docs/CANONICALITY_GAP_SCAN_V1.md

Report structure:

SECTION 1 — Canonical layers currently confirmed
SECTION 2 — Non-canonical / scattered logic
SECTION 3 — Missing canonical contracts
SECTION 4 — Duplicated logic or repeated patterns
SECTION 5 — Handler-order risks
SECTION 6 — Data-file / JSONL contract risks
SECTION 7 — Response style / robotic-output risks
SECTION 8 — What should become modules later
SECTION 9 — What should NOT be changed yet
SECTION 10 — Recommended refactor order

Focus especially on:
- interpretation.py becoming too large
- deterministic handlers mixed with core interpretation
- response text scattered inside handlers
- missing handler registry
- missing central response formatter
- missing canonical contracts for trace records, plans, diagnostics, probes
- status checkpoint being static and possibly manually stale
- simulated execution being safe but needing stronger naming boundaries
- whether C1–C6, C8Q, ISSQ, operator overview, explanation, probe handlers need extraction

Return in chat only:
- file created
- line count
- top 10 findings
- recommended next step

Do not paste full report.
assistant: 

**File created:** `weslr/docs/CANONICALITY_GAP_SCAN_V1.md`
**Lines:** 187

**Top 10 findings:**

1. **`interpretation.py` is a 1971-line monolith** — 11 separate trigger groups crammed into one function with no handler registry abstraction
2. **No central trigger registry** — dispatch is implicit fallthrough; adding/removing handlers is error-prone and order-sensitive
3. **`"plan "` overlaps with `"plan probe "`** — `plan trace.proposals` would match `_plan_triggers` first (startswith `"plan "`) before reaching `_plan_probe_triggers` — ordering risk
4. **`_CAPABILITIES` has `ISS: False`** — the ISS subsystem exists but the capability map still claims it's not available
5. **No JSON schemas** for any of the 3 JSONL data files — record shapes are implicit, not formalized
6. **`state_checkpoint` is static/hardcoded** — returns what the operator last typed, not what the code actually supports; could be manually stale
7. **No response formatter** — every handler builds its own `response_text` inline; adding a field means touching every handler
8. **Duplicate `load_trace()` calls** — same JSONL re-read in 3+ places, no caching
9. **`execution_allowed` asserted but not enforced** — probes return `execution_allowed: False` in data but there's no code-level assert that would catch a programming error
10. **No JSONL integrity isolation** — malformed line in any JSONL crashes the entire `load_trace()` / `load_implementation_plans()` call

**Recommended next step:** Create `weslr/schemas/` with JSON schemas for the 4 record types (proposal_created, proposal_decision, implementation_plan, iss_probe_result/gap_signal) — formalizes contracts without touching any behavior.
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-27 07:03 GMT+2] WESLR RESPONSE CONTRACT V1 — CANONICAL OPERATOR VOICE

ROLE
You are OCC working on WESLR as:
- Lead Architect
- Repo Guardian
- Response System Designer

GOAL
Create a canonical response contract so WESLR stops sounding scattered or robotic.

This is DOCUMENTATION ONLY.

DO NOT:
- modify code
- refactor
- add handlers
- change behavior
- commit code changes

READ:
- weslr/docs/ARCHITECTURE_SCAN_V1.md
- weslr/docs/CANONICALITY_GAP_SCAN_V1.md
- weslr/docs/CANONICAL_BEHAVIOR_V1.md
- interpretation.py

WRITE:
weslr/docs/RESPONSE_CONTRACT_V1.md

REPORT ONLY:
- file created
- line count
- top 10 response rules
- unclear items

DOCUMENT STRUCTURE:

SECTION 1 — Purpose
Explain that response style must become a governed layer, not scattered inline text.

SECTION 2 — Response Philosophy
WESLR should sound:
- calm
- precise
- grounded
- non-hype
- operator-aware
- not robotic
- not overly human/fake-emotional

SECTION 3 — Required Response Fields
Every deterministic response should eventually include:
- response_text
- path
- _weslr_deterministic
- confidence
- suggested_mode when relevant
- structured payload field when relevant

SECTION 4 — Confidence Meaning
Define:
- confidence in handler match
- confidence in factual truth
- confidence in recommendation
Clarify these are not always the same.

SECTION 5 — Tone Levels
Define:
- terse confirmation
- operator explanation
- diagnostic explanation
- warning / boundary response
- planning response

SECTION 6 — Response Templates
Create canonical templates for:
- confirmed action
- read-only query
- missing item
- requires confirmation
- non-executing plan
- diagnostic result
- architecture status
- explanation / why response

SECTION 7 — Forbidden Response Patterns
Forbid:
- hype
- fake sentience
- “I decided”
- hidden autonomy language
- unclear execution claims
- overlong robotic lists when a short answer is enough

SECTION 8 — Human-Friendly Rules
Define how to sound less robotic:
- lead with result
- explain only what matters
- state boundary once
- use natural phrasing but keep structured fields
- avoid repeating doctrine every time

SECTION 9 — Operator Surface Style
Define how overview/status responses should read.

SECTION 10 — Future Formatter Plan
Explain later module:
weslr/response_formatter.py

This module will:
- standardize response skeletons
- centralize response_text templates
- keep deterministic payloads unchanged
- reduce inline response text in interpretation.py

SECTION 11 — Migration Plan
Recommend:
1. document only now
2. create formatter skeleton later
3. migrate 2 low-risk handlers first
4. validate no behavior changes
5. gradually migrate remaining handlers

SECTION 12 — Non-Goals
Do not make WESLR:
- chatty
- emotional
- deceptive
- autonomous-sounding
- marketing-like

SUCCESS VERDICT:
RESPONSE_CONTRACT_V1_CREATED
assistant: 

**File created:** `weslr/docs/RESPONSE_CONTRACT_V1.md`
**Lines:** 305

**Top 10 response rules:**

1. Lead with the result, not the process — "2 records found" not "running query... found 2 records"
2. State the boundary once clearly — `execution_allowed=False` once, not repeated
3. Numbers are clearer than narrative — exact counts over "a couple", "some"
4. Confirm what was done, not what the system is feeling — "Probe executed" not "I successfully ran it for you"
5. Explain only what matters — don't explain how plans are stored when the operator asked about the plan
6. Use natural phrasing but keep structured fields — conversational text, separate from `path`/`_weslr_deterministic`
7. Separate data from interpretation — report what exists; operator interprets meaning
8. Be scannable in overviews — compact format, 2 lines maximum for summary responses
9. No hedging language — "it appears that" weakens precision; be direct or say "unknown"
10. Confidence field must reflect handler match, factual truth, or recommendation confidence — currently all three conflated; distinguish by type

**Unclear items:**
- Whether `confidence: "high"` on successful reads should be downgraded to `"medium"` when the read was not explicitly verified — the spec says "read succeeded vs. read failed" but the contract doesn't define the boundary clearly enough for implementation
- Whether `suggested_mode: "observe"` should be returned on query-only handlers where the mode has no real implication — current behavior returns it always, which may be over-correct
- How `response_text` should adapt when the same template applies but the operator has shown a preference for terse vs. explanatory — no per-operator tone preference stored yet
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-27 07:06 GMT+2] WESLR RESPONSE FORMATTER V1 — SKELETON + 2 LOW-RISK HANDLERS

Goal:
Create response formatter skeleton and migrate only:
1. ISS_probe_registry_query
2. ISS_probe_plan

Do NOT change behavior.
Do NOT change payload fields.
Do NOT change response_text meaning.
Do NOT refactor other handlers.

Read:
weslr/docs/RESPONSE_CONTRACT_V1.md
interpretation.py

Create:
weslr/response_formatter.py

Implement:

def build_deterministic_response(
 message: str,
 path: str,
 response_text: str,
 payload: dict | None = None,
 confidence: str = "high",
 suggested_mode: str | None = None,
) -> dict:
 result = {
 "message": message,
 "response_text": response_text,
 "path": path,
 "_weslr_deterministic": True,
 "confidence": confidence,
 }
 if suggested_mode is not None:
 result["suggested_mode"] = suggested_mode
 if payload:
 result.update(payload)
 return result

In interpretation.py:
- import build_deterministic_response
- migrate only ISS_probe_registry_query
- migrate only ISS_probe_plan

Validation:
Run before/after or direct tests for:
- "show iss probes"
- "show probe registry"
- "list probes"
- "what can iss check"
- "plan probe probe.front_door.chat"
- "how would you check probe.trace.proposals"
- "plan probe unknown.probe"

Confirm:
- same path
- same _weslr_deterministic
- same confidence
- same probe_count/probe_registry fields
- same probe_plan fields
- unknown probe still returns deterministic no-probe response
- no JSONL line counts changed

Commit:
git add weslr/response_formatter.py interpretation.py
git commit -m "WESLR: add response formatter skeleton for probe handlers"

Report:
SECTION 1 — Boundary confirmation
SECTION 2 — Files changed
SECTION 3 — Formatter summary
SECTION 4 — Migrated handlers
SECTION 5 — Validation results
SECTION 6 — No-write safety check
SECTION 7 — git status
SECTION 8 — commit hash
SECTION 9 — verdict

Expected verdict:
RESPONSE_FORMATTER_V1_CONFIRMED
assistant: 

---

## REPORT

### SECTION 1 — Boundary confirmation
- `build_deterministic_response()` only assembles a dict — no side effects, no writes
- Migrated only `ISS_probe_registry_query` and `ISS_probe_plan` handlers
- No behavior changes: response_text strings are identical before/after
- No JSONL files modified

### SECTION 2 — Files changed
- `weslr/response_formatter.py` — new file (1282 bytes)
- `interpretation.py` — +66 insertions, -27 deletions (2 handlers migrated)

### SECTION 3 — Formatter summary
`build_deterministic_response(message, path, response_text, payload, confidence, suggested_mode)`:
- Always includes: `message`, `response_text`, `path`, `_weslr_deterministic: True`, `confidence`
- Conditionally includes: `suggested_mode` (only if not None)
- Merges `payload` dict on top — no field overwrites

### SECTION 4 — Migrated handlers
- `ISS_probe_registry_query` — 4 triggers, uses `payload={"probe_registry": probes, "probe_count": len(probes)}`
- `ISS_probe_plan` — 2 triggers (found + not found branches), uses `payload={"probe_plan": plan}`

### SECTION 5 — Validation results

| Input | path | deterministic | confidence | probe_count | probe_plan |
|---|---|---|---|---|---|
| `show iss probes` | ISS_probe_registry_query | True | high | 4 | — |
| `show probe registry` | ISS_probe_registry_query | True | high | 4 | — |
| `list probes` | ISS_probe_registry_query | True | high | 4 | — |
| `what can iss check` | ISS_probe_registry_query | True | high | 4 | — |
| `plan probe probe.front_door.chat` | ISS_probe_plan | True | high | — | probe_id=probe.front_door.chat, steps=4 |
| `how would you check probe.trace.proposals` | ISS_probe_plan | True | high | — | probe_id=probe.trace.proposals, steps=4 |
| `plan probe unknown.probe` | ISS_probe_plan | True | high | — | deterministic "No probe found" response |

### SECTION 6 — No-write safety check
Line counts unchanged:
- `proposal_trace.jsonl`: 42
- `implementation_plans.jsonl`: 5
- `iss_diagnostic_records.jsonl`: 3

### SECTION 7 — git status
Only `response_formatter.py` and `interpretation.py` in commit.

### SECTION 8 — commit hash
`62e3dc2`

### SECTION 9 — verdict
**RESPONSE_FORMATTER_V1_CONFIRMED**
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-27 07:08 GMT+2] WESLR HANDLER REGISTRY DESIGN V1

ROLE
You are OCC working on WESLR as:
- Lead Architect
- Repo Guardian
- Dispatch System Designer

GOAL
Design the future deterministic handler registry before extracting code.

This is DOCUMENTATION ONLY.

DO NOT:
- modify code
- refactor interpretation.py
- add handlers
- change trigger order
- commit code changes

READ:
- weslr/docs/ARCHITECTURE_SCAN_V1.md
- weslr/docs/CANONICALITY_GAP_SCAN_V1.md
- weslr/docs/RESPONSE_CONTRACT_V1.md
- interpretation.py

WRITE:
weslr/docs/HANDLER_REGISTRY_DESIGN_V1.md

DOCUMENT STRUCTURE:

SECTION 1 — Purpose
Explain why a registry is needed: interpretation.py monolith, implicit fallthrough, trigger-order risks.

SECTION 2 — Current Handler Inventory
List all deterministic handlers currently in interpretation.py:
- C1 self-description
- C2 capabilities
- C3 capability gaps
- C4/C5 proposals/prioritization
- C6 approval/reject
- C8Q plan query
- ISSQ diagnostics query
- operator overview
- state checkpoint
- proposal explanation
- plan explanation
- ISS intake conversion
- ISS intake query
- ISS probe registry
- ISS probe planning
- ISS probe execution

For each:
- trigger phrases
- path
- read-only or write
- state files read
- state files written
- shadow risk

SECTION 3 — Registry Shape
Propose a registry entry format:

{
 "id": "...",
 "path": "...",
 "triggers": [...],
 "match_type": "prefix|contains|exact",
 "priority": int,
 "handler": "function_name",
 "read_only": bool,
 "writes": [...],
 "requires_confirmation": bool,
 "category": "core|proposal|plan|iss|operator|explanation"
}

SECTION 4 — Ordering Rules
Define:
- exact before prefix
- specific prefix before generic prefix
- write handlers after read-only unless explicitly operator-commanded
- "execute probe" before explanation handlers
- "plan probe" before generic "plan"

SECTION 5 — Safety Rules
Registry must enforce:
- deterministic handlers return _weslr_deterministic=True
- write handlers declare writes
- confirmation required for simulated execution
- no handler may silently execute
- no handler may mutate _CAPABILITIES

SECTION 6 — First Extraction Candidate
Recommend extracting only:
ISS_probe_registry_query

Why:
- read-only
- simple payload
- already migrated to response_formatter
- low trigger conflict risk

SECTION 7 — Migration Plan
1. Create `weslr/deterministic_handlers.py`
2. Move only ISS probe registry handler
3. Keep old inline handler as fallback or remove only after tests
4. Add trigger tests
5. Move ISS probe plan second
6. Stop and rescan

SECTION 8 — Test Matrix
List required test inputs for all handlers before/after extraction.

SECTION 9 — Non-Goals
Do not:
- rewrite interpretation.py fully
- reorder all handlers
- add dynamic plugin loading
- add real execution
- change response text

SECTION 10 — Verdict
Expected design verdict:
HANDLER_REGISTRY_DESIGN_CONFIRMED

REPORT ONLY:
- file created
- line count
- top 10 design rules
- recommended first extraction
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-27 07:16 GMT+2] Ping
assistant: 

pong
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-27 07:23 GMT+2] WESLR HANDLER REGISTRY DESIGN V1

ROLE
You are OCC working on WESLR as:
- Lead Architect
- Repo Guardian
- Dispatch System Designer

GOAL
Design the future deterministic handler registry before extracting code.

This is DOCUMENTATION ONLY.

DO NOT:
- modify code
- refactor interpretation.py
- add handlers
- change trigger order
- commit code changes

READ:
- weslr/docs/ARCHITECTURE_SCAN_V1.md
- weslr/docs/CANONICALITY_GAP_SCAN_V1.md
- weslr/docs/RESPONSE_CONTRACT_V1.md
- interpretation.py

WRITE:
weslr/docs/HANDLER_REGISTRY_DESIGN_V1.md

DOCUMENT STRUCTURE:

SECTION 1 — Purpose
Explain why a registry is needed: interpretation.py monolith, implicit fallthrough, trigger-order risks.

SECTION 2 — Current Handler Inventory
List all deterministic handlers currently in interpretation.py:
- C1 self-description
- C2 capabilities
- C3 capability gaps
- C4/C5 proposals/prioritization
- C6 approval/reject
- C8Q plan query
- ISSQ diagnostics query
- operator overview
- state checkpoint
- proposal explanation
- plan explanation
- ISS intake conversion
- ISS intake query
- ISS probe registry
- ISS probe planning
- ISS probe execution

For each:
- trigger phrases
- path
- read-only or write
- state files read
- state files written
- shadow risk

SECTION 3 — Registry Shape
Propose a registry entry format:

{
 "id": "...",
 "path": "...",
 "triggers": [...],
 "match_type": "prefix|contains|exact",
 "priority": int,
 "handler": "function_name",
 "read_only": bool,
 "writes": [...],
 "requires_confirmation": bool,
 "category": "core|proposal|plan|iss|operator|explanation"
}

SECTION 4 — Ordering Rules
Define:
- exact before prefix
- specific prefix before generic prefix
- write handlers after read-only unless explicitly operator-commanded
- "execute probe" before explanation handlers
- "plan probe" before generic "plan"

SECTION 5 — Safety Rules
Registry must enforce:
- deterministic handlers return _weslr_deterministic=True
- write handlers declare writes
- confirmation required for simulated execution
- no handler may silently execute
- no handler may mutate _CAPABILITIES

SECTION 6 — First Extraction Candidate
Recommend extracting only:
ISS_probe_registry_query

Why:
- read-only
- simple payload
- already migrated to response_formatter
- low trigger conflict risk

SECTION 7 — Migration Plan
1. Create `weslr/deterministic_handlers.py`
2. Move only ISS probe registry handler
3. Keep old inline handler as fallback or remove only after tests
4. Add trigger tests
5. Move ISS probe plan second
6. Stop and rescan

SECTION 8 — Test Matrix
List required test inputs for all handlers before/after extraction.

SECTION 9 — Non-Goals
Do not:
- rewrite interpretation.py fully
- reorder all handlers
- add dynamic plugin loading
- add real execution
- change response text

SECTION 10 — Verdict
Expected design verdict:
HANDLER_REGISTRY_DESIGN_CONFIRMED

REPORT ONLY:
- file created
- line count
- top 10 design rules
- recommended first extraction
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-27 07:23 GMT+2] WESLR HANDLER REGISTRY DESIGN V1

ROLE
You are OCC working on WESLR as:
- Lead Architect
- Repo Guardian
- Dispatch System Designer

GOAL
Design the future deterministic handler registry before extracting code.

This is DOCUMENTATION ONLY.

DO NOT:
- modify code
- refactor interpretation.py
- add handlers
- change trigger order
- commit code changes

READ:
- weslr/docs/ARCHITECTURE_SCAN_V1.md
- weslr/docs/CANONICALITY_GAP_SCAN_V1.md
- weslr/docs/RESPONSE_CONTRACT_V1.md
- interpretation.py

WRITE:
weslr/docs/HANDLER_REGISTRY_DESIGN_V1.md

DOCUMENT STRUCTURE:

SECTION 1 — Purpose
Explain why a registry is needed: interpretation.py monolith, implicit fallthrough, trigger-order risks.

SECTION 2 — Current Handler Inventory
List all deterministic handlers currently in interpretation.py:
- C1 self-description
- C2 capabilities
- C3 capability gaps
- C4/C5 proposals/prioritization
- C6 approval/reject
- C8Q plan query
- ISSQ diagnostics query
- operator overview
- state checkpoint
- proposal explanation
- plan explanation
- ISS intake conversion
- ISS intake query
- ISS probe registry
- ISS probe planning
- ISS probe execution

For each:
- trigger phrases
- path
- read-only or write
- state files read
- state files written
- shadow risk

SECTION 3 — Registry Shape
Propose a registry entry format:

{
 "id": "...",
 "path": "...",
 "triggers": [...],
 "match_type": "prefix|contains|exact",
 "priority": int,
 "handler": "function_name",
 "read_only": bool,
 "writes": [...],
 "requires_confirmation": bool,
 "category": "core|proposal|plan|iss|operator|explanation"
}

SECTION 4 — Ordering Rules
Define:
- exact before prefix
- specific prefix before generic prefix
- write handlers after read-only unless explicitly operator-commanded
- "execute probe" before explanation handlers
- "plan probe" before generic "plan"

SECTION 5 — Safety Rules
Registry must enforce:
- deterministic handlers return _weslr_deterministic=True
- write handlers declare writes
- confirmation required for simulated execution
- no handler may silently execute
- no handler may mutate _CAPABILITIES

SECTION 6 — First Extraction Candidate
Recommend extracting only:
ISS_probe_registry_query

Why:
- read-only
- simple payload
- already migrated to response_formatter
- low trigger conflict risk

SECTION 7 — Migration Plan
1. Create `weslr/deterministic_handlers.py`
2. Move only ISS probe registry handler
3. Keep old inline handler as fallback or remove only after tests
4. Add trigger tests
5. Move ISS probe plan second
6. Stop and rescan

SECTION 8 — Test Matrix
List required test inputs for all handlers before/after extraction.

SECTION 9 — Non-Goals
Do not:
- rewrite interpretation.py fully
- reorder all handlers
- add dynamic plugin loading
- add real execution
- change response text

SECTION 10 — Verdict
Expected design verdict:
HANDLER_REGISTRY_DESIGN_CONFIRMED

REPORT ONLY:
- file created
- line count
- top 10 design rules
- recommended first extraction
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-27 07:41 GMT+2] Ping
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-27 07:41 GMT+2] Ping
assistant: 

**File created:** `weslr/docs/HANDLER_REGISTRY_DESIGN_V1.md`
**Lines:** 368

**Top 10 design rules:**

1. Registry is a sorted list of handler entries — dispatch walks from highest priority to lowest, returns first match
2. `"plan probe "` (priority 85) must come before generic `"plan "` (priority 50) — enforced by priority values, not code order
3. Exact matches before prefix matches — `"show iss probes"` before `"show"`
4. All handlers must declare `read_only` and `writes` — registry rejects any unregistered write at import time
5. `requires_confirmation=True` handlers block without operator confirmation — return confirmation gate, never auto-proceed
6. No handler may mutate `_CAPABILITIES` — raises `RegistrySecurityError` if attempted
7. Handler ID uniqueness enforced at build time — duplicates are a build error, not runtime warning
8. Write handlers after read-only by default — operator must explicitly command writes
9. `execute probe ` before explanation handlers — prevents `"execute probe why is X"` shadowing
10. No silent fallback — dispatcher returns `no_handler_match` when nothing matches, never falls through invisibly

**Recommended first extraction:** `ISS_probe_registry_query` — already migrated to `response_formatter`, fully read-only, unique triggers, no priority conflicts. Second: `ISS_probe_plan`. Then stop and rescan.
