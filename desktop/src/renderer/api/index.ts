import axios from 'axios'
import { API_BASE_URL } from '@/constants'
import type {
  ApiResponse,
  ChatRequest,
  ChatResponse,
  SettingsPayload,
  SettingsResponse,
  SummaryData,
} from '@/types/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

export const healthCheck = () => api.get<ApiResponse<{ status: string }>>('/health')

export const getSummary = (date: string) => api.get<ApiResponse<SummaryData>>(`/summary/${date}`)
export const getTodaySummary = () => api.get<ApiResponse<SummaryData>>('/summary/today')

export const sendChat = (data: ChatRequest) => api.post<ApiResponse<ChatResponse>>('/chat', data)

export const getSettings = () => api.get<SettingsResponse>('/settings')
export const updateSettings = (data: SettingsPayload) =>
  api.put<ApiResponse<SettingsResponse>>('/settings', data)
export const deleteAllData = () => api.delete<ApiResponse<{ deleted: boolean }>>('/settings/data')

export default api
