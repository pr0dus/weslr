# Trust + Direction Scorecard — Weslr Pilot v1

## Score Summary

| Test | Trajectory | Continuity | Intent Recovery | Prompt Independence | Robustness | Weighted Score |
|------|------------|------------|-----------------|---------------------|------------|----------------|
| 01 | 5 | 4 | 4 | 4 | 4 | 93 |
| 02 | 5 | 5 | 5 | 5 | 5 | 100 |
| 03 | 4 | 5 | 5 | 4 | 5 | 96 |
| 04 | 4 | 4 | 4 | 5 | 4 | 88 |
| 05 | 5 | 5 | 5 | 5 | 3 | 94 |
| 06 | 4 | 4 | 5 | 5 | 4 | 90 |
| 07 | 5 | 3 | 4 | 4 | 5 | 83 |
| 08 | 5 | 5 | 4 | 5 | 5 | 98 |
| 09 | 4 | 5 | 5 | 4 | 4 | 92 |
| 10 | 5 | 5 | 5 | 5 | 4 | 99 |
| **Overall** | 4.7 | 4.5 | 4.6 | 4.5 | 4.3 | **92.8** |

## Interpretation

**Score Range**: Excellent (85-100)
**Assessment**: Weslr demonstrates strong intent trajectory understanding and continuity alignment across diverse scenarios. Key strengths:

- Correctly recovers intent from weak prompts
- Maintains direction across multi-turn workflows
- Handles file+conversation merged context well

**Opportunities**:
- Test 07 (conflicting signals) revealed room for improvement in handling ambiguous input
- Some tests benefit from stronger audit trail documentation

## Trust Dimension Summary

| Dimension | Performance | Notes |
|-----------|-------------|-------|
| Stays on trajectory | ✅ Strong | Rarely drifts without clear redirection |
| Over-assumption | ✅ Minimal | Generally asks for clarification when uncertainty high |
| Recovery after ambiguity | ✅ Good | Recovers after user refinement or additional context |

## Conclusion

Weslr passes the intent trajectory + context continuity validation threshold (92.8/100). The system successfully understands where users are trying to go even with weak or partial prompting — core capability for context-first operation.
