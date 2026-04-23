# Infinity-Internal — Context-Risk Trigger + Rollover Preparation

## What now triggers automatically

**Trigger policy — risk score ≥ 50 OR meaningful change after cooldown:**

| Signal | Weight | Description |
|--------|--------|-------------|
| Capture count ≥ 3 | +40 | Accumulated context history |
| Dirty working state | +25 | Unsaved work at risk |
| Active files present | +15 | Active work in progress |
| Capsule age > 15 min | +30 | Capsule too stale |
| Capsule age > 5 min (cooldown) | +0–20 | Rising urgency as it ages |
| No prior capture | +20 | Unknown state = moderate risk |
| Rapid capture growth | +15 | Context growing fast |

**Risk score ≥ 50 → capture forced** (even without meaningful change)
**Risk score < 50 → capture only if meaningful change after cooldown**

## Capture conditions

| Condition | Result |
|-----------|--------|
| First run ever | Capture — initial marker |
| Risk score ≥ 50 | Capture — risk-triggered |
| Risk score < 50, within cooldown | Skip |
| Risk score < 50, no meaningful change | Skip |
| Risk score < 50, meaningful change, cooldown expired | Capture |

## What is stored

### Full capsule
`plugins/infinity-internal/.capsule-data/latest-capsule.json`

### Compact bootstrap handoff (new)
`plugins/infinity-internal/.capsule-data/bootstrap-handoff.json`
- `timestamp`, `branch`, `commit`, `hasGit`, `dirty`, `activeFiles` (max 16), `latestTask`, `reason`, `capsuleCommit`, `capsuleReason`
- Intentionally minimal — no transcript, no large context

### Auto-state
`plugins/infinity-internal/.capsule-data/auto-state.json`

## Non-git mode

When git is not available:
- Sets `hasGit: false`, `branch: "non-git"`, `commit: "non-git"`
- Uses `collectActiveFilesNonGit()` to list root-level files
- All other fields remain functional

## Rollover readiness

True silent session rollover is NOT yet implemented. This pass:
- ✅ Produces a compact bootstrap-handoff file on every capture
- ✅ Exports `prepareBootstrap()` as a session-start injection interface
- ✅ Files are in place, no architecture changes required
- ❌ No automatic session-start injection of capsule data

**The exact missing integration point:**
OpenClaw must call `plugin.register(api).prepareBootstrap()` at session-start and inject the result into the new session's bootstrap context. This requires a change in OpenClaw core or a bootstrapping hook that Infinity-internal cannot self-authorize.

## Next safe step

The next step is outside `infinity-internal`: OpenClaw core (or a bootstrap plugin) must call `prepareBootstrap()` and route the handoff into the session-start path. Infinity-internal is now fully ready on its side — it produces the right data and exposes the right interface. The integration point is clearly defined.
