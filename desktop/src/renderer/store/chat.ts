import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { sendChatStream } from '@/api'
import type { ChatContext } from '@/types/api'
import { handleApiError } from '@/utils/error'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  status: 'sending' | 'sent' | 'streaming' | 'failed'
}

export interface ChatSession {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
  messages: ChatMessage[]
}

const DEFAULT_CHAT_TITLE = 'New conversation'

function createSession(): ChatSession {
  const now = new Date()
  return {
    id: `chat_${Date.now()}_${Math.random().toString(36).slice(2)}`,
    title: DEFAULT_CHAT_TITLE,
    createdAt: now,
    updatedAt: now,
    messages: [],
  }
}

function buildSessionTitle(content: string): string {
  const compact = content.replace(/\s+/g, ' ').trim()
  return compact.slice(0, 28) || DEFAULT_CHAT_TITLE
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([createSession()])
  const activeChatId = ref(sessions.value[0].id)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const draft = ref('')

  const activeSession = computed(() => {
    return sessions.value.find((session) => session.id === activeChatId.value) ?? sessions.value[0]
  })

  const messages = computed(() => activeSession.value.messages)
  const chatId = computed(() => activeSession.value.id)

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

  function selectChat(sessionId: string) {
    if (sessions.value.some((session) => session.id === sessionId)) {
      activeChatId.value = sessionId
      error.value = null
    }
  }

  function resetChat() {
    const nextSession = createSession()
    sessions.value.unshift(nextSession)
    activeChatId.value = nextSession.id
    error.value = null
  }

  function removeChat(sessionId: string) {
    if (sessions.value.length === 1) {
      const nextSession = createSession()
      sessions.value = [nextSession]
      activeChatId.value = nextSession.id
      error.value = null
      return
    }

    const nextSessions = sessions.value.filter((session) => session.id !== sessionId)
    sessions.value = nextSessions

    if (!nextSessions.some((session) => session.id === activeChatId.value)) {
      activeChatId.value = nextSessions[0].id
    }
  }

  async function sendMessage(content: string, userContext?: ChatContext) {
    const trimmed = content.trim()
    if (loading.value || !trimmed) return

    const session = activeSession.value
    const messageId = `msg_${Date.now()}_${Math.random().toString(36).slice(2)}`
    session.messages.push({
      id: messageId,
      role: 'user',
      content: trimmed,
      timestamp: new Date(),
      status: 'sent',
    })

    if (session.title === DEFAULT_CHAT_TITLE) {
      session.title = buildSessionTitle(trimmed)
    }
    session.updatedAt = new Date()

    loading.value = true
    error.value = null

    // 创建 assistant 消息占位
    const assistantMessageId = `msg_${Date.now()}_${Math.random().toString(36).slice(2)}`
    const assistantIndex = session.messages.length
    session.messages.push({
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      status: 'streaming',
    })

    try {
      let fullReply = ''
      for await (const chunk of sendChatStream({
        chat_id: session.id,
        message: trimmed,
        user_context: userContext,
      })) {
        fullReply += chunk
        session.messages[assistantIndex].content = fullReply
      }
      session.messages[assistantIndex].status = 'sent'
      session.updatedAt = new Date()
    } catch (e: unknown) {
      error.value = handleApiError(e)
      session.messages[assistantIndex].status = 'failed'
      session.messages[assistantIndex].content = '抱歉，回复失败了。'
    } finally {
      loading.value = false
    }
  }

  function setDraft(content: string) {
    draft.value = content
  }

  return {
    activeChatId,
    activeSession,
    chatId,
    draft,
    error,
    groupedMessages,
    loading,
    messages,
    removeChat,
    resetChat,
    selectChat,
    sendMessage,
    setDraft,
    sessions,
  }
})
