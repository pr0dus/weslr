# WESLR FRONTDOOR UI SPEC V1

**Version:** 1.0
**Type:** Design / Specification — no implementation required
**Date:** 2026-04-30

---

## SECTION 1 — CORE PRINCIPLE

WESLR is a single-surface conversational system.

**Rules:**
- One visible interaction surface at all times
- No persistent split view (vertical or horizontal)
- No permanent side panels visible by default
- No tool-like UI by default (no visible "tools", "panels", "modes" tabs)
- Everything appears as natural conversation

The user does not need to know WESLR has subsystems, write handlers, evidence stores, or ISS probes. All complexity is invisible unless explicitly explored through conversation.

---

## SECTION 2 — PRIMARY LAYOUT

```
┌─────────────────────────────────────────────────────────┐
│                     WESLR HEADER                        │
│  [optional: session indicator only — no nav, no tabs]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│              CONVERSATION FEED                           │
│                                                          │
│   [User message]                                         │
│   [WESLR response — natural paragraph only]             │
│                                                          │
│   [User message]                                         │
│   [WESLR response]                                      │
│                                                          │
│   [ ... scrollable, newest at bottom ]                  │
│                                                          │
├─────────────────────────────────────────────────────────┤
│   [Free text input field — bottom, always visible]      │
└─────────────────────────────────────────────────────────┘
```

**Visible elements by default:**
- Conversation feed (vertical scroll)
- Single text input field at bottom
- Minimal header (product name only)

**Never visible by default:**
- Graph panels
- Evidence panels
- System panels
- Diagnostics windows
- Proposal browsers
- Flag indicators
- Mode switches

---

## SECTION 3 — RESPONSE DESIGN

Every WESLR response rendered to the user must be:

1. **Natural paragraphs** — prose, not structured output
2. **Inline guidance** — optional parenthetical or follow-up offer
3. **No internal JSON structures** — never expose raw response dicts
4. **No system flags or internal metadata** — never show `_omnichat_policy`, `knowledge_view`, `execution_allowed`, `autonomous_changes_enabled`, or similar
5. **No structured prefixes** — no `knowledge_view:`, `evidence:`, `structured:`, `system:`, `result:`, `info:`

**Correct example:**
> "I can walk through this with you, or if you'd like I can explore the connections involved in more detail. Just let me know."

**Incorrect examples:**
> `knowledge_view: { ... }`
> `evidence: [ ... ]`
> `structured: {"path": "..."}`
> `"source": "direct_answer"`

If WESLR needs to show deeper information, it embeds it inline as explanatory text — not as a revealed data structure.

---

## SECTION 4 — INLINE EXPANSION MODEL

When deeper system data exists (graph context, evidence, diagnostics), it remains **hidden by default**.

**User-driven exposure only:**

| User says | WESLR responds |
|-----------|----------------|
| `"show connections"` | Natural language summary of connections, embedded in response |
| `"what did you find?"` | Narrative explanation, no panel opens |
| `"explain further"` | Inline elaboration inside current response |
| `"show diagnostics"` | (Operator mode only) Inline text, no separate panel |

**Key rule:** Expanding information does not open a new UI panel. The expansion appears as text within the chat — a continuation of the conversation.

**No new panels open under any user action.**

---

## SECTION 5 — EVIDENCE EXPOSURE

Evidence, when surfaced, appears as:

- Natural narrative explanation
- Optional bullet points (brief, readable)
- Always accompanied by a qualifying sentence:
  > "This is exploratory and reflects initial analysis — not confirmed system knowledge."

**Never:**
- A separate "evidence panel"
- Raw evidence JSON or dict structures
- Evidence presented as authoritative system output

---

## SECTION 6 — OPTIONAL PANELS (STRICT GATES)

Panels beyond the chat surface are **operator/dev mode only** and must satisfy all three conditions:

1. **Hidden by default** — never auto-open
2. **User explicitly opens** via conversation or deliberate UI action
3. **Operator/dev mode active** — normal users never see them

