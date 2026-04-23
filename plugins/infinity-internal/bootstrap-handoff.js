/**
 * Infinity Internal — Bootstrap Handoff
 * Compact restore payload for session-start injection.
 * This file is the exact shape a future session-start injector reads.
 * Kept intentionally minimal: no transcript, no large context.
 */

const { existsSync, readFileSync, writeFileSync, mkdirSync } = require("fs");
const path = require("path");

const HANDOFF_KEY = "bootstrap-handoff";
const CAPSULE_DATA_DIR = path.resolve(__dirname, ".capsule-data");
// INFINITY_HANDOFF.md lives in the workspace root, matching VALID_BOOTSTRAP_NAMES allowlist
const WORKSPACE_ROOT = path.resolve(__dirname, "..", "..");

function ensureStorageDir() {
  if (!existsSync(CAPSULE_DATA_DIR)) {
    mkdirSync(CAPSULE_DATA_DIR, { recursive: true });
  }
}

/**
 * Persist the bootstrap handoff record.
 * This is a minimal subset of the full capsule — just enough for a
 * session-start injector to prime continuity context without full restore.
 */
function persistHandoff(capsule) {
  try {
    ensureStorageDir();
    // Bootstrap handoff: intentionally minimal
    const handoff = {
      timestamp: Date.now(),
      branch: capsule.branch,
      commit: capsule.commit,
      hasGit: capsule.hasGit !== undefined ? capsule.hasGit : true,
      dirty: capsule.dirty,
      activeFiles: (capsule.activeFiles || []).slice(0, 16),
      latestTask: capsule.latestTask || null,
      reason: capsule.reason || "auto-capture",
      capsuleCommit: capsule.commit,
      capsuleReason: capsule.reason
    };
    const filePath = path.join(CAPSULE_DATA_DIR, `${HANDOFF_KEY}.json`);
    writeFileSync(filePath, JSON.stringify(handoff, null, 2), "utf8");

    // Also mirror as INFINITY_HANDOFF.md in workspace root so bootstrap-extra-files can include it
    const handoffMdPath = path.join(WORKSPACE_ROOT, "INFINITY_HANDOFF.md");
    const mdContent = [
      "---",
      "name: INFINITY_HANDOFF",
      'description: "Infinity compact continuity handoff"',
      'metadata: {"openclaw": {"auto": "infinity-internal"}}',
      "---",
      "",
      "# Infinity Continuity Handoff",
      "",
      `| Field | Value |`,
      `|---|---|`,
      `| timestamp | ${handoff.timestamp} |`,
      `| branch | ${handoff.branch ?? "—"} |`,
      `| commit | ${handoff.commit ?? "—"} |`,
      `| hasGit | ${handoff.hasGit} |`,
      `| dirty | ${handoff.dirty} |`,
      `| reason | ${handoff.reason} |`,
      `| activeFiles | ${(handoff.activeFiles || []).slice(0, 8).join(", ") || "none"} |`,
      `| latestTask | ${handoff.latestTask || "—"} |`,
      ""
    ].join("\n");
    writeFileSync(handoffMdPath, mdContent, "utf8");

    return { success: true, path: filePath };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/**
 * Load the bootstrap handoff record (if present).
 * Returns { found, data }.
 */
function loadHandoff() {
  try {
    const filePath = path.join(CAPSULE_DATA_DIR, `${HANDOFF_KEY}.json`);
    if (!existsSync(filePath)) {
      return { found: false };
    }
    const content = readFileSync(filePath, "utf8");
    const data = JSON.parse(content);
    return { found: true, data };
  } catch (err) {
    return { found: false, error: err.message };
  }
}

module.exports = { persistHandoff, loadHandoff };
module.exports.default = { persistHandoff, loadHandoff };
