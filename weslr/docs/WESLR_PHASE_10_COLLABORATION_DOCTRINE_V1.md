# WESLR Phase 10 — Collaboration Doctrine V1
> Purpose: Enable multiple users to work within isolated tenants while optionally sharing hypotheses in a controlled "library" space. Provide a Jupyter kernel stub so WESLR can be used from notebooks. Generate human-readable explanations of hypotheses and reasoning steps using templates.

---

## Components

### 1. Workspace Manager (per-tenant)
- Each tenant has private hypotheses (via existing `HypothesisRepository` with tenant isolation)
- `share_hypothesis(hypothesis_id, shareable=True)` — marks hypothesis as shareable, strips user-specific metadata, returns anonymized copy
- `list_shared_library()` — returns all shareable hypotheses from all tenants (shareable=True, anonymized)
- `import_from_library(shared_hypothesis_id)` — copy a shared hypothesis into current tenant's repository with provenance "imported from library"
- **Storage:** in-memory `SHARED_HYPOTHESES` dict keyed by `shared_hypothesis_id`
- **Anonymization:** strips `created_by`, `tenant_id`, free-text user comments; keeps scientific content (title, description, confidence, domain, effect_size, causal_graph)

### 2. Jupyter Kernel Stub
- `weslr/jupyter_kernel_stub.py` — `run_in_notebook(command_string)` function
- Accepts Weslr commands (e.g., `/explore ...`) via CLI dispatcher
- Returns `{"output": str, "error": str|None, "images": list}`
- `/jupyter info` command prints connection instructions
- Phase 10: stub only, no full Jupyter messaging protocol

### 3. Explanation Generator (template-based, no LLM)
- `weslr/modules/explanation_generator.py`
- `explain_hypothesis(hypothesis_id, format='text')` — human-readable paragraph
- `explain_causal_link(cause, effect, confidence)` — explain a causal edge
- `explain_abduction(observation, explanation)` — format abduction results
- Templates use f-strings with conditionals; no external libraries
- All deterministic

---

## Constraints

1. **No LLM or generative AI** — templates only, all outputs deterministic
2. **Shared library access logs** — not required for Phase 10
3. **No persistent storage across sessions** — all in-memory
4. **Cross-tenant isolation** — Tenant A cannot see Tenant B's private hypotheses, only shared ones
5. **Shared library contains only** — hypotheses explicitly marked `shareable=True` and stripped of user-specific identifiers
6. **Hypothesis shareable field** — `shareable=False` by default
7. **Anonymization rules** — remove `created_by`, `tenant_id`, free-text user comments; keep scientific content

---

## Commands

| Command | Action |
|---|---|
| `/workspace share <hypothesis_id>` | Mark hypothesis shareable, add to shared library |
| `/workspace library list` | List all public hypotheses from all tenants |
| `/workspace import <shared_hypothesis_id>` | Copy shared hypothesis into current tenant |
| `/jupyter info` | Print Jupyter stub connection instructions |
| `/explain hypothesis <id>` | Full narrative explanation of a hypothesis |
| `/explain cause <cause> <effect>` | Explain a causal edge |
| `/explain abduce <observation>` | Combine abduction results with explanation template |

---

## Architecture Notes

- Shared hypotheses stored in module-level `SHARED_HYPOTHESES` dict (in-memory, per-process)
- Each shared hypothesis has a `shared_id` (deterministic UUID v5 based on original hypothesis id + "shared" namespace)
- Import creates a new hypothesis in the tenant's repository with provenance "imported from library"
- Explanation generator uses f-string templates; no jinja2 or external templating libraries
- Jupyter stub calls into existing CLI dispatcher or Weslr CLI directly

---

## Files Created

1. `weslr/docs/WESLR_PHASE_10_COLLABORATION_DOCTRINE_V1.md` — this file
2. `weslr/modules/workspace.py` — WorkspaceManager + SHARED_HYPOTHESES
3. `weslr/modules/explanation_generator.py` — template-based explanation functions
4. `weslr/jupyter_kernel_stub.py` — run_in_notebook() stub
5. `weslr/commands/collaboration_commands.py` — command handlers
6. `weslr/tests/test_collaboration.py` — 20+ tests

## Integration Points

- `HypothesisRepository` gains optional `shareable=False` field
- Report generator can optionally call `explain_hypothesis()` for narrative sections
- Abductive reasoner can call `explain_abduction()` to format explanations

---

_Phase 10 — User & Collaboration Features. No generative AI. Deterministic only._