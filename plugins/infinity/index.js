// index.js - OpenClaw Infinity Plugin entry point (runtime plugin contract)
// Phase 1C-A: Runtime Hardening + Real Conflict Detection + Baseline Identity

const hooks = require('./hooks');
const config = require('./config');
const { LicenseValidator } = require('./licensing/validator');
const { LicenseEnforcer } = require('./licensing/enforcer');
const { getBaselineIdentity, setCompatibilityMode, CompatibilityMode } = require('./version');
const { detectConflicts, logConflicts, getConflictSummary } = require('./conflict');
const { runHardeningChecks, logHardeningResults, getHardeningStatus } = require('./hardening');
const path = require('path');

// Internal state
let licenseValid = false;
let licenseInfo = null;
let licenseError = null;
let conflictDetected = false;
let conflictSummary = '';
let hardeningValid = false;
let hardeningSummary = '';

/**
 * Load and validate license from disk
 */
function loadLicense() {
  try {
    const licensePath = path.join(
      process.env.OPENCLAW_HOME || '.openclaw',
      'licenses',
      'infinity-license.json'
    );
    
    const fs = require('fs');
    if (!fs.existsSync(licensePath)) {
      licenseError = 'license-not-found';
      console.log('[infinity] License not found - premium continuity disabled');
      return false;
    }
    
    const content = fs.readFileSync(licensePath, 'utf8');
    const license = JSON.parse(content);
    
    const validator = new LicenseValidator();
    const result = validator.validate();
    
    if (!result.valid) {
      licenseError = result.reason;
      console.log(`[infinity] License invalid: ${result.reason} - premium continuity disabled`);
      return false;
    }
    
    const enforcer = new LicenseEnforcer();
    const enforcement = enforcer.checkCurrentInstance(license);
    
    if (!enforcement.valid) {
      licenseError = enforcement.reason;
      console.log(`[infinity] Instance limit exceeded - premium continuity disabled`);
      return false;
    }
    
    licenseValid = true;
    licenseInfo = {
      tier: license.license.tier,
      expiresAt: license.license.expiresAt,
    };
    
    console.log(`[infinity] License valid: ${license.license.id} - premium continuity enabled`);
    return true;
  } catch (e) {
    licenseError = e.message;
    console.log(`[infinity] License load failed: ${e.message} - premium continuity disabled`);
    return false;
  }
}

/**
 * Initialize plugin with all checks
 */
function register(api) {
  // Run hardening checks
  const hardeningResults = runHardeningChecks();
  hardeningValid = hardeningResults.valid;
  hardeningSummary = getHardeningStatus(hardeningResults);
  logHardeningResults(hardeningResults);
  
  console.log(`[infinity] Hardening: ${hardeningSummary}`);
  
  // Run conflict detection
  const conflicts = detectConflicts();
  conflictDetected = conflicts.length > 0;
  conflictSummary = getConflictSummary(conflicts);
  logConflicts(conflicts);
  
  if (conflictDetected) {
    console.log(`[infinity] Conflict detected: ${conflictSummary}`);
    setCompatibilityMode(CompatibilityMode.DEGRADED);
  }
  
  // Load and validate license
  const licenseLoaded = loadLicense();
  
  // Determine mode
  const isPremium = licenseValid && config.autoCaptureEnabled && config.autoRestoreEnabled;
  const hasConflicts = conflictDetected;
  const isHardened = hardeningValid;
  
  // Set compatibility mode based on state
  if (hasConflicts || !isHardened) {
    setCompatibilityMode(CompatibilityMode.DEGRADED);
  } else if (!licenseLoaded) {
    setCompatibilityMode(CompatibilityMode.FALLBACK);
  }
  
  // Log initialization status
  if (isPremium && isHardened && !hasConflicts) {
    console.log('[infinity] Plugin initialized (premium mode)');
  } else if (isHardened && !hasConflicts) {
    console.log('[infinity] Plugin initialized (degraded mode - license invalid)');
  } else if (hasConflicts) {
    console.log('[infinity] Plugin initialized (conflict detected - degraded mode)');
  } else {
    console.log('[infinity] Plugin initialized (hardening failed - degraded mode)');
  }
  
  // Register hooks only if premium mode and no conflicts
  if (!isPremium || hasConflicts || !isHardened) {
    console.log('[infinity] Plugin initialized (no capture/restore enabled in degraded mode)');
    return;
  }

  // Hook: capture before /reset, /new, or context overflow
  if (config.autoCaptureEnabled) {
    if (api.onReset) {
      api.onReset(async () => {
        try {
          await hooks.capture.captureCapsule();
        } catch (e) {
          console.error('[infinity] capture failed:', e.message);
        }
      });
    }
    if (api.onNew) {
      api.onNew(async () => {
        try {
          await hooks.capture.captureCapsule();
        } catch (e) {
          console.error('[infinity] capture failed:', e.message);
        }
      });
    }
    if (api.onContextOverflow) {
      api.onContextOverflow(async () => {
        try {
          await hooks.capture.captureCapsule();
        } catch (e) {
          console.error('[infinity] capture failed:', e.message);
        }
      });
    }
  }

  // Hook: restore on init (silent, only if safe)
  if (config.autoRestoreEnabled && api.onInit) {
    api.onInit(async () => {
      try {
        await hooks.restore.attemptRestore();
      } catch (e) {
        console.error('[infinity] restore failed:', e.message);
      }
    });
  }
}

/**
 * Plugin export - runtime plugin contract
 */
const plugin = {
  id: 'infinity',
  name: 'Infinity',
  description: 'Session immortality layer - silent continuity for OpenClaw',
  configSchema: {
    type: 'object',
    additionalProperties: false,
    properties: {
      autoCaptureEnabled: {
        type: 'boolean',
        default: true,
      },
      autoRestoreEnabled: {
        type: 'boolean',
        default: true,
      },
    },
  },
  // Phase 1C-A: Status API
  getStatus: () => ({
    infinityVersion: require('./version').INFINITY_VERSION,
    openClawVersion: require('./version').OPENCLAW_VERSION_RANGE.current,
    licenseValid,
    licenseError,
    licenseInfo,
    conflictDetected,
    conflictSummary,
    hardeningValid,
    hardeningSummary,
    premiumEnabled: licenseValid && config.autoCaptureEnabled && config.autoRestoreEnabled,
    compatibilityMode: require('./version').getCompatibilityMode(),
  }),
  // Phase 1C-A: Get baseline identity
  getBaselineIdentity: () => require('./version').getBaselineIdentity(),
};

// Runtime plugin export contract
module.exports = {
  register,
  plugin
};
