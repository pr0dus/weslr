const config = require("./config");
const { buildRestartPayload } = require("./capsule/utils");
const storage = require("./storage");

async function capture(details = {}) {
  const reason = details.reason || config.restartReason;
  const payload = buildRestartPayload(reason);
  storage.persist("latest-capsule", payload);
  return payload;
}

async function restore(record) {
  if (!record) {
    return { restored: false, reason: "no capsule provided" };
  }
  return { restored: true, record };
}

// ASSUMPTION: OpenClaw will invoke register(api) with its plugin API surface.
function register(api = {}) {
  const label = `[${config.pluginName}]`;
  if (api.logger && typeof api.logger.info === "function") {
    api.logger.info(`${label} staging restart capsule registered (SAFE STEP 1).`);
  } else {
    console.log(`${label} staging restart capsule registered (SAFE STEP 1).`);
  }
  return { capture, restore };
}

const plugin = {
  id: config.pluginName,
  name: "Infinity Internal",
  description: "Staged deterministic restart capsule (SAFE STEP 1).",
  configSchema: {
    type: "object",
    additionalProperties: false,
    properties: {
      enabled: {
        type: "boolean",
        default: true,
        description: "Reserved toggle for final deployment stage (currently inert)."
      }
    }
  },
  register
};

module.exports = plugin;
module.exports.default = plugin;
module.exports.register = register;
module.exports.capture = capture;
module.exports.restore = restore;
