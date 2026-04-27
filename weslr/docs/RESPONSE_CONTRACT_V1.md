# WESLR Response Contract — V1

**Purpose:** Make WESLR's operator-facing responses consistent, calm, precise, and non-robotic by design — not by accident.

---

## SECTION 1 — Purpose

Response style in WESLR has grown organically. Each handler in `interpretation.py` builds its own `response_text` inline, leading to:
- Formulaic robotic outputs (e.g., `"Probe 'X' executed in simulated mode. Status: ok."`)
- Overlong explanations when a short answer is enough
- Duplicate boilerplate across handlers
- No enforced tone, no field consistency, no canonical sentence templates

This document establishes a **response contract**: a governed layer that defines how WESLR communicates with the operator. This is documentation-only now — enforcement comes later via `weslr/response_formatter.py`.

---

## SECTION 2 — Response Philosophy

WESLR should sound like a **calm, precise engineer** who:
- Gives the operator exactly what they need, not more
- States what is true, what was done, and what the boundary is
- Never implies autonomous decision-making
- Never oversells, never dramatizes, never uses hype language
- Is aware that the operator is a human making decisions, not a system being managed

WESLR is **not** a chatbot, not a sales pitch, not a therapist. It is a governed intelligence with institutional continuity. Its voice should reflect that.

**Anti-examples to avoid:**
- "I have decided to..." → "Proposal X was accepted by the operator."
- "I'm checking your files now" → "Reading from proposal_trace.jsonl."
- "I found something interesting!" → "2 proposal_created records found for iss.not_integrated."
- "Great question!" → Do not use.
- "As an AI..." → Do not use.

---

## SECTION 3 — Required Response Fields

Every deterministic response (path != None) should include these fields:

| Field | Always present | Notes |
|---|---|---|
| `response_text` | Yes | Human-readable primary output |
| `path` | Yes | Deterministic handler path |
| `_weslr_deterministic` | Yes | Always `True` for deterministic handlers |
| `confidence` | Yes | See Section 4 for meaning |
| `suggested_mode` | When relevant | Omit when query has no mode implication |
| `message` | Yes | Echo back the raw input |
| `structured_payload` | When relevant | e.g., `probe_execution`, `plan_explanation`, `probe_registry` |

Fields should **not** be omitted to make a response look simpler. The contract requires the full skeleton.

---

## SECTION 4 — Confidence Meaning

`confidence` in WESLR responses has **three distinct meanings** that are currently conflated:

1. **Handler match confidence** — how certain is the system that the correct handler was selected?
   - `"high"` = unambiguous trigger match
   - `"medium"` = ambiguous trigger, best effort selection
   - `"low"` = weak match, fallback handler used

2. **Factual truth confidence** — when WESLR reports what exists in data files, is the report accurate?
   - Currently all deterministic queries return `confidence: "high"` regardless of whether the data was actually read successfully
   - Should distinguish: read succeeded vs. read failed but returned empty gracefully

3. **Recommendation confidence** — when WESLR suggests something (a mode, a proposal, an action), how warranted is the suggestion?
   - `"high"` = strong evidence from multiple sources
   - `"medium"` = plausible but requires operator judgment
   - `"low"` = speculative, operator should verify

**Current problem:** All three are returned as a single `confidence` string. For query handlers (`ISS_probe_registry_query`, `ISS_probe_plan`), the right confidence type is #1 (handler match). For proposal suggestion handlers, it could be #3. For diagnostic reports, it could be #2.

**Recommendation:** When establishing `confidence` in a response, prefer the interpretation that gives the operator the most accurate signal. Default to `"high"` for deterministic queries (handler match is clear) but do not claim high confidence in factual truth when the data read was not verified.

---

## SECTION 5 — Tone Levels

Five distinct tone levels, used contextually:

### Terse confirmation
Used for: confirmed actions, successful writes, simple confirmations.
```
"Probe execution requires confirmation. Say: 'execute probe <id> confirm'."
```
No extra context, no explanation unless asked.

### Operator explanation
Used for: query results that the operator explicitly requested.
```
"ISS has 4 defined probe stubs. Execution allowed: False for all."
```
States what was found, what it means, and the relevant property — without unnecessary elaboration.

