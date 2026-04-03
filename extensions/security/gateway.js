#!/usr/bin/env node
/**
 * extensions/security/gateway.js - Security API for Workspace (Phase 2C)
 * Platform-facing Security API with workspace paths
 */

// Import from the workspace security module
import { SecurityAPI, SecureFS, SecureImport } from "../dist/security/index.js";

export { SecurityAPI, SecureFS, SecureImport };
