<template>
  <div class="time-pie-chart">
    <div class="time-pie-chart__header">
      <div class="time-pie-chart__heading">
        <p class="time-pie-chart__eyebrow">Time Distribution</p>
        <h3>{{ title }}</h3>
      </div>
    </div>

    <div class="time-pie-chart__canvas">
      <Pie :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import { ArcElement, Chart as ChartJS, Legend, Tooltip, type Plugin } from 'chart.js'

const pieLabelPlugin: Plugin<'pie'> = {
  id: 'pieLabelPlugin',
  afterDatasetsDraw(chart) {
    const { ctx } = chart
    const dataset = chart.data.datasets[0]
    const meta = chart.getDatasetMeta(0)
    const values = (dataset.data as number[]) || []
    const total = values.reduce((sum, value) => sum + value, 0)

    if (!total) return

    ctx.save()
    meta.data.forEach((arc, index) => {
      const value = values[index]
      if (!value) return

      const percentage = Math.round((value / total) * 100)
      const pieArc = arc as unknown as {
        tooltipPosition: (useFinalPosition: boolean) => { x: number; y: number }
        outerRadius: number
        innerRadius: number
      }
      const position = pieArc.tooltipPosition(true)
      const radius = pieArc.outerRadius - pieArc.innerRadius
      if (radius < 36 || percentage < 8) return

      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = '#fffdfb'

      ctx.font = '600 14px "Microsoft YaHei UI", "PingFang SC", sans-serif'
      ctx.fillText(`${percentage}%`, position.x, position.y - 10)

      ctx.font = '500 12px "Microsoft YaHei UI", "PingFang SC", sans-serif'
      ctx.fillText(`${value.toFixed(1)}h`, position.x, position.y + 10)
    })
    ctx.restore()
  },
}

ChartJS.register(ArcElement, Tooltip, Legend, pieLabelPlugin)

interface Props {
  title: string
  workHours: number
  entertainmentHours: number
  otherHours: number
}

const props = defineProps<Props>()

function readCssVar(name: string, fallback: string) {
  if (typeof window === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

const chartValues = computed(() => [props.workHours, props.entertainmentHours, props.otherHours])

const chartData = computed(() => ({
  labels: ['工作', '娱乐', '其他'],
  datasets: [
    {
      data: chartValues.value,
      backgroundColor: [
        readCssVar('--color-accent', '#c98a69'),
        readCssVar('--color-warning', '#d4a84b'),
        readCssVar('--color-text-tertiary', '#b09a88'),
      ],
      borderColor: readCssVar('--color-bg-card', '#fffdfb'),
      borderWidth: 4,
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
        generateLabels(chart: ChartJS<'pie'>) {
          const labels = ['工作', '娱乐', '其他']
          const values = chartValues.value
          const total = values.reduce((sum, value) => sum + value, 0)

          return labels.map((label, index) => {
            const value = values[index]
            const percentage = total ? Math.round((value / total) * 100) : 0
            const style = Array.isArray(chart.data.datasets[0].backgroundColor)
              ? chart.data.datasets[0].backgroundColor[index]
              : chart.data.datasets[0].backgroundColor

            return {
              text: `${label} ${value.toFixed(1)}h · ${percentage}%`,
              fillStyle: style,
              strokeStyle: style,
              lineWidth: 0,
              hidden: false,
              index,
            }
          })
        },
      },
    },
    tooltip: {
      callbacks: {
        label(context: { label?: string; parsed: number }) {
          const total = chartValues.value.reduce((sum, value) => sum + value, 0)
          const percentage = total ? Math.round((context.parsed / total) * 100) : 0
          return `${context.label || ''}: ${context.parsed.toFixed(1)} 小时（${percentage}%）`
        },
      },
    },
  },
}))
</script>

<style scoped>
.time-pie-chart {
  display: flex;
  height: 100%;
  flex-direction: column;
  gap: var(--space-5);
}

.time-pie-chart__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
  flex-wrap: wrap;
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
