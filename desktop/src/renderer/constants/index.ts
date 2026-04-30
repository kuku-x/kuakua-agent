// API 配置，可通过桌面端 `desktop/.env` 覆盖。
export const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8001/api'

// 错误消息
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络连接失败，请检查后端服务是否启动',
  ACTIVITYWATCH_NOT_RUNNING: 'ActivityWatch 未运行，请先启动',
  API_KEY_NOT_SET: '请先在设置中配置 API 密钥',
  UNKNOWN_ERROR: '发生未知错误，请稍后重试',
}

// 分类关键词
export const APP_CATEGORIES = {
  work: ['code', 'idea', 'webstorm', 'pycharm', 'vscode', 'word', 'excel', 'ppt', 'pdf', 'notion', 'obsidian'],
  entertainment: ['youtube', 'netflix', 'game', 'steam', 'netease', 'music', 'spotify', 'bili'],
}
