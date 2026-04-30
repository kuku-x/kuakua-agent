import { onMounted, onUnmounted, ref } from 'vue'

export interface PraisePushEvent {
  type: 'praise_push'
  data: { content: string; trigger: string }
}

export interface SummaryProgressEvent {
  type: 'summary_progress'
  data: { date: string; progress: string }
}

export interface ChatStreamEvent {
  type: 'chat_stream'
  data: { chat_id: string; chunk: string; done: boolean }
}

export type WsMessage = PraisePushEvent | SummaryProgressEvent | ChatStreamEvent

// ============ 模块级单例状态 ============
// 所有 useWebSocket() 调用者共享同一个连接，避免多实例泄漏。
const MAX_MESSAGES = 200

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let intentionalClose = false
let refCount = 0

const connected = ref(false)
const messages = ref<WsMessage[]>([])
const listeners: Map<string, Set<(event: WsMessage) => void>> = new Map()

function buildWsUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}/ws`
}

function connect() {
  // 防止重复连接
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return
  }

  const url = buildWsUrl()
  ws = new WebSocket(url)

  ws.onopen = () => {
    connected.value = true
    console.log('[WS] Connected')
  }

  ws.onclose = () => {
    connected.value = false
    console.log('[WS] Disconnected')
    // 只有非主动断开时才重连
    if (!intentionalClose) {
      if (reconnectTimer !== null) clearTimeout(reconnectTimer)
      reconnectTimer = setTimeout(connect, 3000)
    }
  }

  ws.onerror = (err) => {
    console.error('[WS] Error', err)
  }

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data) as WsMessage
      // 环形缓冲：保持最近 N 条消息
      if (messages.value.length >= MAX_MESSAGES) {
        messages.value = messages.value.slice(-MAX_MESSAGES + 1)
      }
      messages.value.push(msg)
      listeners.get(msg.type)?.forEach(cb => cb(msg))
      listeners.get('*')?.forEach(cb => cb(msg))
    } catch {
      // ignore parse errors
    }
  }
}

function disconnect() {
  intentionalClose = true
  if (reconnectTimer !== null) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  ws?.close()
  ws = null
}

/**
 * 每个调用 useWebSocket 的组件共享同一个 WebSocket 连接。
 * 组件挂载时引用计数 +1，卸载时 -1；归零时真正断开。
 */
export function useWebSocket() {
  onMounted(() => {
    refCount++
    if (refCount === 1) {
      intentionalClose = false
      connect()
    }
  })

  onUnmounted(() => {
    refCount--
    if (refCount <= 0) {
      refCount = 0
      disconnect()
    }
  })

  function on(type: string, callback: (event: WsMessage) => void) {
    if (!listeners.has(type)) {
      listeners.set(type, new Set())
    }
    listeners.get(type)!.add(callback)
    // 返回取消订阅函数，方便调用方在 onUnmounted 中清理
    return () => {
      listeners.get(type)?.delete(callback)
    }
  }

  function off(type: string, callback: (event: WsMessage) => void) {
    listeners.get(type)?.delete(callback)
  }

  return { connected, messages, on, off, disconnect }
}
