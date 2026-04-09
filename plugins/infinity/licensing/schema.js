// schema.js - Infinity Productization Phase 1A — Licensing Core
// 
// Canonical signed payload, deterministic serialization, and signature verification.

const crypto = require('crypto');

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
 * Fields EXCLUDED from signing (signature envelope fields)
 */
const SIGNED_PAYLOAD_EXCLUDE = ['signature'];

/**
 * Canonicalize license payload - deterministic serialization
 * 
 * This function extracts only the payload fields to be signed,
 * excludes signature envelope fields, and produces stable byte output.
 */
function canonicalizePayload(license) {
    // Extract only payload fields (everything except signature)
    const payload = {
        meta: license.meta,
        license: license.license,
        instance: license.instance,
        entitlements: license.entitlements,
        audit: license.audit
    };
    
    // Sort keys recursively at all levels
    return sortKeysRecursively(payload);
}

/**
 * Sort object keys recursively (alphabetically)
 */
function sortKeysRecursively(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }
    
    if (Array.isArray(obj)) {
        return obj.map(item => sortKeysRecursively(item));
    }
    
    const sorted = {};
    const keys = Object.keys(obj).sort();
    
    for (const key of keys) {
        sorted[key] = sortKeysRecursively(obj[key]);
    }
    
    return sorted;
}

/**
 * Convert canonicalized payload to stable JSON bytes (UTF-8)
 * Minified JSON, no trailing newline
 */
function payloadToBytes(canonicalPayload) {
    return Buffer.from(JSON.stringify(canonicalPayload), 'utf8');
}

/**
 * Hash payload for signing/verification
 */
function hashPayload(canonicalPayload) {
    const bytes = payloadToBytes(canonicalPayload);
    return crypto.createHash('sha256').update(bytes).digest();
}

/**
 * Generate deterministic fingerprint for instance
 * Uses SHA256 of concatenated components
 */
function createFingerprint(hostname, workspace, installId, activationTimestamp) {
    const components = [
        'instance-',
        hashString(hostname),
        hashString(workspace),
        hashString(installId),
        hashString(activationTimestamp)
    ].join('');
    
    return hashString(components);
}

function hashString(str) {
    if (!str) {
        str = '';
    }
    return crypto.createHash('sha256').update(str).digest('hex');
}

/**
 * Verify license signature
 */
function verifySignature(license, publicKey) {
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
        
        // Canonicalize payload (excluding signature)
        const canonicalPayload = canonicalizePayload(license);
        
        // Sign with embedded public key (for verification)
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
 * Sign license payload
 * Returns just the signature string (not full license)
 */
function signPayload(payload, privateKey) {
    const canonicalPayload = canonicalizePayload(payload);
    const bytes = payloadToBytes(canonicalPayload);
    
    const sign = crypto.createSign('RSA-SHA256');
    sign.update(bytes);
    
    return sign.sign(privateKey, 'base64');
}

/**
 * Validate license schema
 */
function validate(license) {
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

/**
 * Create license template
 */
function createLicense(tier, workspace, hostname, openclawVersion, installId) {
    const fingerprint = createFingerprint(hostname, workspace, installId, new Date().toISOString());
    
    return {
        meta: {
            formatVersion: '1.0',
            type: 'infinity-license'
        },
        license: {
            id: generateId(),
            tier,
            issuedAt: new Date().toISOString(),
            expiresAt: calculateExpiry(),
            renewable: true,
            maxInstances: TIER_MAX_INSTANCES[tier],
            product: 'Website OC',
            region: 'production'
        },
        instance: {
            id: generateId(),
            workspace,
            hostname,
            openclawVersion,
            installedAt: new Date().toISOString(),
            lastActive: new Date().toISOString(),
            installId,
            fingerprint: fingerprint
        },
        signature: {
            algorithm: 'RSA-SHA256',
            publicKey: null,  // Will be set by caller
            signature: null  // Will be set by caller
        },
        entitlements: {
            updateEligibleUntil: calculateExpiry(),
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

function generateId() {
    return 'license-' + Math.random().toString(36).substring(2, 15);
}

function calculateExpiry() {
    const expiry = new Date();
    expiry.setFullYear(expiry.getFullYear() + 1);
    return expiry.toISOString();
}

module.exports = {
    LicenseTier,
    TIER_MAX_INSTANCES,
    SupportLevel,
    SIGNED_PAYLOAD_EXCLUDE,
    canonicalizePayload,
    sortKeysRecursively,
    payloadToBytes,
    hashPayload,
    createFingerprint,
    hashString,
    verifySignature,
    signPayload,
    validate,
    createLicense
};
