<template>
  <KuCard padding="lg" class="weather-card">
    <div class="weather-card__header">
      <div>
        <p class="weather-card__eyebrow">Weather</p>
        <h3>{{ weather?.city || draft.city }}</h3>
      </div>
      <button class="weather-card__config-toggle" type="button" @click="editing = !editing">
        {{ editing ? '收起' : '设置' }}
      </button>
    </div>

    <form v-if="editing" class="weather-card__form" @submit.prevent="saveAndRefresh">
      <label class="weather-card__field">
        <span>城市</span>
        <input v-model="draft.city" type="text" placeholder="深圳" />
      </label>
      <label class="weather-card__field">
        <span>纬度</span>
        <input v-model="draft.latitude" type="text" placeholder="22.5431" />
      </label>
      <label class="weather-card__field">
        <span>经度</span>
        <input v-model="draft.longitude" type="text" placeholder="114.0579" />
      </label>
      <div class="weather-card__form-actions">
        <button class="weather-card__button weather-card__button--primary" type="submit">保存</button>
        <button class="weather-card__button" type="button" @click="resetDraft">重置</button>
      </div>
    </form>

    <div v-if="loading" class="weather-card__skeleton" aria-hidden="true">
      <div class="weather-card__skeleton-main">
        <div class="weather-card__skeleton-copy">
          <div class="weather-card__skeleton-line weather-card__skeleton-line--city"></div>
          <div class="weather-card__skeleton-line weather-card__skeleton-line--temp"></div>
          <div class="weather-card__skeleton-line weather-card__skeleton-line--meta"></div>
        </div>
        <div class="weather-card__skeleton-art"></div>
      </div>
    </div>

    <div v-else-if="error" class="weather-card__state weather-card__state--error">
      <p>{{ error }}</p>
      <button class="weather-card__button" type="button" @click="fetchWeather">重试</button>
    </div>

    <div v-else-if="weather" class="weather-card__content">
      <div class="weather-card__copy">
        <div class="weather-card__headline">
          <p class="weather-card__temperature">{{ weather.temperature }}℃</p>
          <p class="weather-card__condition">{{ weather.condition }}</p>
        </div>
        <p class="weather-card__meta">
          体感温度 {{ weather.apparentTemperature ?? weather.temperature }}℃ · {{ weather.windText }}
        </p>
      </div>

      <div class="weather-card__art" :class="`weather-card__art--${illustrationType}`" aria-hidden="true">
        <div v-if="illustrationType === 'sunny'" class="weather-art weather-art--sunny">
          <div class="weather-art__sun-core"></div>
          <span v-for="n in 8" :key="n" class="weather-art__sun-ray" :style="sunRayStyle(n)"></span>
        </div>

        <div v-else-if="illustrationType === 'cloudy'" class="weather-art weather-art--cloudy">
          <div class="weather-art__cloud weather-art__cloud--large"></div>
          <div class="weather-art__cloud weather-art__cloud--small"></div>
        </div>

        <div v-else-if="illustrationType === 'rainy'" class="weather-art weather-art--rainy">
          <div class="weather-art__cloud weather-art__cloud--large"></div>
          <div class="weather-art__cloud weather-art__cloud--small"></div>
          <span v-for="n in 4" :key="n" class="weather-art__rain-drop" :style="rainDropStyle(n)"></span>
        </div>

        <div v-else-if="illustrationType === 'snowy'" class="weather-art weather-art--snowy">
          <div class="weather-art__cloud weather-art__cloud--large"></div>
          <span v-for="n in 3" :key="n" class="weather-art__snowflake" :style="snowStyle(n)">✦</span>
        </div>

        <div v-else-if="illustrationType === 'stormy'" class="weather-art weather-art--stormy">
          <div class="weather-art__cloud weather-art__cloud--large"></div>
          <div class="weather-art__cloud weather-art__cloud--small"></div>
          <div class="weather-art__lightning"></div>
        </div>

        <div v-else class="weather-art weather-art--foggy">
          <div class="weather-art__mist"></div>
          <div class="weather-art__mist weather-art__mist--mid"></div>
          <div class="weather-art__mist weather-art__mist--low"></div>
        </div>
      </div>
    </div>
  </KuCard>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, watch } from 'vue'
import KuCard from '@/components/base/KuCard.vue'
import { useWeatherWidget } from '@/hooks/useWeatherWidget'

const { config, weather, loading, error, fetchWeather, updateConfig } = useWeatherWidget()

const draft = reactive({
  city: config.value.city,
  latitude: config.value.latitude,
  longitude: config.value.longitude,
})

const editing = defineModel<boolean>('editing', { default: false })

const illustrationType = computed(() => {
  const code = weather.value?.weatherCode
  if (code === null || code === undefined) return 'cloudy'
  if (code === 0 || code === 1) return 'sunny'
  if (code === 2 || code === 3) return 'cloudy'
  if (code === 45 || code === 48) return 'foggy'
  if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) return 'rainy'
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) return 'snowy'
  if (code >= 95) return 'stormy'
  return 'cloudy'
})

