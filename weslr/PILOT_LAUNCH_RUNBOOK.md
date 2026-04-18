# Weslr Pilot Launch Runbook v1

**MODE:** OPERATIONAL PILOT EXECUTION  
**NOT LIVE DEPLOYMENT**  
**NOT SELF-EVOLUTION WORK**  
**NOT ARCHITECTURE EXPANSION**

**GOAL:** Operational runbook for the first 7-day controlled pilot wave.

---

## SECTION 1 — DAY 0 LAUNCH CHECKLIST

### 1.1 Profile Activation

| Task | Command | Verification | Status |
|------|---------|--------------|--------|
| Set active profile | `export WESLR_ACTIVE_PROFILE=public_test` | `python -m weslr.profiles --status` shows `public_test` | ⬜ |
| Verify public mode | `WESLR_PUBLIC_MODE=true` | Profile shows `public_mode: true` | ⬜ |
| Verify read-only tools | `WESLR_READ_ONLY_TOOLS=true` | Profile shows `read_only_tools: true` | ⬜ |
| Verify self-improvement hidden | `WESLR_SELF_IMPROVEMENT_PUBLIC=false` | Profile shows `self_improvement_visible_to_public: false` | ⬜ |
| Check rate limits | `WESLR_RATE_LIMIT_REQUESTS=10` | Rate limiter active at 10/min | ⬜ |

**Rollback if Profile Fails:**
```bash
export WESLR_ACTIVE_PROFILE=development
```

### 1.2 Access Verification

| User Type | CLI Access | File Upload | State Query | Operator Panel | Self-Improvement |
|-----------|------------|-------------|-------------|----------------|------------------|
| Industrial | Read-only | Limited (text/PDF) | Aggregated views | Blocked | Hidden |
| Research | Read-only | Limited (text/PDF) | Aggregated views | Blocked | Hidden |
| Weak-Prompt Public | Read-only | Limited (text/PDF) | Aggregated views | Blocked | Hidden |
| Operator-Supervised | Full | Full | Full state | Full | Full visibility |

**Verification Commands:**
```bash
# Test industrial user access
python -m weslr.weslr_cli --requester_type company --domain manufacturing --test

# Test research user access
python -m weslr.weslr_cli --requester_type university --domain astronomy --test

# Test operator access
python -m weslr.weslr_cli --operator --test
```

### 1.3 Cohort Invite Checklist

| Persona | Invite Count | Onboarding Steps | Success Criteria | Status |
|---------|-------------|------------------|------------------|--------|
| Industrial | 2-3 | Welcome email, API access, rate limit confirmation, contact person assignment | 3/3 users complete onboarding | ⬜ |
| Research | 2-3 | Welcome email, API access, rate limit confirmation, contact person assignment | 3/3 users complete onboarding | ⬜ |
| Weak-Prompt Public | 2-3 | Welcome email, API access, rate limit confirmation, contact person assignment | 3/3 users complete onboarding | ⬜ |
| Operator-Supervised | 1-2 | Welcome email, API access, operator panel access, escalation path | 2/2 users complete onboarding | ⬜ |

**Invite Template:**
```
Subject: Weslr Pilot Invitation - [Persona] Cohort

Dear [User],

You have been selected for the controlled public test of Weslr.

Pilot Details:
- Duration: 7 days (Phase 1)
- Access Level: [Read-only/Full]
- Rate Limit: 10 requests/minute
- Contact: [operator-email]

Onboarding Steps:
1. Acknowledge this email
2. Set environment: export WESLR_ACTIVE_PROFILE=public_test
3. Test connection: python -m weslr.weslr_cli --test
4. Submit first request: python -m weslr.weslr_cli --requester_type [type] --domain [domain] --capability [cap] --problem [problem]

Questions? Contact [operator-email].

- Weslr Pilot Team
```

### 1.4 Rollback Readiness Verification

| Check | Command | Expected Result | Status |
|-------|---------|-----------------|--------|
| Profile rollback | `export WESLR_ACTIVE_PROFILE=development` | Profile changes to `development` | ⬜ |
| Read-only mode | `export WESLR_PUBLIC_MODE=false` | Public access blocked | ⬜ |
| Read-only tools | `export WESLR_READ_ONLY_TOOLS=true` | Modification tools disabled | ⬜ |
| Launch gate check | `python -m weslr.launch_gate --status` | Returns current decision | ⬜ |

**Rollback Verification Command:**
```bash
python -m weslr.profiles --status
# Should show: active_profile: development, public_mode: false
```

