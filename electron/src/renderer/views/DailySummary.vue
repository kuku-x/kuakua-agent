<template>
  <div class="daily-summary">
    <h1>今日夸夸</h1>

    <div v-if="store.loading" class="loading">
      <p>正在生成今日夸夸～</p>
    </div>

    <div v-else-if="store.error" class="error">
      <p>{{ store.error }}</p>
      <button @click="refresh">重试</button>
    </div>

    <div v-else-if="store.summary" class="summary-content">
      <SummaryCard :summary="store.summary" />

      <div class="charts">
        <TimePieChart :data="store.summary" />
      </div>

      <div class="apps-list">
        <h3>今日应用</h3>
        <div class="app-item" v-for="app in store.summary.top_apps" :key="app.name">
          <span class="app-name">{{ app.name }}</span>
          <span class="app-duration">{{ app.duration.toFixed(1) }}h</span>
          <span class="app-category" :class="app.category">{{ app.category }}</span>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>暂无数据，请确保ActivityWatch正在运行</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useSummaryStore } from '@/store/summary'
import SummaryCard from '@/components/SummaryCard.vue'
import TimePieChart from '@/components/TimePieChart.vue'

const store = useSummaryStore()

onMounted(() => {
  store.fetchTodaySummary()
})

function refresh() {
  store.fetchTodaySummary()
}
</script>

<style scoped>
.daily-summary {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  text-align: center;
  margin-bottom: 24px;
  color: #333;
}

.loading, .error, .empty {
  text-align: center;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
}

.loading {
  color: #666;
}

.error {
  color: #ff4d4f;
}

button {
  margin-top: 16px;
  padding: 8px 24px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.charts {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
}

.apps-list {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
}

.apps-list h3 {
  margin-bottom: 16px;
}

.app-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.app-item:last-child {
  border-bottom: none;
}

.app-name {
  flex: 1;
}

.app-duration {
  color: #666;
  margin-right: 12px;
}

.app-category {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.app-category.work {
  background: #e6f7ff;
  color: #1890ff;
}

.app-category.entertainment {
  background: #fff7e6;
  color: #fa8c16;
}

.app-category.other {
  background: #f5f5f5;
  color: #999;
}
</style>