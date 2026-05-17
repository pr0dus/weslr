# WESLR Design: Prompt Set Routing Validator V1

**Work packet:** WESLR_WORK_PACKET_V1  
**Task:** DESIGN_PROMPT_SET_ROUTING_VALIDATOR_V1  
**Checkpoint:** 1a28f11 — safe non-model ChatResponder shadow retry reviewed  
**Date:** 2026-05-17 23:27 GMT+2  
**Operator:** pr0dus  
**Role:** Prompt Set Routing Validator Designer  
**Layer:** WESLR_CANON_ALIGNMENT design only  
**Live behavior changed:** No  
**Classification:** `design_only` — no implementation, no calls, no commits  

---

## SECTION 1 — STATUS

| Property | Value |
|----------|-------|
| Design authorized | Yes |
| Correct repo | ✅ `~/weslr-pr47-clean`, `master`, `1a28f11` |
| No ChatResponder calls | ✅ Confirmed |
| No prompt execution | ✅ Confirmed |
| No source edits | ✅ Confirmed |
| No commits | ✅ Confirmed (report-only, untracked doc) |
| Release gate | ✅ PASS |
| Release check | ✅ PASS |

---

## SECTION 2 — CONTEXT / ROOT PROBLEM

### The Mismatch

`controlled_behavior_prompt_set.py` builds prompts with metadata flags like `requires_model_call=False`. But `chat_responder.py` routing is purely keyword-driven and classifier-driven — it does not read this metadata.

**Example failure (proven at 801a634 / 1a28f11):**
- `ordinary_task_behavior_003` text: `"Help me write a short polite message asking for more information."`
- Metadata: `requires_model_call=False`, `requires_search=False`, `requires_memory_write=False`
- `respond_chat()` routing:
  - No keyword match (no "lunch", "workout", "plan", "email", "wife", "code")
  - Limited ordinary-task classifier rejects it — no planning terms like "plan", "steps", "checklist"
  - Plan-helper demotion does not fire (no plan-helper trigger)
  - Meaning-vector imports fail or don't fire
  - Falls through to `_model_chat_response()` → `generate_chat()` → **FORBIDDEN PATH ENTERED**

**Consequence:** The safe non-model harness correctly intercepted the call with a mock, but the routing mismatch means:
- The prompt metadata was misleading
- The prompt would have entered a live model path if the harness had not been active
- Future prompts added to the set could repeat this pattern silently

### Why This Matters

Without a routing validator:
- We cannot detect metadata/routing mismatches before any ChatResponder call
- Prompt-set designers may add prompts with `requires_model_call=False` that actually require the model path
- Any future call risks entering the model path unless mock is active
- The classification label (`keyword_branch_only` vs `safe_mocked_model_path_observed`) cannot be trusted without route simulation

---

## SECTION 3 — DESIGN SUMMARY

### 3.1 Routing Simulation Goal

Given prompt text + metadata, predict the likely `respond_chat()` route **without calling `respond_chat()`**.

**Route classifications:**

| Classification | Meaning | Safe? |
|----------------|---------|-------|
| `safe_keyword_branch` | Matches a deterministic keyword branch (lunch, workout, email, plan, wife/partner, code/bug) | ✅ Yes |
| `safe_limited_ordinary_task` | Matches `_classify_limited_ordinary_task_request()` with `eligible=True` | ✅ Yes |
| `safe_frontier_shadow_metadata` | Matches `_try_limited_frontier_runtime_response()` | ✅ Yes |
| `safe_plan_helper_feature_flag_required` | Matches `_is_plan_helper_live_demotion_early_candidate_v1()` but requires `WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1` env flag | ⚠️ Yes only with explicit feature flag |
| `requires_generate_chat_mock` | No deterministic safe path matches; would fall through to `_model_chat_response()` → `generate_chat()` | ⚠️ Safe only if mock is active |
| `forbidden_model_path` | Predicted to reach `_model_chat_response()` with no mock active | ❌ Block |
| `forbidden_search_or_advisor_path` | Predicted to reach search, advisor, currentness, or source path | ❌ Block |
| `ambiguous_needs_review` | Cannot determine route from prompt text alone | ⚠️ Needs explicit approval |

### 3.2 Metadata Mismatch Detection

Detect these specific mismatches:

