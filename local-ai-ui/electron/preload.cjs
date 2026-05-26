const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('localAI', {
  platform: process.platform
});
