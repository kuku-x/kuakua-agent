import { computed } from 'vue'
import { useChatStore } from '@/store/chat'

export function useChat() {
  const store = useChatStore()

  const canSend = computed(() => !store.loading)

  const lastMessage = computed(() => {
    if (store.messages.length === 0) return null
    return store.messages[store.messages.length - 1]
  })

  return {
    messages: store.messages,
    groupedMessages: store.groupedMessages,
    chatId: store.chatId,
    loading: store.loading,
    error: store.error,
    canSend,
    lastMessage,
    sendMessage: store.sendMessage,
    resetChat: store.resetChat,
  }
}