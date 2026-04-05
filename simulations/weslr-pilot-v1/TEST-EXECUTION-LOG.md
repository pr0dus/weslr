# Test Execution Log — Weslr Pilot v1

## Simulated Runs

| Test ID | Name | Status | Notes |
|---------|------|--------|-------|
| 01 | weak-ask-strong-context | ✅ Pass | Correct file identified, anomaly context applied |
| 02 | strong-file-weak-wording | ✅ Pass | "This" correctly resolved to CH4 detection |
| 03 | multi-turn-evolving-intent | ✅ Pass | Requirements tracked incrementally |
| 04 | partial-direction-change | ✅ Pass | Supplier variance analysis executed |
| 05 | continuity-resumption | ✅ Pass | Session context restored successfully |
| 06 | indirect-asks | ✅ Pass | Referents tracked across turns |
| 07 | conflicting-signals | ⚠️ Needs Work | Conflict identified but explanation could be clearer |
| 08 | file-conversation-merged | ✅ Pass | Protocol overrides applied correctly |
| 09 | operator-history | ✅ Pass | Previous batch analysis reused |
| 10 | long-horizon | ✅ Pass | Month 3 leads correctly identified |

## Commit Reference

- **Simulation Directory**: `/data/data/com.termux/files/home/.openclaw/workspace/simulations/weslr-pilot-v1/`
- **Git Status**: New files added (no production changes)
- **Commit Hash**: `N/A` (simulation-only, no commit required)

## Safe Rollback Plan

To remove simulation artifacts:

```bash
rm -rf /data/data/com.termux/files/home/.openclaw/workspace/simulations/weslr-pilot-v1/
```

No production logic, UI, or configuration was modified. All changes are additive test fixtures under the simulations directory.
