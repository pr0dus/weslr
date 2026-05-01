# WESLR Implemented Reality Inventory V1

**Date:** 2026-05-01
**Purpose:** Factual inventory of what is implemented vs spec-only vs not implemented
**Method:** Direct code inspection, not documentation reliance

---

## A) IMPLEMENTED AND TESTED

### /chat Path
- **File:** `main.py` (ThreadingHTTPServer, ChatHandler)
- **Status:** LIVE — endpoint binds and responds with 200
- **Tests:** No dedicated unit test (tested via curl live)
- **Key:** `POST /chat` → `build_communicator_message_payload()` → response

### Interpretation
- **File:** `interpretation.py` (1078+ lines)
- **Status:** LIVE — `interpret_human_turn()` used by `/chat` and detector
- **Functions:** `interpret_human_turn()`, `classify_human_turn()`, `detect_intent()`
- **Tests:** Used by contract observation builder, no standalone test file found

### Public Signal Capture
- **File:** `weslr/website_signal_integration.py` (103 lines)
- **Status:** LIVE — `capture_website_signal()` wired as fire-and-forget in main.py
- **Functions:** `capture_website_signal()`, `build_public_signal_record()`
- **Tests:** `test_website_signal_integration_v1.py` (11 tests — has `sys.exit(0)` bug, INTERNALERROR)

### Contract Observation
- **File:** `weslr/contract_observation.py` (310 lines)
- **Status:** LIVE — `build_contract_observation()`, `validate_contract_observation()`, `append_contract_observation()`
- **Storage:** `weslr/contract_observations.jsonl` (19 real records)
- **Tests:** `test_contract_observation_v1.py` — **21 passed** ✅

### Contract Insufficiency Detector
- **File:** `weslr/contract_insufficiency_detector.py` (267 lines)
- **Status:** LIVE — `detect_insufficiency()` reads real file, `check_stability()` tracks patterns
- **Functions:** `detect_insufficiency()`, `_append_insufficiency_evidence()`, `_get_contract_key()`, `check_stability()`
- **Tests:** `test_contract_insufficiency_detector_v1.py` — **16 passed** ✅
- **Note:** `test_contract_insufficiency_detector_synthetic.py` has 1 failure (detector creates real file in certain test setups)

### Response Contracts
- **File:** `weslr/contract_observation.py` — `response_contract` field in observation records
- **Status:** LIVE — contracts assigned per response path in `build_contract_observation()`
- **Contracts observed in real data:** `conversational_entry`, `guided_help`, `structured_explanation`, `uncertainty_boundary`

### Bootstrap / OCW Status
- **File:** `weslr/bootstrap.py` (457 lines)
- **Status:** IMPLEMENTED — `new_timeline_id()`, `new_activation_token()`, `verify_secret_words()`, `new_pending_bootstrap()`
- **Purpose:** Timeline creation, bootstrap tokens, secret word verification

---

## B) IMPLEMENTED BUT NOT FULLY LIVE

### Response Expander
- **File:** `weslr/omnichat/response_expander.py` (400+ lines)
- **Status:** LIVE — deterministic expansion layer, no LLM, adds _omnichat_policy + expanded_response
- **Note:** Inventory previously listed `weslr/response_expansion.py` — that file does not exist. The actual module is `omnichat/response_expander.py`. Inventory corrected.

---

## C) SPEC ONLY / DOCTRINE ONLY

### Proposal Bridge
- **Doc:** `weslr/docs/WESLR_CONTRACT_IMPROVEMENT_PROPOSAL_BRIDGE_V1.md` (111 lines)
- **File:** `weslr/contract_improvement_proposal_bridge.py` — DOES NOT EXIST
- **Status:** SPEC ONLY — no implementation. `proposal_ready: false` state used by detector but bridge not wired.

### Review Interface
- **Doc:** `weslr/docs/WESLR_REVIEW_INTERFACE_V1.md` (207 lines)
- **File:** `weslr/review_interface.py` — DOES NOT EXIST
- **Status:** SPEC ONLY

### Decision Log
- **Doc:** `weslr/docs/WESLR_REVIEW_DECISION_LOG_V1.md` (202 lines)
- **File:** `weslr/review_decision_log.py` — DOES NOT EXIST
- **Status:** SPEC ONLY

### Operator Consistency
- **Doc:** `weslr/docs/WESLR_OPERATOR_CONSISTENCY_LAYER_V1.md` (161 lines)
- **File:** `weslr/operator_consistency.py` — DOES NOT EXIST
- **Status:** SPEC ONLY — marked "diagnostic layer on the human, not the system"

