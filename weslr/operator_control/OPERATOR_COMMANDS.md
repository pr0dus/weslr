# OPERATOR COMMANDS — WESLR

Compact command workflows for development continuity.

---

## `weslr resume`

**Purpose**: Re-establish continuity from latest sealed checkpoint.

**Required checks**:
1. Verify `pwd`, `git root`, `branch`, `HEAD`
2. Confirm `latest_sealed_commit` matches repo state
3. Load `OPERATOR_STATE.json` for context
4. Confirm `active_scope` includes `weslr` only
5. Confirm `excluded_scope` is not routing target

**Expected output**:
- Current branch/HEAD hash
- Latest checkpoint confirmation
- Open bottlenecks summary (WESLR core only)
- Next priority category

**Stop condition**: State verified and ready for next action.

---

## `weslr verify`

**Purpose**: Full repo integrity and state validation.

**Required checks**:
1. `pwd` matches authoritative workspace path
2. WESLR scope contains only Python files (no TIA/C# unless requested)
3. Git working tree clean or only expected untracked files
4. `OPERATOR_STATE.json` reflects current repo truth
5. `active_scope` contains `weslr`, `excluded_scope` contains only forbidden entries

**Expected output**:
- `pwd` / git root / branch / HEAD
- Git status summary
- Python file count in WESLR scope
- TIA/C# file count (should be zero unless explicitly requested)
- Scope configuration summary

**Stop condition**: All checks pass or discrepancies documented.

---

## `weslr implement <layer>`

**Purpose**: Implement a specific layer or feature.

**Required checks**:
1. `weslr verify` passed
2. Layer scope defined and additive only
3. Layer belongs to `allowed_next_categories`
4. No TIA/C# unless explicitly requested
5. No product runtime expansion

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
4. `next_priority` updated to new category after implementation

**Expected output**:
- Commit message
- Exact commit hash
- Updated `OPERATOR_STATE.json` with `latest_sealed_commit`

**Stop condition**: Commit created and hash recorded.

---

## `weslr audit bottlenecks`

**Purpose**: Review and categorize open bottlenecks.

**Required checks**:
1. Read `active_bottlenecks` from `OPERATOR_STATE.json` for WESLR core scope
2. Read `archived_or_external_bottlenecks` for excluded domains (optional, only if explicitly requested)
3. Review recent commit history for context
4. Confirm `excluded_scope` entries are not included in active bottleneck count

**Expected output**:
- Categorized bottleneck list (planning / blocking / deferred)
- WESLR core bottleneck summary
- External/archived bottleneck summary (if requested)
- Recommendation for next workflow step

**Stop condition**: All bottlenecks addressed or deferred. Never report "0 bottlenecks" if WESLR core roadmap has pending items.

---

## `weslr forensic <id>`

**Purpose**: Investigate a specific issue or change by commit or context.

**Required checks**:
1. Repo truth source (`git log`, `git show`)
2. Operator state history (if tracked)
3. Verify `active_scope` context matches investigation domain

**Expected output**:
- Commit message and diff summary
- Context from operator state at time of change
- Scope verification (active vs excluded)

**Stop condition**: Investigation complete.

---

## `weslr next`

**Purpose**: Recommend and prepare for next priority action.

**Required checks**:
1. Read `next_priority` from `OPERATOR_STATE.json`
2. Confirm `next_priority` belongs to `allowed_next_categories`
3. Run `weslr verify` to confirm readiness
4. Load continuity context
5. Exclude `excluded_scope` entries from all routing

**Expected output**:
- Prioritized next step (from `allowed_next_categories`)
- Required workflow command(s)
- Estimated scope and risk
- Confirmation: `next_priority` is NOT in `excluded_scope`

**Stop condition**: Next action ready for `weslr implement`. Never route to excluded scopes.
