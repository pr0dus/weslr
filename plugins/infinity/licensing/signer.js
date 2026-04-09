// signer.js - Infinity Productization Phase 1A — Licensing Core
// 
// License signing with deterministic payload canonicalization.
// Public key embedded in signature after signing.
// No private key on customer machine.

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { 
    canonicalizePayload, 
    payloadToBytes, 
    signPayload as canonicalSign,
    createFingerprint 
} = require('./schema');

class LicenseSigner {
    constructor() {
        this.publicKeyPath = path.join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'keys',
            'infinity-public.pem'
        );
    }
    
    /**
     * Generate RSA key pair (server-side only)
     * PRIVATE KEY IS NEVER SHIPPED TO CUSTOMER
     */
    static generateKeyPair() {
        return new Promise((resolve, reject) => {
            crypto.generateKeyPair('rsa', {
                modulusLength: 2048,
                publicKeyEncoding: { type: 'spki', format: 'pem' },
                privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
            }, (err, publicKey, privateKey) => {
                if (err) {
                    reject(err);
                } else {
                    resolve({ publicKey, privateKey });
                }
            });
        });
    }
    
    /**
     * Sign license with deterministic payload canonicalization
     * The signature covers ONLY the payload (meta, license, instance, entitlements, audit)
     * The public key is embedded AFTER signing.
     */
    sign(license, privateKey) {
        // Store original public key if present
        const originalPublicKey = license.signature?.publicKey || '';
        
        // Sign with canonical payload
        const signature = canonicalSign(license, privateKey);
        
        // Embed the NEW public key and signature
        return {
            ...license,
            signature: {
                algorithm: 'RSA-SHA256',
                publicKey: originalPublicKey,  // Keep original public key for verification
                signature: signature
            }
        };
    }
    
    /**
     * Sign with embedded public key
     * This is used when generating a fresh license with a new key pair
     */
    signWithEmbeddedKey(license, privateKey, publicKey) {
        // Store the public key before signing
        const embeddedKey = license.signature?.publicKey || '';
        
        // Sign with canonical payload
        const signature = canonicalSign(license, privateKey);
        
        // Embed the public key and signature
        return {
            ...license,
            signature: {
                algorithm: 'RSA-SHA256',
                publicKey: embeddedKey || publicKey,
                signature: signature
            }
        };
    }
    
    /**
     * Verify license signature
     * Uses canonical payload (excluding signature fields)
     */
    verify(license) {
        try {
            const { algorithm, signature, publicKey: embeddedKey } = license.signature;
            
            if (algorithm !== 'RSA-SHA256') {
                return { valid: false, reason: 'unsupported-algorithm' };
            }
            
            // Verify signature with embedded public key
            const verify = crypto.createVerify('RSA-SHA256');
            
            // Canonicalize payload for verification
            const canonicalPayload = canonicalizePayload(license);
            verify.update(payloadToBytes(canonicalPayload));
            
            try {
                verify.verify(embeddedKey, Buffer.from(signature, 'base64'));
                return { valid: true };
            } catch (e) {
                return { valid: false, reason: 'signature-mismatch' };
            }
        } catch (e) {
            return { valid: false, reason: 'verify-error', error: e.message };
        }
    }
    
    /**
     * Create fingerprint from instance data
     * Deterministic: SHA256(hostname + workspace + installId + activationTimestamp)
     */
    static createFingerprint(hostname, workspace, installId, activationTimestamp) {
        return createFingerprint(hostname, workspace, installId, activationTimestamp);
    }
    
    /**
     * Store public key to file
     * Called during build/install (server-side only)
     */
    static storePublicKey(publicKey, publicKeyPath) {
        const dir = path.dirname(publicKeyPath);
        
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        
        fs.writeFileSync(publicKeyPath, publicKey, { mode: 0o644 });
    }
    
    /**
     * Get license path
     */
    static getLicensePath() {
        return path.join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'licenses',
            'infinity-license.json'
        );
    }
    
    /**
     * Get public key path
     */
    static getPublicKeyPath() {
        return path.join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'keys',
            'infinity-public.pem'
        );
    }
    
    /**
     * Check if public key exists
     */
    static hasPublicKey() {
        return fs.existsSync(this.getPublicKeyPath());
    }
}

module.exports = {
    LicenseSigner
};
