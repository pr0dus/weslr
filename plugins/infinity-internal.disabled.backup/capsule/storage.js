const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

function getWorkspaceRoot() {
  return process.env.OPENCLAW_WORKSPACE || process.cwd();
}

function getCapsulesDir() {
  return path.join(getWorkspaceRoot(), '.openclaw', 'continuity', 'capsules');
}

function ensureCapsulesDir() {
  const dir = getCapsulesDir();
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  return dir;
}

function listCapsules() {
  const dir = getCapsulesDir();
  if (!fs.existsSync(dir)) {
    return [];
  }
  return fs
    .readdirSync(dir)
    .filter((entry) => entry.endsWith('.json'))
    .sort((a, b) => b.localeCompare(a));
}

function saveCapsule(capsule) {
  const dir = ensureCapsulesDir();
  const filename = `cap-${Date.now()}-${uuidv4()}.json`;
  const filepath = path.join(dir, filename);
  fs.writeFileSync(filepath, JSON.stringify(capsule, null, 2), 'utf8');
  return filename;
}

function getLatestCapsuleFile() {
  const entries = listCapsules();
  if (entries.length === 0) {
    return null;
  }
  return path.join(getCapsulesDir(), entries[0]);
}

function getCapsulePath(filename) {
  if (!filename) return null;
  return path.join(getCapsulesDir(), filename);
}

module.exports = {
  getCapsulesDir,
  listCapsules,
  saveCapsule,
  getLatestCapsuleFile,
  getCapsulePath,
};
