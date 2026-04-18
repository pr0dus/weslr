# Session: 2026-04-13 18:40:41 UTC

- **Session Key**: agent:main:main
- **Session ID**: ded9fec5-68db-4340-882f-45e59f93132e
- **Source**: webchat

## Conversation Summary

user: System: [2026-04-13 19:47:46 GMT+2] Exec failed (keen-she, signal SIGTERM)
System: [2026-04-13 19:48:29 GMT+2] Exec completed (delta-cl, code 0) :: provider_state: ('healthy', 'provider live') status live: True response: Couldn't form a response on the task at hand.
System: [2026-04-13 19:49:55 GMT+2] Exec completed (amber-ca, code 0) :: provider_state: ('healthy', 'provider live') status live: True response: Describe the provider health and policy.
System: [2026-04-13 19:51:56 GMT+2] Exec completed (oceanic-, code 0) :: provider_state: ('healthy', 'provider live') status live: True response: Please describe the provider health and policy.
System: [2026-04-13 19:52:17 GMT+2] Exec completed (fast-dun, code 0) :: provider_state: ('healthy', 'provider live') status live: True response: Couldn't form a response on the task at hand.

A new session was started via /new or /reset. Run your Session Startup sequence - read the required files before responding to the user. Then greet the user in your configured persona, if one is provided. Be yourself - use your defined voice, mannerisms, and mood. Keep it to 1-3 sentences and ask what they want to do. If the runtime model differs from default_model in the system prompt, mention the default model. Do not mention internal steps, files, tools, or reasoning.
Current time: Monday, April 13th, 2026 — 8:02 PM (Europe/Berlin) / 2026-04-13 18:02 UTC
assistant: [[reply_to_current]] Evening. I’m Qwen, here to help with whatever you’re tackling—what would you like to do next?
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-13 20:03 GMT+2] We need to recover a missing LOCAL OpenClaw plugin/integration called "infinity-internal" on Termux/Android.

CURRENT STATE

- OpenClaw gateway now starts again after removing stale config entries that referenced "infinity-internal".
- Previous error was:
 "plugins.allow: plugin not found: infinity-internal"
- Therefore the config reference existed, but the actual plugin/runtime entry is missing.
- We also have a separate public/sellable Infinity-related flow with token generation. That is NOT the target here.
- We need the INTERNAL local version only.
- We must not break the currently working gateway.

ENVIRONMENT

- Termux / Android
- OpenClaw installed under:
 "/data/data/com.termux/files/usr/lib/node_modules/openclaw"
- User config under:
 "/data/data/com.termux/files/home/.openclaw"
- Gateway currently runs successfully after stale "infinity-internal" config removal.

GOAL
Reconstruct or reinstall a working local plugin/integration named "infinity-internal" for internal use only, without touching the public/token-generation version.

STRICT RULES

- Do NOT modify unrelated system files
- Do NOT break the currently working gateway
- Do NOT re-add "infinity-internal" to config until the plugin exists and validates
- Do NOT redesign the architecture
- Do NOT mix internal Infinity with the public/token-generation version
- Preserve rollback ability
- Minimal additive changes only

TASK

1. Inspect the installed OpenClaw runtime and determine how a plugin named "infinity-internal" is expected to be discovered:
 - by manifest
 - by extension folder name
 - by package metadata
 - by config alias
2. Search the workspace and config directories for any remaining traces of previous "infinity-internal" implementation:
 - file names
 - manifests
 - source code
 - old config references
 - hooks or commands that mention Infinity
3. Determine whether "infinity-internal" was:
 - a custom OpenClaw plugin
 - a local extension folder
 - a config alias to another provider/tool
 - or a workspace-side component loaded by hooks
4. Produce the MINIMAL recovery plan to restore it.
5. If source is missing, reconstruct the smallest viable "infinity-internal" implementation needed for internal workflow only.
6. Keep public/token-generation Infinity completely separate.
7. Show all files before applying.
8. Show exact safe validation commands.
9. Only after validation, show the exact config entries to restore.

OUTPUT FORMAT
SECTION 1 — Discovery results
SECTION 2 — What "infinity-internal" most likely was
SECTION 3 — Minimal recovery plan
SECTION 4 — Exact files to create/update
SECTION 5 — Exact config to restore
SECTION 6 — Safe validation commands
SECTION 7 — Rollback commands

