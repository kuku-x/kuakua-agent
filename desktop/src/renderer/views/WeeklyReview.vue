<template>
  <section class="weekly-page">
    <KuCard padding="lg" class="weekly-page__hero">
      <div>
        <p class="weekly-page__eyebrow">Weekly Review</p>
        <h2>{{ stats.week_start ? `${stats.week_start} → ${stats.week_end}` : '本周复盘' }}</h2>
        <p v-if="stats.day_count" class="weekly-page__meta">{{ stats.day_count }} 天数据</p>
      </div>
      <KuButton size="sm" variant="ghost" :loading="loading" @click="loadReview">
        刷新
      </KuButton>
    </KuCard>

    <KuCard v-if="loading" padding="lg" class="weekly-page__content">
      <KuSpinner text="正在生成周报..." />
    </KuCard>

    <KuCard v-else-if="error" padding="lg" class="weekly-page__content">
      <p class="weekly-page__error">{{ error }}</p>
      <KuButton size="sm" @click="loadReview">重试</KuButton>
    </KuCard>

    <template v-else-if="review">
      <!-- 数据概览 -->
      <div class="weekly-page__stats">
        <KuCard padding="md" class="weekly-page__stat">
          <span class="weekly-page__stat-value">{{ stats.total_hours }}h</span>
          <span class="weekly-page__stat-label">总活跃</span>
        </KuCard>
        <KuCard padding="md" class="weekly-page__stat">
          <span class="weekly-page__stat-value">{{ stats.work_hours }}h</span>
          <span class="weekly-page__stat-label">工作</span>
        </KuCard>
        <KuCard padding="md" class="weekly-page__stat">
          <span class="weekly-page__stat-value">{{ stats.entertainment_hours }}h</span>
          <span class="weekly-page__stat-label">娱乐</span>
        </KuCard>
        <KuCard padding="md" class="weekly-page__stat">
          <span class="weekly-page__stat-value">{{ stats.other_hours }}h</span>
          <span class="weekly-page__stat-label">其他</span>
        </KuCard>
      </div>

      <!-- 逐日条形 -->
      <KuCard v-if="daily.length" padding="lg" class="weekly-page__chart-card">
        <h3 class="weekly-page__chart-title">每日分布</h3>
        <div class="weekly-page__chart">
          <div v-for="d in daily" :key="d.date" class="weekly-page__bar-row">
            <span class="weekly-page__bar-date">{{ d.date.slice(5) }}</span>
            <div class="weekly-page__bar-track">
              <div
                class="weekly-page__bar weekly-page__bar--work"
                :style="{ width: pct(d.work, maxHours) + '%' }"
              ></div>
              <div
                class="weekly-page__bar weekly-page__bar--entertainment"
                :style="{ width: pct(d.entertainment, maxHours) + '%' }"
              ></div>
              <div
                class="weekly-page__bar weekly-page__bar--other"
                :style="{ width: pct(d.other, maxHours) + '%' }"
              ></div>
            </div>
            <span class="weekly-page__bar-total">{{ d.total }}h</span>
          </div>
        </div>
      </KuCard>

      <!-- AI 周报文本 -->
      <KuCard padding="lg" class="weekly-page__content">
        <div class="weekly-page__review-text">{{ review }}</div>
      </KuCard>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import KuButton from '@/components/base/KuButton.vue'
import KuCard from '@/components/base/KuCard.vue'
import KuSpinner from '@/components/base/KuSpinner.vue'
import api from '@/api'
import { handleApiError } from '@/utils/error'
import type { WeeklyReviewData, WeeklyReviewStats } from '@/types/api'

const EMPTY_STATS: WeeklyReviewStats = {
  total_hours: 0, work_hours: 0, entertainment_hours: 0,
  other_hours: 0, day_count: 0, week_start: '', week_end: '',
}

const review = ref('')
const stats = ref<WeeklyReviewStats>({ ...EMPTY_STATS })
const daily = ref<WeeklyReviewData['daily']>([])
const loading = ref(false)
const error = ref('')
const hasLoaded = ref(false)

