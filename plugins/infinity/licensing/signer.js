/**
 * Infinity Productization Phase 1A — Licensing Core
 * 
 * License signing and verification.
 * Server-side signing (private key), client-side verification (public key only).
 * No private key on customer machine.
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

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
     * Load existing public key from file
     */
    loadPublicKey() {
        try {
            if (!fs.existsSync(this.publicKeyPath)) {
                return null;
            }
            
            const content = fs.readFileSync(this.publicKeyPath, 'utf8');
            return content;
        } catch (e) {
            return null;
        }
    }
    
    /**
     * Sign license payload
     * This is done server-side only
     * Customer machines only verify, never sign
     */
    sign(license, privateKey) {
        try {
            // Remove existing signature if present
            const licenseCopy = JSON.parse(JSON.stringify(license));
            licenseCopy.signature.signature = null;
            
            // Create signature
            const sign = crypto.createSign('SHA256');
            sign.update(JSON.stringify(licenseCopy, null, 2));
            
            const signature = sign.sign(privateKey, 'base64');
            
            // Embed signature
            licenseCopy.signature.signature = signature;
            
            return licenseCopy;
        } catch (e) {
            throw new Error(`Sign error: ${e.message}`);
        }
    }
    
    /**
     * Verify license signature
     * This is done on customer machine (public key only)
     */
    verify(license) {
        try {
            const { algorithm, signature, publicKey: embeddedKey } = license.signature;
            
            if (algorithm !== 'RSA-SHA256') {
                return { valid: false, reason: 'unsupported-algorithm' };
            }
            
            // Verify signature with embedded public key
            const verify = crypto.createVerify('SHA256');
            verify.update(JSON.stringify(license, null, 2));
            
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
        const components = [
            'instance-',
            this.hashString(hostname),
            this.hashString(workspace),
            this.hashString(installId),
            this.hashString(activationTimestamp)
        ].join('');
        
        return this.hashString(components);
    }
    
    /**
     * Hash string to SHA256
     */
    static hashString(str) {
        if (!str) {
            str = '';
        }
        return crypto.createHash('sha256').update(str).digest('hex');
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
