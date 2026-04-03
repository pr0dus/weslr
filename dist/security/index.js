#!/usr/bin/env node
/**
 * dist/security/index.js - Platform-Facing Security API
 * Phase 2A: Runtime-facing export layer with platform path binding
 */

import { AuditTrail } from "../security/audit/index.js";
import { MaliciousCodeDetector } from "../security/detector/malicious-code.js";
import RiskEngine from "../security/risk-engine/index.js";
import Gate from "../security/gate/index.js";
import Rollback from "../security/rollback/index.js";
import Continuity from "../security/continuity/index.js";
import SecurityPolicy from "../security/policy/index.js";
import SecurityLogs from "../security/audit/logs/index.js";

/**
 * Main detector instance
 */
const threatDetector = new MaliciousCodeDetector();

/**
 * Risk engine instance
 */
const riskEngine = new RiskEngine(SecurityPolicy.default);

/**
 * Platform-facing Security API
 * Binds platform paths to generic modules
 */
export const SecurityAPI = {
  // Audit - with platform paths
  Audit: {
    init: async () => {
      await AuditTrail.init();
      return await SecurityLogs.init();
    },
    write: AuditTrail.write,
    read: AuditTrail.read,
    verify: AuditTrail.verify,
    stats: AuditTrail.stats
  },

  // Detection - generic (platform-neutral)
  Detector: {
    scanCode: (code, context) => threatDetector.scanCode(code, context),
    checkPrivilegeEscalation: (cmd, args) => threatDetector.checkPrivilegeEscalation(cmd, args),
    calculateRisk: (issues) => threatDetector.calculateRisk(issues)
  },

  // Risk Engine - generic (platform-neutral)
  RiskEngine: riskEngine,

  // Gate hooks - generic (platform-neutral signatures)
  Gate,

  // Rollback - with platform paths
  Rollback: {
    init: Rollback.init,
    create: Rollback.create,
    get: Rollback.get,
    getById: Rollback.getById,
    execute: Rollback.execute,
    delete: Rollback.delete,
    summary: Rollback.summary
  },

  // Continuity - with platform paths
  Continuity: {
    init: Continuity.init,
    storeBaseline: Continuity.storeBaseline,
    getBaseline: Continuity.getBaseline,
    storeChecksum: Continuity.storeChecksum,
    getChecksums: Continuity.getChecksums,
    checkAnomalies: Continuity.checkAnomalies,
    reset: Continuity.reset,
    createAlert: Continuity.createAlert
  },

  // Policy - with platform paths
  Policy: {
    load: SecurityPolicy.load,
    save: SecurityPolicy.save,
    validate: SecurityPolicy.validate,
    get: SecurityPolicy.get,
    update: SecurityPolicy.update,
    default: SecurityPolicy.default
  },

  // Security Logs - with platform paths
  Logs: {
    init: SecurityLogs.init,
    log: SecurityLogs.log,
    read: SecurityLogs.read,
    summary: SecurityLogs.summary,
    types: SecurityLogs.types,
    createEvent: SecurityLogs.createEvent
  },

  // Security Self-Protection Core
  Core: {
    init: async () => {
      await SecurityAPI.Audit.init();
      await SecurityAPI.Rollback.init();
      await SecurityAPI.Continuity.init();
      return true;
    },
    status: async () => {
      const policy = await SecurityPolicy.load();
      const auditStats = await SecurityAPI.Audit.stats();
      const logsSummary = await SecurityLogs.summary();
      const rollbackSummary = await Rollback.summary();
      const anomalyCheck = await Continuity.checkAnomalies();

      return {
        version: "2.0",
        enabled: true,
        policy,
        audit: {
          entryCount: auditStats.entryCount,
          headHash: auditStats.headHash,
          lastEntryAt: auditStats.lastEntryAt
        },
        logs: logsSummary,
        rollback: rollbackSummary,
        continuity: anomalyCheck
      };
    }
  }
};

/**
 * Secure write wrapper (real integration - phase 2A)
 * Wraps fs.write* with preWriteHook
 */
import fs from "node:fs/promises";

async function _realFsWriteFile(filepath, data, options = {}) {
  // Run pre-write hook
  const hookResult = await Gate.preWriteHook(filepath, {
    action: "write",
    ...options
  });

  if (hookResult.blocked) {
    // Log security event
    await SecurityAPI.Logs.log({
      type: "pre_write_blocked",
      filepath,
      reason: hookResult.reason || "Hook blocked write",
      timestamp: new Date().toISOString()
    });
    throw new Error(`Security: write blocked for ${filepath}`);
  }

  // Create rollback artifact before write
  await SecurityAPI.Continuity.storeChecksum(filepath, data);

  // Perform actual write
  return await fs.writeFile(filepath, data, options);
}

async function _realFsAppendFile(filepath, data, options = {}) {
  const hookResult = await Gate.preWriteHook(filepath, {
    action: "append",
    ...options
  });

  if (hookResult.blocked) {
    await SecurityAPI.Logs.log({
      type: "pre_append_blocked",
      filepath,
      reason: hookResult.reason || "Hook blocked append",
      timestamp: new Date().toISOString()
    });
    throw new Error(`Security: append blocked for ${filepath}`);
  }

  await SecurityAPI.Continuity.storeChecksum(filepath, data);

  return await fs.appendFile(filepath, data, options);
}

export const SecureFS = {
  writeFile: _realFsWriteFile,
  appendFile: _realFsAppendFile
};

/**
 * Secure import wrapper (real integration - phase 2A)
 * Wraps dynamic import with preEvolutionHook
 */
async function _realDynamicImport(modulePath, context = {}) {
  // Run pre-evolution hook
  const hookResult = await Gate.preEvolutionHook(modulePath, {
    action: "import",
    ...context
  });

  if (hookResult.blocked) {
    await SecurityAPI.Logs.log({
      type: "pre_import_blocked",
      modulePath,
      reason: hookResult.reason || "Hook blocked import",
      timestamp: new Date().toISOString()
    });
    throw new Error(`Security: import blocked for ${modulePath}`);
  }

  // Create rollback metadata
  const rollbackPoint = await Gate.createRollbackPoint({
    id: `import-${Date.now()}`,
    type: "import",
    description: `Import ${modulePath}`,
    timestamp: new Date().toISOString()
  }, {
    artifacts: [{ type: "module", path: modulePath }]
  });

  // Perform actual import
  return await import(modulePath);
}

export const SecureImport = {
  dynamic: _realDynamicImport
};

export default SecurityAPI;