**Allowed panel types (operator-only):**
- System overview
- Diagnostics readout
- ISS probe registry
- Proposal / plan list
- Execution log (tail only)

**Allowed trigger language:**
- `"show system overview"` (operator only)
- `"show diagnostics"` (operator only)
- `"show iss probes"` (operator only)

**Condition for visibility:** `execution_allowed` state must be acknowledged in UI state, never as a visible system flag to the user.

---

## SECTION 7 — INPUT FIELD

Single free-text input at the bottom of the conversation feed:

- **No command syntax required** — natural language works
- **No mode switcher** — no "command mode" / "chat mode" toggle
- **No visible command palette** by default
- **No button bar** above input

Commands are accepted naturally (e.g., `"show diagnostics"` works as a message), but are never presented as a required UI element.

---

## SECTION 8 — ERROR / UNKNOWN INPUT UX

When WESLR cannot resolve intent or input is unclear:

**Correct behavior:**
> "I might have misunderstood — would you like me to look into that differently, or try a different angle?"

**Never:**
- Show technical error codes
- Expose internal routing failures
- Display `"path: fallback_safe"` or similar metadata
- Present a system error dialog

The user experience is always conversational clarification. The internal path or classification is never shown.

---

## SECTION 9 — MOBILE BEHAVIOR

Mobile must be **identical** to desktop:

- Full-width conversation feed, no split panels
- Natural paragraph rendering (no horizontal scroll)
- Expansions appear inline within the chat flow
- Input field always visible at bottom
- No drawer, no bottom sheet for system info
- Touch targets for expansion indicators (if any) are large enough to tap comfortably

**No degraded experience on mobile.** All functionality is accessible through conversation; no features require a wider viewport.

---

## SECTION 10 — PROHIBITIONS

The following must **never** appear in user-visible output:

| Prohibited | Reason |
|-----------|--------|
| Raw JSON or Python dict structures | Exposes internal response format |
| System flags (`_omnichat_policy`, `knowledge_view`, `execution_allowed`, etc.) | Internal state, not user-relevant |
| `source`, `intent`, `path` fields from response | Internal routing metadata |
| Proposal IDs or plan IDs | Unless explicitly asked by operator |
| Graph visualizations | No panels by default |
| Evidence panel or evidence list UI | Evidence is narrative only |
| Structured output prefixes (`result:`, `info:`, `system:`) | Breaks conversational illusion |
| Auto-opening panels on any user action | Chat must remain primary surface |

**Prohibited behaviors:**
- Auto-switching UI modes based on detected intent
- Auto-opening diagnostics after any command
- Presenting tool results as separate from conversation
- Showing confirmation dialogs for system-internal actions

---

## SECTION 11 — FUTURE EXTENSIONS

The single-surface rule is permanent. Extensions may add:

- **Collapsible inline sections** — within a message, a "▼" toggle reveals supplementary detail without leaving the chat
- **Expand indicators** — small inline affordance (e.g., `▼ notes`) inside long responses; clicking expands content in-place
- **Operator-only right panel** — accessible only in dev/operator mode, never shown to normal users, containing system overview and diagnostics; chat remains primary and dominant
- **Persistent session indicator** — shows session duration or entity count in header, purely informational, non-interactive

**What remains unchanged:**
- Chat is always the primary and dominant surface
- No second panel visible to normal users
- All complexity is accessible through conversation only

---

## SECTION 12 — SUMMARY

| Element | Rule |
|---------|------|
| Primary surface | Single chat feed |
| Default state | All complexity hidden |
| Exposure model | User-driven, inline only |
| Panels | Operator/dev only, hidden by default |
| Response format | Natural paragraphs only |
| Error handling | Conversational clarification |
| Mobile | Identical to desktop |
| Internal flags | Never exposed |
| Structured output | Never exposed |

---

**Verdict:** WESLR_FRONTDOOR_UI_SPEC_DEFINED