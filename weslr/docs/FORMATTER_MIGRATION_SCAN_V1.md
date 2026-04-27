# WESLR Formatter Migration Scan — V1

**Scan date:** 2026-04-27
**Commits inspected:** `50c1a69`, `0834cb3`, `7998f44`, `8056fa7`

---

## SECTION 1 — Scope

Files inspected:
- `interpretation.py` (1929 lines)
- `weslr/response_formatter.py` (41 lines)
- `weslr/deterministic_handlers.py` (118 lines)
- `weslr/docs/RESPONSE_CONTRACT_V1.md`
- `weslr/docs/POST_REGISTRY_EXTRACTION_SCAN_V1.md`

Migrations confirmed:
1. `ISS_probe_registry_query` → `build_deterministic_response` (commit `50c1a69`)
2. `ISS_probe_plan` → `build_deterministic_response` (commit `0834cb3`)
3. `ISS_query_all / ISS_query_gaps / ISS_query_probes` → `build_deterministic_response` (commit `7998f44`)
4. `operator_overview` → `build_deterministic_response` (commit `8056fa7`)

---

## SECTION 2 — Formatter Adoption Status

| Handler | Path | Uses formatter | Committed |
|---|---|---|---|
| ISS probe registry query | `ISS_probe_registry_query` | **Yes** | `50c1a69` |
| ISS probe planning | `ISS_probe_plan` | **Yes** | `0834cb3` |
| ISS diagnostics (all) | `ISS_query_all` | **Yes** | `7998f44` |
| ISS gaps query | `ISS_query_gaps` | **Yes** | `7998f44` |
| ISS probes query | `ISS_query_probes` | **Yes** | `7998f44` |
| Operator overview | `operator_overview` | **Yes** | `8056fa7` |
| All other handlers | — | **No** | — |

5 handler paths now use `build_deterministic_response`. The formatter's base contract (message, response_text, path, _weslr_deterministic, confidence, suggested_mode, payload) is applied consistently across migrated handlers.

---

## SECTION 3 — Remaining Inline Response Handlers

Still building response dicts directly (in `interpretation.py`):

```
_self_description_triggers  — who are you / what are you (base turn assessment)
_capability_list_triggers  — what can you do / capabilities (base turn assessment)
_capability_gaps_trigger  (line ~871) — how can you improve (uses `in` check, returns path=None)
_plan_triggers             (line ~1027) — plan query (C8)
_iss_intake_triggers       (line ~1510) — ISS intake query
_intake_triggers           (line ~1420) — accept gap / convert gap handlers
_plan_explain_triggers     (line ~1582) — plan explanation
_execute_triggers         (line ~1693) — probe execution (write, confirmation-gated)
_explain_triggers          (line ~1748) — proposal explanation
_ck_triggers              (line ~1843) — state checkpoint query
proposal explanation inline (line ~1838)
proposal approval/rejection inline (C6)
capability_proposal_ranked inline (C4/C5)
```

~12 handler groups remain inline. Count includes C4/C5/C6 write handlers which are not yet candidates for formatter migration.

---

## SECTION 4 — Field Consistency Check

**Migrated handlers — field presence:**

| Field | iss_probe_registry | iss_probe_plan | ISS_query_all/Gaps/Probes | operator_overview |
|---|---|---|---|---|
| `message` | ✓ | ✓ | ✓ | ✓ |
| `response_text` | ✓ | ✓ | ✓ | ✓ |
| `path` | ✓ | ✓ | ✓ | ✓ |
| `_weslr_deterministic` | ✓ | ✓ | ✓ | ✓ |
| `confidence` | ✓ (high) | ✓ (high) | ✓ (high) | ✓ (high) |
| `suggested_mode` | ✓ (observe) | ✓ (observe) | ✓ (observe) | ✓ (observe) |
| `payload` | ✓ (probe_registry, probe_count) | ✓ (probe_plan) | ✓ (diagnostics/gaps/probes) | ✓ (overview) |

All migrated handlers attach `mode_analysis`, `mode_suggestion`, `suggestion_surface` **manually after** the formatter call:
```python
result = build_deterministic_response(...)
result["mode_analysis"] = {...}
result["mode_suggestion"] = None
result["suggestion_surface"] = {...}
return result
```

This is consistent across all 3 ISS query branches and the operator overview. It works but requires the caller to remember to re-attach these fields. A future formatter version could accept these as optional parameters.

---

## SECTION 5 — Behavior Drift Check

Route verification:

| Input | Expected path | Result |
|---|---|---|
| `show iss probes` | ISS_probe_registry_query | **OK** |
| `plan probe probe.front_door.chat` | ISS_probe_plan | **OK** |
| `show diagnostics` | ISS_query_all | **OK** |
| `show gaps` | ISS_query_gaps | **OK** |
| `show probe results` | ISS_query_probes | **OK** |
| `show system overview` | operator_overview | **OK** |
| `weslr overview` | operator_overview | **OK** |
| `explain plan iss.not_integrated` | plan_explanation | **OK** |
| `how can you improve` | capability_gaps | **OK** (returns path=None but response_text correct — pre-existing) |
| `tell me about solar panels` | None | **OK** |

No behavior regressions introduced by migrations. `how can you improve` is pre-existing: handler uses `in` check rather than prefix match, builds response dict directly, returns `path=None` — this is the handler's own choice, not introduced by migration.

---

## SECTION 6 — Response Style Findings

