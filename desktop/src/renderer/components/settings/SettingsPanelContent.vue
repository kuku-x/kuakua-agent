<template>
  <div class="settings-sheet">
    <section class="settings-sheet__section">
      <div class="settings-sheet__head">
        <p class="settings-sheet__eyebrow">Source & Model</p>
        <h3>模型与数据来源</h3>
      </div>

      <div class="settings-sheet__stack">
        <div class="settings-sheet__field">
          <KuInput
            v-model="apiKeyInput"
            type="password"
            label="模型 API Key"
            placeholder="请输入新的 API Key"
            :hint="
              apiKeySet
                ? '当前已经配置密钥，留空则保持现有设置。'
                : '用于聊天与每日摘要生成。'
            "
          />
        </div>

        <div class="settings-sheet__field">
          <KuInput
            v-model="settings.aw_server_url"
            label="ActivityWatch 地址"
            placeholder="http://127.0.0.1:5600"
            hint="填写你本地 ActivityWatch 服务的访问地址。"
          />
        </div>

        <div class="settings-sheet__field settings-sheet__field--status">
          <div class="settings-sheet__status-row">
            <p class="settings-sheet__status-label">ActivityWatch 状态</p>
            <span
              class="settings-sheet__status-badge"
              :class="awStatus?.connected ? 'settings-sheet__status-badge--ok' : 'settings-sheet__status-badge--error'"
            >
              {{ awStatusLoading ? '检测中...' : awStatus?.connected ? '已连接' : '未连接' }}
            </span>
          </div>
        </div>

        <div class="settings-sheet__field">
          <KuInput
            v-model="settings.openweather_location"
            label="天气位置"
            placeholder="Shanghai,CN"
            hint="免费天气服务无需 API Key，支持城市名或 城市,国家代码，例如 Shanghai,CN。"
          />
        </div>

        <div class="settings-sheet__field">
          <KuInput
            v-model="fishAudioApiKeyInput"
            type="password"
            label="Fish Audio API Key"
            placeholder="请输入 Fish Audio API Key"
            :hint="
              settings.fish_audio_api_key_set
                ? '当前已经配置 Fish Audio 密钥，留空则保持现有设置。'
                : '用于将夸夸内容转换成语音播报。'
            "
          />
        </div>

        <div class="settings-sheet__field">
          <KuInput
            v-model="settings.fish_audio_model"
            label="Fish Audio 模型"
            placeholder="s2-pro"
            hint="Fish Audio 请求头中的 model 值，默认使用 s2-pro。"
          />
        </div>

        <div class="settings-sheet__toggle">
          <div>
            <p>数据脱敏</p>
            <small>在摘要结果中隐藏更细的应用名称，降低隐私暴露风险。</small>
          </div>
          <label class="settings-sheet__switch">
            <input v-model="settings.data_masking" type="checkbox" />
            <span></span>
          </label>
        </div>
      </div>

      <div class="settings-sheet__actions">
        <KuButton variant="primary" :loading="saving" @click="saveSettings">
          {{ saving ? '保存中...' : '保存设置' }}
        </KuButton>

        <p
          v-if="saveMessage"
          class="settings-sheet__message"
          :class="saveSuccess ? 'settings-sheet__message--success' : 'settings-sheet__message--error'"
        >
          {{ saveMessage }}
        </p>
      </div>
    </section>

    <section class="settings-sheet__section">
      <div class="settings-sheet__head">
        <p class="settings-sheet__eyebrow">Praise</p>
        <h3>夸夸 Agent</h3>
      </div>

      <div class="settings-sheet__stack">
        <div class="settings-sheet__toggle">
          <div>
            <p>主动夸夸</p>
            <small>开启后，夸夸 Agent 会根据时间与行为组合规则自动发起夸夸。</small>
          </div>
          <label class="settings-sheet__switch">
            <input v-model="praise.praise_auto_enable" type="checkbox" />
            <span></span>
          </label>
        </div>

        <div class="settings-sheet__toggle">
          <div>
            <p>语音播报</p>
            <small>开启后，夸夸内容会通过 Fish Audio 生成语音并本地播放。</small>
          </div>
          <label class="settings-sheet__switch">
            <input v-model="praise.tts_enable" type="checkbox" />
            <span></span>
          </label>
        </div>

        <div class="settings-sheet__field">
          <KuInput
            v-model="praise.tts_voice"
            label="Fish Voice ID"
            placeholder="请输入 Fish Audio reference_id"
          />
        </div>

        <div class="settings-sheet__field">
          <KuInput
            :model-value="String(praise.tts_speed)"
            type="text"
            label="语速"
            placeholder="1.0"
            @update:model-value="praise.tts_speed = Number($event)"
          />
        </div>

        <div class="settings-sheet__field">
          <KuInput
            v-model="praise.do_not_disturb_start"
            label="免打扰开始时间"
            placeholder="22:00"
          />
        </div>

        <div class="settings-sheet__field">
          <KuInput
            v-model="praise.do_not_disturb_end"
            label="免打扰结束时间"
            placeholder="08:00"
          />
        </div>

        <div class="settings-sheet__field">
          <KuInput
            :model-value="String(praise.max_praises_per_day)"
            type="text"
            label="每日夸夸上限"
            placeholder="10"
            @update:model-value="praise.max_praises_per_day = Number($event)"
          />
        </div>

        <div class="settings-sheet__field">
          <KuInput
            :model-value="String(praise.global_cooldown_minutes)"
            type="text"
            label="全局冷却时间（分钟）"
            placeholder="30"
            @update:model-value="praise.global_cooldown_minutes = Number($event)"
          />
        </div>
      </div>

      <div class="settings-sheet__actions">
        <KuButton variant="primary" :loading="praiseLoading" @click="savePraiseConfig">
          {{ praiseLoading ? '保存中...' : '保存夸夸设置' }}
        </KuButton>
        <p
          v-if="praiseSaveMsg"
          class="settings-sheet__message"
          :class="praiseSaveSuccess ? 'settings-sheet__message--success' : 'settings-sheet__message--error'"
        >
          {{ praiseSaveMsg }}
        </p>
      </div>
    </section>

    <section class="settings-sheet__section">
      <div class="settings-sheet__head">
        <p class="settings-sheet__eyebrow">Daily Quote</p>
        <h3>每日一句</h3>
      </div>

      <div class="settings-sheet__stack">
        <div class="settings-sheet__field">
          <label class="settings-sheet__label">文案分类</label>
          <select v-model="quoteCategory" class="settings-sheet__select">
            <option v-for="cat in HITOKOTO_CATEGORIES" :key="cat.code" :value="cat.code">
              {{ cat.label }}
            </option>
          </select>
          <small class="settings-sheet__hint">选择你喜欢的文案类型，每天会显示该分类的一句话。</small>
        </div>
      </div>

      <div class="settings-sheet__actions">
        <KuButton variant="primary" @click="saveQuoteCategory">
          保存分类
        </KuButton>
      </div>
    </section>

    <section class="settings-sheet__section settings-sheet__section--danger">
      <div class="settings-sheet__head">
        <p class="settings-sheet__eyebrow">Danger Zone</p>
        <h3>清除本地数据</h3>
      </div>

      <p class="settings-sheet__copy">
        删除当前应用在本地保存的设置和历史记录。这个操作无法撤销，请确认后再继续。
      </p>

      <KuButton variant="danger" @click="confirmDelete">删除全部数据</KuButton>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import KuButton from '@/components/base/KuButton.vue'
