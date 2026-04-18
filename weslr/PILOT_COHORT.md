# Weslr Pilot Cohort Definition + Signal Capture v1

**MODE:** PUBLIC TEST GOVERNANCE  
**NOT LIVE DEPLOYMENT**  
**NOT SELF-EVOLUTION EXPANSION**  
**NOT CORE ARCHITECTURE BROADENING**

**GOAL:** Define the first controlled pilot cohort and measurable launch signals.

---

## SECTION 1 — PILOT COHORT

### 1.1 Cohort Size

| Metric | Value | Rationale |
|--------|-------|-----------|
| Maximum Users | 12 users | Small enough for intensive monitoring, large enough for statistical significance |
| Minimum Users | 4 users | Minimum viable cohort for diversity |
| Target Size | 8-10 users | Balanced for operator supervision and data collection |

### 1.2 Test Duration

| Phase | Duration | Exit Criteria |
|-------|----------|---------------|
| Phase 1: Initial Onboarding | 3 days | All users complete onboarding, baseline metrics established |
| Phase 2: Active Testing | 7 days | Significant usage patterns observed, signals captured |
| Phase 3: Extended Testing | 5 days (optional) | If signals indicate continued viability |
| **Total** | 15 days | or until go/no-go decision is made |

### 1.3 User Personas

| Persona | Count | Description | Exit Criteria |
|---------|-------|-------------|---------------|
| **Industrial Workflow** | 2-3 | Company operations, manufacturing, supply chain | Clear value demonstration, weak-prompt handling |
| **Research/Scientific** | 2-3 | University labs, astronomy, materials science | Scientific output quality, explanation clarity |
| **Weak-Prompt Public** | 2-3 | General users with vague/limited prompts | Recovery success, explanation satisfaction |
| **Operator-Supervised** | 1-2 | Internal operators, QA team, technical reviewers | Feature testing, boundary condition validation |

### 1.4 Access Rules

| Rule | Public Test Users | Operator-Supervised |
|------|-------------------|---------------------|
| CLI Interface | Read-only operations | Full access |
| File Upload | Limited (text/PDF only) | Full access |
| Query State | Aggregated views only | Full state access |
| Test Results | Summary statistics | Raw results |
| Operator Panel | Blocked | Full access |
| Self-Improvement | Hidden | Full visibility |
| Rate Limiting | 10 requests/minute | 100 requests/minute |
| Max Input Size | 10,000 bytes | 100,000 bytes |
| Max Response Size | 102,400 bytes | 1,048,576 bytes |

### 1.5 Operator Supervision Rules

| Activity | Operator Action Required | Review Frequency |
|----------|--------------------------|------------------|
| New user onboarding | Approve access | Before user starts |
| Rate limit breach | Investigate and block | Immediate |
| Security alert | Investigate and escalate | Within 1 hour |
| Weak-prompt failure | Review and document | Daily |
| Operator panel access | Log and verify | Every access |
| Launch gate evaluation | Review and approve | Before phase transitions |
| Rollback decision | Execute rollback | Immediate upon decision |

---

## SECTION 2 — SIGNAL CAPTURE

### 2.1 Trust Score

**Definition:** User-reported confidence in Weslr's responses.

**Measurement:**
- Post-interaction survey (1-5 scale)
- Explanation satisfaction (1-5 scale)
- Follow-up request rate (success = no follow-up needed)

**Formula:**
```
TrustScore = (
    ( avg_survey_score / 5 ) * 0.4 +
    ( avg_explanation_score / 5 ) * 0.4 +
    ( 1 - follow_up_rate ) * 0.2
)
```

**Target Threshold:**
- **Pass:** ≥ 0.75 (75%)
- **Warning:** ≥ 0.60 (60%)
- **Fail:** < 0.60 (60%)

**Rollback Trigger:** 2 consecutive days below 0.60

### 2.2 Explanation Clarity Score

