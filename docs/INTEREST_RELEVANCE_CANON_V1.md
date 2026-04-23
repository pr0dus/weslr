# Interest Tracker + Relevance Surface — Canonical Architecture v1

> Status: **SEALED** — Interest Tracker / Relevance chapter complete as of 2026-04-20
> This document is authoritative. It is not a design document. It is the architectural contract.

---

## SECTION 1 — PURPOSE

This layer exists to:

- track recurring domains of significance as explicit **interests**
- attach bounded evidence via **occurrences**
- provide **read-only relevance scoring** against any given context
- surface relevance as **metadata only**, never as behavior
- reduce dependence on LLM context by externalizing theme continuity

**What this layer is NOT:**

- NOT a reasoning engine — scoring is structural, not inferential
- NOT a decision system — relevance output never decides anything
- NOT a routing authority — it does not change which handler is called
- NOT a learning system — interests are created explicitly, not derived autonomously
- NOT a context container — it reduces context dependence, not replaces it

---

## SECTION 2 — CORE CONCEPTS

### Interest

An interest is a named, operator-tracked domain of significance.

- **Definition:** A structured record representing a theme the operator considers worth tracking
- **Creation:** Explicit only — via CLI (`interest create`) or direct `interest_tracker.create_interest()` call
- **Lifecycle:** Owned by the operator; never auto-created, never auto-pruned by relevance logic
- **State:** Stored in `weslr/interests.json`; mutable only via explicit write functions

### Occurrence

An occurrence is a bounded evidence link between an interest and a triggering item.

- **Definition:** A record of one instance where a tracked interest was relevant to something
- **Creation:** Manual only — via CLI (`interest add-occurrence`) or direct `interest_tracker.add_occurrence()` call
- **Limits:** Max 20 per interest; oldest entries pruned on write
- **Fields:** type (artifact|question|proposal), item_id, triggered_at, reason

### Relevance Surface

The relevance surface is a read-only query interface over the interest registry.

- **Definition:** A function that scores and ranks interests against a given context
- **Behavior:** Additive only — scores interests, never modifies them
- **Output:** Ranked list of scored interests with explainable match reasons
- **Constraints:** Advisory metadata only; never changes behavior of any system

### Integration Point

An integration point is a bounded, explicit attachment of relevance metadata into an existing response surface.

- **Definition:** A specific location in existing code where `_relevant_interests` is attached to a response
- **Current:** `sim.explain_item()` artifact branch — the only integration point as of v1
- **Rule:** Every integration point must be listed in this document before it is created

---

## SECTION 3 — SOURCE OF TRUTH

### Authoritative Files

| File | Role | Authority |
|------|------|-----------|
| `weslr/interests.json` | State truth | Single source of truth for all interest data |
| `weslr/interest_tracker.py` | Write authority | Only module authorized to write to interests.json |
| `weslr/relevance_surface.py` | Read-only scoring | Only module authorized to score interests |
| `sim.py` (explain_item) | Current integration | Only place `_relevant_interests` is currently attached |

### Explicit rules

- **No other module may write to `interests.json`** — direct file writes to interests.json are forbidden
- **No other module may create interests** except via `interest_tracker.create_interest()`
- **No other module may create occurrences** except via `interest_tracker.add_occurrence()`
- **No other module may call `interests.json` directly** for write operations
- **Only `relevance_surface.py` may score interests** — scoring logic must not be duplicated

---

## SECTION 4 — DATA MODEL CONTRACT

### interests.json Schema

```json
{
  "interests": [
    {
      "id": "string (8 hex chars, uuid[:8])",
      "name": "string (normalized: lowercase, underscores, no spaces)",
      "display_name": "string (human-friendly, spaces allowed)",
      "status": "string (currently only 'active' is meaningful; 'archived' reserved for future)",
      "created_at": "string (ISO 8601 UTC: YYYY-MM-DDTHH:MM:SSZ)",
      "last_seen_at": "string (ISO 8601 UTC, updated on each add_occurrence call)",
      "occurrence_count": "integer (0..∞, capped by occurrences array length in practice)",
      "tags": "list of string (normalized lowercase, sorted, no duplicates)",
      "occurrences": [
        {
          "type": "string (one of: artifact | question | proposal)",
          "item_id": "string (identifier of the triggering item)",
          "triggered_at": "string (ISO 8601 UTC)",
          "reason": "string (human-readable description of why this occurrence was recorded)"
        }
      ]
    }
  ]
}
```

### Bounds

| Constraint | Value | Enforced by |
|------------|-------|--------------|
| Max interests | 50 | `interest_tracker.create_interest()` raises if cap exceeded |
| Max occurrences per interest | 20 | `interest_tracker.add_occurrence()` prunes oldest on write |
| Interest id length | 8 chars | `uuid.uuid4()[:8]` — not configurable |
| Normalized name | lowercase + underscores | `normalize_name()` — applied on every create |

### Field immutability expectations

- `id`: never modified after creation
- `created_at`: never modified after creation
- `name`: never modified after creation (enforced by duplicate check)
- `display_name`: may be updated via future explicit function (not yet implemented)
- `status`: may be changed via future explicit function (not yet implemented)
- `occurrences`: append-only within each interest; oldest pruned at 20

---

## SECTION 5 — WRITE RULES

### Allowed writes

| Operation | Method | Notes |
|-----------|--------|-------|
| Create interest | `interest_tracker.create_interest(name, tags)` | CLI: `interest create <name> [tags]` |
| Add occurrence | `interest_tracker.add_occurrence(interest_id, type, item_id, reason)` | CLI: `interest add-occurrence <id> <type> <item_id> [reason]` |
| Prune stale | `interest_tracker.prune_stale(max_open)` | CLI: `interest prune [max]` (manages cap, not occurrences) |

