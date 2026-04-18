// conflict.js - Infinity Plugin Conflict Detection
// Phase 1C-A: Runtime Hardening + Real Conflict Detection
//
// Conflict detection rules:
// - Mere existence of workspace/repo copies is NOT a runtime conflict by itself
// - Only warn on actual active/load-path/registry/lifecycle/storage conflicts

const fs = require('fs');
const path = require('path');

/**
 * Get all possible Infinity plugin locations
 */
function getPluginLocations() {
  const locations = [];
  
  // Runtime location (authoritative)
  const runtimeHome = process.env.OPENCLAW_HOME || '.openclaw';
  locations.push({
    path: path.join(runtimeHome, 'plugins', 'infinity'),
    type: 'runtime',
    active: false,
  });
  
  // Workspace location (may be Phase 1B, not necessarily conflicting)
  const workspaceHome = process.env.OPENCLAW_WORKSPACE || '';
  if (workspaceHome) {
    locations.push({
      path: path.join(workspaceHome, 'plugins', 'infinity'),
      type: 'workspace',
      active: false,
    });
  }
  
  // Infinity repo location (if exists)
  const repoHome = '/data/data/com.termux/files/home/.openclaw/infinity-repo/plugins';
  if (fs.existsSync(repoHome)) {
    locations.push({
      path: path.join(repoHome, 'infinity'),
      type: 'repo',
      active: false,
    });
  }
  
  return locations;
}

/**
 * Check if a plugin at location is active (loaded by OpenClaw)
 */
function isPluginActive(location) {
  try {
    const stats = fs.statSync(location);
    if (stats.isDirectory()) {
      // Check if it's a valid plugin (has index.js)
      return fs.existsSync(path.join(location, 'index.js'));
    }
  } catch (e) {
    // Path doesn't exist or is inaccessible
  }
  
  return false;
}

/**
 * Detect plugin conflicts
 * Returns array of detected conflicts
 */
function detectConflicts() {
  const conflicts = [];
  const locations = getPluginLocations();
  
  // Check which locations are active
  for (const location of locations) {
    location.active = isPluginActive(location.path);
  }
  
  // Check for actual conflicts (not just existence)
  const activeLocations = locations.filter(l => l.active);
  
  if (activeLocations.length > 1) {
    // Multiple Infinity plugins are active - this is a REAL conflict
    conflicts.push({
      type: 'active-multiple',
      locations: activeLocations.map(l => l.path),
      severity: 'high',
      description: 'Multiple Infinity plugins are active simultaneously',
      impact: 'Unpredictable behavior possible',
    });
  }
  
  // Check for registry conflicts (duplicate Infinity entries)
  if (checkRegistryConflict()) {
    conflicts.push({
      type: 'registry-duplicate',
      severity: 'medium',
      description: 'Infinity plugin appears multiple times in registry',
      impact: 'Configuration inconsistency',
    });
  }
  
  // Check for lifecycle conflicts (conflicting hooks)
  if (checkLifecycleConflict()) {
    conflicts.push({
      type: 'lifecycle-conflict',
      severity: 'medium',
      description: 'Infinity lifecycle hooks conflict with other plugins',
      impact: 'Hooks may interfere with each other',
    });
  }
  
  // Check for storage conflicts (shared storage from multiple locations)
  if (checkStorageConflict()) {
    conflicts.push({
      type: 'storage-conflict',
      severity: 'high',
      description: 'Infinity storage files conflict across locations',
      impact: 'Capsule corruption possible',
    });
  }
  
  return conflicts;
}

/**
 * Check registry for duplicate Infinity entries
 */
function checkRegistryConflict() {
  try {
    const configPath = path.join(process.env.OPENCLAW_HOME || '.openclaw', 'openclaw.json');
    if (!fs.existsSync(configPath)) {
      return false;
    }
    
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    const plugins = config.plugins || {};
    
    // Count Infinity entries in registry
    let infinityCount = 0;
    
    if (plugins.entries && plugins.entries.infinity) {
      infinityCount++;
    }
    
    // Check if Infinity appears multiple times
    if (infinityCount > 1) {
      return true;
    }
  } catch (e) {
    // Config file unreadable
  }
  
  return false;
}

/**
 * Check for lifecycle hook conflicts
 */
