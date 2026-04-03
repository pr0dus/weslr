#!/usr/bin/env node
/**
 * security/detector/index.js - Threat Detection Layer (Scaffold)
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
      riskScore: 0,
      threatTags: []
    };

    const maliciousResult = await this.detectors.maliciousCode.scan(code);
    if (maliciousResult.hasIssues) {
      results.issues.push(...maliciousResult.issues);
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
   * Calculate weighted risk score
   */
  calculateRiskScore(threats) {
    // Phase 1: Simplified scoring
    let score = 0;

    for (const tag of threats.threatTags || []) {
      switch (tag) {
        case "code-injection":
          score += 35;
          break;
        case "privilege-escalation":
          score += 30;
          break;
        case "continuity-corruption":
          score += 20;
          break;
        case "plugin-compromise":
          score += 15;
          break;
        case "persistence-attack":
          score += 25;
          break;
        default:
          score += 5;
      }
    }

    return Math.min(100, score);
  }
}

export default ThreatDetector;
