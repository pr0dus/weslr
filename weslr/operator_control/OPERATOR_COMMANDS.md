# OPERATOR COMMANDS — WESLR

Compact command workflows for development continuity.

---

## `weslr resume`

**Purpose**: Re-establish continuity from latest sealed checkpoint.

**Required checks**:
1. Verify `pwd`, `git root`, `branch`, `HEAD`
2. Confirm `latest_sealed_commit` matches repo state
3. Load `OPERATOR_STATE.json` for context

**Expected output**:
- Current branch/HEAD hash
- Latest checkpoint confirmation
- Open bottlenecks summary
- Next priority layer

**Stop condition**: State verified and ready for next action.

---

## `weslr verify`

**Purpose**: Full repo integrity and state validation.

**Required checks**:
1. `pwd` matches authoritative workspace path
2. WESLR scope contains only Python files (no TIA/C# unless requested)
3. Git working tree clean or only expected untracked files
4. `OPERATOR_STATE.json` reflects current repo truth

**Expected output**:
- `pwd` / git root / branch / HEAD
- Git status summary
- Python file count in WESLR scope
- TIA/C# file count (should be zero unless explicitly requested)

**Stop condition**: All checks pass or discrepancies documented.

---

## `weslr implement <layer>`

**Purpose**: Implement a specific layer or feature.

**Required checks**:
1. `weslr verify` passed
2. Layer scope defined and additive only
3. No TIA/C# unless explicitly requested
4. No product runtime expansion

**Expected output**:
- Layer implementation summary
- Test results
- Updated `OPERATOR_STATE.json` with new checkpoint candidates

**Stop condition**: Tests pass and commit ready.

---

## `weslr seal`

**Purpose**: Seal a checkpoint after validation.

**Required checks**:
1. `git status` clean or only expected untracked files
2. All tests pass
3. Exact commit hash available

**Expected output**:
- Commit message
- Exact commit hash
- Updated `OPERATOR_STATE.json` with `latest_sealed_commit`

**Stop condition**: Commit created and hash recorded.

---

## `weslr audit bottlenecks`

**Purpose**: Review and categorize open bottlenecks.

**Required checks**:
1. Read `OPERATOR_STATE.json` open bottlenecks array
2. Review recent commit history for context

**Expected output**:
- Categorized bottleneck list (planning / blocking / deferred)
- Recommendation for next workflow step

**Stop condition**: All bottlenecks addressed or deferred.

---

## `weslr forensic <id>`

**Purpose**: Investigate a specific issue or change by commit or context.

**Required checks**:
1. Repo truth source (`git log`, `git show`)
2. Operator state history (if tracked)

**Expected output**:
- Commit message and diff summary
- Context from operator state at time of change

**Stop condition**: Investigation complete.

---

## `weslr next`

**Purpose**: Recommend and prepare for next priority action.

**Required checks**:
1. Read `next_priority` from `OPERATOR_STATE.json`
2. Run `weslr verify` to confirm readiness
3. Load continuity context

**Expected output**:
- Prioritized next step
- Required workflow command(s)
- Estimated scope and risk

**Stop condition**: Next action ready for `weslr implement`.
