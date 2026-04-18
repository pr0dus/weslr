// version.js - Infinity Plugin Baseline Identity and Compatibility Constants
// Phase 1C-A: Runtime Hardening + Conflict Detection

/**
 * Infinity Plugin Version (Semantic Versioning)
 */
const INFINITY_VERSION = '1.0.0';

/**
 * OpenClaw Version Range (that Infinity was built against)
 */
const OPENCLAW_VERSION_RANGE = {
  min: '2026.3.0',
  max: '2026.4.0',
  current: '2026.3.13',
  compatible: true,
};

/**
 * Compatibility Modes
 */
const CompatibilityMode = {
  STRICT: 'strict',       // Only exact version match
  FALLBACK: 'fallback',   // Allow minor version differences
  DEGRADED: 'degraded',   // Accept but warn
};

/**
 * Current Compatibility Mode (determined at runtime)
 */
let currentCompatibilityMode = CompatibilityMode.STRICT;

/**
 * License File Schema Version
 */
const LICENSE_SCHEMA_VERSION = '1.0';

/**
 * Config File Schema Version
 */
const CONFIG_SCHEMA_VERSION = '1.0';

/**
 * Get Infinity Version String
 */
function getVersion() {
  return INFINITY_VERSION;
}

/**
 * Get OpenClaw Version Range
 */
function getOpenClawVersionRange() {
  return OPENCLAW_VERSION_RANGE;
}

/**
 * Get Current Compatibility Mode
 */
function getCompatibilityMode() {
  return currentCompatibilityMode;
}

/**
 * Set Compatibility Mode
 */
function setCompatibilityMode(mode) {
  currentCompatibilityMode = mode;
}

/**
 * Check if OpenClaw version is compatible
 */
function isOpenClawVersionCompatible(version) {
  if (!version) return false;
  
  const [major, minor, patch] = version.split('.').map(Number);
  const [minMajor, minMinor, minPatch] = OPENCLAW_VERSION_RANGE.min.split('.').map(Number);
  const [maxMajor, maxMinor, maxPatch] = OPENCLAW_VERSION_RANGE.max.split('.').map(Number);
  
  // Check if version is within range
  const inRange = 
    (major > minMajor || (major === minMajor && minor >= minMinor)) &&
    (major < maxMajor || (major === maxMajor && minor <= maxMinor));
  
  return inRange;
}

/**
 * Get Baseline Identity Object
 */
function getBaselineIdentity() {
  return {
    infinity: {
      version: INFINITY_VERSION,
      builtAgainst: OPENCLAW_VERSION_RANGE.current,
    },
    compatibility: {
      mode: currentCompatibilityMode,
      openClawVersion: OPENCLAW_VERSION_RANGE.current,
      compatible: OPENCLAW_VERSION_RANGE.compatible,
    },
    schema: {
      license: LICENSE_SCHEMA_VERSION,
      config: CONFIG_SCHEMA_VERSION,
    },
  };
}

module.exports = {
  INFINITY_VERSION,
  OPENCLAW_VERSION_RANGE,
  CompatibilityMode,
  LICENSE_SCHEMA_VERSION,
  CONFIG_SCHEMA_VERSION,
  getVersion,
  getOpenClawVersionRange,
  getCompatibilityMode,
  setCompatibilityMode,
  isOpenClawVersionCompatible,
  getBaselineIdentity,
};
