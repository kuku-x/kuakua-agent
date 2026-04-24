<template>
  <div :class="['ku-card', `ku-card--${padding}`, { 'ku-card--hoverable': hoverable }]">
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  padding?: 'sm' | 'md' | 'lg'
  hoverable?: boolean
}>(), {
  padding: 'md',
  hoverable: false
})
</script>

<style scoped>
.ku-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  transition: all var(--duration-fast) var(--ease-out);
}

.ku-card--sm {
  padding: var(--space-4);
}

.ku-card--md {
  padding: var(--space-6);
}

.ku-card--lg {
  padding: var(--space-8);
}

.ku-card--hoverable:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-strong);
}
</style>