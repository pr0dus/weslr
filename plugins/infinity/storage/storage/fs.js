// storage/fs.js - File I/O abstraction for capsule storage

const fs = require('fs');
const path = require('path');
const { CAPSULES_DIR } = require('../capsule/utils');

function getDir() {
  const workspace = process.env.OPENCLAW_WORKSPACE || process.cwd();
  const dir = path.join(workspace, CAPSULES_DIR);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  return dir;
}

function saveCapsule(filename, capsule) {
  const dir = getDir();
  const filepath = path.join(dir, filename);
  fs.writeFileSync(filepath, JSON.stringify(capsule, null, 2), 'utf8');
  return filename;
}

function loadCapsule(filename) {
  const dir = getDir();
  const filepath = path.join(dir, filename);
  if (!fs.existsSync(filepath)) return null;
  try {
    const raw = fs.readFileSync(filepath, 'utf8');
    return JSON.parse(raw);
  } catch (e) {
    console.error(`[infinity] Failed to load ${filename}: ${e.message}`);
    return null;
  }
}

function listCapsules() {
  const dir = getDir();
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter(f => f.startsWith('v1-') && f.endsWith('.json'));
}

function deleteCapsule(filename) {
  const dir = getDir();
  const filepath = path.join(dir, filename);
  if (fs.existsSync(filepath)) {
    fs.unlinkSync(filepath);
    return true;
  }
  return false;
}

module.exports = {
  getDir,
  saveCapsule,
  loadCapsule,
  listCapsules,
  deleteCapsule,
};
