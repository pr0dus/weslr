// Test script to trace the exact import failure
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const extDir = '/data/data/com.termux/files/usr/lib/node_modules/openclaw/extensions/security.disabled';

console.log('Extension dir:', extDir);

try {
  // Try importing plugin.js with absolute path
  const plugin = await import('file://' + join(extDir, 'plugin.js'));
  console.log('PLUGIN IMPORT OK');
  console.log('default export keys:', Object.keys(plugin.default || {}));
} catch (e) {
  console.error('Direct import failed:', e.message);
  console.error('Code:', e.code);
}
