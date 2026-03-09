const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');
const express = require('express');
const http = require('http');

let server = null;
let win = null;

function getServePath() {
  const appPath = path.join(__dirname, 'app');
  const parentPath = path.join(__dirname, '..');
  if (fs.existsSync(appPath) && fs.existsSync(path.join(appPath, 'index.html'))) {
    return appPath;
  }
  return parentPath;
}

function createWindow() {
  const port = 8765;
  const servePath = getServePath();
  const expressApp = express();
  expressApp.use((req, res, next) => {
    res.setHeader('Accept-Ranges', 'bytes');
    next();
  });
  expressApp.use(express.static(servePath, { dotfiles: 'allow' }));
  server = http.createServer(expressApp);
  server.listen(port, () => {
    win = new BrowserWindow({
      width: 900,
      height: 800,
      title: 'ListenEnglish',
      webPreferences: { nodeIntegration: false, contextIsolation: true }
    });
    win.loadURL('http://localhost:' + port + '/');
    win.on('closed', () => { win = null; });
  });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => {
  if (server) server.close();
  app.quit();
});
