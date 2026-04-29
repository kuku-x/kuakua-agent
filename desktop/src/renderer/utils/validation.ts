import type { AppUsage, ChatResponse, SettingsResponse, SummaryData } from '@/types/api'

const APP_NAME_MAP: Record<string, string> = {
  msedge: 'Microsoft Edge',
  chrome: 'Google Chrome',
  firefox: 'Mozilla Firefox',
  code: 'Visual Studio Code',
  explorer: '文件资源管理器',
  electron: 'Electron',
  obsidian: 'Obsidian',
  qq: 'QQ',
  wechat: '微信',
  dingtalk: '钉钉',
  feishu: '飞书',
  wps: 'WPS Office',
  word: 'Microsoft Word',
  excel: 'Microsoft Excel',
  powerpoint: 'Microsoft PowerPoint',
  outlook: 'Microsoft Outlook',
  terminal: 'Windows Terminal',
  powershell: 'PowerShell',
  cmd: '命令提示符',
  pycharm: 'PyCharm',
  idea: 'IntelliJ IDEA',
  webstorm: 'WebStorm',
  goland: 'GoLand',
  rider: 'JetBrains Rider',
  clion: 'CLion',
  datagrip: 'DataGrip',
  notion: 'Notion',
  slack: 'Slack',
  teams: 'Microsoft Teams',
  zoom: 'Zoom',
  discord: 'Discord',
  spotify: 'Spotify',
  music: '网易云音乐',
  qqmusic: 'QQ音乐',
  netease: '网易云音乐',
  bilibili: '哔哩哔哩',
  douyin: '抖音',
  youtube: 'YouTube',
  netflix: 'Netflix',
  steam: 'Steam',
  postman: 'Postman',
  figma: 'Figma',
  github: 'GitHub',
  git: 'Git',
  cursor: 'Cursor',
  arc: 'Arc Browser',
  'com.xingin.xhs': '小红书',
  'com.taobao.idlefish': '闲鱼',
  'com.larus.nova': 'Nova Launcher',
  'com.tencent.mm': '微信',
  'com.tencent.mobileqq': 'QQ',
  'com.ss.android.ugc.aweme': '抖音',
  'com.eg.android.alipaygphone': '支付宝',
  'tv.danmaku.bili': '哔哩哔哩',
  'com.sankuai.meituan': '美团',
  'com.xunmeng.pinduoduo': '拼多多',
  'com.jingdong.app.mall': '京东',
  'com.netease.cloudmusic': '网易云音乐',
  'com.tencent.qqmusic': 'QQ音乐',
}

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

export function normalizeAppName(value: string): string {
  const trimmed = value.trim()
  if (!trimmed) return ''

  const key = trimmed.toLowerCase().endsWith('.exe') ? trimmed.slice(0, -4).toLowerCase() : trimmed.toLowerCase()
  return APP_NAME_MAP[key] || (trimmed.toLowerCase().endsWith('.exe') ? trimmed.slice(0, -4) : trimmed)
}

function normalizeAppUsage(value: unknown): AppUsage | null {
  if (!value || typeof value !== 'object') return null
  const item = value as Record<string, unknown>
  const name = normalizeAppName(asString(item.name))
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
    computer_hours: asNumber(item.computer_hours),
    phone_hours: asNumber(item.phone_hours),
    phone_device_ids: asStringArray(item.phone_device_ids),
    computer_top_apps: Array.isArray(item.computer_top_apps)
      ? item.computer_top_apps.map(normalizeAppUsage).filter((app): app is AppUsage => app !== null)
      : [],
    phone_top_apps: Array.isArray(item.phone_top_apps)
      ? item.phone_top_apps.map(normalizeAppUsage).filter((app): app is AppUsage => app !== null)
      : [],
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
    openweather_location: asString(item.openweather_location, 'Shanghai,CN'),
    nightly_summary_enable: Boolean(item.nightly_summary_enable),
    nightly_summary_time: asString(item.nightly_summary_time, '21:30'),
  }
}
