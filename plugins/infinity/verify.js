const crypto = require('crypto');
const fs = require('fs');

// Read the signed license
const license = JSON.parse(fs.readFileSync('/data/data/com.termux/files/home/.openclaw/licenses/infinity-license.json', 'utf8'));

// For signature verification, we need to reconstruct the signed payload
// The signed payload is everything EXCEPT the signature.publicKey field

console.log('Verifying signature...');

// Create a copy that matches what was signed:
// - Keep all fields
// - Set signature.publicKey to empty string (as it was during signing)
const toVerify = JSON.parse(JSON.stringify(license));
toVerify.signature.publicKey = '';

console.log('Hash input (with empty publicKey):', JSON.stringify(toVerify, null, 2).substring(0, 200) + '...');

const verify = crypto.createVerify('RSA-SHA256');
verify.update(JSON.stringify(toVerify, null, 2));

const isVerified = verify.verify(license.signature.publicKey, Buffer.from(license.signature.signature, 'base64'));

console.log('Signature verified:', isVerified ? 'YES' : 'NO');

if (!isVerified) {
    console.log('\nDebug:');
    console.log('Public key (embedded):', license.signature.publicKey.substring(0, 60));
    console.log('Signature:', license.signature.signature.substring(0, 50));
    
    // Also try with empty public key for verification
    console.log('\nTrying with empty public key...');
    try {
        const verify2 = crypto.createVerify('RSA-SHA256');
        verify2.update(JSON.stringify(toVerify, null, 2));
        console.log('Verification result with empty key:', verify2.verify('', Buffer.from(license.signature.signature, 'base64')));
    } catch (e) {
        console.log('Error with empty key:', e.message);
    }
}
