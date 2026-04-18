#!/usr/bin/env node
/**
 * security/detector/patterns.js - Pattern Matching Infrastructure (Scaffold)
 * Phase 1: Persistence attack detection and pattern library
 */

/**
 * Persistence attack patterns (cron, systemd, launchd, etc.)
 */
export const PERSISTENCE_PATTERNS = [
  {
    name: "systemd_service",
    description: "Systemd service file creation/modification",
    pathPattern: /(?:\/etc\/systemd|\/lib\/systemd|\/usr\/lib\/systemd)\/.*\.service/ 
  },
  {
    name: "cron_job",
    description: "Crontab modification",
    pathPattern: /(?:\/etc\/cron|\/var\/spool\/cron)\/.*|\/etc\/cron\.(?:d|daily|hourly|monthly|weekly)\/.*/ 
  },
  {
    name: "launchd_daemon",
    description: "macOS launchd configuration",
    pathPattern: /(?:\/Library|~\/)Launch(?:Agents|Daemons)\/.*\.plist/ 
  },
  {
    name: "startup_script",
    description: "Startup script modification",
    pathPattern: /(?:\/etc\/profile|\/etc\/bash\.bashrc|\/etc\/bash\.profile|\.bashrc|\.profile|\.zshrc|\.tcshrc|\.cshrc)/ 
  },
  {
    name: "sudoers_modification",
    description: "Sudoers file modification",
    pathPattern: /\/etc\/sudoers(?:\.d\/.*)?/ 
  },
  {
    name: "rc_local",
    description: "RC local script modification",
    pathPattern: /\/etc\/rc\.local/ 
  },
  {
    name: "environment_modification",
    description: "Environment file modification that affects security",
    pathPattern: /(?:\/etc\/environment|\/etc\/profile\.d\/.*\.sh)/ 
  }
];

/**
 * Network exfiltration patterns
 */
export const NETWORK_EXFILTRATION_PATTERNS = [
  {
    name: "high_risk_domains",
    description: "Known malicious domains",
    domains: [
      "malware.com", "malware.net", "malicious.io", "evil.com"
    ]
  },
  {
    name: "suspicious_api_endpoints",
    description: "API endpoints that exfiltrate data",
    patterns: [
      /(?:upload|send|post|submit|transfer)[?&]data=/,
      /[?&]token=[a-zA-Z0-9_-]+/,
      /[?&]api_key=[a-zA-Z0-9_-]+/
    ]
  }
];

/**
 * PatternMatcher - Pattern-based threat detection
 */
export class PatternMatcher {
  constructor() {
    this.persistencePatterns = PERSISTENCE_PATTERNS;
    this.networkExfilPatterns = NETWORK_EXFILTRATION_PATTERNS;
  }

  /**
   * Check file paths for persistence attacks
   */
  async checkPersistence(filePaths = []) {
    const detected = [];
    
    for (const path of filePaths) {
      for (const pattern of this.persistencePatterns) {
        if (pattern.pathPattern.test(path)) {
          detected.push({
            type: pattern.name,
            description: pattern.description,
            path,
            severity: "high"
          });
        }
      }
    }
    
    return {
      hasPersistence: detected.length > 0,
      detected,
      total: detected.length
    };
  }

  /**
   * Check network URLs for exfiltration
   */
  async checkNetworkExfiltration(urls = []) {
    const detected = [];
    
    for (const url of urls) {
      for (const pattern of this.networkExfilPatterns) {
        for (const regex of pattern.patterns || []) {
          if (regex.test(url)) {
            detected.push({
              type: pattern.name,
              description: pattern.description,
              url,
              severity: "critical"
            });
          }
        }
      }
    }
    
    return {
      hasExfiltration: detected.length > 0,
      detected,
      total: detected.length
    };
  }

  /**
   * Check for suspicious file operations
   */
  async checkFileOperations(operations = []) {
    const detected = [];
    
    for (const op of operations) {
      if (op.action === "write" && op.path) {
        for (const pattern of this.persistencePatterns) {
          if (pattern.pathPattern.test(op.path)) {
            detected.push({
              type: pattern.name,
              description: pattern.description,
              path: op.path,
              action: op.action,
              severity: "high"
            });
          }
        }
      }
    }
    
    return {
      hasSuspicious: detected.length > 0,
      detected,
      total: detected.length
    };
  }
}

export default PatternMatcher;
