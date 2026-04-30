<template>
  <div class="app-layout" :class="{ 'app-layout--sidebar-collapsed': sidebarCollapsed }">
    <GlobalError />

    <div
      v-if="mobileSidebarOpen"
      class="app-layout__overlay"
      @click="mobileSidebarOpen = false"
    ></div>

    <Sidebar
      :collapsed="sidebarCollapsed"
      :mobile-open="mobileSidebarOpen"
      @toggle="handleSidebarToggle"
    />

    <main class="app-layout__main">
      <header class="app-layout__topbar">
        <button
          class="app-layout__menu-btn mobile-only"
          type="button"
          aria-label="打开侧边栏"
          @click="mobileSidebarOpen = true"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <div class="app-layout__heading">
          <p class="app-layout__eyebrow">{{ currentEyebrow }}</p>
          <h1>{{ currentHeading }}</h1>
          <p v-if="currentDescription" class="app-layout__desc">{{ currentDescription }}</p>
        </div>

        <div class="app-layout__topbar-actions">
          <div class="app-layout__status">
            <span class="app-layout__status-pill">{{ currentStatus }}</span>
          </div>

          <SettingsTrigger @click="settingsOpen = true" />
        </div>
      </header>

      <div class="app-layout__content">
        <section v-if="nightlySummary" class="nightly-summary-card">
          <div class="nightly-summary-card__head">
            <div>
              <p class="nightly-summary-card__eyebrow">Nightly Summary</p>
              <h2>今晚总结已生成</h2>
            </div>

            <button
              class="nightly-summary-card__dismiss"
              type="button"
              aria-label="关闭晚间总结提醒"
              @click="dismissNightlySummary"
            >
              ×
            </button>
          </div>

          <p class="nightly-summary-card__date">{{ nightlySummary.date }}</p>
          <p class="nightly-summary-card__content">{{ nightlySummary.content }}</p>

          <div class="nightly-summary-card__actions">
            <RouterLink to="/nightly-summary" class="nightly-summary-card__action">
              查看完整总结
            </RouterLink>
            <button class="nightly-summary-card__dismiss-link" type="button" @click="dismissNightlySummary">
              标记已读
            </button>
          </div>
        </section>

        <router-view />
      </div>
    </main>

    <SettingsPanel :open="settingsOpen" @close="settingsOpen = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getLatestNightlySummary, markNightlySummaryRead } from '@/api'
import { reportGlobalError } from '@/utils/error'
import Sidebar from '@/components/layout/Sidebar.vue'
import SettingsPanel from '@/components/settings/SettingsPanel.vue'
import SettingsTrigger from '@/components/settings/SettingsTrigger.vue'
import GlobalError from '@/components/widgets/GlobalError.vue'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useChatStore } from '@/store/chat'
import { useSummaryStore } from '@/store/summary'
import type { NightlySummary } from '@/types/api'

const route = useRoute()
const chatStore = useChatStore()
const summaryStore = useSummaryStore()
const { on } = useWebSocket()

// 保存取消订阅函数，组件卸载时清理
const unsubPraise = on('praise_push', (event) => {
  if (event.type === 'praise_push') {
    window.electronAPI?.showSystemNotification?.({
      title: '夸夸',
      body: event.data.content,
    })
  }
})

const sidebarCollapsed = ref(false)
const mobileSidebarOpen = ref(false)
const settingsOpen = ref(false)
const nightlySummary = ref<NightlySummary | null>(null)
const notifiedNightlyDate = ref('')
let nightlySummaryTimer: ReturnType<typeof setTimeout> | null = null
let nightlyLoading = false

const currentEyebrow = computed(() => (route.path === '/chat' ? '陪伴聊天' : '每日摘要'))

const currentHeading = computed(() => {
  if (route.path === '/chat') {
    return chatStore.activeSession?.title || '开始一段新对话'
  }
  return '看看今天的专注、放松与节奏'
})

const currentDescription = computed(() => {
  if (route.path === '/chat') {
    return '结合今天的上下文继续聊天，或者从一条新的提示开始。'
  }
  return '先理解今天发生了什么，再决定要不要带着摘要进入下一步对话。'
})

const currentStatus = computed(() => {
  if (route.path === '/chat') {
    return chatStore.messages.length === 0
      ? '等待你的第一条消息'
      : `当前共 ${chatStore.messages.length} 条消息`
  }

  if (summaryStore.summary) {
    return `今日累计 ${summaryStore.summary.total_hours} 小时`
  }

  if (summaryStore.loading) {
    return '正在刷新摘要'
  }

  return '等待摘要数据'
})

watch(
  () => route.fullPath,
  () => {
    mobileSidebarOpen.value = false
  },
)

onMounted(() => {
  // 只在 summary 确实为空且未在加载中才请求，避免与子页面重复
  if (!summaryStore.summary && !summaryStore.loading) {
    summaryStore.fetchTodaySummary()
  }

  void syncNightlySummary()
  scheduleNextNightlyPoll()
})

onUnmounted(() => {
  // 清理 WebSocket 监听器
  unsubPraise?.()
  // 清理定时器
  if (nightlySummaryTimer !== null) {
    clearTimeout(nightlySummaryTimer)
    nightlySummaryTimer = null
  }
})

