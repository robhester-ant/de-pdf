const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess;

// Path to Python executable and script
const isProd = process.env.NODE_ENV === 'production';
const pythonPath = isProd 
  ? path.join(process.resourcesPath, 'python-server', 'python', 'python')
  : 'python3';
const scriptPath = isProd
  ? path.join(process.resourcesPath, 'python-server', 'app.py')
  : path.join(__dirname, 'python-server', 'app.py');

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    icon: path.join(__dirname, 'assets', 'icon.png')
  });

  // Load the app
  mainWindow.loadFile('index.html');

  // Open DevTools in development
  if (!isProd) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startPythonServer() {
  // Start Python backend
  console.log('Starting Python server...');
  
  const env = { ...process.env };
  env.FLASK_ENV = isProd ? 'production' : 'development';
  
  pythonProcess = spawn(pythonPath, [scriptPath], {
    env: env,
    stdio: ['ignore', 'pipe', 'pipe']
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
  });

  // Give the server time to start
  return new Promise((resolve) => {
    setTimeout(resolve, 2000);
  });
}

app.whenReady().then(async () => {
  await startPythonServer();
  createWindow();
});

app.on('window-all-closed', () => {
  // Kill Python process
  if (pythonProcess) {
    pythonProcess.kill();
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// Clean up Python process on exit
app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// Handle API key storage using Electron's storage
ipcMain.handle('save-api-key', async (event, apiKey) => {
  const configPath = path.join(app.getPath('userData'), 'config.json');
  try {
    fs.writeFileSync(configPath, JSON.stringify({ apiKey }));
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-api-key', async () => {
  const configPath = path.join(app.getPath('userData'), 'config.json');
  try {
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      return { hasKey: true, apiKey: config.apiKey };
    }
    return { hasKey: false };
  } catch (error) {
    return { hasKey: false };
  }
});

ipcMain.handle('reset-api-key', async () => {
  const configPath = path.join(app.getPath('userData'), 'config.json');
  try {
    if (fs.existsSync(configPath)) {
      fs.unlinkSync(configPath);
    }
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});