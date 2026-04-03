#!/usr/bin/env node
/**
 * extensions/security/gateway-wrappers.js
 * Phase 2C: Gateway fs wrapper hooks (opt-in via OPENCLAW_SECURITY_ENABLED)
 */

import fs from "node:fs";
import fsPromises from "node:fs/promises";
import { SecureFS } from "./gateway.js";

/**
 * Check if security is enabled via environment variable
 */
export function isSecurityEnabled() {
  return process.env.OPENCLAW_SECURITY_ENABLED === "1" || 
         process.env.OPENCLAW_SECURITY_ENABLED === "true";
}

/**
 * Wrap fsPromises.writeFile to use SecureFS
 */
export function wrapFsPromisesWriteFile() {
  if (!isSecurityEnabled()) {
    console.log("[security/gateway] OPENCLAW_SECURITY_ENABLED not set, skipping wrappers");
    return;
  }

  console.log("[security/gateway] Wrapping fsPromises.writeFile with security checks");

  const originalWriteFile = fsPromises.writeFile;

  async function secureWriteFile(filepath, data, options = {}) {
    // Run through SecureFS which includes preWriteHook, audit logging, etc.
    return await SecureFS.writeFile(filepath, data, options);
  }

  // Override the module's fsPromises.writeFile
  fsPromises.writeFile = secureWriteFile;
}

/**
 * Initialize Gateway security wrappers
 */
export function initGatewaySecurityWrappers() {
  if (!isSecurityEnabled()) {
    console.log("[security/gateway] Security not enabled, skipping initialization");
    return {
      enabled: false,
      reason: "OPENCLAW_SECURITY_ENABLED not set"
    };
  }

  wrapFsPromisesWriteFile();

  return {
    enabled: true,
    wrappers: ["fsPromises.writeFile"]
  };
}

export default {
  init: initGatewaySecurityWrappers,
  isSecurityEnabled,
  wrapFsPromisesWriteFile
};
