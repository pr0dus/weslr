#!/usr/bin/env node
/**
 * security/audit/index.js - Immutable Audit Trail Foundation
 * Phase 1: Audit trail infrastructure with cryptographic chaining
 */

import crypto from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs/promises";
import { resolveStateDir, resolveGatewayLockDir } from "../../dist/paths-dQ_clcF4.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const STATE_DIR = resolveStateDir();
const AUDIT_DIR = path.join(STATE_DIR, ".openclaw", "audit");
const AUDIT_LOG = path.join(AUDIT_DIR, "entries.log");
const AUDIT_CHAIN = path.join(AUDIT_DIR, "chain.json");

/**
 * Initialize audit trail directory structure
 */
export async function initAuditTrail() {
  try {
    await fs.mkdir(AUDIT_DIR, { recursive: true });
    
    // Initialize chain file if not exists
    const chainExists = await fs.access(AUDIT_CHAIN).then(() => true).catch(() => false);
    if (!chainExists) {
      await fs.writeFile(AUDIT_CHAIN, JSON.stringify({
        headHash: null,
        entryCount: 0,
        createdAt: new Date().toISOString()
      }, null, 2));
    }
    
    // Initialize log file if not exists
    const logExists = await fs.access(AUDIT_LOG).then(() => true).catch(() => false);
    if (!logExists) {
      await fs.writeFile(AUDIT_LOG, "");
    }
    
    return true;
  } catch (err) {
    console.error("[security/audit] Failed to initialize audit trail:", err);
    return false;
  }
}

/**
 * Calculate hash of data
 */
export function hashData(data) {
  if (typeof data !== "string") {
    data = JSON.stringify(data);
  }
  return crypto.createHash("sha256").update(data).digest("hex");
}

/**
 * Read current chain state
 */
export async function readChainState() {
  try {
    const content = await fs.readFile(AUDIT_CHAIN, "utf8");
    return JSON.parse(content);
  } catch (err) {
    return { headHash: null, entryCount: 0, createdAt: new Date().toISOString() };
  }
}

/**
 * Write audit entry with chaining
 */
export async function writeAuditEntry(entry) {
  const timestamp = new Date().toISOString();
  const prevChain = await readChainState();
  
  // Prepare entry with chaining metadata
  const fullEntry = {
    ...entry,
    timestamp,
    prevHash: prevChain.headHash || null,
    dataHash: hashData(JSON.stringify(entry))
  };
  
  // Calculate chain hash
  const chainHashInput = JSON.stringify({
    ...fullEntry,
    chainIndex: prevChain.entryCount + 1
  });
  const currentHash = hashData(chainHashInput);
  
  // Append to log (append-only, no overwrite)
  await fs.appendFile(AUDIT_LOG, JSON.stringify(fullEntry) + "\n");
  
  // Update chain state
  await fs.writeFile(AUDIT_CHAIN, JSON.stringify({
    headHash: currentHash,
    entryCount: prevChain.entryCount + 1,
    createdAt: prevChain.createdAt,
    lastEntryAt: timestamp
  }, null, 2));
  
  return {
    success: true,
    hash: currentHash,
    index: prevChain.entryCount + 1
  };
}

/**
 * Read audit entries (reverse chronological)
 */
export async function readAuditEntries(limit = 100) {
  try {
    const content = await fs.readFile(AUDIT_LOG, "utf8");
    const lines = content.trim().split("\n").filter(l => l.length > 0);
    
    return lines.slice(-limit).map(line => JSON.parse(line)).reverse();
  } catch (err) {
    return [];
  }
}

/**
 * Verify audit chain integrity
 */
export async function verifyAuditChain() {
  const entries = await readAuditEntries(1000);
  let currentPrevHash = null;
  let integrity = true;
  
  for (const entry of entries) {
    if (entry.prevHash !== currentPrevHash) {
      integrity = false;
      console.error(`[security/audit] Chain break at entry:`, entry);
    }
    
    // Verify data hash
    const computedDataHash = hashData(JSON.stringify({
      ...entry,
      prevHash: undefined,
      dataHash: undefined
    }));
    
    if (entry.dataHash !== computedDataHash) {
      integrity = false;
      console.error(`[security/audit] Data tamper detected at entry:`, entry);
    }
    
    currentPrevHash = entry.dataHash;
  }
  
  return integrity;
}

/**
 * Get audit statistics
 */
export async function getAuditStats() {
  const chain = await readChainState();
  const entries = await readAuditEntries(1000);
  
  return {
    entryCount: chain.entryCount,
    headHash: chain.headHash,
    createdAt: chain.createdAt,
    lastEntryAt: chain.lastEntryAt || entries[entries.length - 1]?.timestamp,
    entries: entries.slice(-10).map(e => ({ type: e.type, timestamp: e.timestamp }))
  };
}

// Export forPhase 1 usage
export const AuditTrail = {
  init: initAuditTrail,
  write: writeAuditEntry,
  read: readAuditEntries,
  verify: verifyAuditChain,
  stats: getAuditStats
};
