# WESLR Project Boundaries V1

## 1. Repository identity
- Repository: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Role: WESLR core repo
- Branch normally: `master`
- This document is the standing boundary bootstrap for future OCC implementation lanes.

## 2. Operator split
- OCC implements WESLR core code, helpers, protocols, tests, validation, docs, reports, and commits.
- Nova is not the WESLR core code implementer.
- Nova may later run, observe, or design UI visuals and possibly wiki/instructions/payments work, but that is separate and uncertain.

## 3. Protected files by default
Unless explicitly approved, do not edit:
- `weslr/chat_responder.py`
- `weslr/main.py`
- repo-root `main.py`
- `dialogue.py`
- `chat_ui.py`

## 4. Default forbidden scopes
Unless explicitly approved, do not implement:
- runtime wiring
- public chat behavior changes
- final-answer generation authority
- provider/model calls
- retrieval/tool execution
- `.weslr` reads/writes
- persistence/database writes
- real memory mutation
- real project mutation
- autonomous self-modification
- public claims
- official benchmark/intelligence claims
- broad release-gate weakening

## 5. Default allowed scopes for metadata-helper lanes
Usually allowed in approved helper lanes:
- design docs
- pure deterministic helper files
- focused tests
- implementation reports
- narrow exact-path release-gate allowance only if necessary

## 6. WESLR doctrine
- LLM may be helper or candidate generator only.
- WESLR owns validation, structure, boundary routing, calibration, compression, and governance.
- Internal exploration can be radical.
- Public/export claims must be controlled separately.

## 7. Release gate rule
- Never weaken release gates broadly.
- If a project pattern requires it, use only a narrow exact-path allowlist.
- Record the exact reason.

## 8. Public claim rule
- No AGI, sentience, consciousness, or official intelligence claims.
- No “WESLR solved math/science/physics” claims.
- Capability maturity must always be qualified.

## 9. Required safe restart ritual
Before touching files in a future lane:
1. Read this file.
2. Read `BUILD_STANDARD.md`.
3. Print repo root, branch, current HEAD, and `git status --short`.
4. State the exact allowed scope and forbidden scope.
5. State protected files.
6. State whether unrelated uncommitted files exist.
7. State the exact next task before editing.
8. Stop if boundaries are missing, ambiguous, or contradictory.
