#!/usr/bin/env node
/**
 * extensions/security/src/index.js - Security Extension (Phase 2A)
 * Runtime integration entry point
 */

// Platform API
export { SecurityAPI, SecureFS, SecureImport } from "../../dist/security/index.js";

// Gateway runtime integration
export { GatewayRuntimeSecurity, init, status, secureFS, secureImport, enabled } from "./gateway.js";

export default {
  SecurityAPI,
  SecureFS,
  SecureImport,
  GatewayRuntimeSecurity,
  init,
  status,
  secureFS,
  secureImport,
  enabled
};