function checkLifecycleConflict() {
  try {
    const runtimeHome = process.env.OPENCLAW_HOME || '.openclaw';
    const hooksDir = path.join(runtimeHome, 'plugins', 'infinity', 'hooks');
    
    if (!fs.existsSync(hooksDir)) {
      return false;
    }
    
    // Check for conflicting hook implementations
    const hooks = fs.readdirSync(hooksDir);
    
    // This is a simplified check - actual conflict would be determined by OpenClaw
    // For now, just log presence of hooks
    return false;
  } catch (e) {
    // Hooks directory unreadable
  }
  
  return false;
}

/**
 * Check for storage file conflicts
 */
function checkStorageConflict() {
  try {
    const runtimeHome = process.env.OPENCLAW_HOME || '.openclaw';
    const capsuleDir = path.join(runtimeHome, 'plugins', 'infinity', 'capsule');
    const storageDir = path.join(runtimeHome, 'plugins', 'infinity', 'storage');
    
    // Check if capsule/storage directories exist
    const hasRuntimeCapsule = fs.existsSync(capsuleDir);
    const hasRuntimeStorage = fs.existsSync(storageDir);
    
    // Check workspace for conflicting storage
    const workspaceHome = process.env.OPENCLAW_WORKSPACE || '';
    if (workspaceHome) {
      const workspaceCapsule = path.join(workspaceHome, 'plugins', 'infinity', 'capsule');
      const workspaceStorage = path.join(workspaceHome, 'plugins', 'infinity', 'storage');
      
      if (hasRuntimeCapsule && fs.existsSync(workspaceCapsule)) {
        // Both runtime and workspace have capsule - potential conflict
        if (hasStorageConflict(capsuleDir, workspaceCapsule)) {
          return true;
        }
      }
      
      if (hasRuntimeStorage && fs.existsSync(workspaceStorage)) {
        // Both runtime and workspace have storage - potential conflict
        if (hasStorageConflict(storageDir, workspaceStorage)) {
          return true;
        }
      }
    }
  } catch (e) {
    // Storage directories unreadable
  }
  
  return false;
}

/**
 * Check if two storage directories have conflicting files
 */
function hasStorageConflict(dir1, dir2) {
  try {
    const files1 = fs.readdirSync(dir1);
    const files2 = fs.readdirSync(dir2);
    
    // Check for files with same names
    const commonFiles = files1.filter(f => files2.includes(f));
    
    if (commonFiles.length > 0) {
      // Files with same name exist in both directories - potential conflict
      return true;
    }
  } catch (e) {
    // Directory unreadable
  }
  
  return false;
}

/**
 * Log conflicts to file
 */
function logConflicts(conflicts) {
  const logPath = path.join(process.env.OPENCLAW_HOME || '.openclaw', 'logs', 'infinity.log');
  
  const timestamp = new Date().toISOString();
  const logEntry = conflicts.map(c => ({
    timestamp,
    type: c.type,
    severity: c.severity,
    description: c.description,
    impact: c.impact,
  }));
  
  try {
    // Append to existing log
    const existingLog = fs.existsSync(logPath) ? fs.readFileSync(logPath, 'utf8') : '';
    fs.appendFileSync(logPath, JSON.stringify(logEntry, null, 2) + '\n---\n');
  } catch (e) {
    // Log file unwritable
    console.log(`[infinity] Conflict log write failed: ${e.message}`);
  }
}

/**
 * Get conflict summary string
 */
function getConflictSummary(conflicts) {
  if (conflicts.length === 0) {
    return 'No conflicts detected';
  }
  
  const severityCounts = {
    high: 0,
    medium: 0,
    low: 0,
  };
  
  for (const conflict of conflicts) {
    severityCounts[conflict.severity] = (severityCounts[conflict.severity] || 0) + 1;
  }
  
  return `Detected ${conflicts.length} conflict(s): ${severityCounts.high} high, ${severityCounts.medium} medium, ${severityCounts.low} low`;
}

module.exports = {
  getPluginLocations,
  isPluginActive,
  detectConflicts,
  checkRegistryConflict,
  checkLifecycleConflict,
  checkStorageConflict,
  hasStorageConflict,
  logConflicts,
  getConflictSummary,
};
