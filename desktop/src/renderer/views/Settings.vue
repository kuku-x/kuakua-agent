<template>
  <section class="settings-page">
    <KuCard padding="lg" class="settings-page__hero">
      <div>
        <p class="settings-page__eyebrow">Preferences</p>
        <h2>让夸夸 Agent 更贴近你的本地使用方式</h2>
        <p>
          设置页继续使用原有配置接口和数据结构，只对表单布局、分区层级和视觉样式做整理。
        </p>
      </div>
    </KuCard>

    <div class="settings-page__grid">
      <KuCard padding="lg">
        <div class="settings-page__panel-head">
          <div>
            <p class="settings-page__eyebrow">Source & Model</p>
            <h3>模型与数据来源</h3>
          </div>
        </div>

        <div class="settings-page__form">
          <div class="settings-page__field">
            <KuInput
              v-model="apiKeyInput"
              type="password"
              label="豆包 API Key"
              placeholder="请输入新的 API Key"
              :hint="
                apiKeySet
                  ? '当前已经配置密钥，留空则保持现有设置。'
                  : '用于聊天与每日摘要生成。'
              "
            />
          </div>

          <div class="settings-page__field">
            <KuInput
              v-model="settings.aw_server_url"
              label="ActivityWatch 地址"
              placeholder="http://127.0.0.1:5600"
              hint="填写你本地 ActivityWatch 服务的访问地址。"
            />
          </div>

          <div class="settings-page__toggle">
            <div>
              <p>数据脱敏</p>
              <small>在摘要结果中隐藏更细的应用名称，降低隐私暴露风险。</small>
            </div>
            <label class="settings-page__switch">
              <input v-model="settings.data_masking" type="checkbox" />
              <span></span>
            </label>
          </div>
        </div>

        <div class="settings-page__actions">
          <KuButton variant="primary" :loading="saving" @click="saveSettings">
            {{ saving ? '保存中...' : '保存设置' }}
          </KuButton>

          <p
            v-if="saveMessage"
            class="settings-page__message"
            :class="saveSuccess ? 'settings-page__message--success' : 'settings-page__message--error'"
          >
            {{ saveMessage }}
          </p>
        </div>
      </KuCard>

      <div class="settings-page__side">
        <KuCard padding="lg">
          <p class="settings-page__eyebrow">Notes</p>
          <h3>这里不会改动你的业务逻辑</h3>
          <p class="settings-page__copy">
            所有设置项仍然直接对接现有接口，只是界面结构更清晰，方便后续扩展。
          </p>
        </KuCard>

        <KuCard padding="lg" class="settings-page__danger">
          <p class="settings-page__eyebrow">Danger Zone</p>
          <h3>清除本地数据</h3>
          <p class="settings-page__copy">
            删除当前应用在本地保存的设置和历史记录。这个操作无法撤销，请确认后再继续。
          </p>
          <KuButton variant="danger" @click="confirmDelete">删除全部数据</KuButton>
        </KuCard>

        <KuCard padding="lg">
          <div class="settings-page__panel-head">
            <div>
              <p class="settings-page__eyebrow">Praise</p>
              <h3>夸夸 Agent</h3>
            </div>
          </div>

          <div class="settings-page__form">
            <div class="settings-page__toggle">
              <div>
                <p>主动夸夸</p>
                <small>开启后，夸夸 Agent 将根据时间与行为组合规则自动发起夸夸</small>
              </div>
              <label class="settings-page__switch">
                <input v-model="praise.praise_auto_enable" type="checkbox" />
                <span></span>
              </label>
            </div>

            <div class="settings-page__toggle">
              <div>
                <p>语音播报</p>
                <small>开启后，夸夸内容将使用 TTS 语音念出来</small>
              </div>
              <label class="settings-page__switch">
                <input v-model="praise.tts_enable" type="checkbox" />
                <span></span>
              </label>
            </div>

            <div class="settings-page__field">
              <KuInput
                v-model="praise.do_not_disturb_start"
                label="免打扰开始时间"
                placeholder="22:00"
              />
            </div>

            <div class="settings-page__field">
              <KuInput
                v-model="praise.do_not_disturb_end"
                label="免打扰结束时间"
                placeholder="08:00"
              />
            </div>

            <div class="settings-page__field">
              <KuInput
                v-model.number="praise.max_praises_per_day"
                type="number"
                label="每日夸夸上限"
              />
            </div>

            <div class="settings-page__field">
              <KuInput
                v-model.number="praise.global_cooldown_minutes"
                type="number"
                label="全局冷却时间（分钟）"
              />
            </div>
          </div>

          <div class="settings-page__actions">
            <KuButton variant="primary" :loading="praiseLoading" @click="savePraiseConfig">
              {{ praiseLoading ? '保存中...' : '保存夸夸设置' }}
            </KuButton>
            <p
              v-if="praiseSaveMsg"
              class="settings-page__message"
              :class="praiseSaveSuccess ? 'settings-page__message--success' : 'settings-page__message--error'"
            >
              {{ praiseSaveMsg }}
            </p>
          </div>
        </KuCard>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import KuButton from '@/components/base/KuButton.vue'
