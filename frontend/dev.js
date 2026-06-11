const { spawn } = require('child_process');
const path = require('path');

console.log("==================================================");
console.log("Latent Regime Discovery: Unified Dev Environment");
console.log("==================================================");

const isWindows = process.platform === 'win32';

// 1. Resolve paths
const rootDir = path.resolve(__dirname, '..');
const pythonExe = isWindows 
  ? path.join(rootDir, '.venv', 'Scripts', 'python.exe')
  : path.join(rootDir, '.venv', 'bin', 'python');

const serverScript = path.join(rootDir, 'src', 'api', 'server.py');

console.log(`[Backend] Python Executable: ${pythonExe}`);
console.log(`[Backend] Server Script: ${serverScript}`);

// 2. Start the Python backend process
console.log("\n[System] Starting Python Backend...");
const backend = spawn(pythonExe, [serverScript], {
  cwd: rootDir, // Run from root directory to keep imports intact
  stdio: 'inherit'
});

// 3. Start the Next.js frontend process
console.log("[System] Starting Next.js Frontend...");
// We spawn next dev via npx/npm
const frontend = spawn(isWindows ? 'npx.cmd' : 'npx', ['next', 'dev'], {
  cwd: __dirname, // Run from frontend directory
  stdio: 'inherit',
  shell: true
});

// 4. Handle process termination
let isCleaningUp = false;
const cleanup = () => {
  if (isCleaningUp) return;
  isCleaningUp = true;
  console.log("\n[System] Shutting down services...");
  
  try {
    backend.kill('SIGTERM');
  } catch (e) {}
  
  try {
    frontend.kill('SIGTERM');
  } catch (e) {}
  
  process.exit();
};

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

backend.on('close', (code) => {
  if (code !== 0 && code !== null) {
    console.log(`[Backend] Process exited unexpectedly with code ${code}`);
  } else {
    console.log(`[Backend] Process exited`);
  }
  cleanup();
});

frontend.on('close', (code) => {
  if (code !== 0 && code !== null) {
    console.log(`[Frontend] Process exited unexpectedly with code ${code}`);
  } else {
    console.log(`[Frontend] Process exited`);
  }
  cleanup();
});
