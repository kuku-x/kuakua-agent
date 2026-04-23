<template>
  <div class="settings">
    <h1>设置</h1>

    <div class="settings-form">
      <div class="form-item">
        <label>豆包API密钥</label>
        <input type="password" v-model="apiKeyInput" placeholder="请输入新的API密钥" />
        <span class="hint">{{ apiKeySet ? '已配置密钥；留空则保持不变' : '用于调用AI生成夸夸和聊天' }}</span>
      </div>

      <div class="form-item">
        <label>ActivityWatch地址</label>
        <input type="text" v-model="settings.aw_server_url" placeholder="http://127.0.0.1:5600" />
        <span class="hint">ActivityWatch服务的地址</span>
      </div>

      <div class="form-item">
        <label>
          <input type="checkbox" v-model="settings.data_masking" />
          启用数据脱敏
        </label>
        <span class="hint">隐藏具体应用名称，保护隐私</span>
      </div>

      <div class="form-actions">
        <button @click="saveSettings" :disabled="saving">
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </div>

      <div v-if="saveMessage" class="save-message" :class="saveSuccess ? 'success' : 'error'">
        {{ saveMessage }}
      </div>
    </div>

    <div class="danger-zone">
      <h3>危险区域</h3>
      <button class="danger-btn" @click="confirmDelete">删除所有数据</button>
      <span class="hint">删除后无法恢复</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSettings, updateSettings, deleteAllData } from '@/api'
import type { SettingsPayload, SettingsResponse } from '@/types/api'
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

onMounted(async () => {
  try {
    settings.value = normalizeSettings((await getSettings()).data)
    apiKeySet.value = settings.value.doubao_api_key_set
  } catch (e: unknown) {
    saveSuccess.value = false
    saveMessage.value = handleApiError(e)
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
    saveMessage.value = '设置保存成功'
  } catch (e: unknown) {
    saveSuccess.value = false
    saveMessage.value = handleApiError(e)
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  if (!confirm('确定要删除所有数据吗？此操作不可恢复。')) {
    return
  }

  try {
    await deleteAllData()
    saveSuccess.value = true
    saveMessage.value = '所有数据已删除'
  } catch (e: unknown) {
    saveSuccess.value = false
    saveMessage.value = handleApiError(e)
  }
}
</script>

<style scoped>
.settings {
  max-width: 600px;
  margin: 0 auto;
}

h1 {
  text-align: center;
  margin-bottom: 32px;
}

.settings-form {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
}

.form-item {
  margin-bottom: 24px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

input[type="text"],
input[type="password"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  font-size: 14px;
}

input:focus {
  outline: none;
  border-color: #1890ff;
}

.hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #666;
}

.form-actions {
  margin-top: 32px;
}

button {
  padding: 10px 32px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

button:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

.save-message {
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
}

.save-message.success {
  background: #f6ffed;
  color: #237804;
  border: 1px solid #b7eb8f;
}

.save-message.error {
  background: #fff2f0;
  color: #a8071a;
  border: 1px solid #ffccc7;
}

.danger-zone {
  margin-top: 48px;
  padding: 24px;
  background: #fff;
  border: 1px solid #ffccc7;
  border-radius: 8px;
}

.danger-zone h3 {
  color: #a8071a;
  margin-bottom: 16px;
}

.danger-btn {
  background: #ff4d4f;
}

.danger-btn:hover {
  background: #ff7875;
}

.danger-zone .hint {
  margin-left: 12px;
}
</style>
