# CONTEXT_AND_BOUNDARY_SIGNALS_V1

**Status:** Canonical · Active  
**Applies to:** `dialogue.py` runtime response metadata  
**Signals:** `_context_selection_v1` · `_boundary_hints`

---

## SECTION 1 — PURPOSE

### Why these signals exist

The system needs a lightweight structural description of each turn — not what the user wants done, but what is structurally present in the message and what is currently governing the response.

This was introduced because the system previously lacked any structural distinction between, for example:

- a user referencing a stored artifact versus introducing a new topic
- a turn that references a tool versus a turn about a role
- a continuation versus a clean break

Without these signals, the system had no observable way to tell the difference without making implicit assumptions or hardcoded domain labels.

### Why they must remain generic and structural

If the signals become coupled to product names, domain labels, routing logic, or governance, they become part of the system they were meant to describe — creating a circular dependency. The signal would then reflect the system's own state, not the input's structure.

Keeping them generic and structural means they remain **observational**: they describe what is present without asserting what should happen.

### Why this is different from domain labeling or routing

A domain label assigns a message to a bucket (e.g. "openclaw", "weslr_core", "infinity"). A context selection describes the relationship between the message and the system's current state — specifically, whether the turn is governed by an ongoing thread, a resolved artifact, or a fresh topic.

Boundary hints classify the kinds of entities mentioned — not what they mean or whether they are important.

Neither is a routing instruction. Neither is a domain label. Neither implies authority over what happens next.

---

## SECTION 2 — CURRENT REALITY

### `_context_selection_v1`

**Allowed values (exact set, no extensions without canon):**

| Value | Meaning |
|---|---|
| `current_thread` | Active thread present; message is a continuation with no artifact reference |
| `resolved_artifact` | Active artifact was resolved; the turn references stored content |
| `new_topic` | Message introduces a clearly new topic (no overlap, no reference phrases) |
| `uncertain` | Cannot determine — empty input or ambiguous signal |

**Purpose:** Describe what structurally governs the current turn — thread, artifact, new topic, or unclear.

**Implementation:** `_compute_context_selection(message, research_context, active_thread)`  
Location: `dialogue.py` — do not move without separate canon.

**Rules (fixed):**
- `research_context._has_active_artifact` → `resolved_artifact` (always, no exceptions)
- `active_thread` present + no reference phrase → `current_thread`
- message starts with `_NEW_TOPIC_SIGNALS` keyword + no reference phrase → `new_topic`
- otherwise → `uncertain`

**Observational only:** This field describes the turn. It does not trigger behavior.

---

### `_boundary_hints`

**Allowed values (exact set, no extensions without canon):**

| Value | Trigger keywords (non-exhaustive examples) |
|---|---|
| `system` | system, platform, environment, infrastructure, host, device |
| `module` | module, plugin, component, package, library, dependency |
| `tool` | tool, cli, command, app, application, utility |
| `runtime` | runtime, engine, process, instance, daemon, service |
| `role` | user, operator, agent, role, person, human, collaborator |
| `interface` | ui, api, endpoint, interface, port, hook, handler, webhook |
| `data` | data, artifact, state, config, memory, context, message, file |
| `unknown` | Nothing matches |

**Purpose:** Describe what structural types of entities/concepts are present in the turn — not which specific entities, not their importance.

**Implementation:** `_compute_boundary_hints(message)`  
Location: `dialogue.py` — do not move without separate canon.

**Rules (fixed):**
- Returns unique sorted list of matching types
- If nothing matches → `["unknown"]`
- Empty message → `["unknown"]`

**Observational only:** This field describes the turn. It does not trigger behavior.

---

## SECTION 3 — NON-AUTHORITY RULE

These signals are **descriptive, not authoritative**.

Explicitly:

- They do not grant permission to act
- They do not change system behavior
- They do not trigger routing, scoring, governance, or execution
- They do not suppress or modify responses
- They do not create obligations for downstream handlers

The signals describe what is present. What happens next is determined by the existing routing, governance, and execution logic — which operates independently.

Any use that causes these signals to influence behavior must be proposed as a separate architectural change with its own canon and review.

---

## SECTION 4 — RELATION TO OTHER SYSTEMS

