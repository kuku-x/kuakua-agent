<template>
  <div class="aw-status" :class="`aw-status--${status}`" @click="$emit('click')">
    <span class="aw-status__dot" :class="{ 'aw-status__dot--pulse': status === 'syncing' }"></span>
    <span class="aw-status__label">{{ label }}</span>
    <div class="aw-status__actions" @click.stop>
      <button class="aw-status__btn" title="重连" @click="$emit('retry')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 4v6h-6M1 20v-6h6"/>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
        </svg>
      </button>
      <button class="aw-status__btn" title="更多" @click="$emit('more')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="5" r="2"/>
          <circle cx="12" cy="12" r="2"/>
          <circle cx="12" cy="19" r="2"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: 'connected' | 'syncing' | 'disconnected'
  lastSyncTime: Date | null
}>()

defineEmits<{
  click: []
  retry: []
  more: []
}>()

const label = computed(() => {
  switch (props.status) {
    case 'connected': return '已连接'
    case 'syncing': return '同步中'
    case 'disconnected': return '已断开'
  }
})
</script>

<style scoped>
.aw-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--color-bg-elevated);
  cursor: pointer;
  transition: background 0.2s;
}

.aw-status:hover {
  background: var(--color-bg-hover);
}

.aw-status__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.aw-status--connected .aw-status__dot { background: #22c55e; }
.aw-status--syncing .aw-status__dot { background: #eab308; }
.aw-status--disconnected .aw-status__dot { background: #ef4444; }

.aw-status__dot--pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}

.aw-status__label {
  flex: 1;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.aw-status__actions {
  display: flex;
  gap: 4px;
}

.aw-status__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.aw-status__btn:hover {
  background: var(--color-bg-active);
  color: var(--color-text-primary);
}
</style>
