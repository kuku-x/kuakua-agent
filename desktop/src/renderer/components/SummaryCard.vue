<template>
  <div class="summary-card">
    <div class="praise-section">
      <div class="praise-icon">✨</div>
      <p class="praise-text">{{ summary.praise_text }}</p>
    </div>

    <div class="stats-section">
      <div class="stat-item">
        <div class="stat-value">{{ summary.total_hours }}</div>
        <div class="stat-label">总时长(h)</div>
      </div>
      <div class="stat-item work">
        <div class="stat-value">{{ summary.work_hours }}</div>
        <div class="stat-label">工作(h)</div>
      </div>
      <div class="stat-item entertainment">
        <div class="stat-value">{{ summary.entertainment_hours }}</div>
        <div class="stat-label">娱乐(h)</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ summary.focus_score }}</div>
        <div class="stat-label">专注分</div>
      </div>
    </div>

    <div class="suggestions-section" v-if="summary.suggestions?.length">
      <h4>💡 建议</h4>
      <ul>
        <li v-for="(suggestion, index) in summary.suggestions" :key="index">
          {{ suggestion }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SummaryData } from '@/store/summary'

defineProps<{
  summary: SummaryData
}>()
</script>

<style scoped>
.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.praise-section {
  text-align: center;
  margin-bottom: 32px;
}

.praise-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.praise-text {
  font-size: 20px;
  line-height: 1.6;
  font-weight: 500;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-item {
  background: rgba(255, 255, 255, 0.2);
  padding: 16px;
  border-radius: 12px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
  margin-top: 4px;
}

.suggestions-section {
  background: rgba(255, 255, 255, 0.15);
  padding: 20px;
  border-radius: 12px;
}

.suggestions-section h4 {
  margin-bottom: 12px;
  font-size: 14px;
}

.suggestions-section ul {
  list-style: none;
  padding: 0;
}

.suggestions-section li {
  padding: 8px 0;
  font-size: 14px;
  opacity: 0.95;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.suggestions-section li:last-child {
  border-bottom: none;
}
</style>