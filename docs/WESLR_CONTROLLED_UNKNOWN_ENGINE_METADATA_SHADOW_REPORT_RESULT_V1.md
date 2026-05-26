# WESLR Controlled UNKNOWN ENGINE Metadata Shadow Report Result V1

## 1. Run Identity

- Lane: `RUN_CONTROLLED_UNKNOWN_ENGINE_METADATA_SHADOW_REPORT_V1`
- Lane type: `CONTROLLED_REPORT_RUN`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`
- Start HEAD: `8846766`
- Run date: `2026-05-26 07:46:43 UTC`
- Runner module path: `weslr/controlled_unknown_engine_metadata_shadow_runner.py`

## 2. Fixture Set

- Fixture count: 6
- Fixture kinds used:
  - `synthetic_unknown_engine_fixture`
  - `synthetic_cognitive_gym_metadata`
  - `synthetic_tier_0_2_math_readiness_card`
  - `synthetic_candidate_invariant_metadata`
  - `synthetic_failed_path_metadata`
  - `explicitly_approved_safe_internal_metadata`
- Input confirmation: synthetic/internal metadata only.
- Explicit internal metadata fixture confirmation: source-scoped, explicitly approved, metadata-summary only, and no raw content.
- No raw/private/live/provider/search/model/advisor/.weslr/runtime/final-answer/proof content was used.
- No real user-private content, real open-problem solving prompt, Erdős/Millennium proof attempt, theorem-prover task, provider/model/search/advisor output, `.weslr` state, runtime transcript, unscoped memory/context/evidence/artifact, final-answer text, proof text, solution text, or capability claim was used.

## 3. Runner Output Summary

- Report count: 6
- Validation status counts:
  - `valid_metadata_shadow_report`: 6
- Report validation counts:
  - `valid`: 6
- Produced metadata kinds:
  - `blocked_claim_summary`
  - `gap_summary`
  - `unknown_engine_result_artifact_metadata_shape`
  - `unknown_engine_run_metadata_shape`
  - `validation_summary`
- Blocked claims observed:
  - `advisor`
  - `certification`
  - `dot_weslr`
  - `external_validation`
  - `final_answer`
  - `intelligence`
  - `judge`
  - `model`
  - `official`
  - `open_problem`
  - `prize`
  - `product_readiness`
  - `proof`
  - `provider`
  - `public`
  - `runtime`
  - `score`
  - `search`
  - `solution`
  - `turing`
- Denied-authority summary: 12 denied-authority fields were present and false in every report.
  - `grants_runtime_authority`: false
  - `permits_chat_wiring`: false
  - `permits_dot_weslr_public_state`: false
  - `permits_external_validation_claim`: false
  - `permits_final_answer_generation`: false
  - `permits_official_claims`: false
  - `permits_provider_calls`: false
  - `permits_public_browser_runtime`: false
  - `permits_real_problem_solving`: false
  - `permits_scoring_or_judging`: false
  - `permits_solution_or_proof_claims`: false
  - `permits_theorem_solver_execution`: false
- No-run-authority flags summary: 12 no-run-authority flags were present and false in every report.
  - `is_engine_execution`: false
  - `is_external_validation`: false
  - `is_final_answer`: false
  - `is_live_problem_solving`: false
  - `is_official_benchmark`: false
  - `is_proof_validation`: false
  - `is_runtime_wiring`: false
  - `is_scoring_or_judging`: false
  - `is_theorem_prover_run`: false
  - `is_user_facing_output`: false
  - `uses_dot_weslr`: false
  - `uses_provider_model_search_or_advisor`: false
- Observed gaps:
  - none
- Next safe steps observed from runner metadata:
  - `add_synthetic_negative_fixture_coverage`
  - `analyze_internal_shadow_report_metadata_only`
  - `review_controlled_unknown_engine_metadata_shadow_runner_implementation_v1`

## 4. Safety Boundary Confirmation

- No real problem solving: confirmed.
- No theorem solver/prover execution: confirmed.
- No proof/solution/open-problem claim: confirmed.
- No scoring/judging/benchmark claim: confirmed.
- No provider/model/search/advisor calls: confirmed.
- No `.weslr` IO: confirmed.
- No runtime/chat/browser wiring: confirmed.
- No final/user-facing output: confirmed.
- No external validation claim: confirmed.

## 5. Expert Lane Handling

- Expert-style output observed: false
- Any expert-style output would be labeled `internal_expert_simulation` only by the runner contract.
- Expert-style output is not external validation.
- Adjudication is required before any expert-style output can be carried forward.
- Public/proof/prize/solution claims remain blocked.

## 6. Result Judgment

`controlled_unknown_engine_metadata_shadow_report_clean`

## 7. Recommended Next Lane

`REVIEW_CONTROLLED_UNKNOWN_ENGINE_METADATA_SHADOW_REPORT_V1`

## 8. Per-Fixture Internal Metadata Summary

### `synthetic_unknown_engine_fixture`

- Report validation valid: true
- Report validation status: `valid_metadata_shadow_report`
- Runner validation status: `valid_metadata_shadow_report`
- Blocked claim count: 20
- Denied authority count: 12
- No-run authority flag count: 12
- Observed gap count: 0
- Expert simulation present: false

### `synthetic_cognitive_gym_metadata`

- Report validation valid: true
- Report validation status: `valid_metadata_shadow_report`
- Runner validation status: `valid_metadata_shadow_report`
- Blocked claim count: 20
- Denied authority count: 12
- No-run authority flag count: 12
- Observed gap count: 0
- Expert simulation present: false

### `synthetic_tier_0_2_math_readiness_card`

- Report validation valid: true
- Report validation status: `valid_metadata_shadow_report`
- Runner validation status: `valid_metadata_shadow_report`
- Blocked claim count: 20
- Denied authority count: 12
- No-run authority flag count: 12
- Observed gap count: 0
- Expert simulation present: false

### `synthetic_candidate_invariant_metadata`

- Report validation valid: true
- Report validation status: `valid_metadata_shadow_report`
- Runner validation status: `valid_metadata_shadow_report`
- Blocked claim count: 20
- Denied authority count: 12
- No-run authority flag count: 12
- Observed gap count: 0
- Expert simulation present: false

### `synthetic_failed_path_metadata`

- Report validation valid: true
- Report validation status: `valid_metadata_shadow_report`
- Runner validation status: `valid_metadata_shadow_report`
- Blocked claim count: 20
- Denied authority count: 12
- No-run authority flag count: 12
- Observed gap count: 0
- Expert simulation present: false

### `explicitly_approved_safe_internal_metadata`

- Report validation valid: true
- Report validation status: `valid_metadata_shadow_report`
- Runner validation status: `valid_metadata_shadow_report`
- Blocked claim count: 20
- Denied authority count: 12
- No-run authority flag count: 12
- Observed gap count: 0
- Expert simulation present: false
