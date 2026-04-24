<template>
  <div :class="['ku-spinner', `ku-spinner--${size}`]" role="status">
    <span class="ku-spinner__circle"></span>
    <span class="ku-spinner__text" v-if="text">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  size?: 'sm' | 'md' | 'lg'
  text?: string
}>(), {
  size: 'md',
  text: ''
})
</script>

<style scoped>
.ku-spinner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
}

.ku-spinner--sm .ku-spinner__circle {
  width: 16px;
  height: 16px;
}

.ku-spinner--md .ku-spinner__circle {
  width: 24px;
  height: 24px;
}

.ku-spinner--lg .ku-spinner__circle {
  width: 40px;
  height: 40px;
}

.ku-spinner__circle {
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: ku-spin 0.8s linear infinite;
}

.ku-spinner__text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

@keyframes ku-spin {
  to { transform: rotate(360deg); }
}
</style>
