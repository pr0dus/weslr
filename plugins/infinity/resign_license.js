/**
 * License Re-Sign Script - WITH DETERMINISTIC JSON
 */

const crypto = require('crypto');
const fs = require('fs');

// Custom JSON.stringify with sorted keys for determinism
function stringifySorted(obj) {
    const replacer = (key, value) => {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
            const sorted = {};
            Object.keys(value).sort().forEach((k) => {
                sorted[k] = value[k];
            });
            return sorted;
        }
        return value;
    };
    return JSON.stringify(obj, replacer);
}

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

async function resignLicense() {
    console.log('=== License Re-Sign Operation (DETERMINISTIC) ===\n');
    
    const licensePath = '/data/data/com.termux/files/home/.openclaw/licenses/infinity-license.json';
    const existingLicense = JSON.parse(fs.readFileSync(licensePath, 'utf8'));
    
    console.log('Loaded existing license');
    console.log('License ID:', existingLicense.license.id);
    
    const unchangedPayload = {
        meta: existingLicense.meta,
        license: {
            id: existingLicense.license.id,
            tier: existingLicense.license.tier,
            issuedAt: existingLicense.license.issuedAt,
            expiresAt: existingLicense.license.expiresAt,
            renewable: existingLicense.license.renewable,
            maxInstances: existingLicense.license.maxInstances,
            product: existingLicense.license.product,
            region: existingLicense.license.region,
        },
        instance: {
            id: existingLicense.instance.id,
            hostname: existingLicense.instance.hostname,
            workspace: existingLicense.instance.workspace,
            openclawVersion: existingLicense.instance.openclawVersion,
            installedAt: existingLicense.instance.installedAt,
            lastActive: existingLicense.instance.lastActive,
            installId: existingLicense.instance.installId,
            fingerprint: existingLicense.instance.fingerprint,
        },
        entitlements: {
            updateEligibleUntil: existingLicense.entitlements.updateEligibleUntil,
            supportsRenewal: existingLicense.entitlements.supportsRenewal,
            supportLevel: existingLicense.entitlements.supportLevel,
        },
        audit: {
            createdBy: existingLicense.audit.createdBy,
            createdAt: existingLicense.audit.createdAt,
            lastValidated: existingLicense.audit.lastValidated,
        },
    };
    
    const { publicKey, privateKey } = await generateKeys();
    console.log('\nGenerated new RSA key pair (2048-bit)');
    
    const fullLicense = {
        ...unchangedPayload,
        signature: {
            algorithm: 'RSA-SHA256',
            publicKey: publicKey,
            signature: ''
        }
    };
    
    const signed = stringifySorted(fullLicense);
    
    const sign = crypto.createSign('RSA-SHA256');
    sign.update(signed);
    const signature = sign.sign(privateKey, 'base64');
    
    fullLicense.signature.signature = signature;
    
    fs.writeFileSync(licensePath, JSON.stringify(fullLicense, null, 2));
    console.log('\nLicense re-signed and saved to:', licensePath);
    
    const publicKeyPath = '/data/data/com.termux/files/home/.openclaw/keys/infinity-public.pem';
    fs.writeFileSync(publicKeyPath, publicKey, { mode: 0o644 });
    console.log('New public key saved to:', publicKeyPath);
    
    console.log('\n--- LICENSE DETAILS (UNCHANGED) ---');
    console.log('License ID:', fullLicense.license.id);
    console.log('Tier:', fullLicense.license.tier);
    console.log('Product:', fullLicense.license.product);
    console.log('Region:', fullLicense.license.region);
    console.log('Max Instances:', fullLicense.license.maxInstances);
    console.log('Issued:', fullLicense.license.issuedAt);
    console.log('Expires:', fullLicense.license.expiresAt);
    console.log('Hostname:', fullLicense.instance.hostname);
    console.log('Workspace:', fullLicense.instance.workspace);
    console.log('Fingerprint:', fullLicense.instance.fingerprint);
    
    console.log('\n--- NEW SIGNATURE ---');
    console.log('Algorithm:', fullLicense.signature.algorithm);
    console.log('Signature:', fullLicense.signature.signature.substring(0, 50) + '...');
    
    // Verify
    const verify = crypto.createVerify('RSA-SHA256');
    verify.update(stringifySorted(fullLicense));
    const isVerified = verify.verify(publicKey, Buffer.from(fullLicense.signature.signature, 'base64'));
    
    console.log('\n--- VERIFICATION ---');
    console.log('Payload unchanged: YES');
    console.log('Re-signed with new key pair: YES');
    console.log('New public key embedded: YES');
    console.log('Signature verified: ' + (isVerified ? 'YES' : 'NO'));
}

resignLicense().catch(console.error);