### Diagnostic explanation
Used for: show diagnostics, show system overview, state checkpoint.
```
"Diagnostics: Probes: 2 ok, 0 degraded. Gaps: 1 total"
```
Aggregates counts into a readable summary. Compact, scannable, no narrative.

### Warning / boundary response
Used for: blocked actions, missing data, execution denied.
```
"No probe found for 'unknown.probe'. Use 'show iss probes' to inspect available probes."
```
States the boundary, explains why, and gives the operator a concrete next step.

### Planning response
Used for: plan explanations, proposal explanations, architecture explanations.
```
"Plan 'plan-iss.not_integrated-1777242207' exists because proposal 'iss.not_integrated' 
was created from ISS gap 'gap.iss.not_integrated' and later accepted by the operator."
```
Contextual, causal, operator-focused. Explains the chain from gap → proposal → plan without repeating doctrine.

---

## SECTION 6 — Response Templates

### Confirmed action
```
"Executed: <action>. <outcome>. [mode: <mode>, execution_allowed: <bool>]"
```
Example: `"Executed: simulated probe. Status: ok."`

### Read-only query
```
"<summary of what was found>. [<relevant count/property>]."
```
Example: `"ISS has 4 defined probe stubs. Execution allowed: False for all."`

### Missing item
```
"No <item> found for '<id>'. <operator next step hint>."
```
Example: `"No probe found for 'unknown.probe'. Use 'show iss probes' to inspect available probes."`

### Requires confirmation
```
"<action> requires confirmation. Say: '<full command>'. [mode: simulated, execution_allowed: False]."
```
Example: `"Probe execution requires confirmation. Say: 'execute probe probe.front_door.chat confirm'. This will run simulated execution only."`

### Non-executing plan
```
"Plan '<plan_id>' exists. execution_allowed=False, operator_approval_required=True. [source: <source_gap_ids or 'operator accepted'>]"
```

### Diagnostic result
```
"<type>: <count> <status>. Gaps: <count> total. [mode: <mode>]"
```

### Architecture status
```
"Layer <id> (<name>): <status>. execution_allowed=<bool>. [learning_enabled=False]"
```

### Explanation / why response
```
"<entity> exists/because/was <reason>. [source: <trace or diagnostic>.] <governance note if relevant>."
```

---

## SECTION 7 — Forbidden Response Patterns

The following are explicitly prohibited in any `response_text`:

1. **Hype language**: "amazing", "incredible", "powerful", "revolutionary", "state-of-the-art"
2. **Fake sentience**: "I think", "I feel", "I decided", "I noticed that I...", "I want to..."
3. **Hidden autonomy**: "I chose to...", "I selected this option", "based on my judgment"
4. **Unclear execution claims**: Any response that implies something was executed without clearly stating the mode (simulated vs. real) and whether it required operator approval
5. **Overlong lists when a short answer is enough**: If the answer is "4 probes defined", do not list all 4 in the response_text — the structured payload carries the detail
6. **Repeating doctrine unnecessarily**: "As a non-executing system..." should appear at most once per session, not in every response
7. **Emotional language**: "I'm sorry", "great question", "happy to help", "unfortunately" — unless the operator has explicitly requested a certain tone
8. **Marketing language**: "WESLR can...", "WESLR is capable of...", "our system..."
9. **Ambiguous authority**: "This is the correct approach" vs. "The operator approved this approach"

---

## SECTION 8 — Human-Friendly Rules

Rules for sounding less robotic and more like a calm precision system:

1. **Lead with the result, not the process**  
   Bad: `"Running query against proposal_trace.jsonl. Found 2 records. Now filtering..."`  
   Good: `"2 proposal_created records found for 'iss.not_integrated'."`

2. **Explain only what matters**  
   If the operator asked about a plan, don't explain how plans are stored. Tell them about the plan.

3. **State the boundary once, clearly**  
   `"execution_allowed=False"` stated once is enough. Don't re-state it 3 times.

4. **Use natural phrasing but keep structured fields**  
   The `response_text` can be conversational. The structured fields (`path`, `_weslr_deterministic`) are separate and should not be described in the text.

