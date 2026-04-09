// index.js - OpenClaw Infinity Plugin entry point (runtime plugin contract)
// Phase 1B: Runtime License Enforcement - Paid functionality fails closed

const hooks = require('./hooks');
const config = require('./config');
const { LicenseValidator } = require('./licensing/validator');
const { LicenseEnforcer } = require('./licensing/enforcer');
const path = require('path');

// Internal state
let licenseValid = false;
let licenseInfo = null;
let licenseError = null;

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
            expiresAt: license.license.expiresAt
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
 * Check if license is valid (for hooks to check)
 */
function isLicenseValid() {
    return licenseValid;
}

/**
 * Get license error (if any)
 */
function getLicenseError() {
    return licenseError;
}

/**
 * Initialize plugin with license check
 */
function register(api) {
    // Check license on startup
    loadLicense();
    
    // Determine mode
    const isPremium = licenseValid && config.autoCaptureEnabled && config.autoRestoreEnabled;
    
    // Log initialization
    if (isPremium) {
        console.log('[infinity] Plugin initialized (premium mode)');
    } else if (licenseValid) {
        console.log('[infinity] Plugin initialized (degraded mode - premium disabled)');
    } else {
        console.log('[infinity] Plugin initialized (degraded mode - invalid license)');
    }
    
    // Register hooks only if premium mode
    if (!isPremium) {
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
    // Phase 1B: License status API
    getStatus: () => ({
        licenseValid,
        licenseError,
        licenseInfo,
        premiumEnabled: licenseValid && config.autoCaptureEnabled && config.autoRestoreEnabled
    }),
    // Phase 1B: License check helper for hooks
    isLicenseValid,
    getLicenseError,
};

// Runtime plugin export contract
module.exports = {
    register,
    plugin
};
