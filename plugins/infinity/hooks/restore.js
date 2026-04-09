// hooks/restore.js - Silent restore on init (safe subset only)

const { safeLoadCapsule, getLatestCapsuleFile, checkFilesExist, isCapsuleStale } = require('../capsule/utils');
const storage = require('../storage');

function getCurrentRepo() {
  return process.env.OPENCLAW_WORKSPACE || process.cwd();
}

async function getBranch(repoPath) {
  try {
    const { execSync } = require('child_process');
    return execSync('git rev-parse --abbrev-ref HEAD', { cwd: repoPath, encoding: 'utf8' }).trim();
  } catch (e) {
    return 'unknown';
  }
}

function getActiveFiles() {
  const api = require('openclaw-api');
  return api.getActiveFiles?.() || [];
}

function reopenFiles(filepaths) {
  // Silent reopen — no UI
  const api = require('openclaw-api');
  if (api.reopenFiles) {
    api.reopenFiles(filepaths);
  }
}

function setPendingTests(tests) {
  // Internal remembered session state only — no execution
  const api = require('openclaw-api');
  if (api.setPendingTests) {
    api.setPendingTests(tests);
  }
}

function setLatestTaskDescription(desc) {
  // Internal remembered session state only
  const api = require('openclaw-api');
  if (api.setLatestTaskDescription) {
    api.setLatestTaskDescription(desc);
  }
}

async function attemptRestore() {
  const repoPath = getCurrentRepo();
  const branch = await getBranch(repoPath);
  const activeFiles = getActiveFiles();

  // Check if active task exists (files open)
  if (activeFiles.length > 0) {
    console.log('[infinity] restore skipped: active task exists');
    return { result: 'skipped_existing_active_task' };
  }

  const latestFilename = getLatestCapsuleFile();
  if (!latestFilename) {
    console.log('[infinity] restore skipped: no capsule found');
    return { result: 'skipped_no_capsule' };
  }

  const capsule = safeLoadCapsule(latestFilename);
  if (!capsule) {
    console.log('[infinity] restore skipped: invalid capsule');
    return { result: 'skipped_invalid_capsule' };
  }

  // Safe checks
  if (capsule.git.repo !== repoPath) {
    console.log('[infinity] restore skipped: repo mismatch');
    return { result: 'skipped_repo_mismatch' };
  }

  if (capsule.git.branch !== branch) {
    console.log('[infinity] restore skipped: branch mismatch');
    return { result: 'skipped_branch_mismatch' };
  }

  if (isCapsuleStale(capsule)) {
    console.log('[infinity] restore skipped: stale capsule');
    return { result: 'skipped_stale' };
  }

  if (!checkFilesExist(capsule.session.activeFiles)) {
    console.log('[infinity] restore skipped: missing files');
    return { result: 'skipped_missing_files' };
  }

  // Restore safely (v1 subset only)
  reopenFiles(capsule.session.activeFiles);
  setPendingTests(capsule.session.pendingTests);
  setLatestTaskDescription(capsule.session.latestTaskDescription);

  console.log(`[infinity] restored capsule ${capsule.meta.id}`);
  return { result: 'restored' };
}

module.exports = {
  attemptRestore,
};
