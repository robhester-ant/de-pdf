const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  saveApiKey: (apiKey) => ipcRenderer.invoke('save-api-key', apiKey),
  getApiKey: () => ipcRenderer.invoke('get-api-key'),
  resetApiKey: () => ipcRenderer.invoke('reset-api-key')
});