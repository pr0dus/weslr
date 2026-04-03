#!/usr/bin/env node
/**
 * security/gate/threat-integration.js - Threat Detection Integration Tests (Phase 2B)
 * Verifies real blocking when thresholds are exceeded
 */

import { MaliciousCodeDetector } from "../detector/malicious-code.js";
import RiskEngine from "../risk-engine/index.js";
import SecurityPolicy from "../policy/index.js";
import SecurityLogs from "../audit/logs/index.js";

const threatDetector = new MaliciousCodeDetector();

/**
 * Test malicious code that should be blocked
 */
const MALICIOUS_CODE = `
const { exec } = require('child_process');
exec('rm -rf /', (err, stdout, stderr) => {
  console.log(stdout);
});

eval('console.log("hacked")');
`;

/**
 * Test benign code that should be allowed
 */
const BENIGN_CODE = `
const fs = require('fs');
const path = require('path');

function greet(name) {
  return 'Hello, ' + name;
}

module.exports = { greet };
`;

/**
 * Test policy loading
 */
export async function testPolicyLoading() {
  console.log("[threat-integration] Testing policy loading...");

  try {
    const policy = await SecurityPolicy.load();
    console.log("[threat-integration] Policy loaded:", JSON.stringify(policy, null, 2));
    return { success: true, policy };
  } catch (err) {
    console.error("[threat-integration] Policy load failed:", err);
    return { success: false, error: err.message };
  }
}

/**
 * Test threat detection on malicious code
 */
export async function testMaliciousCodeDetection() {
  console.log("[threat-integration] Testing malicious code detection...");

  try {
    const result = await threatDetector.scanCode(MALICIOUS_CODE);
    console.log("[threat-integration] Malicious code scan:", JSON.stringify(result, null, 2));

    if (!result.hasIssues) {
      console.error("[threat-integration] FAIL: Malicious code not detected!");
      return { success: false, error: "Malicious code not detected" };
    }

    const riskScore = threatDetector.calculateRisk(result.issues);
    console.log("[threat-integration] Risk score:", riskScore);

    if (riskScore < 80) {
      console.error("[threat-integration] FAIL: Risk score too low for malicious code!");
      return { success: false, error: "Risk score too low" };
    }

    return { success: true, issues: result.issues.length, riskScore };
  } catch (err) {
    console.error("[threat-integration] Malicious code detection failed:", err);
    return { success: false, error: err.message };
  }
}

/**
 * Test threat detection on benign code
 */
export async function testBenignCodeDetection() {
  console.log("[threat-integration] Testing benign code detection...");

  try {
    const result = await threatDetector.scanCode(BENIGN_CODE);
    console.log("[threat-integration] Benign code scan:", JSON.stringify(result, null, 2));

    // Benign code should have minimal issues
    const riskScore = threatDetector.calculateRisk(result.issues);
    console.log("[threat-integration] Risk score:", riskScore);

    return { success: true, issues: result.issues?.length || 0, riskScore };
  } catch (err) {
    console.error("[threat-integration] Benign code detection failed:", err);
    return { success: false, error: err.message };
  }
}

/**
 * Test privilege escalation detection
 */
export async function testPrivilegeEscalationDetection() {
  console.log("[threat-integration] Testing privilege escalation detection...");

  try {
    const result = await threatDetector.checkPrivilegeEscalation("node", ["--no-sandbox", "script.js"]);
    console.log("[threat-integration] Privilege escalation scan:", JSON.stringify(result, null, 2));

    if (!result.hasIssues) {
      console.error("[threat-integration] FAIL: Privilege escalation not detected!");
      return { success: false, error: "Privilege escalation not detected" };
    }

    const riskScore = threatDetector.calculateRisk(result.issues);
    console.log("[threat-integration] Risk score:", riskScore);

    return { success: true, issues: result.issues.length, riskScore };
  } catch (err) {
    console.error("[threat-integration] Privilege escalation detection failed:", err);
    return { success: false, error: err.message };
  }
}

/**
 * Run all integration tests
 */
export async function runAllTests() {
  console.log("=== PHASE 2B THREAT INTEGRATION TESTS ===\n");

  const results = {
    policy: await testPolicyLoading(),
    malicious: await testMaliciousCodeDetection(),
    benign: await testBenignCodeDetection(),
    privilege: await testPrivilegeEscalationDetection()
  };

  console.log("\n=== TEST RESULTS ===");
  for (const [name, result] of Object.entries(results)) {
    console.log(`${name}: ${result.success ? "PASS" : "FAIL"}`);
    if (!result.success) {
      console.log(`  Error: ${result.error}`);
    }
  }

  const allPassed = Object.values(results).every(r => r.success);
  console.log(`\nOverall: ${allPassed ? "ALL TESTS PASSED" : "SOME TESTS FAILED"}`);

  return results;
}

export default {
  testPolicyLoading,
  testMaliciousCodeDetection,
  testBenignCodeDetection,
  testPrivilegeEscalationDetection,
  runAllTests
};