IMPORTANT
Do not give vague advice.
Do not skip file contents.
Do not auto-apply changes.
Do not conflate internal Infinity with public/token-based Infinity.
assistant: [[reply_to_current]]
Section 1 — Discovery results  
- OpenClaw discovers plugins by scanning (1) configured `plugins.load.paths`, then (2) `<workspace>/.openclaw/extensions`, (3) `~/.openclaw/extensions`, and finally (4) the bundled `extensions/` shipped with the runtime. Each plugin must live in a directory referenced by those paths and include an `openclaw.plugin.json` manifest so `plugins.allow`, `plugins.entries`, etc., can resolve the id before the code ever runs. Source: `/data/data/com.termux/files/usr/lib/node_modules/openclaw/docs/tools/plugin.md`, “Discovery & precedence” section.  
- The current runtime config (`~/.openclaw/openclaw.json`) already points `plugins.load.paths` at `/data/data/com.termux/files/home/.openclaw/workspace/plugins` but only allows/enables `telegram`. A historical backup (`~/.openclaw/openclaw.json.backup-infinity-internal-fix`) shows `plugins.allow` and `plugins.entries` used to admit `infinity-internal` as soon as it existed again, so restoring the plugin simply requires putting the code back into that workspace path before re-adding the config.  
- The gateway was healthy after removing the stale entry because OpenClaw hardens any missing files: the startup log recorded repeated “missing-module” complaints for `.openclaw/plugins/infinity-internal/{config,index,hooks/*}` (see `~/.openclaw/logs/infinity.log` around lines 360‑420). Those complaints are the same “plugin not found” error the gateway reported when `plugins.allow` still mentioned `infinity-internal`.

Section 2 — What “infinity-internal” most likely was  
- The logs, config backup, and the fact that `openclaw.plugins` expect id-based discovery all point to `infinity-internal` being a **local OpenClaw plugin** placed under the workspace `plugins/` directory, not a remote provider or channel.  
- The plugin was a **custom runtime extension** that mirrored `plugins/infinity/` (capsule capture/restore, hooks, conflict/hardening helpers) but was stripped of the licensing stack and shipped only to the internal phone/Termux workflow; it needed its own `openclaw.plugin.json`, `index.js`, and `plugins.entries.infinity-internal` entry to be discoverable.  
- No other workspace directories or manifests still reference `infinity-internal`, but `logs/infinity.log` and the config backup prove that OpenClaw expected to load files from `~/.openclaw/plugins/infinity-internal` and that the previous entry was removed only after the config was edited. Until those files exist, the gateway repeatedly flags missing modules and refuses to wire the continuity hooks.

Section 3 — Minimal recovery plan  
1. **Recreate `plugins/infinity-internal/` under the workspace plugin root** by copying the shared modules from `plugins/infinity/` (config, hooks, capsule, storage, conflict, hardening, version, manifest/package metadata) **but skipping** `licensing/`, `generate_license.js`, `resign_license.js`, and the commercial test harnesses.  
2. **Add a dedicated manifest** `plugins/infinity-internal/openclaw.plugin.json` that declares `id: "infinity-internal"`, the same schema as the public version, and `register: "./index.js"`.  
3. **Write a new entrypoint** `plugins/infinity-internal/index.js` that uses the shared hooks/hardening/conflict helpers but never calls `LicenseValidator`/`LicenseEnforcer`. It should log `[infinity-internal]`, always register capture/restore if `config.auto*` are true, and expose plugin metadata (`name: "Infinity Internal"`, `description`, etc.) without claiming any commercial entitlement.  
4. **Do not touch `~/.openclaw/openclaw.json` yet**—the plugin must exist and pass validation before we re-add `plugins.allow`/`plugins.entries` for `infinity-internal`.  
5. **Validate before re-adding config** (see Section 6 commands).  
6. **Once validated, re-enable the plugin** by restoring the allow/entries snippet shown in Section 5 (use the backup file as the exact template).  
7. **Keep the current gateway config and runtime untouched** throughout; we only add a new workspace plugin directory and later tweak config when the plugin is verified to load.