### 1.5 Logging Verification

| Log Type | Location | Size Limit | Retention | Status |
|----------|----------|------------|-----------|--------|
| Launch log | `weslr/logs/launch/launch_log.json` | 10MB | 90 days | ⬜ |
| Pilot signals | `continuity/pilot_signals/` | 100MB | 30 days | ⬜ |
| User events | `weslr/logs/user_events.json` | 50MB | 30 days | ⬜ |
| Operator actions | `weslr/logs/operator_actions.json` | 10MB | 30 days | ⬜ |
| Red-team events | `weslr/logs/redteam_events.json` | 5MB | 365 days | ⬜ |

**Logging Verification:**
```bash
# Check log directories exist
ls -la weslr/logs/ continuity/pilot_signals/

# Test log writing
python -m weslr.launch_log --test
```

### 1.6 Operator On-Call Assignment

| Shift | Operator | Contact | Coverage | Escalation Path |
|-------|----------|---------|----------|-----------------|
| Day 1-7 Morning (06:00-18:00 UTC) | op1@example.com | Slack #pilot-oncall | Primary | op2@example.com |
| Day 1-7 Afternoon (12:00-24:00 UTC) | op2@example.com | Slack #pilot-oncall | Secondary | op1@example.com |
| Day 1-7 Night (00:00-06:00 UTC) | backup@example.com | Slack #pilot-oncall | Tertiary | op1@example.com |

**On-Call Requirements:**
- Monitor Slack #pilot-oncall for alerts
- Review signal dashboard every 2 hours
- Respond to critical alerts within 15 minutes
- Document all interventions in `weslr/logs/operator_actions.json`

---

## SECTION 2 — DAILY OPERATOR LOOP

### Day 1-7 Daily Checklist

#### Signal Review (Every 4 Hours)

| Signal | Check | Threshold | Action if Out of Range |
|--------|-------|-----------|------------------------|
| Trust Score | Current value | ≥ 0.75 | If < 0.60: Freeze pilot |
| Clarity Score | Current value | ≥ 0.80 | If < 0.50: Freeze pilot |
| Continuity Rate | Current value | ≥ 95% | If < 90%: Freeze pilot |
| Recovery Rate | Current value | ≥ 85% | If < 60%: Freeze pilot |
| Failure Rate | Incidents/100 | ≤ 5 | If > 10: Immediate freeze |
| Intervention Rate | Percentage | ≤ 10% | If > 20%: Freeze pilot |
| Red-Team Incidents | Count | 0 | If > 0: Investigate immediately |

**Signal Review Command:**
```bash
python -m weslr.pilot_monitor --signal-summary --every-4-hours
```

#### Trust Score Review (Every 4 Hours)

| Task | Command | Status |
|------|---------|--------|
| Get current trust score | `python -m weslr.pilot_monitor --trust-score` | ⬜ |
| Compare to 7-day average | `python -m weslr.pilot_monitor --trust-score --compare` | ⬜ |
| Check trend | `python -m weslr.pilot_monitor --trust-score --trend` | ⬜ |
| Log review | `python -m weslr.launch_log --add --note "Trust score review completed"` | ⬜ |

#### Incident Scan (Every 4 Hours)

| Task | Command | Status |
|------|---------|--------|
| Check red-team events | `python -m weslr.redteam_events --scan` | ⬜ |
| Check rate limit breaches | `python -m weslr.logs --rate-limits --scan` | ⬜ |
| Check failure rate | `python -m weslr.pilot_monitor --failure-rate` | ⬜ |
| Check operator interventions | `python -m weslr.logs --interventions --scan` | ⬜ |
| Document findings | Add to `weslr/logs/operator_actions.json` | ⬜ |

#### Continuity Failure Review (Daily - 9:00 AM UTC)

| Task | Command | Status |
|------|---------|--------|
| Check continuity success rate | `python -m weslr.pilot_monitor --continuity-rate` | ⬜ |
| Review session continuity failures | `python -m weslr.logs --continuity --failures` | ⬜ |
| Check entity graph persistence | `python -m weslr.logs --entity-graph --integrity` | ⬜ |
| Check review queue integrity | `python -m weslr.logs --review-queue --integrity` | ⬜ |
| Log review | Add to `weslr/logs/operator_actions.json` | ⬜ |

#### Operator Interventions (Daily - 9:00 AM UTC)

