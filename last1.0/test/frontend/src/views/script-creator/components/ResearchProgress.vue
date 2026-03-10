<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Loading, Check, Clock } from '@element-plus/icons-vue'
import { useScriptCreatorStore } from '../../../stores/scriptCreator'

const store = useScriptCreatorStore()
const elapsed = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  timer = setInterval(() => {
    elapsed.value += 1
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

// 数据驱动模式的多阶段进度
const isDataDriven = computed(() => store.dataDrivenMode)

const progressPercent = computed(() => {
  if (!isDataDriven.value) {
    // 旧模式：假进度
    return Math.min(5 + elapsed.value * 1.5, 95)
  }
  // 数据驱动模式：跟踪真实phase
  const phaseMap: Record<string, number> = {
    searching: 15,
    downloading: 35,
    analyzing: 60,
    generating: 85,
    done: 100,
    error: 0,
  }
  return phaseMap[store.researchPhase] || 5
})

const subtitle = computed(() => {
  if (isDataDriven.value) {
    const p = store.researchPhase
    const map: Record<string, string> = {
      searching: '搜索同行业爆款 + 跨行业创意视频...',
      downloading: '下载视频 → ASR语音转文字 + Gemini视觉分析...',
      analyzing: '评论聚类分析 + 提取成功模式 + 创意迁移方案...',
      generating: '基于真实数据生成3个方向的脚本...',
      done: '调研完成！',
      error: '调研过程中遇到问题',
    }
    return map[p] || '正在调研中...'
  }
  const p = store.researchProgress || ''
  if (p.includes('分镜脚本')) {
    return 'Director策略 → Screenwriter编剧 → Producer质审，约1-2分钟'
  }
  return '分析市场 + 生成创意方向，约10-20秒'
})

// 数据驱动模式的步骤列表
const researchSteps = computed(() => {
  if (!isDataDriven.value) return []
  const phase = store.researchPhase
  const steps = [
    { label: '搜索同行业爆款视频', done: ['downloading', 'analyzing', 'generating', 'done'].includes(phase), active: phase === 'searching' },
    { label: '下载分析视频（ASR+Gemini）', done: ['analyzing', 'generating', 'done'].includes(phase), active: phase === 'downloading' },
    { label: '评论区数据采集与聚类', done: ['generating', 'done'].includes(phase), active: phase === 'analyzing' },
    { label: '搜索跨行业创意视频', done: ['analyzing', 'generating', 'done'].includes(phase), active: phase === 'downloading' || phase === 'analyzing' },
    { label: '提取创意模式与迁移方案', done: ['generating', 'done'].includes(phase), active: phase === 'analyzing' },
    { label: '生成3个方向的数据驱动脚本', done: phase === 'done', active: phase === 'generating' },
  ]
  return steps
})

// 最近的实时日志
const recentDetails = computed(() => {
  const details = store.researchDetails || []
  return details.slice(-5)
})
</script>

<template>
  <div style="max-width: 560px; margin: 60px auto; text-align: center;">
    <el-icon class="is-loading" :size="50" style="color: #409eff;"><Loading /></el-icon>
    <h3 style="margin-top: 16px;">{{ store.researchProgress || '正在处理...' }}</h3>
    <el-progress
      :percentage="Math.min(Math.round(progressPercent), 98)"
      :stroke-width="10"
      style="margin-top: 16px;"
    />
    <p style="color: #909399; margin-top: 12px; font-size: 13px;">{{ subtitle }}</p>

    <!-- 数据驱动模式：多阶段步骤列表 -->
    <div v-if="isDataDriven && researchSteps.length" style="text-align: left; margin-top: 24px; padding: 16px; background: #f8f9fa; border-radius: 8px;">
      <div
        v-for="(s, i) in researchSteps"
        :key="i"
        style="display: flex; align-items: center; padding: 6px 0; font-size: 13px;"
        :style="{ color: s.done ? '#67c23a' : s.active ? '#409eff' : '#c0c4cc' }"
      >
        <el-icon v-if="s.done" style="margin-right: 8px;"><Check /></el-icon>
        <el-icon v-else-if="s.active" class="is-loading" style="margin-right: 8px;"><Loading /></el-icon>
        <el-icon v-else style="margin-right: 8px;"><Clock /></el-icon>
        <span>{{ s.label }}</span>
        <span v-if="s.done" style="margin-left: auto; font-size: 11px;">✓</span>
        <span v-else-if="s.active" style="margin-left: auto; font-size: 11px;">进行中</span>
        <span v-else style="margin-left: auto; font-size: 11px;">等待中</span>
      </div>
    </div>

    <!-- 实时日志 -->
    <div v-if="isDataDriven && recentDetails.length" style="margin-top: 16px; text-align: left;">
      <p
        v-for="(d, i) in recentDetails"
        :key="i"
        style="color: #b0b4ba; font-size: 11px; line-height: 1.6; margin: 0; padding: 0;"
      >
        {{ d }}
      </p>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="store.researchError"
      :title="store.researchError"
      type="error"
      style="margin-top: 16px;"
      show-icon
    />

    <p style="color: #c0c4cc; font-size: 12px; margin-top: 12px;">
      已等待 {{ elapsed }} 秒
    </p>
  </div>
</template>
