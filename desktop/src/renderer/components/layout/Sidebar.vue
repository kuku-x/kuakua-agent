<template>
  <aside
    :class="[
      'sidebar',
      { 'sidebar--collapsed': collapsed },
      { 'sidebar--mobile-open': mobileOpen }
    ]"
  >
    <!-- 侧边栏头部 -->
    <div class="sidebar__header">
      <button
        class="sidebar__toggle"
        @click="$emit('toggle')"
        :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
      >
        <span class="sidebar__toggle-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path v-if="!collapsed" d="M15 18l-6-6 6-6" />
            <path v-else d="M9 18l6-6-6-6" />
          </svg>
        </span>
      </button>
      <button
        v-if="!collapsed"
        class="sidebar__new-chat"
        @click="startNewChat"
      >
        <span class="sidebar__new-chat-plus">+</span>
        <span>新建对话</span>
      </button>
    </div>

    <!-- 今日概览 -->
    <div v-if="!collapsed" class="sidebar__section sidebar__overview">
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
          <strong class="sidebar__overview-praise">正在整理今天的行为数据...</strong>
        </template>
        <template v-else>
          <strong class="sidebar__overview-praise">今天的摘要还没有准备好</strong>
        </template>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="sidebar__nav">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="sidebar__nav-item"
        :title="collapsed ? item.label : undefined"
      >
        <span class="sidebar__nav-icon">{{ item.icon }}</span>
        <span v-if="!collapsed" class="sidebar__nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- 历史会话 -->
    <div class="sidebar__section sidebar__conversations">
      <p v-if="!collapsed" class="sidebar__section-title">
        历史对话
        <span class="sidebar__session-count">{{ chatStore.sessions.length }}</span>
      </p>
      <div class="sidebar__session-list">
        <button
          v-for="session in chatStore.sessions"
          :key="session.id"
          class="sidebar__session-item"
          :class="{ 'sidebar__session-item--active': session.id === chatStore.activeChatId && route.path === '/chat' }"
          @click="openConversation(session.id)"
          :title="collapsed ? session.title : undefined"
        >
          <span class="sidebar__session-icon">聊</span>
          <span v-if="!collapsed" class="sidebar__session-info">
            <strong>{{ session.title }}</strong>
            <small>{{ formatTime(session.updatedAt) }}</small>
          </span>
        </button>
      </div>
    </div>
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
  { to: '/', label: '每日摘要', icon: '摘' },
  { to: '/chat', label: '陪伴聊天', icon: '聊' },
  { to: '/settings', label: '偏好设置', icon: '设' },
]

function startNewChat() {
  chatStore.resetChat()
  router.push('/chat')
}

function openConversation(sessionId: string) {
  chatStore.selectChat(sessionId)
  router.push('/chat')
}

function formatTime(date: Date): string {
  const h = `${date.getHours()}`.padStart(2, '0')
  const m = `${date.getMinutes()}`.padStart(2, '0')
  return `${h}:${m}`
}
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  max-width: var(--sidebar-width);
  height: 100vh;
  padding: var(--space-4);
  background: var(--color-bg-sidebar);
  border-right: 1px solid var(--color-border);
  overflow: hidden;
  transition: all var(--duration-normal) var(--ease-out);
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
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__toggle:hover {
  background: var(--color-accent-soft);
  color: var(--color-text-primary);
}

.sidebar__toggle-icon {
  display: flex;
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
  width: 100%;
  min-height: 44px;
  padding: 0 var(--space-4);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__new-chat:hover {
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
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.sidebar__session-count {
  font-weight: var(--font-weight-normal);
  color: var(--color-text-tertiary);
}

.sidebar__overview-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.sidebar__overview-praise {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-normal);
  color: var(--color-text-primary);
}

.sidebar__overview-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
}

.sidebar__stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-2);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
}

.sidebar__stat span {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.sidebar__stat b {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar__nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  color: var(--color-text-secondary);
  border-radius: var(--radius-md);
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__nav-item:hover {
  background: var(--color-accent-soft);
  color: var(--color-text-primary);
}

.sidebar__nav-item.router-link-active {
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  box-shadow: var(--shadow-sm);
}

.sidebar__nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.sidebar__nav-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.sidebar__conversations {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.sidebar__session-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar__session-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: left;
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__session-item:hover {
  background: var(--color-accent-soft);
}

.sidebar__session-item--active {
  background: var(--color-bg-card);
  box-shadow: var(--shadow-sm);
}

.sidebar__session-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-secondary);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.sidebar__session-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.sidebar__session-info strong {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar__session-info small {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

@media (max-width: 960px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 50;
    height: 100vh;
    transform: translateX(-100%);
    transition: transform var(--duration-normal) var(--ease-out);
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
