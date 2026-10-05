const fs = require('fs');
const path = require('path');

function loadEnv(filePath) {
  if (fs.existsSync(filePath)) {
    const lines = fs.readFileSync(filePath, 'utf8').split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIdx = trimmed.indexOf('=');
      if (eqIdx !== -1) {
        const key = trimmed.slice(0, eqIdx).trim();
        const val = trimmed.slice(eqIdx + 1).trim();
        if (!process.env[key]) {
          process.env[key] = val;
        }
      }
    }
  }
}

loadEnv(path.join(__dirname, '..', '.env'));
loadEnv(path.join(__dirname, '.env'));

const apiUrl = process.env.API_URL || 'https://api.reps-fitness.com';

const content = `window.__ENV__ = {
  API_URL: ${JSON.stringify(apiUrl)}
};
`;

const targetDir = path.join(__dirname, 'assets', 'js');
if (!fs.existsSync(targetDir)) {
  fs.mkdirSync(targetDir, { recursive: true });
}

const targetFile = path.join(targetDir, 'env.js');
fs.writeFileSync(targetFile, content, 'utf8');

console.log(`[build] Successfully generated assets/js/env.js with API_URL: ${apiUrl}`);
