#!/usr/bin/env node
/**
 * security/audit/logs/index.js - Security Event Logging
 * Phase 1: Structured security event logging
 */

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, "..", "..", "..");

/**
 * Initialize security logging
 */
export async function initSecurityLogs() {
  const SECURITY_LOGS_DIR = path.join(projectRoot, ".openclaw", "audit", "logs");

  try {
    await fs.mkdir(SECURITY_LOGS_DIR, { recursive: true });
    return true;
  } catch (err) {
    console.error("[security/logs] Failed to initialize security logs:", err);
    return false;
  }
}

/**
 * Log security event
 */
export async function logSecurityEvent(event) {
  const SECURITY_LOGS_DIR = path.join(projectRoot, ".openclaw", "audit", "logs");
  const timestamp = new Date().toISOString();
  const entry = {
    ...event,
    timestamp,
    id: `${event.type}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  };

  // Determine log file by type
  const logFile = path.join(SECURITY_LOGS_DIR, `${event.type || "generic"}.log`);

  // Append to log (append-only)
  await fs.appendFile(logFile, JSON.stringify(entry) + "\n");

  return entry;
}

/**
 * Read security events from a log file
 */
export async function readSecurityEvents(type, options = {}) {
  const SECURITY_LOGS_DIR = path.join(projectRoot, ".openclaw", "audit", "logs");
  const logFile = path.join(SECURITY_LOGS_DIR, `${type}.log`);

  try {
    const content = await fs.readFile(logFile, "utf8");
    const lines = content.trim().split("\n").filter(l => l.length > 0);

    let events = lines.map(line => JSON.parse(line));

    // Apply filters
    if (options.limit) {
      events = events.slice(-options.limit);
    }
    if (options.since) {
      events = events.filter(e => new Date(e.timestamp) > new Date(options.since));
    }

    return events.reverse();
  } catch (err) {
    return [];
  }
}

/**
 * Get security event summary
 */
export async function getSecuritySummary() {
  const SECURITY_LOGS_DIR = path.join(projectRoot, ".openclaw", "audit", "logs");

  try {
    const files = await fs.readdir(SECURITY_LOGS_DIR);

    const summary = {
      totalEvents: 0,
      byType: {},
      last24h: 0,
      critical: 0
    };

    for (const file of files) {
      if (!file.endsWith(".log")) continue;

      const type = file.replace(".log", "");
      const events = await readSecurityEvents(type);

      summary.totalEvents += events.length;
      summary.byType[type] = events.length;

      const now = new Date();
      const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

      summary.last24h += events.filter(e => new Date(e.timestamp) > dayAgo).length;
      summary.critical += events.filter(e => e.severity === "critical").length;
    }

    return summary;
  } catch (err) {
    return { totalEvents: 0, byType: {}, last24h: 0, critical: 0 };
  }
}

/**
 * Security event types
 */
export const SECURITY_EVENT_TYPES = {
  THREAT_DETECTED: "threat_detected",
  SELF_MOD_ATTEMPT: "self_mod_attempt",
  POLICY_VIOLATION: "policy_violation",
  RISK_ASSESSMENT: "risk_assessment",
  ROLLBACK_INITIATED: "rollback_initiated",
  CONTINUITY_ANOMALY: "continuity_anomaly",
  AUDIT_TRAIL_ACCESS: "audit_trail_access",
  SYSTEM_SECURITY: "system_security"
};

/**
 * Create security event builder
 */
export function createSecurityEvent(type, payload) {
  return {
    type,
    timestamp: null, // Will be set by log function
    id: null,
    severity: payload.severity || "info",
    category: payload.category || "security",
    description: payload.description || "",
    details: payload.details || {},
    tags: payload.tags || []
  };
}

export default {
  init: initSecurityLogs,
  log: logSecurityEvent,
  read: readSecurityEvents,
  summary: getSecuritySummary,
  types: SECURITY_EVENT_TYPES,
  createEvent: createSecurityEvent
};
