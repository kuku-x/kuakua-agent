import axios from 'axios'
import { API_BASE_URL } from '@/constants'
import type {
  ApiResponse,
  ChatRequest,
  ChatResponse,
  SettingsPayload,
  SettingsResponse,
  SummaryData,
  PraiseConfig,
  MilestoneResponse,
  ProfileResponse,
  FeedbackCreate,
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

export const getPraiseConfig = () => api.get<ApiResponse<PraiseConfig>>('/settings/praise')
export const updatePraiseConfig = (data: PraiseConfig) =>
  api.put<ApiResponse<PraiseConfig>>('/settings/praise', data)

export const getMilestones = () => api.get<ApiResponse<MilestoneResponse[]>>('/memory/milestones')
export const createMilestone = (data: { event_type: string; title: string; description?: string }) =>
  api.post<ApiResponse<MilestoneResponse>>('/memory/milestones', data)

export const getProfiles = () => api.get<ApiResponse<ProfileResponse[]>>('/memory/profiles')

export const submitFeedback = (data: FeedbackCreate) =>
  api.post<ApiResponse<{ recorded: boolean }>>('/feedback', data)

export default api
