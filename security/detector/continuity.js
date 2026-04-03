#!/usr/bin/env node
/**
 * security/detector/continuity.js - Continuity Anomaly Detection (Scaffold)
 * Phase 1: Baseline comparison and state deviation detection
 */

/**
 * ContinuityDetector - Detects continuity/state corruption
 */
export class ContinuityDetector {
  constructor() {
    this.baselines = new Map();
  }

  /**
   * Store baseline state for later comparison
   */
  async storeBaseline(key, state) {
    const hash = this.hashState(state);
    this.baselines.set(key, {
      timestamp: new Date().toISOString(),
      hash,
      state
    });
    return hash;
  }

  /**
   * Get stored baseline
   */
  async getBaseline(key) {
    return this.baselines.get(key);
  }

  /**
   * Analyze deviation from baseline
   */
  async analyze(currentState, baseline) {
    if (!baseline) {
      return {
        isAnomaly: false,
        deviationScore: 0,
        message: "No baseline found",
        affectedModules: []
      };
    }

    const deviationScore = this.calculateDeviation(currentState, baseline.state);
    
    return {
      isAnomaly: deviationScore > 0.25, // 25% threshold
      deviationScore,
      message: deviationScore > 0.25 
        ? "Continuity anomaly detected" 
        : "State within normal parameters",
      affectedModules: this.identifyChangedModules(currentState, baseline.state),
      baselineHash: baseline.hash,
      currentHash: this.hashState(currentState)
    };
  }

  /**
   * Calculate deviation between states (Kullback-Leibler divergence approximation)
   */
  calculateDeviation(current, baseline) {
    // Simple Euclidean distance for now
    const currentKeys = Object.keys(current);
    const baselineKeys = Object.keys(baseline);
    
    const allKeys = new Set([...currentKeys, ...baselineKeys]);
    let sumSquaredDiff = 0;
    let count = 0;
    
    for (const key of allKeys) {
      const currVal = current[key] ?? 0;
      const baseVal = baseline[key] ?? 0;
      
      const diff = Math.abs(currVal - baseVal);
      sumSquaredDiff += diff * diff;
      count++;
    }
    
    return Math.sqrt(sumSquaredDiff / count);
  }

  /**
   * Identify which modules changed
   */
  identifyChangedModules(current, baseline) {
    const currentKeys = Object.keys(current);
    const baselineKeys = Object.keys(baseline);
    
    const added = currentKeys.filter(k => !baselineKeys.includes(k));
    const removed = baselineKeys.filter(k => !currentKeys.includes(k));
    
    const commonKeys = currentKeys.filter(k => baselineKeys.includes(k));
    const changed = commonKeys.filter(k => 
      JSON.stringify(current[k]) !== JSON.stringify(baseline[k])
    );
    
    return {
      added,
      removed,
      changed,
      totalChanged: added.length + removed.length + changed.length
    };
  }

  /**
   * Hash state for integrity verification
   */
  hashState(state) {
    const json = JSON.stringify(state, Object.keys(state).sort());
    return require("crypto").createHash("sha256").update(json).digest("hex");
  }
}

export default ContinuityDetector;
