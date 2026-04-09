/**
 * validator.js - Infinity Productization Phase 1A — Licensing Core
 * 
 * License validation logic with new binding model:
 * - Hard-binding: installId + machineFingerprint
 * - Advisory: workspace, hostname, openclawVersion (warn but PASS)
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { 
    canonicalizePayload, 
    payloadToBytes,
    validate as validateSchema,
    SupportLevel
} = require('./schema');

class LicenseValidator {
    constructor() {
        this.licensePath = path.join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'licenses',
            'infinity-license.json'
        );
        this.publicKeyPath = path.join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'keys',
            'infinity-public.pem'
        );
        
        // Local install data paths
        this.installIdPath = path.join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'identity',
            'install-id'
        );
        this.installSecretPath = path.join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'identity',
            'secret'
        );
    }
    
    /**
     * Load license from file
     */
    loadLicense() {
        try {
            if (!fs.existsSync(this.licensePath)) {
                return { valid: false, reason: 'file-not-found', error: 'License file not found' };
            }
            
            const content = fs.readFileSync(this.licensePath, 'utf8');
            const license = JSON.parse(content);
            
            const schemaCheck = validateSchema(license);
            if (!schemaCheck.valid) {
                return { 
                    valid: false, 
                    reason: 'invalid-schema', 
                    errors: schemaCheck.errors 
                };
            }
            
            return { valid: true, license };
        } catch (e) {
            return { valid: false, reason: 'load-error', error: e.message };
        }
    }
    
    /**
     * Load public key from file
     */
    loadPublicKey() {
        try {
            if (!fs.existsSync(this.publicKeyPath)) {
                return { valid: false, error: 'Public key file not found' };
            }
            
            const content = fs.readFileSync(this.publicKeyPath, 'utf8');
            
            if (!content.includes('-----BEGIN PUBLIC KEY-----')) {
                return { valid: false, error: 'Invalid public key format' };
            }
            
            return { valid: true, publicKey: content };
        } catch (e) {
            return { valid: false, error: e.message };
        }
    }
    
    /**
     * Verify RSA-SHA256 signature using canonical payload
     */
    verifySignature(license, publicKey) {
        try {
            const { algorithm, signature, publicKey: embeddedKey } = license.signature;
            
            if (algorithm !== 'RSA-SHA256') {
                return { valid: false, reason: 'unsupported-algorithm' };
            }
            
            const keyBuffer = crypto.createPublicKey(publicKey);
            const embeddedKeyBuffer = crypto.createPublicKey(embeddedKey);
            
            if (keyBuffer.export({ type: 'spki', format: 'der' }).toString('hex') !==
                embeddedKeyBuffer.export({ type: 'spki', format: 'der' }).toString('hex')) {
                return { valid: false, reason: 'public-key-mismatch' };
            }
            
            // Canonicalize payload for verification
            const canonicalPayload = canonicalizePayload(license);
            
            // Verify signature
            const verify = crypto.createVerify('RSA-SHA256');
            verify.update(payloadToBytes(canonicalPayload));
            
            try {
                verify.verify(embeddedKeyBuffer, Buffer.from(signature, 'base64'));
                return { valid: true };
            } catch (e) {
                return { valid: false, reason: 'signature-mismatch' };
            }
        } catch (e) {
            return { valid: false, reason: 'verify-error', error: e.message };
        }
    }
    
    /**
     * Check if license is expired
     */
    checkExpiration(license) {
        const expiresAt = new Date(license.license.expiresAt);
        const now = new Date();
        
        if (expiresAt < now) {
            return { valid: false, reason: 'expired', expiresAt };
        }
        
        return { valid: true, expiresAt };
    }
    
    /**
     * Check update entitlement
     */
    checkEntitlement(license) {
        const updateEligibleUntil = new Date(license.entitlements.updateEligibleUntil);
        const now = new Date();
        
        if (updateEligibleUntil < now) {
            return { 
                valid: true,
                reason: 'updates-expired',
                updateEligibleUntil,
                canUpdate: false
            };
        }
        
        return { 
            valid: true,
            canUpdate: true,
            updateEligibleUntil
        };
    }
    
    /**
     * Load local install data (installId and installSecret)
     */
    loadLocalInstallData() {
        try {
            const installId = fs.readFileSync(this.installIdPath, 'utf8').trim();
            const installSecret = fs.readFileSync(this.installSecretPath, 'utf8').trim();
            
            return {
                installId,
                installSecret,
                valid: true
            };
        } catch (e) {
            return {
                installId: null,
                installSecret: null,
                valid: false,
                error: e.message
            };
        }
    }
    
    /**
     * Validate hard-binding fields: installId + machineFingerprint
     */
    checkHardBinding(license, localData) {
        // Check installId
        if (localData.installId !== license.instance.installId) {
            return {
                valid: false,
                reason: 'install-id-mismatch',
                localInstallId: localData.installId,
                licenseInstallId: license.instance.installId
            };
        }
        
        // Check machineFingerprint
        const computedFingerprint = require('./schema').createMachineFingerprint(
            localData.installSecret,
            license.instance.hostname,
            license.instance.workspace,
            license.instance.openclawVersion,
            license.instance.installId
        );
        
        if (computedFingerprint !== license.instance.machineFingerprint) {
            return {
                valid: false,
                reason: 'machine-fingerprint-mismatch',
                computedFingerprint,
                licenseFingerprint: license.instance.machineFingerprint
            };
        }
        
        return { valid: true };
    }
    
    /**
     * Check advisory fields (workspace, hostname, openclawVersion)
     * These are logged but do NOT cause hard failure
     */
    checkAdvisoryFields(license) {
        const warnings = [];
        
        // Check workspace
        const currentWorkspace = process.env.OPENCLAW_WORKSPACE;
        if (currentWorkspace && currentWorkspace !== license.instance.workspace) {
            warnings.push({
                type: 'workspace-mismatch',
                local: currentWorkspace,
                license: license.instance.workspace
            });
        }
        
        // Check hostname
        const currentHostname = require('os').hostname();
        if (currentHostname !== license.instance.hostname) {
            warnings.push({
                type: 'hostname-mismatch',
                local: currentHostname,
                license: license.instance.hostname
            });
        }
        
        // Check openclawVersion
        const currentVersion = process.env.OPENCLAW_VERSION || 'unknown';
        if (currentVersion !== license.instance.openclawVersion) {
            warnings.push({
                type: 'version-mismatch',
                local: currentVersion,
                license: license.instance.openclawVersion
            });
        }
        
        return {
            valid: true,  // Advisory always passes
            warnings
        };
    }
    
    /**
     * Complete validation with new binding model
     */
    validate() {
        const result = {
            valid: true,
            checks: {},
            warnings: []
        };
        
        // Load license
        const loadResult = this.loadLicense();
        if (!loadResult.valid) {
            return {
                valid: false,
                reason: loadResult.reason,
                error: loadResult.error,
                checks: {},
                warnings: []
            };
        }
        result.license = loadResult.license;
        
        // Load public key
        const keyResult = this.loadPublicKey();
        if (!keyResult.valid) {
            return {
                valid: false,
                reason: 'public-key-error',
                error: keyResult.error,
                checks: {},
                warnings: []
            };
        }
        result.checks.publicKey = keyResult.publicKey;
        
        // Verify signature
        const sigResult = this.verifySignature(result.license, keyResult.publicKey);
        if (!sigResult.valid) {
            return {
                valid: false,
                reason: sigResult.reason,
                checks: result.checks,
                warnings: []
            };
        }
        result.checks.signature = { valid: true, algorithm: 'RSA-SHA256' };
        
        // Check expiration
        const expResult = this.checkExpiration(result.license);
        if (!expResult.valid) {
            return {
                valid: false,
                reason: expResult.reason,
                details: { expiresAt: expResult.expiresAt },
                checks: result.checks,
                warnings: []
            };
        }
        result.checks.expiration = { valid: true, expiresAt: expResult.expiresAt };
        
        // Check entitlement
        const entResult = this.checkEntitlement(result.license);
        result.checks.entitlement = {
            valid: true,
            canUpdate: entResult.canUpdate,
            updateEligibleUntil: entResult.updateEligibleUntil
        };
        
        // Load local install data
        const localData = this.loadLocalInstallData();
        if (!localData.valid) {
            return {
                valid: false,
                reason: 'local-install-data-error',
                error: localData.error,
                checks: result.checks,
                warnings: []
            };
        }
        
        // Check hard-binding (installId + machineFingerprint)
        const hardBindingResult = this.checkHardBinding(result.license, localData);
        if (!hardBindingResult.valid) {
            result.checks.hardBinding = {
                valid: false,
                reason: hardBindingResult.reason,
                details: hardBindingResult
            };
            
            return {
                valid: false,
                reason: hardBindingResult.reason,
                checks: result.checks,
                warnings: []
            };
        }
        result.checks.hardBinding = { valid: true };
        
        // Check advisory fields (warn but PASS)
        const advisoryResult = this.checkAdvisoryFields(result.license);
        result.checks.advisory = { valid: true };
        if (advisoryResult.warnings.length > 0) {
            result.warnings = advisoryResult.warnings;
        }
        
        return result;
    }
    
    getLicensePath() {
        return this.licensePath;
    }
    
    getPublicKeyPath() {
        return this.publicKeyPath;
    }
}

module.exports = {
    LicenseValidator
};
