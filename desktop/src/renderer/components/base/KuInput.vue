<template>
  <div class="ku-input-wrapper">
    <label v-if="label" class="ku-input__label">{{ label }}</label>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      class="ku-input"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <span v-if="hint" class="ku-input__hint">{{ hint }}</span>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  modelValue?: string
  type?: 'text' | 'password' | 'email'
  placeholder?: string
  label?: string
  hint?: string
  disabled?: boolean
}>(), {
  modelValue: '',
  type: 'text',
  placeholder: '',
  label: '',
  hint: '',
  disabled: false
})

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<style scoped>
.ku-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.ku-input__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.ku-input {
  width: 100%;
  min-height: 48px;
  padding: 0 var(--space-4);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  transition: all var(--duration-fast) var(--ease-out);
}

.ku-input:focus {
  border-color: var(--color-accent);
  outline: none;
}

.ku-input::placeholder {
  color: var(--color-text-tertiary);
}

.ku-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ku-input__hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
