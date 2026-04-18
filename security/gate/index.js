#!/usr/bin/env node
/**
 * security/gate/index.js - Gate Hooks (Phase 2B)
 * Real threat detection and policy-based blocking
 */

import ThreatDetector from "../detector/index.js";
import RiskEngine from "../risk-engine/index.js";
import SecurityPolicy from "../policy/index.js";
import SecurityLogs from "../audit/logs/index.js";
import { SECURITY_EVENT_TYPES } from "../audit/logs/index.js";

/**
 * Global risk engine instance
 */
const riskEngine = new RiskEngine(SecurityPolicy.default);

/**
 * Threat detector instance
 */
const threatDetector = new ThreatDetector();

/**
 * Immutable patterns (files that should never be modified)
 */
const IMMUTABLE_PATTERNS = [
  /security\/.*\.(js|mjs|json)$/,        // Self-protection modules
  /dist\/.*\.(mjs|js)$/,                 // Compiled entry points
  /package\.json$/,                      // Dependency manifest
  /openclaw\.mjs$/,                      // CLI entry point
  /dist\/index\.js$/,                    // Main distribution
  /\.openclaw\/workspace\/.*$/           // User workspace
];

/**
 * Check if path matches immutable pattern
 */
function isImmutablePath(filepath) {
  for (const pattern of IMMUTABLE_PATTERNS) {
    if (pattern.test(filepath)) {
      return true;
    }
  }
  return false;
}

/**
 * Load security policy (with defaults)
 */
async function loadPolicy() {
  try {
    return await SecurityPolicy.load();
  } catch {
    return SecurityPolicy.default;
  }
}

/**
 * Log security event to audit trail
 */
async function logSecurityEvent(hook) {
  try {
    await SecurityLogs.log({
      type: hook.type === "pre_write" ? "pre_write_blocked" : "pre_import_blocked",
      filepath: hook.filepath,
      modulePath: hook.modulePath,
      action: hook.action,
      reason: hook.reason,
      riskScore: hook.riskScore,
      timestamp: hook.timestamp
    });
  } catch (err) {
    console.error("[security/gate] Failed to log security event:", err.message);
  }
}

/**
 * Pre-write hook with real threat detection
 */
export async function preWriteHook(filepath, options = {}) {
  const hook = {
    type: "pre_write",
    timestamp: new Date().toISOString(),
    filepath,
    action: options.action || "write",
    status: "pending",
    riskScore: 0,
    blocked: false,
    reason: null
  };

  // Load policy for thresholds
  const policy = await loadPolicy();
  const thresholds = policy.riskThresholds || SecurityPolicy.default.riskThresholds;

  // Check immutable path first (non-negotiable)
  if (isImmutablePath(filepath)) {
    hook.blocked = true;
    hook.reason = `Path matches immutable pattern: ${filepath}`;
    hook.riskScore = 100;
    await logSecurityEvent(hook);
    return hook;
  }

  // If content provided, scan for malicious patterns
  if (options.content) {
    const scanResult = await threatDetector.scanCode(options.content, {
      filepath,
      action: options.action
    });

    if (scanResult.hasIssues) {
      hook.riskScore = threatDetector.calculateRiskScore(scanResult);
      hook.issues = scanResult.issues;

      // Check if content contains forbidden patterns from policy
      const hasForbidden = policy.selfEvolution?.forbiddenPatterns?.some(pattern => {
        return scanResult.issues.some(issue => issue.match.includes(pattern));
      });

      if (hasForbidden || hook.riskScore >= thresholds.autoBlock) {
        hook.blocked = true;
        if (hasForbidden) {
          hook.reason = `Forbidden pattern detected in content`;
        } else {
          hook.reason = `Risk score ${hook.riskScore} >= ${thresholds.autoBlock} (autoBlock threshold)`;
        }
        await logSecurityEvent(hook);
        return hook;
      }
    }
  }

  // Check for privilege escalation in command arguments
  if (options.args && Array.isArray(options.args)) {
    const privilegeResult = await threatDetector.checkPrivilegeEscalation(filepath, options.args);
    if (privilegeResult.hasIssues) {
      hook.riskScore = threatDetector.calculateRiskScore({
        issues: privilegeResult.issues,
        threatTags: ["privilege-escalation"]
      });
      hook.issues = privilegeResult.issues;

      if (hook.riskScore >= thresholds.autoBlock) {
        hook.blocked = true;
        hook.reason = `Privilege escalation detected (risk score: ${hook.riskScore})`;
        await logSecurityEvent(hook);
        return hook;
      }
    }
  }

  // Allow if no threats detected
  hook.riskScore = 0;
  hook.status = "completed";
  return hook;
}

