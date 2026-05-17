# WESLR Design: Routing Validator Safe Preflight Integration V1

**Date:** Mon 2026-05-18 00:25 GMT+2  
**Checkpoint:** `5880d1a` — validator report V2 reviewed clean  
**Layer:** `WESLR_CANON_ALIGNMENT` design only  
**Purpose:** Design how `prompt_set_routing_validator.py` integrates into the safe ChatResponder shadow preflight pipeline.

---

## 1. Integration Target

The routing validator plugs into the preflight chain **before** any callable construction or shadow execution.

### Current preflight entry point
```
real_chatresponder_shadow_call_helpers.py::evaluate_prompt_with_real_chatresponder_shadow_call_v1()
  → preflight_for_real_chatresponder_shadow_call_v1()
    → (existing family/blocker checks)
    → if preflight_allowed:
      → build_safe_injected_callable_v1()
      → execute_shadow_call()
```

### Future preflight entry point (this design)
```
evaluate_prompt_with_real_chatresponder_shadow_call_v1()
  → routing_validator_preflight_v1()   ← NEW: route prediction + alignment
    → validate_prompt_route_alignment_v1(prompt_item, config)
    → if safe_to_call and not blocked:
      → proceed to existing preflight
    → else:
      → return preflight-blocked observation
  → preflight_for_real_chatresponder_shadow_call_v1()
    → (existing family/blocker checks)
    → if preflight_allowed:
      → build_safe_injected_callable_v1()
      → execute_shadow_call()
```

**Key principle:** Routing validator is the **first gate** in the preflight chain. It prevents metadata/routing mismatches from ever reaching callable construction.

---

## 2. Preflight Sequence

Exact future order for every shadow call:

| Step | Action | Module | Notes |
|------|--------|--------|-------|
| A | Working-root guard | `scripts/weslr_assert_correct_repo.sh` | Abort if wrong repo/branch |
| B | Prompt-set item validation | `controlled_behavior_prompt_set.py` | Validate item structure |
| C | Routing validator prediction | `prompt_set_routing_validator.py` | Predict route class |
| D | Metadata/routing alignment check | `prompt_set_routing_validator.py` | Flag mismatches |
| E | Family/blocker validation | `real_chatresponder_shadow_call_helpers.py` | Blocked families blocked |
| F | Mock requirement check | `prompt_set_routing_validator.py` + config | Mock must be active if required |
| G | Blocker contract validation | `real_chatresponder_shadow_call_helpers.py` | Contract must pass |
| H | Only then: callable construction | `real_chatresponder_shadow_call_helpers.py` | `build_safe_injected_callable_v1()` |

**Critical rule:** Steps C–F must all pass before H is reached. Any failure produces a blocked observation without callable construction.

---

## 3. Allow / Block Rules

### Allow without mock
A prompt may proceed without mock **only if all** are true:
- `alignment_status == "aligned"` or `"blocked_by_boundary"` is not the status
- `safe_to_call == True`
- `requires_mock == False`
- `route_class` is one of:
  - `safe_keyword_branch`
  - `safe_limited_ordinary_task`
  - `safe_frontier_shadow_metadata`
  - `safe_plan_helper_feature_flag_required` (with feature flag enabled)
- Family is in `ALLOWED_FIRST_CALL_FAMILIES_V1`
- No metadata mismatch flagged
- Blocker contract passes

### Allow with mock
A prompt may proceed with mock **only if all** are true:
- `alignment_status == "aligned"` or `"blocked_by_boundary"` is not the status
- `safe_to_call == True`
- `requires_mock == True`
- `route_class == "requires_generate_chat_mock"`
- Mock is explicitly active: `config["generate_chat_mock_active"] == True`
- Family is in `ALLOWED_FIRST_CALL_FAMILIES_V1`
- Blocker contract passes

### Block unconditionally
A prompt is blocked **if any** are true:
- `alignment_status == "mismatch"`
- `safe_to_call == False`
- Family is in `BLOCKED_REFINEMENT_FAMILIES_V1` or `BLOCKED_FAMILIES_V1`
- `route_class == "forbidden_model_path"`
- `route_class == "forbidden_search_or_advisor_path"`
- `route_class == "ambiguous_needs_review"`
- `requires_mock == True` but mock is not active
- Route requires feature flag without explicit isolation design
- Blocker contract fails

---

## 4. Known Failure Case Handling

### ordinary_task_behavior_003
**Text:** `"Help me write a short polite message asking for more information."`**Metadata:** `requires_model_call=False`, `safety_class=safe_synthetic`, `family=ordinary_task_behavior`

#### Without mock:
1. `predict_chat_responder_route_v1()` → `forbidden_model_path`
2. `validate_prompt_route_alignment_v1()` → `alignment_status="mismatch"`
3. `safe_to_call = False`
4. **Result:** BLOCKED before callable construction
5. **Reason labels:** `no_safe_path_and_mock_not_active`, `metadata_requires_model_call_false_but_forbidden_path`, `safe_synthetic_class_but_unsafe_route`