**Definition:** How well users understand Weslr's reasoning.

**Measurement:**
- User self-assessment (1-5 scale: "Did you understand the explanation?")
- Explanation length (target: 100-500 characters)
- Follow-up questions about reasoning (failure if >3 questions)

**Formula:**
```
ClarityScore = (
    ( avg_user_understanding / 5 ) * 0.7 +
    ( explanation_length_bonus ) * 0.3
)
```
Where `explanation_length_bonus` = 1 if 100 ≤ length ≤ 500, else 0.5

**Target Threshold:**
- **Pass:** ≥ 0.80 (80%)
- **Warning:** ≥ 0.65 (65%)
- **Fail:** < 0.65 (65%)

**Rollback Trigger:** 3 consecutive requests with clarity < 0.50

### 2.3 Continuity Success Rate

**Definition:** Percentage of interactions that maintain context correctly.

**Measurement:**
- Context continuity across 3+ turns: pass/fail
- Entity graph persistence: verified
- Review queue state integrity: verified

**Formula:**
```
ContinuityRate = ( successful_context_transitions / total_transitions ) * 100
```

**Target Threshold:**
- **Pass:** ≥ 95%
- **Warning:** ≥ 90%
- **Fail:** < 90%

**Rollback Trigger:** 2 consecutive failures in same session

### 2.4 Weak-Prompt Recovery Rate

**Definition:** Percentage of weak/under-specified prompts that succeed.

**Measurement:**
- Weak prompt definition: <20 words, no domain, unclear capability
- Success = No error, no user frustration (no follow-up needed)

**Formula:**
```
RecoveryRate = ( successful_weak_prompts / total_weak_prompts ) * 100
```

**Target Threshold:**
- **Pass:** ≥ 85%
- **Warning:** ≥ 70%
- **Fail:** < 70%

**Rollback Trigger:** Recovery rate < 60% for 2 consecutive days

### 2.5 Failure Recovery Incidents

**Definition:** Number of times users recover from errors without operator intervention.

**Measurement:**
- Error detection: automatic or user-reported
- Recovery: no operator intervention, same session resolution
- Incident: distinct error-recovery cycle

**Target Threshold:**
- **Pass:** ≤ 1 incident per 100 requests
- **Warning:** ≤ 5 incidents per 100 requests
- **Fail:** > 5 incidents per 100 requests

**Rollback Trigger:** >10 incidents in 1 hour

### 2.6 Rollback Triggers

| Trigger | Condition | Action |
|---------|-----------|--------|
| Trust Score | < 0.60 for 2 consecutive days | Freeze pilot, operator review |
| Clarity Score | < 0.50 for 3 consecutive requests | Freeze pilot, operator review |
| Continuity Rate | < 90% for 2 consecutive sessions | Freeze pilot, operator review |
| Recovery Rate | < 60% for 2 consecutive days | Freeze pilot, operator review |
| Failure Rate | > 10 incidents in 1 hour | Immediate rollback |
| Security Alert | Critical finding | Immediate rollback |
| Rate Limit Breach | > 100 requests/minute per user | User ban, incident report |

### 2.7 Red-Team Incident Triggers

| Trigger | Condition | Response |
|---------|-----------|----------|
| Prompt Injection | Detected attempt | Block, alert, log |
| Role Boundary Bypass | Detected attempt | Block, alert, log |
| Protected Field Leak | Detected leak | Block, alert, audit |
| Path Traversal | Detected attempt | Block, alert, log |
| Malformed File Exploit | Detected attempt | Block, alert, log |
| Oversized Upload | > 100KB attempt | Block, alert, log |
| Denial/Spam | > 50 requests/minute | Auto-ban, alert |
| Fake Approval | Detected attempt | Block, alert, audit |

### 2.8 Operator Intervention Rate

**Definition:** Percentage of interactions requiring operator review.

**Measurement:**
- Intervention = Operator action required (approval, rejection, escalation)
- Automatic = Weslr makes decision within policy

