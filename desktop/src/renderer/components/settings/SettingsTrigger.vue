<template>
  <button
    class="settings-trigger"
    type="button"
    aria-label="打开设置"
    title="打开设置"
  >
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="3.2" />
      <path d="M19.4 15a1 1 0 0 0 .2 1.1l.1.1a2 2 0 0 1 0 2.8 2 2 0 0 1-2.8 0l-.1-.1a1 1 0 0 0-1.1-.2 1 1 0 0 0-.6.9V20a2 2 0 0 1-4 0v-.2a1 1 0 0 0-.7-.9 1 1 0 0 0-1.1.2l-.1.1a2 2 0 0 1-2.8 0 2 2 0 0 1 0-2.8l.1-.1a1 1 0 0 0 .2-1.1 1 1 0 0 0-.9-.6H4a2 2 0 0 1 0-4h.2a1 1 0 0 0 .9-.7 1 1 0 0 0-.2-1.1l-.1-.1a2 2 0 0 1 0-2.8 2 2 0 0 1 2.8 0l.1.1a1 1 0 0 0 1.1.2h.1a1 1 0 0 0 .6-.9V4a2 2 0 0 1 4 0v.2a1 1 0 0 0 .6.9 1 1 0 0 0 1.1-.2l.1-.1a2 2 0 0 1 2.8 0 2 2 0 0 1 0 2.8l-.1.1a1 1 0 0 0-.2 1.1v.1a1 1 0 0 0 .9.6H20a2 2 0 0 1 0 4h-.2a1 1 0 0 0-.9.6Z" />
    </svg>
  </button>
</template>

<style scoped>
.settings-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  color: var(--color-text-secondary);
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-xs);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.settings-trigger:hover {
  color: var(--color-text-primary);
  background: rgba(255, 255, 255, 0.92);
  border-color: var(--color-border-strong);
  transform: translateY(-1px) rotate(10deg);
}

.settings-trigger svg {
  width: 20px;
  height: 20px;
}
</style>
