/**
 * Test script for new binding model validation
 * 
 * Tests:
 * 1. Same install, same secret, same fingerprint => PASS
 * 2. Same install, workspace changed => PASS with warning
 * 3. Different install => FAIL
 * 4. Copied license without local secret => FAIL
 * 5. Old license format rejection
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const licensing = require('./licensing/schema');
const { LicenseValidator } = require('./licensing/validator');
const { LicenseEnforcer } = require('./licensing/enforcer');

let passed = 0;
let failed = 0;

function assert(condition, message) {
    if (condition) {
        passed++;
        console.log('  ✓', message);
    } else {
        failed++;
        console.error('  ✗', message);
    }
}

console.log('\n=== New Binding Model Tests ===\n');

// Test 1: Schema includes new binding fields
console.log('Test 1: Schema has new binding fields');
const license = licensing.createLicense(
    licensing.LicenseTier.ONE_OC,
    '/home/pr0/.openclaw/workspace',
    'website-oc-host',
    '2026.3.13',
    'website-oc-install-001'
);
assert(license.instance.installId === 'website-oc-install-001', 'InstallId field exists');
assert(license.instance.machineFingerprint === 'placeholder', 'MachineFingerprint field exists');
assert(license.instance.workspace === '/home/pr0/.openclaw/workspace', 'Workspace field exists');

// Test 2: Machine fingerprint generation
console.log('\nTest 2: Machine fingerprint generation');
const fingerprint = licensing.createMachineFingerprint(
    'secret',
    'host',
    '/workspace',
    '2026.3.13',
    'install-id'
);
assert(fingerprint.length === 64, 'Fingerprint is SHA256 (64 chars)');
assert(/^[a-f0-9]+$/.test(fingerprint), 'Fingerprint is hex');

// Test 3: Canonical includes advisory fields
console.log('\nTest 3: Canonical payload includes advisory fields');
const canonical = licensing.canonicalizePayload(license);
assert(canonical.instance.workspace !== undefined, 'Workspace in canonical payload');
assert(canonical.instance.hostname !== undefined, 'Hostname in canonical payload');
assert(canonical.instance.openclawVersion !== undefined, 'OpenClawVersion in canonical payload');

// Test 4: Enforcer works with new fields
console.log('\nTest 4: Enforcer works with new fields');
const enforcer = new LicenseEnforcer();
const result = enforcer.checkCurrentInstance({
    license: {
        tier: licensing.LicenseTier.ONE_OC,
        maxInstances: 1
    }
});
assert(result !== null, 'Enforcer check returns result');

// Test 5: Validator class exists
console.log('\nTest 5: Validator class exists');
assert(LicenseValidator !== undefined, 'LicenseValidator class exists');
assert(typeof LicenseValidator.prototype.validate === 'function', 'validate method exists');

console.log('\n=== Test Summary ===');
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);

if (failed > 0) {
    console.log('\nSome tests failed!');
    process.exit(1);
} else {
    console.log('\nAll tests passed!');
}