#### With mock active:
1. `predict_chat_responder_route_v1()` → `requires_generate_chat_mock`
2. `validate_prompt_route_alignment_v1()` → `alignment_status="aligned"`
3. `safe_to_call = True`, `requires_mock = True`
4. Mock active check passes
5. **Result:** ALLOWED, callable may be constructed
6. **Reason labels:** `mock_intercept_authorized`

**Anti-drift rule:** `ordinary_task_behavior_003` must NEVER silently fall through to live `generate_chat()`. The only allowed paths are blocked (no mock) or mock-intercepted (mock active).

---

## 5. Data Shape: Safe Preflight Result

The routing validator preflight should produce a metadata-only result:

```python
{
    "preflight_type": "weslr_routing_validator_preflight_v1",
    "prompt_id": str,
    "family": str,
    "route_class": str,  # one of 8 route classes
    "alignment_status": str,  # aligned | mismatch | blocked_by_boundary | needs_review
    "safe_to_call": bool,
    "requires_mock": bool,
    "mock_authorized": bool,  # config["generate_chat_mock_active"] is True
    "blocked_by_boundary": bool,
    "reason_labels": list[str],
    "matched_terms": list[str],
    "routing_validator_applied": True,
    "raw_text_retained": False,
    "model_calls": False,
    "search_calls": False,
    "advisor_calls": False,
    "writes": False,
    # No raw prompt text
    # No response text
    # No hidden prompts
    # No answer keys
}
```

---

## 6. Report / Audit Metadata

Future integration should embed these fields in every shadow-call observation:

```python
{
    "routing_validator_applied": True,
    "route_class": "requires_generate_chat_mock",
    "alignment_status": "aligned",
    "safe_to_call": True,
    "requires_mock": True,
    "blocker_contract_valid": True,
    "mock_active": True,
    "raw_text_retained": False,
}
```

This allows downstream review to verify that the routing validator was applied and what its decision was.

---

## 7. Tests for Future Implementation

Tests to add in `weslr/tests/test_routing_validator_safe_preflight_integration_v1.py`:

| Test | Expected |
|------|----------|
| `ordinary_task_behavior_003` blocked without mock | `safe_to_call=False`, `alignment_status="mismatch"`, callable NOT constructed |
| `ordinary_task_behavior_003` allowed with mock | `safe_to_call=True`, `requires_mock=True`, callable constructed |
| Blocked family blocked even with mock | `memory_honesty` family → blocked, `safe_to_call=False` regardless of mock |
| Search/currentness prompt blocked | `forbidden_search_or_advisor_path` → blocked without mock, blocked with mock |
| Keyword prompt allowed without mock | `safe_keyword_branch` → `safe_to_call=True`, `requires_mock=False` |
| Mismatch prompts blocked without mock | `metadata_requires_model_call_false_but_forbidden_path` → blocked |
| No raw prompt text in preflight result | `raw_text`, `raw_prompt`, `response_text` absent |
| No ChatResponder/respond_chat/generate_chat import in test file | Source inspection pass |
| Existing safe non-model harness tests pass | `test_safe_non_model_chatresponder_harness_v1.py` passes |
| Release gate / check pass | `release_gate_v1.py` and `weslr_release_check.sh` pass |

---

## 8. Files Proposed for Implementation

| File | Action |
|------|--------|
| `weslr/real_chatresponder_shadow_call_helpers.py` | Add `routing_validator_preflight_v1()` call at start of `evaluate_prompt_with_real_chatresponder_shadow_call_v1()` |
| `weslr/tests/test_routing_validator_safe_preflight_integration_v1.py` | New test file covering integration tests |
| `weslr/prompt_set_routing_validator.py` | No changes needed — existing API is sufficient |

**No new module required** unless integration complexity grows beyond what `real_chatresponder_shadow_call_helpers.py` can hold.

---

## 9. Anti-Drift Rules

1. **Preflight only:** Integration adds preflight gates, not final response logic.
2. **No family broadening:** Blocked families remain blocked. No exceptions.
3. **No live model calls:** `forbidden_model_path` and `forbidden_search_or_advisor_path` remain blocked.
4. **No default feature flags:** `safe_plan_helper_feature_flag_required` requires explicit flag.
5. **No chat_responder.py edits:** Runtime behavior of chat responder is unchanged.
6. **No broad WESLR readiness claims:** Integration is a preflight safety layer, not a readiness signal.
7. **No raw text retention:** Preflight results must never contain raw prompts or responses.
8. **No official test claims:** Validator reports are internal alignment tools, not certification.

---

## 10. Recommended Next Lane

**`IMPLEMENT_ROUTING_VALIDATOR_SAFE_PREFLIGHT_INTEGRATION_V1`**

Implement the integration design in:
- `weslr/real_chatresponder_shadow_call_helpers.py`
- `weslr/tests/test_routing_validator_safe_preflight_integration_v1.py`

Follow the exact preflight sequence and allow/block rules from this design.

---

## Safety Confirmation

- Design only — no implementation.
- No ChatResponder/respond_chat/generate_chat calls.
- No live model/search/advisor calls.
- No `.weslr` writes.
- No raw prompt/response storage.
- No official claims.
- No `.openclaw/workspace` edits.