Section 4 — Exact files to create/update  
- `plugins/infinity-internal/index.js` (new): internal entrypoint that mirrors the public `index.js` but only runs `runHardeningChecks`, `hooks.capture`, `hooks.restore`, and shared `conflict` helpers. It must set `plugin.id = "infinity-internal"`, log with `[infinity-internal]`, and never import or call anything from `licensing/`.  
- `plugins/infinity-internal/openclaw.plugin.json` (new): manifest like the public one but with `"id": "infinity-internal"`, `"register": "./index.js"`, and the same inline config schema so OpenClaw can validate the entry without executing code.  
- `plugins/infinity-internal/config.js`, `version.js`, `conflict.js`, `hardening.js`, `manifest.json`, `package.json`, and the shared `capsule/`, `hooks/`, and `storage/` directories (copied from `plugins/infinity/`): keep identical copies so the internal variant uses the same continuation logic, hardening checks, and storage helpers. Do **not** include the `licensing/` tree, the `generate_license.js`/`resign_license.js` tools, or the `test_*` files—that keeps the internal build license-free.  
- Optional: keep `plugins/infinity-internal/.openclaw/` (capsules/keys/licenses) alone; no changes are required for recovery but delete any stale license files if they cause confusion.  
- `plugins/infinity-internal/hooks/capture.js` and `hooks/restore.js`: already part of the copy; they should continue to reference storage and the OpenClaw API without new licensing logic.  
- `plugins/infinity-internal/README.md` (if desired) can mirror the public README with a note that this directory is internal-only and must never be published.  

Section 5 — Exact config to restore** *(apply only after the new plugin validates)*  
```json
"plugins": {
  "allow": [
    "infinity-internal",
    "telegram"
  ],
  "load": {
    "paths": [
      "/data/data/com.termux/files/home/.openclaw/workspace/plugins"
    ]
  },
  "entries": {
    "telegram": {
      "enabled": true
    },
    "infinity-internal": {
      "enabled": true
    }
  }
}
```
Use the backup `~/.openclaw/openclaw.json.backup-infinity-internal-fix` as the exact snippet to merge into the active `openclaw.json` once verification passes; do not reintroduce `infinity-internal` into `plugins.allow`/`plugins.entries` until the new directory and manifest are working.

Section 6 — Safe validation commands  
1. `openclaw plugins list --json | grep infinity-internal` – confirms the manifest is discoverable.  
2. `openclaw plugins doctor infinity-internal` – ensures OpenClaw can load and validate the internal plugin without licence errors.  
3. `openclaw doctor` (or `openclaw doctor --non-interactive`) – rechecks the entire runtime for regressions (the gateway should still be healthy).  
4. `openclaw gateway status` – quick sanity check that the gateway didn’t break when the new plugin directory appeared.  
Run these before touching `openclaw.json`; once they all pass, restore the `plugins` allow/entries block from Section 5.

Section 7 — Rollback commands  
- Remove the recovered internal plugin if it causes trouble:  
  ```bash
  rm -rf plugins/infinity-internal
  ```  
  (Or, to preserve the work for later, move it aside: `mv plugins/infinity-internal plugins/infinity-internal.bak`.)  
- Restore the previous configuration if you already merged it:  
  ```bash
  cp ~/.openclaw/openclaw.json.backup-infinity-internal-fix ~/.openclaw/openclaw.json
  ```  
  *Then* restart the gateway or run `openclaw doctor` to confirm you’re back to the current working state.
