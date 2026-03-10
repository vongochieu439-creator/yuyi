<template>
  <div class="video-production">
    <el-card>
      <template #header>
        <h3>视频生成</h3>
      </template>

      <div class="progress-area">
        <el-progress
          :percentage="store.videoPercent"
          :status="progressStatus"
          :stroke-width="20"
          striped
          striped-flow
        />
        <p class="progress-text">{{ store.videoProgress }}</p>
      </div>

      <div class="steps-detail" v-if="store.videoGenerating">
        <el-timeline>
          <el-timeline-item
            v-for="(s, i) in steps"
            :key="i"
            :type="stepType(i)"
            :hollow="store.videoPercent < s.threshold"
          >
            {{ s.label }}
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useScriptCreatorStore } from '../../../stores/scriptCreator'

const store = useScriptCreatorStore()

const steps = [
  { label: '图生视频片段', threshold: 10 },
  { label: 'TTS配音生成', threshold: 80 },
  { label: 'FFmpeg合成', threshold: 90 },
  { label: '完成', threshold: 100 },
]

const progressStatus = computed(() => {
  if (store.videoProgress.includes('错误')) return 'exception'
  if (store.videoPercent >= 100) return 'success'
  return undefined
})

const stepType = (index: number) => {
  const pct = store.videoPercent
  if (pct >= steps[index].threshold) return 'success'
  if (index > 0 && pct >= steps[index - 1].threshold) return 'primary'
  return 'info'
}
</script>

<style scoped>
.video-production { padding: 20px 0; max-width: 600px; margin: 0 auto; }
.progress-area { text-align: center; margin-bottom: 24px; }
.progress-text { margin-top: 12px; color: #666; font-size: 14px; }
.steps-detail { margin-top: 20px; }
</style>
