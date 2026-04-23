<template>
  <div v-if="appStore.globalError" class="global-error" role="alert">
    <span>{{ appStore.globalError }}</span>
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
  top: 16px;
  left: 50%;
  z-index: 1000;
  display: flex;
  max-width: min(560px, calc(100vw - 32px));
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  color: #7a1f1f;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
  transform: translateX(-50%);
}

.global-error button {
  flex: 0 0 auto;
  padding: 4px 10px;
  color: #7a1f1f;
  cursor: pointer;
  background: transparent;
  border: 1px solid #ffaaa5;
  border-radius: 6px;
}
</style>

