import { Notification, app, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'

let mainWindow: BrowserWindow | null = null
const DEV_SERVER_URL = process.env.ELECTRON_RENDERER_URL || 'http://localhost:5175'
const WINDOW_ICON_NAME = process.platform === 'win32' ? 'icon.ico' : 'icon.png'
const WINDOW_ICON_PATH = app.isPackaged
  ? join(process.resourcesPath, 'build', WINDOW_ICON_NAME)
  : join(app.getAppPath(), 'build', WINDOW_ICON_NAME)

// Some Windows environments may deny default cache directory access in dev mode.
if (!app.isPackaged) {
  const devUserDataPath = join(app.getPath('temp'), 'kuakua-agent-dev')
  app.setPath('userData', devUserDataPath)
}

if (process.platform === 'win32') {
  app.setAppUserModelId('com.kuakua.app')
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
    icon: WINDOW_ICON_PATH,
    title: '夸夸',
  })

  mainWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }))
  mainWindow.webContents.on('will-navigate', (event, url) => {
    const allowedUrl = app.isPackaged ? url.startsWith('file://') : url.startsWith(DEV_SERVER_URL)
    if (!allowedUrl) {
      event.preventDefault()
    }
  })

  if (!app.isPackaged) {
    mainWindow.loadURL(DEV_SERVER_URL)
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})

ipcMain.handle('get-app-version', () => {
  return app.getVersion()
})

ipcMain.handle('show-system-notification', (_event, payload: { title: string; body: string }) => {
  const notification = new Notification({
    title: payload.title,
    body: payload.body,
    silent: false,
  })

  notification.on('click', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) {
        mainWindow.restore()
      }
      mainWindow.show()
      mainWindow.focus()
      return
    }

    createWindow()
  })

  notification.show()
  return true
})
