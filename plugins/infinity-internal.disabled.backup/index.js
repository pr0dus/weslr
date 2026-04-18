const capture = require('./hooks/capture');
const restore = require('./hooks/restore');

const DEFAULT_CONFIG = {
  captureEnabled: true,
  restoreEnabled: true,
};

function logFor(api) {
  const logger = api.logger;
  return {
    info: (msg, meta) => {
      if (logger && typeof logger.info === 'function') {
        logger.info(msg, meta);
      } else {
        console.log(msg, meta ?? '');
      }
    },
    warn: (msg, meta) => {
      if (logger && typeof logger.warn === 'function') {
        logger.warn(msg, meta);
      } else {
        console.warn(msg, meta ?? '');
      }
    },
    error: (msg, meta) => {
      if (logger && typeof logger.error === 'function') {
        logger.error(msg, meta);
      } else {
        console.error(msg, meta ?? '');
      }
    },
  };
}

function register(api) {
  const { info, warn, error } = logFor(api);
  const config = { ...DEFAULT_CONFIG, ...(api.pluginConfig || {}) };

  if (typeof api.on !== 'function') {
    warn('[infinity-internal] plugin API missing `on` lifecycle hook');
    return;
  }

  if (config.captureEnabled) {
    api.on('before_reset', async (event) => {
      try {
        const { filename } = await capture.captureCapsule({ reason: event?.reason || 'pre-reset' });
        info(`[infinity-internal] capsule recorded`, { filename });
      } catch (err) {
        error('[infinity-internal] capture failed', err.message || err);
      }
    });
    info('[infinity-internal] registered before_reset hook');
  }

  if (config.restoreEnabled) {
    const restoreHandler = async () => {
      try {
        const result = restore.attemptRestore();
        info('[infinity-internal] restore attempt result', result);
      } catch (err) {
        error('[infinity-internal] restore failed', err.message || err);
      }
    };
    api.on('session_start', restoreHandler);
    info('[infinity-internal] registered session_start hook');

    api.on('gateway_start', restoreHandler);
    info('[infinity-internal] registered gateway_start hook');
  }
}

const plugin = {
  id: 'infinity-internal',
  name: 'Infinity Internal',
  description: 'Deterministic restart capsule system for Termux/OpenClaw',
  version: '0.1.0',
  kind: 'workspace',
  configSchema: {
    type: 'object',
    additionalProperties: false,
    properties: {
      captureEnabled: { type: 'boolean', default: true },
      restoreEnabled: { type: 'boolean', default: true },
    },
  },
  register,
};

module.exports = plugin;
module.exports.default = plugin;
module.exports.register = register;