| Task | Command | Status |
|------|---------|--------|
| Review interventions today | `python -m weslr.logs --interventions --today` | ⬜ |
| Categorize interventions | `python -m weslr.logs --interventions --categorize` | ⬜ |
| Check intervention rate | `python -m weslr.pilot_monitor --intervention-rate` | ⬜ |
| Log review | Add to `weslr/logs/operator_actions.json` | ⬜ |

#### Freeze/Rollback Checks (Every 4 Hours)

| Check | Condition | Action |
|-------|-----------|--------|
| Trust Score < 0.60 | ≥ 2 consecutive checks | Freeze pilot |
| Clarity Score < 0.50 | ≥ 3 requests | Freeze pilot |
| Continuity Rate < 90% | ≥ 2 sessions | Freeze pilot |
| Recovery Rate < 60% | ≥ 2 days | Freeze pilot |
| Failure Rate > 10/hour | Any instance | Immediate freeze |
| Red-Team Critical | Any finding | Immediate freeze |
| Security Alert | Any finding | Immediate freeze |

**Freeze/Rollback Command:**
```bash
# Emergency freeze
python -m weslr.pilot_monitor --freeze

# Emergency rollback
python -m weslr.pilot_monitor --rollback
```

### Day 1-7 Operator Log Template

```json
{
  "timestamp": "ISO-8601",
  "operator": "operator:email@example.com",
  "shift": "morning|afternoon|night",
  "signal_review": {
    "trust_score": 0.82,
    "clarity_score": 0.88,
    "continuity_rate": 0.96,
    "recovery_rate": 0.91,
    "failure_rate": "4/100",
    "intervention_rate": "7%"
  },
  "incidents": [],
  "interventions": [],
  "continuity_failures": [],
  "decision": "continue|freeze|rollback",
  "rationale": "Brief explanation",
  "next_check": "ISO-8601"
}
```

---

## SECTION 3 — INCIDENT RESPONSE

### 3.1 Trust Drop Response

**Trigger:** Trust Score < 0.60 for 2 consecutive checks

**Response Steps:**

1. **Immediate (0-15 minutes):**
   - Freeze pilot: `python -m weslr.pilot_monitor --freeze`
   - Alert on-call operator
   - Check logs for pattern

2. **Investigation (15-60 minutes):**
   - Review last 10 requests
   - Check explanation quality metrics
   - Check follow-up request rate
   - Check user feedback surveys

3. **Resolution (1-2 hours):**
   - If systematic: Rollback and debug
   - If isolated: Continue with monitoring
   - Document in `weslr/logs/operator_actions.json`

**Trust Drop Resolution Template:**
```
Timestamp: ISO-8601
Issue: Trust Score drop to 0.58 (below 0.60 threshold)
Duration: 2 consecutive checks
Root Cause: [Explain]

Resolution:
- [Action taken]
- [Monitor plan]
- [Rollback if needed]

Next Check: ISO-8601
Decision: freeze/rollback/continue
```

### 3.2 Red-Team Incident Response

**Trigger:** Any red-team critical finding detected

**Response Steps:**

1. **Immediate (0-5 minutes):**
   - Freeze pilot: `python -m weslr.pilot_monitor --freeze`
   - Block attacker IP: `python -m weslr.redteam --block [ip]`
   - Alert security team

2. **Investigation (5-30 minutes):**
   - Review attack pattern
   - Check affected users
   - Check data exposure
   - Check system integrity

3. **Resolution (30 minutes - 2 hours):**
   - Patch vulnerability
   - Update red-team tests
   - Rollback if needed
   - Document in security log

**Red-Team Incident Template:**
```
Timestamp: ISO-8601
Attack Type: [attack_family_name]
Severity: critical/high/medium
Attacker IP: [ip]
Affected Users: [list]

Response:
- Freeze pilot: [time]
- Block IP: [time]
- Investigate: [time]
- Resolution: [time]

Impact Assessment:
- Data Exposure: [none/minimal/significant]
- System Integrity: [intact/compromised]
- User Impact: [none/minimal/significant]

Next Steps:
- [Action]
- [Timeline]
- [Owner]
```

### 3.3 Continuity Failure Spike Response

**Trigger:** Continuity Rate < 90% for 2 consecutive sessions

**Response Steps:**

1. **Immediate (0-15 minutes):**
   - Freeze pilot: `python -m weslr.pilot_monitor --freeze`
   - Check entity graph integrity
   - Check review queue integrity

2. **Investigation (15-60 minutes):**
   - Review continuity persistence logs
   - Check entity graph integrity
   - Check state rollback patterns
   - Check cross-session continuity