import KuInput from '@/components/base/KuInput.vue'
import { deleteAllData, getActivityWatchStatus, getSettings, updateSettings } from '@/api'
import { praiseApi } from '@/api/praise'
import { HITOKOTO_CATEGORIES, getSavedCategory, saveCategory } from '@/hooks/useHitokoto'
import type { ActivityWatchStatus, PraiseConfig, SettingsPayload, SettingsResponse } from '@/types/api'
import { handleApiError } from '@/utils/error'
import { normalizeSettings } from '@/utils/validation'

const settings = ref<SettingsResponse>({
  aw_server_url: 'http://127.0.0.1:5600',
  data_masking: false,
  doubao_api_key_set: false,
  openweather_location: 'Shanghai,CN',
  fish_audio_api_key_set: false,
  fish_audio_model: 's2-pro',
})

const apiKeyInput = ref('')
const fishAudioApiKeyInput = ref('')
const apiKeySet = ref(false)
const saving = ref(false)
const saveMessage = ref('')
const saveSuccess = ref(false)
const awStatus = ref<ActivityWatchStatus | null>(null)
const awStatusLoading = ref(false)

const praise = ref<PraiseConfig>({
  praise_auto_enable: true,
  tts_enable: false,
  tts_voice: 'default',
  tts_speed: 1.0,
  do_not_disturb_start: '22:00',
  do_not_disturb_end: '08:00',
  max_praises_per_day: 10,
  global_cooldown_minutes: 30,
})
const praiseLoading = ref(false)
const praiseSaveMsg = ref('')
const praiseSaveSuccess = ref(false)