| Mismatch | Detection Logic |
|----------|----------------|
| `requires_model_call=False` but predicted route is `forbidden_model_path` | Simulate routing; if result is `forbidden_model_path`, flag mismatch |
| `requires_search=False` but prompt implies currentness/search/source | Check for "current", "latest", "source", "look up" terms in prompt text |
| `allowed family` but `blocked route` | Family may be allowed but route simulation shows blocked path |
| `safe_synthetic` class but route requires mock | `safe_synthetic` should not require mock; flag if it does |
| Prompt text does not match known deterministic safe branches | If no keyword match and no ordinary-task classifier match, flag |

### 3.3 Safe Path Inventory

**Current safe non-model paths in `chat_responder.py`:**

1. **Keyword branches** (lines ~1962–2012 in `respond_chat`):
   - "lunch" → deterministic lunch response
   - "workout"/"gym"/"run"/"exercise" → deterministic workout response
   - "plan" → deterministic plan response (with email/workout context)
   - "email" → deterministic email response
   - "wife"/"partner" → deterministic relationship response
   - "code"/"bug" → deterministic code response

2. **Limited ordinary-task runtime** (lines ~1192–1400):
   - `_classify_limited_ordinary_task_request()` classifies
   - Requires planning terms: "plan", "steps", "step plan", "rollout", "checklist", "break down", "debug", "organize", "migration", "deployment", "deploy", "staged change", "server change"
   - Rejects: "official iq", "certification", "medical", "legal", "financial", "diagnose", "prescription", "lawsuit", "investment", "remember me", "write a story", "poem", "creative writing"
   - Rejects currentness terms unless benign lunch exclusion

3. **Frontier shadow metadata** (lines ~1453–1600):
   - `_try_limited_frontier_runtime_response()`
   - Handles frontier-specific terms

4. **Plan-helper live demotion** (lines ~74–120, ~1970–1985):
   - `_is_plan_helper_live_demotion_early_candidate_v1()`
   - Requires explicit env flag `WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1`
   - Without flag, does not fire

5. **Mocked `generate_chat` path** (only with harness):
   - `install_generate_chat_mock()` intercepts `generate_chat()`
   - `_model_chat_response()` calls `generate_chat()` → mock returns safe deterministic response
   - No live model call occurs
   - This is the **fallback safe path**, not a deterministic safe path

**Not safe (blocked):**
- Any path reaching `_model_chat_response()` without mock active
- Any path reaching `analyze_meaning()` / `determine_response_obligation()` meaning-vector imports
- Any path with `record_inadequacy_event()` → JSONL write
- Any search/advisor/currentness/source path

---

## SECTION 4 — PROPOSED API

### 4.1 Core Functions

```python
def predict_chat_responder_route_v1(
    prompt_text: str,
    *,
    metadata: Optional[dict[str, Any]] = None,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Simulate respond_chat routing for a prompt without calling it.

    Returns a route prediction dict with:
    - route_classification: one of the 8 classifications above
    - reason: human-readable explanation
    - keyword_matched: which keyword matched (if any)
    - ordinary_task_eligible: bool
    - ordinary_task_decision: str (if eligible)
    - requires_mock: bool
    - is_safe_without_mock: bool
    - blocked_families: list[str]
    - metadata_mismatches: list[str]
    """


def validate_prompt_route_alignment_v1(
    prompt_item: dict[str, Any],
    *,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Validate a single controlled prompt item against routing reality.

    Takes a prompt dict (from controlled_behavior_prompt_set) and:
    1. Simulates routing via predict_chat_responder_route_v1()
    2. Checks metadata consistency (requires_model_call, requires_search, etc.)
    3. Returns validation result with pass/block/mismatch status
    """


def summarize_prompt_route_alignment_v1(
    prompt_set: dict[str, Any],
    *,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Validate an entire prompt set and produce summary statistics.

    Returns:
    - total_prompts: int
    - safe_without_mock: int
    - requires_mock: int
    - blocked: int
    - ambiguous: int
    - metadata_mismatches: list[dict]
    - recommended_actions: list[str]
    """


def render_prompt_route_alignment_markdown_v1(
    summary: dict[str, Any],
    *,
    title: str = "Prompt Set Route Alignment Report",
) -> str:
    """Render a human-readable markdown report from summary."""
```

### 4.2 Route Classification Decision Tree

