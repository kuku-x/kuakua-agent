<template>
  <section class="summary-page">
    <KuCard padding="lg" class="summary-page__hero">
      <div class="summary-page__hero-copy">
        <p class="summary-page__eyebrow">Today in Kuakua</p>
        <h2>先看懂今天，再决定接下来要怎么陪自己</h2>
        <p>
          页面保留原有摘要能力，只把信息重新编排成更清晰的结构，方便你快速浏览、
          刷新和进入聊天。
        </p>
      </div>

      <KuButton :loading="store.loading" @click="refresh">
        {{ store.loading ? '刷新中...' : '刷新摘要' }}
      </KuButton>
    </KuCard>

    <div v-if="store.summary" class="summary-page__actions">
      <KuButton variant="primary" @click="openChatWithSummary">带着今日摘要去聊天</KuButton>
      <KuButton @click="openEncouragementChat">让夸夸鼓励我一下</KuButton>
    </div>

    <KuCard v-if="store.loading" class="summary-page__state">
      <KuSpinner text="正在整理今天的摘要数据..." />
    </KuCard>

    <KuCard v-else-if="store.error" class="summary-page__state summary-page__state--error">
      <p>{{ store.error }}</p>
      <KuButton @click="refresh">重新尝试</KuButton>
    </KuCard>

    <div v-else-if="store.summary" class="summary-page__grid">
      <SummaryCard :summary="store.summary" />

      <KuCard padding="lg" class="summary-page__chart">
        <TimePieChart :data="store.summary" />
      </KuCard>

      <KuCard padding="lg" class="summary-page__apps">
        <div class="summary-page__panel-head">
          <div>
            <p class="summary-page__panel-eyebrow">Top Apps</p>
            <h3>今天主要把时间用在哪些应用</h3>
          </div>
          <span>已记录 {{ store.summary.top_apps.length }} 项</span>
        </div>

        <div class="summary-page__app-list">
          <article v-for="app in store.summary.top_apps" :key="app.name" class="summary-page__app">
            <div class="summary-page__app-copy">
              <strong>{{ app.name }}</strong>
              <p>{{ formatCategory(app.category) }}</p>
            </div>
            <div class="summary-page__app-meta">
              <span>{{ formatDuration(app.duration) }}</span>
              <span class="summary-page__app-tag" :class="`summary-page__app-tag--${app.category}`">
                {{ formatCategoryTag(app.category) }}
              </span>
            </div>
          </article>
        </div>
      </KuCard>
    </div>

    <KuCard v-else class="summary-page__state">
      <p>暂时还没有摘要数据，请确认 ActivityWatch 正在运行后再试一次。</p>
    </KuCard>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import KuButton from '@/components/base/KuButton.vue'
import KuCard from '@/components/base/KuCard.vue'
import KuSpinner from '@/components/base/KuSpinner.vue'
import SummaryCard from '@/components/SummaryCard.vue'
import TimePieChart from '@/components/TimePieChart.vue'
import { useChatStore } from '@/store/chat'
import { useSummaryStore } from '@/store/summary'
import { formatDuration } from '@/utils/format'

const store = useSummaryStore()
const chatStore = useChatStore()
const router = useRouter()

onMounted(() => {
  if (!store.summary && !store.loading) {
    store.fetchTodaySummary()
  }
})

function refresh() {
  store.fetchTodaySummary()
}

function formatCategory(category: string) {
  if (category === 'work') return '偏工作使用'
  if (category === 'entertainment') return '偏娱乐放松'
  return '其他活动'
}

function formatCategoryTag(category: string) {
  if (category === 'work') return '工作'
  if (category === 'entertainment') return '娱乐'
  return '其他'
}

function openChatWithSummary() {
  if (!store.summary) return

  chatStore.resetChat()
  chatStore.setDraft(
    `请结合今天的摘要陪我复盘一下。今天总共活跃 ${store.summary.total_hours} 小时，` +
      `其中工作 ${store.summary.work_hours} 小时，娱乐 ${store.summary.entertainment_hours} 小时。`,
  )
  router.push('/chat')
}

function openEncouragementChat() {
  chatStore.resetChat()
  chatStore.setDraft('请结合我今天的表现，温柔地鼓励我一下。')
  router.push('/chat')
}
</script>

<style scoped>
.summary-page {
  display: flex;
  max-width: var(--content-max-width);
  margin: 0 auto;
  flex-direction: column;
  gap: var(--space-5);
}

.summary-page__hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-5);
  background:
    radial-gradient(circle at top left, rgba(201, 138, 105, 0.16), transparent 32%),
    var(--color-bg-card);
}

.summary-page__hero-copy {
  flex: 1;
  min-width: 0;
}

.summary-page__eyebrow,
.summary-page__panel-eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.summary-page__hero-copy h2 {
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.15;
  letter-spacing: -0.04em;
}

.summary-page__hero-copy p:last-child {
  max-width: 640px;
  margin-top: var(--space-3);
  color: var(--color-text-secondary);
}

.summary-page__actions {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.summary-page__state {
  display: flex;
  min-height: 220px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  text-align: center;
  color: var(--color-text-secondary);
}

.summary-page__state--error {
  color: var(--color-danger);
}

.summary-page__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-5);
  align-items: start;
}

.summary-page__apps {
  grid-column: 1 / -1;
}

.summary-page__panel-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.summary-page__panel-head h3 {
  font-size: var(--font-size-2xl);
}

.summary-page__panel-head span {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.summary-page__app-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.summary-page__app {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.summary-page__app-copy strong {
  display: block;
  margin-bottom: 4px;
}

.summary-page__app-copy p {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.summary-page__app-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

.summary-page__app-tag {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 var(--space-3);
  font-size: var(--font-size-xs);
  border-radius: var(--radius-full);
}

.summary-page__app-tag--work {
  color: var(--color-accent-hover);
  background: rgba(201, 138, 105, 0.14);
}

.summary-page__app-tag--entertainment {
  color: #a3782d;
  background: rgba(212, 168, 75, 0.18);
}

.summary-page__app-tag--other {
  color: var(--color-text-secondary);
  background: var(--color-accent-light);
}

@media (max-width: 960px) {
  .summary-page__hero,
  .summary-page__panel-head,
  .summary-page__app {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-page__grid {
    grid-template-columns: 1fr;
  }

  .summary-page__actions {
    flex-direction: column;
  }

  .summary-page__app-meta {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
