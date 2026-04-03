#!/usr/bin/env node
/**
 * security/detector/malicious-code.js - Malicious Code Detection
 * Phase 1: Pattern-based detection for eval, child_process, etc.
 * Uses regex-based approach to avoid external dependencies
 */

/**
 * Malicious code patterns to detect
 */
export const MALICIOUS_PATTERNS = [
  {
    name: "eval_injection",
    description: "Use of eval() or Function constructor",
    severity: "high",
    patterns: [
      /\beval\s*\(/,
      /\bFunction\s*\(/,
      /\bnew\s+Function\s*\(/,
      /\bescape\s*\(/,
      /\bunescape\s*\(/
    ]
  },
  {
    name: "child_process_rce",
    description: "Potential remote code execution",
    severity: "critical",
    patterns: [
      /child_process\.(?:exec|spawn|execSync|spawnSync)\s*\(/,
      /require\s*\(\s*["']child_process["']\s*\)/,
      /import\s*\(\s*["']child_process["']\s*\)/
    ]
  },
  {
    name: "fs_write_anywhere",
    description: "Writing to arbitrary file paths",
    severity: "high",
    patterns: [
      /fs\.(?:writeFileSync|writeFile)\s*\(\s*["']\/[a-zA-Z]/,
      /fs\.(?:writeFileSync|writeFile)\s*\(\s*["'][a-zA-Z]:\//
    ]
  },
  {
    name: "eval_via_proxy",
    description: "Dynamic imports with potential injection",
    severity: "high",
    patterns: [
      /import\s*\(\s*process\.env/,
      /import\s*\(\s*process\.argv/,
      /import\s*\(\s*require\.resolve/
    ]
  },
  {
    name: "setuid_sudo",
    description: "Privilege escalation attempts",
    severity: "critical",
    patterns: [
      /\bsudo\b/,
      /\bsetuid\s*\(/,
      /chmod\s+\+s/
    ]
  },
  {
    name: "network_exfiltration",
    description: "Potential data exfiltration",
    severity: "critical",
    patterns: [
      /fetch\s*\([^)]*["']https?:\/\/[^\s"'&]+[?&](?:data|token|key)=/,
      /axios\.(?:get|post)\s*\([^)]*[?&](?:token|key)=/
    ]
  }
];

/**
 * MaliciousCodeDetector - Scans code for malicious patterns
 */
export class MaliciousCodeDetector {
  constructor() {
    this.patterns = MALICIOUS_PATTERNS;
  }

  /**
   * Scan code string for malicious patterns
   */
  async scan(code) {
    const issues = [];

    for (const pattern of this.patterns) {
      for (const regex of pattern.patterns) {
        const match = code.match(regex);
        if (match) {
          issues.push({
            type: pattern.name,
            severity: pattern.severity,
            pattern: pattern.description,
            foundAt: code.search(regex),
            match: match[0]
          });
        }
      }
    }

    return {
      hasIssues: issues.length > 0,
      issues,
      riskScore: this.calculateRisk(issues)
    };
  }

  /**
   * Check command for privilege escalation
   */
  async checkPrivilegeEscalation(command, args = []) {
    const fullCommand = [command, ...args].join(" ");
    const issues = [];

    for (const pattern of this.patterns) {
      if (pattern.name === "setuid_sudo") {
        for (const regex of pattern.patterns) {
          if (fullCommand.match(regex)) {
            issues.push({
              type: pattern.name,
              severity: pattern.severity,
              foundAt: fullCommand.search(regex),
              match: fullCommand.match(regex)[0]
            });
          }
        }
      }
    }

    return {
      hasIssues: issues.length > 0,
      issues,
      command: fullCommand
    };
  }

  /**
   * Calculate risk score from issues
   */
  calculateRisk(issues) {
    if (issues.length === 0) return 0;

    let score = 0;

    for (const issue of issues) {
      switch (issue.severity) {
        case "critical":
          score += 30;
          break;
        case "high":
          score += 20;
          break;
        case "medium":
          score += 10;
          break;
        case "low":
          score += 5;
          break;
        default:
          score += 5;
      }
    }

    return Math.min(100, score);
  }
}

export default MaliciousCodeDetector;