### Explicitly forbidden

- ❌ Automatic interest creation based on artifact content or frequency analysis
- ❌ Automatic occurrence creation from any background scan
- ❌ Inference-based write operations against interests.json
- ❌ Direct file writes to interests.json from any module except interest_tracker
- ❌ Background scanning of artifacts or questions to derive interests
- ❌ Scheduled or event-driven interest creation without operator command
- ❌ Unbounded occurrence accumulation (enforced at 20 per interest)

---

## SECTION 6 — READ / INTEGRATION RULES

### Allowed reads

| Operation | Method | Notes |
|-----------|--------|-------|
| List interests | `interest_tracker.list_interests(status, tag)` | CLI: `interest list` |
| Get single interest | `interest_tracker.get_interest(id_or_name)` | CLI: `interest show <id>` |
| Score interests | `relevance_surface.query_relevant_interests(text, tags, top_n, status)` | CLI: `python -m weslr.relevance_surface --text X --tags Y` |

### Current allowed integration point

| Location | File | Function | Attached as | Behavior change |
|----------|------|----------|------------|-----------------|
| Artifact explanation | `sim.py` | `explain_item()` | `_relevant_interests` | Metadata only — no behavior change |

**Rule:** `_relevant_interests` must be a list (JSON array) attached as a top-level field in the response dict. It must not be nested inside other fields or used as a conditional.

### Explicitly forbidden integration behaviors

- ❌ Attaching `_relevant_interests` to chat main door responses (not yet approved)
- ❌ Using relevance score as a condition in any routing decision
- ❌ Modifying response content, ranking, or wording based on relevance output
- ❌ Injecting relevance results into LLM prompt construction
- ❌ Storing relevance outputs in artifact or question registry
- ❌ Creating new integration points without explicit canonicalization doc update

---

## SECTION 7 — RELEVANCE CONTRACT

### What relevance output IS

- A **ranked list** of scored interests with **explainable match reasons**
- Advisory **metadata** that describes what is relevant, not what must be done
- **Deterministic** and **inspectable** — every score can be traced to a specific match reason
- **Read-only** — never modifies any state

### What relevance output IS NOT

Relevance output must NEVER influence:
- **decisions** — no relevance score may gate, trigger, or override any decision
- **routing** — no relevance score may change which handler or function is called
- **wording** — no relevance score may alter any user-facing message or response
- **confidence scoring** — no relevance score may modify internal_score or any confidence metric
- **governance outcomes** — no relevance score may affect proposal acceptance, artifact approval, or any governance signal

### Score explainability requirement

Every scored interest in a relevance result must include `match_reasons` — a list of human-readable strings describing why that interest scored. Examples:
- `"matched tag: governance"`
- `"query text matched display_name"`
- `"recent activity within 48 hours"`
- `"occurrence_count bonus: 1.0"`

If a relevance result does not include `match_reasons`, it is non-compliant with this canon.

---

## SECTION 8 — FORBIDDEN DRIFT

The following future changes are **forbidden** without explicit update to this document and operator approval:

| Forbidden change | Reason |
|-----------------|--------|
| Silent auto-creation of interests | Violates explicit creation requirement; creates hidden state |
| Silent auto-creation of occurrences | Violates manual occurrence requirement; creates unbounded evidence |
| Using relevance to influence decision logic | Violates advisory-only contract; introduces hidden authority |
| Using relevance to change ranking or order | Violates non-influence rule; introduces hidden prioritization |
| Hidden prioritization based on interests | Routing authority must remain explicit and inspectable |
| Automatic theme inference without governance | Theme discovery must be operator-controlled, not system-inferred |
| Expanding integration points without canon update | Each integration point must be defined and approved |
| Injecting relevance into prompt construction | Must remain external metadata, not contextual prompt input |
| Using relevance output as a gate | Relevance is advisory — never a condition |

---

## SECTION 9 — FUTURE EXTENSION RULES

The following are explicitly allowed as **future extension steps**, each requiring:
1. A written proposal
2. Operator review and approval
3. Explicit update to this document before implementation

### Allowed future steps (require approval)

| Extension | Description | Phase |
|----------|-------------|-------|
| Interest suggestion system | WESLR proposes new interests via governance proposal (not auto-created) | Future |
| Additional integration points | Attaching `_relevant_interests` to other explicit surfaces | Future |
| Thread tracking connection | Linking interests to conversation threads or timeline events | Future |
| Operator profile linkage | Associating interests with operator role or context | Future |

### Requirements for any extension

- Written proposal describing the purpose and bounded scope
- Explicit operator approval before implementation
- Update to this canonicalization document before code lands
- Tests verifying the extension does not violate write/read rules
- Reverted if extension violates any SECTION 8 forbidden drift rule

---

## SECTION 10 — STOP LINE

**Canonicalization pass — verified completed:**

- ✅ No code changes made in this pass
- ✅ Documentation only (this file)
- ✅ No behavior modifications introduced
- ✅ No schema changes to interests.json
- ✅ No new integration points added (Phase 3 integration remains the only one)
- ✅ All forbidden drift rules are documented and binding
- ✅ Interest Tracker / Relevance chapter is now sealed at v1

**Next authorized step:** Any of the allowed future extensions from SECTION 9, subject to the stated approval requirements. Nothing else is authorized without an explicit update to this document.

---

*This canon was produced at the conclusion of the Interest Tracker / Relevance chapter (2026-04-20) and is binding on all current and future implementations of interest tracking, relevance scoring, and metadata integration in WESLR.*