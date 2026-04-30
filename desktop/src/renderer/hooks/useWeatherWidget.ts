import { ref } from 'vue'

export interface WeatherWidgetConfig {
  city: string
  latitude: string
  longitude: string
}

export interface WeatherWidgetData {
  city: string
  temperature: number
  apparentTemperature: number | null
  condition: string
  windText: string
  weatherCode: number | null
}

const WEATHER_WIDGET_KEY = 'kuakua:weather-widget'

const DEFAULT_CONFIG: WeatherWidgetConfig = {
  city: '深圳',
  latitude: '22.5431',
  longitude: '114.0579',
}

const WEATHER_CODE_MAP: Record<number, string> = {
  0: '晴天',
  1: '大致晴朗',
  2: '局部多云',
  3: '阴天',
  45: '有雾',
  48: '冻雾',
  51: '小毛毛雨',
  53: '毛毛雨',
  55: '强毛毛雨',
  56: '冻毛毛雨',
  57: '强冻毛毛雨',
  61: '小雨',
  63: '中雨',
  65: '大雨',
  66: '冻雨',
  67: '强冻雨',
  71: '小雪',
  73: '中雪',
  75: '大雪',
  77: '雪粒',
  80: '阵雨',
  81: '较强阵雨',
  82: '强阵雨',
  85: '阵雪',
  86: '强阵雪',
  95: '雷暴',
  96: '雷暴伴冰雹',
  99: '强雷暴伴冰雹',
}

function loadConfig(): WeatherWidgetConfig {
  try {
    const raw = window.localStorage.getItem(WEATHER_WIDGET_KEY)
    if (!raw) return DEFAULT_CONFIG

    const parsed = JSON.parse(raw) as Partial<WeatherWidgetConfig>
    return {
      city: typeof parsed.city === 'string' && parsed.city.trim() ? parsed.city.trim() : DEFAULT_CONFIG.city,
      latitude:
        typeof parsed.latitude === 'string' && parsed.latitude.trim()
          ? parsed.latitude.trim()
          : DEFAULT_CONFIG.latitude,
      longitude:
        typeof parsed.longitude === 'string' && parsed.longitude.trim()
          ? parsed.longitude.trim()
          : DEFAULT_CONFIG.longitude,
    }
  } catch {
    return DEFAULT_CONFIG
  }
}

function saveConfig(config: WeatherWidgetConfig) {
  window.localStorage.setItem(WEATHER_WIDGET_KEY, JSON.stringify(config))
}

function formatWind(speed: number | null) {
  if (speed === null) return '风况未知'
  if (speed < 6) return '微风'
  if (speed < 12) return '轻风'
  if (speed < 20) return '和风'
  if (speed < 29) return '强风'
  return '大风'
}

export function useWeatherWidget() {
  const config = ref<WeatherWidgetConfig>(loadConfig())
  const weather = ref<WeatherWidgetData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  let abortController: AbortController | null = null

  async function fetchWeather() {
    // 取消前一个未完成的请求
    abortController?.abort()
    abortController = new AbortController()

    loading.value = true
    error.value = null

    try {
      const latitude = Number(config.value.latitude)
      const longitude = Number(config.value.longitude)

      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        throw new Error('请输入有效的经纬度')
      }

      const response = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m&timezone=auto`,
        { signal: abortController.signal },
      )

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = (await response.json()) as {
        current?: {
          temperature_2m?: number
          apparent_temperature?: number
          weather_code?: number
          wind_speed_10m?: number
        }
      }

      const current = data.current
      if (!current || typeof current.temperature_2m !== 'number') {
        throw new Error('天气数据不完整')
      }

      weather.value = {
        city: config.value.city,
        temperature: Math.round(current.temperature_2m),
        apparentTemperature:
          typeof current.apparent_temperature === 'number' ? Math.round(current.apparent_temperature) : null,
        condition:
          typeof current.weather_code === 'number'
            ? WEATHER_CODE_MAP[current.weather_code] || '天气未知'
            : '天气未知',
        windText: formatWind(typeof current.wind_speed_10m === 'number' ? current.wind_speed_10m : null),
        weatherCode: typeof current.weather_code === 'number' ? current.weather_code : null,
      }
    } catch (e) {
      if (e instanceof Error && e.name === 'AbortError') {
        return // 请求被取消，不更新 UI
      }
      error.value = '天气数据加载失败'
    } finally {
      if (!abortController?.signal.aborted) {
        loading.value = false
      }
    }
  }

  function updateConfig(nextConfig: WeatherWidgetConfig) {
    config.value = {
      city: nextConfig.city.trim() || DEFAULT_CONFIG.city,
      latitude: nextConfig.latitude.trim(),
      longitude: nextConfig.longitude.trim(),
    }
    saveConfig(config.value)
  }

  return {
    config,
    weather,
    loading,
    error,
    fetchWeather,
    updateConfig,
  }
}
