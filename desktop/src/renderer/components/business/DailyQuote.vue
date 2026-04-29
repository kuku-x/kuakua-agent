<template>
  <div class="daily-quote">
    <div v-if="loading" class="daily-quote__loading">
      <span class="daily-quote__dot"></span>
      <span class="daily-quote__dot"></span>
      <span class="daily-quote__dot"></span>
    </div>

    <template v-else-if="quote">
      <p class="daily-quote__text">「{{ quote.hitokoto }}」</p>
      <p class="daily-quote__from">
        <span v-if="quote.from">—— {{ quote.from }}</span>
        <span v-if="quote.from_who">《{{ quote.from_who }}》</span>
      </p>
    </template>

    <button class="daily-quote__refresh" @click="handleRefresh" :disabled="loading">
      <svg v-if="!loading" class="daily-quote__refresh-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M1 4v6h6M23 20v-6h-6" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>{{ loading ? '加载中...' : '换一句' }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useHitokoto } from '@/hooks/useHitokoto'

const { quote, loading, fetchQuote, refreshQuote } = useHitokoto()

onMounted(() => {
  fetchQuote()
})

async function handleRefresh() {
  await refreshQuote()
}
</script>

<style scoped>
.daily-quote {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-6) var(--space-5);
  text-align: center;
}

.daily-quote__loading {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-4) 0;
}

.daily-quote__dot {
  width: 8px;
  height: 8px;
  background: var(--color-text-tertiary);
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite both;
}

.daily-quote__dot:nth-child(1) { animation-delay: -0.32s; }
.daily-quote__dot:nth-child(2) { animation-delay: -0.16s; }
.daily-quote__dot:nth-child(3) { animation-delay: 0s; }

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.daily-quote__text {
  font-size: var(--font-size-lg);
  line-height: 1.8;
  color: var(--color-text-primary);
  max-width: 480px;
}

.daily-quote__from {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

.daily-quote__from span {
  margin: 0 var(--space-1);
}

.daily-quote__refresh {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  color: var(--color-text-secondary);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.daily-quote__refresh:hover:not(:disabled) {
  color: var(--color-accent);
  border-color: var(--color-accent-soft);
  background: rgba(201, 138, 105, 0.06);
}

.daily-quote__refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.daily-quote__refresh-icon {
  width: 14px;
  height: 14px;
}

.daily-quote__refresh:hover:not(:disabled) .daily-quote__refresh-icon {
  animation: spin 1s ease-in-out;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
