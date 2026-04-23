<template>
  <div class="chat-companion">
    <h1>聊天陪伴</h1>

    <div class="chat-container">
      <div class="messages" ref="messagesRef">
        <div v-if="store.messages.length === 0" class="empty-messages">
          <p>有什么想聊的吗？我在这里陪你～</p>
        </div>

        <div
          v-for="(msg, index) in store.messages"
          :key="index"
          class="message"
          :class="msg.role"
        >
          <div class="bubble">{{ msg.content }}</div>
        </div>
      </div>

      <div class="input-area">
        <textarea
          v-model="inputMessage"
          placeholder="说点什么吧..."
          @keydown.enter.exact.prevent="sendMessage"
          rows="2"
        ></textarea>
        <button @click="sendMessage" :disabled="store.loading">
          {{ store.loading ? '发送中...' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useChatStore } from '@/store/chat'
import { useSummaryStore } from '@/store/summary'

const store = useChatStore()
const summaryStore = useSummaryStore()
const inputMessage = ref('')
const messagesRef = ref<HTMLElement | null>(null)

async function sendMessage() {
  const msg = inputMessage.value.trim()
  if (!msg) return

  inputMessage.value = ''

  const context = summaryStore.summary ? {
    total_hours: summaryStore.summary.total_hours,
    work_hours: summaryStore.summary.work_hours,
    entertainment_hours: summaryStore.summary.entertainment_hours,
  } : undefined

  await store.sendMessage(msg, context)

  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-companion {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
}

h1 {
  text-align: center;
  margin-bottom: 24px;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.empty-messages {
  text-align: center;
  color: #999;
  padding: 40px;
}

.message {
  display: flex;
  margin-bottom: 16px;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
}

.message.user .bubble {
  background: #1890ff;
  color: #fff;
}

.message.assistant .bubble {
  background: #f5f5f5;
  color: #333;
}

.input-area {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}

textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  resize: none;
  font-size: 14px;
}

textarea:focus {
  outline: none;
  border-color: #1890ff;
}

button {
  padding: 8px 24px;
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
</style>