<template>
  <section class="nightly-page">
    <KuCard padding="lg" class="nightly-page__hero">
      <div>
        <p class="nightly-page__eyebrow">Nightly Summary</p>
        <h2>{{ summary?.date || '晚间总结' }}</h2>
        <p v-if="summary" class="nightly-page__meta">
          每晚 {{ praiseConfig?.nightly_summary_time || '21:30' }} 自动生成
        </p>
      </div>
      <KuButton
        v-if="summary"
        size="sm"
        variant="ghost"
        @click="openChatWithSummary"
      >
        带着总结去聊天
      </KuButton>
    </KuCard>

    <KuCard v-if="loading" padding="lg" class="nightly-page__content">
      <KuSpinner text="正在加载晚间总结..." />
    </KuCard>

    <KuCard
      v-else-if="!summary && !error"
      padding="lg"
      class="nightly-page__content nightly-page__content--empty"
    >
      <p class="nightly-page__empty-title">还没有今天的晚间总结</p>
      <p class="nightly-page__empty-desc">
        晚间总结会在每天设定的时间自动生成。你也可以在这里回看最近几天的总结。
      </p>

      <div v-if="history.length > 0" class="nightly-page__history-section">
        <h3>历史总结</h3>
        <div class="nightly-page__history-list">
          <button
            v-for="item in history"
            :key="item.date"
            class="nightly-page__history-item"
            @click="loadSummary(item.date)"
          >
            <span class="nightly-page__history-date">{{ formatDate(item.date) }}</span>
            <span class="nightly-page__history-preview">{{ truncate(item.content, 60) }}</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>
      </div>
    </KuCard>

    <KuCard v-else-if="error" padding="lg" class="nightly-page__content">
      <p class="nightly-page__error">{{ error }}</p>
      <KuButton size="sm" @click="loadLatest">重试</KuButton>
    </KuCard>

    <KuCard v-else-if="summary" padding="lg" class="nightly-page__content">
      <div class="nightly-page__summary-text">{{ summary.content }}</div>

      <div class="nightly-page__history-section" style="margin-top: var(--space-6)">
        <h3>历史总结</h3>
        <div class="nightly-page__history-list">
          <button
            v-for="item in history"
            :key="item.date"
            class="nightly-page__history-item"
            :class="{ 'nightly-page__history-item--active': item.date === summary.date }"
            @click="loadSummary(item.date)"
          >
            <span class="nightly-page__history-date">{{ formatDate(item.date) }}</span>
            <span class="nightly-page__history-preview">{{ truncate(item.content, 60) }}</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>
      </div>
    </KuCard>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getLatestNightlySummary, getNightlySummaryHistory, markNightlySummaryRead } from '@/api'
import { praiseApi } from '@/api/praise'
import KuButton from '@/components/base/KuButton.vue'
import KuCard from '@/components/base/KuCard.vue'
import KuSpinner from '@/components/base/KuSpinner.vue'
import { useChatStore } from '@/store/chat'
import type { NightlySummary as NightlySummaryType, PraiseConfig } from '@/types/api'

const router = useRouter()
const chatStore = useChatStore()

const MAX_PREVIEW_LENGTH = 200

const summary = ref<NightlySummaryType | null>(null)
const loading = ref(false)
const error = ref('')
const praiseConfig = ref<PraiseConfig | null>(null)
const history = ref<Array<{ date: string; content: string }>>([])

onMounted(() => {
  void loadLatest()
  void loadPraiseConfig()
  void loadHistory()
})

async function loadLatest() {
  loading.value = true
  error.value = ''

  try {
    const res = await getLatestNightlySummary()
    summary.value = res.data.data
    if (summary.value?.unread) {
      void markNightlySummaryRead()
    }
  } catch {
    error.value = '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function loadSummary(targetDate: string) {
  const selected = history.value.find((item) => item.date === targetDate)
  if (!selected) {
    return
  }

  summary.value = {
    date: selected.date,
    content: selected.content,
    unread: false,
  }
  error.value = ''
}

async function loadPraiseConfig() {
  try {
    const res = await praiseApi.getConfig()
    if (res.data.status === 'success') {
      praiseConfig.value = res.data.data
    }
  } catch {
    // no-op
  }
}

async function loadHistory() {
  try {
    const res = await getNightlySummaryHistory(7)
    if (res.data.status === 'success') {
      history.value = res.data.data || []
    }
  } catch {
    // no-op
  }
}

function openChatWithSummary() {
  if (!summary.value) return
  chatStore.resetChat()
  chatStore.setDraft(`请结合今晚的总结陪我复盘一下：${summary.value.content.slice(0, MAX_PREVIEW_LENGTH)}`)
  router.push('/chat')
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function truncate(text: string, max: number) {
  return text.length > max ? `${text.slice(0, max)}...` : text
}
</script>

<style scoped>
.nightly-page {
  display: flex;
  max-width: var(--content-max-width);
  margin: 0 auto;
  flex-direction: column;
  gap: var(--space-5);
}

.nightly-page__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  background:
    radial-gradient(circle at top left, rgba(201, 138, 105, 0.12), transparent 30%),
    radial-gradient(circle at bottom right, rgba(212, 168, 75, 0.08), transparent 30%),
    var(--color-bg-card);
}

.nightly-page__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.nightly-page__hero h2 {
  font-size: clamp(1.6rem, 2.5vw, 2rem);
  letter-spacing: -0.02em;
}

.nightly-page__meta {
  margin-top: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.nightly-page__content {
  min-height: 260px;
}

.nightly-page__content--empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.nightly-page__empty-title {
  margin-bottom: var(--space-3);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
}

.nightly-page__empty-desc {
  max-width: 480px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.nightly-page__error {
  margin-bottom: var(--space-4);
  color: var(--color-danger);
}

.nightly-page__summary-text {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  line-height: 2;
  white-space: pre-wrap;
}

.nightly-page__history-section {
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.nightly-page__history-section h3 {
  margin-bottom: var(--space-3);
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
}

.nightly-page__history-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nightly-page__history-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  color: var(--color-text-primary);
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast);
}

.nightly-page__history-item:hover {
  background: var(--color-bg-elevated);
  border-color: var(--color-border);
}

.nightly-page__history-item--active {
  background: var(--color-accent-soft);
  border-color: rgba(201, 138, 105, 0.2);
}

.nightly-page__history-date {
  min-width: 60px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  white-space: nowrap;
}

.nightly-page__history-preview {
  flex: 1;
  overflow: hidden;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nightly-page__history-item svg {
  flex-shrink: 0;
  color: var(--color-text-tertiary);
}
</style>
