const { execSync } = require("child_process");
const { readFileSync, existsSync } = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function runGit(cmd) {
  try {
    return execSync(`git ${cmd}`, { cwd: repoRoot, encoding: "utf8" }).trim();
  } catch (error) {
    return null;
  }
}

function collectActiveFiles(statusText, limit = 32) {
  if (!statusText) {
    return [];
  }
  const exclusions = [".backup", ".disabled", ".rollback", "__pycache__"];
  const seen = new Set();
  const files = [];
  statusText
    .split(/\r?\n/)
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .forEach((entry) => {
      if (files.length >= limit) {
        return;
      }
      const lowered = entry.toLowerCase();
      if (exclusions.some((token) => lowered.includes(token))) {
        return;
      }
      if (seen.has(entry)) {
        return;
      }
      seen.add(entry);
      files.push(entry);
    });
  return files;
}

function loadPendingTests() {
  const filePath = path.join(repoRoot, ".pending-tests");
  if (existsSync(filePath)) {
    return readFileSync(filePath, "utf8").split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  }
  const envValue = process.env.PENDING_TESTS;
  if (envValue) {
    return envValue.split(",").map((entry) => entry.trim()).filter(Boolean);
  }
  return [];
}

function loadLatestTask() {
  const filePath = path.join(repoRoot, ".latest-task");
  if (existsSync(filePath)) {
    return readFileSync(filePath, "utf8").split(/\r?\n/)[0]?.trim() || null;
  }
  return process.env.LATEST_TASK_DESCRIPTION || null;
}

module.exports = {
  buildRestartPayload(reason) {
    const status = runGit("status --porcelain");
    const branch = runGit("rev-parse --abbrev-ref HEAD") || "unknown";
    const commit = runGit("rev-parse HEAD") || "unknown";
    const latestTask = loadLatestTask();
    return {
      repoRoot,
      branch,
      commit,
      dirty: Boolean(status && status.trim()),
      activeFiles: collectActiveFiles(status),
      pendingTests: loadPendingTests(),
      latestTask,
      reason
    };
  }
};
