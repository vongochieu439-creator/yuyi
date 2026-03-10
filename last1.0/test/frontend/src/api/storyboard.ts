import request from './request'

/** 获取分镜数据 */
export function getStoryboard(projectId: string) {
  return request.get(`/storyboard/${projectId}`)
}

/** 批量审核 */
export function reviewFrames(projectId: string, actions: Array<{ frame_id: number; action: string; feedback?: string }>) {
  return request.post(`/storyboard/${projectId}/review`, { actions })
}

/** 单帧重新生成 */
export function regenerateFrame(projectId: string, frameId: number, feedback?: string) {
  return request.post(`/storyboard/${projectId}/regenerate-frame/${frameId}`, { feedback })
}

/** 获取成本估算 */
export function getCostEstimate(projectId: string) {
  return request.get(`/storyboard/${projectId}/cost-estimate`)
}

// ==================== SSE 流式接口 ====================

function createSSEFetch(
  url: string,
  body: any,
  onEvent: (event: string, data: any) => void,
  onError?: (err: any) => void,
): AbortController {
  const controller = new AbortController()
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

  fetch(`${baseUrl}/api${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
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
              // ignore
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

/** SSE生成分镜 */
export function generateStoryboard(
  params: { user_input: string; style: string; hook_type?: string; total_duration?: number; character_description?: string; product_detail?: string },
  onEvent: (event: string, data: any) => void,
  onError?: (err: any) => void,
): AbortController {
  return createSSEFetch('/storyboard/generate', params, onEvent, onError)
}

/** SSE生成分镜图 */
export function generateImages(
  projectId: string,
  onEvent: (event: string, data: any) => void,
  onError?: (err: any) => void,
): AbortController {
  return createSSEFetch(`/storyboard/${projectId}/generate-images`, {}, onEvent, onError)
}

/** SSE视频制作 */
export function produceVideo(
  projectId: string,
  onEvent: (event: string, data: any) => void,
  onError?: (err: any) => void,
): AbortController {
  return createSSEFetch(`/storyboard/${projectId}/produce`, {}, onEvent, onError)
}
