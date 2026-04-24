<template>
  <div class="time-pie-chart">
    <h3>时间分布</h3>
    <div class="chart-container">
      <Pie :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'
import type { SummaryData } from '@/store/summary'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  data: SummaryData
}>()

const chartData = computed(() => ({
  labels: ['工作', '娱乐', '其他'],
  datasets: [
    {
      data: [
        props.data.work_hours,
        props.data.entertainment_hours,
        props.data.other_hours,
      ],
      backgroundColor: ['#1890ff', '#fa8c16', '#999'],
      borderWidth: 0,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
    },
  },
}
</script>

<style scoped>
.time-pie-chart h3 {
  margin-bottom: 16px;
}

.chart-container {
  height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>