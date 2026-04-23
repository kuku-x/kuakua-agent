import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sendChat } from '@/api'
import type { ChatContext } from '@/types/api'
import { handleApiError } from '@/utils/error'
import { normalizeChatResponse } from '@/utils/validation'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  status: 'sending' | 'sent' | 'failed'
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const chatId = ref(`chat_${Date.now()}`)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const groupedMessages = computed(() => {
    const groups: { date: string; messages: ChatMessage[] }[] = []
    let currentDate = ''

    for (const msg of messages.value) {
      const msgDate = msg.timestamp.toDateString()
      if (msgDate !== currentDate) {
        currentDate = msgDate
        groups.push({ date: msgDate, messages: [] })
      }
      groups[groups.length - 1].messages.push(msg)
    }

    return groups
  })

  async function sendMessage(content: string, userContext?: ChatContext) {
    const trimmed = content.trim()
    if (loading.value || !trimmed) return

    const messageId = `msg_${Date.now()}_${Math.random().toString(36).slice(2)}`
    const messageIndex = messages.value.length
    messages.value.push({
      id: messageId,
      role: 'user',
      content: trimmed,
      timestamp: new Date(),
      status: 'sending',
    })

    loading.value = true
    error.value = null

    try {
      const response = await sendChat({
        chat_id: chatId.value,
        message: trimmed,
        user_context: userContext,
      })

      if (response.data.status === 'success' && response.data.data) {
        const data = normalizeChatResponse(response.data.data)
        messages.value[messageIndex].status = 'sent'
        messages.value.push({
          id: `msg_${Date.now()}_${Math.random().toString(36).slice(2)}`,
          role: 'assistant',
          content: data.reply,
          timestamp: new Date(),
          status: 'sent',
        })
      } else {
        error.value = response.data.message || '获取回复失败'
        messages.value[messageIndex].status = 'failed'
      }
    } catch (e: unknown) {
      error.value = handleApiError(e)
      messages.value[messageIndex].status = 'failed'
    } finally {
      loading.value = false
    }
  }

  function resetChat() {
    messages.value = []
    chatId.value = `chat_${Date.now()}`
  }

  return { messages, chatId, loading, error, groupedMessages, sendMessage, resetChat }
})