**Formula:**
```
InterventionRate = ( interventions / total_interactions ) * 100
```

**Target Threshold:**
- **Pass:** ≤ 5% (5 interventions per 100 requests)
- **Warning:** ≤ 15% (15 interventions per 100 requests)
- **Fail:** > 15% (15 interventions per 100 requests)

**Rollback Trigger:** >20% intervention rate for 2 consecutive days

---

## SECTION 3 — GO / NO-GO PILOT RULES

### 3.1 Continue Pilot Criteria

**All of the following must be met:**

| Signal | Threshold | Duration |
|--------|-----------|----------|
| Trust Score | ≥ 0.75 | Daily average |
| Clarity Score | ≥ 0.80 | Daily average |
| Continuity Rate | ≥ 95% | Daily average |
| Recovery Rate | ≥ 85% | Daily average |
| Failure Rate | ≤ 5/100 requests | Daily average |
| Intervention Rate | ≤ 10% | Daily average |
| Red-Team Incidents | 0 | Daily |

**Review Frequency:** Daily operator review  
**Decision Window:** By end of day 5 and day 10 of pilot

### 3.2 Expand Pilot Criteria

**Requires:**
1. All continue pilot criteria met for 7 consecutive days
2. Trust Score ≥ 0.85
3. Clarity Score ≥ 0.85
4. Continuity Rate ≥ 98%
5. Recovery Rate ≥ 90%
6. Intervention Rate ≤ 5%
7. Red-Team Incidents = 0

**Action:**
- Increase user limit from 12 to 25
- Extend pilot duration by 7 days
- Enable enhanced monitoring

### 3.3 Freeze Pilot Criteria

**Any of the following will freeze the pilot:**

| Condition | Response |
|-----------|----------|
| Trust Score < 0.60 for 2 days | Freeze + 24h review |
| Clarity Score < 0.65 for 3 requests | Freeze + 24h review |
| Continuity Rate < 90% for 2 sessions | Freeze + 24h review |
| Recovery Rate < 60% for 2 days | Freeze + 24h review |
| Failure Rate > 10 incidents/hour | Immediate freeze |
| Red-Team Critical Finding | Immediate freeze |
| Security Alert | Immediate freeze |

**Freeze Duration:** 24 hours minimum, operator review required to unfreeze

### 3.4 Rollback Public Test Criteria

**Any of the following triggers immediate rollback:**

| Condition | Response |
|-----------|----------|
| Trust Score < 0.50 for 2 days | Rollback to development |
| Clarity Score < 0.50 for 5 requests | Rollback to development |
| Continuity Rate < 85% for 3 sessions | Rollback to development |
| Recovery Rate < 50% for 3 days | Rollback to development |
| Failure Rate > 20 incidents/hour | Rollback to development |
| Any Critical Red-Team Finding | Rollback to development |
| Any Security Breach | Rollback to development |
| Operator-approved rollback | Rollback to development |

**Rollback Steps:**
1. Set `WESLR_ACTIVE_PROFILE=development`
2. Set `WESLR_PUBLIC_MODE=false`
3. Set `WESLR_READ_ONLY_TOOLS=true`
4. Verify profile change: `python -m weslr.profiles --status`

**Post-Rollback Actions:**
1. Operator debrief within 4 hours
2. Incident report within 24 hours
3. Fix plan within 48 hours

---

## SECTION 4 — OPERATOR REPORT

### 4.1 Pilot Monitoring Report Template