watch(
  () => config.value,
  (value) => {
    draft.city = value.city
    draft.latitude = value.latitude
    draft.longitude = value.longitude
  },
  { deep: true },
)

onMounted(() => {
  fetchWeather()
})

async function saveAndRefresh() {
  updateConfig({
    city: draft.city,
    latitude: draft.latitude,
    longitude: draft.longitude,
  })
  editing.value = false
  await fetchWeather()
}

function resetDraft() {
  draft.city = config.value.city
  draft.latitude = config.value.latitude
  draft.longitude = config.value.longitude
}

function sunRayStyle(index: number) {
  const angle = (index - 1) * 45
  return { transform: `translate(-50%, -50%) rotate(${angle}deg)` }
}

function rainDropStyle(index: number) {
  return { left: `${22 + index * 15}%`, animationDelay: `${index * 0.14}s` }
}

function snowStyle(index: number) {
  return { left: `${24 + index * 18}%`, top: `${62 + index * 6}%` }
}
</script>

<style scoped>
.weather-card {
  display: flex;
  height: 100%;
  min-height: 0;
  flex-direction: column;
  gap: var(--space-5);
  background:
    radial-gradient(circle at top right, rgba(201, 138, 105, 0.12), transparent 34%),
    linear-gradient(180deg, rgba(255, 253, 251, 0.98), rgba(244, 237, 229, 0.92)),
    var(--color-bg-card);
}

.weather-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.weather-card__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.weather-card__header h3 {
  font-size: clamp(1.8rem, 3vw, 2.5rem);
  line-height: 1.25;
  letter-spacing: -0.04em;
  color: var(--color-text-primary);
}

.weather-card__config-toggle,
.weather-card__button {
  border: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.7);
  color: var(--color-text-secondary);
  border-radius: var(--radius-full);
  padding: 8px 14px;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.weather-card__config-toggle:hover,
.weather-card__button:hover {
  color: var(--color-text-primary);
  border-color: var(--color-border-strong);
}

.weather-card__button--primary {
  background: var(--color-accent-soft);
  color: var(--color-accent-hover);
}

.weather-card__form {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-3);
  padding: var(--space-4);
  background: rgba(255, 255, 255, 0.48);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.weather-card__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.weather-card__field span {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.weather-card__field input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.82);
  color: var(--color-text-primary);
}

.weather-card__field input:focus {
  outline: none;
  border-color: rgba(201, 138, 105, 0.35);
  box-shadow: 0 0 0 3px rgba(201, 138, 105, 0.12);
}

.weather-card__form-actions {
  grid-column: 1 / -1;
  display: flex;
  gap: var(--space-3);
}

.weather-card__content,
.weather-card__state {
  display: flex;
  flex: 1;
  min-height: 0;
}

.weather-card__content {
  align-items: center;
  gap: var(--space-5);
}

.weather-card__copy {
  flex: 1;
  min-width: 0;
}

