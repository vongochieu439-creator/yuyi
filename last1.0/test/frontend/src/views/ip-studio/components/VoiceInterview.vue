<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'
import { Microphone, ChatDotRound, Loading, CloseBold, Phone, Headset } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useIPStudioStore } from '../../../stores/ipStudio'
import { useWebSocket } from '../../../composables/useWebSocket'
import { useVoiceStream } from '../../../composables/useVoiceStream'
import { useAudioPlayer } from '../../../composables/useAudioPlayer'
import PhaseProgress from '../../../components/PhaseProgress.vue'

const store = useIPStudioStore()
const { connect, send, close: closeWs, connected: wsConnected } = useWebSocket('/api/ip-studio/interview/live')
const { start: startRecording, stop: stopRecording } = useVoiceStream()
const { playPcm16Base64, cleanup: cleanupAudio } = useAudioPlayer(24000)

const voiceState = ref<'idle' | 'connecting' | 'ai_speaking' | 'user_speaking' | 'thinking'>('idle')
const voicePhase = ref('background')
const voiceTranscript = ref<Array<{ role: string; text: string }>>([])
const voiceMuted = ref(false)
const voiceDuration = ref('00:00')
const voiceStartTime = ref<number | null>(null)
const durationTimer = ref<ReturnType<typeof setInterval> | null>(null)

const phases = [
  { key: 'background', label: '背景采集', desc: '3-5轮' },
  { key: 'hot_topics', label: '热点观点', desc: '3-5轮' },
  { key: 'cognitive', label: '思维挖掘', desc: '4-6轮' },
  { key: 'voice', label: '表达采样', desc: '3-4轮' },
]

const roundCount = computed(() => voiceTranscript.value.filter(t => t.role === 'user').length)

const lastSubtitle = computed(() => {
  const filtered = voiceTranscript.value.filter(t => t.role !== 'phase-transition')
  const last = filtered[filtered.length - 1]
  if (!last) return ''
  return last.text.length > 80 ? last.text.slice(0, 80) + '...' : last.text
})

const circleGradient = computed(() => {
  if (voiceState.value === 'ai_speaking') return 'linear-gradient(135deg, #8b5cf6, #ec4899)'
  if (voiceState.value === 'user_speaking') return 'linear-gradient(135deg, #10b981, #06b6d4)'
  return 'linear-gradient(135deg, #d1d5db, #9ca3af)'
})

const circleShadow = computed(() => {
  if (voiceState.value === 'ai_speaking' || voiceState.value === 'user_speaking')
    return '0 0 40px rgba(139, 92, 246, 0.3)'
  return 'none'
})

const pulseColor = computed(() => {
  if (voiceState.value === 'ai_speaking') return 'rgba(139,92,246,0.4)'
  return 'rgba(16,185,129,0.4)'
})

const startVoiceInterview = () => {
  const name = store.intervieweeName || store.currentProfile?.name || ''
  const industry = store.intervieweeIndustry || store.currentProfile?.industry || ''
  const role = store.intervieweeRole || store.currentProfile?.role || '创始人'

  if (!name || !industry) {
    ElMessage.warning('请先填写姓名和行业信息')
    store.goToView('interview')
    return
  }

  voiceState.value = 'connecting'
  voiceTranscript.value = []
  voiceMuted.value = false

  // onMessage: handle all server events
  const onMessage = (data: Record<string, unknown>) => {
    switch (data.type) {
      case 'connected':
        voiceState.value = 'idle'
        voiceStartTime.value = Date.now()
        durationTimer.value = setInterval(() => {
          const sec = Math.floor((Date.now() - (voiceStartTime.value || Date.now())) / 1000)
          const m = String(Math.floor(sec / 60)).padStart(2, '0')
          const s = String(sec % 60).padStart(2, '0')
          voiceDuration.value = `${m}:${s}`
        }, 1000)
        startMic()
        ElMessage.success('语音连接成功，开始访谈')
        break
      case 'ai_speaking_start':
        voiceState.value = 'ai_speaking'
        break
      case 'ai_audio':
        playPcm16Base64(data.data as string)
        break
      case 'ai_speaking_done':
        if (voiceState.value === 'ai_speaking') voiceState.value = 'idle'
        break
      case 'user_speaking_start':
        voiceState.value = 'user_speaking'
        break
      case 'user_speaking_done':
        voiceState.value = 'thinking'
        break
      case 'transcript':
        if ((data.text as string)?.trim())
          voiceTranscript.value.push({ role: data.role as string, text: data.text as string })
        break
      case 'phase_change':
        voicePhase.value = data.phase as string
        voiceTranscript.value.push({ role: 'phase-transition', text: (data.message as string) || `进入${data.phase}阶段` })
        ElMessage.info(`阶段切换：${(data.message as string) || data.phase}`)
        break
      case 'interview_done':
        finishInterview(data.chat_history as Array<{ role: string; content: string }>)
        break
      case 'error':
        ElMessage.error((data.message as string) || '语音访谈出错')
        voiceState.value = 'idle'
        break
    }
  }

  // onOpen: send init immediately when WebSocket opens (same as old working code)
  const onOpen = () => {
    console.log('[Voice] WS open, sending init:', { name, industry, role })
    send({ type: 'init', name, industry, role })
  }

  // onError
  const onError = () => {
    ElMessage.error('语音连接出错')
    voiceState.value = 'idle'
  }

  connect(onMessage, onOpen, onError)
}

