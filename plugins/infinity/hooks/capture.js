// hooks/capture.js - Silent capture before /reset, /new, or context overflow

const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const storage = require('../storage');

function getCurrentRepo() {
  // OpenClaw workspace root is our repo identity for v1
  return process.env.OPENCLAW_WORKSPACE || process.cwd();
}

async function getBranch(repoPath) {
  try {
    const { execSync } = require('child_process');
    const branch = execSync('git rev-parse --abbrev-ref HEAD', {
      cwd: repoPath,
      encoding: 'utf8',
    }).trim();
    return branch;
  } catch (e) {
    return 'unknown';
  }
}

async function getHeadCommit(repoPath) {
  try {
    const { execSync } = require('child_process');
    const commit = execSync('git rev-parse HEAD', { cwd: repoPath, encoding: 'utf8' }).trim();
    return commit;
  } catch (e) {
    return 'unknown';
  }
}

async function isDirty(repoPath) {
  try {
    const { execSync } = require('child_process');
    const status = execSync('git diff-index --quiet HEAD --', { cwd: repoPath, encoding: 'utf8' });
    return status !== 0;
  } catch (e) {
    return true;
  }
}

function getActiveFiles() {
  // OpenClaw internal API — returns list of active file paths
  // For v1, use a best-effort approximation if internal API not available
  // Implementation assumes OpenClaw provides this
  const api = require('openclaw-api');
  return api.getActiveFiles?.() || [];
}

function getPendingTests() {
  // Internal session state for pending tests (no execution)
  const api = require('openclaw-api');
  return api.getPendingTests?.() || [];
}

function getLatestTaskDescription() {
  // Internal session state
  const api = require('openclaw-api');
  return api.getLatestTaskDescription?.() || '';
}

async function captureCapsule() {
  const repoPath = getCurrentRepo();
  const branch = await getBranch(repoPath);
  const commit = await getHeadCommit(repoPath);
  const dirty = await isDirty(repoPath);
  const activeFiles = getActiveFiles();
  const pendingTests = getPendingTests();
  const latestTaskDescription = getLatestTaskDescription();

  const capsule = {
    version: 1,
    timestamp: new Date().toISOString(),
    git: { repo: repoPath, branch, commit, dirty },
    session: { activeFiles, pendingTests, latestTaskDescription },
    meta: {
      id: `v1-${Date.now()}-${uuidv4()}`,
      reason: 'pre-reset', // default, overridden in specific hooks
    },
  };

  // Validate
  const { validateCapsule } = require('../capsule/schema');
  validateCapsule(capsule);

  // Save
  const filename = storage.save(capsule);
  console.log(`[infinity] captured capsule ${filename}`);
  return filename;
}

module.exports = {
  captureCapsule,
};