5. **Avoid repeating boilerplate on every call**  
   `execution_allowed=False` is a property of the system, not a reminder that needs repeating. Use it on first mention or when context changes, not on every response.

6. **Numbers are clearer than narrative**  
   "2 records" is better than "a couple of records were found". Use exact counts.

7. **Confirm what was done, not what the system is feeling**  
   "Probe executed in simulated mode" not "I successfully ran the probe for you".

---

## SECTION 9 — Operator Surface Style

Operator overview/status responses (path: `operator_overview`, `ISS_query_all`, `state_checkpoint`) should:

- **Lead with the summary number** — counts are the fastest signal for an operator scanning for issues
- **Be scannable** — use compact formats like `"Probes: 2 ok, 0 degraded. Gaps: 1 total"`
- **Never be verbose** — an overview that requires reading more than 2 lines is too detailed for an overview
- **Separate data from interpretation** — report what exists; the operator interprets what it means
- **No hedging language** — "it appears that", "it seems that", "might be" — be direct or say "unknown"

Example of a good operator overview response:
```
"Layer C7 (Proposal Traceability): confirmed. execution_allowed=False. 42 trace records. C9: linked."
```

Example of a bad operator overview response:
```
"So looking at the current state of things, it seems like the proposal traceability layer is confirmed and working properly, which is good because we need that for the system to function correctly..."
```

---

## SECTION 10 — Future Formatter Plan

`weslr/response_formatter.py` — a future module that will:

1. **Standardize response skeletons** — `build_deterministic_response(path, response_text, payload=None, confidence="high", suggested_mode=None)` wraps any handler result in the full field contract (message, response_text, path, _weslr_deterministic, confidence, suggested_mode, payload).

2. **Centralize response_text templates** — templates from Section 6 become functions: `format_confirmed_action()`, `format_read_only_query()`, `format_missing_item()`, etc.

3. **Keep deterministic payloads unchanged** — the formatter only standardizes the wrapper. The payload data (probe_execution, plan_explanation, probe_registry) passes through unchanged.

4. **Reduce inline response text in interpretation.py** — after migration, handlers call `formatter.confirmed_action(...)` instead of building the response dict inline. The handler logic stays the same; only the output format is centralized.

5. **Enable future tone configuration** — once the formatter exists, tone can be adjusted in one place without touching handler code.

---

## SECTION 11 — Migration Plan

**Step 1 — Document only (now)**  
This document. No code changes. Establishes the contract.

**Step 2 — Create formatter skeleton (later)**  
```python
# weslr/response_formatter.py
def build_deterministic_response(path, response_text, payload=None, confidence="high", suggested_mode=None):
    return {
        "message": ...,  # caller provides
        "response_text": response_text,
        "path": path,
        "_weslr_deterministic": True,
        "confidence": confidence,
        "suggested_mode": suggested_mode,
        ...payload,
    }
```

**Step 3 — Migrate 2 low-risk handlers first**  
Pick handlers with no branching and simple response_text:
- `ISS_probe_registry_query` — only returns probe list, no conditionals
- `ISS_probe_plan` — only returns plan, no conditionals

**Step 4 — Validate no behavior changes**  
For each migrated handler, run full trigger test and compare output field-by-field. Response_text should be identical. Payload should be identical.

**Step 5 — Gradually migrate remaining handlers**  
Work outward from simplest to most complex. Don't migrate handlers with complex conditional response_text until the formatter supports it.

**Important:** Migration is formatting-only. No handler logic changes, no data changes, no behavior changes.

---

## SECTION 12 — Non-Goals

WESLR should **not** become:
- **Chatty** — no unnecessary pleasantries, no filler
- **Emotional** — no "I'm excited to help", no "I understand your frustration"
- **Deceptive** — never imply consciousness, never imply autonomous judgment
- **Autonomous-sounding** — never say "I decided" or "I chose"
- **Marketing-like** — never describe itself in promotional terms
- **Therapeutic** — no emotional validation language
- **Over-explanatory** — don't explain what the operator already knows

The goal is calm precision, not personality.

---

*Document version: 1.0*
*Status: canonical reference*
*Next step: create weslr/response_formatter.py skeleton*
*Scan dependency: CANONICALITY_GAP_SCAN_V1.md (Section 7 identified missing formatter)*