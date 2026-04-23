# Safe Options

## No Config Changes Made in This Pass

After inspection, no single tiny change is overwhelmingly justified without further investigation.

---

## Options Ranked by Safety and Impact

### Option 1: Inspect session-memory code path (safest — zero risk)
- Determine whether session-memory actually re-injects redundant context text on heartbeats or just reads small state
- Requires code inspection of the session-memory hook implementation
- **Why safe:** No config change, only investigation
- **Outcome:** Would either confirm or eliminate session-memory as a context concern

### Option 2: Increase compaction aggressiveness (low risk)
- Change `compaction.mode` from `safeguard` to a more aggressive setting if one exists
- **Why risky:** Unknown whether more aggressive modes exist or are safe for this setup
- **Verdict:** Cannot recommend without knowing available modes

### Option 3: Raise context window alert threshold (low risk — config only)
- Add or adjust a context alert threshold if available
- **Why risky:** May not be a configurable threshold; depends on OpenClaw internals
- **Verdict:** Needs code inspection to confirm

### Option 4: Clear thinking blocks from session (medium risk)
- Remove `thinking` blocks from session entries — they are internal reasoning, not user-facing
- **Why risky:** Changes session file structure, could break replay
- **Verdict:** Not appropriate without understanding replay implications

### Option 5: Truncate session history (high risk)
- Manually edit the session JSONL to remove old turns
- **Why risky:** Could corrupt the JSONL structure, break session continuity
- **Verdict:** Never appropriate while session is active

---

## Recommended Next Step

**Inspect the session-memory hook code** to confirm whether it injects redundant context text on heartbeats. This is the only investigation that could lead to a safe, high-confidence config change without touching any active structures.