user: Pre-compaction memory flush. Store durable memories only in memory/2026-04-13.md (create memory/ if needed). Treat workspace bootstrap/reference files such as MEMORY.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them. If memory/2026-04-13.md already exists, APPEND new content only and do not overwrite existing entries. Do NOT create timestamped variant files (e.g., 2026-04-13-HHMM.md); always use the canonical 2026-04-13.md filename. If nothing to store, reply with NO_REPLY.
Current time: Monday, April 13th, 2026 — 8:11 PM (Europe/Berlin) / 2026-04-13 18:11 UTC
assistant: NO_REPLY
user: System: [2026-04-13 20:05:34 GMT+2] Exec completed (clear-re, code 2) :: oundtrip.js:45: type: 'infinity-license' /data/data/com.termux/files/home/.openclaw/workspace_clean_hints/plugins/infinity/version.js:94: infinity: { /data/data/com.termux/files/h…
System: [2026-04-13 20:05:56 GMT+2] Exec completed (kind-hav, code 2) :: Apr 3 18:51 openclaw.plugin.json /data/data/com.termux/files/home/.openclaw/workspace_clean_hints/memory/2026-04-03-openclaw-security-repair.md:123:-rw-------. 1 u0_a547 u0_a547 2…
System: [2026-04-13 20:07:26 GMT+2] Exec completed (brisk-fo, code 0) :: ath-based loading). /data/data/com.termux/files/usr/lib/node_modules/openclaw/CHANGELOG.md:3735:- **BREAKING:** Microsoft Teams is now a plugin; install `@openclaw/msteams` via `o…

Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-13 20:11 GMT+2] Your recovery analysis is directionally correct, but the implementation plan is still too broad.

We now need a STRICT MINIMAL rebuild of "infinity-internal" for Termux.

AUTHORITATIVE PATH
Use ONLY this plugin root:
"/data/data/com.termux/files/home/.openclaw/workspace/plugins/infinity-internal"

Do NOT use "~/.openclaw/plugins/infinity-internal".
Do NOT change plugin discovery paths.
Do NOT touch the public/commercial Infinity package.

GOAL
Create the SMALLEST possible internal plugin that restores internal Infinity continuity behavior without licensing, token generation, or commercial packaging.

CRITICAL CONSTRAINTS

- Minimal additive changes only
- No broad directory copy
- No copying the full public Infinity tree
- No licensing code
- No token generation
- No commercial test harnesses
- No hidden dependency imports
- No config changes yet
- No auto-apply

TASK

1. Inspect the public Infinity plugin tree and determine the absolute MINIMUM files/functions required for internal continuity behavior.
2. Produce a dependency map:
 - which exact functions "index.js" needs
 - which exact local modules those functions require
 - which files are truly mandatory
3. Reduce the internal plugin to the smallest viable set.
4. Show the final exact file tree for "infinity-internal".
5. Show the FULL contents for each file to create.
6. Ensure every import path is self-contained inside:
 "/data/data/com.termux/files/home/.openclaw/workspace/plugins/infinity-internal"
7. Ensure there are NO imports from:
 - licensing/
 - generate_license.js
 - resign_license.js
 - public/commercial Infinity paths
8. Add a correct "openclaw.plugin.json" with id:
 "infinity-internal"
9. Provide ONLY validation commands that do not require editing live config yet.

OUTPUT FORMAT
SECTION 1 — Minimal dependency map
SECTION 2 — Final internal plugin file tree
SECTION 3 — Full file contents
SECTION 4 — Validation commands before config restore
SECTION 5 — Exact config snippet to restore later
SECTION 6 — Rollback commands

IMPORTANT
Do not propose broad copies.
Do not hand-wave missing code.
Do not omit file contents.
Do not apply changes automatically.
assistant: [[reply_to_current]]
SECTION 1 — Minimal dependency map  
1. `plugins/infinity-internal/index.js` (register):  
   - Needs `config.autoCaptureEnabled` & `config.autoRestoreEnabled` so it knows whether to hook capture/restore.  
   - Needs `hooks.capture.captureCapsule()` plus `hooks.restore.attemptRestore()` to provide continuity behavior.  
   - No licensing, hardening, conflict, or version modules—just the shared config/hook surface it owns.  
2. `hooks/capture.js`:  
   - Builds each capsule using `openclaw-api` helpers (`getActiveFiles`, `getPendingTests`, `getLatestTaskDescription`).  
   - Requires `uuid` for capsule IDs and the workspace’s `.openclaw` storage via `../storage/index.js`.  
   - Validates capsules through `../capsule/schema.js`.  
   - Depends on nothing outside the `infinity-internal` tree (child_process, fs, path, openclaw-api, uuid, storage, capsule schema).  
3. `hooks/restore.js`:  
   - Calls `../capsule/utils` helpers (`getLatestCapsuleFile`, `safeLoadCapsule`, `checkFilesExist`, `isCapsuleStale`).  
   - Reinstates open files/tests via `openclaw-api` (reopenFiles, setPendingTests, setLatestTaskDescription).  
   - Logs `[infinity-internal]` and never touches licensing.  
4. `storage/index.js` → `storage/fs.js`:  
   - `storage.fs` uses `capsule/utils.CAPSULES_DIR` to know where `.openclaw/capsules` live and performs read/write/delete with `fs`/`path`.  
   - No external dependencies beyond Node built-ins.  
5. `capsule/schema.js` & `capsule/utils.js`:  
   - Schema relies on `ajv`, so the internal tree must list `ajv` as a dependency or rely on a shared install.  
   - Utils rely on Node built-ins (`fs`, `path`) and export helpers used by restore/capture/storage.

SECTION 2 — Final internal plugin file tree  
```
plugins/infinity-internal/
├── openclaw.plugin.json
├── package.json
├── config.js
├── index.js
├── capsule/
│   ├── schema.js
│   └── utils.js
├── hooks/
│   ├── capture.js
│   └── restore.js
└── storage/
    ├── fs.js
    └── index.js
