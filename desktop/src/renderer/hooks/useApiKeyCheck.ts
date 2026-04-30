import { ref } from 'vue'
import { getSettings } from '@/api'

export function useApiKeyCheck() {
  const hasApiKey = ref(true)
  const checking = ref(false)

  async function checkApiKey() {
    checking.value = true
    try {
      const res = await getSettings()
      hasApiKey.value = res.data.data?.doubao_api_key_set ?? false
    } catch {
      hasApiKey.value = false
    } finally {
      checking.value = false
    }
  }

  return { hasApiKey, checking, checkApiKey }
}