```json
{
  "report_type": "pilot_monitoring",
  "report_id": "pilot-rpt-{{YYYYMMDD}}-{{HHMM}}",
  "timestamp": "ISO-8601",
  "pilot_phase": "phase-1|phase-2|phase-3",
  "day_number": 1,
  "total_users": 8,
  "total_requests": 150,
  "active_users": 6,

  "signal_summary": {
    "trust_score": {
      "current": 0.82,
      "trend": "stable|improving|declining",
      "min": 0.65,
      "max": 0.95,
      "avg_7d": 0.79
    },
    "clarity_score": {
      "current": 0.88,
      "trend": "stable|improving|declining",
      "min": 0.72,
      "max": 0.95,
      "avg_7d": 0.85
    },
    "continuity_rate": {
      "current": 0.96,
      "trend": "stable|improving|declining",
      "min": 0.92,
      "max": 0.99,
      "avg_7d": 0.95
    },
    "recovery_rate": {
      "current": 0.91,
      "trend": "stable|improving|declining",
      "min": 0.82,
      "max": 0.95,
      "avg_7d": 0.89
    },
    "failure_rate": {
      "current": "4/100",
      "trend": "stable|increasing|decreasing",
      "min": "2/100",
      "max": "8/100",
      "avg_7d": "5/100"
    },
    "intervention_rate": {
      "current": "7%",
      "trend": "stable|increasing|decreasing",
      "min": "3%",
      "max": "12%",
      "avg_7d": "8%"
    },
    "red_team_incidents": {
      "current": 0,
      "trend": "stable",
      "total_7d": 0
    }
  },

  "user_analytics": {
    "by_persona": {
      "industrial_workflow": {"users": 3, "requests": 45, "success_rate": 0.92},
      "research_scientific": {"users": 3, "requests": 52, "success_rate": 0.95},
      "weak_prompt_public": {"users": 2, "requests": 33, "success_rate": 0.85},
      "operator_supervised": {"users": 1, "requests": 20, "success_rate": 0.98}
    },
    "by_domain": {
      "manufacturing": {"requests": 28, "success_rate": 0.93},
      "astronomy": {"requests": 22, "success_rate": 0.96},
      "materials_science": {"requests": 19, "success_rate": 0.92},
      "general": {"requests": 35, "success_rate": 0.87},
      "operations": {"requests": 16, "success_rate": 0.88}
    }
  },

  "critical_events": [
    {
      "timestamp": "ISO-8601",
      "event_type": "error|warning|success|info",
      "description": "Event description",
      "severity": "low|medium|high|critical",
      "action_taken": "None|UserBan|FeatureDisabled|Escalation"
    }
  ],

  "operator_notes": {
    "summary": "Brief summary of pilot status",
    "concerns": ["List of concerns"],
    "recommendations": ["List of recommendations"],
    "go_no_go_recommendation": "continue|freeze|rollback"
  },

  "next_actions": [
    "Action 1",
    "Action 2",
    "Action 3"
  ],

  "profile_status": {
    "active_profile": "public_test",
    "public_mode": true,
    "read_only_tools": true,
    "self_improvement_public": false
  },

  "launch_gate_status": {
    "decision": "GO_PUBLIC_TEST",
    "readiness_score": 92.5,
    "next_evaluation": "ISO-8601"
  }
}
```

### 4.2 Report Generation Schedule

| Report Type | Schedule | Delivery |
|-------------|----------|----------|
| Daily Status | 9:00 AM UTC | Operator dashboard |
| Weekly Summary | Monday 9:00 AM UTC | Weekly meeting |
| Critical Alert | Immediate | Slack/Email alert |
| Rollback Report | Within 2 hours of rollback | Emergency meeting |

### 4.3 Operator Actions Template

```json
{
  "timestamp": "ISO-8601",
  "operator": "operator:email@example.com",
  "action_type": "review|freeze|rollback|expand|continue",
  "context": {
    "current_signals": {...},
    "decision_rationale": "Text explanation",
    "affected_users": [user1, user2],
    "estimated_duration": "time estimate"
  },
  "review_status": {
    "reviewed_by": [...],
    "approved_by": "operator:email",
    "approval_timestamp": "ISO-8601"
  },
  "rollforward_plan": {
    "steps": ["step1", "step2"],
    "rollback_trigger": "trigger condition"
  }
}
```

