import { ref, onBeforeUnmount } from 'vue'

export function useWebSocket(url: string) {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnects = 3
  let _onMessage: ((data: Record<string, unknown>) => void) | null = null

  const connect = (
    onMessage: (data: Record<string, unknown>) => void,
    onOpen?: () => void,
    onError?: (err: Event) => void
  ) => {
    _onMessage = onMessage
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const fullUrl = `${protocol}//${window.location.host}${url}`
    console.log('[WS] Connecting to:', fullUrl)
    ws.value = new WebSocket(fullUrl)

    ws.value.onopen = () => {
      console.log('[WS] Connected')
      connected.value = true
      reconnectAttempts.value = 0
      onOpen?.()
    }

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        _onMessage?.(data)
      } catch {
        // ignore parse errors
      }
    }

    ws.value.onerror = (err) => {
      console.error('[WS] Error:', err)
      onError?.(err)
    }

    ws.value.onclose = (event) => {
      console.log('[WS] Closed:', event.code, event.reason)
      connected.value = false
      if (reconnectAttempts.value < maxReconnects && _onMessage) {
        reconnectAttempts.value++
        setTimeout(() => connect(_onMessage!, onOpen, onError), 2000 * reconnectAttempts.value)
      }
    }
  }

  const send = (data: Record<string, unknown>) => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data))
    } else {
      console.warn('[WS] Cannot send, readyState:', ws.value?.readyState)
    }
  }

  const close = () => {
    reconnectAttempts.value = maxReconnects // Prevent reconnection
    ws.value?.close()
    ws.value = null
    connected.value = false
  }

  onBeforeUnmount(() => {
    close()
  })

  return { ws, connected, connect, send, close }
}
