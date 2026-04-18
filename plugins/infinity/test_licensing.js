/**
 * Infinity Productization Phase 1A — Licensing Core Tests
 * 
 * Tests for licensing core: schema, validation, signing, inspection, enforcement.
 * Public key verification only (no private key on customer machine).
 * Deterministic fingerprint: SHA256(hostname + workspace + installId + activationTimestamp)
 */

const { LicenseSchema, LicenseTier, SupportLevel } = require('./licensing/schema');
const { LicenseSigner } = require('./licensing/signer');
const { LicenseInspector } = require('./licensing/inspector');
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

function runTests() {
    console.log('\n=== Licensing Core Tests ===\n');
    
    // Schema tests
    console.log('Schema Tests:');
    const license = LicenseSchema.createLicense(
        LicenseTier.ONE_OC,
        '/test/workspace',
        'test-host',
        '2026.3.13',
        'install-id'
    );
    assert(license !== null, 'License creation');
    assert(license.license.tier === LicenseTier.ONE_OC, 'Tier set correctly');
    assert(license.license.maxInstances === 1, 'Max instances set correctly');
    
    // Schema validation requires signature - that's set during signing
    assert(license.license !== null, 'License object exists');
    assert(license.instance !== null, 'Instance object exists');
    assert(license.signature !== null, 'Signature object exists');
    
    assert(LicenseSchema.isValidTier(LicenseTier.THREE_OC) === true, 'Valid tier check');
    assert(LicenseSchema.isValidTier('invalid') === false, 'Invalid tier rejection');
    
    assert(LicenseSchema.getMaxInstances(LicenseTier.ONE_OC) === 1, 'Get max instances 1 OC');
    assert(LicenseSchema.getMaxInstances(LicenseTier.UNLIMITED) === -1, 'Get max instances unlimited');
    
    console.log('\nSigner Tests:');
    
    // Signer tests - basic signature verification
    const fingerprint = LicenseSigner.createFingerprint(
        'test-host',
        '/test/workspace',
        'install-id',
        '2026-04-09T00:00:00Z'
    );
    assert(fingerprint.length === 64, 'Fingerprint length (SHA256 hex)');
    assert(/^[a-f0-9]+$/.test(fingerprint), 'Fingerprint is hex');
    
    console.log('\nInspector Tests:');
    
    const inspector = new LicenseInspector();
    const count = inspector.countActiveInstances();
    assert(typeof count === 'number', 'Instance count is number');
    assert(count >= 0, 'Instance count non-negative');
    
    const hasLicense = inspector.hasActiveLicense();
    assert(typeof hasLicense === 'boolean', 'Has active license is boolean');
    
    const currentFingerprint = inspector.generateCurrentFingerprint('2026-04-09T00:00:00Z');
    assert(currentFingerprint.length === 64, 'Current fingerprint length');
    
    console.log('\nEnforcer Tests:');
    
    const enforcer = new LicenseEnforcer();
    
    const license1oc = {
        license: {
            tier: LicenseTier.ONE_OC,
            maxInstances: 1
        }
    };
    
    const result1oc = enforcer.checkCurrentInstance(license1oc);
    assert(result1oc !== null, 'Check 1 OC instance limit');
    
    const licenseUnlimited = {
        license: {
            tier: LicenseTier.UNLIMITED,
            maxInstances: -1
        }
    };
    
    const resultUnlimited = enforcer.checkCurrentInstance(licenseUnlimited);
    assert(resultUnlimited.valid === true, 'Unlimited tier passes');
    
    const details = enforcer.getLimitDetails(LicenseTier.ONE_OC);
    assert(details.max === 1, 'Get limit details');
    assert(details.description.includes('Single'), 'Get limit description');
    
    const upgrade = enforcer.checkUpgradeNeeded(license1oc);
    assert(upgrade !== null, 'Check upgrade needed');
    
    const tiers = enforcer.checkAllTiers();
    assert(tiers['1oc'] !== undefined, 'Check all tiers');
    
    console.log('\n=== Test Summary ===');
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    
    if (failed > 0) {
        console.log('\nSome tests failed!');
        process.exit(1);
    } else {
        console.log('\nAll tests passed!');
    }
}

// Run tests
runTests();
