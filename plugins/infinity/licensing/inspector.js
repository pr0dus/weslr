/**
 * Infinity Productization Phase 1A — Licensing Core
 * 
 * License file inspection and instance detection.
 * Counts instances and detects active sessions.
 * No execution side-effects.
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { LicenseSigner } = require('./signer');

class LicenseInspector {
    constructor() {
        this.licenseDir = path.join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'licenses'
        );
        this.currentWorkspace = process.env.OPENCLAW_WORKSPACE;
        this.currentHostname = this.getHostname();
        this.openclawVersion = this.getOpenClawVersion();
    }
    
    /**
     * Get current hostname
     */
    getHostname() {
        try {
            return require('os').hostname();
        } catch (e) {
            return 'unknown';
        }
    }
    
    /**
     * Get OpenClaw version
     */
    getOpenClawVersion() {
        try {
            const openclawConfig = require('../config');
            return openclawConfig?.meta?.lastTouchedVersion || 'unknown';
        } catch (e) {
            return 'unknown';
        }
    }
    
    /**
     * Get install ID (from .openclaw/identity/)
     */
    getInstallId() {
        try {
            const identityDir = path.join(
                process.env.OPENCLAW_HOME || '.openclaw',
                'identity'
            );
            
            if (fs.existsSync(identityDir)) {
                const files = fs.readdirSync(identityDir);
                if (files.length > 0) {
                    // Read first file in identity directory
                    const content = fs.readFileSync(path.join(identityDir, files[0]), 'utf8');
                    return this.hashString(content);
                }
            }
            
            // Fallback: use hostname + timestamp
            return this.hashString(this.currentHostname + Date.now());
        } catch (e) {
            return this.hashString('default-' + this.currentHostname);
        }
    }
    
    /**
     * Count active instances
     * An instance is active if:
     * - License file exists and is valid
     * - Workspace exists
     * - lastActive is recent (within 24 hours)
     */
    countActiveInstances() {
        if (!fs.existsSync(this.licenseDir)) {
            return 0;
        }
        
        const files = fs.readdirSync(this.licenseDir);
        let count = 0;
        
        for (const file of files) {
            if (!file.endsWith('.json')) continue;
            
            try {
                const licensePath = path.join(this.licenseDir, file);
                const content = fs.readFileSync(licensePath, 'utf8');
                const license = JSON.parse(content);
                
                // Check if license is valid
                if (!license.license || !license.instance) continue;
                
                // Check workspace exists
                if (license.instance.workspace && 
                    !fs.existsSync(license.instance.workspace)) {
                    continue;
                }
                
                // Check lastActive is recent (within 24 hours)
                const lastActive = new Date(license.instance.lastActive);
                const now = new Date();
                const hoursSinceActive = (now - lastActive) / (1000 * 60 * 60);
                
                if (hoursSinceActive <= 24) {
                    count++;
                }
            } catch (e) {
                // Skip invalid files
                continue;
            }
        }
        
        return count;
    }
    
    /**
     * Detect current instance in license directory
     */
    detectCurrentInstance() {
        if (!fs.existsSync(this.licenseDir)) {
            return null;
        }
        
        const files = fs.readdirSync(this.licenseDir);
        
        for (const file of files) {
            if (!file.endsWith('.json')) continue;
            
            try {
                const licensePath = path.join(this.licenseDir, file);
                const content = fs.readFileSync(licensePath, 'utf8');
                const license = JSON.parse(content);
                
                // Check if workspace matches
                if (license.instance.workspace === this.currentWorkspace) {
                    // Check hostname matches
                    if (license.instance.hostname === this.currentHostname) {
                        return {
                            file,
                            license,
                            matches: {
                                workspace: true,
                                hostname: true
                            }
                        };
                    }
                }
            } catch (e) {
                continue;
            }
        }
        
        return null;
    }
    
    /**
     * Generate fingerprint for current instance
     */
    generateCurrentFingerprint(activationTimestamp) {
        const installId = this.getInstallId();
        return LicenseSigner.createFingerprint(
            this.currentHostname,
            this.currentWorkspace,
            installId,
            activationTimestamp
        );
    }
    
    /**
     * Check if current workspace has active license
     */
    hasActiveLicense() {
        const current = this.detectCurrentInstance();
        return current !== null;
    }
    
    /**
     * Get instance count
     */
    getInstanceCount() {
        return this.countActiveInstances();
    }
    
    /**
     * Hash string to SHA256
     */
    hashString(str) {
        return crypto.createHash('sha256').update(str).digest('hex');
    }
    
    /**
     * Get license directory
     */
    getLicenseDir() {
        return this.licenseDir;
    }
    
    /**
     * Get current workspace
     */
    getCurrentWorkspace() {
        return this.currentWorkspace;
    }
    
    /**
     * Get current hostname
     */
    getCurrentHostname() {
        return this.currentHostname;
    }
}

module.exports = {
    LicenseInspector
};
