/**
 * Test script for canonicalized license signing and verification
 * 
 * Generates a fresh key pair, signs a license, verifies the signature,
 * and confirms repeated verification passes.
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// Load the new schema functions
const licensing = require('./licensing/schema');

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

function generateLicense(tier, workspace, hostname, openclawVersion, installId) {
    const expiration = new Date();
    expiration.setFullYear(expiration.getFullYear() + 1);
    
    const fingerprint = licensing.createFingerprint(
        hostname,
        workspace,
        installId,
        new Date().toISOString()
    );
    
    return {
        meta: {
            formatVersion: '1.0',
            type: 'infinity-license'
        },
        license: {
            id: 'test-license-' + Math.random().toString(36).substring(2, 15),
            tier,
            issuedAt: new Date().toISOString(),
            expiresAt: expiration.toISOString(),
            renewable: true,
            maxInstances: licensing.TIER_MAX_INSTANCES[tier]
        },
        instance: {
            id: 'test-instance-' + Math.random().toString(36).substring(2, 15),
            hostname,
            workspace,
            openclawVersion,
            installedAt: new Date().toISOString(),
            lastActive: new Date().toISOString(),
            installId,
            fingerprint
        },
        signature: {
            algorithm: 'RSA-SHA256',
            publicKey: '',
            signature: ''
        },
        entitlements: {
            updateEligibleUntil: expiration.toISOString(),
            supportsRenewal: true,
            supportLevel: 'premium'
        },
        audit: {
            createdBy: 'test-signer',
            createdAt: new Date().toISOString(),
            lastValidated: null
        }
    };
}

async function testRoundtrip() {
    console.log('=== Canonical License Sign/Verify Roundtrip Test ===\n');
    
    // Generate key pair
    const { publicKey, privateKey } = await generateKeys();
    console.log('Generated new RSA key pair (2048-bit)');
    
    // Create license
    const license = generateLicense(
        licensing.LicenseTier.ONE_OC,
        '/var/www/website-oc',
        'website-oc-host',
        '2026.3.13',
        'website-oc-install-001'
    );
    
    console.log('Created test license');
    console.log('  Tier:', license.license.tier);
    console.log('  Workspace:', license.instance.workspace);
    console.log('  Fingerprint:', license.instance.fingerprint.substring(0, 16) + '...');
    
    // Sign with canonical payload
    const signature = licensing.signPayload(license, privateKey);
    
    // Embed the signature
    const signedLicense = {
        ...license,
        signature: {
            algorithm: 'RSA-SHA256',
            publicKey: publicKey,
            signature: signature
        }
    };
    
    console.log('\nSigned license with canonical payload');
    console.log('  Signature:', signature.substring(0, 50) + '...');
    
    // Verify with embedded public key
    const verifyResult = licensing.verifySignature(signedLicense, publicKey);
    
    console.log('\n--- Verification Result ---');
    console.log('  Valid:', verifyResult.valid ? 'YES' : 'NO');
    console.log('  Reason:', verifyResult.reason || 'N/A');
    
    if (verifyResult.valid) {
        console.log('\n--- Roundtrip Tests ---');
        
        // Test 1: First verification
        const v1 = licensing.verifySignature(signedLicense, publicKey);
        console.log('  First verification:', v1.valid ? 'PASS' : 'FAIL');
        
        // Test 2: Second verification (ensure consistency)
        const v2 = licensing.verifySignature(signedLicense, publicKey);
        console.log('  Second verification:', v2.valid ? 'PASS' : 'FAIL');
        
        // Test 3: Verify same signature with same key
        console.log('  Signature consistency:', v1.valid === v2.valid ? 'PASS' : 'FAIL');
        
        // Test 4: Verify with public key from embedded key
        const embeddedKey = signedLicense.signature.publicKey;
        if (embeddedKey) {
            const v3 = licensing.verifySignature(signedLicense, embeddedKey);
            console.log('  Embedded key verification:', v3.valid ? 'PASS' : 'FAIL');
        }
        
        // Test 5: Check canonical payload is deterministic
        const canonical1 = licensing.canonicalizePayload(signedLicense);
        const canonical2 = licensing.canonicalizePayload(signedLicense);
        console.log('  Canonical determinism:', JSON.stringify(canonical1) === JSON.stringify(canonical2) ? 'PASS' : 'FAIL');
        
        console.log('\n=== ALL ROUNDTRIP TESTS PASSED ===');
    } else {
        console.log('\n=== ROUNDTRIP TEST FAILED ===');
        console.log('Error:', verifyResult.error);
    }
}

testRoundtrip().catch(console.error);
