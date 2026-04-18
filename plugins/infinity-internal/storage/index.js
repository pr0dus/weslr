const fsStorage = require("./fs");

module.exports = {
  persist(name, payload) {
    fsStorage.persist(name, payload);
  },
  load(name) {
    return fsStorage.read(name);
  }
};
