const Ajv = require('ajv');

const CAPSULE_SCHEMA = {
  type: 'object',
  required: ['version', 'timestamp', 'git', 'session', 'anchor', 'meta'],
  properties: {
    version: { const: 1 },
    timestamp: { type: 'string', format: 'date-time' },
    git: {
      type: 'object',
      required: ['repo', 'branch', 'commit'],
      properties: {
        repo: { type: 'string' },
        branch: { type: 'string' },
        commit: { type: 'string' },
      },
    },
    session: {
      type: 'object',
      required: ['activeFiles', 'pendingTests'],
      properties: {
        activeFiles: {
          type: 'array',
          items: { type: 'string' },
        },
        pendingTests: {
          type: 'array',
          items: { type: 'string' },
        },
      },
    },
    anchor: {
      type: 'object',
      required: ['task', 'note'],
      properties: {
        task: { type: 'string' },
        note: { type: 'string' },
      },
    },
    meta: {
      type: 'object',
      required: ['id', 'reason'],
      properties: {
        id: { type: 'string' },
        reason: { type: 'string' },
      },
    },
  },
};

const ajv = new Ajv({ strict: false });

function validateCapsule(capsule) {
  const valid = ajv.validate(CAPSULE_SCHEMA, capsule);
  if (!valid) {
    throw new Error(`capsule validation failed: ${ajv.errorsText(ajv.errors)}`);
  }
}

module.exports = {
  CAPSULE_SCHEMA,
  validateCapsule,
};
