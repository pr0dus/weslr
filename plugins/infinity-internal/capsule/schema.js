module.exports = {
  type: "object",
  description: "Minimal deterministic restart capsule payload schema.",
  required: ["repoRoot", "branch", "commit", "dirty", "activeFiles", "reason"],
  properties: {
    repoRoot: { type: "string" },
    branch: { type: "string" },
    commit: { type: "string" },
    dirty: { type: "boolean" },
    activeFiles: { type: "array", items: { type: "string" } },
    pendingTests: { type: "array", items: { type: "string" } },
    latestTask: { type: ["string", "null"] },
    reason: { type: "string" }
  }
};
