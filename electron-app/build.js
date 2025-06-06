const builder = require('electron-builder');
const path = require('path');

// Build configuration
const config = {
  appId: 'com.yourcompany.document-to-markdown',
  productName: 'Document to Markdown',
  directories: {
    output: 'dist'
  },
  files: [
    'main.js',
    'preload.js',
    'index.html',
    'renderer.js',
    'python-server/**/*',
    '!python-server/**/__pycache__',
    '!python-server/**/*.pyc'
  ],
  extraResources: [
    {
      from: 'python-server',
      to: 'python-server',
      filter: ['**/*', '!**/__pycache__', '!**/*.pyc']
    }
  ],
  mac: {
    category: 'public.app-category.productivity',
    icon: 'build/icon.icns'
  },
  win: {
    target: 'nsis',
    icon: 'build/icon.ico'
  },
  linux: {
    target: 'AppImage',
    icon: 'build/icon.png'
  },
  nsis: {
    oneClick: false,
    allowToChangeInstallationDirectory: true
  }
};

// Build for current platform
builder.build({
  config: config,
  publish: 'never'
})
.then((result) => {
  console.log('Build complete:', result);
})
.catch((error) => {
  console.error('Build failed:', error);
  process.exit(1);
});