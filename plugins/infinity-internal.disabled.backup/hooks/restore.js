const fs = require('fs');
const path = require('path');
const storage = require('../capsule/storage');
const { safeLoadCapsule, isCapsuleStale } = require('../capsule/utils');

function getWorkspaceRoot() {
  return process.env.OPENCLAW_WORKSPACE || process.cwd();
}

function persistResumeState(capsule) {
  const dir = path.join(getWorkspaceRoot(), '.openclaw', 'continuity');
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  const state = {
    restoredAt: new Date().toISOString(),
    capsuleId: capsule.meta.id,
    anchor: capsule.anchor,
  };
  fs.writeFileSync(path.join(dir, 'resume-state.json'), JSON.stringify(state, null, 2), 'utf8');
}

function attemptRestore() {
  const latestFile = storage.getLatestCapsuleFile();
  if (!latestFile) {
    return { result: 'skipped_no_capsule' };
  }

  const capsule = safeLoadCapsule(latestFile);
  if (!capsule) {
    return { result: 'skipped_invalid_capsule' };
  }

  const workspaceRoot = getWorkspaceRoot();
  if (capsule.git?.repo !== workspaceRoot) {
    return { result: 'skipped_repo_mismatch' };
  }

  if (isCapsuleStale(capsule)) {
    return { result: 'skipped_stale_capsule' };
  }

  persistResumeState(capsule);

  return {
    result: 'restored',
    capsuleId: capsule.meta.id,
    anchor: capsule.anchor,
  };
}

module.exports = {
  attemptRestore,
};
