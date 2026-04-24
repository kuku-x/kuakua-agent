import { contextBridge, ipcRenderer } from 'electron'

// 暴露给渲染进程的API
contextBridge.exposeInMainWorld('electronAPI', {
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  // 后续可以添加更多IPC调用
})

// 类型声明
declare global {
  interface Window {
    electronAPI: {
      getAppVersion: () => Promise<string>
    }
  }
}