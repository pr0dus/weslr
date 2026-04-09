// capsule/schema.js - JSON schema and validation helpers for Infinity Capsules (v1)

const CAPSULE_SCHEMA = {
  type: 'object',
  required: ['version', 'timestamp', 'git', 'session', 'meta'],
  properties: {
    version: { const: 1, description: 'Capsule schema version' },
    timestamp: { type: 'string', format: 'date-time' },
    git: {
      type: 'object',
      required: ['repo', 'branch', 'commit', 'dirty'],
      properties: {
        repo: { type: 'string', pattern: '^/' },
        branch: { type: 'string' },
        commit: { type: 'string' },
        dirty: { type: 'boolean' },
      },
    },
    session: {
      type: 'object',
      required: ['activeFiles', 'pendingTests', 'latestTaskDescription'],
      properties: {
        activeFiles: {
          type: 'array',
          items: { type: 'string' },
        },
        pendingTests: {
          type: 'array',
          items: { type: 'string' },
        },
        latestTaskDescription: { type: 'string' },
      },
    },
    meta: {
      type: 'object',
      required: ['reason'],
      properties: {
        reason: { type: 'string', enum: ['pre-reset', 'ctx-overflow'] },
        parentId: { type: 'string' },
      },
    },
  },
};

function validateCapsule(capsule) {
  const { validate } = require('ajv')({ strict: false });
  const ajv = validateCapsule.ajv || new (require('ajv'))({ strict: false });
  validateCapsule.ajv = ajv;

  const valid = ajv.validate(CAPSULE_SCHEMA, capsule);
  if (!valid) {
    throw new Error(`Capsule validation failed: ${ajv.errorsText(ajv.errors)}`);
  }
}

module.exports = { CAPSULE_SCHEMA, validateCapsule };