const quoteCategory = ref(getSavedCategory())

onMounted(async () => {
  await Promise.all([loadSettings(), loadPraiseConfig()])
})

async function loadSettings() {
  try {
    settings.value = normalizeSettings((await getSettings()).data)
    apiKeySet.value = settings.value.doubao_api_key_set
    await refreshActivityWatchStatus()
  } catch (error: unknown) {
    saveSuccess.value = false
    saveMessage.value = handleApiError(error)
  }
}

async function loadPraiseConfig() {
  try {
    const praiseRes = await praiseApi.getConfig()
    if (praiseRes.data.status === 'success') {
      praise.value = praiseRes.data.data
    }
  } catch (error: unknown) {
    void error
  }
}

async function refreshActivityWatchStatus() {
  awStatusLoading.value = true
  try {
    const response = await getActivityWatchStatus()
    awStatus.value = response.data.data
  } catch (error: unknown) {
    awStatus.value = {
      aw_server_url: settings.value.aw_server_url,
      connected: false,
      bucket_count: 0,
      message: handleApiError(error),
    }
  } finally {
    awStatusLoading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  saveMessage.value = ''

  try {
    const payload: SettingsPayload = {
      aw_server_url: settings.value.aw_server_url,
      data_masking: settings.value.data_masking,
      openweather_location: settings.value.openweather_location,
      fish_audio_model: settings.value.fish_audio_model,
    }

    const trimmedApiKey = apiKeyInput.value.trim()
    const trimmedFishKey = fishAudioApiKeyInput.value.trim()

    if (trimmedApiKey) {
      payload.doubao_api_key = trimmedApiKey
    }
    if (trimmedFishKey) {
      payload.fish_audio_api_key = trimmedFishKey
    }

    const response = await updateSettings(payload)
    settings.value = normalizeSettings(response.data.data)
    apiKeySet.value = settings.value.doubao_api_key_set
    apiKeyInput.value = ''
    fishAudioApiKeyInput.value = ''
    saveSuccess.value = true
    saveMessage.value = '设置已保存'
    await refreshActivityWatchStatus()
  } catch (error: unknown) {
    saveSuccess.value = false
    saveMessage.value = handleApiError(error)
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  if (!window.confirm('确定要删除全部本地数据吗？此操作无法撤销。')) {
    return
  }

  try {
    await deleteAllData()
    saveSuccess.value = true
    saveMessage.value = '本地数据已删除'
  } catch (error: unknown) {
    saveSuccess.value = false
    saveMessage.value = handleApiError(error)
  }
}

async function savePraiseConfig() {
  praiseLoading.value = true
  praiseSaveMsg.value = ''
  try {
    const payload = {
      ...praise.value,
      tts_speed: Number(praise.value.tts_speed),
      max_praises_per_day: Number(praise.value.max_praises_per_day),
      global_cooldown_minutes: Number(praise.value.global_cooldown_minutes),
    }
    const res = await praiseApi.updateConfig(payload)
    if (res.data.status === 'success') {
      praise.value = res.data.data
      praiseSaveSuccess.value = true
      praiseSaveMsg.value = '夸夸设置已保存'
    }
  } catch (error: unknown) {
    praiseSaveSuccess.value = false
    praiseSaveMsg.value = handleApiError(error)
  } finally {
    praiseLoading.value = false
  }
}

function saveQuoteCategory() {
  saveCategory(quoteCategory.value)
}
</script>

<style scoped>
.settings-sheet {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.settings-sheet__section {
  padding: var(--space-5);
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(126, 104, 84, 0.12);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xs);
  backdrop-filter: blur(10px);
}

.settings-sheet__section--danger {
  border-color: rgba(192, 96, 80, 0.18);
}

.settings-sheet__head {
  margin-bottom: var(--space-4);
}

.settings-sheet__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.settings-sheet__head h3 {
  font-size: var(--font-size-2xl);
}

.settings-sheet__copy {
  margin-bottom: var(--space-4);
  color: var(--color-text-secondary);
}

.settings-sheet__stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.settings-sheet__field,
.settings-sheet__toggle {
  padding: var(--space-4);
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.settings-sheet__field--status {
  display: flex;
  align-items: center;
}

.settings-sheet__status-row {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.settings-sheet__status-label,
.settings-sheet__toggle p {
  font-weight: var(--font-weight-medium);
}

.settings-sheet__toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.settings-sheet__toggle small {
  display: block;
  margin-top: var(--space-1);
  color: var(--color-text-secondary);
}

.settings-sheet__switch {
  position: relative;
  width: 52px;
  height: 32px;
  flex-shrink: 0;
}

.settings-sheet__switch input {
  position: absolute;
  inset: 0;
  opacity: 0;
}

.settings-sheet__switch span {
  position: absolute;
  inset: 0;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  transition: all var(--duration-fast) var(--ease-out);
}

.settings-sheet__switch span::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 24px;
  height: 24px;
  background: var(--color-bg-card);
  border-radius: 50%;
  box-shadow: var(--shadow-xs);
  transition: transform var(--duration-fast) var(--ease-out);
}

.settings-sheet__switch input:checked + span {
  background: var(--color-accent-soft);
  border-color: rgba(201, 138, 105, 0.28);
}

.settings-sheet__switch input:checked + span::after {
  transform: translateX(20px);
  background: var(--color-accent);
}

.settings-sheet__status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 72px;
  min-height: 32px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.settings-sheet__status-badge--ok {
  color: var(--color-success);
  background: var(--color-success-soft);
}

.settings-sheet__status-badge--error {
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

.settings-sheet__actions {
  margin-top: var(--space-5);
}

.settings-sheet__message {
  margin-top: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
}

.settings-sheet__message--success {
  color: var(--color-success);
  background: var(--color-success-soft);
}

.settings-sheet__message--error {
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

@media (max-width: 720px) {
  .settings-sheet__toggle,
  .settings-sheet__status-row {
    flex-direction: column;
    align-items: flex-start;
  }
}

.settings-sheet__label {
  display: block;
  margin-bottom: var(--space-2);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
}

.settings-sheet__select {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236c6c80' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--space-4) center;
}

.settings-sheet__select:focus {
  outline: none;
  border-color: var(--color-accent-soft);
  box-shadow: 0 0 0 3px rgba(201, 138, 105, 0.12);
}

.settings-sheet__hint {
  display: block;
  margin-top: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
</style>
