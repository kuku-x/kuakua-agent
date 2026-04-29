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

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const messages = ref<WsMessage[]>([])
  let reconnectTimer: number | null = null

  const listeners = new Map<string, Set<(event: WsMessage) => void>>()

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws`

    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      connected.value = true
      console.log('[WS] Connected')
    }

    ws.value.onclose = () => {
      connected.value = false
      console.log('[WS] Disconnected, reconnecting in 3s...')
      reconnectTimer = window.setTimeout(connect, 3000)
    }

    ws.value.onerror = (err) => {
      console.error('[WS] Error', err)
    }

    ws.value.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WsMessage
        messages.value.push(msg)
        listeners.get(msg.type)?.forEach(cb => cb(msg))
        listeners.get('*')?.forEach(cb => cb(msg))
      } catch {
        // ignore parse errors
      }
    }
  }

  function on(type: string, callback: (event: WsMessage) => void) {
    if (!listeners.has(type)) {
      listeners.set(type, new Set())
    }
    listeners.get(type)!.add(callback)
  }

  function off(type: string, callback: (event: WsMessage) => void) {
    listeners.get(type)?.delete(callback)
  }

  function disconnect() {
    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws.value?.close()
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return { connected, messages, on, off, disconnect }
}