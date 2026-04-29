<template>
  <div class="settings-sheet">
    <!-- 侧边栏 -->
    <nav class="settings-nav">
      <button
        v-for="item in navItems"
        :key="item.id"
        class="settings-nav__item"
        :class="{ 'settings-nav__item--active': activeTab === item.id }"
        type="button"
        @click="activeTab = item.id"
      >
        <span class="settings-nav__icon" v-html="item.icon"></span>
        <span class="settings-nav__label">{{ item.label }}</span>
      </button>
    </nav>

    <!-- 内容区 -->
    <div class="settings-content">

      <!-- ==================== 偏好设置 ==================== -->
      <section v-show="activeTab === 'preference'" class="settings-card">
        <div class="settings-card__head">
          <h3>基本设置</h3>
        </div>

        <div class="settings-card__body">
          <!-- API Key -->
          <div class="settings-card__group">
            <label class="settings-card__label">模型 API Key</label>
            <div class="settings-card__input-row">
              <div class="settings-card__input-wrap settings-card__input-wrap--icon-left">
                <span class="settings-card__input-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="16" height="16">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  </svg>
                </span>
                <input
                  v-model="apiKeyInput"
                  :type="showApiKey ? 'text' : 'password'"
                  class="settings-card__input"
                  placeholder="请输入新的 API Key，留空则保持不变"
                />
                <button class="settings-card__input-action" type="button" @click="showApiKey = !showApiKey">
                  <svg v-if="!showApiKey" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="16" height="16">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="16" height="16">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                </button>
              </div>
              <KuButton size="sm" :loading="saving" @click="saveSettings">保存</KuButton>
              <KuButton v-if="apiKeySet" size="sm" variant="ghost" type="button" @click="clearApiKey">清空</KuButton>
            </div>
            <p class="settings-card__hint">
              <span v-if="apiKeySet" class="settings-card__hint--ok">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polyline points="20 6 9 17 4 12"/></svg>
                已配置密钥
              </span>
              <span v-else>用于聊天与晚间总结生成</span>
            </p>
          </div>

          <!-- ActivityWatch -->
          <div class="settings-card__group">
            <label class="settings-card__label">ActivityWatch 地址</label>
            <div class="settings-card__input-row">
              <div class="settings-card__input-wrap settings-card__input-wrap--icon-left">
                <span class="settings-card__input-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="16" height="16">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                    <line x1="8" y1="21" x2="16" y2="21"/>
                    <line x1="12" y1="17" x2="12" y2="21"/>
                  </svg>
                </span>
                <input
                  v-model="settings.aw_server_url"
                  type="text"
                  class="settings-card__input"
                  placeholder="http://127.0.0.1:5600"
                />
              </div>
              <span
                class="settings-card__status-badge"
                :class="awStatus?.connected ? 'settings-card__status-badge--ok' : 'settings-card__status-badge--error'"
              >
                <svg v-if="awStatus?.connected" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="12" height="12"><polyline points="20 6 9 17 4 12"/></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="12" height="12"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                {{ awStatusLoading ? '检测中' : awStatus?.connected ? '已连接' : '未连接' }}
              </span>
            </div>
            <p class="settings-card__hint">填写本地 ActivityWatch 服务地址</p>
          </div>

          <!-- 数据脱敏 -->
          <div class="settings-card__group settings-card__group--row">
            <div class="settings-card__toggle-desc">
              <label class="settings-card__label">数据脱敏</label>
              <p class="settings-card__desc">在摘要结果中隐藏更细的应用名称，降低隐私暴露风险。</p>
            </div>
            <label class="settings-card__switch">
              <input v-model="settings.data_masking" type="checkbox" />
              <span></span>
            </label>
          </div>
        </div>

        <div class="settings-card__footer">
          <KuButton variant="primary" size="md" :loading="saving" @click="saveSettings">
            {{ saving ? '保存中...' : '保存设置' }}
          </KuButton>
          <p v-if="saveMessage" class="settings-card__message" :class="saveSuccess ? 'settings-card__message--ok' : 'settings-card__message--error'">
            {{ saveMessage }}
          </p>
        </div>
      </section>

      <!-- ==================== 夸夸设置 ==================== -->
      <section v-show="activeTab === 'praise'" class="settings-card">
        <div class="settings-card__head">
          <h3>夸夸设置</h3>
        </div>

        <div class="settings-card__body">
          <!-- 功能开关 -->
          <div class="settings-card__section-label">功能开关</div>

          <div class="settings-card__toggle-item">
            <div class="settings-card__toggle-desc">
              <label class="settings-card__label">主动夸夸</label>
              <p class="settings-card__desc">开启后，Agent 会根据时间与行为规则自动发起夸夸。</p>
            </div>
            <label class="settings-card__switch">
              <input v-model="praise.praise_auto_enable" type="checkbox" />
              <span></span>
            </label>
          </div>

          <div class="settings-card__toggle-item">
            <div class="settings-card__toggle-desc">
              <label class="settings-card__label">语音播报</label>
              <p class="settings-card__desc">开启后，夸夸内容会通过 Kokoro-82M 生成本地语音并播放。</p>
            </div>
            <label class="settings-card__switch">
              <input v-model="praise.tts_enable" type="checkbox" />
              <span></span>
            </label>
          </div>

          <div class="settings-card__toggle-item">
            <div class="settings-card__toggle-desc">
              <label class="settings-card__label">晚间总结提醒</label>
              <p class="settings-card__desc">每天到设定时间后生成当天总结，并在桌面端展示提醒与完整内容。</p>
            </div>
            <label class="settings-card__switch">
              <input v-model="praise.nightly_summary_enable" type="checkbox" />
              <span></span>
            </label>
          </div>

          <!-- TTS 配置 -->
          <div class="settings-card__section-label">Kokoro TTS</div>

          <div class="settings-card__group">
            <label class="settings-card__label">模型路径</label>
            <div class="settings-card__input-row">
              <div class="settings-card__input-wrap">
                <input
                  v-model="praise.kokoro_model_path"
                  type="text"
                  class="settings-card__input"
                  placeholder="./ckpts/kokoro-v1.1"
                />
              </div>
              <KuButton size="sm" variant="secondary" @click="selectModelPath">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="14" height="14">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
                选择文件夹
              </KuButton>
            </div>
            <p class="settings-card__hint">可填写本地模型目录，或保留默认路径。</p>
          </div>

          <div class="settings-card__group">
            <label class="settings-card__label">音色 ID</label>
            <div class="settings-card__select-wrap">
              <select v-model="praise.kokoro_voice" class="settings-card__select">
                <optgroup label="女声">
                  <option v-for="v in femaleVoices" :key="v" :value="v">{{ v }}</option>
                </optgroup>
                <optgroup label="男声">
                  <option v-for="v in maleVoices" :key="v" :value="v">{{ v }}</option>
                </optgroup>
              </select>
            </div>
            <p class="settings-card__hint">选择音色后可在预览区试听效果。</p>
          </div>

          <div class="settings-card__group">
            <div class="settings-card__slider-header">
              <label class="settings-card__label">语速</label>
              <span class="settings-card__slider-value">{{ praise.tts_speed.toFixed(1) }}x</span>
            </div>
            <div class="settings-card__slider-wrap">
              <span class="settings-card__slider-label">0.5</span>
              <input
                v-model.number="praise.tts_speed"
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                class="settings-card__slider"
              />
              <span class="settings-card__slider-label">2.0</span>
            </div>
          </div>

          <!-- 时间设置 -->
          <div class="settings-card__section-label">时间设置</div>

          <div class="settings-card__group">
            <label class="settings-card__label">免打扰时段</label>
            <div class="settings-card__time-row">
              <div class="settings-card__time-wrap">
                <input
                  v-model="praise.do_not_disturb_start"
                  type="time"
                  class="settings-card__time-input"
                />
                <span class="settings-card__time-sep">至</span>
                <input
                  v-model="praise.do_not_disturb_end"
                  type="time"
                  class="settings-card__time-input"
                />
              </div>
            </div>
            <p class="settings-card__hint">此时段内不会主动发起夸夸。</p>
          </div>

          <div class="settings-card__group">
            <label class="settings-card__label">晚间总结时间</label>
            <div class="settings-card__input-row">
              <div class="settings-card__input-wrap settings-card__input-wrap--icon-left">
                <span class="settings-card__input-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="16" height="16">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12 6 12 12 16 14"/>
                  </svg>
                </span>
                <input
                  v-model="praise.nightly_summary_time"
                  type="time"
                  class="settings-card__input"
                />
              </div>
            </div>
            <p class="settings-card__hint">使用 24 小时制。</p>
          </div>
        </div>

        <div class="settings-card__footer">
          <KuButton variant="primary" size="md" :loading="praiseLoading" @click="savePraiseConfig">
            {{ praiseLoading ? '保存中...' : '保存夸夸设置' }}
          </KuButton>
          <p v-if="praiseSaveMsg" class="settings-card__message" :class="praiseSaveSuccess ? 'settings-card__message--ok' : 'settings-card__message--error'">
            {{ praiseSaveMsg }}
          </p>
        </div>
      </section>

      <!-- ==================== 每日一句 ==================== -->
      <section v-show="activeTab === 'quote'" class="settings-card">
        <div class="settings-card__head">
          <h3>每日一句</h3>
        </div>

        <div class="settings-card__body">
          <div class="settings-card__group">
            <label class="settings-card__label">文案分类</label>
            <div class="settings-card__select-wrap">
              <select v-model="quoteCategory" class="settings-card__select">
                <option v-for="cat in HITOKOTO_CATEGORIES" :key="cat.code" :value="cat.code">
                  {{ cat.label }}
                </option>
              </select>
            </div>
            <p class="settings-card__hint">选择你喜欢的文案类型，每天会显示该分类的一句话。</p>
          </div>

          <!-- 预览 -->
          <div class="settings-card__preview">
            <p class="settings-card__preview-label">效果预览</p>
            <blockquote class="settings-card__preview-quote">
              {{ previewQuote }}
            </blockquote>
          </div>
        </div>

        <div class="settings-card__footer">
          <KuButton variant="primary" size="md" @click="saveQuoteCategory">保存分类</KuButton>
        </div>
      </section>

      <!-- ==================== 数据管理 ==================== -->
      <section v-show="activeTab === 'data'" class="settings-card settings-card--danger">
        <div class="settings-card__head">
          <h3>清除本地数据</h3>
        </div>

        <div class="settings-card__body">
          <p class="settings-card__danger-desc">
            删除当前应用在本地保存的设置和历史记录。这个操作无法撤销，请确认后再继续。
          </p>
        </div>

        <div class="settings-card__footer">
          <KuButton variant="danger" size="md" @click="confirmDelete">删除全部数据</KuButton>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KuButton from '@/components/base/KuButton.vue'