const startMic = async () => {
  try {
    await startRecording((base64: string) => {
      if (!voiceMuted.value && voiceState.value !== 'ai_speaking') {
        send({ type: 'audio', data: base64 })
      }
    })
  } catch {
    ElMessage.error('麦克风权限获取失败')
  }
}

const toggleMute = () => {
  voiceMuted.value = !voiceMuted.value
  ElMessage.info(voiceMuted.value ? '麦克风已静音' : '麦克风已开启')
}

const endCall = async () => {
  try {
    await ElMessageBox.confirm('确定结束通话吗？访谈记录将被保存。', '结束通话', {
      confirmButtonText: '结束', cancelButtonText: '继续', type: 'warning'
    })
  } catch { return }
  send({ type: 'end_call' })
  setTimeout(() => {
    const chatHistory = voiceTranscript.value
      .filter(t => t.role === 'user' || t.role === 'ai')
      .map(t => ({ role: t.role, content: t.text }))
    finishInterview(chatHistory)
  }, 3000)
}

const finishInterview = (chatHistory: any[]) => {
  cleanup()
  store.chatHistory = chatHistory.map((m: any) => ({ role: m.role as 'user' | 'ai', content: m.content }))
  ElMessage.success('访谈完成！')
  store.goToView('interview')
}

const cleanup = () => {
  stopRecording()
  closeWs()
  if (durationTimer.value) clearInterval(durationTimer.value)
  cleanupAudio()
}

onBeforeUnmount(() => cleanup())
</script>

