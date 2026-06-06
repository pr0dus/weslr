# WESLR Next Coded Target From Designed But Not Coded Inventory V1

## 1. Inventory summary
- Source inventory: `docs/WESLR_DESIGNED_BUT_NOT_CODED_INVENTORY_V1.md`
- Highest-value coded work still pending is the project-chat boundary chain.
- The inventory separates coded, designed-only, partial, planning-only, Nova/UI-owned, and reconciled items clearly.
- The project-chat runtime chain is still blocked at the retrieval/evidence layer before any final-answer or live-chat work.

## 2. Candidate comparison
1. Project Chat Runtime Boundary
- Too close to runtime wiring.
- Useful, but it should follow retrieval and answer-boundary groundwork.

2. Project Chat RAG and Evidence Retrieval Boundary
- Best leverage point for the next coded lane.
- Establishes evidence boundaries before answer generation.
- Keeps project chat grounded in source/evidence governance.

3. Final Answer Generation Boundary for Project Chat
- Important, but premature before retrieval/source rules are coded.

4. Private Project Chat Owner Preview Boundary
- Safe, but it is a private preview surface boundary, not the core project-chat evidence path.

5. Private Owner Preview Render View Model
- Partial and untracked-source dependent.
- Not the best next coded target because it is already drifting from clean tracked-code selection.

## 3. Risk notes
- Runtime wiring is still forbidden.
- Final-answer generation without retrieval boundaries would be unsafe and out of order.
- UI/Nova work must stay separate.
- Partial/untracked-source work should not be selected ahead of a clean tracked boundary target.

## 4. Dependency order
1. Project-chat runtime boundary
2. Project-chat RAG/evidence retrieval boundary
3. Final-answer generation boundary
4. Private preview boundaries and UI-adjacent view models

Given the current inventory, the next coded target should be step 2.

## 5. Selected next coded target
- `Project Chat RAG and Evidence Retrieval Boundary`

## 6. Why this target comes first
- It is the highest-leverage coded boundary still missing before any final-answer implementation.
- It keeps chat behavior evidence-led instead of answer-led.
- It fits the “working private project chat” direction without touching live chat or protected runtime files.
- It reduces the risk of coding answer generation against an unbounded retrieval model.

## 7. What files should be implemented in the next lane
- `weslr/project_chat_rag_and_evidence_retrieval.py` *(or the lane’s exact helper filename pattern)*
- `weslr/tests/test_project_chat_rag_and_evidence_retrieval_v1.py`
- `docs/WESLR_PROJECT_CHAT_RAG_AND_EVIDENCE_RETRIEVAL_HELPERS_IMPLEMENTATION_REPORT_V1.md`

## 8. What must stay forbidden
- `weslr/chat_responder.py`
- `weslr/main.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`
- live chat wiring
- final-answer execution
- retrieval/search execution from the runtime path
- tool execution
- persistence/database writes
- `.weslr` IO
- public/user-facing behavior
- Nova/UI-owned work

## 9. Expected implementation lane name
- `IMPLEMENT_WESLR_PROJECT_CHAT_RAG_AND_EVIDENCE_RETRIEVAL_HELPERS_V1`

## 10. Final judgment
- `weslr_next_coded_target_selected_ready_for_project_chat_rag_evidence_implementation`
