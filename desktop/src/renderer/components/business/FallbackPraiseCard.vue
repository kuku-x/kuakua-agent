<template>
  <KuCard class="fallback-card">
    <p class="fallback-card__praise">{{ praise }}</p>
    <p class="fallback-card__hint">— 模板夸夸（配置 API Key 解锁更多）</p>
  </KuCard>
</template>

<script setup lang="ts">
import KuCard from '@/components/base/KuCard.vue'
import { getRandomTemplatePraise } from '@/utils/praiseTemplates'

const praise = getRandomTemplatePraise()
</script>

<style scoped>
.fallback-card {
  padding: var(--space-5);
  text-align: center;
}

.fallback-card__praise {
  font-size: 1.1rem;
  color: var(--color-text-primary);
  line-height: 1.6;
  margin-bottom: var(--space-3);
}

.fallback-card__hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}
</style>