**Migrated responses vs RESPONSE_CONTRACT_V1:**

| Check | Status |
|---|---|
| Lead with result, not process | **PASS** — all migrated responses state what was found first |
| Compact | **PASS** — no over-elaboration in migrated responses |
| No hype language | **PASS** — clinical, precise |
| No fake sentience | **PASS** — "ISS has N probes" not "I have N probes defined" |
| No unclear execution claims | **PASS** — all specify execution_allowed=False or simulated mode |

**Notable:** The `explain plan iss.not_integrated` response (`plan_explanation`) already follows the RESPONSE_CONTRACT_V1 template for planning responses: `"Plan '<plan_id>' exists because proposal '<proposal_id>' was created from ISS gap '<gap_id>' and later accepted by the operator."` — causal chain, compact, no narrative.

**operator_overview response_text** includes `"System is deterministic, non-executing, and operator-controlled."` — this is an explicit boundary statement, consistent with RESPONSE_CONTRACT_V1 tone. Compact, scannable.

---

## SECTION 7 — Remaining Risks

1. **~12 inline handlers still bypass formatter** — response construction is duplicated across ~12 handler groups. Adding a new field to the response skeleton requires touching each handler individually.

2. **`mode_analysis`/`mode_suggestion`/`suggestion_surface` re-attached manually** — after `build_deterministic_response` returns, the caller must re-attach these three fields. This is consistent but error-prone if a future handler forgets to re-attach them. Could be addressed by passing them as optional parameters to the formatter.

3. **`confidence` still overloaded** — all migrated handlers return `confidence: "high"`. Per RESPONSE_CONTRACT_V1, this conflates handler-match confidence with factual-read confidence. No migrated handler distinguishes these.

4. **`suggested_mode` over-simplified** — all migrated query handlers return `suggested_mode: "observe"`. For `explain plan` and proposal explanation, this may not be the right mode suggestion, but no handler sets it differently.

5. **Write handlers not migrated** — `ISS_probe_execution`, proposal creation/approval, and gap intake still build response dicts manually. These will require the formatter to support `requires_confirmation` and write-declaration fields before migration.

6. **`how can you improve` returns `path=None`** — the capability gaps handler builds its response dict directly without setting `path` (the path would be `capability_gaps`). This is pre-existing but inconsistent with the formatter pattern.

7. **`_B9_STATE` mutable module state** — `_B9_STATE = {"low_confidence_count": 0, "mismatch_count": 0}` is session-only mutable state in `interpretation.py`. Not migrated, not addressed by this scan.

---

## SECTION 8 — Recommended Next Step

**A) Migrate `state_checkpoint_query` to formatter**

Rationale: `state_checkpoint_query` is a read-only handler with a single return path (no branching), similar in complexity to `operator_overview`. It reads only from `get_state_checkpoint()` which returns a static dict. Migrating it would:
- Be low risk — identical structure to operator_overview migration
- Add a third non-ISS handler to the formatter (proves formatter is not ISS-specific)
- Keep the focus on formatter migration rather than adding registry complexity
- Produce a clean pattern before tackling handlers with branching logic

**Why not B (C8 plan query)?** Plan query (`_plan_triggers`) has multiple record types and conditional response_text ("N plans" vs "no plans"). Higher complexity — not the right next step.

**Why not C (schemas first)?** Schemas are documentation-only and block momentum. The formatter migration is working cleanly — continue until a blocker appears.

**Why not D (extract more handlers)?** The registry currently holds 2 ISS handlers. Extracting more before the formatter pattern is established for non-ISS handlers creates registry entries that can't benefit from the formatter pattern yet.

---

## SECTION 9 — Top 10 Findings

1. **5 handler paths migrated** to `build_deterministic_response`, all behavior-verified identical, all committed
2. **Field consistency verified** across all migrated handlers — message, response_text, path, _weslr_deterministic, confidence, suggested_mode, payload all present
3. **No behavior drift** — all 10 route inputs produce expected paths, no regressions
4. **`mode_analysis`/`suggestion_surface` re-attached post-build** — works correctly but not integrated into formatter call; inconsistent risk if new handlers forget to re-attach
5. **`how can you improve` pre-existing path=None** — capability gaps handler returns correct response_text but sets `path=None`; pre-existing, not introduced by migration
6. **~12 handler groups remain inline** — all C1–C6 inline, state checkpoint, proposal/plan explanation, probe execution, intake handlers
7. **`explain plan iss.not_integrated` already clean** — response follows RESPONSE_CONTRACT_V1 template exactly; good reference implementation
8. **`confidence` always "high"** — all migrated handlers return `confidence: "high"` without distinguishing handler-match vs factual-read confidence
9. **Write handlers not migratable yet** — `ISS_probe_execution`, C4/C5/C6 proposal handlers need formatter support for write fields before migration is safe
10. **`state_checkpoint_query` is the natural next target** — read-only, no branching, single return path, mirrors operator_overview migration exactly

---

## SECTION 10 — Verdict

**FORMATTER_MIGRATION_SCAN_CONFIRMED**

Four migrations cleanly applied, no regressions. Formatter now handles 5 ISS operator-facing paths. The remaining ~12 inline handlers need either formatter migration or registry extraction before `interpretation.py` can be considered architecturally improved. `state_checkpoint_query` is the recommended next target for formatter migration.

---

*Document version: 1.0*
*Scan status: canonical reference*
*Next step: migrate state_checkpoint_query to build_deterministic_response*
