# OCC WESLR STAGING TEST LOOP V1

**Version:** 1.0
**Status:** OPERATIONAL DOCTRINE — documented, not implemented
**Date:** 2026-05-01
**Owner:** operator

---

## SECTION 1 — Purpose

Define the safe operational loop where:
- OCC phone can test WESLR staging via `/chat`
- OCW can repair/deploy WESLR staging
- **The operator remains the authority between them**

No automatic wiring. No autonomous repair. No system-to-system command chain without operator approval.

---

## SECTION 2 — Roles

### OCC Phone
- **Role:** Conversation tester, staging probe
- **Action:** Sends messages to `https://staging.weslr.de/chat`
- **Records:** Response, path, status, issue summary
- **Constraint:** Does not modify WESLR runtime
- **Constraint:** Does not command OCW automatically

### WESLR Staging
- **Role:** Target system under test
- **Action:** Responds through `/chat`, appends observation/public signal data
- **Constraint:** Does not command OCW
- **Constraint:** Does not self-repair

### OCW (OpenClaw Website / Weslr-Demo Server)
- **Role:** Repair and deploy environment
- **Owns:** Repo at `/home/pr0/projects/weslr`
- **Capabilities:** `git pull/push`, GitHub, tests, `weslr-staging-demo.service` restart
- **Constraint:** Repairs only after explicit operator instruction
- **Constraint:** No automatic deployment based only on WESLR observations/proposals/AAI output

### Operator (pr0dus)
- **Role:** Authority between OCC and OCW
- **Action:** Reviews OCC reports, decides whether repair is needed, authorizes OCW action
- **Responsibility:** Preserves governance boundary

---

## SECTION 3 — Confirmed Working State

### OCC_TEST_REPORT_V1 — 2026-05-01 12:52 UTC

| Message | Path | Response Contract | Status |
|---------|------|-------------------|--------|
| `"hey"` | `fallback_safe` | `conversational_entry` | ✅ OK |
| `"what can you do"` | `usage_guidance` | — | ✅ OK |
| `"what is WESLR"` | `system_definition_query` | — | ✅ OK |

- **HTTP Status:** 200 for all requests
- **Issues found:** None
- **Severity:** None
- **Observations appended:** Likely (`_weslr_mode: private_dev` confirmed in responses)

**Conclusion:** OCC phone → WESLR staging `/chat` is operational.

---

## SECTION 4 — Report Format

All OCC staging test reports use this format:

### OCC_TEST_REPORT_V1

| Field | Description |
|-------|-------------|
| `test_name` | Identifier e.g. `OCC_TEST_REPORT_V1` |
| `timestamp` | ISO-8601 UTC of test |
| `target_url` | e.g. `https://staging.weslr.de/chat` |
| `message` | The message sent |
| `http_status` | HTTP response code |
| `response_path` | WESLR routing path |
| `response_contract` | Contract label if available |
| `response_excerpt` | First ~200 chars of reply |
| `expected_behavior` | What should happen |
| `actual_behavior` | What actually happened |
| `issue_found` | `true` / `false` |
| `severity` | `none` / `low` / `medium` / `high` / `critical` |
| `suggested_next_action` | What to do next, if anything |
| `raw_prompt_stored` | `false` / `unknown` |
| `notes` | Free-form observations |

---

## SECTION 5 — Repair Handoff Rule

### Forbidden

- WESLR automatically instructing OCW to repair
- OCC auto-triggering OCW repairs based on test results
- OCW changing files based only on WESLR output without operator approval
- Automatic deployment triggered by observation/proposal/AAI

### Permitted

- OCC reports findings to operator
- Operator sends bounded repair instruction to OCW
- OCW executes repair on explicit authorization
- OCW confirms completion to operator

---

## SECTION 6 — Safe Workflow

```
1. OCC tests staging via /chat
2. OCC returns OCC_TEST_REPORT_V1 to operator
3. Operator reviews report
4. If repair needed → operator sends bounded OCW repair prompt
5. OCW fixes on repo (git)
6. OCW tests locally
7. OCW deploys / restarts weslr-staging-demo.service
8. OCC retests staging
```

Each step requires operator awareness. No step is automatic.

---

## SECTION 7 — Current Boundary

This loop is **not** autonomous self-repair.

- OCC: probe and report
- OCW: repair and deploy only when authorized
- Operator: gatekeeper between probe and repair

The governance boundary is maintained:
- OCC cannot command OCW
- WESLR cannot command OCW
- OCW does not self-trigger

---

## SECTION 8 — Verdict

**`OCC_WESLR_STAGING_TEST_LOOP_V1_DEFINED`**

- Document created: `weslr/docs/OCC_WESLR_STAGING_TEST_LOOP_V1.md`
- No runtime code implemented
- No automatic wiring
- Operator authority preserved
- OCW repair handoff governed by explicit instruction only

---

*No runtime behavior modified. No Python files changed. No JSONL files modified. Inspection and documentation only.*