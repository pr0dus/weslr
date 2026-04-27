# OCC Android/Termux exec Patch — Permanent Record

## File

`/data/data/com.termux/files/usr/lib/node_modules/openclaw/dist/exec-_fLrb4o0.js`

## Before (broken)

```js
spawn('/bin/bash', ['-c', cmd], {
  stdio: ['pipe', 'pipe', 'pipe'],
  ...
})
```

## After (fixed)

```js
const child = spawn('/bin/bash', ['-i'], {
  stdio: ['pipe', 'pipe', 'pipe'],
  ...
})
child.stdin.write(cmd + '\n')
```

## Why default failed

Termux Android: bash -c with piped stdin broken after OpenClaw update. Pipe hangs/times out on every command. No exec works → OCC tool broken.

## Why bash -i + stdin works

`bash -i` forces interactive shell initialization with working stdin channel. Writing `innerCmd + newline` via stdin bypasses the broken pipe entirely.

## ⚠️ OpenClaw update will overwrite this

Every `openclaw update` or gateway update.run replaces `exec-_fLrb4o0.js`. exec breaks again after update without this patch.

## Recovery steps after update

1. Re-apply stdin write patch to exec-_fLrb4o0.js
2. Test: `git --version` must return version string
3. Confirm EXIT:0
4. Update this file to reflect new version
5. If unsure, restore from backup before running update