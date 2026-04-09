// capsule/utils.js - Helpers for capsule lifecycle (age, diff, safe-load)

const fs = require('fs');
const path = require('path');

const CAPSULES_DIR = '.openclaw/capsules';
const RETENTION_MS = 2 * 60 * 60 * 1000; // 2 hours

function getCapsulesDir() {
  return path.join(process.env.OPENCLAW_WORKSPACE || process.cwd(), CAPSULES_DIR);
}

function isValidCapsuleId(filename) {
  // Pattern: v1-<timestamp>-<uuid>.json
  return /^v1-\d{13}-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\.json$/.test(filename);
}

function getLatestCapsuleFile() {
  const dir = getCapsulesDir();
  if (!fs.existsSync(dir)) return null;
  const files = fs.readdirSync(dir).filter(isValidCapsuleId);
  if (files.length === 0) return null;
  files.sort().reverse();
  return files[0];
}

function getAgeMs(capsule) {
  return Date.now() - new Date(capsule.timestamp).getTime();
}

function isCapsuleStale(capsule) {
  return getAgeMs(capsule) > RETENTION_MS;
}

function checkFilesExist(filepaths) {
  const workspace = process.env.OPENCLAW_WORKSPACE || process.cwd();
  for (const fp of filepaths) {
    const fullPath = path.isAbsolute(fp) ? fp : path.join(workspace, fp);
    if (!fs.existsSync(fullPath)) return false;
  }
  return true;
}

function safeLoadCapsule(filename) {
  const dir = getCapsulesDir();
  const filepath = path.join(dir, filename);
  if (!fs.existsSync(filepath)) return null;
  try {
    const raw = fs.readFileSync(filepath, 'utf8');
    const capsule = JSON.parse(raw);
    require('./schema').validateCapsule(capsule);
    return capsule;
  } catch (e) {
    console.error(`[infinity] Failed to load capsule ${filename}: ${e.message}`);
    return null;
  }
}

module.exports = {
  CAPSULES_DIR,
  RETENTION_MS,
  getCapsulesDir,
  isValidCapsuleId,
  getLatestCapsuleFile,
  getAgeMs,
  isCapsuleStale,
  checkFilesExist,
  safeLoadCapsule,
};