<template>
  <div class="page-narrow">
    <el-card shadow="always" style="min-height: 600px; display: flex; flex-direction: column;">
      <template #header>
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #ec4899); display: flex; align-items: center; justify-content: center; color: white; font-size: 16px; flex-shrink: 0;">
            <el-icon><Microphone /></el-icon>
          </div>
          <div style="flex: 1;">
            <div style="font-weight: bold; font-size: 15px;">AI记者 · 语音访谈中</div>
            <div style="font-size: 12px; color: #909399;">像打电话一样，直接说就行</div>
          </div>
          <el-tag v-if="voiceState === 'connecting'" type="info">连接中...</el-tag>
          <el-tag v-else-if="wsConnected" type="success">已连接</el-tag>
        </div>
      </template>

      <!-- Phase progress -->
      <PhaseProgress :phases="phases" :current-phase="voicePhase" theme="voice" />

      <!-- Not connected: start button -->
      <div v-if="voiceState === 'idle' && !wsConnected" style="text-align: center; padding: 60px 0;">
        <el-button type="primary" size="large" @click="startVoiceInterview" style="font-size: 16px; padding: 14px 40px;">
          🎙️ 开始语音访谈
        </el-button>
      </div>

      <!-- Central voice circle -->
      <div v-else style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 250px;">
        <div style="position: relative; width: 160px; height: 160px; margin-bottom: 24px;">
          <div :style="{
            width: '160px', height: '160px', borderRadius: '50%',
            background: circleGradient,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.3s ease',
            boxShadow: circleShadow
          }">
            <div v-if="voiceState === 'ai_speaking'" style="color: white; font-size: 48px;">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div v-else-if="voiceState === 'user_speaking'" style="color: white; font-size: 48px;">
              <el-icon><Microphone /></el-icon>
            </div>
            <div v-else-if="voiceState === 'thinking' || voiceState === 'connecting'" style="color: white; font-size: 48px;">
              <el-icon class="is-loading"><Loading /></el-icon>
            </div>
            <div v-else style="color: white; font-size: 48px;">
              <el-icon><Headset /></el-icon>
            </div>
          </div>
          <!-- Pulse ring -->
          <div v-if="voiceState === 'ai_speaking' || voiceState === 'user_speaking'" :style="{
            position: 'absolute', top: '-10px', left: '-10px', width: '180px', height: '180px',
            borderRadius: '50%', border: '2px solid', borderColor: pulseColor,
            animation: 'voicePulse 1.5s ease-in-out infinite'
          }" />
        </div>

        <!-- Status text -->
        <div style="font-size: 16px; font-weight: bold; color: #303133; margin-bottom: 8px;">
          <span v-if="voiceState === 'connecting'">正在连接语音服务...</span>
          <span v-else-if="voiceState === 'ai_speaking'" style="color: #8b5cf6;">AI正在说话...</span>
          <span v-else-if="voiceState === 'user_speaking'" style="color: #10b981;">正在听你说...</span>
          <span v-else-if="voiceState === 'thinking'" style="color: #f59e0b;">AI思考中...</span>
          <span v-else-if="wsConnected" style="color: #6b7280;">等待你说话...</span>
          <span v-else>准备就绪</span>
        </div>

        <!-- Duration + round count -->
        <div v-if="wsConnected" style="display: flex; gap: 16px; font-size: 13px; color: #909399; margin-bottom: 8px;">
          <span>{{ voiceDuration }}</span>
          <span>第 {{ roundCount }} 轮</span>
        </div>

        <!-- Last subtitle -->
        <div v-if="voiceTranscript.length > 0" style="font-size: 13px; color: #606266; max-width: 400px; text-align: center; line-height: 1.5; min-height: 40px;">
          {{ lastSubtitle }}
        </div>
      </div>

      <!-- Collapsible transcript -->
      <el-collapse v-if="voiceTranscript.length > 0" style="margin-top: 16px;">
        <el-collapse-item title="查看对话记录" name="transcript">
          <div style="max-height: 200px; overflow-y: auto; padding: 8px;">
            <div v-for="(t, i) in voiceTranscript" :key="i" style="margin-bottom: 10px;">
              <div v-if="t.role === 'phase-transition'" style="text-align: center; padding: 8px;">
                <div style="display: inline-block; padding: 6px 16px; background: linear-gradient(135deg, #ede9fe, #ddd6fe); border-radius: 16px; font-size: 12px; color: #6d28d9; font-weight: bold;">
                  {{ t.text }}
                </div>
              </div>
              <div v-else-if="t.role === 'ai'" style="display: flex; gap: 8px; align-items: flex-start;">
                <div style="width: 24px; height: 24px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #ec4899); display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; flex-shrink: 0;">AI</div>
                <div style="font-size: 13px; color: #606266; line-height: 1.5;">{{ t.text }}</div>
              </div>
              <div v-else style="display: flex; gap: 8px; align-items: flex-start; justify-content: flex-end;">
                <div style="font-size: 13px; color: #303133; line-height: 1.5; text-align: right;">{{ t.text }}</div>
                <div style="width: 24px; height: 24px; border-radius: 50%; background: #6b7280; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; flex-shrink: 0;">我</div>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <!-- Bottom buttons -->
      <div style="display: flex; gap: 12px; justify-content: center; margin-top: 20px; padding-top: 16px; border-top: 1px solid #f0f0f0;">
        <el-button :type="voiceMuted ? 'danger' : 'default'" circle size="large" @click="toggleMute" :disabled="!wsConnected">
          <el-icon :size="20">
            <CloseBold v-if="voiceMuted" />
            <Microphone v-else />
          </el-icon>
        </el-button>
        <el-button type="danger" size="large" @click="endCall" style="padding: 12px 32px; font-size: 15px;">
          <el-icon style="margin-right: 6px;"><Phone /></el-icon>
          结束通话
        </el-button>
      </div>
    </el-card>
  </div>
</template>
