const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { app } = require('electron');

const SERVICES = [
  { module: 'src.core.orchestrator:app', port: '8004' },
  { module: 'src.services.stt_service:app', port: '8001' },
  { module: 'src.services.tts_service:app', port: '8002' },
  { module: 'src.services.image_service:app', port: '8003' },
  { module: 'src.services.brain_router:app', port: '8000' }
];

function resolvePythonExecutable(backendRoot) {
  const bundledPython = path.join(backendRoot, 'python', 'python.exe');
  if (fs.existsSync(bundledPython)) {
    return bundledPython;
  }

  const venvPython = path.join(backendRoot, 'venv', 'Scripts', 'python.exe');
  if (fs.existsSync(venvPython)) {
    return venvPython;
  }

  return process.platform === 'win32' ? 'python' : 'python3';
}

function startBackendServices({ backendRoot, onStdout, onStderr }) {
  const pythonExecutable = resolvePythonExecutable(backendRoot);
  const runtimeRoot = app.isPackaged
    ? path.join(app.getPath('userData'), 'backend-runtime')
    : backendRoot;
  const pythonRoot = path.dirname(pythonExecutable);
  const scriptsRoot = path.join(pythonRoot, 'Scripts');

  fs.mkdirSync(runtimeRoot, { recursive: true });

  return SERVICES.map((service) => {
    const child = spawn(
      pythonExecutable,
      [
        '-m',
        'uvicorn',
        service.module,
        '--host',
        '127.0.0.1',
        '--port',
        service.port
      ],
      {
        cwd: backendRoot,
        env: {
          ...process.env,
          PATH: [
            pythonRoot,
            scriptsRoot,
            process.env.PATH || '',
          ].filter(Boolean).join(path.delimiter),
          PYTHONPATH: backendRoot,
          LOCAL_AI_BUNDLED_ROOT: backendRoot,
          LOCAL_AI_RUNTIME_ROOT: runtimeRoot,
          PYTORCH_CUDA_ALLOC_CONF: process.env.PYTORCH_CUDA_ALLOC_CONF || 'expandable_segments:True',
        },
        windowsHide: true
      }
    );

    child.stdout?.on('data', (chunk) => onStdout?.(`[${service.port}] ${chunk}`));
    child.stderr?.on('data', (chunk) => onStderr?.(`[${service.port}] ${chunk}`));

    return child;
  });
}

function stopBackendServices(children) {
  for (const child of children) {
    if (!child.killed) {
      child.kill();
    }
  }
}

module.exports = {
  startBackendServices,
  stopBackendServices
};
