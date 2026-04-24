<template>
  <aside
    :class="[
      'sidebar',
      { 'sidebar--collapsed': collapsed },
      { 'sidebar--mobile-open': mobileOpen },
    ]"
  >
    <div class="sidebar__header">
      <button
        class="sidebar__toggle"
        type="button"
        :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
        @click="$emit('toggle')"
      >
        <span class="sidebar__toggle-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path v-if="!collapsed" d="M15 18l-6-6 6-6" />
            <path v-else d="M9 18l6-6-6-6" />
          </svg>
        </span>
      </button>

      <button v-if="!collapsed" class="sidebar__new-chat" type="button" @click="startNewChat">
        <span class="sidebar__new-chat-plus">+</span>
        <span>新建对话</span>
      </button>
    </div>

    <section v-if="!collapsed" class="sidebar__section">
      <p class="sidebar__section-title">今日概览</p>
      <div class="sidebar__overview-card">
        <template v-if="summaryStore.summary">
          <strong class="sidebar__overview-praise">{{ summaryStore.summary.praise_text }}</strong>
          <div class="sidebar__overview-stats">
            <div class="sidebar__stat">
              <span>专注</span>
              <b>{{ summaryStore.summary.work_hours }}h</b>
            </div>
            <div class="sidebar__stat">
              <span>放松</span>
              <b>{{ summaryStore.summary.entertainment_hours }}h</b>
            </div>
            <div class="sidebar__stat">
              <span>总时长</span>
              <b>{{ summaryStore.summary.total_hours }}h</b>
            </div>
          </div>
        </template>

        <template v-else-if="summaryStore.loading">
          <strong class="sidebar__overview-praise">正在整理今天的活动数据...</strong>
        </template>

        <template v-else>
          <strong class="sidebar__overview-praise">今天的摘要还没有准备好</strong>
        </template>
      </div>
    </section>

    <nav class="sidebar__nav">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="sidebar__nav-item"
        :title="collapsed ? item.label : undefined"
      >
        <span class="sidebar__nav-icon">{{ item.icon }}</span>
        <span v-if="!collapsed" class="sidebar__nav-copy">
          <strong>{{ item.label }}</strong>
          <small>{{ item.caption }}</small>
        </span>
      </router-link>
    </nav>

    <section class="sidebar__section sidebar__conversations">
      <p v-if="!collapsed" class="sidebar__section-title">
        历史对话
        <span class="sidebar__session-count">{{ chatStore.sessions.length }}</span>
      </p>

      <div class="sidebar__session-list">
        <button
          v-for="session in chatStore.sessions"
          :key="session.id"
          type="button"
          class="sidebar__session-item"
          :class="{ 'sidebar__session-item--active': isActiveSession(session.id) }"
          :title="collapsed ? session.title : undefined"
          @click="openConversation(session.id)"
        >
          <span class="sidebar__session-icon">{{ collapsed ? '聊' : '对话' }}</span>
          <span v-if="!collapsed" class="sidebar__session-info">
            <strong>{{ session.title }}</strong>
            <small>{{ formatSessionMeta(session.updatedAt, session.messages.length) }}</small>
          </span>
        </button>
      </div>
    </section>
  </aside>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '@/store/chat'
import { useSummaryStore } from '@/store/summary'

defineProps<{
  collapsed: boolean
  mobileOpen: boolean
}>()

defineEmits<{
  toggle: []
}>()

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const summaryStore = useSummaryStore()

const navItems = [
  { to: '/', label: '每日摘要', caption: '今天的节奏与应用分布', icon: '日' },
  { to: '/chat', label: '陪伴聊天', caption: '延续上下文继续聊', icon: '聊' },
]

function isActiveSession(sessionId: string) {
  return route.path === '/chat' && sessionId === chatStore.activeChatId
}

function startNewChat() {
  chatStore.resetChat()
  router.push('/chat')
}

function openConversation(sessionId: string) {
  chatStore.selectChat(sessionId)
  router.push('/chat')
}

function formatSessionMeta(date: Date, count: number) {
  const hours = `${date.getHours()}`.padStart(2, '0')
  const minutes = `${date.getMinutes()}`.padStart(2, '0')
  return `${hours}:${minutes} · ${count} 条消息`
}
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  max-width: var(--sidebar-width);
  height: 100vh;
  min-height: 100vh;
  padding: var(--space-4);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.24), transparent 18%),
    var(--color-bg-sidebar);
  border-right: 1px solid var(--color-border);
  overflow-y: auto;
  transition:
    width var(--duration-normal) var(--ease-out),
    min-width var(--duration-normal) var(--ease-out),
    max-width var(--duration-normal) var(--ease-out),
    transform var(--duration-normal) var(--ease-out);
}

.sidebar--collapsed {
  width: var(--sidebar-width-collapsed);
  min-width: var(--sidebar-width-collapsed);
  max-width: var(--sidebar-width-collapsed);
}

.sidebar__header {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.sidebar__toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  color: var(--color-text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__toggle:hover {
  color: var(--color-text-primary);
  background: var(--color-accent-soft);
}

.sidebar__toggle-icon {
  width: 20px;
  height: 20px;
}

.sidebar__toggle-icon svg {
  width: 100%;
  height: 100%;
}

.sidebar__new-chat {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 44px;
  padding: 0 var(--space-4);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__new-chat:hover {
  transform: translateY(-1px);
  background: var(--color-bg-elevated);
  border-color: var(--color-border-strong);
}

.sidebar__new-chat-plus {
  font-size: 18px;
  line-height: 1;
}

.sidebar__section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.sidebar__section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0 var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.sidebar__session-count {
  font-weight: var(--font-weight-normal);
}

.sidebar__overview-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.sidebar__overview-praise {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
}

.sidebar__overview-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-2);
}

.sidebar__stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-2);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.sidebar__stat span {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
}

.sidebar__stat b {
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.sidebar__nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  color: var(--color-text-secondary);
  border-radius: var(--radius-lg);
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__nav-item:hover {
  color: var(--color-text-primary);
  background: var(--color-accent-soft);
}

.sidebar__nav-item.router-link-active {
  color: var(--color-text-primary);
  background: var(--color-bg-card);
  box-shadow: var(--shadow-xs);
}

.sidebar__nav-icon,
.sidebar__session-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.sidebar__nav-copy,
.sidebar__session-info {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}

.sidebar__nav-copy strong,
.sidebar__session-info strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.sidebar__nav-copy small,
.sidebar__session-info small {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
}

.sidebar__conversations {
  flex: 1;
  min-height: 0;
}

.sidebar__session-list {
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  gap: var(--space-1);
  overflow-y: auto;
}

.sidebar__session-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3);
  background: transparent;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  text-align: left;
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__session-item:hover {
  background: var(--color-accent-soft);
}

.sidebar__session-item--active {
  background: var(--color-bg-card);
  box-shadow: var(--shadow-xs);
}

@media (max-width: 960px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 50;
    transform: translateX(-100%);
  }

  .sidebar--mobile-open {
    transform: translateX(0);
  }

  .sidebar--collapsed {
    width: var(--sidebar-width);
    min-width: var(--sidebar-width);
    max-width: var(--sidebar-width);
  }
}
</style>
