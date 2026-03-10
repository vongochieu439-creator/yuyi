import request from './request'
import { createSSEFetch } from './sse'

// ==================== 原有接口 ====================

export const smartCreate = (data: {
  product_name: string
  industry?: string
  target_duration?: number
  reference_text?: string
  brand_profile_id?: string
  product_detail?: string
  mode?: string
  template_id?: string
}) => request.post('/script/smart-create', data)

export const selectDirection = (sessionId: string, directionId: number) =>
  request.post(`/script/${sessionId}/select`, { direction_id: directionId })

export const selectHook = (sessionId: string, hookId: number) =>
  request.post(`/script/${sessionId}/select-hook`, { hook_id: hookId })

export const chatRefine = (projectId: string, message: string, chatHistory: Array<{role: string; content: string}>) =>
  request.post(`/script/${projectId}/chat`, { message, chat_history: chatHistory })

export const lockScript = (projectId: string) =>
  request.post(`/script/${projectId}/lock`)

export const extractProductInfo = (sourceType: string, content: string) =>
  request.post('/script/extract-product-info', { source_type: sourceType, content })

export const intakeNextQuestion = (sessionId: string, chatHistory: Array<{role: string; content: string}>) =>
  request.post('/script/intake/next-question', { session_id: sessionId, chat_history: chatHistory })

// ==================== V2: 一体化流水线接口 ====================

export const selectScript = (sessionId: string, scriptId: number, scriptData?: any, productName?: string, productDetail?: string, industry?: string) =>
  request.post(`/script/${sessionId}/select-script`, {
    script_id: scriptId,
    script_data: scriptData || null,
    product_name: productName || null,
    product_detail: productDetail || null,
    industry: industry || null,
  })

export const regenerateScripts = (sessionId: string, feedback?: string) =>
  request.post(`/script/${sessionId}/regenerate-scripts`, { feedback })

export const chatRefineV2 = (
  projectId: string,
  message: string,
  chatHistory: Array<{role: string; content: string}>,
  allScriptsContext?: any[]
) =>
  request.post(`/script/${projectId}/chat-v2`, {
    message,
    chat_history: chatHistory,
    all_scripts_context: allScriptsContext,
  })

export const updateFrame = (projectId: string, shotId: number, narration?: string, visualDescription?: string) =>
  request.post(`/script/${projectId}/update-frame`, {
    shot_id: shotId,
    narration,
    visual_description: visualDescription,
  })

export const regenerateFrameImage = (projectId: string, shotId: number, feedback?: string, globalStyle?: string) =>
  request.post(`/script/${projectId}/regenerate-frame-image/${shotId}`, {
    feedback,
    global_style: globalStyle || '',
  })

export const skipToPreview = (sessionId: string, userScript: string, targetDuration: number = 60) =>
  request.post(`/script/${sessionId}/skip-to-preview`, {
    user_script: userScript,
    target_duration: targetDuration,
  })

// ==================== V3: 数据驱动接口 ====================

export const smartCreateV2 = (data: {
  product_name: string
  industry?: string
  target_duration?: number
  reference_text?: string
  brand_profile_id?: string
  product_detail?: string
}) => request.post('/script/smart-create-v2', data)

export const getResearchStatus = (sessionId: string) =>
  request.get(`/script/${sessionId}/status`)

export const getResearchResult = (sessionId: string) =>
  request.get(`/script/${sessionId}/result`)

export const selectDataDrivenScript = (sessionId: string, scriptId: number) =>
  request.post(`/script/${sessionId}/select-data-script`, { script_id: scriptId })

// ==================== 深度模式接口 ====================

export const deepChat = (data: {
  session_id?: string
  message: string
  chat_history: Array<{role: string; content: string}>
  product_name?: string
  industry?: string
}) => request.post('/script/deep/chat', data)

export const deepInspire = (data: {
  session_id?: string
  product_name: string
  industry?: string
}) => request.post('/script/deep/inspire', data)

export const deepGenerate = (sessionId: string) =>
  request.post(`/script/deep/generate/${sessionId}`)

// ==================== SSE 流式接口 ====================

export function generatePreview(
  projectId: string,
  onEvent: (event: string, data: any) => void,
  onError?: (err: any) => void,
  globalStyle?: string,
): AbortController {
  return createSSEFetch(
    `/script/${projectId}/generate-preview`,
    { global_style: globalStyle || '' },
    onEvent,
    onError,
  )
}

export function produceVideo(
  projectId: string,
  onEvent: (event: string, data: any) => void,
  onError?: (err: any) => void,
): AbortController {
  return createSSEFetch(`/script/${projectId}/produce-video`, {}, onEvent, onError)
}
