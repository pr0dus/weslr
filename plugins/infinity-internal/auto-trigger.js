/**
 * Infinity Internal — Auto-Trigger (Context-Risk Edition)
 * Silent background capture driven by continuity risk signals, not just timers.
 * No external packages. No operator commands. Fully self-contained.
 */

const { existsSync, readFileSync, writeFileSync, mkdirSync } = require("fs");
const path = require("path");

const STATE_KEY = "auto-state";
const COOLDOWN_MS = 5 * 60 * 1000;        // 5 minutes base cooldown
const AGING_THRESHOLD_MS = 15 * 60 * 1000; // 15 minutes — force capture if no capture yet / capsule too old
const RISK_CAPTURE_COUNT = 3;              // captures before we start treating state as "high risk"
const MIN_INTERVAL_MS = 60 * 1000;        // 1 minute — absolute minimum between captures
const RISK_THRESHOLD = 50;                 // edge-trigger threshold

// Resolve relative to this file's location
const CAPSULE_DATA_DIR = path.resolve(__dirname, "..", ".capsule-data");

function ensureStorageDir() {
  if (!existsSync(CAPSULE_DATA_DIR)) {
    mkdirSync(CAPSULE_DATA_DIR, { recursive: true });
  }
}

function loadState() {
  try {
    const filePath = path.join(CAPSULE_DATA_DIR, `${STATE_KEY}.json`);
    if (!existsSync(filePath)) {
      return {};
    }
    const raw = JSON.parse(readFileSync(filePath, "utf8"));
    // Guard against null/invalid state — return safe default so callers never receive null
    if (raw == null) {
      return {};
    }
    return raw;
  } catch {
    return {};
  }
}

function saveState(state) {
  try {
    ensureStorageDir();
    const filePath = path.join(CAPSULE_DATA_DIR, `${STATE_KEY}.json`);
    writeFileSync(filePath, JSON.stringify(state, null, 2), "utf8");
  } catch {
    // Non-fatal — state save failure does not block capture
  }
}

/**
 * Compute a simple risk score for the current session state.
 * Higher score = higher continuity risk.
 * Returns a number 0–100.
 */
function computeRiskScore(currentState, lastState) {
  let score = 0;

  // Signal 1: Accumulated captures (more captures = more context history = higher risk)
  const captureCount = lastState?.captureCount || 0;
  if (captureCount >= RISK_CAPTURE_COUNT) {
    score += 40;
  } else if (captureCount >= 1) {
    score += captureCount * 10;
  }

  // Signal 2: Dirty working state (unsaved work at risk)
  if (currentState.dirty) {
    score += 25;
  }

  // Signal 3: Active files presence (means active work happening)
  if (currentState.activeFiles && currentState.activeFiles.length > 0) {
    score += 15;
  }

  // Signal 4: Capsule age — if last capture is too old, risk rises
  if (lastState?.lastCaptureTs) {
    const ageMs = Date.now() - lastState.lastCaptureTs;
    if (ageMs > AGING_THRESHOLD_MS) {
      score += 30;
    } else if (ageMs > COOLDOWN_MS) {
      score += Math.min(20, Math.floor((ageMs - COOLDOWN_MS) / 60000) * 5);
    }
  } else {
    // No prior capture — initial capture gets moderate risk boost
    score += 20;
  }

  // Signal 5: Context growth rate — if captures are increasing fast, risk rises
  if (lastState?.captureCount && lastState?.prevCaptureCount) {
    const growthRate = lastState.captureCount - lastState.prevCaptureCount;
    if (growthRate >= 2) {
      score += 15;
    }
  }

  return Math.min(100, score);
}

/**
 * Determine whether a new capsule capture should be triggered.
 * Returns { shouldCapture, reason, riskScore }.
 *
 * EDGE-TRIGGERED: capture fires only when risk CROSSES threshold (false→true).
 * Does NOT repeat capture while risk stays above threshold.
 */
