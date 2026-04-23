import { computed } from 'vue'
import { useSummaryStore, type SummaryData } from '@/store/summary'

export function useSummary() {
  const store = useSummaryStore()

  const formattedSummary = computed(() => {
    if (!store.summary) return null

    const s = store.summary
    return {
      ...s,
      totalHours: `${s.total_hours}小时`,
      workHours: `${s.work_hours}小时`,
      entertainmentHours: `${s.entertainment_hours}小时`,
      otherHours: `${s.other_hours}小时`,
      focusScore: `${s.focus_score}分`,
    }
  })

  const hasSummary = computed(() => !!store.summary)

  return {
    summary: store.summary,
    formattedSummary,
    loading: store.loading,
    error: store.error,
    hasSummary,
    fetchTodaySummary: store.fetchTodaySummary,
    fetchSummary: store.fetchSummary,
  }
}