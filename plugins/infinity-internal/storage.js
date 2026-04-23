/**
 * Infinity Internal — Storage Backend
 * Provides persist() and load() for capsule data.
 * Storage path: <plugin-dir>/.capsule-data/<key>.json
 */

const { existsSync, mkdirSync, readFileSync, writeFileSync } = require("fs");
const path = require("path");

// Resolve storage directory relative to this file's location
const CAPSULE_DATA_DIR = path.resolve(__dirname, ".capsule-data");

/**
 * Ensure the capsule data directory exists.
 * Creates .capsule-data/ if missing.
 */
function ensureStorageDir() {
  if (!existsSync(CAPSULE_DATA_DIR)) {
    mkdirSync(CAPSULE_DATA_DIR, { recursive: true });
  }
}

/**
 * Persist a capsule record to storage.
 * @param {string} key - Storage key (e.g., "latest-capsule")
 * @param {object} data - Serializable capsule data
 * @returns {{ success: boolean, path: string, error?: string }}
 */
function persist(key, data) {
  try {
    ensureStorageDir();
    const filePath = path.join(CAPSULE_DATA_DIR, `${key}.json`);
    const payload = JSON.stringify(data, null, 2);
    writeFileSync(filePath, payload, "utf8");
    return { success: true, path: filePath };
  } catch (err) {
    return { success: false, error: err.message, path: null };
  }
}

/**
 * Load a capsule record from storage.
 * @param {string} key - Storage key (e.g., "latest-capsule")
 * @returns {{ found: boolean, data: object|null, error?: string }}
 */
function load(key) {
  try {
    const filePath = path.join(CAPSULE_DATA_DIR, `${key}.json`);
    if (!existsSync(filePath)) {
      return { found: false, data: null };
    }
    const content = readFileSync(filePath, "utf8");
    const data = JSON.parse(content);
    return { found: true, data };
  } catch (err) {
    return { found: false, data: null, error: err.message };
  }
}

module.exports = { persist, load };
module.exports.default = { persist, load };