function evaluateTrigger(currentState, lastState) {
  const riskScore = computeRiskScore(currentState, lastState);
  const nowAbove = riskScore >= RISK_THRESHOLD;
  const wasAbove = lastState?.wasAboveThreshold ?? false;
  const edgeCrossed = !wasAbove && nowAbove;

  // First run ever — always capture (risk is unknown)
  if (!lastState) {
    return { shouldCapture: true, reason: "initial-capture", riskScore };
  }

  // Cooldown not expired — skip unless risk is HIGH
  if (lastState.lastCaptureTs) {
    const elapsed = Date.now() - lastState.lastCaptureTs;
    if (elapsed < MIN_INTERVAL_MS) {
      return { shouldCapture: false, reason: `min-interval-active (${Math.round(elapsed / 1000)}s elapsed)`, riskScore };
    }
    if (elapsed < COOLDOWN_MS && riskScore < RISK_THRESHOLD) {
      return { shouldCapture: false, reason: `cooldown-active (${Math.round(elapsed / 1000)}s elapsed)`, riskScore };
    }
  }

  // No meaningful change — skip unless risk is HIGH
  const meaningfulChange =
    currentState.commit !== lastState.lastCommit ||
    currentState.dirty !== lastState.lastDirty ||
    JSON.stringify(currentState.activeFiles || []) !== JSON.stringify(lastState.lastActiveFiles || []);

  if (!meaningfulChange && riskScore < RISK_THRESHOLD) {
    return { shouldCapture: false, reason: "no-meaningful-change", riskScore };
  }

  // EDGE-TRIGGERED: only fire on threshold crossing (false → true)
  if (edgeCrossed) {
    const riskReason =
      riskScore >= 80 ? "critical-risk" :
      riskScore >= 60 ? "high-risk" :
      "moderate-risk";
    return { shouldCapture: true, reason: `risk-triggered-${riskReason}`, riskScore };
  }

  // Normal trigger: meaningful change after cooldown
  if (meaningfulChange) {
    return { shouldCapture: true, reason: "meaningful-state-change", riskScore };
  }

  return { shouldCapture: false, reason: "below-risk-threshold", riskScore };
}

/**
 * Build the next auto-state from a successful capture result + previous state.
 */
function buildNextState(captureResult, prevState = {}) {
  const riskScore = captureResult._riskScore || 0;
  return {
    lastCaptureTs: Date.now(),
    lastCommit: captureResult.commit,
    lastDirty: captureResult.dirty,
    lastActiveFiles: captureResult.activeFiles || [],
    lastReason: captureResult.reason,
    captureCount: (prevState.captureCount || 0) + 1,
    prevCaptureCount: prevState.captureCount || 0,
    lastRiskScore: riskScore,
    wasAboveThreshold: riskScore >= RISK_THRESHOLD
  };
}

/**
 * Start the auto-trigger loop.
 * Requires { capture } — the capture function from index.js.
 * Requires { logger } — the api.logger instance from index.js register().
 * Requires { intervalMs } — check interval in milliseconds (default 2 min).
 */
function startAutoTrigger({ capture, logger, intervalMs = 2 * 60 * 1000 }) {
  let timer = null;
  let lastState = loadState();

  function getCurrentState() {
    // Lazy-load utils to avoid circular requires at module load time
    const { buildRestartPayload } = require("./capsule/utils");
    return buildRestartPayload("auto-check");
  }

  async function tick() {
    let currentState;
    try {
      currentState = getCurrentState();
    } catch (err) {
      if (logger && typeof logger.warn === "function") {
        logger.warn(`[infinity-internal] getCurrentState error: ${err.message}`);
      }
      return;
    }
    try {
      const { shouldCapture, reason, riskScore } = evaluateTrigger(currentState, lastState);

      if (shouldCapture) {
        const result = await capture({ reason, _riskScore: riskScore });
        lastState = buildNextState(result, lastState);
        saveState(lastState);
        if (logger && typeof logger.info === "function") {
          logger.info(`[infinity-internal] auto-capture [risk=${riskScore}]: ${reason}`);
        }
      } else {
        if (logger && typeof logger.debug === "function") {
          logger.debug(`[infinity-internal] auto-check [risk=${riskScore}]: ${reason}`);
        }
      }
    } catch (err) {
      if (logger && typeof logger.warn === "function") {
        logger.warn(`[infinity-internal] auto-check error: ${err.message}`);
      }
    }
  }

  // Run first tick after a short settling period (10s)
  setTimeout(tick, 10 * 1000);

  // Then run on interval
  timer = setInterval(tick, intervalMs);

  return function stopAutoTrigger() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  };
}

module.exports = { startAutoTrigger, evaluateTrigger, computeRiskScore, loadState, saveState };
module.exports.default = { startAutoTrigger, evaluateTrigger, computeRiskScore, loadState, saveState };
