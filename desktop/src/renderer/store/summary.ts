import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTodaySummary, getSummary } from '@/api'
import type { SummaryData } from '@/types/api'
import { handleApiError } from '@/utils/error'
import { normalizeSummary } from '@/utils/validation'

export type { SummaryData }

export const useSummaryStore = defineStore('summary', () => {
  const summary = ref<SummaryData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchTodaySummary() {
    loading.value = true
    error.value = null
    try {
      const response = await getTodaySummary()
      if (response.data.status === 'success' && response.data.data) {
        summary.value = normalizeSummary(response.data.data)
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
        summary.value = normalizeSummary(response.data.data)
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

