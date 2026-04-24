import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTodaySummary, getSummary } from '@/api'
import type { SummaryData } from '@/types/api'
import { handleApiError } from '@/utils/error'
import { normalizeSummary } from '@/utils/validation'

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

function shouldUseCachedSummary(cached: SummaryData | null, incoming: SummaryData) {
  if (!cached) return false
  if (cached.date !== incoming.date) return false
  if (incoming.date !== getTodayDateString()) return false

  return (
    cached.total_hours > incoming.total_hours ||
    cached.work_hours > incoming.work_hours ||
    cached.entertainment_hours > incoming.entertainment_hours ||
    cached.other_hours > incoming.other_hours ||
    cached.top_apps.length > incoming.top_apps.length
  )
}

export const useSummaryStore = defineStore('summary', () => {
  const summary = ref<SummaryData | null>(loadCachedSummary())
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchTodaySummary() {
    loading.value = true
    error.value = null
    try {
      const response = await getTodaySummary()
      if (response.data.status === 'success' && response.data.data) {
        const nextSummary = normalizeSummary(response.data.data)
        const cachedSummary = loadCachedSummary()

        if (shouldUseCachedSummary(cachedSummary, nextSummary)) {
          summary.value = cachedSummary
        } else {
          summary.value = nextSummary
          saveCachedSummary(nextSummary)
        }
      } else {
        error.value = response.data.message || '获取总结失败'
      }
    } catch (e: unknown) {
      error.value = handleApiError(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary(date: string) {
    loading.value = true
    error.value = null
    try {
      const response = await getSummary(date)
      if (response.data.status === 'success' && response.data.data) {
        const nextSummary = normalizeSummary(response.data.data)
        summary.value = nextSummary

        if (nextSummary.date === getTodayDateString()) {
          saveCachedSummary(nextSummary)
        } else {
          clearCachedSummary()
        }
      } else {
        error.value = response.data.message || '获取总结失败'
      }
    } catch (e: unknown) {
      error.value = handleApiError(e)
    } finally {
      loading.value = false
    }
  }

  return { summary, loading, error, fetchTodaySummary, fetchSummary }
})
