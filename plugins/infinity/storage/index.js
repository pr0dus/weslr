// storage/index.js - CRUD on .openclaw/capsules/

const fs = require('./fs');

function save(capsule) {
  // Generate stable filename with id from capsule.meta.id
  const filename = capsule.meta.id + '.json';
  fs.saveCapsule(filename, capsule);
  return filename;
}

function load(filename) {
  return fs.loadCapsule(filename);
}

function list() {
  return fs.listCapsules();
}

function remove(filename) {
  return fs.deleteCapsule(filename);
}

function getLatest() {
  const files = fs.listCapsules();
  if (files.length === 0) return null;
  // Sort by timestamp embedded in filename
  files.sort().reverse();
  return load(files[0]);
}

module.exports = {
  save,
  load,
  list,
  remove,
  getLatest,
};