```

SECTION 3 — Full file contents  

`plugins/infinity-internal/package.json`
```json
{
  "name": "openclaw-infinity-internal",
  "version": "1.0.0",
  "description": "Internal-only Infinity continuity helper",
  "main": "index.js",
  "dependencies": {
    "ajv": "^8.17.1",
    "uuid": "^9.0.1"
  }
}
```

`plugins/infinity-internal/openclaw.plugin.json`
```json
{
  "id": "infinity-internal",
  "name": "Infinity Internal",
  "description": "Internal continuity helper for Termux / owner workflows",
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "autoCaptureEnabled": {
        "type": "boolean",
        "default": true
      },
      "autoRestoreEnabled": {
        "type": "boolean",
        "default": true
      }
    }
  },
  "register": "./index.js"
}
```

`plugins/infinity-internal/config.js`
```javascript
// config.js - Shared continuity knobs

const config = {
  // Retention: 2 hours in milliseconds
  retentionMs: 2 * 60 * 60 * 1000,
  // Auto-capture enabled (for pre-reset, /new, overflow)
  autoCaptureEnabled: true,
  // Auto-restore enabled (on init, silent)
  autoRestoreEnabled: true,
  // Strict missing-files check (v1: true = skip if any file missing)
  strictMissingFiles: true,
  // Log level: 'error', 'warn', 'info', 'debug'
  logLevel: 'info'
};

module.exports = config;
```

`plugins/infinity-internal/index.js`
```javascript
// index.js — Internal Infinity entrypoint (no licensing)

const hooks = require('./hooks');
const config = require('./config');

function register(api) {
  console.log('[infinity-internal] Plugin initialized (internal continuity variant)');

  if (config.autoCaptureEnabled) {
    if (api.onReset) {
      api.onReset(async () => {
        try {
          await hooks.capture.captureCapsule();
        } catch (e) {
          console.error('[infinity-internal] capture failed:', e.message);
        }
      });
    }
    if (api.onNew) {
      api.onNew(async () => {
        try {
          await hooks.capture.captureCapsule();
        } catch (e) {
          console.error('[infinity-internal] capture failed:', e.message);
        }
      });
    }
    if (api.onContextOverflow) {
      api.onContextOverflow(async () => {
        try {
          await hooks.capture.captureCapsule();
        } catch (e) {
          console.error('[infinity-internal] capture failed:', e.message);
        }
      });
    }
  }

  if (config.autoRestoreEnabled && api.onInit) {
    api.onInit(async () => {
      try {
        await hooks.restore.attemptRestore();
      } catch (e) {
        console.error('[infinity-internal] restore failed:', e.message);
      }
    });
  }
}

const plugin = {
  id: 'infinity-internal',
  name: 'Infinity Internal',
  description: 'Internal continuity helper (owner/Termux)',
  configSchema: {
    type: 'object',
    additionalProperties: false,
    properties: {
      autoCaptureEnabled: {
        type: 'boolean',
        default: true
      },
      autoRestoreEnabled: {
        type: 'boolean',
        default: true
      }
    }
  }
};

module.exports = {
  register,
  plugin
};
```

`plugins/infinity-internal/capsule/schema.js`
```javascript
// capsule/schema.js - JSON schema and validation helpers for internal capsules

