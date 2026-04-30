import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchAggregatedUsage, getTodaySummary, getSummary } from '@/api'
import type { AggregatedUsage, SummaryData } from '@/types/api'
import { handleApiError } from '@/utils/error'
import { normalizeAppName, normalizeSummary } from '@/utils/validation'

export type { SummaryData }

const SUMMARY_CACHE_KEY = 'kuakua:summary:daily'

function getTodayDateString() {
  return new Date().toISOString().slice(0, 10)
}

function loadCachedSummary(): SummaryData | null {
  try {
    const raw = window.localStorage.getItem(SUMMARY_CACHE_KEY)
    if (!raw) return null

    const normalized = normalizeSummary(JSON.parse(raw) as SummaryData)
    if (normalized.date !== getTodayDateString()) {
      window.localStorage.removeItem(SUMMARY_CACHE_KEY)
      return null
    }

    return normalized
  } catch {
    window.localStorage.removeItem(SUMMARY_CACHE_KEY)
    return null
  }
}

function saveCachedSummary(data: SummaryData) {
  window.localStorage.setItem(SUMMARY_CACHE_KEY, JSON.stringify(data))
}

function clearCachedSummary() {
  window.localStorage.removeItem(SUMMARY_CACHE_KEY)
}

function normalizeComputerAppName(name: string): string {
  return normalizeAppName(name.replace(/\.exe$/i, ''))
}

function shouldUseCachedSummary(cached: SummaryData | null, incoming: SummaryData) {
  if (!cached) return false
  if (cached.date !== incoming.date) return false
  if (incoming.date !== getTodayDateString()) return false
  // Only fall back to cache when the fresh response is clearly empty / errored
  return incoming.total_hours <= 0 && incoming.top_apps.length === 0
}

function mergeSummaryWithAggregate(summary: SummaryData, aggregate: AggregatedUsage): SummaryData {
  const topAppsMap = new Map<string, { name: string; seconds: number; category: string }>()

  const computerApps = aggregate.computer?.top_apps ?? []
  const phoneApps = aggregate.phone?.top_apps ?? []

  for (const app of computerApps) {
    const rawName = app.name ?? (app as any).Name ?? ''
    const appName = normalizeComputerAppName(rawName)
    if (!appName) continue

    const seconds = app.seconds ?? (app as any).duration ?? (app.hours ?? 0) * 3600
    const category = app.category ?? 'other'
    const current = topAppsMap.get(appName)
    if (current) {
      current.seconds += seconds
      if (current.category === 'other' && category !== 'other') {
        current.category = category
      }
    } else {
      topAppsMap.set(appName, {
        name: appName,
        seconds,
        category,
      })
    }
  }

  for (const app of phoneApps) {
    // Handle both 'name' and 'Name' field from backend
    const appName = normalizeAppName(app.name ?? (app as any).Name ?? '')
    if (!appName) continue

    const seconds = app.seconds ?? (app as any).duration ?? (app.hours ?? 0) * 3600
    const category = app.category ?? 'other'
    const current = topAppsMap.get(appName)
    if (current) {
      current.seconds += seconds
      if (current.category === 'other' && category !== 'other') {
        current.category = category
      }
    } else {
      topAppsMap.set(appName, {
        name: appName,
        seconds,
        category,
      })
    }
  }

  const combinedTopApps = Array.from(topAppsMap.values())
    .sort((a, b) => b.seconds - a.seconds)
    .slice(0, 10)
    .map((app) => ({
      name: app.name,
      duration: Math.round((app.seconds / 3600) * 10) / 10,
      category: app.category,
    }))

  const computerTotal = aggregate.computer?.total_hours ?? 0
  const phoneTotal = aggregate.phone?.total_hours ?? 0
  // Use summary data as primary; aggregate only adds phone breakdown.
  // max() prevents aggregate from shrinking already-correct summary values.
  const combinedTotal = Math.max(
    summary.total_hours,
    aggregate.combined?.total_hours ?? (computerTotal + phoneTotal),
  )
  const workHours = Math.max(summary.work_hours, aggregate.combined?.work_hours ?? 0)
  const entertainmentHours = Math.max(summary.entertainment_hours, aggregate.combined?.entertainment_hours ?? 0)
  const otherHours = Math.max(0, combinedTotal - workHours - entertainmentHours)

  return {
    ...summary,
    total_hours: combinedTotal,
    work_hours: workHours,
    entertainment_hours: entertainmentHours,
    other_hours: Math.round(otherHours * 10) / 10,
    top_apps: combinedTopApps,
    computer_hours: computerTotal,
    phone_hours: phoneTotal,
    phone_device_ids: aggregate.phone?.device_ids ?? summary.phone_device_ids ?? [],
    computer_top_apps: computerApps.map((app) => ({
      name: normalizeComputerAppName((app as any).name ?? (app as any).Name ?? ''),
      duration: (app as any).hours ?? ((app as any).seconds ?? (app as any).duration ?? 0) / 3600,
      category: (app as any).category ?? 'other',
    })).filter(app => app.name),
    phone_top_apps: phoneApps.map((app) => ({
      name: normalizeAppName((app as any).name ?? (app as any).Name ?? ''),
      duration: (app as any).hours ?? ((app as any).seconds ?? (app as any).duration ?? 0) / 3600,
      category: (app as any).category ?? 'other',
    })).filter(app => app.name),
  }
}

