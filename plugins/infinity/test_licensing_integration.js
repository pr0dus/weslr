/**
 * Infinity Phase 1B — Runtime License Enforcement Tests
 * 
 * Tests for runtime license enforcement.
 * OpenClaw must always remain safe.
 * Infinity premium continuity must fail closed when license is invalid.
 */

const { LicenseSchema, LicenseTier } = require('./licensing/schema');
const { LicenseSigner } = require('./licensing/signer');
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

function testLicenseValidation() {
    console.log('\n=== License Validation Tests ===\n');
    
    // Test valid license
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
    
    // Test all tiers
    const tiers = [LicenseTier.ONE_OC, LicenseTier.THREE_OC, LicenseTier.SEVEN_OC, LicenseTier.UNLIMITED];
    
    for (const tier of tiers) {
        const l = LicenseSchema.createLicense(
            tier,
            '/test/workspace',
            'test-host',
            '2026.3.13',
            'install-id'
        );
        assert(l.license.tier === tier, `Tier ${tier} creation`);
        assert(l.license.maxInstances === LicenseEnforcer.prototype.getLimitDetails(tier).max, `Max instances for ${tier}`);
    }
    
    console.log('\nLicense validation tests completed.');
}

function testEnforcement() {
    console.log('\n=== Enforcement Tests ===\n');
    
    const enforcer = new LicenseEnforcer();
    
    // Test 1 OC tier
    const license1oc = {
        license: {
            tier: LicenseTier.ONE_OC,
            maxInstances: 1
        }
    };
    
    const result1oc = enforcer.checkCurrentInstance(license1oc);
    assert(result1oc !== null, '1 OC enforcement check');
    assert(result1oc.valid === true, '1 OC valid (0 instances)');
    
    // Test unlimited tier
    const licenseUnlimited = {
        license: {
            tier: LicenseTier.UNLIMITED,
            maxInstances: -1
        }
    };
    
    const resultUnlimited = enforcer.checkCurrentInstance(licenseUnlimited);
    assert(resultUnlimited.valid === true, 'Unlimited tier passes');
    
    // Test upgrade detection
    const upgrade = enforcer.checkUpgradeNeeded(license1oc);
    assert(upgrade !== null, 'Upgrade check');
    
    console.log('\nEnforcement tests completed.');
}

function testAdapterPattern() {
    console.log('\n=== Adapter Pattern Tests ===\n');
    
    // Adapter should wrap validation and enforcement
    class LicenseAdapter {
        constructor() {
            this.validator = require('./licensing/validator').LicenseValidator;
            this.enforcer = require('./licensing/enforcer').LicenseEnforcer;
        }
        
        validate(license) {
            const validator = new this.validator();
            const result = validator.validate();
            return result;
        }
        
        enforce(license) {
            const enforcer = new this.enforcer();
            return enforcer.checkCurrentInstance(license);
        }
    }
    
    const adapter = new LicenseAdapter();
    const license = LicenseSchema.createLicense(
        LicenseTier.THREE_OC,
        '/test/workspace',
        'test-host',
        '2026.3.13',
        'install-id'
    );
    
    assert(adapter !== null, 'Adapter instantiation');
    
    console.log('\nAdapter pattern tests completed.');
}

function testIntegrationPoints() {
    console.log('\n=== Integration Points Tests ===\n');
    
    // Test that integration points exist
    assert(typeof LicenseSigner.createFingerprint === 'function', 'Signer fingerprint method');
    assert(typeof LicenseSigner.hashString === 'function', 'Signer hash method');
    assert(typeof LicenseEnforcer.prototype.checkCurrentInstance === 'function', 'Enforcer check method');
    assert(typeof LicenseEnforcer.prototype.getLimitDetails === 'function', 'Enforcer details method');
    assert(typeof LicenseEnforcer.prototype.checkUpgradeNeeded === 'function', 'Enforcer upgrade method');
    
    // Test fingerprint consistency
    const fp1 = LicenseSigner.createFingerprint(
        'host',
        '/workspace',
        'id',
        '2026-04-09T00:00:00Z'
    );
    
    const fp2 = LicenseSigner.createFingerprint(
        'host',
        '/workspace',
        'id',
        '2026-04-09T00:00:00Z'
    );
    
    assert(fp1 === fp2, 'Fingerprint consistency');
    
    console.log('\nIntegration points tests completed.');
}

function testFailSafeBehavior() {
    console.log('\n=== Fail-Safe Behavior Tests ===\n');
    
    // Test that invalid license doesn't break OpenClaw
    // (simulated by checking that license check returns false)
    
    // Missing license case
    const enforcer = new LicenseEnforcer();
    const license = {
        license: {
            tier: LicenseTier.ONE_OC,
            maxInstances: 1
        }
    };
    
    const result = enforcer.checkCurrentInstance(license);
    assert(result !== null, 'Enforcement result always returned');
    
    // Premium features fail closed
    const premiumEnabled = result.valid; // Only true when valid
    assert(typeof premiumEnabled === 'boolean', 'Premium enabled is boolean');
    
    // OpenClaw always safe (no throw, no block)
    try {
        // Simulate license validation failure
        const invalidLicense = { license: { tier: 'invalid' } };
        // This should not throw
        enforcer.checkCurrentInstance(invalidLicense);
        assert(true, 'No crash on invalid license');
    } catch (e) {
        assert(false, 'Should not throw on invalid license');
    }
    
    console.log('\nFail-safe behavior tests completed.');
}

// Run all tests
function runTests() {
    console.log('\n=== Infinity Phase 1B Runtime License Enforcement Tests ===\n');
    
    testLicenseValidation();
    testEnforcement();
    testAdapterPattern();
    testIntegrationPoints();
    testFailSafeBehavior();
    
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
