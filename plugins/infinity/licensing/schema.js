/**
 * Infinity Productization Phase 1A — Licensing Core
 * 
 * Schema definitions for licensing data structures.
 * Server-side signing, client-side verification.
 * No private key on customer machine.
 */

/**
 * License Tier Definitions
 */
const LicenseTier = {
    ONE_OC: '1oc',
    THREE_OC: '3oc',
    SEVEN_OC: '7oc',
    UNLIMITED: 'unlimited'
};

/**
 * Maximum instances per tier
 */
const TIER_MAX_INSTANCES = {
    [LicenseTier.ONE_OC]: 1,
    [LicenseTier.THREE_OC]: 3,
    [LicenseTier.SEVEN_OC]: 7,
    [LicenseTier.UNLIMITED]: -1  // -1 means no limit
};

/**
 * Support levels
 */
const SupportLevel = {
    STANDARD: 'standard',
    PREMIUM: 'premium',
    ENTERPRISE: 'enterprise'
};

/**
 * License schema
 */
class LicenseSchema {
    static validate(license) {
        const errors = [];
        
        // Required top-level fields
        if (!license.license) errors.push('license object missing');
        if (!license.instance) errors.push('instance object missing');
        if (!license.signature) errors.push('signature object missing');
        
        // License fields
        if (license.license) {
            if (!license.license.id) errors.push('license.id required');
            if (!license.license.tier) errors.push('license.tier required');
            if (license.license.tier && !Object.values(LicenseTier).includes(license.license.tier)) {
                errors.push(`license.tier must be one of: ${Object.values(LicenseTier).join(', ')}`);
            }
            if (!license.license.issuedAt) errors.push('license.issuedAt required');
            if (!license.license.expiresAt) errors.push('license.expiresAt required');
        }
        
        // Instance fields
        if (license.instance) {
            if (!license.instance.id) errors.push('instance.id required');
            if (!license.instance.workspace) errors.push('instance.workspace required');
            if (!license.instance.installedAt) errors.push('instance.installedAt required');
        }
        
        // Signature fields
        if (license.signature) {
            if (!license.signature.algorithm) errors.push('signature.algorithm required');
            if (!license.signature.publicKey) errors.push('signature.publicKey required');
            if (!license.signature.signature) errors.push('signature.signature required');
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    }
    
    static createLicense(tier, workspace, hostname, openclawVersion, installId) {
        return {
            meta: {
                formatVersion: '1.0',
                type: 'infinity-license'
            },
            license: {
                id: this.generateId(),
                tier,
                issuedAt: new Date().toISOString(),
                expiresAt: this.calculateExpiry(),
                renewable: true,
                maxInstances: TIER_MAX_INSTANCES[tier]
            },
            instance: {
                id: this.generateId(),
                workspace,
                hostname,
                openclawVersion,
                installedAt: new Date().toISOString(),
                lastActive: new Date().toISOString(),
                installId,
                fingerprint: null  // Will be set by signer
            },
            signature: {
                algorithm: 'RSA-SHA256',
                publicKey: null,  // Will be set by signer
                signature: null  // Will be set by signer
            },
            entitlements: {
                updateEligibleUntil: this.calculateExpiry(),
                supportsRenewal: true,
                supportLevel: SupportLevel.STANDARD
            },
            audit: {
                createdBy: 'license-server',
                createdAt: new Date().toISOString(),
                lastValidated: null
            }
        };
    }
    
    static generateId() {
        // Simple UUID-like identifier
        return 'license-' + Math.random().toString(36).substring(2, 15);
    }
    
    static calculateExpiry() {
        // 12 months from now
        const expiry = new Date();
        expiry.setFullYear(expiry.getFullYear() + 1);
        return expiry.toISOString();
    }
    
    static createFingerprint(hostname, workspace, installId, activationTimestamp) {
        // Deterministic fingerprint:
        // HMAC-SHA256 of concatenated components
        const components = [
            'instance-',
            this.hashString(hostname),
            this.hashString(workspace),
            this.hashString(installId),
            this.hashString(activationTimestamp)
        ].join('');
        
        return this.hashString(components);
    }
    
    static hashString(str) {
        if (!str) {
            str = '';
        }
        const crypto = require('crypto');
        return crypto.createHash('sha256').update(str).digest('hex');
    }
    
    static getLicensePath() {
        return require('path').join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'licenses',
            'infinity-license.json'
        );
    }
    
    static getPublicKeyPath() {
        return require('path').join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'keys',
            'infinity-public.pem'
        );
    }
    
    static getLicenseDirectory() {
        return require('path').join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'licenses'
        );
    }
    
    static isValidTier(tier) {
        return Object.values(LicenseTier).includes(tier);
    }
    
    static getMaxInstances(tier) {
        return TIER_MAX_INSTANCES[tier] || -1;
    }
}

module.exports = {
    LicenseTier,
    TIER_MAX_INSTANCES,
    SupportLevel,
    LicenseSchema
};
