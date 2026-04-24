<template>
  <button
    :class="['ku-button', `ku-button--${variant}`, `ku-button--${size}`, { 'ku-button--disabled': disabled || loading }]"
    :disabled="disabled || loading"
    :type="type"
    :aria-busy="loading"
  >
    <span v-if="loading" class="ku-button__spinner"></span>
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  type?: 'button' | 'submit' | 'reset'
}>(), {
  variant: 'secondary',
  size: 'md',
  disabled: false,
  loading: false,
  type: 'button'
})
</script>

<style scoped>
.ku-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-weight: var(--font-weight-medium);
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  white-space: nowrap;
}

.ku-button--sm {
  min-height: 32px;
  padding: 0 var(--space-3);
  font-size: var(--font-size-sm);
}

.ku-button--md {
  min-height: 44px;
  padding: 0 var(--space-5);
  font-size: var(--font-size-base);
}

.ku-button--lg {
  min-height: 52px;
  padding: 0 var(--space-6);
  font-size: var(--font-size-lg);
}

.ku-button--primary {
  color: var(--color-text-inverse);
  background: var(--color-accent);
  border-color: var(--color-accent);
}

.ku-button--primary:hover:not(:disabled) {
  background: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
}

.ku-button--secondary {
  color: var(--color-text-primary);
  background: var(--color-bg-card);
  border-color: var(--color-border);
}

.ku-button--secondary:hover:not(:disabled) {
  background: var(--color-bg-elevated);
  border-color: var(--color-border-strong);
}

.ku-button--ghost {
  color: var(--color-text-secondary);
  background: transparent;
  border-color: transparent;
}

.ku-button--ghost:hover:not(:disabled) {
  color: var(--color-text-primary);
  background: var(--color-accent-soft);
}

.ku-button--danger {
  color: var(--color-text-inverse);
  background: var(--color-danger);
  border-color: var(--color-danger);
}

.ku-button--disabled,
.ku-button--disabled:hover {
  opacity: 0.5;
  cursor: not-allowed;
}

.ku-button__spinner {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
