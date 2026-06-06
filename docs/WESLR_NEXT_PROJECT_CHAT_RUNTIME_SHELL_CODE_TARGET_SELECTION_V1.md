# WESLR Next Project Chat Runtime Shell Code Target V1 — Selection

## OCC Final Report

1. Handshake result
- PASS
- Repo root, branch, and expected HEAD matched.

2. Start HEAD
- `ae0311b940f6fe319270ef8dec81e8d571549033`

3. Target selection lane
- `SELECT_WESLR_NEXT_PROJECT_CHAT_RUNTIME_SHELL_CODE_TARGET_V1`

4. WESLR repo root and branch
- Root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`

5. Selection artifact
- `docs/WESLR_NEXT_PROJECT_CHAT_RUNTIME_SHELL_CODE_TARGET_SELECTION_V1.md`

6. Current coded pieces
- Project Chat RAG/Evidence Retrieval Helpers
- Project Chat Final Answer Generation Helpers
- Project Chat Answer Plan Metadata Helpers
- Project Chat Runtime Dry-Run Metadata
- Controlled Project Chat Runtime Shell Metadata
- Controlled Final Answer Generation
- Controlled User Facing Output
- Private Project Chat Owner Preview Boundary helpers
- Private Owner Preview Render View Model helpers

7. Candidate comparison
- `1. Implement Project Chat Runtime Boundary helpers` — useful, but too broad and too close to policy/boundary docs rather than the next connective packet.
- `2. Implement Private Project Chat Owner Preview Boundary helpers` — useful for the private preview lane, but not the strongest connector for the project-chat runtime shell itself.
- `3. Implement Private Owner Preview Render View Model` — rejected for this lane because it trends toward UI/render-view work, which is not the next internal metadata connector.
- `4. Implement a Project Chat Assembly/Orchestration Packet helper` — selected. This is the next safe internal connector between the already-coded metadata helpers.
- `5. Implement a Project Chat Runtime Shell dry-run consumer` — useful, but it should come after the assembly packet exists.

8. Dependency order
- Answer plan metadata helpers
- RAG/evidence retrieval helpers
- Final answer generation helpers
- Runtime dry-run metadata
- Controlled runtime shell metadata
- Assembly/orchestration packet helper
- Runtime shell dry-run consumer
- Any later private preview or UI consumption

9. Selected next coded target
- `Implement a Project Chat Assembly/Orchestration Packet helper`

10. Why this target comes first
- It connects the existing metadata helpers without live chat.
- It can assemble the user request metadata, project context metadata, retrieval/evidence packet, answer-plan packet, final-answer packet, and blocked/missing/approval state into one internal orchestration packet.
- It stays private, internal, and metadata-first.
- It avoids UI/Nova-owned work, model/provider/search/tool calls, live retrieval, persistence, and `weslr/chat_responder.py` changes.
- It gives the runtime shell a single safe packet boundary to consume later.

11. Files proposed for implementation
- `weslr/project_chat_assembly_orchestration_packet.py`
- `weslr/tests/test_project_chat_assembly_orchestration_packet_v1.py`
- `docs/WESLR_PROJECT_CHAT_ASSEMBLY_ORCHESTRATION_PACKET_HELPERS_IMPLEMENTATION_REPORT_V1.md`
- `docs/WESLR_PROJECT_CHAT_ASSEMBLY_ORCHESTRATION_PACKET_HELPERS_REVIEW_V1.md`

12. Forbidden behavior
- No live chat wiring
- No `weslr/chat_responder.py` edits
- No model/provider/search/tool calls
- No retrieval execution
- No persistence
- No public/user-facing behavior
- No answer delivery
- No `.weslr` IO
- No private data mutation
- No UI/Nova-owned work

13. Expected implementation lane
- `IMPLEMENT_WESLR_PROJECT_CHAT_ASSEMBLY_ORCHESTRATION_HELPERS_V1`

14. Final judgment
- `weslr_next_project_chat_runtime_shell_code_target_selected_ready_for_assembly_orchestration_helpers`