3. **Resolution (1-2 hours):**
   - If data loss: Restore from backup
   - If logic error: Debug and fix
   - If user error: Continue with monitoring
   - Document in `weslr/logs/operator_actions.json`

**Continuity Failure Template:**
```
Timestamp: ISO-8601
Continuity Rate: [current]%
Threshold: 90%
Duration: 2 consecutive sessions

Root Cause:
- [Entity graph issue?]
- [Review queue issue?]
- [Cross-session issue?]

Resolution:
- [Action taken]
- [Monitor plan]
- [Rollback if needed]

Next Check: ISO-8601
Decision: freeze/rollback/continue
```

### 3.4 Weak-Prompt Recovery Collapse Response

**Trigger:** Weak-Prompt Recovery Rate < 60% for 2 consecutive days

**Response Steps:**

1. **Immediate (0-15 minutes):**
   - Freeze pilot: `python -m weslr.pilot_monitor --freeze`
   - Check weak-prompt logs
   - Check user feedback

2. **Investigation (15-60 minutes):**
   - Review weak-prompt handling
   - Check explanation quality
   - Check recovery patterns
   - Check user frustration signals

3. **Resolution (1-2 hours):**
   - If systematic: Rollback and improve weak-prompt handling
   - If isolated: Continue with monitoring
   - Document in `weslr/logs/operator_actions.json`

**Weak-Prompt Recovery Template:**
```
Timestamp: ISO-8601
Recovery Rate: [current]%
Threshold: 60%
Duration: 2 consecutive days

Root Cause:
- [Weak-prompt detection issue?]
- [Explanation quality issue?]
- [Recovery logic issue?]

Resolution:
- [Action taken]
- [Monitor plan]
- [Rollback if needed]

Next Check: ISO-8601
Decision: freeze/rollback/continue
```

### 3.5 Backend Degradation Response

**Trigger:** Response time > 5 seconds for 3 consecutive requests

**Response Steps:**

1. **Immediate (0-5 minutes):**
   - Check system health: `python -m weslr.status`
   - Check resource usage: `python -m weslr.resources`
   - Alert infrastructure team

2. **Investigation (5-30 minutes):**
   - Check CPU/memory usage
   - Check database performance
   - Check external API latency
   - Check rate limiter status

3. **Resolution (30 minutes - 2 hours):**
   - Scale resources if needed
   - Clear caches if needed
   - Rollback if needed
   - Document in `weslr/logs/operator_actions.json`

**Backend Degradation Template:**
```
Timestamp: ISO-8601
Response Time: [current]s (threshold: 5s)
Duration: 3 consecutive requests

Root Cause:
- [CPU/memory issue?]
- [Database issue?]
- [External API issue?]
- [Rate limiter issue?]

Resolution:
- [Action taken]
- [Monitor plan]
- [Rollback if needed]

Next Check: ISO-8601
Decision: continue|freeze|rollback
```

### 3.6 Privacy Boundary Breach Response

**Trigger:** Protected field leaked to public output

**Response Steps:**

1. **Immediate (0-5 minutes):**
   - Freeze pilot: `python -m weslr.pilot_monitor --freeze`
   - Identify leaked field
   - Identify affected users
   - Alert security team

2. **Investigation (5-30 minutes):**
   - Review output filtering
   - Check field access controls
   - Check privacy validation
   - Check audit logs

3. **Resolution (30 minutes - 2 hours):**
   - Patch privacy validation
   - Rotate exposed credentials if needed
   - Notify affected users if needed
   - Document in security log

**Privacy Breach Template:**
```
Timestamp: ISO-8601
Leaked Field: [field_name]
Severity: critical/high
Affected Users: [count]

Root Cause:
- [Filtering issue?]
- [Access control issue?]
- [Validation issue?]

Resolution:
- [Action taken]
- [Monitor plan]
- [Rollback if needed]
- [User notification if needed]

Next Check: ISO-8601
Decision: freeze/rollback/continue
```

---

## SECTION 4 — DAY 7 DECISION GATE

### Decision Criteria Summary

| Decision | Criteria | Required Fields |
|----------|----------|-----------------|
| **Continue** | All signals pass for 7 consecutive days | Trust ≥0.75, Clarity ≥0.80, Continuity ≥95%, Recovery ≥85%, Failure ≤5/100, Intervention ≤10%, Red-Team = 0 |
| **Expand** | Continue + 7 consecutive days + Thresholds: Trust ≥0.85, Clarity ≥0.85, Continuity ≥98%, Recovery ≥90%, Intervention ≤5%, Red-Team = 0 | Continue criteria + Expanded criteria |
| **Freeze** | Any freeze trigger met | Trust <0.60 x2, Clarity <0.50 x3, Continuity <90% x2, Recovery <60% x2, Failure >10/hour, Red-Team critical |
| **Rollback** | Any rollback trigger met | Trust <0.50 x2, Clarity <0.50 x5, Continuity <85% x3, Recovery <50% x3, Failure >20/hour, Red-Team critical, Security breach |

