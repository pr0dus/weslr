// validator.js - Infinity Productization Phase 1A — Licensing Core
// 
// License validation logic.
// Verifies signature, expiration, instance limit, entitlements.
// Uses canonical payload (excluding signature) for verification.
// No private key on customer machine - only public key verification.

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
            
            // Verify it's a valid PEM format
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
            
            // Verify public key matches embedded key
            const keyBuffer = crypto.createPublicKey(publicKey);
            const embeddedKeyBuffer = crypto.createPublicKey(embeddedKey);
            
            if (keyBuffer.export({ type: 'spki', format: 'der' }).toString('hex') !==
                embeddedKeyBuffer.export({ type: 'spki', format: 'der' }).toString('hex')) {
                return { valid: false, reason: 'public-key-mismatch' };
            }
            
            // Canonicalize payload for verification (excluding signature fields)
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
                valid: true,  // License still valid
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
     * Check if instance is valid (workspace matches)
     */
    checkInstanceMatch(license) {
        const currentWorkspace = process.env.OPENCLAW_WORKSPACE;
        const licenseWorkspace = license.instance.workspace;
        
        if (!currentWorkspace || currentWorkspace !== licenseWorkspace) {
            return { valid: false, reason: 'workspace-mismatch' };
        }
        
        return { valid: true, workspace: licenseWorkspace };
    }
    
    /**
     * Check instance limit (done by enforcer)
     */
    checkInstanceLimit(license, currentInstanceCount) {
        const maxInstances = license.license.maxInstances;
        
        if (maxInstances === -1) {
            return { valid: true, reason: 'unlimited' };
        }
        
        if (currentInstanceCount > maxInstances) {
            return { 
                valid: false, 
                reason: 'instance-limit-exceeded',
                currentInstanceCount,
                maxInstances
            };
        }
        
        return { valid: true, currentInstanceCount, maxInstances };
    }
    
    /**
     * Complete validation
     */
    validate() {
        const result = {
            valid: true,
            checks: {}
        };
        
        // Load license
        const loadResult = this.loadLicense();
        if (!loadResult.valid) {
            return {
                valid: false,
                reason: loadResult.reason,
                error: loadResult.error,
                checks: {}
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
                checks: {}
            };
        }
        result.checks.publicKey = keyResult.publicKey;
        
        // Verify signature
        const sigResult = this.verifySignature(result.license, keyResult.publicKey);
        if (!sigResult.valid) {
            return {
                valid: false,
                reason: sigResult.reason,
                checks: result.checks
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
                checks: result.checks
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
        
        // Check workspace match
        const instResult = this.checkInstanceMatch(result.license);
        if (!instResult.valid) {
            return {
                valid: false,
                reason: instResult.reason,
                checks: result.checks
            };
        }
        result.checks.instance = { valid: true, workspace: instResult.workspace };
        
        // Instance limit check is done by enforcer
        
        return result;
    }
    
    /**
     * Get license path
     */
    getLicensePath() {
        return this.licensePath;
    }
    
    /**
     * Get public key path
     */
    getPublicKeyPath() {
        return this.publicKeyPath;
    }
}

module.exports = {
    LicenseValidator
};
