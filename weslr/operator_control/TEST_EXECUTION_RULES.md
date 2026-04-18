# WESLR TEST EXECUTION RULES

Operator execution discipline for running WESLR tests.

---

## 1. TEST EXECUTION COMMAND

**Command to run all WESLR tests:**

```bash
cd /data/data/com.termux/files/home/.openclaw/workspace
python -m unittest discover -s weslr -p 'test_*.py' -v
```

**Command to run a specific layer's tests:**

```bash
python -m unittest weslr.test_<layer> -v
```

---

## 2. REQUIRED TEST CATEGORIES

Each WESLR layer must pass all four test categories:

| Category | Class Prefix | Purpose |
|----------|--------------|---------|
| Model Tests | `Test<Layer>Model` | Data models, enums, serialization |
| Behavior Tests | `Test<Layer>Behavior` | Public method behavior from operator perspective |
| Integration Tests | `Test<Layer>Integration` | Layer hooks into WESLR correctly |
| Backward Compatibility Tests | `Test<Layer>BackwardCompatibility` | Existing functionality preserved |

---

## 3. PASSING REQUIREMENTS

- **All tests must pass** before commit/merge
- **No skipping** of tests just to make suite pass
- **No weakening tests** to match incorrect behavior
- If expectations changed, report why in commit message

---

## 4. TELEMETRY-SPECIFIC RULES (v68)

For the Distributed Execution Telemetry layer:

- Tests must validate intended behavior, not current implementation accidents
- `skip_handshake=True` paths must NOT expect handshake telemetry
- Telemetry must remain passive and must not drive execution logic
- No weakening tests just to make suite pass
- If expectations changed, report why

---

## 5. VIOLATIONS (Rejected)

These are explicit violations and should be rejected:

- Skipping tests to make code changes easier
- Updating tests to match incorrect behavior
- Adding layers without all four test categories
- Breaking backward compatibility without documentation
- Running tests with `skip_handshake=True` expecting handshake telemetry

---

## 6. SUMMARY REPORTING

### 6.1 Test Run Output

```
Ran X tests in Ys

OK (all passing)
# OR
FAILED (failures=Z)
```

### 6.2 Commit Message Test Summary

Include test summary in commit message:

```
v68: Distributed Execution Telemetry Layer - Passive observability for distributed execution flow

- Flow lifecycle event emission (FLOW_CREATED, FLOW_COMPLETED, FLOW_FAILED, FLOW_CANCELLED, FLOW_REJECTED, FLOW_ROLLBACK_*)
- Handshake success/failure metrics
- Deadline breach metrics
- Dispatch/receipt timing metrics
- Rollback/failure metrics
- Audit export hooks for JSON export
- Correlation by flow/request/session IDs
- TelemetryObserver for passive hooking into execution objects
- No flow control, passive observability only
- No backend/service, no scheduler, no consensus
- All 61 tests pass
```

---

*WESLR Operator Test Execution Rules v1.0.0*
*Last updated: 2026-04-07*
*Created during: operator_testing_rules_repair*