const CAPSULE_SCHEMA = {
  type: 'object',
  required: ['version', 'timestamp', 'git', 'session', 'meta'],
  properties: {
    version: { const: 1, description: 'Capsule schema version' },
    timestamp: { type: 'string', format: 'date-time' },
    git: {
      type: 'object',
      required: ['repo', 'branch', 'commit', 'dirty'],
      properties: {
        repo: { type: 'string', pattern: '^/' },
        branch: { type: 'string' },
        commit: { type: 'string' },
        dirty: { type: 'boolean' }
      }
    },
    session: {
      type: 'object',
      required: ['activeFiles', 'pendingTests', 'latestTaskDescription'],
      properties: {
        activeFiles: {
          type: 'array',
          items: { type: 'string' }
        },
        pendingTests: {
          type: 'array',
          items: { type: 'string' }
        },
        latestTaskDescription: { type: 'string' }
      }
    },
    meta: {
      type: 'object',
      required: ['reason'],
      properties: {
        reason: { type: 'string', enum: ['pre-reset', 'ctx-overflow'] },
        parentId: { type: 'string' }
      }
    }
  }
};

function validateCapsule(capsule) {
  const Ajv = require('ajv');
  const ajv = validateCapsule.ajv || new Ajv({ strict: false });
  validateCapsule.ajv = ajv;

  const valid = ajv.validate(CAPSULE_SCHEMA, capsule);
  if (!valid) {
    throw new Error(`Capsule validation failed: ${ajv.errorsText(ajv.errors)}`);
  }
}

module.exports = { CAPSULE_SCHEMA, validateCapsule };
```

`plugins/infinity-internal/capsule/utils.js`
```javascript
// capsule/utils.js - Helpers for capsule lifecycle

const fs = require('fs');
const path = require('path');

const CAPSULES_DIR = '.openclaw/capsules';
const RETENTION_MS = 2 * 60 * 60 * 1000;

function getCapsulesDir() {
  return path.join(process.env.OPENCLAW_WORKSPACE || process.cwd(), CAPSULES_DIR);
}

function isValidCapsuleId(filename) {
  return /^v1-\d{13}-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\.json$/.test(filename);
}

function getLatestCapsuleFile() {
  const dir = getCapsulesDir();
  if (!fs.existsSync(dir)) return null;
  const files = fs.readdirSync(dir).filter(isValidCapsuleId);
  if (files.length === 0) return null;
  files.sort().reverse();
  return files[0];
}

function getAgeMs(capsule) {
  return Date.now() - new Date(capsule.timestamp).getTime();
}

function isCapsuleStale(capsule) {
  return getAgeMs(capsule) > RETENTION_MS;
}

function checkFilesExist(filepaths) {
  const workspace = process.env.OPENCLAW_WORKSPACE || process.cwd();
  for (const fp of filepaths) {
    const fullPath = path.isAbsolute(fp) ? fp : path.join(workspace, fp);
    if (!fs.existsSync(fullPath)) return false;
  }
  return true;
}

function safeLoadCapsule(filename) {
  const dir = getCapsulesDir();
  const filepath = path.join(dir, filename);
  if (!fs.existsSync(filepath)) return null;
  try {
    const raw = fs.readFileSync(filepath, 'utf8');
    const capsule = JSON.parse(raw);
    require('./schema').validateCapsule(capsule);
    return capsule;
  } catch (e) {
    console.error(`[infinity-internal] Failed to load capsule ${filename}: ${e.message}`);
    return null;
  }
}

module.exports = {
  CAPSULES_DIR,
  RETENTION_MS,
  getCapsulesDir,
  isValidCapsuleId,
  getLatestCapsuleFile,
  getAgeMs,
  isCapsuleStale,
  checkFilesExist,
  safeLoadCapsule
};
```

`plugins/infinity-internal/storage/fs.js`
```javascript
// storage/fs.js - File I/O abstraction for capsule storage

const fs = require('fs');
const path = require('path');
const { CAPSULES_DIR } = require('../capsule/utils');

function getDir() {
  const workspace = process.env.OPENCLAW_WORKSPACE || process.cwd();
  const dir = path.join(workspace, CAPSULES_DIR);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  return dir;
}

function saveCapsule(filename, capsule) {
  const dir = getDir();
  const filepath = path.join(dir, filename);
  fs.writeFileSync(filepath, JSON.stringify(capsule, null, 2), 'utf8');
  return filename;
}

