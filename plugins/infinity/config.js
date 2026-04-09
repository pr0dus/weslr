// config.js - Global settings for Infinity Plugin

const config = {
  // Retention: 2 hours in milliseconds
  retentionMs: 2 * 60 * 60 * 1000,
  // Auto-capture enabled (for pre-reset, /new, overflow)
  autoCaptureEnabled: true,
  // Auto-restore enabled (on init, silent)
  autoRestoreEnabled: true,
  // Strict missing-files check (v1: true = skip if any file missing)
  strictMissingFiles: true,
  // Log level: 'error', 'warn', 'info', 'debug'
  logLevel: 'info',
};

module.exports = config;
