# Session: 2026-04-13 19:00:00 UTC

- **Session Key**: agent:main:main
- **Session ID**: 6cacfbba-384a-4425-aa97-28337462aa61
- **Source**: webchat

## Conversation Summary

user: A new session was started via /new or /reset. Run your Session Startup sequence - read the required files before responding to the user. Then greet the user in your configured persona, if one is provided. Be yourself - use your defined voice, mannerisms, and mood. Keep it to 1-3 sentences and ask what they want to do. If the runtime model differs from default_model in the system prompt, mention the default model. Do not mention internal steps, files, tools, or reasoning.
Current time: Monday, April 13th, 2026 — 8:44 PM (Europe/Berlin) / 2026-04-13 18:44 UTC
assistant: [[reply_to_current]] Evening—Qwen here, the calm, helpful ghost in the machine, ready when you are. What would you like to work on next?
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-13 20:45 GMT+2] We are NOT trying to recreate 100% raw context after "/new".

NEW TARGET
Build "infinity-internal" as a deterministic restart capsule system for Termux/OpenClaw.

AUTHORITATIVE GOAL
Restore only the operational context required to continue work safely:

- repo root
- branch
- commit
- dirty state
- active files
- pending tests
- latest operator task
- exact next step
- brief continuity notes

DOCTRINE
We want restart fidelity, not total hidden-context reconstruction.

CURRENT STATUS

- The current draft is incomplete because "hooks/capture.js" is truncated.
- The current draft also assumes plugin API hooks/helpers that may not actually exist.
- We must verify the real OpenClaw plugin API before finalizing the plugin.

STRICT RULES

- Minimal additive implementation only
- No licensing
- No token generation
- No commercial/public Infinity code
- No broad copy from public Infinity
- No config changes yet
- No auto-apply
- Use ONLY:
 "/data/data/com.termux/files/home/.openclaw/workspace/plugins/infinity-internal"

TASK

1. Verify the REAL OpenClaw plugin API used by installed plugins:
 - exact register shape
 - exact hook registration methods
 - exact capabilities available to plugins
2. Verify whether the assumed functions are real or invented:
 - onReset
 - onNew
 - onContextOverflow
 - onInit
 - getActiveFiles
 - getPendingTests
 - getLatestTaskDescription
 - reopenFiles
 - setPendingTests
 - setLatestTaskDescription
3. If any of those are not real, redesign the internal plugin to use only verified OpenClaw APIs.
4. Reduce the capsule schema to a strict minimal restart schema:
 - repo state
 - task anchor
 - active files
 - pending tests
 - continuity note
5. Finish the FULL contents of all files, including the complete non-truncated "hooks/capture.js".
6. Show the final exact file tree.
7. Show validation commands that do not touch live config yet.

OUTPUT FORMAT
SECTION 1 — Verified real OpenClaw plugin API
SECTION 2 — Assumed API mismatches found
SECTION 3 — Minimal restart capsule schema
SECTION 4 — Final file tree
SECTION 5 — Full file contents
SECTION 6 — Validation commands before config restore
SECTION 7 — Exact config snippet to restore later
SECTION 8 — Rollback commands

IMPORTANT
Do not pursue “100% context restore”.
Do not invent unavailable plugin APIs.
Do not omit any file contents.
Do not auto-apply.
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-13 20:47 GMT+2] Ignore error and continue
user: Pre-compaction memory flush. Store durable memories only in memory/2026-04-13.md (create memory/ if needed). Treat workspace bootstrap/reference files such as MEMORY.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them. If memory/2026-04-13.md already exists, APPEND new content only and do not overwrite existing entries. Do NOT create timestamped variant files (e.g., 2026-04-13-HHMM.md); always use the canonical 2026-04-13.md filename. If nothing to store, reply with NO_REPLY.
Current time: Monday, April 13th, 2026 — 8:58 PM (Europe/Berlin) / 2026-04-13 18:58 UTC