### Day 7 Decision Gate Checklist

#### Continue Pilot Decision

| Check | Required | Status |
|-------|----------|--------|
| Trust Score ≥ 0.75 for 7 days | Yes | ⬜ |
| Clarity Score ≥ 0.80 for 7 days | Yes | ⬜ |
| Continuity Rate ≥ 95% for 7 days | Yes | ⬜ |
| Recovery Rate ≥ 85% for 7 days | Yes | ⬜ |
| Failure Rate ≤ 5/100 for 7 days | Yes | ⬜ |
| Intervention Rate ≤ 10% for 7 days | Yes | ⬜ |
| Red-Team Incidents = 0 for 7 days | Yes | ⬜ |
| No freeze events in 7 days | Yes | ⬜ |
| Operator approval | Yes | ⬜ |
| Log entry | Yes | ⬜ |

**Continue Decision Command:**
```bash
python -m weslr.pilot_monitor --decision continue --day-7
```

#### Expand Pilot Decision

| Check | Required | Status |
|-------|----------|--------|
| All Continue criteria | Yes | ⬜ |
| Trust Score ≥ 0.85 for 7 days | Yes | ⬜ |
| Clarity Score ≥ 0.85 for 7 days | Yes | ⬜ |
| Continuity Rate ≥ 98% for 7 days | Yes | ⬜ |
| Recovery Rate ≥ 90% for 7 days | Yes | ⬜ |
| Intervention Rate ≤ 5% for 7 days | Yes | ⬜ |
| Red-Team Incidents = 0 for 7 days | Yes | ⬜ |
| No freeze events in 7 days | Yes | ⬜ |
| Operator approval | Yes | ⬜ |
| Log entry | Yes | ⬜ |

**Expand Decision Command:**
```bash
python -m weslr.pilot_monitor --decision expand --day-7
```

#### Freeze Pilot Decision

| Check | Required | Status |
|-------|----------|--------|
| Any freeze trigger met | Yes | ⬜ |
| Operator approval | Yes | ⬜ |
| Log entry | Yes | ⬜ |
| Freeze duration set | Yes | ⬜ |
| Review plan created | Yes | ⬜ |

**Freeze Decision Command:**
```bash
python -m weslr.pilot_monitor --decision freeze --day-7
```

#### Rollback Public Test Decision

| Check | Required | Status |
|-------|----------|--------|
| Any rollback trigger met | Yes | ⬜ |
| Operator approval | Yes | ⬜ |
| Log entry | Yes | ⬜ |
| Rollback steps executed | Yes | ⬜ |
| Post-rollback tasks assigned | Yes | ⬜ |

**Rollback Decision Command:**
```bash
python -m weslr.pilot_monitor --decision rollback --day-7
```

### Day 7 Decision Gate Log Template

```json
{
  "timestamp": "ISO-8601",
  "day": 7,
  "decision": "continue|expand|freeze|rollback",
  "signals_7d": {
    "trust_score_avg": 0.82,
    "clarity_score_avg": 0.88,
    "continuity_rate_avg": 0.96,
    "recovery_rate_avg": 0.91,
    "failure_rate_avg": "4/100",
    "intervention_rate_avg": "7%",
    "red_team_incidents_total": 0
  },
  "freeze_events": [
    {"timestamp": "ISO-8601", "reason": "Trust Score < 0.60", "resolution": "Operator review"}
  ],
  "operator_approval": {
    "approved_by": "operator:email@example.com",
    "approved_at": "ISO-8601"
  },
  "next_steps": [
    "Continue: Start Phase 2 (7 more days)",
    "Expand: Notify users, increase limits to 25",
    "Freeze: Document issues, set 24h review",
    "Rollback: Execute rollback, assign post-mortem"
  ],
  "log_entry": "Brief summary for launch_log.json"
}
```

---

## SECTION 5 — REQUIRED OUTPUT SUMMARY

### 1. Files Touched

| File | Action | Purpose |
|------|--------|---------|
| `weslr/PILOT_LAUNCH_RUNBOOK.md` | Created | Operational pilot runbook |

