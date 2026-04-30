<template>
  <KuCard padding="lg" class="timeline-card">
    <div class="timeline-card__head">
      <p class="timeline-card__eyebrow">Today Timeline</p>
      <h3>今天是怎么展开的</h3>
    </div>

    <div v-if="loading" class="timeline-card__state">
      <KuSpinner text="加载时间线..." />
    </div>

    <div v-else-if="error" class="timeline-card__state timeline-card__state--error">
      <p class="timeline-card__empty">{{ error }}</p>
    </div>

    <div v-else-if="!events.length" class="timeline-card__state">
      <p class="timeline-card__empty">还没有今天的时间线数据。</p>
    </div>

    <div v-else class="timeline-card__chart">
      <!-- Hour labels -->
      <div class="timeline-card__hours">
        <span
          v-for="h in hours"
          :key="h"
          class="timeline-card__hour"
          :style="{ gridRow: rowForHour(h) }"
        >
          {{ String(h).padStart(2, '0') }}:00
        </span>
      </div>

      <!-- App bars -->
      <div class="timeline-card__bars">
        <div
          v-for="block in blocks"
          :key="block.key"
          class="timeline-card__bar"
          :class="`timeline-card__bar--${block.category}`"
          :style="{
            top: `${block.top}%`,
            height: `${block.height}%`,
          }"
          :title="`${block.app} · ${block.duration} · ${block.time}`"
        >
          <span class="timeline-card__bar-label">{{ block.app }}</span>
          <span class="timeline-card__bar-time">{{ block.duration }}</span>
        </div>
      </div>
    </div>
  </KuCard>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KuCard from '@/components/base/KuCard.vue'
import KuSpinner from '@/components/base/KuSpinner.vue'
import api from '@/api'

interface TimelineEntry {
  time: string
  hour: number
  app: string
  duration_seconds: number
  category: string
  title: string
}

interface Block {
  key: string
  app: string
  time: string
  duration: string
  category: string
  top: number
  height: number
}

const events = ref<TimelineEntry[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const HOURS = 24

const hours = Array.from({ length: HOURS }, (_, i) => i)

// Merge consecutive same-app events into visual blocks
const blocks = computed<Block[]>(() => {
  if (!events.value.length) return []

  const merged: TimelineEntry[] = []
  let current = { ...events.value[0] }

  for (let i = 1; i < events.value.length; i++) {
    const e = events.value[i]
    if (e.app === current.app && e.hour === current.hour) {
      current.duration_seconds += e.duration_seconds
    } else {
      merged.push({ ...current })
      current = { ...e }
    }
  }
  merged.push({ ...current })

  const activeStart = merged[0].hour
  const activeEnd = merged[merged.length - 1].hour + 1
  const activeSpan = Math.max(activeEnd - activeStart, 1)

  return merged.map((e, i) => {
    const top = ((e.hour - activeStart) / activeSpan) * 100
    const segs = Math.max(e.duration_seconds / 60, 2)
    const height = Math.min((segs / (activeSpan * 60)) * 100, 20)

    return {
      key: `${e.time}-${i}`,
      app: e.app,
      time: e.time,
      duration: formatMins(e.duration_seconds),
      category: e.category,
      top: Math.max(top, 0),
      height: Math.max(height, 3),
    }
  })
})

function rowForHour(h: number) {
  return h + 2
}

function formatMins(secs: number) {
  if (secs < 60) return `${secs}s`
  if (secs < 3600) return `${Math.round(secs / 60)}m`
  return `${(secs / 3600).toFixed(1)}h`
}

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/summary/timeline')
    if (res.data.status === 'success') {
      events.value = res.data.data || []
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.timeline-card {
  grid-column: 1 / -1;
}

.timeline-card__head {
  margin-bottom: var(--space-5);
}

.timeline-card__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.timeline-card__head h3 {
  font-size: var(--font-size-2xl);
}

.timeline-card__state {
  display: flex;
  min-height: 180px;
  align-items: center;
  justify-content: center;
}

.timeline-card__empty {
  color: var(--color-text-secondary);
}

.timeline-card__state--error .timeline-card__empty {
  color: var(--color-danger);
}

.timeline-card__chart {
  position: relative;
  min-height: 320px;
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: var(--space-3);
}

.timeline-card__hours {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 4px 0;
}

.timeline-card__hour {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  text-align: right;
}

.timeline-card__bars {
  position: relative;
  min-height: 100%;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.timeline-card__bar {
  position: absolute;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-3);
  border-radius: 3px;
  overflow: hidden;
  transition: opacity var(--duration-fast);
}

.timeline-card__bar:hover {
  opacity: 0.85;
}

.timeline-card__bar--work {
  background: linear-gradient(90deg, rgba(201, 138, 105, 0.5), rgba(201, 138, 105, 0.35));
}

.timeline-card__bar--entertainment {
  background: linear-gradient(90deg, rgba(212, 168, 75, 0.5), rgba(212, 168, 75, 0.35));
}

.timeline-card__bar--other {
  background: linear-gradient(90deg, rgba(155, 143, 128, 0.4), rgba(155, 143, 128, 0.25));
}

.timeline-card__bar-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.timeline-card__bar-time {
  font-size: 11px;
  color: var(--color-text-secondary);
  flex-shrink: 0;
  margin-left: var(--space-2);
}
</style>
