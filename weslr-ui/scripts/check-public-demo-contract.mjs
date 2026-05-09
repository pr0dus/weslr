import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const configPath = path.join(root, 'src', 'config.ts');
const appPath = path.join(root, 'src', 'App.tsx');

const config = fs.readFileSync(configPath, 'utf8');
const app = fs.readFileSync(appPath, 'utf8');

const requiredConfigSnippets = [
  "productMode: 'public_demo_readonly'",
  'memoryWrites: false',
  'fileUpload: false',
  'operatorPanel: false',
  'deploymentControls: false',
  'defaultValue: false',
];

const requiredAppSnippets = [
  '<DemoBanner />',
  'File upload is disabled in this read-only public demo',
  'This public demo is limited',
  'No memory writes · No execution · No operator controls · No file upload',
  'if (!config.features.operatorPanel || !visibility.visible) return null;',
];

const failures = [];

for (const snippet of requiredConfigSnippets) {
  if (!config.includes(snippet)) {
    failures.push(`config.ts missing required public-demo contract snippet: ${snippet}`);
  }
}

for (const snippet of requiredAppSnippets) {
  if (!app.includes(snippet)) {
    failures.push(`App.tsx missing required public-demo contract snippet: ${snippet}`);
  }
}

if (failures.length > 0) {
  console.error('WESLR public demo contract check failed:');
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log('WESLR public demo contract check OK');
