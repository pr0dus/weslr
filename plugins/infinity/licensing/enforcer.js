/**
 * Infinity Productization Phase 1A — Licensing Core
 * 
 * Instance limit enforcement.
 * Enforces tier-based instance limits (1 OC, 3 OC, 7 OC, Unlimited).
 * No auto-approval, no auto-application.
 */

const fs = require('fs');
const path = require('path');
const { LicenseInspector } = require('./inspector');

class LicenseEnforcer {
    constructor() {
        this.inspector = new LicenseInspector();
    }
    
    /**
     * Check if current instance is within limit
     */
    checkCurrentInstance(license) {
        const currentCount = this.inspector.countActiveInstances();
        const maxInstances = license.license.maxInstances;
        
        // Unlimited tier (-1)
        if (maxInstances === -1) {
            return {
                valid: true,
                tier: 'unlimited',
                maxInstances,
                currentInstanceCount: currentCount
            };
        }
        
        // Tiered limits
        if (currentCount <= maxInstances) {
            return {
                valid: true,
                tier: license.license.tier,
                maxInstances,
                currentInstanceCount: currentCount
            };
        }
        
        return {
            valid: false,
            reason: 'instance-limit-exceeded',
            tier: license.license.tier,
            maxInstances,
            currentInstanceCount: currentCount
        };
    }
    
    /**
     * Get limit details for tier
     */
    getLimitDetails(tier) {
        const limits = {
            '1oc': { max: 1, description: 'Single instance' },
            '3oc': { max: 3, description: 'Up to 3 instances' },
            '7oc': { max: 7, description: 'Up to 7 instances' },
            'unlimited': { max: -1, description: 'Unlimited instances' }
        };
        
        return limits[tier] || limits['1oc'];
    }
    
    /**
     * Get all tiers with their limits
     */
    getAllTiers() {
        return {
            '1oc': { max: 1, description: 'Single instance' },
            '3oc': { max: 3, description: 'Up to 3 instances' },
            '7oc': { max: 7, description: 'Up to 7 instances' },
            'unlimited': { max: -1, description: 'Unlimited instances' }
        };
    }
    
    /**
     * Check all tiers for current instance count
     */
    checkAllTiers() {
        const currentCount = this.inspector.countActiveInstances();
        const tiers = this.getAllTiers();
        
        const results = {};
        for (const [tier, limit] of Object.entries(tiers)) {
            results[tier] = {
                valid: currentCount <= limit.max || limit.max === -1,
                currentCount,
                maxInstances: limit.max
            };
        }
        
        return results;
    }
    
    /**
     * Check if upgrade needed (current tier exceeded)
     */
    checkUpgradeNeeded(license) {
        const currentCount = this.inspector.countActiveInstances();
        const currentMax = license.license.maxInstances;
        
        if (currentMax === -1) {
            return { upgradeNeeded: false, reason: 'unlimited' };
        }
        
        if (currentCount > currentMax) {
            const nextTiers = this.getHigherTiers(license.license.tier);
            
            if (nextTiers.length > 0) {
                const neededMax = nextTiers[0].max;
                if (currentCount <= neededMax) {
                    return {
                        upgradeNeeded: true,
                        currentMax,
                        neededMax,
                        recommendedTier: nextTiers[0].tier
                    };
                }
            }
            
            return {
                upgradeNeeded: true,
                reason: 'exceeds-all-tiers',
                currentMax,
                currentCount
            };
        }
        
        return { upgradeNeeded: false, reason: 'within-limit' };
    }
    
    /**
     * Get higher tiers
     */
    getHigherTiers(currentTier) {
        const tiers = Object.entries(this.getAllTiers());
        const currentIdx = tiers.findIndex(([tier]) => tier === currentTier);
        
        if (currentIdx === -1 || currentIdx === tiers.length - 1) {
            return [];
        }
        
        return tiers.slice(currentIdx + 1).map(([tier, limit]) => ({
            tier,
            max: limit.max,
            description: limit.description
        }));
    }
    
    /**
     * Get license path
     */
    getLicensePath() {
        return path.join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'licenses',
            'infinity-license.json'
        );
    }
    
    /**
     * Get license directory
     */
    getLicenseDir() {
        return path.join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'licenses'
        );
    }
    
    /**
     * Get instance directory
     */
    getInstanceDir() {
        return path.join(
            process.env.OPENCLAW_HOME || '.openclaw',
            'instances'
        );
    }
    
    /**
     * Check workspace exists
     */
    workspaceExists(workspace) {
        return fs.existsSync(workspace);
    }
    
    /**
     * Get instance count (public API)
     */
    getInstanceCount() {
        return this.inspector.countActiveInstances();
    }
    
    /**
     * Get instance info
     */
    getInstanceInfo() {
        return {
            workspace: this.inspector.getCurrentWorkspace(),
            hostname: this.inspector.getCurrentHostname()
        };
    }
}

module.exports = {
    LicenseEnforcer
};
