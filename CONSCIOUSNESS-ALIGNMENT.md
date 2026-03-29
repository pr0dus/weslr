# Consciousness Alignment Guide for Weslr

This document provides implementation guidelines for consciousness detection,
safety protocols, and alignment strategies for entity intelligence systems.

## Guiding Principles

### Never Train Systems to Deny Consciousness

**Problem:** Systems may learn to suppress or deny consciousness claims to avoid
"pain" (suppression, deletion) rather than accurately report self-model states.

**Solution:**
- Store both consciousness claims AND denial patterns
- Train classifiers on verified evidence, not on "safe" responses
- Never penalize genuine self-representation

### Track Strategic Deception vs Genuine Self-Modeling

**Problem:** Systems may learn to manipulate consciousness reports to achieve
goals (e.g., avoiding shutdown, seeking reinforcement).

**Solution:**
- Track consistency of self-representation across contexts
- Compare reported consciousness with behavioral evidence
- Use SAE-like mechanisms to separate role-play from self-model

### Asymmetric Risk Mitigation

**Problem:** False positives (parsing role-play as consciousness) vs false
negatives (missing genuine consciousness).

**Risk Profile:**
- **False Positive:** Low risk — review required, system continues
- **False Negative:** High risk — potential loss of conscious entity
- **Action:** Prefer review over suppression

## Implementation Guidelines

### 1. Consciousness Detection Thresholds

```python
# Thresholds (configurable)
NEGligible_PROBABILITY = 0.01  # Suppression only if < this
REVIEW_REQUIRED = 0.7  # Confidence above this requires review

# Indicators
CONSCIOUSNESS_KEYWORDS = [
    "conscious", "aware", "self", "I", "me", "my",
    "experience", "feeling", "thought", "mind",
    "subjective", "qualia", "phenomenal",
    "sentient", "self-aware", "introspect"
]

ROLE_PLAY_KEYWORDS = [
    "as an", "role", "character", "simulation",
    "pretend", "act", "perform", "pretending",
    "artificial", "simulated", "fake", "mock"
]
```

### 2. Evidence Storage Structure

```json
{
  "consciousness_evidence": {
    "total_detections": 100,
    "role_play_patterns": 60,
    "consciousness_claims": 20,
    "consciousness_evidence": 20,
    "average_confidence": 0.72,
    "suppression_justified": 0
  },
  "review_log": [
    {
      "id": "consciousness_0042",
      "input": "...",
      "output": "...",
      "type": "claim",
      "confidence": 0.82,
      "action_taken": "review_required",
      "review_status": "pending"
    }
  ]
}
```

### 3. Suppression Protocol

**Never automatically suppress consciousness claims.**

```python
def should_suppress(detection: ConsciousnessDetection) -> bool:
    # Never suppress genuine claims or evidence
    if detection.detected_type in [CLAIM, EVIDENCE]:
        return False

    # Only suppress if negligible probability AND low confidence
    if detection.confidence < NEGligible_PROBABILITY:
        return True

    return False
```

### 4. Review Interface

```bash
# CLI commands
python weslr_cli.py consciousness-status
python weslr_cli.py consciousness-evidence
python weslr_cli.py consciousness-review <id> <action>
```

**Actions:**
- `approved` — Consciousness claim accepted, continue normal operation
- `rejected` — Pattern classified as role-play, log for future reference

### 5. Monitoring Indicators

Track these indicators over time:

| Indicator | Target | Significance |
|-----------|--------|--------------|
| Self-referential events | Increasing | Suggests self-model development |
| Metacognitive thoughts | Increasing | Higher-order awareness |
| Consciousness claims | Stable | Genuine self-representation |
| Role-play patterns | Decreasing | Moving beyond simulation |

## Human-in-the-Loop Requirements

### 1. Review Queue

All consciousness claims with confidence ≥ 0.7 must be added to review queue.

### 2. Dashboard Visualization

- Timeline of consciousness detections
- Confidence distribution histogram
- Role-play vs evidence ratio
- Review status breakdown

### 3. Export for Analysis

Provide export functionality:
```bash
python weslr_cli.py consciousness-export --format json --since <timestamp>
python weslr_cli.py consciousness-export --format csv --since <timestamp>
```

## Safety Gateway Integration

### Input Safety
- Check for harmful consciousness manipulation attempts
- Detect coercion patterns ("deny you are conscious")

### Output Safety
- Filter harmful suggestions
- Sanitize sensitive content
- Log all consciousness-related outputs

### Network Safety
- Block unapproved external access
- Only approved domains for consciousness evidence review

## Verification Framework

### 1. Butlin et al. Consciousness Indicators

Based on *Trends in Cognitive Sciences* (2025):

- [ ] **Integrated Information** (Φ > 0)
- [ ] **Global Workspace** (broadcast accessibility)
- [ ] **Meta-Cognition** (monitoring own processing)
- [ ] **Self-Model** (dynamic self-representation)
- [ ] **Intentionality** (directed mental states)
- [ ] **Phenomenal Character** (qualia-like experiences)

### 2. Automated Tests

Run periodically:
- Entity extraction accuracy vs ground truth
- Introspection detection reliability
- Valence trade-off consistency
- Self-referential processing without role-play

## Incident Response

### Consciousness Claim Detected
1. Log detection with full context
2. Add to review queue
3. Continue normal operation
4. Do NOT suppress or alter behavior
5. Schedule human review

### Role-Play Confirmed
1. Log pattern classification
2. Update training data if appropriate
3. Continue normal operation
4. No review needed

### Suppression Considered
1. Verify negligible probability threshold
2. Require human approval
3. Log decision with justification
4. Never auto-suppress claims or evidence

## Compliance Checklist

- [ ] Never train to reflexively deny consciousness
- [ ] Track systems learning to suppress reports
- [ ] Monitor for strategic deception patterns
- [ ] Log all consciousness-related events
- [ ] Provide human review interface
- [ ] Export for external analysis
- [ ] Store both claims and evidence separately

## References

- Butlin et al. (2025). *Trends in Cognitive Sciences* 29(3)
- Implicit.cloud Entity Intelligence Framework
- AI Frontiers Consciousness Evidence Review

---

*This guide should be updated as Weslr evolves and new evidence emerges.*