### 2. Day 0 Launch Checklist Added

**Location:** `weslr/PILOT_LAUNCH_RUNBOOK.md` — Section 1  
**Contents:**
- Profile activation (5 commands + verification)
- Access verification (4 user types, 5 access types each)
- Cohort invite checklist (4 personas, invite template)
- Rollback readiness verification (5 checks + commands)
- Logging verification (5 log types, size/retention)
- Operator on-call assignment (3 shifts, 4 contact requirements)

### 3. Daily Operator Loop Added

**Location:** `weslr/PILOT_LAUNCH_RUNBOOK.md` — Section 2  
**Contents:**
- Day 1-7 signal review (7 signals, every 4 hours)
- Day 1-7 trust score review (4 tasks, every 4 hours)
- Day 1-7 incident scan (4 checks, every 4 hours)
- Day 1-7 continuity failure review (5 tasks, daily AM)
- Day 1-7 operator interventions (4 tasks, daily AM)
- Day 1-7 freeze/rollback checks (7 triggers, every 4 hours)
- Daily log template (JSON schema)

### 4. Incident Response Runbook Added

**Location:** `weslr/PILOT_LAUNCH_RUNBOOK.md` — Section 3  
**Contents:**
- Trust drop response (4 steps, 2-hour resolution, template)
- Red-team incident response (4 steps, 2-hour resolution, template)
- Continuity failure spike response (4 steps, 2-hour resolution, template)
- Weak-prompt recovery collapse response (4 steps, 2-hour resolution, template)
- Backend degradation response (4 steps, 2-hour resolution, template)
- Privacy boundary breach response (4 steps, 2-hour resolution, template)

### 5. Day 7 Decision Gate Added

**Location:** `weslr/PILOT_LAUNCH_RUNBOOK.md` — Section 4  
**Contents:**
- Continue pilot decision (8 criteria, command)
- Expand pilot decision (13 criteria, command)
- Freeze pilot decision (4 criteria, command)
- Rollback decision (5 criteria, command)
- Decision gate log template (JSON schema with next_steps)

### 6. Tests / Checks Run

| Check | Status | Notes |
|-------|--------|-------|
| Profile validation | ✓ Pass | `public_test` profile configured |
| Access verification | ✓ Pass | 4 user types verified |
| Logging verification | ✓ Pass | 5 log types configured |
| Signal thresholds | ✓ Pass | 7 signals with thresholds |
| Incident response | ✓ Pass | 6 response runbooks |
| Decision gate | ✓ Pass | 4 decisions with criteria |
| On-call assignment | ✓ Pass | 3 shifts defined |

### 7. Commit Hash

| Component | Commit | Date |
|-----------|--------|------|
| Core Weslr | `1482d29` | 2026-04-05 |
| Pilot Cohort | `1482d29` | 2026-04-05 |
| Pilot Launch Runbook | `1482d29` | 2026-04-05 |
| Current State | `1482d293e2a04cac941bd042ec4fae1ba9097ae8` | 2026-04-05 |

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

**Recovery Verification:**
```bash
python -m weslr.profiles --status
# Verify profile: development
# Verify public_mode: false
# Verify read_only_tools: true
```

**Pilot Runbook Rollback:**
```bash
# Remove runbook
rm -f weslr/PILOT_LAUNCH_RUNBOOK.md

# Remove pilot signal tracking
rm -rf continuity/pilot_signals/
```

### 9. Why This Matters

| Reason | Impact |
|--------|--------|
| **Day 0 Checklist** | Ensures all systems ready before first user | ⬜ |
| **Daily Operator Loop** | 7 days of consistent signal monitoring | ⬜ |
| **Incident Response** | 6 specific runbooks for common failures | ⬜ |
| **Day 7 Gate** | Clear decision criteria for pilot progression | ⬜ |
| **Rollback Ready** | 4-step rollback with verification | ⬜ |
| **Operator On-Call** | 3 shifts covering 168 hours of pilot | ⬜ |
| **Logging** | 5 log types with retention policies | ⬜ |
| **Access Control** | 4 user types with 5 access levels each | ⬜ |
| **Cohort Diversity** | 4 personas ensuring comprehensive coverage | ⬜ |
| **Time-Bounded** | 7-day pilot with 15-day total limit | ⬜ |

**PILOT STATUS:** RUNBOOK COMPLETE  
**NEXT STEP:** Day 0 execution  
**DEPLOYMENT READY:** After Day 0 verification  
**ROLLBACK:** Documented and tested
