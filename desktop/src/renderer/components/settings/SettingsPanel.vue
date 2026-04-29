<template>
  <Teleport to="body">
    <transition name="settings-panel-fade">
      <div v-if="open" class="settings-panel" @click.self="emit('close')">
        <div class="settings-panel__backdrop"></div>
        <transition name="settings-panel-slide">
          <aside v-if="open" class="settings-panel__sheet" role="dialog" aria-modal="true" aria-label="设置面板">
            <header class="settings-panel__header">
              <div>
                <p class="settings-panel__eyebrow">Preferences</p>
                <h2>设置</h2>
              </div>
              <button class="settings-panel__close" type="button" aria-label="关闭设置" @click="emit('close')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 6 6 18" />
                  <path d="m6 6 12 12" />
                </svg>
              </button>
            </header>

            <div class="settings-panel__body">
              <SettingsPanelContent />
            </div>
          </aside>
        </transition>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import SettingsPanelContent from '@/components/settings/SettingsPanelContent.vue'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open) {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.settings-panel {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  justify-content: flex-end;
}

.settings-panel__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(38, 29, 22, 0.22);
  backdrop-filter: blur(4px);
}

.settings-panel__sheet {
  position: relative;
  z-index: 1;
  display: flex;
  width: min(720px, calc(100vw - 24px));
  height: calc(100vh - 24px);
  margin: 12px;
  flex-direction: column;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.7), rgba(250, 246, 241, 0.64)),
    rgba(250, 247, 244, 0.72);
  border: 1px solid rgba(126, 104, 84, 0.12);
  border-radius: 28px;
  box-shadow: 0 28px 64px rgba(48, 34, 26, 0.18);
  backdrop-filter: blur(20px);
  overflow: hidden;
}

.settings-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5);
  border-bottom: 1px solid rgba(126, 104, 84, 0.12);
}

.settings-panel__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.settings-panel__header h2 {
  font-size: clamp(1.8rem, 2vw, 2.2rem);
  letter-spacing: -0.03em;
}

.settings-panel__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  color: var(--color-text-secondary);
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.settings-panel__close:hover {
  color: var(--color-text-primary);
  background: rgba(255, 255, 255, 0.94);
}

.settings-panel__close svg {
  width: 18px;
  height: 18px;
}

.settings-panel__body {
  flex: 1;
  padding: 0 var(--space-5) var(--space-5);
  overflow-y: auto;
}

.settings-panel-fade-enter-active,
.settings-panel-fade-leave-active {
  transition: opacity var(--duration-normal) var(--ease-out);
}

.settings-panel-fade-enter-from,
.settings-panel-fade-leave-to {
  opacity: 0;
}

.settings-panel-slide-enter-active,
.settings-panel-slide-leave-active {
  transition:
    transform var(--duration-normal) var(--ease-out),
    opacity var(--duration-normal) var(--ease-out);
}

.settings-panel-slide-enter-from,
.settings-panel-slide-leave-to {
  opacity: 0;
  transform: translateX(24px) scale(0.98);
}

@media (max-width: 720px) {
  .settings-panel {
    justify-content: center;
    align-items: center;
    padding: 10px;
  }

  .settings-panel__sheet {
    width: 100%;
    height: min(92vh, 960px);
    margin: 0;
  }
}
</style>