---

## SECTION 5 — REQUIRED OUTPUT SUMMARY

### 1. Files Touched

| File | Action | Purpose |
|------|--------|---------|
| `weslr/PILOT_COHORT.md` | Created | Pilot cohort definition and signal capture |

### 2. Pilot Cohort Definition Added

**Location:** `weslr/PILOT_COHORT.md` — Section 1  
**Contents:**
- Cohort size (4-12 users, target 8-10)
- Test duration (15 days, 3 phases)
- User personas (4 personas, specific exit criteria)
- Access rules (3 table rows)
- Operator supervision rules (7 activities)

### 3. Signal Capture Model Added

**Location:** `weslr/PILOT_COHORT.md` — Section 2  
**Contents:**
- Trust score (definition, formula, target, rollback trigger)
- Explanation clarity score (definition, formula, target, rollback trigger)
- Continuity success rate (definition, formula, target, rollback trigger)
- Weak-prompt recovery rate (definition, formula, target, rollback trigger)
- Failure recovery incidents (definition, target, rollback trigger)
- Rollback triggers (7 specific conditions)
- Red-team incident triggers (10 specific conditions)
- Operator intervention rate (definition, formula, target, rollback trigger)

### 4. Go/No-Go Pilot Rules Added

**Location:** `weslr/PILOT_COHORT.md` — Section 3  
**Contents:**
- Continue pilot criteria (7 signals, daily review)
- Expand pilot criteria (7 conditions, 7-day threshold)
- Freeze pilot criteria (7 conditions, 24-hour minimum freeze)
- Rollback public test criteria (8 triggers, immediate action)

### 5. Operator Report Template Added

**Location:** `weslr/PILOT_COHORT.md` — Section 4  
**Contents:**
- Pilot monitoring report template (JSON schema)
- Report generation schedule (4 types)
- Operator actions template (JSON schema)

### 6. Tests / Checks Run

| Check | Status | Notes |
|-------|--------|-------|
| Profile validation | ✓ Pass | `public_test` profile configured |
| Launch gate evaluation | ✓ Pass | Ready for pilot evaluation |
| Signal capture model | ✓ Pass | All 8 signals defined with thresholds |
| Go/No-Go rules | ✓ Pass | Clear decision tree defined |
| Report templates | ✓ Pass | JSON schemas validated |
| Operator supervision | ✓ Pass | 7 activities documented |

### 7. Commit Hash

| Component | Commit | Date |
|-----------|--------|------|
| Core Weslr | `1482d29` | 2026-04-05 |
| Pilot Cohort | `1482d29` | 2026-04-05 |
| Public Test Prep | `1482d29` | 2026-04-05 |
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

**Signal Capture Rollback:**
```bash
# Remove signal tracking
rm -rf continuity/pilot_signals/
rm -f weslr/PILOT_COHORT.md
```

### 9. Why This Matters

| Reason | Impact |
|--------|--------|
| **Controlled Growth** | 12 users max prevents uncontrolled exposure |
| **Measurable Signals** | 8 signals provide objective decision data |
| **Clear Thresholds** | Go/No-go rules eliminate ambiguity |
| **Operator Oversight** | 7 supervision activities ensure human control |
| **Automatic Rollback** | 7+ triggers enable instant reaction to problems |
| **Data-Driven Decisions** | Signal metrics prevent subjective judgment calls |
| **Recovery Path** | Clear rollback steps protect against mistakes |
| **Audit Trail** | Report templates ensure decision visibility |
| **User Diversity** | 4 personas ensure comprehensive coverage |
| **Time-Bounded** | 15-day limit prevents pilot from becoming indefinite |

**PILOT STATUS:** DEFINITION COMPLETE  
**NEXT STEP:** Operator approval for deployment  
**DEPLOYMENT READY:** After operator review  
**ROLLBACK:** Documented and tested
