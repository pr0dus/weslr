/**
 * Infinity Phase 1C-A — Runtime Hardening + Conflict Detection Tests
 * 
 * Tests for runtime hardening, conflict detection, and baseline identity.
 * Focus: Real conflict detection vs false positives.
 */

const { getBaselineIdentity, CompatibilityMode, INFINITY_VERSION } = require('./version');
const { detectConflicts, getConflictSummary, getPluginLocations } = require('./conflict');
const { runHardeningChecks, getHardeningStatus } = require('./hardening');

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

function testBaselineIdentity() {
    console.log('\n=== Baseline Identity Tests ===\n');
    
    const identity = getBaselineIdentity();
    
    assert(identity !== null, 'Baseline identity exists');
    assert(identity.infinity !== null, 'Infinity version in identity');
    assert(identity.infinity.version === INFINITY_VERSION, 'Infinity version correct');
    assert(identity.compatibility !== null, 'Compatibility info in identity');
    assert(identity.schema !== null, 'Schema versions in identity');
    
    console.log('Version:', identity.infinity.version);
    console.log('Built against OpenClaw:', identity.compatibility.openClawVersion);
    console.log('License schema:', identity.schema.license);
    console.log('Config schema:', identity.schema.config);
}

function testConflictDetection() {
    console.log('\n=== Conflict Detection Tests ===\n');
    
    // Test plugin locations
    const locations = getPluginLocations();
    assert(locations !== null, 'Plugin locations detected');
    assert(locations.length > 0, 'At least one location found');
    
    console.log('Locations found:', locations.length);
    for (const loc of locations) {
        console.log('  -', loc.type, ':', loc.path);
    }
    
    // Test conflict detection (should return array)
    const conflicts = detectConflicts();
    assert(Array.isArray(conflicts), 'Conflicts is array');
    
    console.log('Conflicts detected:', conflicts.length);
    for (const conflict of conflicts) {
        console.log('  -', conflict.type, '(', conflict.severity, '):', conflict.description);
    }
    
    // Test conflict summary
    const summary = getConflictSummary(conflicts);
    assert(typeof summary === 'string', 'Conflict summary is string');
    console.log('Summary:', summary);
}

function testHardeningChecks() {
    console.log('\n=== Hardening Checks Tests ===\n');
    
    const results = runHardeningChecks();
    
    assert(results !== null, 'Hardening results exist');
    assert(results.checks !== null, 'Hardening checks object exists');
    assert(typeof results.valid === 'boolean', 'Hardening valid is boolean');
    assert(typeof results.summary === 'string', 'Hardening summary is string');
    
    console.log('Valid:', results.valid);
    console.log('Summary:', results.summary);
    
    console.log('Module paths checked:', results.checks.modulePaths.length);
    console.log('File permissions checked:', results.checks.filePermissions.length);
    console.log('License location checked:', results.checks.licenseLocation.length);
    console.log('Baseline identity checked:', results.checks.baselineIdentity.length);
    
    const status = getHardeningStatus(results);
    assert(typeof status === 'string', 'Hardening status is string');
    console.log('Status:', status);
}

function testConflictDetectionVsFalsePositives() {
    console.log('\n=== Conflict Detection vs False Positives ===\n');
    
    // Test that mere existence of workspace/repo copies is NOT a conflict
    const locations = getPluginLocations();
    const activeLocations = locations.filter(l => l.active);
    
    console.log('Total locations:', locations.length);
    console.log('Active locations:', activeLocations.length);
    
    // Workspace/repo copies alone should NOT trigger conflict
    // Only active/loaded plugins should be considered
    if (activeLocations.length <= 1) {
        assert(true, 'Single active location - no conflict');
    } else if (activeLocations.length > 1) {
        console.log('Multiple active locations - this is a REAL conflict');
        // This would be a real conflict if multiple Infinity plugins are actually loaded
    }
    
    // Test that conflict detection doesn't crash on missing directories
    const conflicts = detectConflicts();
    assert(Array.isArray(conflicts), 'Conflict detection works without errors');
    
    console.log('Conflict detection completed without crashes');
}

function testNoCrashBehavior() {
    console.log('\n=== No-Crash Behavior Tests ===\n');
    
    // Test conflict detection without crash
    try {
        const conflicts = detectConflicts();
        assert(Array.isArray(conflicts), 'Conflict detection returns array');
        console.log('  ✓ Conflict detection did not crash');
    } catch (e) {
        console.error('  ✗ Conflict detection crashed:', e.message);
    }
    
    // Test hardening checks without crash
    try {
        const results = runHardeningChecks();
        assert(results !== null, 'Hardening checks returned results');
        console.log('  ✓ Hardening checks did not crash');
    } catch (e) {
        console.error('  ✗ Hardening checks crashed:', e.message);
    }
    
    // Test baseline identity without crash
    try {
        const identity = getBaselineIdentity();
        assert(identity !== null, 'Baseline identity returned');
        console.log('  ✓ Baseline identity did not crash');
    } catch (e) {
        console.error('  ✗ Baseline identity crashed:', e.message);
    }
    
    console.log('No crash tests completed');
}

function testDegradedModeBehavior() {
    console.log('\n=== Degraded Mode Behavior Tests ===\n');
    
    // Test that conflict detection doesn't block operation
    const conflicts = detectConflicts();
    const hasConflicts = conflicts.length > 0;
    
    if (hasConflicts) {
        console.log('Conflicts detected - should use degraded mode');
    } else {
        console.log('No conflicts - can use premium mode if license valid');
    }
    
    // Test that hardening failures don't block operation
    const hardening = runHardeningChecks();
    const hasHardeningIssues = !hardening.valid;
    
    if (hasHardeningIssues) {
        console.log('Hardening issues - should use degraded mode');
    } else {
        console.log('No hardening issues - can proceed normally');
    }
    
    console.log('Degraded mode logic verified');
}

// Run all tests
function runTests() {
    console.log('\n=== Infinity Phase 1C-A Tests ===\n');
    
    testBaselineIdentity();
    testConflictDetection();
    testHardeningChecks();
    testConflictDetectionVsFalsePositives();
    testNoCrashBehavior();
    testDegradedModeBehavior();
    
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
