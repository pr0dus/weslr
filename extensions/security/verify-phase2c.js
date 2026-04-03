#!/usr/bin/env node
import fs from 'node:fs/promises';
import fsSync from 'node:fs';
import { initGatewaySecurityWrappers, wrapFsPromisesWriteFile, isSecurityEnabled } from "./gateway-wrappers.js";
import { SecurityAPI } from "../../dist/security/index.js";

async function setup() {
  // Initialize security
  await SecurityAPI.Core.init();
  console.log('Security initialized:', isSecurityEnabled());
  
  // Start runtime wrappers
  initGatewaySecurityWrappers();
  
  console.log('\n=== TEST 1: Benign write (should succeed) ===');
  const benignPath = '.security-test/benign.txt';
  const benignContent = 'Hello, benign test!';
  try {
    await fs.writeFile(benignPath, benignContent);
    const read = await fs.readFile(benignPath, 'utf8');
    console.log('Benign write:', read === benignContent ? 'SUCCESS' : 'CONTENT MISMATCH');
  } catch (err) {
    console.log('Benign write ERROR:', err.message);
  }
  
  console.log('\n=== TEST 2: Malicious write (should be blocked) ===');
  const maliciousPath = '.security-test/malicious.txt';
  const maliciousContent = "const { exec } = require('child_process'); exec('rm -rf /');";
  try {
    await fs.writeFile(maliciousPath, maliciousContent);
    console.log('Malicious write: FAILED - should have been blocked');
  } catch (err) {
    console.log('Malicious write:', err.message.includes('Security: write blocked') ? 'BLOCKED (CORRECT)' : 'BLOCKED (WRONG REASON): ' + err.message);
  }
  
  console.log('\n=== TEST 3: Verify audit log ===');
  const auditLog = await fsSync.promises.readFile('.openclaw/audit/logs/pre_write_blocked.log', 'utf8').catch(() => '');
  console.log('Audit entries:', auditLog ? auditLog.split('\n').filter(l => l).length : 0);
  
  console.log('\n=== TEST 4: With security disabled ===');
  process.env.OPENCLAW_SECURITY_ENABLED = '';
  const originalWriteFile = (await import('node:fs/promises')).writeFile;
  const testPath = '.security-test/override.txt';
  await fs.writeFile(testPath, 'Override test');
  const result = await fs.readFile(testPath, 'utf8');
  console.log('Override write:', result === 'Override test' ? 'SUCCESS' : 'FAILED');
}

setup().catch(console.error);
