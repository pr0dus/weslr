const fs = require('fs');
const { getLatestCapsuleFile } = require('./storage');

function safeLoadCapsule(filename) {
  if (!filename) {
    return null;
  }
  try {
    const content = fs.readFileSync(filename, 'utf8');
    return JSON.parse(content);
  } catch (err) {
    return null;
  }
}

function getLatestCapsule() {
  const latestPath = getLatestCapsuleFile();
  if (!latestPath) {
    return null;
  }
  return safeLoadCapsule(latestPath);
}

function isCapsuleStale(capsule, ttlMs = 2 * 60 * 60 * 1000) {
  if (!capsule || !capsule.timestamp) return true;
  const ts = Date.parse(capsule.timestamp);
  if (Number.isNaN(ts)) return true;
  return Date.now() - ts > ttlMs;
}

module.exports = {
  safeLoadCapsule,
  getLatestCapsule,
  isCapsuleStale,
};
