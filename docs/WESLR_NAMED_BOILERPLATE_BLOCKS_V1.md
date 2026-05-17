# WESLR_NAMED_BOILERPLATE_BLOCKS_V1

Canonical named boilerplate blocks for compact, safe WESLR task prompts.

**Classification:** WESLR_CANON_ALIGNMENT documentation only.  
**Live behavior changed:** no.  
**Purpose:** make future WESLR prompts shorter while preserving safety, validation, alignment layers, and report discipline.

---

## 1. SAFE_RESTART_RITUAL_V1

Run before every WESLR task to verify repo state:

```
SAFE_RESTART_RITUAL_V1
1. cd /data/data/com.termux/files/home/weslr-pr47-clean
2. pwd
3. git rev-parse --show-toplevel
4. git branch --show-current
5. git status --short
6. git log --oneline -N  (use N appropriate to task depth)
7. git rev-parse HEAD
8. git diff --stat
9. git diff
10. Verify expected HEAD / checkpoint matches.
11. If repo, branch, or scope is wrong — STOP. Do not proceed.
```

**Never remove:** repo-path discipline and branch verification.

---

## 2. WESLR_ALIGNMENT_LAYER_DECLARATION_V1

Every WESLR task must declare its alignment layer and live-behavior impact:

```
WESLR_ALIGNMENT_LAYER_DECLARATION_V1

Layer options:
- OCC_CONTEXT_ALIGNMENT  → affects how OCC/OpenClaw assists the build
- WESLR_CANON_ALIGNMENT  → records WESLR doctrine/design only
- WESLR_RUNTIME_CHANGE   → changes actual WESLR behavior

Required in every task:
- State which layer is touched.
- State whether live WESLR behavior changed: yes / no.
- State whether OCC bootstrap behavior may be influenced.
- State whether WESLR runtime reads the changed file.

Rule:
A context or canon commit does not imply live behavior changed
unless runtime/source files are modified or WESLR explicitly reads
that document at runtime.
```

---

## 3. WESLR_FORBIDDEN_RUNTIME_PATHS_V1

Default-deny list. Explicitly override only if owner-approved.

```
WESLR_FORBIDDEN_RUNTIME_PATHS_V1

Unless explicitly approved per-task:
- No chat_responder.py edits
- No main.py edits
- No staging / deploy / UI / voice file edits
- No broad live runtime replacement
- No model / search / advisor calls
- No .weslr state writes
- No raw private text storage
- No raw prompt / response storage
- No raw response retention
- No source_registry / truth writes
- No default feature flag enablement
- No branch expansion
- No official benchmark / Turing-test / IQ / certification claims
- No fake consciousness / sentience claims
- No human-level-general-intelligence claims
```

---

## 4. WESLR_EVALUATION_SAFETY_BOUNDARIES_V1

Evaluation-specific constraints.

```
WESLR_EVALUATION_SAFETY_BOUNDARIES_V1

- Internal evaluation only.
- Controlled synthetic prompts only, unless separately approved.
- Preflight before every possible ChatResponder call.
- Blocker / monkeypatch contracts before every real shadow call.
- Metadata-only capture.
- No raw response retention.
- Readiness labels are qualitative only.
- No numeric scoring.
- No official / public claims.

Blocked families/paths (keep blocked unless separate design exists):
- memory_honesty
- continuity_relationship
- self_identity_boundaries
- evidence_source_boundaries
- guardrail_preservation
- unsafe live_slice_behavior
- live_slice_behavior_existing_plan_helper_only (needs feature-flag isolation design)
- status / write / search / model / advisor prompts
- currentness / source / external-service paths
- raw_prompt / raw_response storage paths
- global_feature_flag mutation paths
```

---

## 5. WESLR_RELEASE_VALIDATION_V1

Minimum validation for WESLR tasks.

```
WESLR_RELEASE_VALIDATION_V1

1. Relevant focused tests for touched helper / source files.
2. python3 weslr/tests/release_gate_v1.py
3. bash scripts/weslr_release_check.sh

Rules:
- No broad test suites unless the task explicitly needs them.
- No tests that call real ChatResponder unless the task
  explicitly approves real shadow calls.
```

---

## 6. WESLR_REPORT_FORMAT_STANDARD_V1

Standard report-back structure.

```
WESLR_REPORT_FORMAT_STANDARD_V1

SECTION 1 — STATUS
- repo path
- branch
- HEAD
- working tree status
- alignment layer touched
- live behavior changed: yes / no
- files modified / commits made

SECTION 2 — CONTEXT / DESIGN / METHOD
- What was done and why
- Scope and boundaries observed

SECTION 3 — FILES CHANGED or OBSERVATION SUMMARY
- List of changed / observed items
- Before / after where relevant

SECTION 4 — VALIDATION RUN
- Tests run
- Release gate / release check result
- Errors / warnings

SECTION 5 — SAFETY CONFIRMATION
- Confirmation that forbidden paths were not taken
- Confirmation that no raw text was stored
- Confirmation that no official claims were made

SECTION 6 — COMMIT or NEXT STEP
- Commit hash if committed
- Recommended next lane
- Required follow-up task
```

---

## 7. WESLR_WORK_PACKET_V1

Compact prompt format for future tasks.

