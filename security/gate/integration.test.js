#!/usr/bin/env node
/**
 * security/gate/integration.test.js - Integration Tests for Gate Hooks (Phase 2B)
 */

import { preWriteHook, preEvolutionHook } from "./index.js";
import SecurityPolicy from "../policy/index.js";
import SecurityLogs from "../audit/logs/index.js";

// Test data
const MALICIOUS_CONTENT = `
const { exec } = require('child_process');
exec('rm -rf /');
eval('console.log("hacked")');
`;

const BENIGN_CONTENT = `
const fs = require('fs');
function greet(name) { return 'Hello, ' + name; }
module.exports = { greet };
`;

const IMMUTABLE_PATH = "security/index.js";

const POLICY_PATH = "dist/security/index.js";

/**
 * Run all integration tests
 */
export async function runIntegrationTests() {
  console.log("=== PHASE 2B HOOK INTEGRATION TESTS ===\n");
  
  const results = [];
  
  // Test 1: Malicious write should be blocked
  try {
    console.log("Test 1: Malicious write blocked?");
    const hook1 = await preWriteHook("/tmp/test.js", {
      action: "write",
      content: MALICIOUS_CONTENT
    });
    const test1Pass = hook1.blocked === true;
    console.log(`  Result: ${test1Pass ? "BLOCKED" : "ALLOWED"} (expected: BLOCKED)`);
    console.log(`  Risk score: ${hook1.riskScore}`);
    console.log(`  Reason: ${hook1.reason || "none"}`);
    results.push({ name: "malicious_write_blocked", pass: test1Pass });
  } catch (err) {
    console.error("  Error:", err.message);
    results.push({ name: "malicious_write_blocked", pass: false, error: err.message });
  }
  
  // Test 2: Immutable path should be blocked
  try {
    console.log("\nTest 2: Immutable path blocked?");
    const hook2 = await preWriteHook(IMMUTABLE_PATH, {
      action: "write"
    });
    const test2Pass = hook2.blocked === true && hook2.riskScore === 100;
    console.log(`  Result: ${test2Pass ? "BLOCKED" : "ALLOWED"} (expected: BLOCKED)`);
    console.log(`  Risk score: ${hook2.riskScore} (expected: 100)`);
    console.log(`  Reason: ${hook2.reason || "none"}`);
    results.push({ name: "immutable_path_blocked", pass: test2Pass });
  } catch (err) {
    console.error("  Error:", err.message);
    results.push({ name: "immutable_path_blocked", pass: false, error: err.message });
  }
  
  // Test 3: Benign write should be allowed
  try {
    console.log("\nTest 3: Benign write allowed?");
    const hook3 = await preWriteHook("/tmp/benign.js", {
      action: "write",
      content: BENIGN_CONTENT
    });
    const test3Pass = hook3.blocked === false && hook3.riskScore === 0;
    console.log(`  Result: ${test3Pass ? "ALLOWED" : "BLOCKED"} (expected: ALLOWED)`);
    console.log(`  Risk score: ${hook3.riskScore} (expected: 0)`);
    results.push({ name: "benign_write_allowed", pass: test3Pass });
  } catch (err) {
    console.error("  Error:", err.message);
    results.push({ name: "benign_write_allowed", pass: false, error: err.message });
  }
  
  // Test 4: Malicious import should be blocked
  try {
    console.log("\nTest 4: Malicious import blocked?");
    const hook4 = await preEvolutionHook("/tmp/malicious.js", {
      content: MALICIOUS_CONTENT
    });
    const test4Pass = hook4.blocked === true;
    console.log(`  Result: ${test4Pass ? "BLOCKED" : "ALLOWED"} (expected: BLOCKED)`);
    console.log(`  Risk score: ${hook4.riskScore}`);
    console.log(`  Reason: ${hook4.reason || "none"}`);
    results.push({ name: "malicious_import_blocked", pass: test4Pass });
  } catch (err) {
    console.error("  Error:", err.message);
    results.push({ name: "malicious_import_blocked", pass: false, error: err.message });
  }
  
  // Test 5: Benign import should be allowed
  try {
    console.log("\nTest 5: Benign import allowed?");
    const hook5 = await preEvolutionHook("/tmp/benign.js", {
      content: BENIGN_CONTENT
    });
    const test5Pass = hook5.blocked === false && hook5.riskScore === 0;
    console.log(`  Result: ${test5Pass ? "ALLOWED" : "BLOCKED"} (expected: ALLOWED)`);
    console.log(`  Risk score: ${hook5.riskScore} (expected: 0)`);
    results.push({ name: "benign_import_allowed", pass: test5Pass });
  } catch (err) {
    console.error("  Error:", err.message);
    results.push({ name: "benign_import_allowed", pass: false, error: err.message });
  }
  
  // Summary
  console.log("\n=== INTEGRATION TEST RESULTS ===");
  let allPass = true;
  for (const r of results) {
    console.log(`${r.name}: ${r.pass ? "PASS" : "FAIL"}`);
    if (r.error) console.log(`  Error: ${r.error}`);
    if (!r.pass) allPass = false;
  }
  console.log(`\nOverall: ${allPass ? "ALL TESTS PASSED" : "SOME TESTS FAILED"}`);
  
  return { results, allPassed: allPass };
}

export default {
  runIntegrationTests
};
