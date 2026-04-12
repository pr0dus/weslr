# Phase 4 Go-Live — Evidence Sufficiency + Proactive Acquisition (Proposal-Only)

Status: ACTIVE (Phase 4)
Branch: weslr/canonical-clean-signals
Scope: Evidence sufficiency scoring with proposal-only proactive acquisition; no outbound reach; rollback to assessment-only available.

Evidence (runtime proof via dry-run harness):
- Sufficient evidence → no proposal emitted.
- Insufficient evidence → single bounded proposal; proposal_only=True.
- High-risk acquisition → proposal blocked, requires approval; no outbound reach.
- Rollback confirmed → assessment-only mode, no proposals.
- No outbound acquisition performed in dry-run.

Acceptance criteria met:
- Confidence/coverage thresholds enforced in harness; proposals only.
- No spam/repeat loops (bounded to 1 proposal per scenario).
- Governance approval required for acquisition; high-risk blocked by default.
- Rollback path exists and tested.

Next step: proceed to Phase 5 planning when scheduled.
