export interface ApiResponse<T> {
  status: 'success'
  data: T
  message?: string | null
}

export interface AppUsage {
  name: string
  duration: number
  category: 'work' | 'entertainment' | 'other' | string
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
  openweather_api_key?: string
  openweather_location: string
  fish_audio_api_key?: string
  fish_audio_model: string
}

export interface SettingsResponse {
  aw_server_url: string
  data_masking: boolean
  doubao_api_key_set: boolean
  openweather_api_key_set: boolean
  openweather_location: string
  fish_audio_api_key_set: boolean
  fish_audio_model: string
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
  tts_voice: string
  tts_speed: number
  do_not_disturb_start: string
  do_not_disturb_end: string
  max_praises_per_day: number
  global_cooldown_minutes: number
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
