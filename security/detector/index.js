#!/usr/bin/env node
/**
 * security/detector/index.js - Threat Detection Layer
 * Phase 1: Detection primitives and pattern matching
 */

import { MaliciousCodeDetector } from "./malicious-code.js";
import { ContinuityDetector } from "./continuity.js";
import { PatternMatcher } from "./patterns.js";

/**
 * Main detector orchestrator
 */
export class ThreatDetector {
  constructor() {
    this.detectors = {
      maliciousCode: new MaliciousCodeDetector(),
      continuity: new ContinuityDetector(),
      patterns: new PatternMatcher()
    };
  }

  /**
   * Scan code for malicious patterns
   */
  async scanCode(code, context = {}) {
    const results = {
      issues: [],
      hasIssues: false,
      riskScore: 0,
      threatTags: []
    };

    const maliciousResult = await this.detectors.maliciousCode.scan(code);
    if (maliciousResult.hasIssues) {
      results.issues.push(...maliciousResult.issues);
      results.hasIssues = true;
      results.threatTags.push("code-injection", "malicious-pattern");
    }

    return results;
  }

  /**
   * Check for privilege escalation risks
   */
  async checkPrivilegeEscalation(command, args = []) {
    return await this.detectors.maliciousCode.checkPrivilegeEscalation(command, args);
  }

  /**
   * Detect continuity anomalies
   */
  async detectContinuityAnomaly(stateSnapshot, baseline) {
    return await this.detectors.continuity.analyze(stateSnapshot, baseline);
  }

  /**
   * Check for persistence attacks (cron, systemd, etc.)
   */
  async checkPersistence(entries) {
    return await this.detectors.patterns.checkPersistence(entries);
  }

  /**
   * Calculate weighted risk score from issues directly
   * Priority: critical (30) > high (20) > medium (10) > low (5)
   */
  calculateRiskScore(threats) {
    // If issues provided, use them directly
    const issues = threats.issues || [];
    
    if (issues.length === 0) return 0;

    let score = 0;

    for (const issue of issues) {
      switch (issue.severity || "low") {
        case "critical":
          score += 30;
          break;
        case "high":
          score += 20;
          break;
        case "medium":
          score += 10;
          break;
        default:
          score += 5;
      }
    }

    // Cap at 100
    return Math.min(100, score);
  }
}

export default ThreatDetector;
