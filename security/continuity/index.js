#!/usr/bin/env node
/**
 * security/continuity/index.js - Continuity Protection (Scaffold)
 * Phase 1: State checksums and integrity verification
 */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, "..", "..");

const CONTINUITY_DIR = path.join(projectRoot, ".openclaw", "continuity");
const BASELINE_FILE = path.join(CONTINUITY_DIR, "baseline.json");
const CHECKSUM_FILE = path.join(CONTINUITY_DIR, "checksums.json");

/**
 * Initialize continuity infrastructure
 */
export async function initContinuity() {
  try {
    await fs.mkdir(CONTINUITY_DIR, { recursive: true });

    // Create baseline if not exists
    try {
      await fs.access(BASELINE_FILE);
    } catch {
      await fs.writeFile(BASELINE_FILE, JSON.stringify({
        version: "1.0",
        createdAt: new Date().toISOString(),
        modules: {}
      }, null, 2));
    }

    // Create checksums file
    try {
      await fs.access(CHECKSUM_FILE);
    } catch {
      await fs.writeFile(CHECKSUM_FILE, JSON.stringify({
        version: "1.0",
        lastChecked: null,
        modules: {}
      }, null, 2));
    }

    return true;
  } catch (err) {
    console.error("[security/continuity] Failed to initialize:", err);
    return false;
  }
}

/**
 * Calculate checksum for module
 */
export function calculateModuleChecksum(modulePath, content) {
  const hash = crypto.createHash("sha256");
  hash.update(content || fs.readFileSync(modulePath));
  return hash.digest("hex");
}

/**
 * Store baseline for module
 */
export async function storeBaseline(modulePath, content) {
  try {
    const contentStr = typeof content === "string" ? content : fs.readFileSync(modulePath, "utf8");
    const checksum = calculateModuleChecksum(modulePath, contentStr);

    const baseline = await getBaseline();
    baseline.modules[modulePath] = {
      checksum,
      lastModified: new Date().toISOString()
    };

    await fs.writeFile(BASELINE_FILE, JSON.stringify(baseline, null, 2));

    return { success: true, checksum };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/**
 * Get current baseline
 */
export async function getBaseline() {
  try {
    const content = await fs.readFile(BASELINE_FILE, "utf8");
    return JSON.parse(content);
  } catch (err) {
    return { version: "1.0", createdAt: new Date().toISOString(), modules: {} };
  }
}

/**
 * Store checksum snapshot
 */
export async function storeChecksum(modulePath, content) {
  try {
    const contentStr = typeof content === "string" ? content : fs.readFileSync(modulePath, "utf8");
    const checksum = calculateModuleChecksum(modulePath, contentStr);

    const checksums = await getChecksums();
    checksums.modules[modulePath] = {
      checksum,
      lastChecked: new Date().toISOString()
    };
    checksums.lastChecked = new Date().toISOString();

    await fs.writeFile(CHECKSUM_FILE, JSON.stringify(checksums, null, 2));

    return { success: true, checksum };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/**
 * Get current checksums
 */
export async function getChecksums() {
  try {
    const content = await fs.readFile(CHECKSUM_FILE, "utf8");
    return JSON.parse(content);
  } catch (err) {
    return { version: "1.0", lastChecked: null, modules: {} };
  }
}

/**
 * Check for continuity anomalies
 */
export async function checkAnomalies() {
  const baseline = await getBaseline();
  const checksums = await getChecksums();

  const anomalies = [];

  // Check all baseline modules
  for (const [modulePath, baselineData] of Object.entries(baseline.modules || {})) {
    const currentChecksum = checksums.modules?.[modulePath]?.checksum;

    if (!currentChecksum) {
      anomalies.push({
        type: "missing",
        module: modulePath,
        message: "No checksum found for module"
      });
    } else if (currentChecksum !== baselineData.checksum) {
      anomalies.push({
        type: "modified",
        module: modulePath,
        baselineChecksum: baselineData.checksum,
        currentChecksum
      });
    }
  }

  // Check for new modules not in baseline
  if (checksums.modules) {
    for (const modulePath of Object.keys(checksums.modules)) {
      if (!baseline.modules?.[modulePath]) {
        anomalies.push({
          type: "new",
          module: modulePath,
          message: "New module detected"
        });
      }
    }
  }

  return {
    hasAnomalies: anomalies.length > 0,
    anomalies,
    count: anomalies.length
  };
}

/**
 * Reset continuity state
 */
export async function resetContinuity() {
  try {
    await fs.writeFile(BASELINE_FILE, JSON.stringify({
      version: "1.0",
      createdAt: new Date().toISOString(),
      modules: {}
    }, null, 2));

    await fs.writeFile(CHECKSUM_FILE, JSON.stringify({
      version: "1.0",
      lastChecked: null,
      modules: {}
    }, null, 2));

    return true;
  } catch (err) {
    return false;
  }
}

/**
 * Continuity alert
 */
export async function createContinuityAlert(eventId, data) {
  return {
    id: `continuity-${eventId}-${Date.now()}`,
    type: "continuity_anomaly",
    timestamp: new Date().toISOString(),
    severity: data.hasAnomalies ? "high" : "info",
    description: data.hasAnomalies ? "Continuity anomaly detected" : "Continuity check passed",
    anomalyCount: data.count || 0,
    data
  };
}

export default {
  init: initContinuity,
  storeBaseline,
  getBaseline,
  storeChecksum,
  getChecksums,
  checkAnomalies,
  reset: resetContinuity,
  createAlert: createContinuityAlert
};
