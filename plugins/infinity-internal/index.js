const config = require("./config");
const { buildRestartPayload } = require("./capsule/utils");
const storage = require("./storage");
const { startAutoTrigger } = require("./auto-trigger");
const { persistHandoff, loadHandoff } = require("./bootstrap-handoff");

const CAPSULE_KEY = "latest-capsule";

async function capture(details = {}) {
  const reason = details.reason || config.restartReason;
  const payload = buildRestartPayload(reason);
  const result = storage.persist(CAPSULE_KEY, payload);
  if (!result.success) {
    // Log but don't crash — return payload anyway so OpenClaw can still function
    console.error(`[${config.pluginName}] storage persist failed: ${result.error}`);
  }
  // Also persist a compact bootstrap handoff for session-start injection
  persistHandoff(payload);
  return payload;
}

async function restore(record) {
  if (record) {
    return { restored: true, source: "passed_record", record };
  }
  // No record passed — try to load latest capsule from storage
  const loaded = storage.load(CAPSULE_KEY);
  if (loaded.found) {
    return { restored: true, source: "stored_latest", record: loaded.data };
  }
  return { restored: false, source: "none", reason: "no capsule stored" };
}

/**
 * Prepare bootstrap handoff for session-start injection.
 * Returns { found, data } with the compact handoff if one exists.
 * This is the exact function a session-start injector calls.
 */
function prepareBootstrap() {
  return loadHandoff();
}

// ASSUMPTION: OpenClaw will invoke register(api) with its plugin API surface.
function register(api = {}) {
  const label = `[${config.pluginName}]`;
  if (api.logger && typeof api.logger.info === "function") {
    api.logger.info(`${label} staging restart capsule registered (SAFE STEP 1).`);
  } else {
    console.log(`${label} staging restart capsule registered (SAFE STEP 1).`);
  }

  // Start silent auto-trigger loop
  const stopAuto = startAutoTrigger({
    capture,
    logger: api.logger || null,
    intervalMs: 2 * 60 * 1000 // check every 2 minutes
  });

  return { capture, restore, stopAuto, prepareBootstrap };
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
module.exports.prepareBootstrap = prepareBootstrap;