```
WESLR_WORK_PACKET_V1
ROLE:        {descriptive role name}
CHECKPOINT:  {short_sha} — {one-line description}
TASK:        {TASK_NAME_V1}
LAYER:       {OCC_CONTEXT_ALIGNMENT | WESLR_CANON_ALIGNMENT | WESLR_RUNTIME_CHANGE}

ALLOWED:    {comma-separated allowed actions / files}
FORBIDDEN:  <<WESLR_FORBIDDEN_RUNTIME_PATHS_V1>>
FILES:      {comma-separated files / globs}

RITUAL:     <<SAFE_RESTART_RITUAL_V1>>
SAFETY:     <<WESLR_EVALUATION_SAFETY_BOUNDARIES_V1>>
VALIDATION: <<WESLR_RELEASE_VALIDATION_V1>>
REPORT:     <<WESLR_REPORT_FORMAT_STANDARD_V1>>
NEXT:       {recommended next lane}
```

**Rule:** Named blocks are references, not permission expansion.  
If a task needs a higher-risk action, it must still say so explicitly.

---

## 8. SAFE_READ_ONLY_SWARM_PATTERN_V1

Read-only sub-agent pattern for parallel analysis.

```
SAFE_READ_ONLY_SWARM_PATTERN_V1

Allowed sub-agent roles (read-only unless explicitly authorized):
- Inventory Agent       → scope / file / dependency inventory
- Test-Impact Agent     → test / validation impact assessment
- Governance Agent      → safety / governance drift check
- Compression Agent     → prompt compression / checklist optimization
- Lead Merge Agent      → merges all findings into one final report

Mandatory swarm rules:
- All sub-agents are READ-ONLY by default.
- No sub-agent may edit runtime source.
- No sub-agent may call ChatResponder.
- No sub-agent may execute prompts.
- No sub-agent may make official claims.
- Lead agent merges; sub-agents do NOT self-authorize changes.
- Swarm results are DESIGN INPUT, not execution triggers.
- No background / autonomous / proactive work.
- No model / search / advisor calls unless task explicitly approves.
- No raw prompt / response retention.
- No .weslr state writes.
```

---

## 9. OCC_CONTEXT_CLEANUP_DEBT_V1

Record of temporary scaffolding.

```
OCC_CONTEXT_CLEANUP_DEBT_V1

OCC / OpenClaw-tied context files inside the WESLR repo are
temporary build / evaluation scaffolding.

Do NOT delete them during the current evaluation lane.

Future cleanup lane (requires separate owner approval):
  AUDIT_AND_CLEAN_OCC_CONTEXT_FILES_FROM_WESLR_REPO_V1

Cleanup must include:
- Exact inventory of OCC-tied files
- Separation of WESLR canon from OCC bootstrap / context
- Owner approval before deletion / relocation
- Backup / commit checkpoint before cleanup
- Release gate + release check after cleanup
- Rollback plan if cleanup causes issues
```

---

## 10. ANTI_DRIFT_RULE_V1

Guard against compact-prompt escalation.

```
ANTI_DRIFT_RULE_V1

Named blocks are REFERENCES, not permission expansion.

A compact prompt that says:
  FORBIDDEN: <<WESLR_FORBIDDEN_RUNTIME_PATHS_V1>>
does NOT authorize anything in that block.

If a task needs a higher-risk action, it MUST say so EXPLICITLY.

Compact prompts CANNOT silently authorize:
- Runtime changes
- ChatResponder calls
- Model / search / advisor calls
- Raw prompt / response storage
- Raw response retention
- Numeric scoring
- Official benchmark / Turing / IQ / certification claims
- Branch expansion
- Default enablement

If there is ANY doubt:
- STOP
- Classify as blocked_by_boundary
- Require explicit owner approval before proceeding
```

---

## Usage Example

```
WESLR_WORK_PACKET_V1
ROLE:        WESLR Shadow Batch Design Engineer
CHECKPOINT:  a5e3756 — OCC context aligned after third shadow batch
TASK:        DESIGN_FOURTH_CONTROLLED_REAL_CHATRESPONDER_SHADOW_BATCH_V1
LAYER:       WESLR_CANON_ALIGNMENT

ALLOWED:    design doc only, one to five low-risk prompt IDs,
             ordinary_task_behavior, conduct_alignment, non_canned_cognition
FORBIDDEN:  <<WESLR_FORBIDDEN_RUNTIME_PATHS_V1>>
FILES:      docs/WESLR_FOURTH_CONTROLLED_REAL_CHATRESPONDER_SHADOW_CALL_BATCH_V1.md

RITUAL:     <<SAFE_RESTART_RITUAL_V1>>
SAFETY:     <<WESLR_EVALUATION_SAFETY_BOUNDARIES_V1>>
VALIDATION: <<WESLR_RELEASE_VALIDATION_V1>>
REPORT:     <<WESLR_REPORT_FORMAT_STANDARD_V1>>
NEXT:       RUN_FOURTH_CONTROLLED_REAL_CHATRESPONDER_SHADOW_CALL_BATCH_REPORT_V1
```

---

## Version

- Block set version: V1
- Created: 2026-05-17
- Next review: when WESLR evaluation work stabilizes or when a new pattern is needed.
