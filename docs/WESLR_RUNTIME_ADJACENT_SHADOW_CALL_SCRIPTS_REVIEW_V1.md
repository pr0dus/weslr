# WESLR Runtime-Adjacent Shadow Call Scripts Review V1

## 1. Purpose and scope
Read-only review of the two runtime-adjacent shadow-call scripts before any helper adoption or repair.

## 2. Repo root, branch, start HEAD, current HEAD
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `91bbd2111d9381c7855a0ad67bf5129bbc41de80`
- Current HEAD: `91bbd2111d9381c7855a0ad67bf5129bbc41de80`

## 3. Files reviewed
- `weslr/tests/run_second_real_chatresponder_shadow_call_batch_v1.py`
- `weslr/tests/run_third_real_chatresponder_shadow_call_batch_v1.py`
- `docs/WESLR_CONTROLLED_SOURCE_ACCESS_ADAPTER_AND_RUNTIME_ADJACENCY_REVIEW_V1.md`

## 4. Protected-file status
Protected files were not changed:
- `weslr/chat_responder.py`
- `weslr/main.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`

## 5. Script 1 summary
`run_second_real_chatresponder_shadow_call_batch_v1.py` is a report-oriented runner that imports `weslr.controlled_behavior_prompt_set` and `weslr.real_chatresponder_shadow_call_helpers`, selects prompt IDs, builds a config with `real_call_authorized=True`, runs preflight/evaluation through shadow-call helper APIs, validates/summarizes/renders results, and writes a docs report.

## 6. Script 2 summary
`run_third_real_chatresponder_shadow_call_batch_v1.py` is the same class of runner, using a slightly different prompt selection strategy and also calling shadow-call helper APIs, then writing a docs report.

## 7. Import/dependency assessment
- Both scripts import `weslr.real_chatresponder_shadow_call_helpers`.
- Both scripts import `weslr.controlled_behavior_prompt_set`.
- No direct `ChatResponder` class import appears in either script.
- Dependency-wise, they are still runtime-adjacent because they drive helper APIs whose names and arguments are explicitly shadow-call oriented.

## 8. ChatResponder/runtime adjacency assessment
- Direct ChatResponder import: no.
- Indirect ChatResponder adjacency: yes.
- The scripts are clearly named for real ChatResponder shadow-call batches and use helper functions that evaluate prompt sets, preflight, validate, summarize, and render shadow-call results.
- That is enough to treat them as runtime-adjacent, not helper-adoption-safe artifacts.

## 9. Provider/model/external-call risk assessment
- The scripts themselves do not visibly call provider APIs directly.
- They do set `real_call_authorized=True` and call `evaluate_prompt_set_with_real_chatresponder_shadow_call_v1`, which is a strong indicator of real-call path dependency.
- Because the imported helper module name explicitly includes `real_chatresponder_shadow_call`, accidental execution could reach live model/provider paths through the helper layer.

## 10. Persistence/write risk assessment
- They write generated report files under `docs/`.
- They do not visibly write source files, project state, or workspace config.
- Report writing is intentional and contained, but it still makes them execution-capable artifact generators rather than inert notes.

## 11. `.weslr` IO risk assessment
- No `.weslr` IO is visible in these scripts.
- However, because they invoke real shadow-call helper APIs, `.weslr`-adjacent risk should be treated as downstream/indirect until the helper layer is separately confirmed inert.

## 12. Memory/project mutation risk assessment
- No direct memory or project mutation is visible in the scripts.
- They do not appear to mutate memory/project state directly.

## 13. Raw/private/session leakage risk assessment
- No raw session bodies, tokens, or secrets are visible in the scripts.
- They do include execution/report code that could surface runtime outputs if accidentally run, so they should remain quarantined from repair lanes.

## 14. Whether scripts are stale/noisy/useful/dangerous
- Useful as historical report generators: yes.
- Noisy: yes.
- Stale for current helper adoption: likely.
- Dangerous to adopt into the current helper lane: yes, because they sit on a real shadow-call path.

## 15. Whether scripts should be quarantined
- Yes.
- They should remain separate from the controlled source access adapter helper path.

## 16. Whether scripts should be ignored for current helper adoption
- Yes.
- They should not block helper adoption, but they should not be folded into it.

## 17. Whether scripts block controlled source access adapter helper repair/adoption
- No, they do not block the helper itself.
- They do block any attempt to conflate helper adoption with runtime-adjacent shadow-call execution.

## 18. Recommended handling
- Quarantine the scripts as runtime-adjacent report runners.
- Keep them untracked for now.
- Review separately before any future execution or adoption.

## 19. Recommended next lane
- `REVIEW_WESLR_REAL_CHATRESPONDER_SHADOW_CALL_HELPERS_AND_REPORT_RUNNERS_V1`

## 20. Final judgment
`runtime_adjacent_shadow_call_scripts_review_found_external_call_risk`