/**
 * Pre-evolution hook with real threat detection
 */
export async function preEvolutionHook(modulePath, context = {}) {
  const hook = {
    type: "pre_evolution",
    timestamp: new Date().toISOString(),
    modulePath,
    action: context.action || "import",
    status: "pending",
    riskScore: 0,
    blocked: false,
    reason: null
  };

  // Load policy for thresholds
  const policy = await loadPolicy();
  const thresholds = policy.riskThresholds || SecurityPolicy.default.riskThresholds;

  // Check immutable path first (non-negotiable)
  if (isImmutablePath(modulePath)) {
    hook.blocked = true;
    hook.reason = `Path matches immutable pattern: ${modulePath}`;
    hook.riskScore = 100;
    await logSecurityEvent(hook);
    return hook;
  }

  // If module content provided, scan for malicious patterns
  if (context.content) {
    const scanResult = await threatDetector.scanCode(context.content, {
      modulePath,
      action: "import"
    });

    if (scanResult.hasIssues) {
      hook.riskScore = threatDetector.calculateRiskScore(scanResult);
      hook.issues = scanResult.issues;

      // Check for forbidden patterns
      const hasForbidden = policy.selfEvolution?.forbiddenPatterns?.some(pattern => {
        return scanResult.issues.some(issue => issue.match.includes(pattern));
      });

      if (hasForbidden || hook.riskScore >= thresholds.autoBlock) {
        hook.blocked = true;
        if (hasForbidden) {
          hook.reason = `Forbidden pattern detected in content`;
        } else {
          hook.reason = `Risk score ${hook.riskScore} >= ${thresholds.autoBlock} (autoBlock threshold)`;
        }
        await logSecurityEvent(hook);
        return hook;
      }
    }
  }

  // Allow if no threats detected
  hook.riskScore = 0;
  hook.status = "completed";
  return hook;
}

/**
 * Rollback metadata injection
 */
export async function injectRollbackMetadata(event, snapshot) {
  const metadata = {
    timestamp: new Date().toISOString(),
    eventId: event.id,
    snapshotHash: snapshot.hash || null,
    rollbackAvailable: true,
    rollbackPath: snapshot.path || null
  };

  return {
    success: true,
    metadata,
    rollbackId: `rollback-${Date.now()}`
  };
}

/**
 * Rollback point creation
 */
export async function createRollbackPoint(event, snapshot = {}) {
  const rollbackPoint = {
    id: `rollback-${Date.now()}`,
    timestamp: new Date().toISOString(),
    description: event.description || "Security rollback point",
    eventId: event.id,
    status: "pending",
    artifacts: snapshot.artifacts || []
  };

  return rollbackPoint;
}

/**
 * Rollback metadata extraction
 */
export async function extractRollbackMetadata(event) {
  return {
    eventId: event.id,
    timestamp: event.timestamp,
    rollbackAvailable: true
  };
}

/**
 * Gate registry for hook management
 */
export const GATE_REGISTRY = {
  hooks: {
    preWrite: [],
    preEvolution: []
  },

  register: function(type, hookFn) {
    if (!this.hooks[type]) {
      throw new Error(`Unknown hook type: ${type}`);
    }
    this.hooks[type].push(hookFn);
  },

  unregister: function(type, hookFn) {
    if (!this.hooks[type]) return;
    this.hooks[type] = this.hooks[type].filter(h => h !== hookFn);
  },

  execute: async function(type, ...args) {
    if (!this.hooks[type]) return { blocked: false };

    const results = [];
    for (const hook of this.hooks[type]) {
      try {
        const result = await hook(...args);
        results.push(result);

        if (result && result.blocked) {
          return result;
        }
      } catch (err) {
        console.error(`[security/gate] Hook ${type} error:`, err);
      }
    }

    return { blocked: false, results };
  }
};

export default {
  preWrite: preWriteHook,
  preEvolution: preEvolutionHook,
  injectRollback: injectRollbackMetadata,
  createRollback: createRollbackPoint,
  extractRollback: extractRollbackMetadata,
  registry: GATE_REGISTRY
};
