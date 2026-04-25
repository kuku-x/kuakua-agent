<template>
  <section class="chat-page">
    <div v-if="store.messages.length === 0" class="chat-page__welcome">
      <KuCard padding="lg" class="chat-page__hero">
        <div>
          <p class="chat-page__eyebrow">Companion Mode</p>
          <h2>从今天的状态开始，慢慢聊一会儿</h2>
        </div>
      </KuCard>

      <KuCard v-if="summaryStore.summary" padding="lg" class="chat-page__context">
        <div class="chat-page__panel-head">
          <div>
            <p class="chat-page__eyebrow">Today Context</p>
            <h3>{{ summaryStore.summary.praise_text }}</h3>
          </div>
          <KuButton @click="useSummaryContext">带着摘要开聊</KuButton>
        </div>

        <div class="chat-page__metrics">
          <article class="chat-page__metric">
            <span>总时长</span>
            <strong>{{ summaryStore.summary.total_hours }}h</strong>
            <small>今天累计记录</small>
          </article>
          <article class="chat-page__metric">
            <span>工作</span>
            <strong>{{ summaryStore.summary.work_hours }}h</strong>
            <small>专注投入</small>
          </article>
          <article class="chat-page__metric">
            <span>娱乐</span>
            <strong>{{ summaryStore.summary.entertainment_hours }}h</strong>
            <small>休息恢复</small>
          </article>
          <article class="chat-page__metric">
            <span>专注分</span>
            <strong>{{ summaryStore.summary.focus_score }}</strong>
            <small>满分 100</small>
          </article>
        </div>

        <div v-if="summaryStore.summary.top_apps.length" class="chat-page__apps">
          <p>今日高频应用</p>
          <div class="chat-page__app-list">
            <span
              v-for="app in summaryStore.summary.top_apps.slice(0, 5)"
              :key="app.name"
              class="chat-page__app-pill"
            >
              {{ app.name }}
            </span>
          </div>
        </div>
      </KuCard>

      <KuCard padding="lg" class="chat-page__prompts">
        <div class="chat-page__panel-head">
          <div>
            <p class="chat-page__eyebrow">Quick Start</p>
            <h3>选择一种模式</h3>
          </div>
        </div>

        <div class="chat-page__prompt-grid">
          <button
            v-for="prompt in starterPrompts"
            :key="prompt.title"
            type="button"
            class="chat-page__prompt-card"
            @click="usePrompt(prompt.content)"
          >
            <strong>{{ prompt.title }}</strong>
            <span>{{ prompt.caption }}</span>
          </button>
        </div>
      </KuCard>
    </div>

    <div v-else class="chat-page__conversation">
      <KuCard v-if="summaryStore.summary" padding="md" class="chat-page__conversation-context">
        <div>
          <p class="chat-page__eyebrow">Conversation Context</p>
          <h3>{{ summaryStore.summary.praise_text }}</h3>
        </div>
        <div class="chat-page__context-tags">
          <span>工作 {{ summaryStore.summary.work_hours }}h</span>
          <span>娱乐 {{ summaryStore.summary.entertainment_hours }}h</span>
        </div>
      </KuCard>

      <div ref="messagesRef" class="chat-page__stream">
        <div class="chat-page__message-stack">
          <article
            v-for="msg in store.messages"
            :key="msg.id"
            class="chat-page__message"
            :class="`chat-page__message--${msg.role}`"
          >
            <div class="chat-page__avatar">{{ msg.role === 'assistant' ? '夸' : '我' }}</div>
            <div class="chat-page__message-body">
              <header class="chat-page__message-meta">
                <strong>{{ msg.role === 'assistant' ? '夸夸' : '我' }}</strong>
                <span>{{ formatTime(msg.timestamp) }}</span>
                <em v-if="msg.status === 'sending'">发送中</em>
                <em v-else-if="msg.status === 'streaming'">回复中...</em>
                <em v-else-if="msg.status === 'failed'" class="chat-page__failed">发送失败</em>
              </header>
              <div class="chat-page__bubble">
                <p>{{ msg.content }}</p>
              </div>
            </div>
          </article>
        </div>
      </div>
    </div>

    <div class="chat-page__composer-wrap">
      <div v-if="store.error" class="chat-page__error">
        {{ store.error }}
      </div>

      <div class="chat-page__composer">
        <div class="chat-page__toolbar">
          <KuButton size="sm" @click="store.resetChat()">新建对话</KuButton>
          <KuButton size="sm" variant="ghost" @click="useSummaryContext">带入今日摘要</KuButton>
          <KuButton size="sm" variant="ghost" @click="prefillEncouragement">获取鼓励</KuButton>
        </div>

        <div class="chat-page__input-shell">
          <textarea
            ref="textareaRef"
            v-model="inputMessage"
            class="chat-page__textarea"
            placeholder="告诉夸夸今天发生了什么、你现在的感受，或者你想得到什么帮助。"
            rows="1"
            @input="resizeTextarea"
            @keydown.enter.exact.prevent="sendMessage"
          ></textarea>

          <KuButton
            variant="primary"
            :loading="store.loading"
            :disabled="!inputMessage.trim()"
            @click="sendMessage"
          >
            发送
          </KuButton>
        </div>
      </div>

      <p class="chat-page__footnote">当前回复会在拿到结果后逐字显示，聊天逻辑和上下文传递保持现有实现。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import KuButton from '@/components/base/KuButton.vue'
