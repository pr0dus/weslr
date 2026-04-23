# Exact Next Steps — Fresh Session

## Step 1: Verify Runtime State
- Confirm Ollama is running locally at `127.0.0.1:11434`
- Confirm primary model is `ollama/minimax-m2.7:cloud` with maxTokens 16,384
- Confirm Telegram is disabled
- Check `sessions.json` for active session references

## Step 2: Read This Handoff
- Read all files in `reports/infinity_handoff_2026-04-22/` for full context
- Confirm workspace path: `/data/data/com.termux/files/home/.openclaw/workspace`

## Step 3: Inspect Infinity Files
Read in order:
1. `plugins/infinity/README.md` — overview and design
2. `plugins/infinity/index.js` — entry point and initialization
3. `plugins/infinity/manifest.json` — plugin contract
4. `plugins/infinity/openclaw.plugin.json` — config schema
5. `plugins/infinity/config.js` — current configuration
6. `plugins/infinity-internal/index.js` — what was staged
7. `plugins/infinity/hooks/` — available hook handlers

## Step 4: Check Capsule/Storage State
1. List `.openclaw/capsules/` — any existing capsules?
2. List `plugins/infinity/storage/` — any stored data?
3. List `plugins/infinity-internal/storage/` — any staged data?
4. Check `plugins/infinity/capsule/` — schema definitions

## Step 5: Determine Minimal Repair Order
Based on the inspection, determine:
1. Is `infinity-internal` a working subset of `infinity`?
2. Does the commercial license need re-binding for the current host?
3. What is the minimal change to enable the commercial `infinity` plugin?
4. Should `infinity` manifest `enabled` be flipped to `true`?
5. Does `infinity-internal` need to remain enabled alongside?

## Step 6: Avoid Broad Architecture Work
- Do not redesign the session-memory system
- Do not touch WESLR continuity files
- Do not trim or edit session JSONL files
- Keep changes minimal and focused on Infinity enablement
