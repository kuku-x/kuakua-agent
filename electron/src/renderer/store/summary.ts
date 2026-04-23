import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTodaySummary, getSummary } from '@/api'

export interface SummaryData {
  date: string
  total_hours: number
  work_hours: number
  entertainment_hours: number
  other_hours: number
  top_apps: Array<{ name: string; duration: number; category: string }>
  focus_score: number
  praise_text: string
  suggestions: string[]
}

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
        summary.value = response.data.data
      } else {
        error.value = response.data.message || '获取总结失败'
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '网络错误'
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
        summary.value = response.data.data
      } else {
        error.value = response.data.message || '获取总结失败'
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '网络错误'
    } finally {
      loading.value = false
    }
  }

  return { summary, loading, error, fetchTodaySummary, fetchSummary }
})