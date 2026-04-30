<template>
  <div class="aw-popover" v-if="visible" @click.stop>
    <div class="aw-popover__header">
      <span class="aw-popover__title">ActivityWatch 状态</span>
      <button class="aw-popover__close" @click="$emit('close')">×</button>
    </div>
    <div class="aw-popover__body">
      <div class="aw-popover__status" :class="`aw-popover__status--${status}`">
        <span class="aw-popover__dot"></span>
        <span>{{ statusLabel }}</span>
      </div>
      <p v-if="lastSyncTime" class="aw-popover__sync">
        上次同步: {{ formatTime(lastSyncTime) }}
      </p>
      <p v-if="error" class="aw-popover__error">{{ error }}</p>
    </div>
    <div class="aw-popover__actions">
      <button type="button" class="aw-popover__action" @click="$emit('retry')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 4v6h-6M1 20v-6h6"/>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
        </svg>
        立即重连
      </button>
      <button type="button" class="aw-popover__action" @click="$emit('openLogs')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14,2 14,8 20,8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
        查看日志
      </button>
      <button type="button" class="aw-popover__action" @click="$emit('openSettings')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        跳转配置
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  visible: boolean
  status: 'connected' | 'syncing' | 'disconnected'
  lastSyncTime: Date | null
  error: string | null
}>()

defineEmits<{
  close: []
  retry: []
  openLogs: []
  openSettings: []
}>()

const statusLabel = computed(() => {
  switch (props.status) {
    case 'connected': return '已连接'
    case 'syncing': return '同步中'
    case 'disconnected': return '已断开'
    default: return '未知状态'
  }
})

function formatTime(date: Date): string {
  const now = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.aw-popover {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  width: 280px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  z-index: 100;
  overflow: hidden;
}

.aw-popover__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
}

.aw-popover__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.aw-popover__close {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 18px;
  cursor: pointer;
  border-radius: 4px;
}

.aw-popover__close:hover {
  background: var(--color-bg-active);
}

.aw-popover__body {
  padding: 16px;
}

.aw-popover__status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 500;
}

.aw-popover__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.aw-popover__status--connected .aw-popover__dot { background: var(--color-success, #22c55e); }
.aw-popover__status--disconnected .aw-popover__dot { background: var(--color-danger, #ef4444); }

.aw-popover__sync {
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.aw-popover__error {
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-danger);
}

.aw-popover__actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  border-top: 1px solid var(--color-border);
}

.aw-popover__action {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: transparent;
  color: var(--color-text-primary);
  font-size: 14px;
  text-align: left;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.aw-popover__action:hover {
  background: var(--color-bg-active);
}
</style>