### Continuity resolution

Context selection is orthogonal to continuity resolution. Continuity resolution determines what the system considers active (artifact, thread). Context selection describes the structural relationship of the incoming message to that active state.

They can both fire simultaneously without conflict:
- Continuity resolution might find an active artifact
- Context selection will then report `resolved_artifact`
- Both are observational and additive

### Contamination metadata

`_contamination_metadata` describes the contamination state of a resolved artifact. It is separate from context selection and boundary hints.

Possible confusion: contamination detection uses some of the same keywords (module, tool, etc.) to classify contamination sources. This is an internal classification for safety purposes — it is **not** the same as `_boundary_hints`, which describes the user's message content.

These two can overlap in a single turn without conflict. They serve different purposes.

### Lineage inspection

`_lineage_inspection` describes the artifact lineage chain when an artifact was resolved. It is orthogonal to context selection.

Context: "resolved_artifact" tells you the turn is artifact-governed.  
Lineage: tells you where that artifact came from and what it references.

They can both be present in the same response without conflict.

### Advisory surfaces

These signals may be surfaced to operators on debug/advisory surfaces. They are not strong-user-facing by default (see SECTION 6).

They do not carry truth classification or quality scores — those are handled by `_truth_guard` and `_quality_class` separately.

---

## SECTION 5 — FORBIDDEN DRIFT

The following are explicitly forbidden without a separate reviewed canon:

1. **Reintroducing product-name-coupled categories**  
   `"weslr_core"`, `"openclaw"`, `"infinity"`, or any equivalent bucket labels in context signals. These conflict with the generic structural model and will be detected and removed.

2. **Using these signals to alter routing automatically**  
   A signal value must not cause the system to select a different response path. Routing decisions are made by the routing layer, not by these signals.

3. **Turning them into governance triggers**  
   Neither signal may trigger, enable, or disable governance checks. Governance operates independently.

4. **Treating them as certainty rather than observation**  
   The values are observational descriptions — not guarantees. A `new_topic` classification is a best-effort structural observation; it does not mean the topic is definitely new.

5. **Mixing them with authority language**  
   In documentation and code, these signals are described as "observational", "descriptive", "advisory only". They are never described as "required", "authoritative", "binding", or "decisive".

---

## SECTION 6 — SAFE EXPOSURE

### Where these signals may appear safely

- **Runtime metadata** — attached to response dicts in `dialogue.py` return values
- **Operator/debug surfaces** — explicit debug views, log inspection tools
- **Future advisory inspection** — internal monitoring dashboards, session introspection
- **API response metadata** — if API is extended to expose runtime metadata

### Where these signals should NOT appear by default

- **Strong user-facing warning language** — these are structural metadata, not alerts
- **Execution control surfaces** — they must not appear in paths that gate actions
- **External-facing documentation** — unless the audience is technical/operator

If a future feature needs to surface these in a user-facing context, it requires a separate review.

---

## SECTION 7 — FUTURE EXTENSION BOUNDARY

### Allowed future expansion (no separate canon required)

- **Improved heuristics** for `_compute_context_selection` — more accurate classification within the existing value set
- **Broader generic category coverage** for `_boundary_hints` — adding to the existing keyword list if new structural types emerge
- **Better operator surfacing** — exposing the signals more clearly in debug/operator interfaces
- **Documentation refinement** — clarifying edge cases, adding examples

### Not allowed without separate canon

- **Behavioral use** — any logic that makes a decision based on these signal values
- **Policy coupling** — linking these signals to governance policies, approval thresholds, or scoring
- **Auto-suppression or auto-selection logic** — using these signals to automatically suppress or select response paths
- **Extending the value set** of either signal without a reviewed proposal

For any of the above: propose a separate canon document, get review, then implement.

---

## SECTION 8 — STOP LINE

- **Documentation only** — no code changes made
- **No behavior changes** — this document describes existing state
- **No design changes** — future changes require separate canon

**Signals current as of:** 2026-04-23  
**Validated against:** `dialogue.py` `_compute_context_selection()` / `_compute_boundary_hints()`  
**Legacy removed:** `_classify_context()` / `CONTEXT_KEYWORDS` (product-name-coupled classifier)