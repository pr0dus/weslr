#!/usr/bin/env node
/**
 * extensions/security/src/gateway/index.js - Gateway Runtime Integration (Phase 2A)
 * Gateway-specific security enforcement
 */

import { SecurityAPI, SecureFS, SecureImport } from "../dist/security/index.js";

/**
 * Gateway runtime security integration
 * Hooks fs operations and dynamic imports
 */
export const GatewayRuntimeSecurity = {
  initialized: false,
  hooks: {
    fs: {
      write: null,
      append: null
    },
    import: {
      dynamic: null
    }
  }
};

/**
 * Initialize Gateway runtime security
 */
export async function init() {
  if (GatewayRuntimeSecurity.initialized) {
    return { success: true, message: "Already initialized" };
  }

  // Initialize platform security
  await SecurityAPI.Core.init();

  // Install Gateway-specific hooks
  GatewayRuntimeSecurity.hooks.fs.write = SecureFS.writeFile;
  GatewayRuntimeSecurity.hooks.fs.append = SecureFS.appendFile;
  GatewayRuntimeSecurity.hooks.import.dynamic = SecureImport.dynamic;

  GatewayRuntimeSecurity.initialized = true;

  const status = await SecurityAPI.status();
  status.runtime = "gateway";
  status.hooks = GatewayRuntimeSecurity.hooks;

  return { success: true, status };
}

/**
 * Get current security status
 */
export async function status() {
  if (!GatewayRuntimeSecurity.initialized) {
    return { success: false, error: "Runtime security not initialized. Call init() first." };
  }

  const status = await SecurityAPI.status();
  status.runtime = "gateway";
  status.hooks = GatewayRuntimeSecurity.hooks;

  return status;
}

/**
 * Get secure fs wrapper
 */
export function secureFS() {
  if (!GatewayRuntimeSecurity.initialized) {
    throw new Error("Runtime security not initialized");
  }

  return {
    writeFile: SecureFS.writeFile,
    appendFile: SecureFS.appendFile
  };
}

/**
 * Get secure import wrapper
 */
export function secureImport() {
  if (!GatewayRuntimeSecurity.initialized) {
    throw new Error("Runtime security not initialized");
  }

  return {
    dynamic: SecureImport.dynamic
  };
}

/**
 * Check if security is enabled
 */
export function enabled() {
  return GatewayRuntimeSecurity.initialized;
}

export default {
  init,
  status,
  secureFS,
  secureImport,
  enabled
};
