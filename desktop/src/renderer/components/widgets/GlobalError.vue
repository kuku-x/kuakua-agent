<template>
  <div v-if="appStore.globalError" class="global-error" role="alert">
    <div class="global-error__copy">
      <strong>出了点小问题</strong>
      <span>{{ appStore.globalError }}</span>
    </div>
    <button type="button" @click="appStore.clearGlobalError">关闭</button>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/store/app'

const appStore = useAppStore()
</script>

<style scoped>
.global-error {
  position: fixed;
  top: var(--space-4);
  left: 50%;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  min-width: min(560px, calc(100vw - 32px));
  max-width: min(720px, calc(100vw - 32px));
  padding: var(--space-4);
  color: var(--color-danger);
  background: rgba(255, 253, 251, 0.96);
  border: 1px solid rgba(192, 96, 80, 0.18);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  transform: translateX(-50%);
  backdrop-filter: blur(10px);
}

.global-error__copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.global-error__copy strong {
  color: var(--color-text-primary);
}

.global-error__copy span {
  line-height: var(--line-height-normal);
}

.global-error button {
  min-height: 36px;
  padding: 0 var(--space-4);
  color: var(--color-text-primary);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  cursor: pointer;
}

@media (max-width: 640px) {
  .global-error {
    min-width: calc(100vw - 24px);
    padding: var(--space-3);
  }
}
</style>