import KuCard from '@/components/base/KuCard.vue'
import { useChatStore } from '@/store/chat'
import { useSummaryStore } from '@/store/summary'

const store = useChatStore()
const summaryStore = useSummaryStore()
const inputMessage = ref('')
const messagesRef = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const starterPrompts = [
  {
    title: '结合今日摘要聊聊',
    caption: '把今天的行为总结延展成一次温和对话。',
    content: '请结合今天的摘要，陪我一起看看今天有哪些地方做得不错。',
  },
  {
    title: '想要一点鼓励',
    caption: '在有些疲惫的时候，得到温柔回应。',
    content: '我今天有点累，你可以结合我今天的表现鼓励我一下吗？',
  },
  {
    title: '整理下一步行动',
    caption: '把接下来要做的事拆得更轻一点。',
    content: '请帮我想想，基于今天的状态，我接下来最适合先做哪一个小步骤？',
  },
]

onMounted(() => {
  if (!summaryStore.summary && !summaryStore.loading) {
    summaryStore.fetchTodaySummary()
  }

  if (store.draft) {
    inputMessage.value = store.draft
    store.setDraft('')
  }

  resizeTextarea()
})

watch(
  () => store.draft,
  (value) => {
    if (!value) return
    inputMessage.value = value
    store.setDraft('')
    resizeTextarea()
    textareaRef.value?.focus()
  },
)

watch(
  () => store.messages.map((msg) => `${msg.id}:${msg.content.length}:${msg.status}`).join('|'),
  async () => {
    await nextTick()
    scrollToBottom()
  },
)

async function sendMessage() {
  const message = inputMessage.value.trim()
  if (!message) return

  inputMessage.value = ''
  resizeTextarea()

  const context = summaryStore.summary
    ? {
        total_hours: summaryStore.summary.total_hours,
        work_hours: summaryStore.summary.work_hours,
        entertainment_hours: summaryStore.summary.entertainment_hours,
      }
    : undefined

  await store.sendMessage(message, context)
}

function usePrompt(content: string) {
  inputMessage.value = content
  resizeTextarea()
  textareaRef.value?.focus()
}

function useSummaryContext() {
  if (!summaryStore.summary) {
    inputMessage.value = '请根据我最近的活动，陪我一起回顾一下今天。'
  } else {
    inputMessage.value =
      `请结合今天的摘要陪我回顾一下。今天总共活跃 ${summaryStore.summary.total_hours} 小时，` +
      `其中工作 ${summaryStore.summary.work_hours} 小时，娱乐 ${summaryStore.summary.entertainment_hours} 小时。`
  }

  resizeTextarea()
  textareaRef.value?.focus()
}

function prefillEncouragement() {
  inputMessage.value = '请温柔地鼓励我一下，也提醒我今天有哪些地方做得不错。'
  resizeTextarea()
  textareaRef.value?.focus()
}

function resizeTextarea() {
  if (!textareaRef.value) return
  textareaRef.value.style.height = '0px'
  textareaRef.value.style.height = `${Math.min(textareaRef.value.scrollHeight, 240)}px`
}

function scrollToBottom() {
  if (!messagesRef.value) return
  messagesRef.value.scrollTop = messagesRef.value.scrollHeight
}

function formatTime(date: Date) {
  return `${`${date.getHours()}`.padStart(2, '0')}:${`${date.getMinutes()}`.padStart(2, '0')}`
}
</script>

<style scoped>
.chat-page {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: var(--space-5);
  min-height: calc(100vh - 160px);
}

.chat-page__welcome,
.chat-page__conversation {
  display: flex;
  max-width: var(--content-max-width);
  margin: 0 auto;
  flex-direction: column;
  gap: var(--space-5);
  width: 100%;
}

.chat-page__hero {
  background:
    radial-gradient(circle at top left, rgba(201, 138, 105, 0.16), transparent 30%),
    var(--color-bg-card);
}

