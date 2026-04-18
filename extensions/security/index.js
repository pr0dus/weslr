#!/usr/bin/env node
/**
 * extensions/security/index.js - Security Extension (Phase 2C)
 * Gateway runtime integration with opt-in fs wrappers
 */

export { SecurityAPI, SecureFS, SecureImport } from "../dist/security/index.js";

export { 
  isSecurityEnabled, 
  wrapFsPromisesWriteFile, 
  initGatewaySecurityWrappers 
} from "./gateway-wrappers.js";

export { 
  GatewayRuntimeSecurity, 
  initRuntimeSecurity, 
  getSecurityStatus, 
  getSecureFS, 
  getSecureImport 
} from "./gateway.js";

export default {
  SecurityAPI,
  SecureFS,
  SecureImport,
  GatewayRuntimeSecurity,
  init: initRuntimeSecurity,
  status: getSecurityStatus,
  secureFS: getSecureFS,
  secureImport: getSecureImport,
  initWrappers: initGatewaySecurityWrappers,
  isSecurityEnabled,
  wrapFsPromisesWriteFile
};