function handleSidebarToggle() {
  if (window.matchMedia('(max-width: 960px)').matches) {
    mobileSidebarOpen.value = !mobileSidebarOpen.value
    return
  }

  sidebarCollapsed.value = !sidebarCollapsed.value
}

function scheduleNextNightlyPoll() {
  if (nightlySummaryTimer !== null) {
    clearTimeout(nightlySummaryTimer)
  }
  nightlySummaryTimer = setTimeout(() => {
    void syncNightlySummary()
  }, 30000)
}

async function syncNightlySummary() {
  // 防止并发请求
  if (nightlyLoading) {
    scheduleNextNightlyPoll()
    return
  }
  nightlyLoading = true
  try {
    const response = await getLatestNightlySummary()
    const latest = response.data.data
    nightlySummary.value = latest?.unread ? latest : null

    if (latest?.unread && notifiedNightlyDate.value !== latest.date) {
      notifiedNightlyDate.value = latest.date
      window.electronAPI?.showSystemNotification?.({
        title: '夸夸',
        body: latest.content,
      })
    }
  } catch (error: unknown) {
    console.error('Failed to sync nightly summary:', error)
    reportGlobalError('晚间总结同步失败，请检查后端服务')
  } finally {
    nightlyLoading = false
    scheduleNextNightlyPoll()
  }
}

async function dismissNightlySummary() {
  try {
    await markNightlySummaryRead()
  } catch (error: unknown) {
    console.error('Failed to dismiss nightly summary:', error)
  } finally {
    nightlySummary.value = null
  }
}
</script>

<style scoped>
.app-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(201, 138, 105, 0.14), transparent 24%),
    radial-gradient(circle at bottom right, rgba(212, 168, 75, 0.1), transparent 22%),
    var(--color-bg-primary);
  transition: grid-template-columns var(--duration-normal) var(--ease-out);
}

.app-layout--sidebar-collapsed {
  grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr);
}

.app-layout__overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(25, 19, 15, 0.32);
}

.app-layout__main {
  display: flex;
  min-width: 0;
  min-height: 100vh;
  flex-direction: column;
}

.app-layout__topbar {
  position: sticky;
  top: 0;
  z-index: 15;
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-6) var(--space-4);
  background: linear-gradient(
    180deg,
    rgba(250, 247, 244, 0.96) 0%,
    rgba(250, 247, 244, 0.88) 55%,
    rgba(250, 247, 244, 0) 100%
  );
  backdrop-filter: blur(14px);
}

.app-layout__menu-btn {
  display: none;
  width: 44px;
  height: 44px;
  padding: 10px;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  box-shadow: var(--shadow-xs);
}

.app-layout__menu-btn span {
  display: block;
  width: 100%;
  height: 2px;
  background: var(--color-text-secondary);
  border-radius: var(--radius-full);
}

.app-layout__heading {
  flex: 1;
  min-width: 0;
}

.app-layout__eyebrow {
  margin-bottom: var(--space-2);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-tertiary);
}

.app-layout__heading h1 {
  font-size: clamp(1.9rem, 3vw, 2.5rem);
  letter-spacing: -0.03em;
}

.app-layout__desc {
  max-width: 680px;
  margin-top: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.app-layout__topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

.app-layout__status {
  flex-shrink: 0;
}

.app-layout__status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 38px;
  padding: 0 var(--space-4);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-xs);
  white-space: nowrap;
}

.app-layout__content {
  flex: 1;
  min-width: 0;
  padding: 0 var(--space-6) var(--space-6);
}

.nightly-summary-card {
  margin-bottom: var(--space-5);
  padding: var(--space-5);
  background:
    linear-gradient(135deg, rgba(201, 138, 105, 0.16), rgba(212, 168, 75, 0.1)),
    rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(201, 138, 105, 0.18);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(10px);
}

.nightly-summary-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.nightly-summary-card__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.nightly-summary-card h2 {
  font-size: clamp(1.3rem, 2vw, 1.7rem);
  letter-spacing: -0.02em;
}

.nightly-summary-card__dismiss,
.nightly-summary-card__action {
  border: none;
  cursor: pointer;
}

.nightly-summary-card__dismiss {
  width: 36px;
  height: 36px;
  color: var(--color-text-secondary);
  font-size: 1.5rem;
  line-height: 1;
  background: rgba(255, 255, 255, 0.72);
  border-radius: var(--radius-full);
}

.nightly-summary-card__date {
  margin-top: var(--space-3);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

.nightly-summary-card__content {
  margin-top: var(--space-3);
  color: var(--color-text-primary);
  line-height: 1.8;
  white-space: pre-wrap;
}

.nightly-summary-card__action {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 0 var(--space-4);
  color: #fff;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  background: var(--color-accent);
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-xs);
  text-decoration: none;
}

.nightly-summary-card__dismiss-link {
  min-height: 40px;
  padding: 0 var(--space-4);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  cursor: pointer;
}

.nightly-summary-card__actions {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.mobile-only {
  display: none;
}

@media (max-width: 960px) {
  .app-layout {
    grid-template-columns: 1fr;
  }

  .app-layout__menu-btn {
    display: flex;
  }

  .app-layout__topbar {
    padding: var(--space-4);
  }

  .app-layout__content {
    padding: 0 var(--space-4) var(--space-4);
  }

  .nightly-summary-card {
    padding: var(--space-4);
  }

  .app-layout__status {
    display: none;
  }

  .mobile-only {
    display: flex;
  }
}
</style>