.weather-card__headline {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.weather-card__temperature {
  font-size: var(--font-size-4xl);
  line-height: 1;
  letter-spacing: -0.04em;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.weather-card__condition {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.weather-card__headline {
  align-items: flex-start;
}

.weather-card__copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.weather-card__meta {
  margin-top: var(--space-3);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
  color: var(--color-text-secondary);
}

.weather-card__state {
  justify-content: center;
}

.weather-card__state p {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.weather-card__state {
  flex-direction: column;
  justify-content: center;
}

.weather-card__state--error {
  gap: var(--space-4);
  color: var(--color-danger);
}

.weather-card__art {
  position: relative;
  width: 170px;
  height: 150px;
  flex-shrink: 0;
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(201, 138, 105, 0.1));
  border: 1px solid rgba(119, 104, 87, 0.08);
  overflow: hidden;
}

.weather-card__art::before {
  content: '';
  position: absolute;
  inset: auto -10% -34% 12%;
  height: 60%;
  background: radial-gradient(circle, rgba(201, 138, 105, 0.12), transparent 68%);
}

.weather-art {
  position: absolute;
  inset: 0;
}

.weather-art__sun-core {
  position: absolute;
  top: 36px;
  right: 34px;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #ffe6a3, #e3b862 72%);
  box-shadow: 0 0 28px rgba(227, 184, 98, 0.24);
}

.weather-art__sun-ray {
  position: absolute;
  top: 63px;
  right: 61px;
  width: 6px;
  height: 22px;
  border-radius: 999px;
  background: rgba(227, 184, 98, 0.7);
  transform-origin: center -20px;
}

.weather-art__cloud {
  position: absolute;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(231, 220, 209, 0.95));
  border-radius: 999px;
  box-shadow: 0 10px 24px rgba(130, 106, 88, 0.08);
}

.weather-art__cloud::before,
.weather-art__cloud::after {
  content: '';
  position: absolute;
  background: inherit;
  border-radius: 50%;
}

.weather-art__cloud--large {
  left: 28px;
  top: 56px;
  width: 98px;
  height: 38px;
}

.weather-art__cloud--large::before {
  left: 12px;
  bottom: 16px;
  width: 34px;
  height: 34px;
}

.weather-art__cloud--large::after {
  right: 14px;
  bottom: 12px;
  width: 42px;
  height: 42px;
}

.weather-art__cloud--small {
  right: 24px;
  top: 74px;
  width: 56px;
  height: 24px;
  opacity: 0.88;
}

.weather-art__cloud--small::before {
  left: 8px;
  bottom: 10px;
  width: 20px;
  height: 20px;
}

.weather-art__cloud--small::after {
  right: 8px;
  bottom: 8px;
  width: 24px;
  height: 24px;
}

.weather-art__rain-drop {
  position: absolute;
  top: 100px;
  width: 8px;
  height: 18px;
  border-radius: 999px 999px 999px 999px / 60% 60% 40% 40%;
  background: linear-gradient(180deg, rgba(122, 159, 191, 0.2), rgba(122, 159, 191, 0.72));
  transform: rotate(12deg);
  animation: weather-rain 1.6s ease-in-out infinite;
}

.weather-art__snowflake {
  position: absolute;
  color: rgba(122, 159, 191, 0.8);
  font-size: 18px;
}

.weather-art__lightning {
  position: absolute;
  left: 68px;
  top: 92px;
  width: 28px;
  height: 42px;
  background: linear-gradient(180deg, #f3d37f, #d6a84e);
  clip-path: polygon(42% 0, 100% 0, 60% 46%, 88% 46%, 24% 100%, 42% 58%, 14% 58%);
  filter: drop-shadow(0 8px 10px rgba(214, 168, 78, 0.22));
}

.weather-art__mist {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 62px;
  height: 12px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(233, 226, 219, 0.4), rgba(233, 226, 219, 0.95), rgba(233, 226, 219, 0.4));
}

.weather-art__mist--mid {
  top: 86px;
  left: 18px;
  right: 18px;
}

.weather-art__mist--low {
  top: 110px;
  left: 30px;
  right: 30px;
}

.weather-card__art--sunny {
  background: linear-gradient(180deg, rgba(255, 246, 222, 0.82), rgba(255, 255, 255, 0.74));
}

.weather-card__art--rainy,
.weather-card__art--stormy {
  background: linear-gradient(180deg, rgba(238, 233, 227, 0.9), rgba(219, 206, 196, 0.72));
}

.weather-card__art--snowy,
.weather-card__art--cloudy,
.weather-card__art--foggy {
  background: linear-gradient(180deg, rgba(250, 247, 243, 0.9), rgba(232, 223, 215, 0.76));
}

.weather-card__skeleton {
  display: flex;
  min-height: 180px;
  flex-direction: column;
  justify-content: center;
}

.weather-card__skeleton-main {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.weather-card__skeleton-copy {
  flex: 1;
}

.weather-card__skeleton-art {
  width: 170px;
  height: 150px;
  flex-shrink: 0;
  border-radius: 28px;
  background: linear-gradient(
    90deg,
    rgba(201, 138, 105, 0.08),
    rgba(201, 138, 105, 0.16),
    rgba(201, 138, 105, 0.08)
  );
  background-size: 200% 100%;
  animation: weather-card-shimmer 1.4s linear infinite;
}

.weather-card__skeleton-line {
  border-radius: var(--radius-full);
  background: linear-gradient(
    90deg,
    rgba(201, 138, 105, 0.08),
    rgba(201, 138, 105, 0.18),
    rgba(201, 138, 105, 0.08)
  );
  background-size: 200% 100%;
  animation: weather-card-shimmer 1.4s linear infinite;
}

.weather-card__skeleton-line--city {
  width: 110px;
  height: 22px;
}

.weather-card__skeleton-line--temp {
  width: 180px;
  height: 56px;
  margin-top: var(--space-4);
}

.weather-card__skeleton-line--meta {
  width: 220px;
  height: 18px;
  margin-top: var(--space-4);
}

@keyframes weather-card-shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

@keyframes weather-rain {
  0%,
  100% {
    transform: translateY(0) rotate(12deg);
    opacity: 0.45;
  }

  50% {
    transform: translateY(10px) rotate(12deg);
    opacity: 0.9;
  }
}

@media (max-width: 960px) {
  .weather-card__form {
    grid-template-columns: 1fr;
  }

  .weather-card__content,
  .weather-card__skeleton-main {
    flex-direction: column;
    align-items: stretch;
  }

  .weather-card__art,
  .weather-card__skeleton-art {
    width: 100%;
  }
}
</style>
