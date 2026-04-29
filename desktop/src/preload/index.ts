import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  showSystemNotification: (payload: { title: string; body: string }) =>
    ipcRenderer.invoke('show-system-notification', payload),
})

declare global {
  interface Window {
    electronAPI: {
      getAppVersion: () => Promise<string>
      showSystemNotification: (payload: { title: string; body: string }) => Promise<boolean>
    }
  }
}
