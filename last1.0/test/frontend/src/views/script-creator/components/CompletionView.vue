<template>
  <div class="completion-view">
    <el-result icon="success" title="视频生成完成!" sub-title="你的营销视频已经准备好了">
      <template #extra>
        <div class="video-player" v-if="store.videoUrl">
          <video
            :src="getVideoUrl(store.videoUrl)"
            controls
            class="player"
          />
        </div>
        <div class="action-buttons">
          <el-button type="primary" size="large" @click="handleDownload">
            下载视频
          </el-button>
          <el-button size="large" @click="store.reset()">
            创建新视频
          </el-button>
        </div>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { useScriptCreatorStore } from '../../../stores/scriptCreator'

const store = useScriptCreatorStore()
const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

const getVideoUrl = (url: string) => {
  if (url.startsWith('http')) return url
  return `${baseUrl}${url}`
}

const handleDownload = () => {
  if (!store.videoUrl) return
  const link = document.createElement('a')
  link.href = getVideoUrl(store.videoUrl)
  link.download = 'marketing_video.mp4'
  link.click()
}
</script>

<style scoped>
.completion-view { padding: 40px 0; }
.video-player { margin-bottom: 24px; }
.player { width: 100%; max-width: 720px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.action-buttons { display: flex; gap: 12px; justify-content: center; }
</style>
