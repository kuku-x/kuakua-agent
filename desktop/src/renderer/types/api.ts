export interface ApiResponse<T> {
  status: 'success'
  data: T
  message?: string | null
}

export interface AppUsage {
  name: string
  duration: number
  category: 'work' | 'entertainment' | 'other' | string
  // 后端返回的额外字段
  seconds?: number
  hours?: number
  Name?: string  // 后端用大写
}

export interface AggregatedAppUsage {
  name: string
  duration: number
  seconds: number
  hours: number
  category: string
  Name?: string
}

export interface DeviceUsage {
  total_seconds: number
  total_hours: number
  top_apps: AggregatedAppUsage[]
  device_ids?: string[]
}

export interface CombinedUsage {
  total_hours: number
  work_hours: number
  entertainment_hours: number
}

export interface AggregatedUsage {
  date: string
  computer: DeviceUsage
  phone: DeviceUsage
  combined: CombinedUsage
}

export interface SummaryData {
  date: string
  total_hours: number
  work_hours: number
  entertainment_hours: number
  other_hours: number
  top_apps: AppUsage[]
  focus_score: number
  praise_text: string
  suggestions: string[]
  computer_hours?: number
  phone_hours?: number
  phone_device_ids?: string[]
  computer_top_apps?: AppUsage[]
  phone_top_apps?: AppUsage[]
}

export interface ChatContext {
  total_hours?: number
  work_hours?: number
  entertainment_hours?: number
}

export interface ChatRequest {
  chat_id: string
  message: string
  user_context?: ChatContext
}

export interface ChatResponse {
  reply: string
}

export interface SettingsPayload {
  aw_server_url: string
  data_masking: boolean
  doubao_api_key?: string
  fish_audio_api_key?: string
}

export interface SettingsResponse {
  aw_server_url: string
  data_masking: boolean
  doubao_api_key_set: boolean
  fish_audio_api_key_set: boolean
}

export interface NightlySummary {
  date: string
  content: string
  unread: boolean
}

export interface ActivityWatchStatus {
  aw_server_url: string
  connected: boolean
  bucket_count: number
  message: string
}

export interface PraiseConfig {
  praise_auto_enable: boolean
  tts_enable: boolean
  tts_engine: 'kokoro' | 'fish_audio'
  kokoro_voice: string
  kokoro_model_path: string
  fish_audio_voice_id: string
  tts_speed: number
  do_not_disturb_start: string
  do_not_disturb_end: string
  nightly_summary_enable: boolean
  nightly_summary_time: string
}

export interface TtsVoice {
  id: string
  title: string
  tags?: string[]
}

export interface MilestoneResponse {
  id: number
  event_type: string
  title: string
  description: string | null
  occurred_at: string
  is_recalled: boolean
}

export interface ProfileResponse {
  scene: string
  weight: number
  keywords: string[]
}

export interface FeedbackCreate {
  praise_id: number
  reaction: 'liked' | 'disliked' | 'neutral'
}

// ============ 手机使用数据类型 ============

export interface PhoneUsageEntry {
  date: string
  app_name: string
  package_name: string
  duration_seconds: number
  last_used: string | null
  event_count: number
}

export interface PhoneSyncRequest {
  device_id: string
  device_name: string
  entries: PhoneUsageEntry[]
  sync_time: string
}

export interface PhoneSyncResponse {
  success: boolean
  synced_count: number
  message: string
}