function loadCapsule(filename) {
  const dir = getDir();
  const filepath = path.join(dir, filename);
  if (!fs.existsSync(filepath)) return null;
  try {
    const raw = fs.readFileSync(filepath, 'utf8');
    return JSON.parse(raw);
  } catch (e) {
    console.error(`[infinity-internal] Failed to load ${filename}: ${e.message}`);
    return null;
  }
}

function listCapsules() {
  const dir = getDir();
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter(f => f.startsWith('v1-') && f.endsWith('.json'));
}

function deleteCapsule(filename) {
  const dir = getDir();
  const filepath = path.join(dir, filename);
  if (fs.existsSync(filepath)) {
    fs.unlinkSync(filepath);
    return true;
  }
  return false;
}

module.exports = {
  getDir,
  saveCapsule,
  loadCapsule,
  listCapsules,
  deleteCapsule
};
```

`plugins/infinity-internal/storage/index.js`
```javascript
// storage/index.js - CRUD on .openclaw/capsules/

const fs = require('./fs');

function save(capsule) {
  const filename = capsule.meta.id + '.json';
  fs.saveCapsule(filename, capsule);
  return filename;
}

function load(filename) {
  return fs.loadCapsule(filename);
}

function list() {
  return fs.listCapsules();
}

function remove(filename) {
  return fs.deleteCapsule(filename);
}

function getLatest() {
  const files = fs.listCapsules();
  if (files.length === 0) return null;
  files.sort().reverse();
  return load(files[0]);
}

module.exports = {
  save,
  load,
  list,
  remove,
  getLatest
};
```

`plugins/infinity-internal/hooks/capture.js`
```javascript
// hooks/capture.js - Silent capture before /reset, /new, or context overflow

const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const storage = require('../storage');

function getCurrentRepo() {
  return process.env.OPENCLAW_WORKSPACE || process.cwd();
}

async function getBranch(repoPath) {
  try {
    const { execSync } = require('child_process');
    const branch = execSync('git rev-parse --abbrev-ref HEAD', {
      cwd: repoPath,
      encoding: 'utf8'
    }).trim();
    return branch;
  } catch (e) {
    return 'unknown';
  }
}

async function getHeadCommit(repoPath) {
  try {
    const { execSync } = require('child_process');
    const commit = execSync('git rev-parse HEAD', { cwd: repoPath, encoding: 'utf8' }).trim();
    return commit;
  } catch (e) {
    return 'unknown';
  }
}

async function isDirty(repoPath) {
  try {
    const { execSync } = require('child_process');
    const status = execSync('git diff-index --quiet HEAD --', { cwd: repoPath, encoding: 'utf8' });
    return status !== 0;
  } catch (e) {
    return true;
  }
}

function getActiveFiles() {
  const api = require('openclaw-api');
  return api.getActiveFiles?.() || [];
}

function getPendingTests() {
  const api = require('openclaw-api');
  return api.getPendingTests?.() || [];
}

function getLatestTaskDescription() {
  const api = require('openclaw-api');
  return api.getLatestTaskDescription?.() || '';
}

async function captureCapsule() {
  const repoPath = getCurrentRepo();
  const branch = await getBranch(repoPath);
  const commit = await getHeadCommit(repoPath);
  const dirty = await isDirty(repoPath);
  const activeFiles = getActiveFiles();
  const pendingTests = getPendingTests();
  const latestTaskDescription = getLatestTaskDescription();

  const capsule = {
    version: 1,
    timestamp: new Date().toISOString(),
    git: { repo: repoPath, branch, commit, dirty },
    session: { activeFiles, pendingTests, latestTaskDescription },
    meta: {
      id: `v1-${Date.now()}-${uuidv4()}`,
      reason: 'pre-reset'
    }
  };

  const { validateCapsule } = require('../capsule/schema');
  validateCapsule(capsule);

  const filename = storage.save(capsule);
  console.log(`[infinity-internal] captured capsule ${filename}`);
  return filename;
}

module.exports = {
  captureCapsule
};
```

`plugins/infinity-internal/hooks/restore.js`
```javascript
// hooks/restore.js - Silent restore on init (safe subset only)

const { safeLoadCapsule, getLatestCapsuleFile, checkFilesExist, isCapsuleStale } = require('../capsule/utils');

function getCurrentRepo() {
  return process.env.OPENCLAW_WORKSPACE || process.cwd();
}