.chat-page__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.chat-page__hero h2 {
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.15;
  letter-spacing: -0.04em;
}

.chat-page__hero p:last-child {
  max-width: 700px;
  margin-top: var(--space-3);
  color: var(--color-text-secondary);
}

.chat-page__panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.chat-page__panel-head h3,
.chat-page__conversation-context h3 {
  font-size: var(--font-size-2xl);
}

.chat-page__metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-3);
}

.chat-page__metric {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.chat-page__metric span,
.chat-page__metric small,
.chat-page__apps p {
  color: var(--color-text-secondary);
}

.chat-page__metric strong {
  font-size: var(--font-size-3xl);
}

.chat-page__apps {
  margin-top: var(--space-5);
}

.chat-page__app-list,
.chat-page__context-tags {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.chat-page__app-pill,
.chat-page__context-tags span {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 var(--space-3);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
}

.chat-page__prompt-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
}

.chat-page__prompt-card {
  display: flex;
  min-height: 150px;
  flex-direction: column;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5);
  color: inherit;
  text-align: left;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.55), rgba(255, 255, 255, 0.1)),
    var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition:
    transform var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out),
    border-color var(--duration-fast) var(--ease-out);
}

.chat-page__prompt-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-md);
}

.chat-page__prompt-card span {
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
}

.chat-page__conversation-context {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.chat-page__stream {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.chat-page__message-stack {
  display: flex;
  max-width: var(--content-max-width);
  margin: 0 auto;
  flex-direction: column;
  gap: var(--space-3);
}

.chat-page__message {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-4);
  border-radius: var(--radius-xl);
  align-self: flex-start;
}

.chat-page__message--assistant {
  background: rgba(255, 255, 255, 0.45);
}

.chat-page__message--user {
  flex-direction: row-reverse;
  align-self: flex-end;
}

.chat-page__message--user .chat-page__avatar {
  color: var(--color-text-inverse);
  background: var(--color-accent);
  border-color: rgba(201, 138, 105, 0.28);
}

.chat-page__message--user .chat-page__message-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.chat-page__message--user .chat-page__bubble {
  color: var(--color-text-inverse);
  background: linear-gradient(135deg, var(--color-accent), #d18d69);
  border-color: transparent;
}

.chat-page__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.chat-page__message-body {
  min-width: 0;
}

.chat-page__message-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.chat-page__message-meta strong {
  color: var(--color-text-primary);
}

.chat-page__message-meta em {
  font-style: normal;
}

.chat-page__failed {
  color: var(--color-danger);
}

.chat-page__bubble {
  display: inline-block;
  max-width: min(100%, 620px);
  padding: var(--space-3) var(--space-4);
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(126, 104, 84, 0.12);
  border-radius: 22px;
  line-height: var(--line-height-relaxed);
  word-break: break-word;
  white-space: pre-wrap;
}

.chat-page__composer-wrap {
  position: sticky;
  bottom: 0;
  max-width: var(--content-max-width);
  width: 100%;
  margin: 0 auto;
  padding-bottom: var(--space-2);
  background: linear-gradient(180deg, rgba(250, 247, 244, 0), var(--color-bg-primary) 45%);
}

.chat-page__error {
  margin-bottom: var(--space-3);
  padding: var(--space-4);
  color: var(--color-danger);
  background: var(--color-danger-soft);
  border: 1px solid rgba(192, 96, 80, 0.18);
  border-radius: var(--radius-lg);
}

.chat-page__composer {
  padding: var(--space-3);
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(10px);
}

.chat-page__toolbar {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  padding: var(--space-1) var(--space-1) var(--space-3);
}

.chat-page__input-shell {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
}

.chat-page__textarea {
  flex: 1;
  max-height: 240px;
  min-height: 52px;
  padding: var(--space-3) var(--space-1) var(--space-2);
  color: var(--color-text-primary);
  resize: none;
  background: transparent;
  border: none;
  outline: none;
}

.chat-page__textarea::placeholder {
  color: var(--color-text-tertiary);
}

.chat-page__footnote {
  margin-top: var(--space-2);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  text-align: center;
}

@media (max-width: 960px) {
  .chat-page__panel-head,
  .chat-page__conversation-context {
    flex-direction: column;
    align-items: flex-start;
  }

  .chat-page__metrics,
  .chat-page__prompt-grid {
    grid-template-columns: 1fr;
  }

  .chat-page__message,
  .chat-page__message--user {
    width: 100%;
    align-self: stretch;
    flex-direction: row;
    padding: var(--space-4);
  }

  .chat-page__message--user {
    flex-direction: row-reverse;
  }

  .chat-page__message-body {
    flex: 1;
    min-width: 0;
  }

  .chat-page__input-shell {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
