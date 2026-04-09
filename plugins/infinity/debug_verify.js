const crypto = require('crypto');
const fs = require('fs');

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

const license = JSON.parse(fs.readFileSync('/data/data/com.termux/files/home/.openclaw/licenses/infinity-license.json', 'utf8'));

console.log('Debug verification:');
console.log('Public key:', license.signature.publicKey.substring(0, 80));
console.log('\nSignature:', license.signature.signature);

// Try verification
const verify = crypto.createVerify('RSA-SHA256');
verify.update(stringifySorted(license));
const isVerified = verify.verify(license.signature.publicKey, Buffer.from(license.signature.signature, 'base64'));

console.log('\nVerification result:', isVerified ? 'YES' : 'NO');

// Debug - check hash
const sign = crypto.createSign('RSA-SHA256');
sign.update(stringifySorted(license));
const testSig = sign.sign(license.signature.publicKey, 'base64');
console.log('Test signature:', testSig.substring(0, 50));
