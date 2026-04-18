/**
 * License Generator - Test License Creation
 * Generates a self-signed test license for Website OC
 * 
 * Note: For production, this would use server-side private key signing.
 * For testing, we use self-signed licenses (public key embedded in license).
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// ============================================================================
// CONFIGURATION
// ============================================================================

const LicenseTier = {
    ONE_OC: '1oc',
    THREE_OC: '3oc',
    SEVEN_OC: '7oc',
    UNLIMITED: 'unlimited'
};

const SupportLevel = {
    STANDARD: 'standard',
    PREMIUM: 'premium',
    ENTERPRISE: 'enterprise'
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function generateId() {
    return 'license-' + crypto.randomBytes(8).toString('hex');
}

function calculateExpiry() {
    const expiry = new Date();
    expiry.setFullYear(expiry.getFullYear() + 1); // 12 months
    return expiry.toISOString();
}

function hashString(str) {
    if (!str) {
        str = '';
    }
    return crypto.createHash('sha256').update(str).digest('hex');
}

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

// ============================================================================
// KEY GENERATION (FOR TESTING - SELF-SIGNED)
// ============================================================================

function generateKeys() {
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

function signLicense(license, privateKey) {
    // Create a copy without signature
    const licenseCopy = JSON.parse(JSON.stringify(license));
    licenseCopy.signature.signature = null;
    
    const sign = crypto.createSign('SHA256');
    sign.update(JSON.stringify(licenseCopy, null, 2));
    
    const signature = sign.sign(privateKey, 'base64');
    
    // Embed signature
    licenseCopy.signature.signature = signature;
    
    return licenseCopy;
}

// ============================================================================
// TEST LICENSE GENERATION
// ============================================================================

async function generateTestLicense() {
    console.log('Generating test license...\n');
    
    // Generate keys (self-signed for testing)
    const { publicKey, privateKey } = await generateKeys();
    console.log('Generated RSA key pair (2048-bit)');
    
    // Create license data
    const activationTimestamp = new Date().toISOString();
    const hostname = 'website-oc-host';
    const workspace = '/var/www/website-oc'; // Target: Website OC instance
    const installId = 'website-oc-install-001';
    const tier = LicenseTier.ONE_OC;
    
    const license = {
        meta: {
            formatVersion: '1.0',
            type: 'infinity-license'
        },
        license: {
            id: generateId(),
            tier: tier,
            issuedAt: new Date().toISOString(),
            expiresAt: calculateExpiry(),
            renewable: true,
            maxInstances: 1,
            product: 'Website OC',
            region: 'production',
        },
        instance: {
            id: generateId(),
            hostname: hostname,
            workspace: workspace,
            openclawVersion: '2026.3.13',
            installedAt: activationTimestamp,
            lastActive: new Date().toISOString(),
            installId: installId,
            fingerprint: createFingerprint(hostname, workspace, installId, activationTimestamp),
        },
        signature: {
            algorithm: 'RSA-SHA256',
            publicKey: publicKey,
            signature: null, // Will be filled after signing
        },
        entitlements: {
            updateEligibleUntil: calculateExpiry(),
            supportsRenewal: true,
            supportLevel: SupportLevel.PREMIUM,
        },
        audit: {
            createdBy: 'license-generator',
            createdAt: new Date().toISOString(),
            lastValidated: null,
        },
    };
    
    // Sign the license
    const signedLicense = signLicense(license, privateKey);
    
    // Save license to file
    const licensePath = path.join(
        process.env.OPENCLAW_HOME || '.openclaw',
        'licenses',
        'infinity-license.json'
    );
    
    const licenseDir = path.dirname(licensePath);
    if (!fs.existsSync(licenseDir)) {
        fs.mkdirSync(licenseDir, { recursive: true });
    }
    
    fs.writeFileSync(licensePath, JSON.stringify(signedLicense, null, 2));
    console.log(`\nLicense saved to: ${licensePath}`);
    
    // Save public key for verification
    const publicKeyPath = path.join(
        process.env.OPENCLAW_HOME || '.openclaw',
        'keys',
        'infinity-public.pem'
    );
    
    const keyDir = path.dirname(publicKeyPath);
    if (!fs.existsSync(keyDir)) {
        fs.mkdirSync(keyDir, { recursive: true });
    }
    
    fs.writeFileSync(publicKeyPath, publicKey, { mode: 0o644 });
    console.log(`Public key saved to: ${publicKeyPath}`);
    
    // Report license details
    console.log('\n--- LICENSE DETAILS ---');
    console.log(`License ID: ${signedLicense.license.id}`);
    console.log(`Tier: ${signedLicense.license.tier}`);
    console.log(`Product: ${signedLicense.license.product}`);
    console.log(`Region: ${signedLicense.license.region}`);
    console.log(`Max Instances: ${signedLicense.license.maxInstances}`);
    console.log(`Issued: ${signedLicense.license.issuedAt}`);
    console.log(`Expires: ${signedLicense.license.expiresAt}`);
    console.log(`Hostname: ${signedLicense.instance.hostname}`);
    console.log(`Workspace: ${signedLicense.instance.workspace}`);
    console.log(`OpenClaw Version: ${signedLicense.instance.openclawVersion}`);
    console.log(`Fingerprint: ${signedLicense.instance.fingerprint}`);
    console.log(`Support Level: ${signedLicense.entitlements.supportLevel}`);
    console.log(`Update Eligible Until: ${signedLicense.entitlements.updateEligibleUntil}`);
    
    console.log('\n--- SIGNATURE ---');
    console.log(`Algorithm: ${signedLicense.signature.algorithm}`);
    console.log(`Public Key: ${publicKey.substring(0, 50)}...`);
    console.log(`Signature: ${signedLicense.signature.signature.substring(0, 50)}...`);
    
    console.log('\n--- FILE PATHS ---');
    console.log(`License: ${licensePath}`);
    console.log(`Public Key: ${publicKeyPath}`);
    
    console.log('\nLicense generated successfully!');
}

// Run
generateTestLicense().catch(console.error);
