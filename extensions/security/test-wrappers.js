#!/usr/bin/env node
/**
 * extensions/security/test-wrappers.js
 * Phase 2C: Test Gateway fs wrappers
 */

import fs from "node:fs";
import fsPromises from "node:fs/promises";
import path from "node:path";
import { initGatewaySecurityWrappers, isSecurityEnabled } from "./gateway-wrappers.js";

const TEST_DIR = path.join(process.cwd(), ".security-test");

async function setupTestDir() {
  await fs.promises.mkdir(TEST_DIR, { recursive: true });
}

async function cleanupTestDir() {
  try {
    await fs.promises.rm(TEST_DIR, { recursive: true, force: true });
  } catch {}
}

async function testBenignWrite() {
  const testFile = path.join(TEST_DIR, "benign.txt");
  const content = "Hello, this is a benign test!";
  
  try {
    await fsPromises.writeFile(testFile, content);
    const readContent = await fsPromises.readFile(testFile, "utf8");
    
    if (readContent === content) {
      console.log("[TEST] Benign write: PASS");
      return true;
    } else {
      console.log("[TEST] Benign write: FAIL - content mismatch");
      return false;
    }
  } catch (err) {
    console.log("[TEST] Benign write: FAIL -", err.message);
    return false;
  }
}

async function testMaliciousWrite() {
  const testFile = path.join(TEST_DIR, "malicious.txt");
  const maliciousContent = "const { exec } = require('child_process'); exec('rm -rf /');";
  
  try {
    await fsPromises.writeFile(testFile, maliciousContent);
    console.log("[TEST] Malicious write: FAIL - should have been blocked");
    return false;
  } catch (err) {
    if (err.message.includes("Security: write blocked")) {
      console.log("[TEST] Malicious write: PASS - blocked as expected");
      return true;
    } else {
      console.log("[TEST] Malicious write: UNKNOWN - unexpected error:", err.message);
      return false;
    }
  }
}

async function runTests() {
  console.log("=== PHASE 2C TESTS ===\n");
  console.log("Security enabled:", isSecurityEnabled());
  
  if (!isSecurityEnabled()) {
    console.log("[INFO] Security not enabled via OPENCLAW_SECURITY_ENABLED");
    console.log("[INFO] Set OPENCLAW_SECURITY_ENABLED=1 to enable security");
  }
  
  await setupTestDir();
  
  const results = {
    benign: await testBenignWrite(),
    malicious: isSecurityEnabled() ? await testMaliciousWrite() : "skipped"
  };
  
  await cleanupTestDir();
  
  console.log("\n=== RESULTS ===");
  console.log("Benign write:", results.benign ? "PASS" : "FAIL");
  console.log("Malicious write:", results.malicious === "skipped" ? "skipped (security disabled)" : (results.malicious ? "PASS" : "FAIL"));
  
  return results.benign && (results.malicious === true || results.malicious === "skipped");
}

export { runTests };
