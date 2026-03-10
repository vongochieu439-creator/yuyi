import request from './request'

export function getStyles() {
  return request.get('/comic-drama/styles')
}

export function getHistory() {
  return request.get('/comic-drama/history')
}

export function getResult(taskId: string) {
  return request.get(`/comic-drama/result/${taskId}`)
}

/**
 * SSE流式生成漫剧
 */
export function generateComicDrama(
  userInput: string,
  style: string,
  onEvent: (event: string, data: any) => void,
  onError?: (err: any) => void,
): AbortController {
  const controller = new AbortController()
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

  fetch(`${baseUrl}/api/comic-drama/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput, style }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = 'message'
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              onEvent(currentEvent, data)
            } catch {
              // ignore parse errors
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.(err)
      }
    })

  return controller
}
