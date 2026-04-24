<template>
  <div class="app-layout" :class="{ 'app-layout--sidebar-collapsed': sidebarCollapsed }">
    <!-- 移动端遮罩 -->
    <div
      v-if="mobileSidebarOpen"
      class="app-layout__overlay"
      @click="mobileSidebarOpen = false"
    ></div>

    <!-- 侧边栏 -->
    <Sidebar
      :collapsed="sidebarCollapsed"
      :mobile-open="mobileSidebarOpen"
      @toggle="handleSidebarToggle"
    />

    <!-- 主内容区 -->
    <main class="app-layout__main">
      <!-- 顶部栏 -->
      <header class="app-layout__topbar">
        <button
          class="app-layout__menu-btn mobile-only"
          @click="mobileSidebarOpen = true"
          aria-label="打开菜单"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
        <div class="app-layout__heading">
          <h1>{{ currentHeading }}</h1>
          <p v-if="currentDescription" class="app-layout__desc">{{ currentDescription }}</p>
        </div>
        <div class="app-layout__status">
          <span class="app-layout__status-pill">{{ currentStatus }}</span>
        </div>
      </header>

      <!-- 页面内容 -->
      <div class="app-layout__content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './Sidebar.vue'
import { useChatStore } from '@/store/chat'
import { useSummaryStore } from '@/store/summary'

const route = useRoute()
const chatStore = useChatStore()
const summaryStore = useSummaryStore()

const sidebarCollapsed = ref(false)
const mobileSidebarOpen = ref(false)

const currentHeading = computed(() => {
  if (route.path === '/chat') return chatStore.activeSession?.title || '新建对话'
  if (route.path === '/settings') return '偏好设置'
  return '每日摘要'
})

const currentDescription = computed(() => {
  if (route.path === '/chat') return '继续你的陪伴对话，或带着今天的上下文开始新的聊天。'
  if (route.path === '/settings') return '管理豆包 API、ActivityWatch 地址与本地隐私选项。'
  return '查看今天的专注、放松与应用使用情况，快速进入对话陪伴。'
})

const currentStatus = computed(() => {
  if (route.path === '/chat') {
    return chatStore.messages.length === 0
      ? '等待你的第一条消息'
      : `当前共有 ${chatStore.messages.length} 条消息`
  }
  if (route.path === '/settings') return '本地配置页'
  if (summaryStore.summary) return `今日累计 ${summaryStore.summary.total_hours} 小时`
  if (summaryStore.loading) return '正在刷新摘要'
  return '等待摘要数据'
})

watch(() => route.fullPath, () => {
  mobileSidebarOpen.value = false
})

function handleSidebarToggle() {
  if (window.matchMedia('(max-width: 960px)').matches) {
    mobileSidebarOpen.value = !mobileSidebarOpen.value
    return
  }
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<style scoped>
.app-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
  transition: grid-template-columns var(--duration-normal) var(--ease-out);
}

.app-layout--sidebar-collapsed {
  grid-template-columns: var(--sidebar-width-collapsed) 1fr;
}

.app-layout__overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(0, 0, 0, 0.3);
}

.app-layout__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 100vh;
  overflow: hidden;
}

.app-layout__topbar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-6);
  background: linear-gradient(
    to bottom,
    var(--color-bg-primary),
    rgba(250, 247, 244, 0.8),
    transparent
  );
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 10;
}

.app-layout__menu-btn {
  display: none;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  width: 44px;
  height: 44px;
  padding: 10px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
}

.app-layout__menu-btn span {
  display: block;
  width: 100%;
  height: 2px;
  background: var(--color-text-secondary);
  border-radius: 1px;
}

.app-layout__heading {
  flex: 1;
  min-width: 0;
}

.app-layout__heading h1 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.app-layout__desc {
  margin-top: var(--space-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.app-layout__status-pill {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 var(--space-4);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  white-space: nowrap;
}

.app-layout__content {
  flex: 1;
  padding: var(--space-6);
  overflow-x: hidden;
}

.mobile-only {
  display: none;
}

@media (max-width: 960px) {
  .app-layout {
    grid-template-columns: 1fr;
  }

  .app-layout__overlay {
    display: block;
  }

  .app-layout__menu-btn {
    display: flex;
  }

  .app-layout__content {
    padding: var(--space-4);
  }

  .mobile-only {
    display: flex;
  }
}
</style>