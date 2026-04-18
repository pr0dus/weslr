// ASSUMPTION: The host calls restoreCapsule() with captured payloads.
module.exports = {
  async restoreCapsule(record) {
    if (!record) {
      return { restored: false, reason: "missing record" };
    }
    return {
      restored: true,
      restoredAt: new Date().toISOString(),
      record
    };
  }
};
