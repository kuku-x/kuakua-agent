import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const globalError = ref<string | null>(null)

  function setGlobalError(message: string) {
    globalError.value = message
  }

  function clearGlobalError() {
    globalError.value = null
  }

  return { globalError, setGlobalError, clearGlobalError }
})

