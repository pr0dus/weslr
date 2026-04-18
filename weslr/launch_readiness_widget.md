# Launch Readiness Dashboard Widget

This file defines the operator-only "Launch Readiness" widget for the operator dashboard.

## WIDGET SPECIFICATION

### Widget ID
`launch_readiness`

### Widget Type
`launch_gate_result`

### Visibility
Operator-only (not visible to regular users or public)

### Data Source
- Scorecard results (`weslr/test_scorecard.py`)
- Improvement proposals (`weslr/improvement_engine.py`)
- Red-team findings (`weslr/redteam.py`)

## DISPLAY REQUIREMENTS

### Status Indicators
1. **GO_PUBLIC_TEST** — Green banner with "Public Test Ready"
2. **GO_LIMITED_OPERATOR_PILOT** — Yellow banner with "Operator Pilot Only"
3. **NO_GO_REMEDIATION_REQUIRED** — Red banner with "Launch Blocked"

### Primary Display
- Decision status (as above)
- Readiness score percentage
- Category breakdown (score vs threshold for each)

### Secondary Display
- Weakest categories
- Blocking issues count
- Risk level indicator
- Trust score

### Action Buttons
1. **GO_PUBLIC_TEST**: "Deploy to Public Test"
2. **GO_LIMITED_OPERATOR_PILOT**: "Deploy to Operator Pilot"
3. **NO_GO_REMEDIATION_REQUIRED**: "View Remediation Tasks"

## INTERACTION

### Operators can:
- View readiness status
- See category breakdown
- View blocking issues
- View recommended remediation
- Access remediation tasks (for NO_GO case)
- Request manual review (for GO cases)

### Operators CANNOT:
- Bypass the launch gate
- Change the decision
- View if not operator-authorized

## SECURITY

- This widget is operator-only
- Access controlled by `operator` role
- Audit trail for all view operations
- Decision log stored in `weslr/launch_log.json`

## IMPLEMENTATION

### Frontend (Operator Dashboard)
```html
<div class="launch-readiness-widget">
  <div class="status-banner {{ status_class }}">
    {{ status_text }}
  </div>
  <div class="readiness-score">
    <span class="score">{{ readiness_score }}%</span>
    <span class="label">Readiness Score</span>
  </div>
  <div class="category-breakdown">
    <!-- Category scores vs thresholds -->
  </div>
  <div class="blocking-issues">
    <h4>Blocking Issues</h4>
    <ul>
      {% for issue in blocking_issues %}
      <li>{{ issue }}</li>
      {% endfor %}
    </ul>
  </div>
  <div class="remediation">
    <h4>Recommended Remediation</h4>
    <ul>
      {% for step in recommended_remediation %}
      <li>{{ step }}</li>
      {% endfor %}
    </ul>
  </div>
  <div class="actions">
    <button class="deploy-btn {{ action_class }}" onclick="deployTo('{{ decision }}')">
      {{ action_text }}
    </button>
  </div>
</div>
```

### Backend (API Endpoint)
```python
@app.get("/api/launch-readiness")
@require_operator
def get_launch_readiness():
    """Get current launch readiness status."""
    scorecard = weslr.test_scorecard.evaluate(scorecard_results)
    result = weslr.launch_gate.evaluate(
        scorecard,
        improvement_engine.proposals,
        redteam.findings
    )
    return result.to_dict()
```

## LOGGING

### Launch Decision Log
```json
{
  "timestamp": "2026-04-05T11:30:00Z",
  "decision": "GO_PUBLIC_TEST",
  "readiness_score": 95.2,
  "evaluated_by": "operator:alice@example.com",
  "categories": {
    "security": 95,
    "context_trajectory": 92,
    "privacy": 98,
    "explainability": 94,
    "failure_monitoring": 91,
    "total_score": 95.2
  },
  "blocking_issues": [],
  "comments": "All thresholds met, no blocking issues"
}
```

## OPERATOR CHECKLIST

Before approving launch:

- [ ] All categories meet their thresholds
- [ ] No unresolved critical issues
- [ ] Red-team findings resolved or accepted
- [ ] High-risk proposals resolved or accepted
- [ ] Launch log reviewed and approved
- [ ] Rollback plan documented
- [ ] Operator supervision plan in place (for limited pilot)

## RISK ACCEPTANCE

For cases where blocking issues exist but are accepted:

1. Operator must document risk acceptance
2. Risk acceptance must be time-bound
3. Must include remediation timeline
4. Requires second operator approval