export const useSummaryStore = defineStore('summary', () => {
  const summary = ref<SummaryData | null>(loadCachedSummary())
  const loading = ref(false)
  const error = ref<string | null>(null)
  // 请求去重：缓存正在飞行中的 Promise，防止并发重复请求
  let fetchTodayPromise: Promise<void> | null = null

  async function fetchTodaySummary() {
    // 如果已有请求在进行中，直接返回同一个 Promise
    if (fetchTodayPromise) {
      return fetchTodayPromise
    }
    if (loading.value) return

    loading.value = true
    error.value = null
    fetchTodayPromise = (async () => {
      try {
        const [summaryResponse, aggregateResponse] = await Promise.all([
          getTodaySummary(),
          fetchAggregatedUsage(getTodayDateString()),
        ])

        if (summaryResponse.data.status === 'success' && summaryResponse.data.data) {
          const baseSummary = normalizeSummary(summaryResponse.data.data)
          const nextSummary =
            aggregateResponse.data.status === 'success' && aggregateResponse.data.data
              ? mergeSummaryWithAggregate(baseSummary, aggregateResponse.data.data)
              : baseSummary
          const cachedSummary = loadCachedSummary()

          if (shouldUseCachedSummary(cachedSummary, nextSummary)) {
            summary.value = cachedSummary
          } else {
            summary.value = nextSummary
            saveCachedSummary(nextSummary)
          }
        } else {
          error.value = summaryResponse.data.message || '获取总结失败'
        }
      } catch (e: unknown) {
        error.value = handleApiError(e)
      } finally {
        loading.value = false
        fetchTodayPromise = null
      }
    })()
    return fetchTodayPromise
  }

  async function fetchSummary(date: string) {
    loading.value = true
    error.value = null
    try {
      const [summaryResponse, aggregateResponse] = await Promise.all([
        getSummary(date),
        fetchAggregatedUsage(date),
      ])

      if (summaryResponse.data.status === 'success' && summaryResponse.data.data) {
        const baseSummary = normalizeSummary(summaryResponse.data.data)
        const nextSummary =
          aggregateResponse.data.status === 'success' && aggregateResponse.data.data
            ? mergeSummaryWithAggregate(baseSummary, aggregateResponse.data.data)
            : baseSummary
        summary.value = nextSummary

        if (nextSummary.date === getTodayDateString()) {
          saveCachedSummary(nextSummary)
        } else {
          clearCachedSummary()
        }
      } else {
        error.value = summaryResponse.data.message || '获取总结失败'
      }
    } catch (e: unknown) {
      error.value = handleApiError(e)
    } finally {
      loading.value = false
    }
  }

  return { summary, loading, error, fetchTodaySummary, fetchSummary }
})
