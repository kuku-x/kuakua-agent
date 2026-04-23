import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
})

// 健康检查
export const healthCheck = () => api.get('/health')

// 每日总结
export const getSummary = (date: string) => api.get(`/summary/${date}`)
export const getTodaySummary = () => api.get('/summary/today')

// 聊天
export const sendChat = (data: { chat_id: string; message: string; user_context?: any }) =>
  api.post('/chat', data)

// 设置
export const getSettings = () => api.get('/settings')
export const updateSettings = (data: any) => api.put('/settings', data)
export const deleteAllData = () => api.delete('/settings/data')

export default api