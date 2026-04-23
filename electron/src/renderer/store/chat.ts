import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sendChat } from '@/api'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
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

  async function sendMessage(content: string, userContext?: any) {
    if (!content.trim()) return

    // 添加用户消息
    messages.value.push({
      role: 'user',
      content,
      timestamp: new Date(),
    })

    loading.value = true
    error.value = null

    try {
      const response = await sendChat({
        chat_id: chatId.value,
        message: content,
        user_context: userContext,
      })

      // 添加AI回复
      messages.value.push({
        role: 'assistant',
        content: response.data.reply,
        timestamp: new Date(),
      })
    } catch (e: any) {
      error.value = e.message || '发送失败'
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