import { deleteAllData, getActivityWatchStatus, getSettings, updateSettings } from '@/api'
import { praiseApi } from '@/api/praise'
import { HITOKOTO_CATEGORIES, getSavedCategory, saveCategory } from '@/hooks/useHitokoto'
import type { ActivityWatchStatus, PraiseConfig, SettingsPayload, SettingsResponse } from '@/types/api'
import { handleApiError } from '@/utils/error'
import { normalizeSettings } from '@/utils/validation'

// ==================== 侧边栏导航 ====================
const activeTab = ref<'preference' | 'praise' | 'quote' | 'data'>('preference')

const navItems = [
  {
    id: 'preference' as const,
    label: '基本设置',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="18" height="18"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
  },
  {
    id: 'praise' as const,
    label: '夸夸设置',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="18" height="18"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`,
  },
  {
    id: 'quote' as const,
    label: '每日一句',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="18" height="18"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"/><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"/></svg>`,
  },
  {
    id: 'data' as const,
    label: '数据管理',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="18" height="18"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>`,
  },
]

// ==================== 音色列表 ====================
const femaleVoices = [
  'zf_001', 'zf_002', 'zf_003', 'zf_004', 'zf_005',
  'zf_006', 'zf_007', 'zf_008', 'zf_009', 'zf_010',
  'zf_011', 'zf_012', 'zf_013', 'zf_014', 'zf_015',
  'zf_016', 'zf_017', 'zf_018', 'zf_019', 'zf_020',
  'zf_021', 'zf_022', 'zf_023', 'zf_024', 'zf_025',
  'zf_026', 'zf_027', 'zf_028', 'zf_029', 'zf_030',
  'zf_031', 'zf_032',
]
const maleVoices = [
  'zm_001', 'zm_002', 'zm_003', 'zm_004', 'zm_005',
  'zm_006', 'zm_007', 'zm_008', 'zm_009', 'zm_010',
]

// ==================== 状态 ====================
const settings = ref<SettingsResponse>({
  aw_server_url: 'http://127.0.0.1:5600',
  data_masking: false,
  doubao_api_key_set: false,
})

const apiKeyInput = ref('')
const apiKeySet = ref(false)
const showApiKey = ref(false)
const saving = ref(false)
const saveMessage = ref('')
const saveSuccess = ref(false)
const awStatus = ref<ActivityWatchStatus | null>(null)
const awStatusLoading = ref(false)

const praise = ref<PraiseConfig>({
  praise_auto_enable: true,
  tts_enable: false,
  kokoro_voice: 'zf_001',
  kokoro_model_path: './ckpts/kokoro-v1.1',
  tts_speed: 1.0,
  do_not_disturb_start: '22:00',
  do_not_disturb_end: '08:00',
  nightly_summary_enable: true,
  nightly_summary_time: '21:30',
})
const praiseLoading = ref(false)
const praiseSaveMsg = ref('')
const praiseSaveSuccess = ref(false)

const quoteCategory = ref(getSavedCategory())

const previewQuote = computed(() => {
  const cats = HITOKOTO_CATEGORIES.find(c => c.code === quoteCategory.value)
  return cats ? `「${cats.label}」示例文案：今天的你也很棒，继续加油！` : '请选择一个分类查看预览'
})

// ==================== 生命周期 ====================
onMounted(async () => {
  await Promise.all([loadSettings(), loadPraiseConfig()])
})

// ==================== 方法 ====================
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
    praiseSaveSuccess.value = false
    praiseSaveMsg.value = handleApiError(error)
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
    await refreshActivityWatchStatus()
  } catch (error: unknown) {
    saveSuccess.value = false
    saveMessage.value = handleApiError(error)
  } finally {
    saving.value = false
  }
}

function clearApiKey() {
  apiKeyInput.value = ''
}

function selectModelPath() {
  // 浏览器环境下无法打开文件浏览器，提示用户手动输入
  window.alert('请在下方输入框中粘贴 Kokoro 模型文件夹的路径。')
}

async function savePraiseConfig() {
  praiseLoading.value = true
  praiseSaveMsg.value = ''
  try {
    const payload = {
      ...praise.value,
      kokoro_model_path: praise.value.kokoro_model_path.trim(),
      kokoro_voice: praise.value.kokoro_voice.trim(),
      tts_speed: Number(praise.value.tts_speed),
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
</script>

<style scoped>
/* ==================== 整体布局 ==================== */
.settings-sheet {
  display: flex;
  gap: var(--space-4);
  min-height: 100%;
}

/* ==================== 侧边栏导航 ==================== */
.settings-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  width: 148px;
  flex-shrink: 0;
  padding: var(--space-3);
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(126, 104, 84, 0.1);
  border-radius: var(--radius-xl);
}

.settings-nav__item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3) var(--space-3);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  text-align: left;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.settings-nav__item:hover {
  color: var(--color-text-primary);
  background: var(--color-accent-soft);
}

.settings-nav__item--active {
  color: var(--color-accent);
  background: var(--color-accent-soft);
}

.settings-nav__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.settings-nav__label {
  line-height: 1;
}

/* ==================== 内容区 ==================== */
.settings-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ==================== 卡片 ==================== */
.settings-card {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(126, 104, 84, 0.1);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xs);
  backdrop-filter: blur(12px);
  overflow: hidden;
}

.settings-card--danger {
  border-color: rgba(192, 96, 80, 0.18);
}

.settings-card__head {
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid rgba(126, 104, 84, 0.08);
}

.settings-card__head h3 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.settings-card__body {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.settings-card__footer {
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid rgba(126, 104, 84, 0.08);
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

/* ==================== 分组标题 ==================== */
.settings-card__section-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-tertiary);
  padding-bottom: var(--space-1);
  border-bottom: 1px solid rgba(126, 104, 84, 0.08);
}

/* ==================== 表单标签 ==================== */
.settings-card__label {
  display: block;
  margin-bottom: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.settings-card__desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.settings-card__hint {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  margin-top: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.settings-card__hint--ok {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--color-success);
}

/* ==================== 输入框 ==================== */
.settings-card__group {
  display: flex;
  flex-direction: column;
}

.settings-card__input-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.settings-card__input-wrap {
  position: relative;
  flex: 1;
}

.settings-card__input-wrap--icon-left .settings-card__input {
  padding-left: calc(var(--space-4) + 18px);
}

.settings-card__input-icon {
  position: absolute;
  left: var(--space-4);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-tertiary);
  pointer-events: none;
  display: flex;
  align-items: center;
}

.settings-card__input {
  width: 100%;
  min-height: 44px;
  padding: 0 var(--space-4);
  font-size: var(--font-size-sm);
  font-family: inherit;
  color: var(--color-text-primary);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  transition: all var(--duration-fast) var(--ease-out);
}

.settings-card__input:focus {
  border-color: var(--color-accent);
  outline: none;
  box-shadow: 0 0 0 3px var(--color-accent-soft);
}

.settings-card__input::placeholder {
  color: var(--color-text-tertiary);
}

.settings-card__input-action {
  position: absolute;
  right: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  color: var(--color-text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: color var(--duration-fast);
}

.settings-card__input-action:hover {
  color: var(--color-text-primary);
}

/* ==================== 下拉框 ==================== */
.settings-card__select-wrap {
  position: relative;
}

.settings-card__select {
  width: 100%;
  min-height: 44px;
  padding: 0 var(--space-8) 0 var(--space-4);
  font-size: var(--font-size-sm);
  font-family: inherit;
  color: var(--color-text-primary);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%238a7160' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--space-4) center;
  transition: all var(--duration-fast) var(--ease-out);
}

.settings-card__select:focus {
  border-color: var(--color-accent);
  outline: none;
  box-shadow: 0 0 0 3px var(--color-accent-soft);
}

/* ==================== 开关 ==================== */
.settings-card__switch {
  position: relative;
  width: 44px;
  height: 26px;
  flex-shrink: 0;
}

.settings-card__switch input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.settings-card__switch span {
  position: absolute;
  inset: 0;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-full);
  transition: all var(--duration-fast) var(--ease-out);
}

.settings-card__switch span::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: var(--color-bg-card);
  border-radius: 50%;
  box-shadow: var(--shadow-xs);
  transition: transform var(--duration-fast) var(--ease-out);
}

.settings-card__switch input:checked + span {
  background: var(--color-accent-soft);
  border-color: rgba(201, 138, 105, 0.3);
}

.settings-card__switch input:checked + span::after {
  transform: translateX(18px);
  background: var(--color-accent);
}

.settings-card__toggle-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(126, 104, 84, 0.08);
  border-radius: var(--radius-lg);
}

.settings-card__toggle-desc {
  flex: 1;
  min-width: 0;
}

.settings-card__group--row {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(126, 104, 84, 0.08);
  border-radius: var(--radius-lg);
}

/* ==================== 状态标签 ==================== */
.settings-card__status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  min-height: 32px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  white-space: nowrap;
  flex-shrink: 0;
}

.settings-card__status-badge--ok {
  color: var(--color-success);
  background: var(--color-success-soft);
}

.settings-card__status-badge--error {
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

/* ==================== 滑块 ==================== */
.settings-card__slider-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
}

.settings-card__slider-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-accent);
  min-width: 36px;
  text-align: right;
}

.settings-card__slider-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.settings-card__slider-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}

.settings-card__slider {
  flex: 1;
  height: 4px;
  appearance: none;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-full);
  outline: none;
  cursor: pointer;
}

.settings-card__slider::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--color-accent);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: transform var(--duration-fast) var(--ease-out);
}

.settings-card__slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

/* ==================== 时间选择 ==================== */
.settings-card__time-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.settings-card__time-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
}

.settings-card__time-input {
  flex: 1;
  min-height: 44px;
  padding: 0 var(--space-4);
  font-size: var(--font-size-sm);
  font-family: inherit;
  color: var(--color-text-primary);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  transition: all var(--duration-fast) var(--ease-out);
}

.settings-card__time-input:focus {
  border-color: var(--color-accent);
  outline: none;
  box-shadow: 0 0 0 3px var(--color-accent-soft);
}

.settings-card__time-sep {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

/* ==================== 消息提示 ==================== */
.settings-card__message {
  font-size: var(--font-size-sm);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
}

.settings-card__message--ok {
  color: var(--color-success);
  background: var(--color-success-soft);
}

.settings-card__message--error {
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

/* ==================== 每日一句预览 ==================== */
.settings-card__preview {
  padding: var(--space-4);
  background: linear-gradient(135deg, rgba(201, 138, 105, 0.08), rgba(212, 168, 75, 0.06));
  border: 1px solid rgba(201, 138, 105, 0.12);
  border-radius: var(--radius-lg);
}

.settings-card__preview-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-3);
}

.settings-card__preview-quote {
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  line-height: 1.8;
  margin: 0;
  padding-left: var(--space-4);
  border-left: 2px solid var(--color-accent);
  font-style: italic;
}

/* ==================== 危险区 ==================== */
.settings-card__danger-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.7;
}

/* ==================== 响应式 ==================== */
@media (max-width: 520px) {
  .settings-sheet {
    flex-direction: column;
  }

  .settings-nav {
    flex-direction: row;
    width: 100%;
    overflow-x: auto;
    padding: var(--space-2);
  }

  .settings-nav__item {
    flex-direction: column;
    gap: var(--space-1);
    padding: var(--space-2) var(--space-3);
    font-size: var(--font-size-xs);
    white-space: nowrap;
  }

  .settings-nav__label {
    writing-mode: horizontal-tb;
  }
}
</style>