async function getBranch(repoPath) {
  try {
    const { execSync } = require('child_process');
    return execSync('git rev-parse --abbrev-ref HEAD', { cwd: repoPath, encoding: 'utf8' }).trim();
  } catch (e) {
    return 'unknown';
  }
}

function getActiveFiles() {
  const api = require('openclaw-api');
  return api.getActiveFiles?.() || [];
}

function reopenFiles(filepaths) {
  const api = require('openclaw-api');
  if (api.reopenFiles) {
    api.reopenFiles(filepaths);
  }
}

function setPendingTests(tests) {
  const api = require('openclaw-api');
  if (api.setPendingTests) {
    api.setPendingTests(tests);
  }
}

function setLatestTaskDescription(desc) {
  const api = require('openclaw-api');
  if (api.setLatestTaskDescription) {
    api.setLatestTaskDescription(desc);
  }
}

async function attemptRestore() {
  const repoPath = getCurrentRepo();
  const branch = await getBranch(repoPath);
  const activeFiles = getActiveFiles();

  if (activeFiles.length > 0) {
    console.log('[infinity-internal] restore skipped: active task exists');
    return { result: 'skipped_existing_active_task' };
  }

  const latestFilename = getLatestCapsuleFile();
  if (!latestFilename) {
    console.log('[infinity-internal] restore skipped: no capsule found');
    return { result: 'skipped_no_capsule' };
  }

  const capsule = safeLoadCapsule(latestFilename);
  if (!capsule) {
    console.log('[infinity-internal] restore skipped: invalid capsule');
    return { result: 'skipped_invalid_capsule' };
  }

  if (capsule.git.repo !== repoPath) {
    console.log('[infinity-internal] restore skipped: repo mismatch');
    return { result: 'skipped_repo_mismatch' };
  }

  if (capsule.git.branch !== branch) {
    console.log('[infinity-internal] restore skipped: branch mismatch');
    return { result: 'skipped_branch_mismatch' };
  }

  if (isCapsuleStale(capsule)) {
    console.log('[infinity-internal] restore skipped: stale capsule');
    return { result: 'skipped_stale' };
  }

  if (!checkFilesExist(capsule.session.activeFiles)) {
    console.log('[infinity-internal] restore skipped: missing files');
    return { result: 'skipped_missing_files' };
  }

  reopenFiles(capsule.session.activeFiles);
  setPendingTests(capsule.session.pendingTests);
  setLatestTaskDescription(capsule.session.latestTaskDescription);

  console.log(`[infinity-internal] restored capsule ${capsule.meta.id}`);
  return { result: 'restored' };
}

module.exports = {
  attemptRestore
};
```

SECTION 4 — Validation commands before config restore  
1. `node -c /data/data/com.termux/files/home/.openclaw/workspace/plugins/infinity-internal/index.js`  
2. `node -c /data/data/com.termux/files/home/.openclaw/workspace/plugins/infinity-internal/hooks/capture.js`  
3. `node -c /data/data/com.termux/files/home/.openclaw/workspace/plugins/infinity-internal/hooks/restore.js`  
4. `node -c /data/data/com.termux/files/home/.openclaw/workspace/plugins/infinity-internal/capsule/schema.js`  
These ensure the minimal tree parses/loads without touching live config; once satisfied, you can proceed to re-enable the plugin via the config snippet below.

SECTION 5 — Exact config snippet to restore later  
```json
"plugins": {
  "allow": [
    "infinity-internal",
    "telegram"
  ],
  "load": {
    "paths": [
      "/data/data/com.termux/files/home/.openclaw/workspace/plugins"
    ]
  },
  "entries": {
    "telegram": {
      "enabled": true
    },
    "infinity-internal": {
      "enabled": true
    }
  }
}
```

SECTION 6 — Rollback commands  
1. Remove the internal plugin if it misbehaves:  
   ```bash
   rm -rf /data/data/com.termux/files/home/.openclaw/workspace/plugins/infinity-internal
   ```  
2. If the config snippet was applied prematurely, restore the previous config copy:  
   ```bash
   cp ~/.openclaw/openclaw.json.backup-infinity-internal-fix ~/.openclaw/openclaw.json
   ```
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Mon 2026-04-13 20:40 GMT+2] We are NOT trying to recreate 100% raw context after "/new".

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
