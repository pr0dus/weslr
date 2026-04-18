// profiles/website_oc_production.js - Infinity Standard License Profile
// 
// Standard profile for Website OC production license generation.
// 
// Binding model:
// - Hard-binding: installId, machineFingerprint
// - Advisory: workspace, hostname, openclawVersion

const Profile = {
    name: 'website_oc_production',
    description: 'Infinity production license for Website OC (single instance, standard support)',
    meta: {
        formatVersion: '1.0',
        type: 'infinity-license'
    },
    license: {
        tier: '1oc',
        renewable: true,
        maxInstances: 1,
        product: 'Website OC',
        region: 'production'
    },
    instance: {
        // Runtime fields injected at generation:
        // hostname, workspace, openclawVersion, installId, installedAt, lastActive, id
        openclawVersion: '2026.3.13'
    },
    entitlements: {
        updateEligibleUntil: '1y_from_issued',
        supportsRenewal: true,
        supportLevel: 'standard'
    },
    audit: {
        createdBy: 'license-server',
        lastValidated: null
    }
};

module.exports = {
    Profile
};
