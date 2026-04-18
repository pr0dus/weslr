const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { v4: uuidv4 } = require('uuid');
const storage = require('../capsule/storage');
const { validateCapsule } = require('../capsule/schema');

function getWorkspaceRoot() {
  return process.env.OPENCLAW_WORKSPACE || process.cwd();
}

function readContinuityJson(filename, defaultValue) {
  const filePath = path.join(getWorkspaceRoot(), '.openclaw', 'continuity', filename);
  if (!fs.existsSync(filePath)) {
    return defaultValue;
  }
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (err) {
    return defaultValue;
  }
}

function getActiveFiles() {
  return readContinuityJson('active-files.json', []);
}

function getPendingTests() {
  return readContinuityJson('pending-tests.json', []);
}

function getTaskAnchor() {
  return readContinuityJson('task-anchor.json', { task: '', note: '' });
}

function getGitValue(command, repoPath) {
  try {
    return execSync(command, { cwd: repoPath, encoding: 'utf8' }).trim();
  } catch (err) {
    return 'unknown';
  }
}

async function captureCapsule(options = {}) {
  const repoPath = getWorkspaceRoot();
  const branch = getGitValue('git rev-parse --abbrev-ref HEAD', repoPath);
  const commit = getGitValue('git rev-parse HEAD', repoPath);

  const activeFiles = Array.isArray(options.activeFiles) ? options.activeFiles : getActiveFiles();
  const pendingTests = Array.isArray(options.pendingTests) ? options.pendingTests : getPendingTests();
  const anchor = { ...getTaskAnchor() };
  const note = options.note || anchor.note || `captured@${new Date().toISOString()}`;
  const capsule = {
    version: 1,
    timestamp: new Date().toISOString(),
    git: {
      repo: repoPath,
      branch,
      commit,
    },
    session: {
      activeFiles,
      pendingTests,
    },
    anchor: {
      task: anchor.task || '',
      note,
    },
    meta: {
      id: `infinity-internal-${Date.now()}-${uuidv4()}`,
      reason: options.reason || 'pre-reset',
    },
  };

  validateCapsule(capsule);
  const filename = storage.saveCapsule(capsule);
  return { filename, capsule };
}

module.exports = {
  captureCapsule,
};