### Controlled Exposure
- **Doc:** `weslr/docs/WESLR_CONTROLLED_OBSERVATION_ENVIRONMENT_V1.md` (343 lines)
- **File:** `weslr/controlled_observation_environment.py` — DOES NOT EXIST
- **Status:** SPEC ONLY

### Public Readiness
- **Doc:** `weslr/docs/WESLR_PUBLIC_READINESS_PLAN_V1.md` — NO DOC FILE
- **File:** `weslr/public_readiness.py` — DOES NOT EXIST
- **Status:** SPEC ONLY — no implementation

### OmniChat Unification
- **Doc:** `weslr/docs/WESLR_OMNICHAT_UNIFICATION_PLAN_V1.md` (420 lines)
- **File:** `weslr/omni_execution_model.py` — DOES NOT EXIST
- **Status:** SPEC ONLY — plan defined but no implementation

### Frontend / UI
- **Doc:** `weslr/docs/WESLR_FRONTDOOR_UI_SPEC_V1.md` (244 lines)
- **File:** `weslr/frontdoor_ui_spec.py` — DOES NOT EXIST
- **Status:** SPEC ONLY — UI spec defined but no implementation

---

## D) NOT IMPLEMENTED

- **File:** `weslr/omnichat/response_expander.py` — EXISTS (was incorrectly listed as non-existent)
- **Note:** Inventory was wrong — `response_expansion.py` spec file exists but the actual module is `omnichat/response_expander.py`

### Proposal Bridge (Python module)
- `weslr/contract_improvement_proposal_bridge.py` — DOES NOT EXIST

### Review Interface (Python module)
- `weslr/review_interface.py` — DOES NOT EXIST

### Decision Log (Python module)
- `weslr/review_decision_log.py` — DOES NOT EXIST

### Operator Consistency (Python module)
- `weslr/operator_consistency.py` — DOES NOT EXIST

### Controlled Exposure (Python module)
- `weslr/controlled_observation_environment.py` — DOES NOT EXIST

### Public Readiness (Python module)
- `weslr/public_readiness.py` — DOES NOT EXIST

### OmniChat (Python module)
- `weslr/omni_execution_model.py` — DOES NOT EXIST

### Frontend/UI (Python module)
- `weslr/frontdoor_ui_spec.py` — DOES NOT EXIST

---

## Summary Table

| Component | Status | File |
|-----------|--------|------|
| /chat path | ✅ LIVE | main.py |
| Interpretation | ✅ LIVE | interpretation.py |
| Response contracts | ✅ LIVE | contract_observation.py |
| Public signal capture | ✅ LIVE | website_signal_integration.py |
| Contract observation | ✅ LIVE | contract_observation.py |
| Contract insufficiency detector | ✅ LIVE | contract_insufficiency_detector.py |
| Proposal bridge | ❌ SPEC ONLY | no .py file |
| Review interface | ❌ SPEC ONLY | no .py file |
| Decision log | ❌ SPEC ONLY | no .py file |
| Operator consistency | ❌ SPEC ONLY | no .py file |
| Controlled exposure | ❌ SPEC ONLY | no .py file |
| Public readiness | ❌ SPEC ONLY | no .py file |
| Response expander | ❌ SPEC ONLY | no .py file |
| OmniChat unification | ❌ SPEC ONLY | no .py file |
| Frontend/UI | ❌ SPEC ONLY | no .py file |
| Deployment/OCW status | ✅ IMPLEMENTED | bootstrap.py |
| contract_observations.jsonl | ✅ LIVE (19 records) | weslr/ |

---

## Test Results

| Test Suite | Result |
|------------|--------|
| `test_contract_observation_v1.py` | ✅ 21 passed |
| `test_contract_insufficiency_detector_v1.py` | ✅ 16 passed |
| `test_contract_insufficiency_detector_synthetic.py` | ⚠️ 10 passed, 1 failed (detector creates real file in test isolation) |
| `test_website_signal_integration_v1.py` | ❌ INTERNALERROR (sys.exit(0) at line 368) |
| `self_test.py` | ✅ exit code 0 |

---

## Current Blocker List

1. **proposal_ready threshold not reached** — `weak_entry_repetition` on `conversational_entry` has 1/3 stability checks; bridge cannot fire until 3
2. **Proposal bridge not implemented** — no `contract_improvement_proposal_bridge.py`; detector has `proposal_ready` state but nowhere to send it
3. **Review interface not implemented** — no `review_interface.py`; no operator-facing UI for reviewing proposals
4. **Decision log not implemented** — no `review_decision_log.py`; no persistent record of operator decisions
5. **self_test.py output** — appears to run silently with exit 0 but produces no visible output

---

## Commit

```
b8664aaf42a330f4f097f2f30ed0058aab26235b
```