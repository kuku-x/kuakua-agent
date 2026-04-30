<template>
  <div v-if="visible" class="fallback-banner">
    <span>未配置 API Key，部分功能不可用</span>
    <button type="button" @click="$emit('goToSettings')">去设置</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ visible: boolean }>()
defineEmits<{ goToSettings: [] }>()
</script>

<style scoped>
.fallback-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: rgba(234, 179, 8, 0.15);
  border: 1px solid rgba(234, 179, 8, 0.3);
  border-radius: 8px;
  font-size: 13px;
  color: #92400e;
}

.fallback-banner button {
  padding: 4px 12px;
  background: transparent;
  border: 1px solid rgba(234, 179, 8, 0.5);
  border-radius: 4px;
  color: #92400e;
  font-size: 12px;
  cursor: pointer;
}

.fallback-banner button:hover {
  background: rgba(234, 179, 8, 0.1);
}
</style>