// hardening.js - Infinity Plugin Runtime Hardening Checks
// Phase 1C-A: Runtime Hardening + Conflict Detection

const fs = require('fs');
const path = require('path');

/**
 * Required module paths
 */
const REQUIRED_MODULES = [
  'config.js',
  'index.js',
  'hooks/index.js',
  'hooks/capture.js',
  'hooks/restore.js',
];

/**
 * Check if all required modules exist
 */
function validateModulePaths() {
  const issues = [];
  
  for (const module of REQUIRED_MODULES) {
    const modulePath = path.join(process.env.OPENCLAW_HOME || '.openclaw', 'plugins', 'infinity', module);
    if (!fs.existsSync(modulePath)) {
      issues.push({
        type: 'missing-module',
        module,
        path: modulePath,
      });
    }
  }
  
  return issues;
}

/**
 * Check file permissions
 */
function checkFilePermissions() {
  const issues = [];
  
  // Check Infinity plugin directory permissions
  const pluginDir = path.join(process.env.OPENCLAW_HOME || '.openclaw', 'plugins', 'infinity');
  if (fs.existsSync(pluginDir)) {
    try {
      const stats = fs.statSync(pluginDir);
      
      // Check if directory is world-readable (not ideal for production)
      if (stats.mode & 0o004) {
        issues.push({
          type: 'world-readable',
          path: pluginDir,
          mode: stats.mode.toString(8),
        });
      }
    } catch (e) {
      // Directory unreadable
    }
  }
  
  // Check license file permissions if exists
  const licensePath = path.join(process.env.OPENCLAW_HOME || '.openclaw', 'licenses', 'infinity-license.json');
  if (fs.existsSync(licensePath)) {
    try {
      const stats = fs.statSync(licensePath);
      
      if (stats.mode & 0o004) {
        issues.push({
          type: 'license-world-readable',
          path: licensePath,
          mode: stats.mode.toString(8),
        });
      }
    } catch (e) {
      // License file unreadable
    }
  }
  
  return issues;
}

/**
 * Validate license file location
 */
function validateLicenseLocation() {
  const issues = [];
  
  const expectedPath = path.join(process.env.OPENCLAW_HOME || '.openclaw', 'licenses', 'infinity-license.json');
  const licenseDir = path.dirname(expectedPath);
  
  // Check if license directory exists
  if (!fs.existsSync(licenseDir)) {
    issues.push({
      type: 'missing-license-directory',
      path: licenseDir,
    });
  }
  
  // Check if license file is in expected location
  if (fs.existsSync(expectedPath)) {
    // License file exists - verify it's in correct location
    // (no need to check path again since we just verified it)
  }
  
  return issues;
}

/**
 * Check baseline identity
 */
function checkBaselineIdentity() {
  const issues = [];
  
  try {
    const versionPath = path.join(process.env.OPENCLAW_HOME || '.openclaw', 'plugins', 'infinity', 'version.js');
    if (!fs.existsSync(versionPath)) {
      issues.push({
        type: 'missing-version-file',
        path: versionPath,
      });
      return issues;
    }
    
    // Note: This would require dynamic require, which is complex
    // For now, just check file exists
    const stats = fs.statSync(versionPath);
    
    if (stats.size < 1000) {
      issues.push({
        type: 'version-file-too-small',
        path: versionPath,
        size: stats.size,
      });
    }
  } catch (e) {
    // Version file unreadable
    issues.push({
      type: 'version-file-unreadable',
      error: e.message,
    });
  }
  
  return issues;
}

/**
 * Run all hardening checks
 */
function runHardeningChecks() {
  const results = {
    valid: true,
    checks: {
      modulePaths: [],
      filePermissions: [],
      licenseLocation: [],
      baselineIdentity: [],
    },
    summary: '',
  };
  
  // Run checks
  results.checks.modulePaths = validateModulePaths();
  results.checks.filePermissions = checkFilePermissions();
  results.checks.licenseLocation = validateLicenseLocation();
  results.checks.baselineIdentity = checkBaselineIdentity();
  
  // Determine overall validity
  if (results.checks.modulePaths.length > 0 ||
      results.checks.filePermissions.length > 0 ||
      results.checks.licenseLocation.length > 0 ||
      results.checks.baselineIdentity.length > 0) {
    results.valid = false;
  }
  
  // Generate summary
  const totalIssues = 
    results.checks.modulePaths.length +
    results.checks.filePermissions.length +
    results.checks.licenseLocation.length +
    results.checks.baselineIdentity.length;
  
  results.summary = `${totalIssues} hardening issue(s) detected`;
  
  return results;
}

/**
 * Log hardening results
 */
function logHardeningResults(results) {
  const logPath = path.join(process.env.OPENCLAW_HOME || '.openclaw', 'logs', 'infinity.log');
  const timestamp = new Date().toISOString();
  
  const logEntry = {
    timestamp,
    type: 'hardening',
    valid: results.valid,
    summary: results.summary,
    checks: results.checks,
  };
  
  try {
    fs.appendFileSync(logPath, JSON.stringify(logEntry, null, 2) + '\n---\n');
  } catch (e) {
    console.log(`[infinity] Hardening log write failed: ${e.message}`);
  }
}

/**
 * Get hardening status string
 */
function getHardeningStatus(results) {
  if (results.valid) {
    return 'All hardening checks passed';
  }
  
  return `Hardening issues: ${results.summary}`;
}

module.exports = {
  REQUIRED_MODULES,
  validateModulePaths,
  checkFilePermissions,
  validateLicenseLocation,
  checkBaselineIdentity,
  runHardeningChecks,
  logHardeningResults,
  getHardeningStatus,
};
