import type { AppUsage, ChatResponse, SettingsResponse, SummaryData } from '@/types/api'

function asNumber(value: unknown, fallback = 0): number {
  const numberValue = Number(value)
  return Number.isFinite(numberValue) && numberValue >= 0 ? numberValue : fallback
}

function asString(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []
}

function normalizeAppUsage(value: unknown): AppUsage | null {
  if (!value || typeof value !== 'object') return null
  const item = value as Record<string, unknown>
  const name = asString(item.name).trim()
  if (!name) return null

  return {
    name,
    duration: asNumber(item.duration),
    category: asString(item.category, 'other') || 'other',
  }
}

export function normalizeSummary(value: unknown): SummaryData {
  if (!value || typeof value !== 'object') {
    throw new Error('摘要数据格式错误')
  }

  const item = value as Record<string, unknown>
  const topApps = Array.isArray(item.top_apps)
    ? item.top_apps.map(normalizeAppUsage).filter((app): app is AppUsage => app !== null)
    : []

  return {
    date: asString(item.date, new Date().toISOString().slice(0, 10)),
    total_hours: asNumber(item.total_hours),
    work_hours: asNumber(item.work_hours),
    entertainment_hours: asNumber(item.entertainment_hours),
    other_hours: asNumber(item.other_hours),
    top_apps: topApps,
    focus_score: Math.min(100, asNumber(item.focus_score)),
    praise_text: asString(item.praise_text, '暂无总结'),
    suggestions: asStringArray(item.suggestions),
  }
}

export function normalizeChatResponse(value: unknown): ChatResponse {
  if (!value || typeof value !== 'object') {
    throw new Error('聊天响应格式错误')
  }

  const item = value as Record<string, unknown>
  const reply = asString(item.reply).trim()
  if (!reply) {
    throw new Error('聊天响应缺少回复内容')
  }
  return { reply }
}

export function normalizeSettings(value: unknown): SettingsResponse {
  if (!value || typeof value !== 'object') {
    throw new Error('设置数据格式错误')
  }

  const item = value as Record<string, unknown>
  return {
    aw_server_url: asString(item.aw_server_url, 'http://127.0.0.1:5600'),
    data_masking: Boolean(item.data_masking),
    doubao_api_key_set: Boolean(item.doubao_api_key_set),
    openweather_api_key_set: Boolean(item.openweather_api_key_set),
    openweather_location: asString(item.openweather_location, 'Shanghai,CN'),
    fish_audio_api_key_set: Boolean(item.fish_audio_api_key_set),
    fish_audio_model: asString(item.fish_audio_model, 's2-pro'),
  }
}
