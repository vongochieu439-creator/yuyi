import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  generateStoryboard,
  generateImages,
  produceVideo,
  reviewFrames,
  regenerateFrame,
  getCostEstimate,
  getStoryboard,
} from '../api/storyboard'

export interface StoryboardFrame {
  frame_id: number
  visual_prompt: string
  narration: string
  duration: number
  shot_type: string
  camera_movement: string
  lighting: string
  mood: string
  status: 'pending' | 'generating' | 'generated' | 'approved' | 'rejected' | 'regenerating'
  feedback: string | null
  image_url: string | null
  video_url: string | null
  cost_estimate: { image: number; video: number }
}

export interface CostEstimate {
  image_count: number
  image_unit_cost: number
  image_total: number
  video_total_seconds: number
  video_total: number
  tts_cost: number
  grand_total: number
}

export const useStoryboardStore = defineStore('storyboard', () => {
  // State
  const projectId = ref('')
  const title = ref('')
  const userInput = ref('')
  const style = ref('cinematic')
  const hookType = ref<string | null>(null)
  const totalDuration = ref(45)
  const characterDescription = ref('')  // 复用为行业字段
  const productDetail = ref('')

  const step = ref<'input' | 'generating' | 'storyboard' | 'images' | 'review' | 'producing' | 'done' | 'error'>('input')
  const progress = ref('')
  const generating = ref(false)
  const errorMessage = ref('')

  const frames = ref<StoryboardFrame[]>([])
  const character = ref<{ description: string; name: string }>({ description: '', name: '' })
  const analysis = ref<any>({})
  const hookTypeResult = ref('')
  const frameworkResult = ref('')
  const costEstimate = ref<CostEstimate | null>(null)
  const videoUrl = ref('')
  const elapsedSeconds = ref(0)

  let abortController: AbortController | null = null

  // Computed
  const allApproved = computed(() =>
    frames.value.length > 0 && frames.value.every(f => f.status === 'approved')
  )
  const approvedCount = computed(() =>
    frames.value.filter(f => f.status === 'approved').length
  )
  const generatedCount = computed(() =>
    frames.value.filter(f => f.image_url).length
  )

  // ==================== Actions ====================

  /** 生成分镜脚本 */
  const startGenerate = () => {
    if (!userInput.value.trim()) return
    generating.value = true
    step.value = 'generating'
    progress.value = 'AI正在分析话题...'
    frames.value = []
    errorMessage.value = ''
    videoUrl.value = ''

    abortController = generateStoryboard(
      {
        user_input: userInput.value,
        style: style.value,
        hook_type: hookType.value || undefined,
        total_duration: totalDuration.value,
        character_description: characterDescription.value || undefined,
        product_detail: productDetail.value || undefined,
      },
      (event, data) => {
        switch (event) {
          case 'started':
            projectId.value = data.project_id
            progress.value = data.message
            break

          case 'phase_complete':
            progress.value = `${data.phase}阶段完成`
            break

          case 'storyboard_ready':
            title.value = data.title || ''
            frames.value = data.frames || []
            character.value = data.character || { description: '', name: '' }
            analysis.value = data.analysis || {}
            hookTypeResult.value = data.hook_type || ''
            frameworkResult.value = data.psychology_framework || ''
            step.value = 'storyboard'
            generating.value = false
            progress.value = '分镜脚本已就绪'
            break

          case 'error':
            errorMessage.value = data.message
            step.value = 'error'
            generating.value = false
            break
        }
      },
      (err) => {
        errorMessage.value = err.message || '连接失败'
        step.value = 'error'
        generating.value = false
      },
    )
  }

  /** 生成所有分镜图 */
  const startGenerateImages = () => {
    generating.value = true
    step.value = 'images'
    progress.value = '正在生成分镜图...'

    abortController = generateImages(
      projectId.value,
      (event, data) => {
        switch (event) {
          case 'image_generating':
            progress.value = `正在生成帧 ${data.frame_id}...`
            updateFrameStatus(data.frame_id, 'generating')
            break

          case 'image_generated':
            updateFrameImage(data.frame_id, data.image_url)
            updateFrameStatus(data.frame_id, 'generated')
            progress.value = `帧 ${data.frame_id} 生成完成`
            break

          case 'image_failed':
            updateFrameStatus(data.frame_id, 'pending')
            break

          case 'images_complete':
            step.value = 'review'
            generating.value = false
            progress.value = `分镜图生成完成: ${data.success}/${data.total} 成功`
            break

          case 'error':
            errorMessage.value = data.message
            step.value = 'error'
            generating.value = false
            break
        }
      },
      (err) => {
        errorMessage.value = err.message || '图片生成失败'
        step.value = 'error'
        generating.value = false
      },
    )
  }

  /** 批量审核 */
  const submitReview = async (actions: Array<{ frame_id: number; action: string; feedback?: string }>) => {
    try {
      const result: any = await reviewFrames(projectId.value, actions)
      // 更新本地状态
      for (const action of actions) {
        const frame = frames.value.find(f => f.frame_id === action.frame_id)
        if (frame) {
          frame.status = action.action === 'approve' ? 'approved' : 'rejected'
          if (action.feedback) frame.feedback = action.feedback
        }
      }
      return result
    } catch (e: any) {
      errorMessage.value = e.message
      throw e
    }
  }

  /** 全部通过 */
  const approveAll = async () => {
    const actions = frames.value
      .filter(f => f.status === 'generated' || f.status === 'rejected')
      .map(f => ({ frame_id: f.frame_id, action: 'approve' }))
    if (actions.length > 0) {
      await submitReview(actions)
    }
  }

  /** 单帧重新生成 */
  const regenFrame = async (frameId: number, feedback?: string) => {
    updateFrameStatus(frameId, 'regenerating')
    try {
      const result: any = await regenerateFrame(projectId.value, frameId, feedback)
      updateFrameImage(result.frame_id, result.image_url)
      updateFrameStatus(result.frame_id, 'generated')
    } catch (e: any) {
      updateFrameStatus(frameId, 'generated')
      errorMessage.value = e.message
    }
  }

  /** 加载成本估算 */
  const loadCostEstimate = async () => {
    try {
      costEstimate.value = await getCostEstimate(projectId.value) as any
    } catch (e: any) {
      console.error('成本估算失败', e)
    }
  }

  /** 开始视频制作 */
  const startProduce = () => {
    generating.value = true
    step.value = 'producing'
    progress.value = '正在制作视频...'

    abortController = produceVideo(
      projectId.value,
      (event, data) => {
        switch (event) {
          case 'producing_started':
            progress.value = `开始制作 ${data.total_frames} 个场景...`
            break
          case 'video_generating':
            progress.value = `帧 ${data.frame_id} 视频生成中...`
            break
          case 'video_generated':
            progress.value = `帧 ${data.frame_id} 视频完成`
            break
          case 'composing':
            progress.value = data.message
            break
          case 'produce_complete':
            videoUrl.value = data.video_url
            elapsedSeconds.value = data.elapsed_seconds
            step.value = 'done'
            generating.value = false
            progress.value = `视频制作完成！用时 ${data.elapsed_seconds} 秒`
            break
          case 'error':
            errorMessage.value = data.message
            step.value = 'error'
            generating.value = false
            break
        }
      },
      (err) => {
        errorMessage.value = err.message || '视频制作失败'
        step.value = 'error'
        generating.value = false
      },
    )
  }

  /** 停止 */
  const stop = () => {
    abortController?.abort()
    generating.value = false
  }

  /** 重置 */
  const reset = () => {
    stop()
    projectId.value = ''
    title.value = ''
    userInput.value = ''
    productDetail.value = ''
    style.value = 'cinematic'
    hookType.value = null
    step.value = 'input'
    progress.value = ''
    generating.value = false
    errorMessage.value = ''
    frames.value = []
    character.value = { description: '', name: '' }
    analysis.value = {}
    costEstimate.value = null
    videoUrl.value = ''
    elapsedSeconds.value = 0
  }

  // Helpers
  const updateFrameStatus = (frameId: number, status: StoryboardFrame['status']) => {
    const frame = frames.value.find(f => f.frame_id === frameId)
    if (frame) frame.status = status
  }
  const updateFrameImage = (frameId: number, imageUrl: string) => {
    const frame = frames.value.find(f => f.frame_id === frameId)
    if (frame) frame.image_url = imageUrl
  }

  return {
    // State
    projectId, title, userInput, productDetail, style, hookType, totalDuration, characterDescription,
    step, progress, generating, errorMessage,
    frames, character, analysis, hookTypeResult, frameworkResult,
    costEstimate, videoUrl, elapsedSeconds,
    // Computed
    allApproved, approvedCount, generatedCount,
    // Actions
    startGenerate, startGenerateImages, submitReview, approveAll,
    regenFrame, loadCostEstimate, startProduce, stop, reset,
  }
})
