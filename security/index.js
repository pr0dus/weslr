#!/usr/bin/env node
/**
 * security/index.js - Security Self-Protection Layer (Phase 1)
 * Core orchestration and exports
 */

import { AuditTrail } from "./audit/index.js";
import { MaliciousCodeDetector } from "./detector/malicious-code.js";
import RiskEngine from "./risk-engine/index.js";
import Gate from "./gate/index.js";
import Rollback from "./rollback/index.js";
import Continuity from "./continuity/index.js";
import SecurityPolicy from "./policy/index.js";
import SecurityLogs from "./audit/logs/index.js";

/**
 * Main detector instance
 */
const threatDetector = new MaliciousCodeDetector();

/**
 * Risk engine instance
 */
const riskEngine = new RiskEngine(SecurityPolicy.default);

/**
 * Security Self-Protection Layer - Phase 1
 */
export const SecuritySelfProtection = {
  // Audit
  AuditTrail,

  // Detection
  Detector: {
    scanCode: (code, context) => threatDetector.scanCode(code, context),
    checkPrivilegeEscalation: (cmd, args) => threatDetector.checkPrivilegeEscalation(cmd, args),
    calculateRisk: (issues) => threatDetector.calculateRisk(issues)
  },

  // Risk
  RiskEngine: riskEngine,

  // Gates
  Gate,

  // Rollback
  Rollback,

  // Continuity
  Continuity,

  // Policy
  Policy: SecurityPolicy,

  // Logs
  SecurityLogs
};

/**
 * Initialize all security components
 */
export async function initSecurity() {
  const results = {
    audit: await AuditTrail.init(),
    logs: await SecurityLogs.init(),
    rollback: await Rollback.init(),
    continuity: await Continuity.init()
  };

  return results;
}

/**
 * Get security status
 */
export async function getSecurityStatus() {
  const policy = await SecurityPolicy.load();
  const stats = await AuditTrail.stats();
  const summary = await SecurityLogs.summary();
  const rollbackSummary = await Rollback.summary();
  const anomalyCheck = await Continuity.checkAnomalies();

  return {
    version: "1.0",
    enabled: true,
    policy,
    audit: {
      entryCount: stats.entryCount,
      headHash: stats.headHash,
      lastEntryAt: stats.lastEntryAt
    },
    logs: summary,
    rollback: rollbackSummary,
    continuity: anomalyCheck
  };
}

/**
 * Secure write wrapper (Phase 1: stub for future integration)
 */
export async function secureWrite(filepath, data, options = {}) {
  // Phase 1: Direct write with logging
  // Full implementation would:
  // 1. Run preWriteHook
  // 2. Check against immutable patterns
  // 3. Detect threats in content
  // 4. Calculate risk score
  // 5. Block if necessary
  // 6. Create rollback artifact

  await SecurityLogs.log({
    type: "pre_write_attempt",
    filepath,
    action: options.action || "write",
    riskScore: 0,
    blocked: false,
    timestamp: new Date().toISOString()
  });

  // Intended to be wrapped by actual fs.write
  const writeFn = options.writeFn || (async () => {
    const fs = await import("node:fs/promises");
    return fs.writeFile(filepath, data, options);
  });

  return await writeFn();
}

/**
 * Secure import wrapper (Phase 1: stub for future integration)
 */
export async function secureImport(modulePath, context = {}) {
  // Phase 1: Direct import with logging
  // Full implementation would:
  // 1. Run preEvolutionHook
  // 2. Check against immutable patterns
  // 3. Analyze module code
  // 4. Calculate risk score
  // 5. Block if necessary

  await SecurityLogs.log({
    type: "pre_evolution_attempt",
    modulePath,
    action: context.action || "import",
    riskScore: 0,
    blocked: false,
    timestamp: new Date().toISOString()
  });

  // Intended to be wrapped by actual import
  const importFn = context.importFn || (async () => {
    return await import(modulePath);
  });

  return await importFn();
}

export default SecuritySelfProtection;
