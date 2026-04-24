<template>
  <section class="summary-card">
    <div class="summary-card__lead">
      <span class="summary-card__badge">今日夸夸</span>
      <h3>{{ summary.praise_text }}</h3>
    </div>

    <div class="summary-card__stats">
      <article class="summary-card__stat">
        <span>总时长</span>
        <strong>{{ summary.total_hours }}</strong>
        <small>活跃小时</small>
      </article>
      <article class="summary-card__stat">
        <span>工作</span>
        <strong>{{ summary.work_hours }}</strong>
        <small>专注投入</small>
      </article>
      <article class="summary-card__stat">
        <span>娱乐</span>
        <strong>{{ summary.entertainment_hours }}</strong>
        <small>放松恢复</small>
      </article>
      <article class="summary-card__stat">
        <span>专注分</span>
        <strong>{{ summary.focus_score }}</strong>
        <small>满分 100</small>
      </article>
    </div>

    <div v-if="summary.suggestions?.length" class="summary-card__suggestions">
      <p class="summary-card__suggestions-title">温柔建议</p>
      <ul>
        <li v-for="(suggestion, index) in summary.suggestions" :key="index">{{ suggestion }}</li>
      </ul>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { SummaryData } from '@/store/summary'

defineProps<{
  summary: SummaryData
}>()
</script>

<style scoped>
.summary-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  padding: var(--space-8);
  background:
    radial-gradient(circle at top left, rgba(201, 138, 105, 0.18), transparent 30%),
    radial-gradient(circle at bottom right, rgba(212, 168, 75, 0.12), transparent 24%),
    var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
}

.summary-card__badge {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  margin-bottom: var(--space-3);
  padding: 0 var(--space-3);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
}

.summary-card__lead h3 {
  font-size: clamp(1.8rem, 3vw, 2.5rem);
  line-height: 1.25;
  letter-spacing: -0.04em;
}

.summary-card__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.summary-card__stat {
  display: flex;
  min-height: 120px;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-5);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.summary-card__stat span,
.summary-card__stat small,
.summary-card__suggestions-title {
  color: var(--color-text-secondary);
}

.summary-card__stat strong {
  font-size: var(--font-size-4xl);
  letter-spacing: -0.04em;
}

.summary-card__suggestions {
  padding: var(--space-5);
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.summary-card__suggestions-title {
  margin-bottom: var(--space-3);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.summary-card__suggestions ul {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.summary-card__suggestions li {
  padding-top: var(--space-3);
  line-height: var(--line-height-relaxed);
  border-top: 1px solid var(--color-border);
}

.summary-card__suggestions li:first-child {
  padding-top: 0;
  border-top: none;
}

@media (max-width: 720px) {
  .summary-card {
    padding: var(--space-6);
  }

  .summary-card__stats {
    grid-template-columns: 1fr;
  }
}
</style>
