const path = require('node:path');
const { app, BrowserWindow } = require('electron');

const { startBackendServices, stopBackendServices } = require('./backend.cjs');

const isDev = !app.isPackaged;
let mainWindow;
let backendChildren = [];

function resolveBackendRoot() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend');
  }

  return path.resolve(__dirname, '..', '..', 'local-ai-assistant');
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 700,
    backgroundColor: '#0d1117',
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  const startUrl = isDev
    ? 'http://127.0.0.1:5173'
    : `file://${path.join(__dirname, '..', 'dist', 'index.html')}`;

  mainWindow.loadURL(startUrl);
  mainWindow.once('ready-to-show', () => mainWindow.show());
}

app.whenReady().then(() => {
  backendChildren = startBackendServices({
    backendRoot: resolveBackendRoot(),
    onStdout: (message) => console.log(message.trim()),
    onStderr: (message) => console.error(message.trim())
  });

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopBackendServices(backendChildren);
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackendServices(backendChildren);
});