import KuCard from '@/components/base/KuCard.vue'
import KuInput from '@/components/base/KuInput.vue'
import { deleteAllData, getSettings, updateSettings } from '@/api'
import { praiseApi } from '@/api/praise'
import type { SettingsPayload, SettingsResponse, PraiseConfig } from '@/types/api'
import { handleApiError } from '@/utils/error'
import { normalizeSettings } from '@/utils/validation'

const settings = ref<SettingsResponse>({
  aw_server_url: 'http://127.0.0.1:5600',
  data_masking: false,
  doubao_api_key_set: false,
})

const apiKeyInput = ref('')
const apiKeySet = ref(false)
const saving = ref(false)
const saveMessage = ref('')
const saveSuccess = ref(false)

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

onMounted(async () => {
  try {
    settings.value = normalizeSettings((await getSettings()).data)
    apiKeySet.value = settings.value.doubao_api_key_set
  } catch (error: unknown) {
    saveSuccess.value = false
    saveMessage.value = handleApiError(error)
  }
  try {
    const praiseRes = await praiseApi.getConfig()
    if (praiseRes.data.status === 'success') {
      praise.value = praiseRes.data.data
    }
  } catch (error: unknown) {
  // silently ignore - praise settings are optional
  void error
}
})

async function saveSettings() {
  saving.value = true
  saveMessage.value = ''

  try {
    const payload: SettingsPayload = {
      aw_server_url: settings.value.aw_server_url,
      data_masking: settings.value.data_masking,
    }

    const trimmedApiKey = apiKeyInput.value.trim()
    if (trimmedApiKey) {
      payload.doubao_api_key = trimmedApiKey
    }

    const response = await updateSettings(payload)
    settings.value = normalizeSettings(response.data.data)
    apiKeySet.value = settings.value.doubao_api_key_set
    apiKeyInput.value = ''
    saveSuccess.value = true
    saveMessage.value = '设置已保存'
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
    const res = await praiseApi.updateConfig(praise.value)
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
</script>

<style scoped>
.settings-page {
  display: flex;
  max-width: var(--content-max-width);
  margin: 0 auto;
  flex-direction: column;
  gap: var(--space-5);
}

.settings-page__hero {
  background:
    radial-gradient(circle at top left, rgba(201, 138, 105, 0.16), transparent 28%),
    var(--color-bg-card);
}

.settings-page__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.settings-page__hero h2 {
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.15;
  letter-spacing: -0.04em;
}

.settings-page__hero p:last-child,
.settings-page__copy {
  margin-top: var(--space-3);
  color: var(--color-text-secondary);
}

.settings-page__grid {
  display: grid;
  grid-template-columns: 1.08fr 0.92fr;
  gap: var(--space-5);
  align-items: start;
}

.settings-page__panel-head {
  margin-bottom: var(--space-5);
}

.settings-page__panel-head h3,
.settings-page__side h3 {
  font-size: var(--font-size-2xl);
}

.settings-page__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.settings-page__field,
.settings-page__toggle {
  padding: var(--space-4);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.settings-page__toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.settings-page__toggle p {
  font-weight: var(--font-weight-medium);
}

.settings-page__toggle small {
  display: block;
  margin-top: var(--space-1);
  color: var(--color-text-secondary);
}

.settings-page__switch {
  position: relative;
  width: 52px;
  height: 32px;
  flex-shrink: 0;
}

.settings-page__switch input {
  position: absolute;
  inset: 0;
  opacity: 0;
}

.settings-page__switch span {
  position: absolute;
  inset: 0;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  transition: all var(--duration-fast) var(--ease-out);
}

.settings-page__switch span::after {
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

.settings-page__switch input:checked + span {
  background: var(--color-accent-soft);
  border-color: rgba(201, 138, 105, 0.28);
}

.settings-page__switch input:checked + span::after {
  transform: translateX(20px);
  background: var(--color-accent);
}

.settings-page__actions {
  margin-top: var(--space-5);
}

.settings-page__message {
  margin-top: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
}

.settings-page__message--success {
  color: var(--color-success);
  background: var(--color-success-soft);
}

.settings-page__message--error {
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

.settings-page__side {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.settings-page__danger {
  border-color: rgba(192, 96, 80, 0.18);
}

@media (max-width: 960px) {
  .settings-page__grid {
    grid-template-columns: 1fr;
  }

  .settings-page__toggle {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
