<template>
  <div class="settings">
    <h1>设置</h1>

    <div class="settings-form">
      <div class="form-item">
        <label>豆包API密钥</label>
        <input
          type="password"
          v-model="settings.doubao_api_key"
          placeholder="请输入API密钥"
        />
        <span class="hint">用于调用AI生成夸夸和聊天</span>
      </div>

      <div class="form-item">
        <label>ActivityWatch地址</label>
        <input
          type="text"
          v-model="settings.aw_server_url"
          placeholder="http://127.0.0.1:5600"
        />
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
      <button class="danger-btn" @click="confirmDelete">
        删除所有数据
      </button>
      <span class="hint">删除后无法恢复</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSettings, updateSettings, deleteAllData } from '@/api'

const settings = ref({
  doubao_api_key: '',
  aw_server_url: 'http://127.0.0.1:5600',
  data_masking: false,
})

const saving = ref(false)
const saveMessage = ref('')
const saveSuccess = ref(false)

onMounted(async () => {
  try {
    const response = await getSettings()
    const data = response.data
    settings.value.aw_server_url = data.aw_server_url
    settings.value.data_masking = data.data_masking
    if (data.doubao_api_key_set) {
      settings.value.doubao_api_key = '********'
    }
  } catch (e) {
    console.error('获取设置失败', e)
  }
})

async function saveSettings() {
  saving.value = true
  saveMessage.value = ''

  try {
    const payload: Record<string, any> = {
      aw_server_url: settings.value.aw_server_url,
      data_masking: settings.value.data_masking,
    }

    if (settings.value.doubao_api_key && settings.value.doubao_api_key !== '********') {
      payload.doubao_api_key = settings.value.doubao_api_key
    }

    await updateSettings(payload)
    saveSuccess.value = true
    saveMessage.value = '设置保存成功'

    if (settings.value.doubao_api_key === '********') {
      settings.value.doubao_api_key = ''
    }
  } catch (e: any) {
    saveSuccess.value = false
    saveMessage.value = e.response?.data?.detail || '保存失败'
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
    alert('所有数据已删除')
  } catch (e) {
    alert('删除失败')
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
  border-radius: 12px;
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
  color: #999;
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
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.save-message.error {
  background: #fff2f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}

.danger-zone {
  margin-top: 48px;
  padding: 24px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #ffccc7;
}

.danger-zone h3 {
  color: #ff4d4f;
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