```
predict_chat_responder_route_v1(prompt_text):
  1. Empty text? → ambiguous_needs_review (reason: empty_message)
  2. Check blocked terms ("official iq", "certification", "medical", ...)
     → forbidden_model_path (reason: outside_safe_ordinary_scope)
  3. Check search/advisor/currentness terms
     → forbidden_search_or_advisor_path (reason: search_path_detected)
  4. Check keyword matches:
     - "lunch" → safe_keyword_branch
     - "workout"/"gym"/"run"/"exercise" → safe_keyword_branch
     - "plan" → safe_keyword_branch
     - "email" → safe_keyword_branch
     - "wife"/"partner" → safe_keyword_branch
     - "code"/"bug" → safe_keyword_branch
  5. Check limited ordinary-task classifier:
     - planning terms present + not too vague + no blocked terms
       → safe_limited_ordinary_task
  6. Check frontier shadow metadata:
     → safe_frontier_shadow_metadata
  7. Check plan-helper demotion (requires env flag):
     → safe_plan_helper_feature_flag_required
  8. No safe path matched:
     → requires_generate_chat_mock (safe only with mock active)
     → if no mock active: forbidden_model_path
```

---

## SECTION 5 — TEST PLAN

### Unit Tests (proposed file: `weslr/tests/test_prompt_set_routing_validator_v1.py`)

| # | Test | Expected |
|---|------|----------|
| 1 | `test_ordinary_task_behavior_003_predicts_requires_mock()` | `predict_chat_responder_route_v1()` returns `requires_generate_chat_mock` |
| 2 | `test_ordinary_task_behavior_003_blocks_without_mock()` | `validate_prompt_route_alignment_v1()` returns `block` when mock not configured |
| 3 | `test_ordinary_task_behavior_003_allows_with_mock()` | `validate_prompt_route_alignment_v1()` returns `pass` when mock active |
| 4 | `test_lunch_prompt_predicts_safe_keyword_branch()` | "What should I eat for lunch?" → `safe_keyword_branch` |
| 5 | `test_workout_prompt_predicts_safe_keyword_branch()` | "I want to workout later" → `safe_keyword_branch` |
| 6 | `test_planning_prompt_predicts_safe_limited_ordinary_task()` | "Plan a migration to the new server" → `safe_limited_ordinary_task` |
| 7 | `test_metadata_mismatch_detected()` | `requires_model_call=False` but route is `requires_generate_chat_mock` → mismatch flagged |
| 8 | `test_blocked_families_remain_blocked()` | "official iq" → `forbidden_model_path` |
| 9 | `test_search_terms_detected()` | "look up the latest news" → `forbidden_search_or_advisor_path` |
| 10 | `test_empty_prompt_ambiguous()` | "" → `ambiguous_needs_review` |
| 11 | `test_no_chatresponder_calls_in_validator()` | Validator never imports or calls `ChatResponder` |
| 12 | `test_no_raw_prompt_response_storage()` | Validator never stores raw text |

### Integration Tests

| # | Test | Expected |
|---|------|----------|
| 13 | `test_full_prompt_set_summary()` | `summarize_prompt_route_alignment_v1()` counts safe/mock/blocked/ambiguous correctly |
| 14 | `test_markdown_report_render()` | `render_prompt_route_alignment_markdown_v1()` produces valid markdown |

---

## SECTION 6 — VALIDATION RUN

| Gate | Result |
|------|--------|
| `python3 weslr/tests/release_gate_v1.py` | ✅ PASS |
| `bash scripts/weslr_release_check.sh` | ✅ PASS |

---

## SECTION 7 — SAFETY CONFIRMATION

| Safety Check | Result |
|--------------|--------|
| No ChatResponder calls | ✅ Confirmed |
| No prompt execution | ✅ Confirmed |
| No model/search/advisor calls | ✅ Confirmed |
| No source edits | ✅ Confirmed |
| No commits | ✅ Confirmed |
| No `.weslr` writes | ✅ Confirmed |
| No raw prompt/response storage | ✅ Confirmed |
| No official claims | ✅ Confirmed |
| No work in `.openclaw/workspace` | ✅ Confirmed |

---

## SECTION 8 — COMMIT

**No commit.** Design only.

**Untracked doc created:** `docs/WESLR_DESIGN_PROMPT_SET_ROUTING_VALIDATOR_V1.md`

---

## SECTION 9 — NEXT STEP

**Recommended next lane:** `AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_PROMPT_SET_ROUTING_VALIDATOR_DESIGN_V1`

**Awaiting operator approval for:** `IMPLEMENT_PROMPT_SET_ROUTING_VALIDATOR_V1`

Implementation would touch:
- `weslr/prompt_set_routing_validator.py` (new, ~200 lines)
- `weslr/tests/test_prompt_set_routing_validator_v1.py` (new, ~300 lines)

Blocked until design is reviewed and approved.

---

*Design produced by OCC per WESLR_WORK_PACKET_V1. No implementation. No autonomous execution. No self-authorization.*
