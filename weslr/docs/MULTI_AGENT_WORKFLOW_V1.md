# WESLR Multi-Agent Workflow — V1

**Version:** 1.0
**Status:** active doctrine — governs ChatGPT ↔ OCC ↔ OCW coordination
**Created:** 2026-04-27
**Owner:** operator

---

## SECTION 1 — Agent Roles

### ChatGPT
- Architecture, design review, and planning
- Produces task prompts and validates completion reports
- Does not touch source code directly
- Operates as the architect/reviewer, not executor

### OCC
- Canonical WESLR source agent — runs on Android/Termux
- Implements features, fixes, and documentation based on ChatGPT prompts
- Pushes reviewed commits to GitHub
- Maintains discipline: no improvised architecture, no direct destructive actions
- Owns all core source code decisions

### OCW
- Ubuntu server / website deployment agent
- Pulls only from GitHub (never receives source directly)
- Owns website and runtime deployment tasks on weslr.de paths
- Must not improvise architecture — executes only what is committed and documented
- Reports deployment status back through the chain

---

## SECTION 2 — Source of Truth

### GitHub as Transfer Bridge

```
OCC (phone/Termux) → GitHub → OCW (Ubuntu server)
```

- **OCC** commits and pushes source to GitHub
- **OCW** pulls reviewed commits from GitHub only
- Direct OCC → OCW file transfer is not used
- OCW must report current commit hash before and after every pull

### Commit Integrity Rules

- Every commit must pass `release_gate_v1.py` before pushing
- OCW must never pull unreviewed commits
- OCW must validate `git log --oneline` confirms expected commits
- Rollback is done by OCC pushing a revert commit; OCW then pulls

---

## SECTION 3 — Communication Protocol

### Standard Workflow

```
1. ChatGPT  → creates task prompt (architecture, plan, review)
2. User     → gives prompt to OCC
3. OCC      → implements or prepares handoff
4. OCC      → commits to GitHub, records commit hash
5. OCC      → creates OCW handoff message (commit hash + instructions)
6. User     → delivers handoff to OCW
7. OCW      → pulls, validates, deploys, reports
8. OCW      → reports back to user
9. User     → brings report to ChatGPT for validation
```

### Handoff Message Format (OCC → OCW)

Every handoff must include:
- Task description
- Branch name
- Commit hash before work
- Expected commit hash after pull
- Files/directories affected
- Validation commands to run
- What OCW must NOT touch

---

## SECTION 4 — Direct OCC ↔ OCW Communication

If direct agent communication becomes possible later:

- OCC may create handoff files in the repository (e.g., `weslr/docs/ocw-handoffs/`)
- OCW reads handoff files after pulling updated code
- OCW writes a deployment report file in the same directory
- OCW commits deployment docs only when explicitly instructed by OCC
- **No autonomous cross-agent commands** — OCW never runs OCC-provided shell commands directly
- OCW never reads ephemeral session state — only committed files

---

## SECTION 5 — Disconnection Safety

### Phone-Based Agent Problem

OCC runs on a phone that may leave LAN daily. OCW cannot depend on a live OCC connection.

### Survival Rules

- **Every task must end with a recorded commit hash**
- **Every handoff must include current branch + commit hash**
- **No task may depend on a live OCC connection**
- OCW must be able to complete its work using only GitHub as the source
- If OCW encounters an error it cannot resolve, it reports and stops — it does not improvise

### Minimum Viable Handoff

```
Task: <description>
Branch: <branch-name>
Commit: <commit-hash>
OCW must: <action>
OCW must NOT: <list>
Validate with: <command>
```

---

## SECTION 6 — Forbidden Areas

The following are **hard boundaries** for all agents:

| Forbidden | Reason |
|-----------|--------|
| `e-qubs.de` | Completely off-limits |
| OpenClaw core | Not authorized unless explicitly requested |
| TIA bridge | Private commercial IP, separate repo only |
| Secrets / credentials | Never exposed in commits or handoffs |
| Production public exposure | Not until all public readiness gates pass |
| `git add -A` / `git add .` | Too broad; only exact files per commit scope |
| Unreviewed direct pushes | OCW only pulls what OCC has committed |

---

## SECTION 7 — Required Reports

### OCC Report (every commit/push)

Must include:
- Files changed (exact list)
- Commit hash
- Release gate result (`release_gate_v1.py` output)
- Push status (success/failed)
- Next handoff if applicable

### OCW Report (every deployment action)

Must include:
- Working directory
- Branch name
- Commit hash before pull
- Commit hash after pull
- Services touched
- Domains touched (confirmation: only weslr.de paths)
- Validation result (release gate or task-specific)
- Any blockers or errors

---

## SECTION 8 — Staging Rule

**Never use broad staging:**

```bash
# FORBIDDEN
git add -A
git add .
git commit -a
```

**Always use exact file staging:**

```bash
git add <exact-file-1> <exact-file-2>
git diff --cached --name-status   # review before commit
git commit -m "descriptive message"
```

OCW and OCC both follow this rule. Discipline prevents accidental scope creep.

---

## SECTION 9 — Public Deployment Rule

OCW must **not** expose WESLR publicly until **all** of the following are confirmed:

- [x] `public_demo_readonly` mode implemented
- [x] Write handlers blocked in demo mode
- [x] Rate limits active (per-session and per-IP)
- [x] LLM disabled or budget-guarded in public mode
- [x] Public readiness tests pass (`public_readiness_tests.py`)
- [x] Rollback / off switch exists and is tested

**Current status:** Public demo mode is implemented. Remaining items are tracked in the WESLR public readiness plan.

---

## SECTION 10 — Verdict

**MULTI_AGENT_WORKFLOW_DEFINED**

This document establishes the coordination doctrine for WESLR development and deployment across three agents. GitHub is the only bridge. OCC is the canonical source. OCW is the deployment executor. ChatGPT is the architect/reviewer. The operator carries messages and holds final authority.

---

## APPENDIX A — Quick Reference

| Agent | Role | Push/Pull |
|-------|------|-----------|
| ChatGPT | Architect/reviewer | Neither — prompts and validates |
| OCC | Canonical source | Pushes to GitHub |
| OCW | Deployment | Pulls from GitHub only |

| Command | Purpose |
|---------|---------|
| `git diff --cached --name-status` | Review staged files before commit |
| `git add <exact-file>` | Stage only specific files |
| `python3 weslr/tests/release_gate_v1.py` | Validate before push |
| `git rev-parse HEAD` | Get current commit hash |
