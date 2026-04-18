import { SecurityAPI, SecureFS, SecureImport } from "./index.js";

const securityPlugin = {
  id: "security",
  name: "Security Extension",
  description: "Runtime security hooks for file writes and dynamic imports",
  configSchema: {
    type: "object",
    additionalProperties: false,
    properties: {}
  },
  register(api) {
    // Security API is available through module exports.
    // No runtime registration required yet for safe loading validation.
  }
};

export default securityPlugin;
