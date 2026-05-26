const fs = require('node:fs');
const path = require('node:path');

const uiRoot = path.resolve(__dirname, '..');
const backendSourceRoot = path.resolve(uiRoot, '..', 'local-ai-assistant');
const bundleRoot = path.join(uiRoot, '.bundle');
const stagedBackendRoot = path.join(bundleRoot, 'backend');
const venvRoot = path.join(backendSourceRoot, 'venv');
const pyvenvCfgPath = path.join(venvRoot, 'pyvenv.cfg');

function ensureExists(targetPath, label) {
  if (!fs.existsSync(targetPath)) {
    throw new Error(`${label} not found: ${targetPath}`);
  }
}

function recreateDir(targetPath) {
  fs.rmSync(targetPath, { recursive: true, force: true });
  fs.mkdirSync(targetPath, { recursive: true });
}

function copyPath(from, to) {
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.cpSync(from, to, { recursive: true, force: true });
}

function parsePyvenvCfg(filePath) {
  const configText = fs.readFileSync(filePath, 'utf8');
  const entries = {};

  for (const rawLine of configText.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || !line.includes('=')) {
      continue;
    }

    const [key, ...rest] = line.split('=');
    entries[key.trim()] = rest.join('=').trim();
  }

  return entries;
}

function main() {
  ensureExists(backendSourceRoot, 'Backend source root');
  ensureExists(venvRoot, 'Backend virtual environment');
  ensureExists(pyvenvCfgPath, 'pyvenv.cfg');

  const pyvenvCfg = parsePyvenvCfg(pyvenvCfgPath);
  const pythonHome = pyvenvCfg.home;
  if (!pythonHome) {
    throw new Error(`Could not resolve 'home' from ${pyvenvCfgPath}`);
  }

  ensureExists(pythonHome, 'Base Python home');
  ensureExists(path.join(pythonHome, 'python.exe'), 'Base python.exe');

  recreateDir(bundleRoot);
  recreateDir(stagedBackendRoot);

  for (const directoryName of ['src', 'config', 'models']) {
    copyPath(
      path.join(backendSourceRoot, directoryName),
      path.join(stagedBackendRoot, directoryName),
    );
  }

  for (const fileName of ['requirements.txt', '.env']) {
    const sourcePath = path.join(backendSourceRoot, fileName);
    if (fs.existsSync(sourcePath)) {
      copyPath(sourcePath, path.join(stagedBackendRoot, fileName));
    }
  }

  const stagedPythonRoot = path.join(stagedBackendRoot, 'python');
  copyPath(pythonHome, stagedPythonRoot);
  fs.rmSync(path.join(stagedPythonRoot, 'Lib', 'site-packages'), { recursive: true, force: true });

  copyPath(
    path.join(venvRoot, 'Lib', 'site-packages'),
    path.join(stagedPythonRoot, 'Lib', 'site-packages'),
  );

  const venvScriptsPath = path.join(venvRoot, 'Scripts');
  if (fs.existsSync(venvScriptsPath)) {
    copyPath(venvScriptsPath, path.join(stagedPythonRoot, 'Scripts'));
  }

  // Automate PyTorch DLL fix to prevent OSError 126
  const torchLibPath = path.join(stagedPythonRoot, 'Lib', 'site-packages', 'torch', 'lib');
  const sourceDll = path.join(torchLibPath, 'libiomp5md.dll');
  const targetDll = path.join(torchLibPath, 'libomp140.x86_64.dll');
  if (fs.existsSync(sourceDll)) {
    fs.copyFileSync(sourceDll, targetDll);
    console.log(`Copied ${sourceDll} to ${targetDll} to prevent PyTorch OSError 126`);
  }

  fs.writeFileSync(
    path.join(stagedBackendRoot, 'bundle-manifest.json'),
    JSON.stringify(
      {
        builtAt: new Date().toISOString(),
        pythonHome,
        backendSourceRoot,
      },
      null,
      2,
    ),
  );

  console.log(`Bundled backend staged at ${stagedBackendRoot}`);
}

main();