// AbortController 用于取消组件卸载后仍在飞行中的请求
let abortController: AbortController | null = null

const maxHours = computed(() => {
  const max = Math.max(...daily.value.map(d => d.total), 1)
  return Math.ceil(max / 2) * 2
})

function pct(val: number, max: number) {
  return max > 0 ? Math.round((val / max) * 100) : 0
}

onMounted(() => { loadReview() })

onBeforeUnmount(() => {
  abortController?.abort()
})

async function loadReview() {
  // 取消上一个未完成的请求
  abortController?.abort()
  abortController = new AbortController()

  loading.value = true
  // 不清除 error —— 如果之前有数据，保留并展示
  error.value = ''

  try {
    const res = await api.get('/weekly-review', {
      signal: abortController.signal,
    })
    if (res.data.status === 'success') {
      review.value = res.data.data.review || ''
      stats.value = res.data.data.stats || { ...EMPTY_STATS }
      daily.value = res.data.data.daily || []
      error.value = ''
      hasLoaded.value = true
    } else {
      // 只在没有已有数据时才展示错误，否则保留旧数据并提示
      const errMsg = res.data.message || '获取复盘失败'
      if (!hasLoaded.value) {
        error.value = errMsg
      } else {
        error.value = `刷新失败：${errMsg}（显示上次数据）`
      }
    }
  } catch (e: unknown) {
    if (e instanceof Error && e.name === 'CanceledError') {
      return // 请求被 AbortController 取消，忽略
    }
    if (!hasLoaded.value) {
      error.value = handleApiError(e, { source: 'general' })
    } else {
      error.value = `刷新失败（显示上次数据）`
    }
  } finally {
    if (abortController && !abortController.signal.aborted) {
      loading.value = false
    }
  }
}
</script>

<style scoped>
.weekly-page {
  display: flex;
  max-width: var(--content-max-width);
  margin: 0 auto;
  flex-direction: column;
  gap: var(--space-5);
}

.weekly-page__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  background: radial-gradient(circle at top left, rgba(201, 138, 105, .12), transparent 30%), radial-gradient(circle at bottom right, rgba(212, 168, 75, .08), transparent 30%), var(--color-bg-card);
}

.weekly-page__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: .08em;
  text-transform: uppercase;
}

.weekly-page__hero h2 {
  font-size: clamp(1.4rem, 2vw, 1.8rem);
}

.weekly-page__meta {
  margin-top: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.weekly-page__content {
  min-height: 200px;
}

.weekly-page__error {
  color: var(--color-danger);
  margin-bottom: var(--space-4);
}

.weekly-page__review-text {
  font-size: var(--font-size-lg);
  line-height: 2.2;
  white-space: pre-wrap;
  color: var(--color-text-primary);
}

.weekly-page__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-3);
}

.weekly-page__stat {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.weekly-page__stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.weekly-page__stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: .06em;
}

.weekly-page__chart-card {
  padding: var(--space-5);
}

.weekly-page__chart-title {
  font-size: var(--font-size-base);
  margin-bottom: var(--space-4);
  color: var(--color-text-secondary);
}

.weekly-page__chart {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.weekly-page__bar-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.weekly-page__bar-date {
  width: 42px;
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.weekly-page__bar-track {
  flex: 1;
  height: 18px;
  display: flex;
  border-radius: 4px;
  overflow: hidden;
  background: var(--color-bg-secondary);
}

.weekly-page__bar {
  height: 100%;
  transition: width var(--duration-normal);
}

.weekly-page__bar--work {
  background: rgba(201, 138, 105, .7);
}

.weekly-page__bar--entertainment {
  background: rgba(212, 168, 75, .7);
}

.weekly-page__bar--other {
  background: rgba(155, 143, 128, .5);
}

.weekly-page__bar-total {
  width: 36px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  text-align: right;
  flex-shrink: 0;
}

@media (max-width: 520px) {
  .weekly-page__stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
