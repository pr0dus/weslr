const { existsSync, mkdirSync, writeFileSync, readFileSync } = require("fs");
const { resolve } = require("path");

const storageDir = resolve(__dirname, "data");
if (!existsSync(storageDir)) {
  mkdirSync(storageDir, { recursive: true });
}

function persist(name, payload) {
  const filePath = resolve(storageDir, `${name}.json`);
  writeFileSync(filePath, JSON.stringify(payload, null, 2), "utf8");
}

function read(name) {
  const filePath = resolve(storageDir, `${name}.json`);
  if (!existsSync(filePath)) {
    return null;
  }
  try {
    return JSON.parse(readFileSync(filePath, "utf8"));
  } catch (error) {
    return null;
  }
}

module.exports = {
  storageDir,
  persist,
  read
};
