const { execSync } = require("child_process");
const { readFileSync, existsSync, statSync } = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function isGitRepo() {
  try {
    return execSync("git rev-parse --git-dir", { cwd: repoRoot, encoding: "utf8", stdio: "pipe" }) !== null;
  } catch {
    return false;
  }
}

function runGit(cmd) {
  try {
    return execSync(`git ${cmd}`, { cwd: repoRoot, encoding: "utf8", stdio: "pipe" }).trim();
  } catch {
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

function collectActiveFilesNonGit(limit = 32) {
  // Fallback: walk the repo root for recently modified files (non-git)
  const exclusions = [".backup", ".disabled", ".rollback", "__pycache__", "node_modules", ".git"];
  const seen = new Set();
  const files = [];
  try {
    const entries = require("fs").readdirSync(repoRoot);
    for (const entry of entries) {
      if (files.length >= limit) break;
      const lowered = entry.toLowerCase();
      if (exclusions.some((token) => lowered.includes(token))) continue;
      const fullPath = path.join(repoRoot, entry);
      try {
        const stat = statSync(fullPath);
        if (stat.isFile()) {
          seen.add(entry);
          files.push(entry);
        }
      } catch {
        // Skip entries we can't stat
      }
    }
  } catch {
    // readdirSync failure — return empty
  }
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
  isGitRepo,
  buildRestartPayload(reason) {
    const hasGit = isGitRepo();
    const status = hasGit ? runGit("status --porcelain") : null;
    const branch = hasGit ? (runGit("rev-parse --abbrev-ref HEAD") || "unknown") : "non-git";
    const commit = hasGit ? (runGit("rev-parse HEAD") || "unknown") : "non-git";
    const latestTask = loadLatestTask();
    const activeFiles = hasGit
      ? collectActiveFiles(status)
      : collectActiveFilesNonGit();
    return {
      repoRoot,
      branch,
      commit,
      hasGit,
      dirty: Boolean(status && status.trim()),
      activeFiles,
      pendingTests: loadPendingTests(),
      latestTask,
      reason
    };
  }
};
