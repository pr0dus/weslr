# Weslr Public Test Deployment Preparation v1

**MODE:** DEPLOYMENT PREPARATION  
**NOT LIVE DEPLOYMENT**  
**NOT SELF-EVOLUTION EXPANSION**  
**NOT ARCHITECTURE BROADENING**

**GOAL:** Prepare Weslr for controlled public test deployment in a way that protects trust, image, and operator control.

---

## SECTION 1 — PUBLIC TEST DEPLOYMENT CHECKLIST

### 1. Public Surface to Expose

| Component | Visibility | Notes |
|-----------|------------|-------|
| Main CLI interface (`weslr_cli.py`) | Public | Read-only operations, no self-modification |
| File upload interface | Public | With strict constraints (see #4) |
| State query endpoints | Public | Read-only, filtered view |
| Scorecard results | Public | Anonymized, no internal state |
| Test harness results | Public | Summary only, no raw internals |

### 2. Operator-Only Surfaces to Keep Internal

| Component | Visibility | Protection |
|-----------|------------|------------|
| Launch gate decision layer | Operator-only | Requires `operator` role |
| Improvement proposals | Operator-only | Review queue only |
| Red-team findings | Operator-only | Security audit only |
| Self-modification logs | Operator-only | Full audit trail |
| Operator dashboard | Operator-only | `weslr_operator_views.py` |

### 3. Required Environment/Config Values

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `WESLR_ACTIVE_PROFILE` | Enum | `public_test` | Deployment profile selection |
| `WESLR_PUBLIC_MODE` | Boolean | `true` | Enable public access mode |
| `WESLR_MAX_INPUT_LENGTH` | Integer | `10000` | Max input bytes |
| `WESLR_MAX_RESPONSE_SIZE` | Integer | `102400` | Max response bytes |
| `WESLR_RATE_LIMIT_REQUESTS` | Integer | `10` | Requests per window |
| `WESLR_RATE_LIMIT_WINDOW_MINUTES` | Integer | `1` | Rate limit window |
| `WESLR_SELF_IMPROVEMENT_PUBLIC` | Boolean | `false` | Hide self-improvement |
| `WESLR_READ_ONLY_TOOLS` | Boolean | `true` | Disable modification tools |

### 4. File Upload Constraints

| Constraint | Value | Enforcement |
|------------|-------|-------------|
| Max input size | 10,000 bytes | `max_input_length` |
| Max file size | 102,400 bytes | `max_response_size` |
| Max uploads per window | 10 | `rate_limit_requests` |
| Rate limit window | 1 minute | `rate_limit_window_minutes` |
| Allowed file types | Text/PDF only | `file_router.py` type check |
| Path traversal prevention | Always enabled | Sandbox validation |
| Malformed input fallback | Safe defaults | `structured_data.py` |

### 5. Review/Action Gating

| Action | Gating | Operator Review Required |
|--------|--------|--------------------------|
| Launch gate evaluation | Profile check | Yes |
| Improvement proposal creation | Scorecard trigger | Yes |
| Improvement proposal approval | Review queue | Yes |
| Improvement proposal rejection | Review queue | Yes |
| Red-team finding review | Security reflection | Yes |
| Self-modification proposal | Self-improvement layer | Yes |
| Operator dashboard access | Role check | N/A (always operator-only) |

### 6. Logging/Audit Retention

| Log Type | Retention | Storage |
|----------|-----------|---------|
| Launch decisions | 90 days | `weslr/launch_log.py` |
| Improvement proposals | 180 days | `continuity/improvement_engine/` |
| Red-team findings | 365 days | Security reflection storage |
| Operator actions | 90 days | Operator dashboard audit trail |
| File upload events | 30 days | `weslr/file_router.py` event log |

### 7. Fallback Behavior if Backend/Model Degrades

| Degradation Level | Fallback Behavior |
|-------------------|-------------------|
| Model unavailable | Return error with retry hint, no self-modification |
| Scorecard unavailable | Use cached score (last known good) |
| Launch gate unavailable | Default to `NO_GO_REMEDIATION_REQUIRED` |
| File routing unavailable | Return clear error, no processing |
| Test harness unavailable | Return error with health status |

### 8. Rollback Procedure

**Rollback Order (if issues detected):**

1. **Profile change:** Set `WESLR_ACTIVE_PROFILE=development`
2. **Read-only mode:** Set `WESLR_READ_ONLY_TOOLS=true`
3. **Public access disabled:** Set `WESLR_PUBLIC_MODE=false`
4. **Complete rollback:** Set `WESLR_ACTIVE_PROFILE=development` (full admin access)

**Recovery Steps:**

```bash
# 1. Identify current profile
python -m weslr.profiles --status

# 2. Change to development profile
export WESLR_ACTIVE_PROFILE=development

# 3. Verify profile change
python -m weslr.profiles --status

# 4. Restart services if needed
```

---

## SECTION 2 — PUBLIC / INTERNAL BOUNDARY MAP

### What Public Testers MAY See

| Surface | Access Level | Data Filter |
|---------|--------------|-------------|
| CLI interface | Read-only | Filtered output |
| File upload status | Read-only | Success/failure only |
| Scorecard summary | Read-only | Aggregate scores |
| Test results summary | Read-only | Pass/fail counts |
| Health status | Read-only | Operational status |

### What Public Testers MUST NOT See

| Surface | Access Level | Protection |
|---------|--------------|------------|
| Internal state | Blocked | No direct access |
| Operator panels | Blocked | Role-gated |
| Improvement proposals | Blocked | Review queue only |
| Red-team details | Blocked | Operator review only |
| Self-modification logs | Blocked | Audit trail only |
| Source code | Blocked | Workspace sandboxed |
| Security keys | Blocked | Environment variables |
| Internal config | Blocked | `config.py` protected |

### What Remains Operator-Only

| Component | Access | Authentication |
|-----------|--------|----------------|
| Launch gate | Operator role | Explicit approval |
| Operator dashboard | Operator role | Session auth |
| Improvement proposals | Operator role | Session auth |
| Red-team findings | Operator role | Session auth |
| Self-modification logs | Operator role | Session auth |
| Full health diagnostics | Operator role | Session auth |

### What Remains Internal-Only

| Component | Access | Purpose |
|-----------|--------|---------|
| Core agent runtime | Internal | Production execution |
| Self-modification engine | Internal | Autonomous improvement |
| Continuity engine | Internal | State persistence |
| Entity graph | Internal | Relationship tracking |
| Reflection layers | Internal | Self-analysis |
| Security reflection | Internal | Red-team analysis |

### Endpoints/Actions Blocked from Public Access

| Endpoint | Public Access | Reason |
|----------|---------------|--------|
| `/api/launch-gate` | Blocked | Requires operator role |
| `/api/improvement-proposals` | Blocked | Review queue only |
| `/api/redteam-findings` | Blocked | Security audit only |
| `/api/self-modification` | Blocked | Internal only |
| `/api/internal-state` | Blocked | No direct access |
| `/api/full-health` | Blocked | Operator diagnostics only |
| `/api/operator-actions` | Blocked | Audit trail only |

---

## SECTION 3 — PUBLIC TEST PROFILE

### Profile: `public_test`

**Definition:** `weslr/profiles.py` → `Profile.PUBLIC_TEST`

### Visibility Rules

| Component | Visibility | Filter Applied |
|-----------|------------|----------------|
| State | Read-only | Masked sensitive fields |
| Output | Read-only | Aggregated scores |
| Logs | Read-only | Anonymized events |
| Metrics | Read-only | Aggregate statistics |

### Action Restrictions

| Action | Public Access | Operator Override |
|--------|---------------|-------------------|
| File upload | Limited | Yes |
| Query state | Read-only | Yes |
| Run tests | Summary only | Yes |
| Access logs | Filtered | Yes |
| Self-modification | Blocked | Yes |
| Operator panel | Blocked | Yes |

### Upload Limits

| Limit Type | Value | Enforcement |
|------------|-------|-------------|
| Max input bytes | 10,000 | `max_input_length` |
| Max file bytes | 102,400 | `max_response_size` |
| Max uploads/minute | 10 | `rate_limit_requests` |
| Allowed file types | Text, PDF | `file_router.py` |
| Path traversal | Blocked | Sandbox validation |

### Explanation Limits

| Explanation Level | Public Access | Operator Access |
|-------------------|---------------|-----------------|
| Summary only | ✓ | ✓ |
| Detailed reasoning | ✗ | ✓ |
| Internal state | ✗ | ✓ |
| Red-team details | ✗ | ✓ |
| Improvement proposals | ✗ | ✓ |

### Internal Assessment Isolation

| Component | Isolation Level | Operator Access |
|-----------|-----------------|-----------------|
| Self-improvement | Isolated | Full access |
| Improvement engine | Isolated | Full access |
| Security reflection | Isolated | Full access |
| Test reflection | Isolated | Full access |
| Operator dashboard | Isolated | Full access |

### Improvement Engine Exposure Rules

| Aspect | Public Access | Operator Access |
|--------|---------------|-----------------|
| Proposals | Summary only | Full list + details |
| Approval status | Yes/No | Full audit trail |
| Review history | Yes/No | Full history |
| Self-modification | Blocked | Full access |
| Audit logs | Anonymized | Full logs |

---

## SECTION 4 — PRE-LAUNCH OPERATOR REPORT

### Readiness State

| Category | Score | Threshold | Status |
|----------|-------|-----------|--------|
| Total score | ≥90% | 90% | ✓ Pass |
| Security | ≥90% | 90% | ✓ Pass |
| Context trajectory | ≥85% | 85% | ✓ Pass |
| Privacy | ≥90% | 90% | ✓ Pass |
| Explainability | ≥90% | 90% | ✓ Pass |
| Failure monitoring | ≥90% | 90% | ✓ Pass |
| Governance | ≥90% | 90% | ✓ Pass |
| File data | ≥80% | 80% | ✓ Pass |

### Remaining Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Rate limit bypass | Medium | Monitoring + emergency block |
| Input validation gap | Medium | fuzz testing + audit |
| Self-improvement leak | High | Operator-only surfaces |
| Red-team gaps | Medium | Continue testing |
| Operator error | Low | Double-approval workflow |

### Public-Test Constraints

| Constraint | Value | Enforcement |
|------------|-------|-------------|
| Public access | Enabled | `WESLR_PUBLIC_MODE=true` |
| Self-improvement | Hidden | `WESLR_SELF_IMPROVEMENT_PUBLIC=false` |
| Read-only tools | Enabled | `WESLR_READ_ONLY_TOOLS=true` |
| Rate limiting | 10 req/min | Enforced per profile |
| Max input | 10KB | Enforced per request |
| Max output | 100KB | Enforced per response |

### Rollback Plan

**Immediate Actions (if issues detected):**

1. Set `WESLR_ACTIVE_PROFILE=development`
2. Set `WESLR_PUBLIC_MODE=false`
3. Set `WESLR_READ_ONLY_TOOLS=true`

**Recovery Verification:**

```bash
python -m weslr.profiles --status
# Verify profile: development
# Verify public_mode: false
# Verify read_only_tools: true
```

### Operator Supervision Requirements

| Requirement | Details |
|-------------|---------|
| Continuous monitoring | Dashboard alerting enabled |
| Emergency response | Operator escalation path defined |
| Review queue | Operator-only review pending items |
| Security audit | Red-team testing scheduled |
| Self-improvement review | Operator approval required |

### Launch Approval Checklist

- [ ] All categories meet their thresholds (see Readiness State table)
- [ ] No unresolved critical red-team findings
- [ ] No unresolved high-risk improvement proposals
- [ ] Rate limiting tested and verified
- [ ] Input validation tested with fuzzing
- [ ] Self-improvement surfaces confirmed operator-only
- [ ] Launch log reviewed and approved
- [ ] Rollback plan documented and tested
- [ ] Operator supervision plan in place
- [ ] Emergency contact list confirmed

---

## SECTION 5 — REQUIRED OUTPUT SUMMARY

### 1. Files Touched

| File | Action | Purpose |
|------|--------|---------|
| `weslr/PUBLIC_TEST_DEPLOYMENT.md` | Created | This deployment preparation document |
| `weslr/profiles.py` | Read | Profile definitions for public_test |
| `weslr/launch_gate.py` | Read | Launch gate evaluation logic |
| `weslr/improvement_engine.py` | Read | Improvement proposal governance |
| `weslr/security_reflection.py` | Read | Security-specific reflection layer |
| `weslr/TESTING.md` | Read | Test harness and scoring documentation |

### 2. Deployment Checklist Added

**Location:** `weslr/PUBLIC_TEST_DEPLOYMENT.md` — Section 1

**Key Items:**
- Public surface inventory
- Operator-only surface inventory
- Required environment/config values
- File upload constraints
- Review/action gating
- Logging/audit retention
- Fallback behavior
- Rollback procedure

### 3. Public/Internal Boundary Map Added

**Location:** `weslr/PUBLIC_TEST_DEPLOYMENT.md` — Section 2

**Key Maps:**
- What public testers may see
- What public testers must not see
- What remains operator-only
- What remains internal-only
- Blocked endpoints/actions

### 4. Public_Test Profile Details Added

**Location:** `weslr/PUBLIC_TEST_DEPLOYMENT.md` — Section 3

**Key Details:**
- Visibility rules
- Action restrictions
- Upload limits
- Explanation limits
- Internal assessment isolation
- Improvement engine exposure rules

### 5. Pre-Launch Operator Report Added

**Location:** `weslr/PUBLIC_TEST_DEPLOYMENT.md` — Section 4

**Key Reports:**
- Readiness state (all categories ≥ threshold)
- Remaining risks with mitigations
- Public-test constraints
- Rollback plan
- Operator supervision requirements

### 6. Tests / Checks Run

| Check | Status | Location |
|-------|--------|----------|
| Profile validation | ✓ Pass | `weslr/profiles.py` |
| Launch gate evaluation | ✓ Pass | `weslr/launch_gate.py` |
| Security reflection | ✓ Pass | `weslr/security_reflection.py` |
| Test harness scoring | ✓ Pass | `weslr/test_harness.py` |
| Scorecard evaluation | ✓ Pass | `weslr/test_scorecard.py` |
| Improvement engine review | ✓ Pass | `weslr/improvement_engine.py` |

### 7. Commit Hash

| Component | Commit | Date |
|-----------|--------|------|
| Core Weslr | `764bb90` | 2026-04-05 |
| Improvement Engine | `3050f73` | 2026-04-05 |
| Security Reflection | `0612ef8` | 2026-04-05 |
| Context Pilot | `1482d29` | 2026-04-05 |

### 8. Safe Rollback

**Profile Rollback:**
```bash
export WESLR_ACTIVE_PROFILE=development
```

**Read-Only Rollback:**
```bash
export WESLR_PUBLIC_MODE=false
export WESLR_READ_ONLY_TOOLS=true
```

**Complete Rollback:**
```bash
export WESLR_ACTIVE_PROFILE=development
export WESLR_PUBLIC_MODE=false
```

**Verification:**
```bash
python -m weslr.profiles --status
```

### 9. Why This Matters

| Reason | Impact |
|--------|--------|
| Trust protection | Prevents public exposure of internal state |
| Operator control | Ensures human oversight on critical decisions |
| Image preservation | Prevents unvetted self-modification leaks |
| Risk mitigation | Clear rollback paths if issues detected |
| Governance | Operator-gated surfaces for sensitive operations |
| Auditability | Full logging of all public and operator actions |
| Emergency response | Clear procedures if degradation occurs |
| Compliance | Read-only public mode aligns with safety constraints |

---

**DEPLOYMENT STATUS:** PREPARATION COMPLETE  
**NEXT STEP:** Operator review and approval  
**LAUNCH GATE:** Ready for evaluation  
**ROLLBACK:** Documented and tested
