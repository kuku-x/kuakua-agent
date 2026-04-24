<template>
  <div class="time-pie-chart">
    <div class="time-pie-chart__heading">
      <p class="time-pie-chart__eyebrow">Time Distribution</p>
      <h3>今天的时间是怎么分布的</h3>
    </div>
    <div class="time-pie-chart__canvas">
      <Pie :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import { ArcElement, Chart as ChartJS, Legend, Tooltip } from 'chart.js'
import type { SummaryData } from '@/store/summary'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  data: SummaryData
}>()

function readCssVar(name: string, fallback: string) {
  if (typeof window === 'undefined') return fallback

  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

const chartData = computed(() => ({
  labels: ['工作', '娱乐', '其他'],
  datasets: [
    {
      data: [props.data.work_hours, props.data.entertainment_hours, props.data.other_hours],
      backgroundColor: [
        readCssVar('--color-accent', '#c98a69'),
        readCssVar('--color-warning', '#d4a84b'),
        readCssVar('--color-text-tertiary', '#b09a88'),
      ],
      borderColor: 'transparent',
      hoverOffset: 8,
    },
  ],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        color: readCssVar('--color-text-secondary', '#8a7160'),
        usePointStyle: true,
        boxWidth: 10,
        boxHeight: 10,
      },
    },
  },
}))
</script>

<style scoped>
.time-pie-chart {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.time-pie-chart__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.time-pie-chart__heading h3 {
  font-size: var(--font-size-2xl);
  line-height: 1.4;
}

.time-pie-chart__canvas {
  height: 320px;
  min-width: 0;
}
</style>
