# Infinity Plugin Status

## Two Plugin Instances

### 1. `plugins/infinity/` — Main Commercial Plugin
- **Path:** `/data/data/com.termux/files/home/.openclaw/workspace/plugins/infinity/`
- **Status:** `manifest.json` shows `enabled: false`
- **Kind:** Commercial "Session immortality layer"
- **Entry:** `index.js` (has full implementation)
- **Hooks:** `hooks/` directory (on_capture, on_restore, etc.)
- **Storage:** `storage/`, `capsule/` directories
- **License:** `.openclaw/licenses/infinity-license.json` (production license, 1oc tier, expires 2027-04-09)
- **License binding:** installId `website-oc-install-001`, hostname `website-oc-host`, workspace `/var/www/website-oc`
- **Config:** `config.js` — `autoCaptureEnabled: true`, `autoRestoreEnabled: true`, `retentionMs: 2h`
- **Capabilities:** capture, restore (from manifest)

### 2. `plugins/infinity-internal/` — Staged Placeholder
- **Path:** `/data/data/com.termux/files/home/.openclaw/workspace/plugins/infinity-internal/`
- **Status:** `manifest.json` shows `enabled: true`
- **Kind:** "Staged restart capsule plugin placeholder for SAFE STEP 1"
- **Entry:** `index.js` (updated 2026-04-22 18:00-18:01 — recently modified)
- **Storage:** `storage.js` (added 2026-04-22 18:00)
- **License:** None (uses main plugin's license)
- **Capabilities:** capture, restore (from manifest)

## Known Issues

1. **Main plugin disabled** — `infinity` has `enabled: false` in manifest
2. **Binding mismatch** — license is bound to `website-oc-host` / `/var/www/website-oc`, but running on Android (Termux)
3. **License not yet validated** — `lastValidated: null` in license audit block
4. **`infinity-internal` recently modified** — `index.js` and `storage.js` updated 2026-04-22 18:00-18:01 — possibly partial state

## What Should Be Checked First in Fresh Session

1. Read `plugins/infinity/index.js` to understand the full initialization flow
2. Read `plugins/infinity-internal/index.js` to understand what was staged
3. Check `plugins/infinity/hooks/` directory for available hook handlers
4. Check `plugins/infinity/storage/` and `plugins/infinity-internal/storage/` for any saved capsule data
5. Check `.openclaw/capsules/` for any existing capsules
6. Assess whether `infinity-internal` is a stepping-stone toward enabling the main plugin
7. Determine the minimal path to get the commercial `infinity` plugin enabled and functional
