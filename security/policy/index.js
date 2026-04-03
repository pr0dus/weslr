#!/usr/bin/env node
/**
 * security/policy/index.js - Policy Configuration (Scaffold)
 * Phase 1: Policy storage and rule validation
 */

import fs from "node:fs/promises";
import path from "node:path";
import { resolveStateDir } from "../../../dist/paths-dQ_clcF4.js";

const STATE_DIR = resolveStateDir();
const POLICY_DIR = path.join(STATE_DIR, ".openclaw", "config", "security");
const POLICY_FILE = path.join(POLICY_DIR, "security-policy.json");

/**
 * Policy schema validation
 */
const POLICY_SCHEMA = {
  type: "object",
  properties: {
    selfEvolution: {
      type: "object",
      properties: {
        maxAdditiveLines: { type: "integer", minimum: 0, maximum: 10000 },
        maxModificativeLines: { type: "integer", minimum: 0, maximum: 1000 },
        requiresApproval: { type: "array", items: { type: "string" } },
        forbiddenPatterns: { type: "array", items: { type: "string" } }
      },
      required: ["maxAdditiveLines", "maxModificativeLines", "forbiddenPatterns"]
    },
    riskThresholds: {
      type: "object",
      properties: {
        autoBlock: { type: "integer", minimum: 0, maximum: 100 },
        alertOnly: { type: "integer", minimum: 0, maximum: 100 },
        allow: { type: "integer", minimum: 0, maximum: 100 }
      },
      required: ["autoBlock", "alertOnly"]
    },
    audit: {
      type: "object",
      properties: {
        enabled: { type: "boolean" },
        retentionDays: { type: "integer", minimum: 1, maximum: 365 },
        encrypted: { type: "boolean" }
      },
      required: ["enabled", "retentionDays"]
    }
  },
  required: ["selfEvolution", "riskThresholds", "audit"]
};

/**
 * Default policy configuration
 */
export const DEFAULT_POLICY = {
  selfEvolution: {
    maxAdditiveLines: 500,
    maxModificativeLines: 100,
    requiresApproval: ["modificative", "deletive", "dependency"],
    forbiddenPatterns: ["eval(", "child_process", "setuid", "sudo", "chmod +s"]
  },
  riskThresholds: {
    autoBlock: 80,
    alertOnly: 50,
    allow: 0
  },
  audit: {
    enabled: true,
    retentionDays: 30,
    encrypted: false
  }
};

/**
 * Load policy from file
 */
export async function loadPolicy() {
  try {
    await fs.access(POLICY_FILE);
    const content = await fs.readFile(POLICY_FILE, "utf8");
    const policy = JSON.parse(content);
    return validatePolicy(policy) ? policy : DEFAULT_POLICY;
  } catch (err) {
    return DEFAULT_POLICY;
  }
}

/**
 * Save policy to file
 */
export async function savePolicy(policy) {
  if (!validatePolicy(policy)) {
    throw new Error("Invalid policy configuration");
  }
  
  await fs.mkdir(POLICY_DIR, { recursive: true });
  await fs.writeFile(POLICY_FILE, JSON.stringify(policy, null, 2));
  
  return policy;
}

/**
 * Validate policy against schema
 */
export function validatePolicy(policy) {
  // Basic structure validation
  if (!policy.selfEvolution || !policy.riskThresholds || !policy.audit) {
    return false;
  }
  
  // Check required fields
  if (!policy.selfEvolution.maxAdditiveLines || !policy.selfEvolution.forbiddenPatterns) {
    return false;
  }
  
  if (!policy.riskThresholds.autoBlock || !policy.riskThresholds.alertOnly) {
    return false;
  }
  
  if (!policy.audit.enabled || !policy.audit.retentionDays) {
    return false;
  }
  
  // Check values are in range
  if (policy.riskThresholds.autoBlock < policy.riskThresholds.alertOnly) {
    return false;
  }
  
  if (policy.selfEvolution.maxModificativeLines > policy.selfEvolution.maxAdditiveLines) {
    return false;
  }
  
  return true;
}

/**
 * Get policy by name
 */
export async function getPolicy(name = "default") {
  const policy = await loadPolicy();
  return { name, ...policy };
}

/**
 * Update policy values
 */
export async function updatePolicy(updates) {
  const current = await loadPolicy();
  const updated = { ...current, ...updates };
  
  if (!validatePolicy(updated)) {
    throw new Error("Invalid policy updates");
  }
  
  return await savePolicy(updated);
}

export default {
  load: loadPolicy,
  save: savePolicy,
  validate: validatePolicy,
  default: DEFAULT_POLICY,
  get: getPolicy,
  update: updatePolicy
};
