import axios from 'axios'
import { API_BASE_URL } from '@/constants'
import type {
  ApiResponse,
  ChatRequest,
  ChatResponse,
  SettingsPayload,
  SettingsResponse,
  ActivityWatchStatus,
  SummaryData,
  PraiseConfig,
  MilestoneResponse,
  ProfileResponse,
  FeedbackCreate,
  AggregatedUsage,
  NightlySummary,
} from '@/types/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

export const healthCheck = () => api.get<ApiResponse<{ status: string }>>('/health')

export const getSummary = (date: string) => api.get<ApiResponse<SummaryData>>(`/summary/${date}`)
export const getTodaySummary = () => api.get<ApiResponse<SummaryData>>('/summary/today')

export const sendChat = (data: ChatRequest) => api.post<ApiResponse<ChatResponse>>('/chat', data)

export async function* sendChatStream(data: ChatRequest): AsyncGenerator<string, void, unknown> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('No response body')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') {
          return
        }
        if (data.startsWith('[ERROR]')) {
          throw new Error(data.slice(7))
        }
        yield data
      }
    }
  }
}

export const getSettings = () => api.get<SettingsResponse>('/settings')
export const updateSettings = (data: SettingsPayload) =>
  api.put<ApiResponse<SettingsResponse>>('/settings', data)
export const getActivityWatchStatus = () =>
  api.get<ApiResponse<ActivityWatchStatus>>('/settings/activitywatch/status')
export const checkActivityWatch = (aw_server_url: string) =>
  api.post<ApiResponse<ActivityWatchStatus>>('/settings/activitywatch/check', { aw_server_url })
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

export const fetchAggregatedUsage = (date: string) =>
  api.get<ApiResponse<AggregatedUsage>>('/usage/aggregate', { params: { date } })

export const getLatestNightlySummary = () =>
  api.get<ApiResponse<NightlySummary | null>>('/usage/nightly-summary/latest')

export const markNightlySummaryRead = () =>
  api.post<ApiResponse<{ ok: boolean }>>('/usage/nightly-summary/mark-read')

export default api
