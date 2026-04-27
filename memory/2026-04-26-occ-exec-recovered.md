# Session: 2026-04-26 — OCC exec Recovered on Termux

## What

OCC exec tool was non-functional (timeout/permission errors on every command).

## Root Cause

Termux Android — bash -c stdin pipe broke after OpenClaw update.

## Patch

**File:** `/data/data/com.termux/files/usr/lib/node_modules/openclaw/dist/exec-_fLrb4o0.js`

**Change:** In `spawnWithFallback`, Termux bash -c branch now spawns `bash -i` and writes `innerCmd` via **stdin** instead of relying on the broken pipe.

```js
// Before (broken):
spawn('/bin/bash', ['-c', cmd], { stdio: 'pipe', ... })

// After (fixed):
const child = spawn('/bin/bash', ['-i'], { stdio: ['pipe', 'pipe', 'pipe'], ... })
child.stdin.write(cmd + '\n')
```

## Validation

```
whoami     → u0_a547
id         → uid=10547(u0_a547) gid=10547(u0_a547) groups=... context=u:r:untrusted_app_34:s0:c35,c258,c512,c768
pwd        → /data/data/com.termux/files/home
git        → 2.54.0
python3    → 3.13.13
node       → v25.8.2
npm        → 11.13.0
git status → fatal: not a git repository (expected — home is not a git repo)
EXIT:0     → (command chain exit 0, individual cmds OK)
```

**Note:** `which` command is not available on Termux. `command -v` can be used instead.

## OpenClaw Version

2026.4.21 (running on Termux/Android 14, arm64)

## ⚠️ Warning

**DO NOT update OpenClaw without preserving this patch.**

If OpenClaw auto-updates or the user runs `openclaw update`, the patched exec file will be overwritten and exec will break again.

Before any update:
1. Backup the patched `exec-_fLrb4o0.js`
2. Check if the new version includes a fix for Termux exec
3. Re-apply patch if needed after update

## Session Context

Recovery initiated via webchat. User is pr0dus. Exec tool restored and validated.