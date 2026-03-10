import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ProductInfo, Direction, Hook, Shot, QualityCheck, ChatMessage,
  Template, IntakeMessage, FullScript, PreviewFrame,
  DataDrivenScript, ResearchData, ResearchProgress,
} from '../types'
import * as api from '../api/scriptCreator'

export const useScriptCreatorStore = defineStore('scriptCreator', () => {
  // ==================== State ====================
  // Step: 0=产品信息, 1=调研/生成, 2=选择脚本, 3=脚本打磨, 4=分镜预览, 5=视频生成, 6=完成
  const step = ref(0)
  const mode = ref<'quick' | 'deep' | 'data_driven'>('quick')
  const productInfo = ref<ProductInfo | null>(null)
  const sessionId = ref('')
  const projectId = ref('')
  const selectedTemplate = ref<Template | null>(null)
  const loading = ref(false)
  const researchProgress = ref('')
  const competitorSummary = ref<Record<string, unknown>>({})
  const marketSummary = ref<Record<string, unknown>>({})
  const targetDuration = ref(60)

  // Legacy (kept for backward compat)
  const directions = ref<Direction[]>([])
  const selectedDirection = ref<Direction | null>(null)
  const hooks = ref<Hook[]>([])
  const selectedHook = ref<Hook | null>(null)
  const sellingPoints = ref<string[]>([])

  // V2: Multi-script
  const generatedScripts = ref<FullScript[]>([])
  const selectedScriptId = ref<number | null>(null)
  const allScriptsContext = ref<FullScript[]>([])

  // Script editing
  const scriptShots = ref<Shot[]>([])
  const qualityCheck = ref<QualityCheck | null>(null)
  const chatMessages = ref<ChatMessage[]>([])

  // Preview
  const previewFrames = ref<PreviewFrame[]>([])
  const previewGenerating = ref(false)
  const globalStyle = ref('')         // 用户输入的全局风格提示词
  const promptEngineeringStatus = ref('')  // AI 正在优化提示词的状态文字

  // Video production
  const videoGenerating = ref(false)
  const videoProgress = ref('')
  const videoUrl = ref('')
  const videoPercent = ref(0)

  // Deep mode (legacy)
  const intakeMessages = ref<IntakeMessage[]>([])
  const collectedSummary = ref<Record<string, string>>({})

  // Deep mode V2: Creative Studio
  const deepMessages = ref<Array<{role: string; content: string; tool_used?: string; tool_data?: any}>>([])
  const deepInspirations = ref<Array<{angle: string; source: string; data_backing: string; suggested_hook: string}>>([])
  const deepSessionId = ref('')
  const deepLoading = ref(false)

  // V3: Data-driven mode
  const dataDrivenMode = ref(false)
  const researchPhase = ref<string>('idle')  // idle|searching|analyzing|generating|done|error
  const researchDetails = ref<string[]>([])
  const researchPolling = ref(false)
  const researchError = ref<string | null>(null)
  const dataDrivenScripts = ref<DataDrivenScript[]>([])
  const researchData = ref<ResearchData | null>(null)
  let researchPollTimer: ReturnType<typeof setInterval> | null = null

  // ==================== Getters ====================
  const canProceed = computed(() => {
    switch (step.value) {
      case 0: return productInfo.value !== null
      case 2: return selectedScriptId.value !== null
      default: return true
    }
  })

  const selectedScript = computed(() => {
    if (selectedScriptId.value === null) return null
    return generatedScripts.value.find(s => s.script_id === selectedScriptId.value) || null
  })

  // ==================== V2 Actions ====================

  /** Step 0→1→2: 调研 + 生成3个完整脚本 */
  const generateScripts = async () => {
    if (!productInfo.value) return
    loading.value = true
    researchProgress.value = '正在分析市场并生成脚本...'
    step.value = 1

    try {
      const res: any = await api.smartCreate({
        product_name: productInfo.value.product_name,
        industry: productInfo.value.category,
        target_duration: targetDuration.value,
        product_detail: [
          productInfo.value.core_features.join('; '),
          productInfo.value.target_audience ? `目标用户: ${productInfo.value.target_audience}` : '',
          productInfo.value.differentiators?.length ? `差异化: ${productInfo.value.differentiators.join('; ')}` : '',
          productInfo.value.use_cases?.length ? `使用场景: ${productInfo.value.use_cases.join('; ')}` : '',
        ].filter(Boolean).join('\n') || productInfo.value.product_name,
        mode: mode.value === 'deep' ? 'detailed' : 'quick',
        template_id: selectedTemplate.value?.id,
      })
      sessionId.value = res.session_id
      generatedScripts.value = res.scripts || []
      allScriptsContext.value = [...generatedScripts.value]
      competitorSummary.value = res.competitor_summary || {}
      marketSummary.value = res.market_summary || {}
      step.value = 2
    } catch (e) {
      // 失败时回退到step 0
      step.value = 0
      throw e
    } finally {
      loading.value = false
      researchProgress.value = ''
    }
  }

  /** Step 2→1→3: 选择方向 → loading页面 → 后端生成完整脚本 → 进入打磨 */
  const selectScript = async (scriptId: number) => {
    selectedScriptId.value = scriptId
    loading.value = true
    researchProgress.value = '正在生成完整分镜脚本（3个AI角色协作中）...'
    step.value = 1  // 跳到loading页面显示进度
    try {
      // 附带完整脚本数据，防止backend reload后session丢失导致404
      const selectedScript = (generatedScripts.value as any[]).find((s: any) => s.script_id === scriptId)
      const res: any = await api.selectScript(
        sessionId.value,
        scriptId,
        selectedScript || null,
        productInfo.value?.product_name || '',
        productInfo.value?.product_detail || '',
        productInfo.value?.industry || '',
      )
      const data = res.data || res
      projectId.value = data.project_id || ''
      scriptShots.value = data.shots || []
      qualityCheck.value = data.quality_report || null
      step.value = 3
    } catch (e) {
      step.value = 2  // 失败回到选择页面
      throw e
    } finally {
      loading.value = false
      researchProgress.value = ''
    }
  }

  /** Step 2: 换一批脚本 */
  const regenerateScripts = async (feedback?: string) => {
    loading.value = true
    try {
      const res: any = await api.regenerateScripts(sessionId.value, feedback)
      generatedScripts.value = res.scripts || []
      allScriptsContext.value = [...generatedScripts.value]
      selectedScriptId.value = null
    } finally {
      loading.value = false
    }
  }

  /** Step 3: 对话打磨（支持混搭） */
  const sendChatMessage = async (message: string) => {
    chatMessages.value.push({ role: 'user', content: message })
    loading.value = true
    try {
      const history = chatMessages.value.map(m => ({
        role: m.role === 'ai' ? 'assistant' : 'user',
        content: m.content,
      }))
      const res: any = await api.chatRefineV2(
        projectId.value,
        message,
        history,
        allScriptsContext.value,
      )
      chatMessages.value.push({ role: 'ai', content: res.ai_response || '' })
      if (res.updated_shots) {
        scriptShots.value = res.updated_shots
      }
    } finally {
      loading.value = false
    }
  }

  /** Step 3→4: 确认脚本并生成预览图 */
  const confirmAndPreview = async () => {
    loading.value = true
    try {
      await api.lockScript(projectId.value)
      // 初始化预览帧
      previewFrames.value = scriptShots.value.map((s: any) => ({
        shot_id: s.shot_id || s.id,
        image_url: null,
        narration: s.narration || '',
        visual_description: s.visual_description || '',
        duration: s.duration || 5,
        shot_type: s.shot_type || 'medium',
        generating: false,
      }))
      step.value = 4
    } finally {
      loading.value = false
    }
  }

  /** Step 4: SSE生成分镜预览图 */
  const generatePreview = () => {
    previewGenerating.value = true
    promptEngineeringStatus.value = ''
    previewFrames.value.forEach(f => {
      f.generating = true
      f.error = undefined
      f.image_url = null
    })

    api.generatePreview(
      projectId.value,
      (event, data) => {
        if (event === 'prompt_engineering') {
          promptEngineeringStatus.value = data.message || '正在优化提示词...'
        } else if (event === 'started') {
          promptEngineeringStatus.value = ''
        } else if (event === 'frame_generated') {
          const frame = previewFrames.value.find(f => f.shot_id === data.shot_id)
          if (frame) {
            frame.image_url = data.image_url || null
            frame.generating = false
            frame.error = data.success ? undefined : (data.error || '生成失败')
          }
        } else if (event === 'complete') {
          previewGenerating.value = false
          promptEngineeringStatus.value = ''
        } else if (event === 'error') {
          previewGenerating.value = false
          promptEngineeringStatus.value = ''
        }
      },
      () => {
        previewGenerating.value = false
        promptEngineeringStatus.value = ''
      },
      globalStyle.value,
    )
  }

  /** Step 4: 编辑单帧 */
  const updateFrame = async (shotId: number, narration?: string, visualDesc?: string) => {
    await api.updateFrame(projectId.value, shotId, narration, visualDesc)
    const frame = previewFrames.value.find(f => f.shot_id === shotId)
    if (frame) {
      if (narration !== undefined) frame.narration = narration
      if (visualDesc !== undefined) frame.visual_description = visualDesc
    }
    // 同步到scriptShots
    const shot = scriptShots.value.find((s: any) => (s.shot_id || s.id) === shotId)
    if (shot) {
      if (narration !== undefined) shot.narration = narration
      if (visualDesc !== undefined) shot.visual_description = visualDesc
    }
  }

  /** Step 4: 重新生成单帧图片 */
  const regenerateFrameImage = async (shotId: number, feedback?: string) => {
    const frame = previewFrames.value.find(f => f.shot_id === shotId)
    if (frame) {
      frame.generating = true
      frame.error = undefined
    }
    try {
      const res: any = await api.regenerateFrameImage(projectId.value, shotId, feedback, globalStyle.value)
      if (frame) {
        frame.image_url = res.image_url || null
        frame.generating = false
      }
    } catch (e) {
      if (frame) {
        frame.generating = false
        frame.error = '重新生成失败'
      }
    }
  }

  /** Step 4→5: 开始视频制作 */
  const startVideoProduction = () => {
    step.value = 5
    videoGenerating.value = true
    videoProgress.value = '准备中...'
    videoPercent.value = 0

    api.produceVideo(
      projectId.value,
      (event, data) => {
        if (event === 'video_generated' || event === 'progress') {
          videoProgress.value = data.message || ''
          videoPercent.value = data.percent || 0
        } else if (event === 'complete') {
          videoUrl.value = data.video_url || ''
          videoGenerating.value = false
          videoProgress.value = '完成！'
          videoPercent.value = 100
          step.value = 6
        } else if (event === 'error') {
          videoGenerating.value = false
          videoProgress.value = `错误: ${data.message}`
        }
      },
      () => {
        videoGenerating.value = false
      },
    )
  }

  /** 深度模式: 用户自带脚本跳转预览 */
  const skipToPreview = async (userScript: string) => {
    loading.value = true
    try {
      const res: any = await api.skipToPreview(sessionId.value || 'direct', userScript, targetDuration.value)
      const data = res.data || res
      projectId.value = data.project_id || ''
      scriptShots.value = data.shots || []
      previewFrames.value = scriptShots.value.map((s: any) => ({
        shot_id: s.shot_id || s.id,
        image_url: null,
        narration: s.narration || '',
        visual_description: s.visual_description || '',
        duration: s.duration || 5,
        shot_type: s.shot_type || 'medium',
        generating: false,
      }))
      step.value = 4
    } finally {
      loading.value = false
    }
  }

  // ==================== V3: Data-Driven Actions ====================

  /** V3: 启动数据驱动调研 */
  const startDataDrivenResearch = async () => {
    if (!productInfo.value) return
    dataDrivenMode.value = true
    loading.value = true
    researchPhase.value = 'searching'
    researchDetails.value = ['正在启动三方向数据调研...']
    researchError.value = null
    step.value = 1

    try {
      const res: any = await api.smartCreateV2({
        product_name: productInfo.value.product_name,
        industry: productInfo.value.category,
        target_duration: targetDuration.value,
        product_detail: [
          productInfo.value.core_features.join('; '),
          productInfo.value.target_audience ? `目标用户: ${productInfo.value.target_audience}` : '',
          productInfo.value.differentiators?.length ? `差异化: ${productInfo.value.differentiators.join('; ')}` : '',
        ].filter(Boolean).join('\n') || productInfo.value.product_name,
      })
      sessionId.value = res.session_id
      // 开始轮询进度
      startResearchPolling()
    } catch (e) {
      step.value = 0
      researchPhase.value = 'error'
      loading.value = false
      throw e
    }
  }

  /** V3: 轮询调研进度 */
  const startResearchPolling = () => {
    researchPolling.value = true
    researchPollTimer = setInterval(async () => {
      try {
        const res: any = await api.getResearchStatus(sessionId.value)
        researchPhase.value = res.phase || 'searching'
        researchDetails.value = res.details || []
        researchProgress.value = res.details?.slice(-1)[0] || ''

        if (res.phase === 'done') {
          stopResearchPolling()
          await fetchResearchResult()
        } else if (res.phase === 'error') {
          stopResearchPolling()
          researchError.value = res.error || '调研失败'
          loading.value = false
        }
      } catch (e) {
        console.error('轮询调研进度失败:', e)
      }
    }, 3000)
  }

  /** V3: 停止轮询 */
  const stopResearchPolling = () => {
    researchPolling.value = false
    if (researchPollTimer) {
      clearInterval(researchPollTimer)
      researchPollTimer = null
    }
  }

  /** V3: 获取调研结果 */
  const fetchResearchResult = async () => {
    try {
      const res: any = await api.getResearchResult(sessionId.value)
      dataDrivenScripts.value = res.scripts || []
      researchData.value = res.research_data || null

      // 也填充generatedScripts用于兼容现有UI
      generatedScripts.value = dataDrivenScripts.value.map((s: DataDrivenScript) => ({
        script_id: s.script_id,
        name: s.name,
        risk_level: s.direction === 'industry' ? 'safe' as const : s.direction === 'comments' ? 'moderate' as const : 'creative' as const,
        description: s.data_source,
        shots: s.shots,
        total_duration: s.total_duration,
        selling_points: s.selling_points,
        quality_report: s.quality_report,
      }))
      allScriptsContext.value = [...generatedScripts.value]

      step.value = 2
    } catch (e) {
      researchError.value = '获取结果失败'
    } finally {
      loading.value = false
    }
  }

  /** V3: 选择数据驱动脚本 */
  const selectDataDrivenScript = async (scriptId: number) => {
    selectedScriptId.value = scriptId
    loading.value = true
    researchProgress.value = '正在创建项目...'
    step.value = 1

    try {
      const res: any = await api.selectDataDrivenScript(sessionId.value, scriptId)
      const data = res.data || res
      projectId.value = data.project_id || ''
      scriptShots.value = data.shots || []
      qualityCheck.value = data.quality_report || null
      step.value = 3
    } catch (e) {
      step.value = 2
      throw e
    } finally {
      loading.value = false
      researchProgress.value = ''
    }
  }

  // ==================== Deep Mode V2: Creative Studio ====================

  /** Deep V2: 发送对话（带工具调用） */
  const sendDeepChat = async (message: string) => {
    deepMessages.value.push({ role: 'user', content: message })
    deepLoading.value = true
    try {
      const res: any = await api.deepChat({
        session_id: deepSessionId.value || undefined,
        message,
        chat_history: deepMessages.value.map(m => ({ role: m.role === 'ai' ? 'assistant' : m.role, content: m.content })),
        product_name: productInfo.value?.product_name,
        industry: productInfo.value?.category,
      })
      deepSessionId.value = res.session_id || deepSessionId.value
      sessionId.value = deepSessionId.value

      const aiMsg: any = { role: 'ai', content: res.response || '' }
      if (res.tool_used) {
        aiMsg.tool_used = res.tool_used
        aiMsg.tool_data = res.tool_data
      }
      deepMessages.value.push(aiMsg)

      // 如果AI检测到要生成脚本
      if (res.script_ready) {
        return { script_ready: true }
      }
      return res
    } finally {
      deepLoading.value = false
    }
  }

  /** Deep V2: 获取灵感 */
  const getInspirations = async () => {
    if (!productInfo.value?.product_name) return
    deepLoading.value = true
    try {
      const res: any = await api.deepInspire({
        session_id: deepSessionId.value || undefined,
        product_name: productInfo.value.product_name,
        industry: productInfo.value.category,
      })
      deepInspirations.value = res.inspirations || []

      // 添加系统消息展示灵感
      if (deepInspirations.value.length) {
        const insText = deepInspirations.value.map(
          (ins: any) => `[${ins.source}] ${ins.angle}: ${ins.suggested_hook}`
        ).join('\n')
        deepMessages.value.push({
          role: 'ai',
          content: `为你找到${deepInspirations.value.length}个灵感角度:\n${insText}\n\n点击感兴趣的灵感，或者告诉我"就这个方向出脚本"`,
          tool_used: 'inspiration',
          tool_data: { inspirations: deepInspirations.value },
        })
      }
    } finally {
      deepLoading.value = false
    }
  }

  /** Deep V2: 从对话生成脚本 */
  const generateFromDeepConversation = async () => {
    if (!deepSessionId.value) return
    loading.value = true
    researchProgress.value = '正在根据对话上下文生成脚本...'
    step.value = 1

    try {
      const res: any = await api.deepGenerate(deepSessionId.value)
      sessionId.value = deepSessionId.value
      generatedScripts.value = (res.scripts || []).map((s: any) => ({
        ...s,
        hook: s.hook || s.shots?.[0]?.narration || '',
        structure_preview: s.structure_preview || [],
        creative_techniques: s.creative_techniques || [],
      }))
      allScriptsContext.value = [...generatedScripts.value]
      step.value = 2
    } catch (e) {
      step.value = 0
      throw e
    } finally {
      loading.value = false
      researchProgress.value = ''
    }
  }

  // ==================== Legacy Actions (backward compat) ====================

  const startResearch = generateScripts

  const selectDir = async (dir: Direction) => {
    selectedDirection.value = dir
    loading.value = true
    try {
      const res: any = await api.selectDirection(sessionId.value, dir.direction_id)
      const data = res.data || res
      sellingPoints.value = data.selling_points || []
      hooks.value = data.hooks || []
      step.value = 3
    } finally {
      loading.value = false
    }
  }

  const selectHookAndGenerate = async (hook: Hook) => {
    selectedHook.value = hook
    loading.value = true
    try {
      const res: any = await api.selectHook(sessionId.value, hook.hook_id)
      const data = res.data || res
      projectId.value = data.project_id || ''
      scriptShots.value = data.shots || []
      qualityCheck.value = data.quality_check || null
      step.value = 4
    } finally {
      loading.value = false
    }
  }

  const lockCurrentScript = confirmAndPreview

  // Deep mode
  const sendIntakeMessage = async (message: string) => {
    intakeMessages.value.push({ role: 'user', content: message })
    loading.value = true
    try {
      const res: any = await api.intakeNextQuestion(
        sessionId.value,
        intakeMessages.value.map(m => ({ role: m.role, content: m.content })),
      )
      intakeMessages.value.push({ role: 'ai', content: res.question || '' })
      collectedSummary.value = res.collected_summary || {}
      if (res.is_complete) {
        const summary = res.collected_summary || {}
        productInfo.value = {
          product_name: summary.product_name || '',
          category: summary.category || '',
          price_range: summary.price_range || '',
          core_features: summary.core_features || [],
          target_audience: summary.target_audience || '',
          use_cases: summary.use_cases || [],
          differentiators: summary.differentiators || [],
          brand_tone: summary.brand_tone || '',
          raw_content: '',
        }
      }
      return res
    } finally {
      loading.value = false
    }
  }

  const reset = () => {
    step.value = 0
    mode.value = 'quick'
    productInfo.value = null
    sessionId.value = ''
    projectId.value = ''
    directions.value = []
    selectedDirection.value = null
    hooks.value = []
    selectedHook.value = null
    sellingPoints.value = []
    generatedScripts.value = []
    selectedScriptId.value = null
    allScriptsContext.value = []
    scriptShots.value = []
    qualityCheck.value = null
    chatMessages.value = []
    selectedTemplate.value = null
    loading.value = false
    researchProgress.value = ''
    targetDuration.value = 60
    previewFrames.value = []
    previewGenerating.value = false
    videoGenerating.value = false
    videoProgress.value = ''
    videoUrl.value = ''
    videoPercent.value = 0
    intakeMessages.value = []
    collectedSummary.value = {}
    // Deep V2 reset
    deepMessages.value = []
    deepInspirations.value = []
    deepSessionId.value = ''
    deepLoading.value = false
    // V3 reset
    dataDrivenMode.value = false
    researchPhase.value = 'idle'
    researchDetails.value = []
    researchPolling.value = false
    researchError.value = null
    dataDrivenScripts.value = []
    researchData.value = null
    stopResearchPolling()
  }

  return {
    // State
    step, mode, productInfo, sessionId, projectId,
    directions, selectedDirection, hooks, selectedHook,
    sellingPoints, scriptShots, qualityCheck, chatMessages,
    selectedTemplate, loading, researchProgress,
    competitorSummary, marketSummary, targetDuration,
    intakeMessages, collectedSummary,
    // V2 State
    generatedScripts, selectedScriptId, allScriptsContext,
    previewFrames, previewGenerating, globalStyle, promptEngineeringStatus,
    videoGenerating, videoProgress, videoUrl, videoPercent,
    // Deep V2 State
    deepMessages, deepInspirations, deepSessionId, deepLoading,
    // Getters
    canProceed, selectedScript,
    // V2 Actions
    generateScripts, selectScript, regenerateScripts,
    confirmAndPreview, generatePreview, updateFrame,
    regenerateFrameImage, startVideoProduction, skipToPreview,
    // V3 Data-Driven State
    dataDrivenMode, researchPhase, researchDetails, researchPolling,
    researchError, dataDrivenScripts, researchData,
    // V3 Data-Driven Actions
    startDataDrivenResearch, selectDataDrivenScript,
    stopResearchPolling, fetchResearchResult,
    // Deep V2 Actions
    sendDeepChat, getInspirations, generateFromDeepConversation,
    // Legacy Actions
    startResearch, selectDir, selectHookAndGenerate,
    sendChatMessage, lockCurrentScript, sendIntakeMessage, reset,
  }
})
