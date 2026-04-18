const { buildRestartPayload } = require("../capsule/utils");

// ASSUMPTION: The hook host will call captureCapsule() with optional context.
module.exports = {
  async captureCapsule(context = {}) {
    const reason = context.reason || "initial staging capture";
    return {
      payload: buildRestartPayload(reason),
      capturedAt: new Date().toISOString()
    };
  }
};
