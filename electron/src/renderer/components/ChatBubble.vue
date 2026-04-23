<template>
  <div class="chat-bubble" :class="role">
    <div class="avatar">{{ role === 'user' ? '🙂' : '🤖' }}</div>
    <div class="content">{{ content }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  role: 'user' | 'assistant'
  content: string
}>()
</script>

<style scoped>
.chat-bubble {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.chat-bubble.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
}

.user .content {
  background: #1890ff;
  color: #fff;
}

.assistant .content {
  background: #f5f5f5;
  color: #333;
}
</style>